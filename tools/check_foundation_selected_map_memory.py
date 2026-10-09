"""Windows guard pages + UBSan traps for the PRIVATE selected-map prototype.

All409 authentic selected-variant host views use original table pointers.
No game launch, campaign claim, source edit, ROM mutation or owner save write.
"""
from pathlib import Path
import argparse
import ctypes as C
import itertools
import json
import subprocess
import sys

from inspect_foundation_maps import OriginalMaps, ROOT
from inspect_foundation_secondary_maps import scene_records, selected_record, parse_stream
from check_foundation_secondary_provenance import resources, write
from check_foundation_map_resolver import make_view, expected
from check_foundation_field_resolver import View


def sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authentic_states(maps):
    """Reuse the provenance proof's actual stage/bit decision construction."""
    data = bytearray(131072)
    cases = {}
    for scene in range(337):
        records = scene_records(maps, scene)
        for stage in range(256):
            for flags in [0, 255]:
                data[0x5360:0x5372] = bytes([flags]) * 18
                data[0x5372] = stage
                record = selected_record(records, data)
                cases.setdefault((scene, record['record']),
                    (record['stream'], stage, bytes(data[0x5360:0x5372])))
        if not all((scene, record['record']) in cases for record in records):
            bits = sorted({r['operands'][1] for r in records
                           if r['selector'] == 0 and r['operands'][1] < 0x78})
            stages = sorted({r['operands'][0] for r in records if r['selector'] != 255})
            for stage in stages:
                for pattern in itertools.product([0, 1], repeat=len(bits)):
                    data[0x5360:0x5372] = bytes(18)
                    data[0x5372] = stage
                    for bit, enabled in zip(bits, pattern):
                        if enabled:
                            data[0x5360 + bool(bit & 8)] |= 128 >> (bit & 7)
                    record = selected_record(records, data)
                    cases.setdefault((scene, record['record']),
                        (record['stream'], stage, bytes(data[0x5360:0x5372])))
    assert len(cases) == 409
    return cases


