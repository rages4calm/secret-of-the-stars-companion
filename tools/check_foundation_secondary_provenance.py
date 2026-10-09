"""Qualify a PRIVATE field provenance prototype; never install or edit native sources.

Original stream grammar and selected-resource tests are host synthetic. Copied
natural captures retain separate exact center-word evidence. Reports stay local.
"""
from pathlib import Path
import argparse
import ctypes
import json
import itertools
import os
import subprocess

from inspect_foundation_maps import OriginalMaps, ROOT, inspect, sha
from inspect_foundation_secondary_maps import parse_stream, scene_records, selected_record
from check_foundation_map_resolver import make_view, expected
from check_foundation_field_resolver import View


def write(ram, address, value, size=1):
    ram[address:address + size] = int(value).to_bytes(size, 'little')


def resources(maps, ram, stream):
    """Host metadata fixture with the actual original selected pointer tables."""
    ram[0x20] = 1
    ram[0x407] = stream['wrap']
    for layer in range(2):
        descriptor = stream['primary'] if not layer else stream['secondary']
        active = not layer or bool(descriptor and descriptor['active'])
        ram[0x50c + layer] = active
        if not active:
            continue  # Preserve arbitrary old inactive pointers and dimensions.
        for name, address in [('grid', 0x513), ('cells', 0x506), ('tiles', 0x500)]:
            write(ram, address + layer * 3, descriptor[name], 3)
        write(ram, 0x55c if layer else 0x537, descriptor['attributes'], 3)
        ram[0x46d + layer * 2:0x46f + layer * 2] = bytes(descriptor['dimensions'])
    ram[0x452] = stream['secondary']['mode'] if stream['secondary'] and stream['secondary']['active'] else 0
    options = {entry['name']: entry['value'] for entry in stream['optional']}
    write(ram, 0x456, 0x080000 | maps.read(0x08f600 + options.get('stage_tiles', 0) * 2, 2), 3)
    if 'flag_tiles' in options:
        write(ram, 0x453, 0x080000 | maps.read(0x08e900 + options['flag_tiles'] * 2, 2), 3)
    else:
        write(ram, 0x453, 0x08e9a0, 3)  # Demonstrate original stale inactive pointer allowance.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--clang', required=True, type=Path)
    parser.add_argument('--dump-prefix', action='append', type=Path, default=[])
    args = parser.parse_args()
    source = args.source_dir.resolve()
    source.relative_to((ROOT / 'local').resolve())
    output = args.output.resolve()
    output.relative_to((ROOT / 'local').resolve())
    if output.exists():
        raise ValueError('Choose a fresh private output directory')
    maps = OriginalMaps(args.rom.read_bytes())
    output.mkdir(parents=True)
    runtime = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    library = output / ('prototype.dll' if os.name == 'nt' else 'prototype.so')
    command = [str(args.clang), '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared',
               '-DFOUNDATION_FIELD_STANDALONE', '-I' + str(source), '-I' + str(runtime),
               str(source / 'foundation_field.c'), str(runtime / 'sha256.c'), '-o', str(library)]
    if os.name != 'nt':
        command.insert(1, '-fPIC')
    compiled = subprocess.run(command, text=True, capture_output=True)
    (output / 'compile.log').write_text(compiled.stdout + compiled.stderr, encoding='utf-8')
    if compiled.returncode:
        raise ValueError(compiled.stderr)
    dll = ctypes.CDLL(str(library))
    byte_pointer = ctypes.POINTER(ctypes.c_uint8)
    dll.FoundationFieldBind.argtypes = [byte_pointer, ctypes.c_size_t]
    dll.FoundationFieldPrivateSelected.argtypes = [byte_pointer, ctypes.c_size_t]
    dll.FoundationFieldPrivateSelected.restype = ctypes.c_uint
    dll.FoundationFieldPrivateProvenance.argtypes = [byte_pointer, ctypes.c_size_t, ctypes.c_uint]
    dll.FoundationFieldPrivateCondition.argtypes = [byte_pointer, ctypes.c_size_t,
                                                   ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
    for name in ['FoundationFieldCheckView', 'FoundationFieldCheckSceneView']:
        getattr(dll, name).argtypes = [ctypes.POINTER(View)]
    dll.FoundationFieldResolve.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(ctypes.c_uint16)]
    dll.FoundationFieldReset.argtypes = []
    rom = (ctypes.c_uint8 * len(maps.rom)).from_buffer_copy(maps.rom)
    ram = bytearray(131072)
    buffer = (ctypes.c_uint8 * len(ram)).from_buffer(ram)
    checks = {}
    checks['bind_clean'] = bool(dll.FoundationFieldBind(rom, len(maps.rom)))
    scenes = [scene_records(maps, scene) for scene in range(337)]
    starts = sorted({record['stream'] for records in scenes for record in records})
    streams = {start: parse_stream(maps, start) for start in starts}
    structure_count = 0
    for start, stream in streams.items():
        resources(maps, ram, stream)
        checks[f'original_stream_{start:06x}'] = bool(dll.FoundationFieldPrivateProvenance(buffer, len(ram), start))
        structure_count += 1
    # Enumerate actual original condition selection with live host-only WRAM.
    # Static grammar testing above bypasses selection deliberately; these do not.
    selected_states = {}
    selection_comparisons = 0
    for scene, records in enumerate(scenes):
        write(ram, 0x40e, scene, 2)
        for stage in range(256):
            for flags in [0, 255]:
                ram[0x5360:0x5372] = bytes([flags]) * 18
                ram[0x5372] = stage
                record = selected_record(records, ram)
                actual = dll.FoundationFieldPrivateSelected(buffer, len(ram))
                if actual != record['stream']:
                    raise AssertionError(('selection', scene, stage, flags, record, actual))
                selection_comparisons += 1
                key = (scene, record['record'])
                if key not in selected_states:
                    selected_states[key] = (stage, bytes(ram[0x5360:0x5372]), record['stream'])
    # Seven linked variants need mixed bits, not blanket all-set/all-clear.
    for scene, records in enumerate(scenes):
        if all((scene, record['record']) in selected_states for record in records):
            continue
        bits = sorted({record['operands'][1] for record in records
                       if record['selector'] == 0 and record['operands'][1] < 0x78})
        if len(bits) > 16:
            raise AssertionError('Unexpected original selection variable count')
        stages = sorted({record['operands'][0] for record in records if record['selector'] != 255})
        write(ram, 0x40e, scene, 2)
        for stage in stages:
            for pattern in itertools.product([0, 1], repeat=len(bits)):
                ram[0x5360:0x5372] = bytes(18)
                ram[0x5372] = stage
                for bit, enabled in zip(bits, pattern):
                    if enabled:
                        ram[0x5360 + bool(bit & 8)] |= 128 >> (bit & 7)
                record = selected_record(records, ram)
                actual = dll.FoundationFieldPrivateSelected(buffer, len(ram))
                if actual != record['stream']:
                    raise AssertionError(('mixed selection', scene, stage, pattern))
                selection_comparisons += 1
                selected_states.setdefault((scene, record['record']),
                    (stage, bytes(ram[0x5360:0x5372]), record['stream']))
    checks['all409_original_variant_links_selected'] = len(selected_states) == sum(len(r) for r in scenes)
    for (scene, record), (stage, story, start) in selected_states.items():
        write(ram, 0x40e, scene, 2)
        ram[0x5360:0x5372] = story
        ram[0x5372] = stage
        resources(maps, ram, streams[start])
        checks[f'selected_scene_{scene}_record_{record:06x}'] = bool(dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0))
        # Wrong but original-table-member BG2 resource must fail same-stream auth.
        if streams[start]['secondary'] and streams[start]['secondary']['active']:
            actual_grid = int.from_bytes(ram[0x516:0x519], 'little')
            foreign = next(0x090000 | p for p in maps.tables['maps'] if (0x090000 | p) != actual_grid)
            write(ram, 0x516, foreign, 3)
            checks[f'foreign_secondary_scene_{scene}_record_{record:06x}'] = not dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0)
            write(ram, 0x516, actual_grid, 3)
        original_stage = bytes(ram[0x456:0x459])
        write(ram, 0x456, 0x08e9a0, 3)
        checks[f'stale_stage_scene_{scene}_record_{record:06x}'] = not dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0)
        ram[0x456:0x459] = original_stage
        if any(entry['name'] == 'flag_tiles' for entry in streams[start]['optional']):
            original_flag = bytes(ram[0x453:0x456])
            wrong = next((0x080000 | maps.read(0x08e900 + i * 2, 2)) for i in range(55)
                         if (0x080000 | maps.read(0x08e900 + i * 2, 2)) != int.from_bytes(original_flag, 'little'))
            write(ram, 0x453, wrong, 3)
            checks[f'foreign_flag_scene_{scene}_record_{record:06x}'] = not dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0)
            ram[0x453:0x456] = original_flag
    # Unused scene selectors still use the actual read-only original helper.
    conditions = [(0, 4, 0), (1, 4, 0), (2, 4, 0), (3, 4, 2),
                  (4, 0, 0), (5, 0, 0), (6, 3, 2), (7, 0xaa, 0xbb)]
    condition_count = 0
    for stage in [3, 4, 5]:
        for flags in [0, 255]:
            for party in [0, 128]:
                ram[0x5360:0x5372] = bytes([flags]) * 18
                ram[0x5372] = stage
                ram[0x4b6] = party
                for selector, a, b in conditions:
                    record = {'selector': selector, 'operands': [a, b], 'stream': 1}
                    fallback = {'selector': 255, 'operands': [], 'stream': 0}
                    wanted = selected_record([record, fallback], ram)['stream']
                    actual = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), selector, a, b))
                    checks[f'condition_{condition_count}'] = actual == bool(wanted)
                    condition_count += 1
    # Literal offsets derived from original accumulator B, deliberately not
    # routed through the Python story oracle for these packed-nibble cases.
    for phase in [0, 1]:
        ram[0x5360:0x53e2] = bytes(130)
        ram[0x5372] = 4
        ram[0x5362] = 0xa0 if not phase else 0
        ram[0x53e1] = 5 if phase else 0  # FF: odd nibble255 at5362+127.
        ram[0x5363] = 7 if phase else 0  # operand b=3: low nibble3.
        checks[f'accB_selector0_FF_{phase}'] = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), 0, 4, 255)) == (not phase)
        checks[f'accB_selector1_FF_{phase}'] = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), 1, 4, 255)) == bool(phase)
        checks[f'accB_selector4_FF_{phase}'] = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), 4, 127, 3)) == bool(phase)
        checks[f'accB_selector5_FF_{phase}'] = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), 5, 127, 3)) == (not phase)
        checks[f'accB_selector6_{phase}'] = bool(dll.FoundationFieldPrivateCondition(buffer, len(ram), 6, 3, 7)) == bool(phase)
    # A bounded E/F proof uses authentic selected tables, not fabricated
    # no-match sentinels. Locate a real matching conditional coordinate.
    conditional_samples = []
    conditional_kinds = {14: 0, 15: 0}
    conditional_replacements = {14: 0, 15: 0}
    sample_regs = json.loads(Path(str(args.dump_prefix[0]) + '.regs.json').read_text())
    word_value = ctypes.c_uint16()
    for (scene, record), (stage, story, start) in selected_states.items():
        if all(count >= 12 for count in conditional_kinds.values()):
            break
        ram[:] = bytes(len(ram))
        write(ram, 0x40e, scene, 2)
        ram[0x5360:0x5372] = story
        ram[0x5372] = stage
        resources(maps, ram, streams[start])
        for kind, pointer_at, stride in [(14, 0x453, 4), (15, 0x456, 5)]:
            if conditional_kinds[kind] >= 12:
                continue
            if kind == 14 and not any(e['name'] == 'flag_tiles' for e in streams[start]['optional']):
                continue
            pointer = int.from_bytes(ram[pointer_at:pointer_at + 3], 'little')
            matched = None
            for offset in range(0, 255, stride):
                key = maps.read(pointer + offset, 2)
                if key == 65535:
                    break
                px, py = (key >> 8) * 16, (key & 255) * 16
                for layer in range(2):
                    desc = streams[start]['primary'] if not layer else streams[start]['secondary']
                    if not desc or (layer and not desc['active']):
                        continue
                    width, height = desc['dimensions']
                    if px >= width * 256 or py >= height * 256:
                        continue
                    segment = maps.read(desc['grid'] + 2 * ((py // 256) * width + px // 256), 2)
                    cell = maps.read(maps.tables['segments'][segment] + ((py >> 5) & 7) * 8 + ((px >> 5) & 7))
                    metatile = maps.read(desc['cells'] + cell * 4 + ((py >> 4) & 1) * 2 + ((px >> 4) & 1))
                    if maps.read(desc['attributes'] + metatile) & 15 == kind:
                        matched = (layer, px, py, metatile, offset)
                        break
                if matched:
                    break
            if not matched:
                continue
            layer, px, py, metatile, offset = matched
            host_buffer, host_view = make_view(ram, sample_regs)
            if not dll.FoundationFieldCheckSceneView(ctypes.byref(host_view)):
                raise AssertionError(('authentic conditional fixture declined', scene, kind))
            phases = [0, 1] if kind == 14 else [0]
            replacements = []
            for flag_phase in phases:
                if kind == 14:
                    bit = maps.read(pointer + offset + 2, 2)
                    address, mask = 0x53f9 + ((bit >> 3) & 255), 128 >> (bit & 7)
                    host_buffer[address] = (host_buffer[address] | mask) if flag_phase else (host_buffer[address] & ~mask)
                host_ram = bytes(host_buffer)
                if dll.FoundationFieldPrivateSelected(host_buffer, len(host_ram)) != start:
                    raise AssertionError('Conditional flag fixture changed original scene selection')
                if not dll.FoundationFieldCheckSceneView(ctypes.byref(host_view)):
                    raise AssertionError('Selected conditional refresh refused')
                desc = streams[start]['primary'] if not layer else streams[start]['secondary']
                replacement = maps.conditional(host_ram, desc['attributes'], metatile, px, py, set())
                replacements.append(replacement)
                conditional_replacements[kind] += replacement != metatile
                for dx, dy in [(0, 0), (8, 0), (0, 8), (8, 8)]:
                    accepted = dll.FoundationFieldResolve(layer, px + dx, py + dy, ctypes.byref(word_value))
                    wanted = expected(maps, host_ram, layer, px + dx, py + dy)
                    checks[f'conditional_{kind}_{conditional_kinds[kind]}_{flag_phase}_{dx}_{dy}'] = bool(accepted) and word_value.value == wanted
            conditional_samples.append({'kind': kind, 'scene': scene, 'record': record,
                                        'stream': start, 'layer': layer, 'coordinate': [px, py],
                                        'original_id': metatile, 'table': pointer,
                                        'offset': offset, 'selected_ids': replacements})
            conditional_kinds[kind] += 1
    checks['authentic_E_and_F_samples_present'] = all(conditional_kinds.values())
    checks['authentic_E_and_F_replacement_branches_present'] = all(conditional_replacements.values())
    retained_samples = []
    for scene in [216, 221]:
        ram[:] = bytes(len(ram))
        write(ram, 0x40e, scene, 2)
        start = selected_record(scenes[scene], ram)['stream']
        resources(maps, ram, streams[start])
        retained_pointer = 0x080000 | maps.read(0x08e900 + 47 * 2, 2)
        write(ram, 0x453, retained_pointer, 3)
        retained_buffer, retained_view = make_view(ram, sample_regs)
        desc = streams[start]['primary']
        bit = 144
        address, mask = 0x53f9 + (bit >> 3), 128 >> (bit & 7)
        ids = []
        for phase in [0, 1]:
            retained_buffer[address] = mask if phase else 0
            host_ram = bytes(retained_buffer)
            checks[f'retainedE_scene{scene}_phase{phase}_eligible'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(retained_view)))
            ids.append(maps.conditional(host_ram, desc['attributes'], 1, 928, 544, set()))
            for dx, dy in [(0, 0), (8, 0), (0, 8), (8, 8)]:
                accepted = dll.FoundationFieldResolve(0, 928 + dx, 544 + dy, ctypes.byref(word_value))
                checks[f'retainedE_scene{scene}_phase{phase}_{dx}_{dy}'] = bool(accepted) and word_value.value == expected(maps, host_ram, 0, 928 + dx, 544 + dy)
        checks[f'retainedE_scene{scene}_clear_set_ids'] = ids == [1, 2]
        for i, v in enumerate((0x08e9a0).to_bytes(3, 'little')):
            retained_buffer[0x453 + i] = v
        dll.FoundationFieldCheckSceneView(ctypes.byref(retained_view))
        checks[f'retainedE_scene{scene}_unknown_pointer_refuses_E'] = not dll.FoundationFieldResolve(0, 928, 544, ctypes.byref(word_value))
        retained_samples.append({'scene': scene, 'stream': start, 'retained_list_index': 47,
                                 'retained_pointer': retained_pointer, 'coordinate': [928, 544],
                                 'flag_index': bit, 'selected_ids': ids,
                                 'kind': 'host fixture; retained loader history unverified'})
    # Natural captured eligibility and center words are reported separately.
    natural = []
    value = ctypes.c_uint16()
    center_count = 0
    resolve = lambda layer, x, y: value.value if dll.FoundationFieldResolve(layer, x, y, ctypes.byref(value)) else None
    for prefix in args.dump_prefix:
        original = Path(str(prefix) + '.wram.bin').read_bytes()
        regs = json.loads(Path(str(prefix) + '.regs.json').read_text())
        vram = Path(str(prefix) + '.vram.bin').read_bytes()
        metadata = inspect(maps, prefix)
        natural_buffer, view = make_view(original, regs)
        tag = f'natural_scene{metadata["scene"]}'
        checks[tag + '_eligible'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        local_count = 0
        mismatch = 0
        for layer in range(2):
            if not original[0x50c + layer]:
                continue
            cx, cy = metadata['layers'][layer]['raster_world']
            for ty in range(cy // 8, (cy + 223) // 8 + 1):
                for tx in range(cx // 8, (cx + 255) // 8 + 1):
                    actual = resolve(layer, tx * 8, ty * 8)
                    rx, ry = tx % 64, ty % 32
                    offset = (0x9000, 0xb000)[layer] + (rx // 32) * 2048 + (ry * 32 + rx % 32) * 2
                    wanted_vram = int.from_bytes(vram[offset:offset + 2], 'little')
                    wanted_rom = expected(maps, original, layer, tx * 8, ty * 8)
                    mismatch += actual != wanted_vram or actual != wanted_rom
                    local_count += 1
        checks[tag + '_center_words_exact'] = mismatch == 0
        center_count += local_count
        original_secondary = bytes(natural_buffer[0x516:0x519])
        for i, v in enumerate((0x090000 | maps.tables['maps'][0]).to_bytes(3, 'little')):
            natural_buffer[0x516 + i] = v
        checks[tag + '_foreign_secondary_refuses_and_resolve_inactive'] = not dll.FoundationFieldCheckSceneView(ctypes.byref(view)) and resolve(0, 0, 0) is None
        for i, v in enumerate(original_secondary):
            natural_buffer[0x516 + i] = v
        checks[tag + '_cache_recovers'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        checks[tag + '_ram_unchanged'] = bytes(natural_buffer) == original
        dll.FoundationFieldReset()
        checks[tag + '_reset_inactive'] = resolve(0, 0, 0) is None and not dll.FoundationFieldCheckSceneView(ctypes.byref(view))
        checks[tag + '_reset_rebind_recovers'] = bool(dll.FoundationFieldBind(rom, len(maps.rom))) and bool(dll.FoundationFieldCheckSceneView(ctypes.byref(view)))
        natural.append({'prefix': str(prefix), 'scene': metadata['scene'],
                        'input_sha256': metadata['input_sha256'], 'center_words': local_count})
    # Changing the original selector's live stage must invalidate eligibility
    # even when scene/resource tuples are unchanged (same cached candidate).
    changing_scene = next(scene for scene, records in enumerate(scenes) if len(records) > 1)
    states = [(key, state) for key, state in selected_states.items() if key[0] == changing_scene]
    first_key, (stage, story, start) = states[0]
    alternative = next((entry for entry in states if entry[1][2] != start), None)
    if not alternative:
        raise AssertionError('Expected original scene with different live selected streams')
    ram[:] = bytes(len(ram))
    write(ram, 0x40e, changing_scene, 2)
    ram[0x5360:0x5372] = story
    ram[0x5372] = stage
    resources(maps, ram, streams[start])
    checks['original_selection_metadata_positive'] = bool(dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0))
    selected_buffer, selected_view = make_view(ram, regs)
    checks['cached_selection_initial_scene_eligible'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(selected_view)))
    _, (stage2, story2, start2) = alternative
    ram[0x5360:0x5372] = story2
    ram[0x5372] = stage2
    checks['live_selection_changes_with_same_resource_tuple'] = dll.FoundationFieldPrivateSelected(buffer, len(ram)) == start2
    # Different variants can deliberately share identical resources. Require
    # refusal only when the selected full provenance contract actually differs.
    changed_contract = not dll.FoundationFieldPrivateProvenance(buffer, len(ram), 0)
    checks['changed_selection_contract_refuses'] = changed_contract
    for i, v in enumerate(story2):
        selected_buffer[0x5360 + i] = v
    selected_buffer[0x5372] = stage2
    checks['cached_selection_live_refresh_refuses'] = not dll.FoundationFieldCheckSceneView(ctypes.byref(selected_view)) and resolve(0, 0, 0) is None
    for i, v in enumerate(story):
        selected_buffer[0x5360 + i] = v
    selected_buffer[0x5372] = stage
    checks['cached_selection_live_refresh_recovers'] = bool(dll.FoundationFieldCheckSceneView(ctypes.byref(selected_view)))
    report = {'kind': 'private prototype only; no promotion/installation/campaign claim',
              'source_sha256': {p.name: sha(p.read_bytes()) for p in source.glob('foundation_field.*')},
              'library_sha256': sha(library.read_bytes()), 'checks': checks,
              'static_stream_structures': structure_count,
              'original_condition_selection_comparisons': selection_comparisons,
              'host_selected_variant_links': len(selected_states),
              'host_condition_unit_cases': condition_count,
              'authentic_selected_conditional_samples': conditional_samples,
              'conditional_sample_counts': conditional_kinds,
              'conditional_replacement_counts': conditional_replacements,
              'retained_E_samples': retained_samples,
              'natural_captures': natural, 'natural_center_words': center_count,
              'failed': [name for name, passed in checks.items() if not passed]}
    report['qualified_private_prototype'] = not report['failed']
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ['qualified_private_prototype', 'static_stream_structures',
                       'original_condition_selection_comparisons', 'host_selected_variant_links',
                       'host_condition_unit_cases', 'natural_center_words', 'failed']}, indent=2))
    if report['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
