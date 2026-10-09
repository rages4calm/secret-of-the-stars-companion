"""Compile/check the original-word field resolver without launching gameplay.

The standalone C path is the same cache/eligibility/resolver used by the title;
only its live global-to-view adapter is omitted. Inputs are copied captures and
the exact clean USA image. Private reports/build outputs remain under local/.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import hashlib
import json
import os
import shutil
import subprocess

from inspect_foundation_field import ROM_SHA256, ROOT


class View(ctypes.Structure):
    _fields_ = [('ram', ctypes.POINTER(ctypes.c_uint8)), ('ram_size', ctypes.c_size_t),
                ('inidisp', ctypes.c_uint8), ('bgmode', ctypes.c_uint8),
                ('mosaic', ctypes.c_uint8), ('setini', ctypes.c_uint8),
                ('bgsc', ctypes.c_uint8 * 4), ('tm', ctypes.c_uint8), ('ts', ctypes.c_uint8),
                ('bg_tile_adr', ctypes.c_uint16), ('hscroll', ctypes.c_uint16 * 2),
                ('vscroll', ctypes.c_uint16 * 2)]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(rom_path, captures, output):
    rom = rom_path.read_bytes()
    if digest(rom) != ROM_SHA256:
        raise ValueError('Exact clean ROM required')
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'local').resolve()) or output.exists():
        raise ValueError('Choose a fresh private output directory under local/')
    output.mkdir(parents=True)
    authored = ROOT / 'native/foundation/src'
    runtime = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    configured = Path(r'C:\Users\crono\.local\share\retcomm\toolchains\cmake-clang-v1\latest\bin\clang.exe')
    compiler = str(configured) if configured.exists() else shutil.which('clang')
    if not compiler:
        raise ValueError('A C compiler is required for the standalone core proof')
    library = output / ('field-resolver.dll' if os.name == 'nt' else 'field-resolver.so')
    command = [compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared',
               '-DFOUNDATION_FIELD_STANDALONE', '-I' + str(authored), '-I' + str(runtime),
               str(authored / 'foundation_field.c'), str(runtime / 'sha256.c'), '-o', str(library)]
    if os.name != 'nt':
        command.insert(1, '-fPIC')
    compile_result = subprocess.run(command, capture_output=True, text=True)
    (output / 'compile.log').write_text(compile_result.stdout + compile_result.stderr)
    if compile_result.returncode:
        raise ValueError('Standalone C compile failed: ' + compile_result.stderr)
    dll = ctypes.CDLL(str(library))
    dll.FoundationFieldBind.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    dll.FoundationFieldBind.restype = ctypes.c_int
    dll.FoundationFieldCheckView.argtypes = [ctypes.POINTER(View)]
    dll.FoundationFieldCheckView.restype = ctypes.c_int
    dll.FoundationFieldCheckSceneView.argtypes = [ctypes.POINTER(View)]
    dll.FoundationFieldCheckSceneView.restype = ctypes.c_int
    dll.FoundationFieldResolve.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(ctypes.c_uint16)]
    dll.FoundationFieldResolve.restype = ctypes.c_int
    dll.FoundationFieldCamera.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int),
                                        ctypes.POINTER(ctypes.c_int)]
    dll.FoundationFieldCamera.restype = ctypes.c_int
    dll.FoundationFieldReset.argtypes = []
    dll.FoundationFieldReset.restype = None
    rom_buffer = (ctypes.c_uint8 * len(rom)).from_buffer_copy(rom)
    out_word = ctypes.c_uint16(0xdead)
    checks = {'before_bind_rejected': not dll.FoundationFieldResolve(0, 0, 0, ctypes.byref(out_word))}
    checks['exact_rom_binds'] = bool(dll.FoundationFieldBind(rom_buffer, len(rom)))

    def rr(a, n=1):
        o = (a >> 16) * 32768 + (a & 32767)
        return int.from_bytes(rom[o:o + n], 'little')

    def expected(layer, px, py):
        nx = [2, 4][layer]
        metatile = 0
        if 0 <= px < nx * 256 and 0 <= py < nx * 256:
            segment = rr([0x0996a2, 0x099700][layer] + 2 * ((py // 256) * nx + px // 256), 2)
            source = rr(0x09b000 + segment * 3, 3)
            cell = rr(source + ((py // 32) % 8) * 8 + (px // 32) % 8)
            metatile = rr(0x0a8818 + cell * 4 + ((py // 16) % 2) * 2 + (px // 16) % 2)
        return rr(0x038f58 + metatile * 8 + ((py // 8) % 2) * 4 + ((px // 8) % 2) * 2, 2)

    def resolve(layer, x, y):
        if not dll.FoundationFieldResolve(layer, x, y, ctypes.byref(out_word)):
            raise ValueError('Eligible resolver unexpectedly declined')
        return out_word.value

    capture_reports = []
    full_compared = 0
    boundary_compared = 0
    for prefix in captures:
        inputs = {k: Path(str(prefix) + '.' + k) for k in
                  ['wram.bin', 'vram.bin', 'regs.json', 'cgram.bin']}
        before = {k: digest(p.read_bytes()) for k, p in inputs.items()}
        wram = inputs['wram.bin'].read_bytes()
        vram = inputs['vram.bin'].read_bytes()
        regs = json.loads(inputs['regs.json'].read_text())
        if len(wram) != 0x20000 or len(vram) != 0x10000:
            raise ValueError('Complete captured WRAM/VRAM required')
        ram_buffer = (ctypes.c_uint8 * len(wram)).from_buffer_copy(wram)
        view = View(ram_buffer, len(wram), regs['inidisp'], regs['bgmode'], regs['mosaic'],
                    regs['setini'], (ctypes.c_uint8 * 4)(*regs['bgsc']), regs['tm'], regs['ts'],
                    regs['bg_tile_adr'], (ctypes.c_uint16 * 2)(*regs['hscroll'][:2]),
                    (ctypes.c_uint16 * 2)(*regs['vscroll'][:2]))
        if not dll.FoundationFieldCheckView(ctypes.byref(view)):
            raise ValueError('Checked capture was refused by the native contract')
        checks[f'capture{len(capture_reports)}_scene_contract_eligible'] = bool(
            dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        layers = []
        for layer in range(2):
            x, y = ctypes.c_int(), ctypes.c_int()
            if not dll.FoundationFieldCamera(layer, ctypes.byref(x), ctypes.byref(y)):
                raise ValueError('Camera adapter refused')
            camera = [x.value, y.value]
            if camera[0] % 8 or camera[1] % 8:
                raise ValueError('Use tile-aligned center comparison captures')
            comparisons = {}
            for region, start, stop in [('center', 0, 256), ('left', -72, 0), ('right', 256, 328)]:
                differences, decoded_differences, count = 0, 0, 0
                for sy in range(0, 224, 8):
                    for sx in range(start, stop, 8):
                        px, py = camera[0] + sx, camera[1] + sy
                        word = resolve(layer, px, py)
                        decoded_differences += int(word != expected(layer, px, py))
                        tx, ty = (px // 8) % 64, (py // 8) % 32
                        at = [0x9000, 0xb000][layer] + tx // 32 * 2048 + (ty * 32 + tx % 32) * 2
                        actual = int.from_bytes(vram[at:at + 2], 'little')
                        differences += int(actual != word)
                        count += 1
                comparisons[region] = {'compared': count, 'ring_differences': differences,
                                       'independent_decoder_differences': decoded_differences}
            checks[f'capture{len(capture_reports)}_layer{layer}_center_exact'] = comparisons['center']['ring_differences'] == 0
            checks[f'capture{len(capture_reports)}_layer{layer}_decoder_exact'] = all(
                v['independent_decoder_differences'] == 0 for v in comparisons.values())
            size = [512, 1024][layer]
            failures = 0
            for py in range(0, size, 8):
                for px in range(0, size, 8):
                    failures += int(resolve(layer, px, py) != expected(layer, px, py))
                    full_compared += 1
            checks[f'capture{len(capture_reports)}_layer{layer}_full_map_exact'] = failures == 0
            boundary_cases = [-2147483648, -1025, -513, -257, -17, -16, -9, -8, -1,
                              0, 7, 8, 15, 16, 255, 256, size - 1, size, size + 7,
                              size + 8, 2147483647]
            failures = 0
            for px in boundary_cases:
                for py in boundary_cases:
                    failures += int(resolve(layer, px, py) != expected(layer, px, py))
                    boundary_compared += 1
            checks[f'capture{len(capture_reports)}_layer{layer}_boundaries_exact'] = failures == 0
            layers.append({'layer': layer, 'camera': camera, 'comparisons': comparisons})
        checks[f'capture{len(capture_reports)}_ram_not_mutated'] = bytes(ram_buffer) == wram

        # Exercise semantic refusal controls rather than just enumerating types.
        for name, at, value in [('battle_mode', 0x20, 5), ('other_scene', 0x40e, 6),
                                ('wrapping_map', 0x407, 1), ('direct_loading', 0x531, 128),
                                ('different_grid', 0x513, 0), ('different_dimensions', 0x46d, 3),
                                ('different_tileset', 0x500, 0), ('different_cells', 0x506, 0),
                                ('different_attributes', 0x537, 0), ('camera_mismatch', 0x2ad, 1)]:
            old = ram_buffer[at]
            ram_buffer[at] = value
            checks[f'capture{len(capture_reports)}_reject_{name}'] = (
                not dll.FoundationFieldCheckView(ctypes.byref(view)) and
                not dll.FoundationFieldResolve(0, 0, 0, ctypes.byref(out_word)))
            checks[f'capture{len(capture_reports)}_scene_{name}'] = (
                bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view))) == (name == 'camera_mismatch'))
            ram_buffer[at] = old
        for name, attr, value in [('forced_blank', 'inidisp', 128), ('other_ppu_mode', 'bgmode', 1),
                                  ('mosaic', 'mosaic', 1), ('interlace', 'setini', 1),
                                  ('different_char_base', 'bg_tile_adr', 0),
                                  ('different_main_layers', 'tm', 0), ('subscreen', 'ts', 1),
                                  ('truncated_ram', 'ram_size', 1)]:
            old = getattr(view, attr)
            setattr(view, attr, value)
            checks[f'capture{len(capture_reports)}_reject_{name}'] = not dll.FoundationFieldCheckView(ctypes.byref(view))
            checks[f'capture{len(capture_reports)}_scene_reject_{name}'] = not dll.FoundationFieldCheckSceneView(ctypes.byref(view))
            setattr(view, attr, old)
        # Prepare occurs before raster journal applies this field's scroll.
        # Only the explicit scene API accepts unequal PPU/WRAM scroll latches.
        # All other scene/layout/input guards above remain identical.
        saved_scroll = list(view.hscroll), list(view.vscroll)
        for layer in range(2):
            view.hscroll[layer] = (view.hscroll[layer] + 1) & 1023
            view.vscroll[layer] = (view.vscroll[layer] - 1) & 1023
            checks[f'capture{len(capture_reports)}_layer{layer}_strict_scroll_mismatch_rejected'] = not dll.FoundationFieldCheckView(ctypes.byref(view))
            checks[f'capture{len(capture_reports)}_layer{layer}_scene_scroll_mismatch_accepted'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
            cx, cy = ctypes.c_int(), ctypes.c_int()
            checks[f'capture{len(capture_reports)}_layer{layer}_scene_keeps_wram_camera'] = (
                dll.FoundationFieldCamera(layer, ctypes.byref(cx), ctypes.byref(cy)) and
                [cx.value, cy.value] == layers[layer]['camera'])
            view.hscroll[layer], view.vscroll[layer] = saved_scroll[0][layer], saved_scroll[1][layer]
        checks[f'capture{len(capture_reports)}_reeligible_after_controls'] = bool(dll.FoundationFieldCheckView(ctypes.byref(view)))
        checks['invalid_layer_rejected'] = not dll.FoundationFieldResolve(-1, 0, 0, ctypes.byref(out_word)) and not dll.FoundationFieldResolve(2, 0, 0, ctypes.byref(out_word))
        checks['null_result_rejected'] = not dll.FoundationFieldResolve(0, 0, 0, None)
        checks[f'capture{len(capture_reports)}_input_files_unchanged'] = before == {k: digest(p.read_bytes()) for k, p in inputs.items()}
        capture_reports.append({'prefix': str(prefix.resolve()), 'input_hashes': before, 'layers': layers})

    dll.FoundationFieldReset()
    checks['reset_invalidates_resolver'] = not dll.FoundationFieldResolve(0, 0, 0, ctypes.byref(out_word))
    checks['truncated_image_rejected'] = not dll.FoundationFieldBind(rom_buffer, len(rom) - 1)
    changed = bytearray(rom)
    changed[0x10] ^= 1
    changed_buffer = (ctypes.c_uint8 * len(changed)).from_buffer_copy(changed)
    checks['changed_rom_identity_rejected'] = not dll.FoundationFieldBind(changed_buffer, len(changed))
    checks['reject_rom_keeps_resolver_inactive'] = not dll.FoundationFieldResolve(0, 0, 0, ctypes.byref(out_word))
    checks['clean_rebind_after_reject'] = bool(dll.FoundationFieldBind(rom_buffer, len(rom)))
    checks['rom_buffer_not_mutated'] = bytes(rom_buffer) == rom
    checks['rom_file_not_mutated'] = digest(rom_path.read_bytes()) == ROM_SHA256
    report = {'status': 'pass' if all(checks.values()) else 'fail', 'checks': checks,
              'compile_command': command, 'library_sha256': digest(library.read_bytes()),
              'authored_source_hashes': {p.name: digest(p.read_bytes()) for p in
                                        [authored / 'foundation_field.c', authored / 'foundation_field.h']},
              'rom_sha256': ROM_SHA256, 'captures': capture_reports,
              'center_compared': sum(l['comparisons']['center']['compared'] for r in capture_reports for l in r['layers']),
              'full_map_compared': full_compared, 'boundary_compared': boundary_compared,
              'limits': ['Standalone same C core, live PPU adapter not executed here',
                         'No gameplay or installed binary changed by this checker',
                         'Only checked scene-5 map contract, not actor visibility or whole-game widescreen',
                         'Reads captured original words, no external HD artwork or animation identity proof']}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(output / 'report.json')
    print(json.dumps({'status': report['status'], 'center_compared': report['center_compared'],
                      'full_map_compared': full_compared, 'boundary_compared': boundary_compared,
                      'failed_checks': [k for k, value in checks.items() if not value]}))
    return report['status'] == 'pass'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/inputs/clean-usa.sfc')
    parser.add_argument('--capture', type=Path, action='append')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    captures = args.capture or [ROOT / 'local/runs/likado-east-a/dump/east',
                               ROOT / 'local/runs/scroll-pacing-20261009-102819/walk-enhanced/dump/end']
    output = args.output or ROOT / 'local/runs' / ('field-resolver-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    try:
        return 0 if run(args.rom, captures, output) else 1
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f'Field resolver check refused: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