def worker(args):
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.SetErrorMode.argtypes = [C.c_uint32]
    kernel.SetErrorMode.restype = C.c_uint32
    kernel.SetErrorMode(3)
    kernel.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    kernel.VirtualAlloc.restype = C.c_void_p
    kernel.VirtualProtect.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.POINTER(C.c_uint32)]
    kernel.VirtualProtect.restype = C.c_int
    kernel.VirtualFree.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32]
    kernel.VirtualFree.restype = C.c_int
    allocations = []

    def guarded(size):
        assert size % 4096 == 0
        base = kernel.VirtualAlloc(None, size + 8192, 0x3000, 4)
        assert base, C.get_last_error()
        old = C.c_uint32()
        assert kernel.VirtualProtect(base, 4096, 1, C.byref(old))
        assert kernel.VirtualProtect(base + 4096 + size, 4096, 1, C.byref(old))
        allocations.append(base)
        return (C.c_uint8 * size).from_address(base + 4096)

    maps = OriginalMaps(args.rom.read_bytes())
    dll = C.CDLL(str(args.output / 'selected-map-memory.dll'))
    reference = C.CDLL(str(args.output / 'qualified-reference.dll'))
    pointer = C.POINTER(C.c_uint8)
    dll.FoundationFieldBind.argtypes = [pointer, C.c_size_t]
    for name in ['FoundationFieldCheckView', 'FoundationFieldCheckSceneView']:
        getattr(dll, name).argtypes = [C.POINTER(View)]
    dll.FoundationFieldResolve.argtypes = [C.c_int, C.c_int, C.c_int, C.POINTER(C.c_uint16)]
    dll.FoundationFieldReset.argtypes = []
    dll.FoundationFieldPrivateSelected.argtypes = [pointer, C.c_size_t]
    dll.FoundationFieldPrivateSelected.restype = C.c_uint
    reference.FoundationFieldBind.argtypes = [pointer, C.c_size_t]
    reference.FoundationFieldCheckView.argtypes = [C.POINTER(View)]
    rom, ram = guarded(len(maps.rom)), guarded(131072)
    C.memmove(rom, maps.rom, len(maps.rom))
    assert dll.FoundationFieldBind(rom, len(maps.rom))
    assert reference.FoundationFieldBind(rom, len(maps.rom))
    regs = dict(inidisp=15, bgmode=9, mosaic=0, setini=0,
                bgsc=[0x49, 0x59, 0x51, 0], tm=0x17, ts=0,
                bg_tile_adr=0x0400, hscroll=[0, 0], vscroll=[0, 0])
    counts = dict(selected_views=0, active_layers=0, extreme_pairs=0,
                  malformed_refusals=0, invalid_arguments=0, recoveries=0,
                  retained_E_flag_phases=0, reset_reference_cache_rebuilds=0,
                  decoder_accepted_views=0, existing_decoder_declined_views=0,
                  source_backed_attribute_gate_recoveries=0, literal_adjacent_attribute_words=0)
    coordinates = [-2147483648, -2147483647, -65537, -4097, -1, 0, 4097, 65537, 2147483647]

    def resolve(layer, x, y):
        value = C.c_uint16(0x5aa5)
        ok = dll.FoundationFieldResolve(layer, x, y, C.byref(value))
        return bool(ok), value.value

    def reject(view):
        assert not dll.FoundationFieldCheckSceneView(C.byref(view))
        assert resolve(0, 0, 0) == (False, 0x5aa5)

    cases = []
    for (scene, record), (start, stage, story) in authentic_states(maps).items():
        data = bytearray(131072)
        write(data, 0x40e, scene, 2)
        data[0x5360:0x5372] = story
        data[0x5372] = stage
        stream = parse_stream(maps, start)
        resources(maps, data, stream)
        if not stream['flags'] & 32:
            # Authenticate an actual original retained list; loader history is
            # explicitly host synthetic. Scenes216/221 use matching E-list47.
            write(data, 0x453, 0x080000 | maps.read(0x08e900 + 47 * 2, 2), 3)
        _, view = make_view(data, regs)
        view.ram = C.cast(ram, pointer)
        C.memmove(ram, bytes(data), len(data))
        assert dll.FoundationFieldPrivateSelected(ram, len(data)) == start
        eligible = bool(dll.FoundationFieldCheckView(C.byref(view)))
        existing_eligible = bool(reference.FoundationFieldCheckView(C.byref(view)))
        if eligible != existing_eligible:
            assert eligible and not existing_eligible and scene in [1, 2] and data[0x452] == 130, ('unexpected decoder acceptance difference', scene, record, start)
            counts['source_backed_attribute_gate_recoveries'] += 1
        counts['decoder_accepted_views' if eligible else 'existing_decoder_declined_views'] += 1
        counts['selected_views'] += 1
        for layer in range(2):
            if not data[0x50c + layer]:
                assert resolve(layer, -2147483648, 2147483647) == (False, 0x5aa5)
                continue
            if not eligible:
                for x in coordinates:
                    for y in coordinates:
                        assert resolve(layer, x, y) == (False, 0x5aa5)
                continue
            counts['active_layers'] += 1
            for x in coordinates:
                for y in coordinates:
                    ok, value = resolve(layer, x, y)
                    assert ok and value == expected(maps, data, layer, x, y), ('coordinate', scene, layer, x, y, value)
                    counts['extreme_pairs'] += 1
        # Resource guards must reject before reading beyond exact guest/ROM.
        bad = [(0x40e, 337, 2), (0x40e, 65535, 2), (0x50c, 0, 1),
               (0x452, 255, 1), (0x456, 0xffffff, 3)]
        for layer in range(2):
            if not data[0x50c + layer]:
                continue
            bad += [(at, value, 1) for at in (0x46d + layer * 2, 0x46e + layer * 2)
                    for value in (0, 16, 255)]
            addresses = [0x513 + layer * 3, 0x506 + layer * 3, 0x500 + layer * 3,
                         0x55c if layer else 0x537]
            bad += [(at, value, 3) for at in addresses for value in (0, 0x087fff, 0x30ffff, 0xffffff)]
        for at, value, size in bad:
            C.memmove(ram, bytes(data), len(data))
            for i in range(size):
                ram[at + i] = value >> (i * 8) & 255
            reject(view)
            counts['malformed_refusals'] += 1
            C.memmove(ram, bytes(data), len(data))
            assert bool(dll.FoundationFieldCheckView(C.byref(view))) == eligible
            counts['recoveries'] += 1
        for size in [0, 1, 131071, 131073]:
            view.ram_size = size
            reject(view)
            counts['invalid_arguments'] += 1
        view.ram_size = len(data)
        view.ram = None
        reject(view)
        view.ram = C.cast(ram, pointer)
        assert bool(dll.FoundationFieldCheckView(C.byref(view))) == eligible
        for layer in [-2147483648, -1, 2, 2147483647]:
            assert resolve(layer, -2147483648, 2147483647) == (False, 0x5aa5)
            counts['invalid_arguments'] += 1
        assert not dll.FoundationFieldResolve(0, 0, 0, None)
        if scene in [1, 2] and data[0x452] == 130:
            desc = stream['secondary']
            assert desc['attributes'] == 0x098910 and maps.read(0x0989e4) == 0
            point = None
            width, height = desc['dimensions']
            for y in range(height * 16):
                for x in range(width * 16):
                    px, py = x * 16, y * 16
                    segment = maps.read(desc['grid'] + 2 * ((py // 256) * width + px // 256), 2)
                    cell = maps.read(maps.tables['segments'][segment] + ((py >> 5) & 7) * 8 + ((px >> 5) & 7))
                    mid = maps.read(desc['cells'] + cell * 4 + ((py >> 4) & 1) * 2 + ((px >> 4) & 1))
                    if mid == 212:
                        point = px, py
                        break
                if point:
                    break
            assert point, 'Original secondary metatile212 must be present'
            for (dx, dy), literal in zip([(0, 0), (8, 0), (0, 8), (8, 8)], [0x1e04, 0x1e04, 0x1e47, 0x1e47]):
                assert resolve(1, point[0] + dx, point[1] + dy) == (True, literal)
                assert literal == expected(maps, data, 1, point[0] + dx, point[1] + dy)
                counts['literal_adjacent_attribute_words'] += 1
        if scene in [216, 221]:
            address, mask = 0x53f9 + 18, 128
            for phase in [0, 1]:
                ram[address] = data[address] = mask if phase else 0
                assert dll.FoundationFieldCheckView(C.byref(view))
                for dx, dy in [(0, 0), (8, 0), (0, 8), (8, 8)]:
                    assert resolve(0, 928 + dx, 544 + dy) == (True, expected(maps, data, 0, 928 + dx, 544 + dy))
                counts['retained_E_flag_phases'] += 1
        dll.FoundationFieldReset()
        assert resolve(0, 0, 0) == (False, 0x5aa5)
        assert not dll.FoundationFieldCheckView(C.byref(view))
        assert dll.FoundationFieldBind(rom, len(maps.rom))
        assert bool(dll.FoundationFieldCheckView(C.byref(view))) == eligible
        counts['reset_reference_cache_rebuilds'] += 1
        # Resolve a retained coordinate again after reference-membership reset.
        if scene in [216, 221]:
            assert resolve(0, 928, 544) == (True, expected(maps, data, 0, 928, 544))
        assert bytes(ram) == bytes(data), ('guest mutation', scene)
        cases.append(dict(scene=scene, record=record, stream=start, stage=stage,
                          secondary_mode=data[0x452], decoder_eligible=eligible,
                          existing_decoder_eligible=existing_eligible))
    dll.FoundationFieldReset()
    protected = C.cast(allocations[0], pointer)
    for size in [0, 1, len(maps.rom) - 1, len(maps.rom) + 1]:
        assert not dll.FoundationFieldBind(protected, size)
        counts['invalid_arguments'] += 1
    assert not dll.FoundationFieldBind(None, len(maps.rom))
    assert not dll.FoundationFieldCheckView(None)
    for base in allocations:
        assert kernel.VirtualFree(base, 0, 0x8000)
    (args.output / 'worker-report.json').write_text(json.dumps(dict(passed=True, counts=counts, cases=cases), indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return 0
    args.output = args.output.resolve()
    args.source_dir = args.source_dir.resolve()
    args.source_dir.relative_to((ROOT / 'local').resolve())
    args.output.relative_to((ROOT / 'local').resolve())
    if args.output.exists():
        parser.error('Choose a fresh private directory')
    args.output.mkdir(parents=True)
    runtime = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    tracked = [args.source_dir / 'foundation_field.c', args.source_dir / 'foundation_field.h',
               ROOT / 'native/foundation/src/foundation_field.c',
               ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/src/foundation_field.c',
               runtime / 'sha256.c']
    before = {str(p): sha(p) for p in tracked}
    assert before[str(tracked[0])] == 'b58b866ebb82161a7ea6ecb3af0eb4402f69f8b910c420feb4dbfda2ee59d4ae'
    compiler = Path.home() / '.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe'
    command = [str(compiler), '-std=c11', '-O1', '-Wall', '-Wextra', '-Werror', '-shared',
               '-fsanitize=undefined', '-fsanitize-trap=all', '-DFOUNDATION_FIELD_STANDALONE',
               '-I' + str(args.source_dir), '-I' + str(runtime), str(tracked[0]),
               str(runtime / 'sha256.c'), '-o', str(args.output / 'selected-map-memory.dll')]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (args.output / 'compile.log').write_text(built.stdout + built.stderr, encoding='utf-8')
    assert not built.returncode, built.stderr
    reference_command = command.copy()
    reference_command[reference_command.index('-I' + str(args.source_dir))] = '-I' + str(ROOT / 'native/foundation/src')
    reference_command[reference_command.index(str(tracked[0]))] = str(ROOT / 'native/foundation/src/foundation_field.c')
    reference_command[-1] = str(args.output / 'qualified-reference.dll')
    reference_build = subprocess.run(reference_command, capture_output=True, text=True, timeout=30)
    (args.output / 'reference-compile.log').write_text(reference_build.stdout + reference_build.stderr, encoding='utf-8')
    assert not reference_build.returncode, reference_build.stderr
    child = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker',
                            '--rom', str(args.rom.resolve()), '--source-dir', str(args.source_dir),
                            '--output', str(args.output)], capture_output=True, text=True, timeout=180)
    (args.output / 'worker.log').write_text(child.stdout + child.stderr, encoding='utf-8')
    result_path = args.output / 'worker-report.json'
    report = json.loads(result_path.read_text()) if result_path.exists() else {}
    report.update(child_exit_code=child.returncode, source_hashes=before,
                  sources_unchanged=all(sha(p) == before[str(p)] for p in tracked),
                  checker_sha256=sha(Path(__file__)), guard_pages='PAGE_NOACCESS at both ends of exact ROM and WRAM',
                  undefined_behavior_traps=True,
                  limits='Authentic selected host views; retained loader history synthetic; no campaign/gameplay/timing/audio claim')
    report['passed'] = bool(report.get('passed') and child.returncode == 0 and report['sources_unchanged'])
    (args.output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: report.get(key) for key in ['passed', 'child_exit_code', 'counts', 'sources_unchanged']}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
