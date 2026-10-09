"""Qualify the standalone native map resolver against independent ROM decoding.

Natural copied snapshots, full original grids, boundaries, cold/cache switches,
refusal guards and explicitly synthetic host-only story-flag adapters. No game
launch, original ROM mutation, owner save change or campaign certification.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import json
import os
import shutil
import subprocess

from inspect_foundation_maps import OriginalMaps, ROOT, ROM_SHA256, inspect, sha
from check_foundation_field_resolver import View

DEFAULT_PREFIXES = [
    'local/runs/menu-fast-first/field',
    'local/runs/sonya-talk/dump/sonya-talk',
    'local/runs/status-original-control/dump/field',
    'local/runs/patch-david/dump/david',
    'local/runs/sprite-limits-20261009-122344/town-1/dump/before',
    'local/runs/presentation-20261009-125502/field-wide/dump/end',
    'local/runs/actor-wide-20261009-133859/sweep-on/dump/entered',
    'local/runs/actor-wide-20261009-133859/sweep-on/dump/further',
]


def make_view(wram, regs):
    buffer = (ctypes.c_uint8 * len(wram)).from_buffer_copy(wram)
    view = View(buffer, len(wram), regs['inidisp'], regs['bgmode'], regs['mosaic'],
                regs['setini'], (ctypes.c_uint8 * 4)(*regs['bgsc']), regs['tm'], regs['ts'],
                regs['bg_tile_adr'], (ctypes.c_uint16 * 2)(*regs['hscroll'][:2]),
                (ctypes.c_uint16 * 2)(*regs['vscroll'][:2]))
    return buffer, view


def expected(maps, wram, layer, px, py, observed=None):
    wr = lambda a, n=1: int.from_bytes(wram[a:a + n], 'little')
    width, height = wram[0x46d + layer * 2:0x46f + layer * 2]
    grid, cell, tile = (wr(a + layer * 3, 3) for a in (0x513, 0x506, 0x500))
    attr = wr((0x537, 0x55c)[layer], 3)
    if wram[0x407]:
        px %= width * 256
        py %= height * 256
    metatile = 0
    if 0 <= px < width * 256 and 0 <= py < height * 256:
        segment = maps.read(grid + 2 * ((py // 256) * width + px // 256), 2)
        pointer = maps.tables['segments'][segment]
        cell_id = maps.read(pointer + ((py >> 5) & 7) * 8 + ((px >> 5) & 7))
        metatile = maps.read(cell + cell_id * 4 + ((py >> 4) & 1) * 2 + ((px >> 4) & 1))
        metatile = maps.conditional(wram, attr, metatile, px, py,
                                     observed if observed is not None else set())
    return maps.read(tile + metatile * 8 + ((py >> 3) & 1) * 4 + ((px >> 3) & 1) * 2, 2)


def run(rom_path, prefixes, output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'local').resolve()) or output.exists():
        raise ValueError('Choose a fresh private output directory under local/')
    maps = OriginalMaps(rom_path.read_bytes())
    output.mkdir(parents=True)
    authored = ROOT / 'native/foundation/src'
    runtime = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    configured = Path(r'C:\Users\crono\.local\share\retcomm\toolchains\cmake-clang-v1\latest\bin\clang.exe')
    compiler = str(configured) if configured.exists() else shutil.which('clang')
    if not compiler:
        raise ValueError('Standalone C compiler required')
    library = output / ('map-resolver.dll' if os.name == 'nt' else 'map-resolver.so')
    sources = [authored / 'foundation_field.c', authored / 'foundation_field.h']
    source_hashes = {p.name: sha(p.read_bytes()) for p in sources}
    command = [compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared',
               '-DFOUNDATION_FIELD_STANDALONE', '-I' + str(authored), '-I' + str(runtime),
               str(sources[0]), str(runtime / 'sha256.c'), '-o', str(library)]
    if os.name != 'nt':
        command.insert(1, '-fPIC')
    result = subprocess.run(command, capture_output=True, text=True)
    (output / 'compile.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise ValueError('Standalone compile failed: ' + result.stderr)
    dll = ctypes.CDLL(str(library))
    for name in ('FoundationFieldCheckView', 'FoundationFieldCheckSceneView'):
        getattr(dll, name).argtypes = [ctypes.POINTER(View)]
        getattr(dll, name).restype = ctypes.c_int
    dll.FoundationFieldBind.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    dll.FoundationFieldBind.restype = ctypes.c_int
    dll.FoundationFieldResolve.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(ctypes.c_uint16)]
    dll.FoundationFieldResolve.restype = ctypes.c_int
    dll.FoundationFieldLayerActive.argtypes = [ctypes.c_int]
    dll.FoundationFieldLayerActive.restype = ctypes.c_int
    dll.FoundationFieldReset.argtypes = []
    dll.FoundationFieldReset.restype = None
    rom_buffer = (ctypes.c_uint8 * len(maps.rom)).from_buffer_copy(maps.rom)
    value = ctypes.c_uint16()
    checks = {}
    full_count = edge_count = center_count = 0
    reports = []
    def resolve(layer, x, y):
        accepted = dll.FoundationFieldResolve(layer, x, y, ctypes.byref(value))
        return value.value if accepted else None
    checks['before_bind_inactive'] = resolve(0, 0, 0) is None
    checks['original_rom_binds'] = bool(dll.FoundationFieldBind(rom_buffer, len(maps.rom)))
    snapshots = []
    for index, prefix in enumerate(prefixes):
        report = inspect(maps, prefix)
        wram = Path(str(prefix) + '.wram.bin').read_bytes()
        regs = json.loads(Path(str(prefix) + '.regs.json').read_text())
        vram = Path(str(prefix) + '.vram.bin').read_bytes()
        buffer, view = make_view(wram, regs)
        snapshots.append((wram, regs))
        tag = f'capture{index}_scene{report["scene"]}'
        strict_matches = all(
            regs[k][layer] == (int.from_bytes(wram[at:at + 2], 'little') & 1023)
            for layer in range(2) for k, at in
            (('hscroll', 0x2ad + layer * 4), ('vscroll', 0x2af + layer * 4)))
        checks[tag + '_strict_scroll_contract'] = bool(dll.FoundationFieldCheckView(ctypes.byref(view))) == strict_matches
        checks[tag + '_scene_eligible'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        counts = []
        for layer in range(2):
            active = bool(wram[0x50c + layer])
            checks[tag + f'_layer{layer}_active_contract'] = bool(dll.FoundationFieldLayerActive(layer)) == active
            if not active:
                checks[tag + f'_layer{layer}_inactive_declines'] = resolve(layer, 0, 0) is None
                continue
            lr = report['layers'][layer]
            cx, cy = lr['raster_world']
            mismatch = total = 0
            for ty in range(cy // 8, (cy + 223) // 8 + 1):
                for tx in range(cx // 8, (cx + 255) // 8 + 1):
                    native = resolve(layer, tx * 8, ty * 8)
                    rx, ry = tx % 64, ty % 32
                    offset = (0x9000, 0xb000)[layer] + rx // 32 * 2048 + (ry * 32 + rx % 32) * 2
                    original = int.from_bytes(vram[offset:offset + 2], 'little')
                    mismatch += native != original or native != expected(maps, wram, layer, tx * 8, ty * 8)
                    total += 1
            center_count += total
            checks[tag + f'_layer{layer}_center_exact'] = mismatch == 0
            width, height = lr['dimensions_segments']
            failures = 0
            for py in range(0, height * 256, 8):
                for px in range(0, width * 256, 8):
                    failures += resolve(layer, px, py) != expected(maps, wram, layer, px, py)
                    full_count += 1
            checks[tag + f'_layer{layer}_full_grid_exact'] = failures == 0
            xs = [-2147483648, -width * 256 - 9, -width * 256, -72, -17, -1, 0, 7,
                  8, 255, width * 256 - 1, width * 256, width * 512 + 7, 2147483647]
            ys = [-2147483648, -height * 256 - 9, -height * 256, -17, -1, 0, 7, 8,
                  255, height * 256 - 1, height * 256, height * 512 + 7, 2147483647]
            failures = 0
            for px in xs:
                for py in ys:
                    failures += resolve(layer, px, py) != expected(maps, wram, layer, px, py)
                    edge_count += 1
            checks[tag + f'_layer{layer}_period_boundaries_exact'] = failures == 0
            counts.append({'layer': layer, 'center_compared': total,
                           'full_grid_compared': width * height * 1024})
        for layer in range(2):
            old = view.hscroll[layer]
            view.hscroll[layer] = (old + 1) & 1023
            checks[tag + f'_layer{layer}_strict_latch_refused'] = not dll.FoundationFieldCheckView(ctypes.byref(view))
            checks[tag + f'_layer{layer}_scene_latch_accepted'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
            view.hscroll[layer] = old
        for name, at, mutation in [('battle', 0x20, 5), ('bad_scene', 0x40e, 255),
                                   ('grid_not_member', 0x513, 1), ('zero_width', 0x46d, 0),
                                   ('dimension_above_nibble', 0x46d, 16), ('bad_cells', 0x506, 1),
                                   ('bad_tiles', 0x500, 1), ('unpaired_attributes', 0x537, 1),
                                   ('direct_loading', 0x531, 128)]:
            old = buffer[at]
            buffer[at] = mutation
            checks[tag + '_refuse_' + name] = not dll.FoundationFieldCheckSceneView(ctypes.byref(view)) and resolve(0, 0, 0) is None
            buffer[at] = old
        for name, field, mutation in [('forced_blank', 'inidisp', 128), ('wrong_mode', 'bgmode', 1),
                                       ('visible_mosaic', 'mosaic', 16), ('interlace', 'setini', 1),
                                       ('wrong_main_screen', 'tm', 0), ('BG_subscreen', 'ts', 1),
                                       ('wrong_char_base', 'bg_tile_adr', 0), ('short_ram', 'ram_size', 1)]:
            old = getattr(view, field)
            setattr(view, field, mutation)
            checks[tag + '_refuse_' + name] = not dll.FoundationFieldCheckSceneView(ctypes.byref(view))
            setattr(view, field, old)
        checks[tag + '_strict_after_controls'] = bool(dll.FoundationFieldCheckView(ctypes.byref(view))) == strict_matches
        checks[tag + '_scene_reeligible_after_controls'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        checks[tag + '_ram_unchanged'] = bytes(buffer) == wram
        checks[tag + '_input_files_unchanged'] = report['input_sha256'] == {
            kind: sha(Path(str(prefix) + '.' + kind).read_bytes()) for kind in report['input_sha256']}
        dll.FoundationFieldReset()
        checks[tag + '_cold_invalidates'] = resolve(0, 0, 0) is None
        checks[tag + '_cold_rebind'] = bool(dll.FoundationFieldBind(rom_buffer, len(maps.rom))) and bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        reports.append({'prefix': str(prefix.resolve()), 'scene': report['scene'],
                        'input_sha256': report['input_sha256'], 'layers': counts})
    # Resources are switched without reset, exercising cache invalidation across
    # eligible scenes rather than merely creating a fresh DLL for every scene.
    for index in (0, 2, 4, 5, 0):
        wram, regs = snapshots[index]
        buffer, view = make_view(wram, regs)
        checks[f'transition_{index}_{len(checks)}'] = bool(dll.FoundationFieldCheckView(ctypes.byref(view))) and resolve(0, 0, 0) == expected(maps, wram, 0, 0, 0)
    bad_prefix = ROOT / 'local/runs/loading-desktop-20261009-125638/natural-original/dump/door'
    bad_ram = Path(str(bad_prefix) + '.wram.bin').read_bytes()
    bad_regs = json.loads(Path(str(bad_prefix) + '.regs.json').read_text())
    bad_buffer, bad_view = make_view(bad_ram, bad_regs)
    bad_view.inidisp = 15  # Isolate provenance refusal from the natural fade.
    bad_report = inspect(maps, bad_prefix)
    checks['transition_original_centers_still_exact'] = all(l['center_exact'] for l in bad_report['layers'])
    checks['fullbright_stale_scene_resource_tuple_refused'] = not dll.FoundationFieldCheckSceneView(ctypes.byref(bad_view))
    # Host-synthetic flags over genuine original matching conditional records.
    # These are adapter semantics checks, never claims of a campaign scene visit.
    synthetic = []
    world_ram, world_regs = next(s for s in snapshots if int.from_bytes(s[0][0x40e:0x410], 'little') == 0)
    pointer = int.from_bytes(world_ram[0x456:0x459], 'little')
    for offset in range(0, 251, 5):
        key = maps.read(pointer + offset, 2)
        if key == 65535:
            break
        threshold = maps.read(pointer + offset + 2)
        selector = maps.read(pointer + offset + 3)
        if not selector < 0x78 or threshold == 255:
            continue
        px, py = (key >> 8) * 16, (key & 255) * 16
        for stage in (max(0, threshold - 1), threshold, min(255, threshold + 1)):
            for enabled in (False, True):
                ram = bytearray(world_ram)
                ram[0x5372] = stage
                flag_at, mask = 0x5360 + bool(selector & 8), 128 >> (selector & 7)
                ram[flag_at] = ram[flag_at] | mask if enabled else ram[flag_at] & ~mask
                buffer, view = make_view(ram, world_regs)
                exact = bool(dll.FoundationFieldCheckView(ctypes.byref(view))) and all(
                    resolve(0, px + dx, py + dy) == expected(maps, ram, 0, px + dx, py + dy)
                    for dx, dy in ((0, 0), (8, 0), (0, 8), (8, 8)))
                tag = f'synthetic_F_record{offset}_stage{stage}_flag{int(enabled)}'
                checks[tag] = exact and bytes(buffer) == ram
                synthetic.append({'kind': 'F', 'host_only': True, 'pointer': f'{pointer:06X}',
                                  'offset': offset, 'location': [px, py], 'stage': stage,
                                  'threshold': threshold, 'flag_enabled': enabled,
                                  'native_word': resolve(0, px, py), 'exact': exact})
    # Original scene14 primary resources plus original E-table0 record provide
    # positive matched E semantics. Only disposable host RAM adapter changes.
    variant = maps.scene_primary_variants(14)[0]
    ram = bytearray(world_ram)
    def put(at, value, count):
        ram[at:at + count] = value.to_bytes(count, 'little')
    put(0x40e, 14, 2)
    put(0x513, 0x090000 | maps.tables['maps'][variant['map_index']], 3)
    put(0x506, 0x0a0000 | maps.tables['cells'][variant['cell_index']], 3)
    put(0x500, 0x030000 | maps.tables['tiles'][variant['tile_attribute_index']], 3)
    put(0x537, 0x090000 | maps.tables['attributes'][variant['tile_attribute_index']], 3)
    ram[0x46d:0x46f] = bytes(variant['dimensions'])
    ram[0x407], ram[0x50c], ram[0x50d] = variant['wrap'], 128, 0
    pointer = 0x080000 | maps.read(0x08e900, 2)
    put(0x453, pointer, 3)
    key, flag = maps.read(pointer, 2), maps.read(pointer + 2, 2)
    px, py = (key >> 8) * 16, (key & 255) * 16
    flag_at, mask = 0x53f9 + ((flag >> 3) & 255), 128 >> (flag & 7)
    results = []
    for enabled in (False, True):
        ram[flag_at] = ram[flag_at] | mask if enabled else ram[flag_at] & ~mask
        buffer, view = make_view(ram, world_regs)
        exact = bool(dll.FoundationFieldCheckView(ctypes.byref(view))) and all(
            resolve(0, px + dx, py + dy) == expected(maps, ram, 0, px + dx, py + dy)
            for dx, dy in ((0, 0), (8, 0), (0, 8), (8, 8)))
        results.append(resolve(0, px, py))
        checks[f'synthetic_E_matched_flag{int(enabled)}'] = exact and bytes(buffer) == ram
        synthetic.append({'kind': 'E', 'host_only': True, 'scene_resource_adapter': 14,
                          'pointer': f'{pointer:06X}', 'location': [px, py],
                          'flag_index': flag, 'flag_enabled': enabled, 'exact': exact})
    checks['synthetic_E_positive_word_changes'] = results[0] != results[1] and None not in results
    checks['synthetic_F_positive_cases_present'] = len([s for s in synthetic if s['kind'] == 'F']) > 0
    equal_stage_pairs = {}
    for sample in synthetic:
        if sample['kind'] == 'F' and sample['stage'] == sample['threshold']:
            equal_stage_pairs.setdefault(sample['offset'], {})[sample['flag_enabled']] = sample['native_word']
    checks['synthetic_F_flag_changes_native_word_at_equal_stage'] = bool(equal_stage_pairs) and all(
        pair.get(False) is not None and pair.get(True) is not None and pair[False] != pair[True]
        for pair in equal_stage_pairs.values())
    checks['invalid_layer_declines'] = resolve(-1, 0, 0) is None and resolve(2, 0, 0) is None
    checks['null_result_declines'] = not dll.FoundationFieldResolve(0, 0, 0, None)
    dll.FoundationFieldReset()
    checks['wrong_image_size_refused'] = not dll.FoundationFieldBind(rom_buffer, len(maps.rom) - 1)
    unrelated_image = (ctypes.c_uint8 * len(maps.rom))()
    checks['unrelated_zero_image_identity_refused'] = not dll.FoundationFieldBind(unrelated_image, len(maps.rom))
    checks['original_rebind_after_identity_failure'] = bool(dll.FoundationFieldBind(rom_buffer, len(maps.rom)))
    checks['original_rom_buffer_unchanged'] = bytes(rom_buffer) == maps.rom
    checks['original_rom_file_unchanged'] = sha(rom_path.read_bytes()) == ROM_SHA256
    checks['source_did_not_change_during_proof'] = source_hashes == {p.name: sha(p.read_bytes()) for p in sources}
    report = {'status': 'pass' if all(checks.values()) else 'fail', 'checks': checks,
              'compile_command': command, 'library_sha256': sha(library.read_bytes()),
              'authored_source_hashes': source_hashes, 'checker_sha256': sha(Path(__file__).read_bytes()),
              'independent_inspector_sha256': sha((ROOT / 'tools/inspect_foundation_maps.py').read_bytes()),
              'rom_sha256': ROM_SHA256, 'captures': reports, 'synthetic_host_adapters': synthetic,
              'center_compared': center_count, 'full_grid_compared': full_count,
              'boundary_compared': edge_count,
              'limits': ['Standalone same C core; live PPU adapter/compositor not executed',
                         'Synthetic flags/resources test adapters, not observed campaign progression',
                         'Wrap boundaries compare native/independent original map data, not natural world-edge gameplay',
                         'No owner save, installation or original ROM changed']}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(output / 'report.json'), 'status': report['status'],
                      'checks': len(checks), 'center_compared': center_count,
                      'full_grid_compared': full_count, 'boundary_compared': edge_count,
                      'failed_checks': [k for k, v in checks.items() if not v]}))
    return report['status'] == 'pass'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/inputs/clean-usa.sfc')
    parser.add_argument('--prefix', type=Path, action='append')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    prefixes = args.prefix or [ROOT / p for p in DEFAULT_PREFIXES]
    output = args.output or ROOT / ('local/runs/map-resolver-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    return 0 if run(args.rom, prefixes, output) else 1


if __name__ == '__main__':
    raise SystemExit(main())
