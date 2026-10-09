"""Qualify read-only direct-column observations in a copied natural house exit.

Original ROM/state/cache contents and diagnostic CSV remain under local/.
This checks a bounded constructor, not campaign coverage or a speedup.
"""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'regs.json', 'fb.bgrx')
SCRIPT = 'wait 10\ndump before\npress down 96\ndump door\nwait 17\ndump loading\nwait 2\ndump clear\nwait 102\ndump after\nquit\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(value):
    return value - 0x10000 if value & 0x8000 else value


def rom_slice(rom, address, count):
    bank, low = address >> 16, address & 0xffff
    offset = (bank & 0x7f) * 0x8000 + (low & 0x7fff)
    if not 0 <= address <= 0xffffff or low < 0x8000 or low + count > 0x10000 or offset + count > len(rom):
        raise ValueError(f'Unqualified ROM read {address:06x}+{count}')
    return rom[offset:offset + count]


def word(rom, address):
    return int.from_bytes(rom_slice(rom, address, 2), 'little')


def analyze(base, rom, case='observer-on', clear_mode='0'):
    directory = base / case
    with (directory / 'columns.csv').open() as file:
        raw = list(csv.DictReader(file))
    if not raw or any(None in row or None in row.values() for row in raw):
        raise ValueError('Missing rows or inconsistent CSV column count')
    text_keys = {'event', 'dp_hex', 'coordinate_hex', 'progression_hex', 'attributes1_sha256', 'attributes2_sha256'}
    rows = [{k: v if k in text_keys else int(v) for k, v in row.items()} for row in raw]
    events = collections.Counter(row['event'] for row in rows)
    stores = [r for r in rows if r['event'] == 'column_store']
    posts = [r for r in rows if r['event'] == 'column_after_store']
    entries = [r for r in rows if r['event'] == 'column_entry']
    exits = [r for r in rows if r['event'] == 'column_exit']
    constructors = [r for r in rows if r['event'].startswith('constructor_')]
    checks = {
        'column_trace_well_formed': True,
        'all_rows_exact_rom': all(r['rom_ok'] for r in rows),
        'complete_thirty_word_columns': bool(entries) and len(entries) == len(exits) and
            all(r['completed'] == 1 and r['stores'] == 30 for r in exits),
        'one_post_observation_per_store': bool(stores) and len(stores) == len(posts) == len(entries) * 30,
        'all_store_contexts_valid': all(r['store_bytes_valid'] == r['context_ok'] == r['sequence_ok'] == 1 for r in stores),
        'all_actual_port_writes_match': all(r['post_valid'] == r['sequence_ok'] == 1 and
            r['post_actual_word'] == r['post_expected_word'] and r['vram_pointer'] == r['post_expected_pointer'] for r in posts),
        'exact_direct_column_caller': bool(entries) and all(r['column_caller'] == 0x01b25c for r in entries),
        'exact_loading_dp': all(r['dp_valid'] and r['d'] == 0x0b00 for r in entries + stores + posts + exits),
        'both_layers_observed': {r['dp_layer'] for r in entries} == {0, 2},
        'native_clear_disabled': '[foundation] native_clear_original_cost=0' in (directory / 'host.log').read_text(errors='replace') and
            '[foundation] native_clear_reduced_internal_cost=1' not in (directory / 'host.log').read_text(errors='replace') and
            '[foundation] native_clear_fast_cost=1' not in (directory / 'host.log').read_text(errors='replace') and
            '[foundation_clear] native_instructions=' not in (directory / 'host.log').read_text(errors='replace'),
    }
    if clear_mode == 'fast':
        log = (directory / 'host.log').read_text(errors='replace')
        checks.pop('native_clear_disabled')
        checks['explicit_combined_fast_clear'] = '[foundation] native_clear_fast_cost=1' in log and '[foundation_clear] native_instructions=18432' in log
    grouping = collections.defaultdict(list)
    for row in rows:
        grouping[(row['epoch'], row['column'])].append(row)
    paired_costs = collections.Counter()
    lookup_costs = collections.Counter()
    total_column_cpu = total_column_master = 0
    segments = collections.Counter()
    resources = collections.Counter()
    world_samples = []
    hierarchy_exact = tile_exact = attribute_exact = True
    hierarchy_count = boundary_count = attribute_count = 0
    selector_counts = collections.Counter()
    for group in grouping.values():
        pending = lookup = None
        for row in group:
            event = row['event']
            if event == 'column_store':
                pending = row
                tile_exact &= bool(row['tile_rom_valid']) and row['a'] == row['tile_expected'] == word(rom, row['tile_source'])
                dp = bytes.fromhex(row['dp_hex'])
                dp16 = lambda at: int.from_bytes(dp[at:at+2], 'little')
                if row['dp_outside']:
                    boundary_count += 1
                    hierarchy_exact &= row['metatile'] == 0
                else:
                    try:
                        grid_byte = dp16(0x17)
                        sid = word(rom, row['dp_map'] + grid_byte)
                        segment = int.from_bytes(rom_slice(rom, 0x09b000 + sid * 3, 3), 'little')
                        cell_index = row['dp_cell_index']
                        cell_id = rom_slice(rom, segment + cell_index, 1)[0]
                        meta_at = row['dp_cells'] + cell_id * 4 + row['dp_cell_quadrant']
                        metatile = rom_slice(rom, meta_at, 1)[0]
                        hierarchy_exact &= segment == row['dp_segment'] and cell_id * 4 + row['dp_cell_quadrant'] == row['dp_metatile_index']
                        if row['attribute_selector'] not in (14, 15):
                            hierarchy_exact &= metatile == row['metatile']
                        hierarchy_exact &= row['dp_tile_index'] == row['metatile'] * 8 + row['dp_tile_quadrant'] * 2
                        width = dp[0x13]
                        grid_index = grid_byte // 2
                        wx = (grid_index % width) * 256 + (cell_index % 8) * 32 + (row['dp_cell_quadrant'] & 1) * 16 + (row['dp_tile_quadrant'] & 1) * 8
                        wy = (grid_index // width) * 256 + (cell_index // 8) * 32 + (row['dp_cell_quadrant'] >> 1) * 16 + (row['dp_tile_quadrant'] >> 1) * 8
                        hierarchy_count += 1
                        segments[(row['dp_layer'], sid, segment)] += 1
                        if len(world_samples) < 12:
                            world_samples.append({'column': row['column'], 'layer': row['dp_layer'], 'x': wx, 'y': wy,
                                'word_address': row['store_word_address'], 'word': row['a'], 'segment_id': sid})
                    except (ValueError, ZeroDivisionError, IndexError):
                        hierarchy_exact = False
                if lookup is not None:
                    lookup_costs[(row['cpu_cycles']-lookup['cpu_cycles'], row['master_cycles']-lookup['master_cycles'])] += 1
                    lookup = None
            elif event == 'column_after_store' and pending is not None:
                paired_costs[(row['cpu_cycles'] - pending['cpu_cycles'], row['master_cycles'] - pending['master_cycles'])] += 1
                pending = None
            elif event == 'lookup_entry':
                lookup = row
            elif event == 'column_exit':
                total_column_cpu += row['column_cpu_delta']
                total_column_master += row['column_master_delta']
            elif event == 'column_entry':
                key = tuple(row[k] for k in ('dp_layer', 'map1', 'map2', 'cells1', 'cells2', 'tiles1', 'tiles2', 'attributes1', 'attributes2', 'attributes1_sha256', 'attributes2_sha256', 'conditions_e', 'conditions_f'))
                resources[key] += 1
            elif event == 'attribute_entry':
                attribute_count += 1
                expected = rom_slice(rom, row['dp_attributes'] + row['attribute_input'], 1)[0] & 15
                selector_counts[expected] += 1
                attribute_exact &= row['attribute_rom_valid'] == 1 and expected == row['attribute_selector']
    checks['tileword_rom_loads_exact'] = bool(stores) and tile_exact
    checks['segment_cell_metatile_hierarchy_exact'] = hierarchy_count > 0 and hierarchy_exact
    checks['attribute_selectors_match_rom'] = attribute_count > 0 and attribute_exact
    checks['long_sta_original_costs_exact'] = sum(paired_costs.values()) == len(stores) and all(dc == 6 and dm in (44, 84) for dc, dm in paired_costs)
    checks['all_resource_hashes_exact'] = all(hashlib.sha256(rom_slice(rom, r[f'attributes{layer}'], 256)).hexdigest() == r[f'attributes{layer}_sha256'] for r in entries for layer in (1, 2))
    return {'checks': checks, 'events': dict(events), 'columns': len(entries), 'words': len(stores),
        'inside_hierarchy_comparisons': hierarchy_count, 'boundary_metatile_zero_comparisons': boundary_count,
        'attribute_calls': attribute_count, 'attribute_selectors': dict(selector_counts),
        'column_cpu_cycles': total_column_cpu, 'column_master_cycles': total_column_master,
        'store_instruction_costs': {f'{dc}/{dm}': count for (dc, dm), count in sorted(paired_costs.items())},
        'lookup_block_costs': {f'{dc}/{dm}': count for (dc, dm), count in sorted(lookup_costs.items())},
        'lookup_block_cpu_cycles': sum(dc * count for (dc, dm), count in lookup_costs.items()),
        'constructors': constructors,
        'column_camera_range': {key: [min(signed(r[key]) for r in entries), max(signed(r[key]) for r in entries)] for key in ('camera1_x','camera1_y','camera2_x','camera2_y')},
        'resources': [{'columns': count, 'identity': list(key)} for key, count in resources.items()],
        'segments': [{'layer': layer, 'segment_id': sid, 'segment_rom': f'{address:06X}', 'words': count} for (layer, sid, address), count in sorted(segments.items())],
        'world_samples': world_samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--analyze', type=Path, help='Re-analyze an existing private checker run')
    parser.add_argument('--native-proof', action='store_true', help='Require exact original-cost native lookup parity and positive replacements')
    parser.add_argument('--fast-proof', action='store_true', help='Only after original-cost parity, test separate diagnostic fast lookup')
    parser.add_argument('--combined-fast-clear', action='store_true', help='Also test diagnostic fast clear plus qualified fast lookup')
    args = parser.parse_args()
    if bool(args.exe) == bool(args.analyze):
        parser.error('Specify --exe or --analyze')
    if args.fast_proof and not args.native_proof or args.combined_fast_clear and not args.fast_proof:
        parser.error('Fast proof requires native proof; combined proof also requires fast proof')
    rom_path = ROOT / 'local/inputs/clean-usa.sfc'
    if sha(rom_path) != ROM_SHA:
        raise ValueError('Exact clean USA ROM required')
    rom = rom_path.read_bytes()
    if args.analyze:
        base = args.analyze.resolve(strict=True)
        if not base.is_relative_to(ROOT / 'local'):
            raise ValueError('Private run must be under local/')
        report = json.loads((base / 'report.json').read_text()) if (base / 'report.json').exists() else {'checks': {}}
    else:
        base = ROOT / 'local/runs' / ('columns-' + time.strftime('%Y%m%d-%H%M%S'))
        base.mkdir(exist_ok=False)
        source = base / 'qualified.exe'
        shutil.copy2(args.exe.resolve(strict=True), source)
        fixture = ROOT / 'local/runs/likado-inside-a/saves/save0.sav'
        fixture_hash = sha(fixture)
        report = {'exe_sha256': sha(source), 'rom_sha256': ROM_SHA, 'fixture_sha256': fixture_hash,
            'observer_source_sha256': sha(ROOT / 'native/foundation/src/foundation_loading.c'),
            'checker_sha256': sha(Path(__file__)), 'checks': {}, 'cases': {}, 'limits': [
                'Copied natural house exit only; no owner progress changes',
                'Observed conditional paths are reported separately from unobserved selectors',
                'No CPU budget change, native column replacement, host speedup or scrolling-fix claim',
                'Headless fixtures do not certify listening, physical controller or display scanout']}
        def run(name, observed, native='0', clear='0', state=fixture, script=SCRIPT, save_at=None, load_at=None, config_columns=None):
            directory = base / name
            directory.mkdir()
            (directory / 'dump').mkdir()
            shutil.copy2(source, directory / 'game.exe')
            shutil.copy2(state, directory / 'resume.state')
            (directory / 'input.txt').write_text(script)
            (directory / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
            if config_columns is not None:
                (directory / 'foundation.ini').write_text(f'NativeColumns={config_columns}\n')
            env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
                SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory / 'cpu.csv'), SNESRECOMP_FOUNDATION_TRACE=str(directory / 'field.csv'),
                SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_BATTLE_INFO='0', SNESRECOMP_FOUNDATION_JOURNAL='0',
                SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0', SNESRECOMP_FOUNDATION_WIDE='0', SNESRECOMP_FOUNDATION_NATIVE_CLEAR=clear)
            if native is not None:
                env['SNESRECOMP_FOUNDATION_NATIVE_COLUMNS'] = native
            if observed:
                env['SNESRECOMP_FOUNDATION_COLUMNS_TRACE'] = str(directory / 'columns.csv')
            if save_at is not None:
                env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save_at), SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
            if load_at is not None:
                env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load_at), SNESRECOMP_RUN_FRAMES='280')
            start = time.perf_counter()
            with (directory / 'host.log').open('w') as log:
                result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom', str(rom_path),
                    '--resume-state', str(directory / 'resume.state'), '--script', str(directory / 'input.txt')],
                    cwd=directory, env=env, stdout=log, stderr=log, timeout=45,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            report['cases'][name] = {'exit': result.returncode, 'seconds': time.perf_counter() - start,
                'resumed': 'resume state loaded:' in (directory / 'host.log').read_text(errors='replace')}
            log_text = (directory / 'host.log').read_text(errors='replace')
            count = re.search(r'\[foundation_column_lookup\] native_instructions=(\d+)', log_text)
            report['cases'][name]['native_lookup_instructions'] = int(count.group(1)) if count else 0
            return directory
        run('observer-off', False)
        run('observer-on', True)
        left, right = base / 'observer-off', base / 'observer-on'
        tags = sorted(p.name[:-len('.wram.bin')] for p in (left / 'dump').glob('*.wram.bin'))
        other = sorted(p.name[:-len('.wram.bin')] for p in (right / 'dump').glob('*.wram.bin'))
        checks = report['checks']
        checks['all_processes_exit_and_resume'] = all(c['exit'] == 0 and c['resumed'] for c in report['cases'].values())
        checks['same_binary_for_off_and_on'] = sha(left / 'game.exe') == sha(right / 'game.exe') == report['exe_sha256']
        checks['same_dump_tags'] = bool(tags) and tags == other
        checks['all_guest_snapshots_identical'] = bool(tags) and all((left / 'dump' / (tag + '.' + ext)).read_bytes() == (right / 'dump' / (tag + '.' + ext)).read_bytes() for tag in tags for ext in EXTENSIONS)
        checks['field_trace_identical'] = (left / 'field.csv').read_bytes() == (right / 'field.csv').read_bytes()
        checks['complete_cpu_trace_identical'] = (left / 'cpu.csv').read_bytes() == (right / 'cpu.csv').read_bytes()
        checks['original_fixture_preserved'] = sha(fixture) == fixture_hash
        checks['original_rom_preserved'] = sha(rom_path) == ROM_SHA
        checks['observer_off_has_no_column_trace'] = not (left / 'columns.csv').exists()
        report['dump_tags'] = tags
        # Preserve parity evidence even when subsequent capture analysis fails.
        (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    details = analyze(base, rom)
    report['analysis_checker_sha256'] = sha(Path(__file__))
    report['checks'].update(details.pop('checks'))
    report['column_observation'] = details
    if args.exe and args.native_proof:
        original = base / 'observer-on'
        native = run('native-original', True, native='original')
        checks = report['checks']
        tags = report['dump_tags']
        checks['native_original_all_guest_snapshots_identical'] = all((original / 'dump' / (tag + '.' + ext)).read_bytes() == (native / 'dump' / (tag + '.' + ext)).read_bytes() for tag in tags for ext in EXTENSIONS)
        checks['native_original_field_trace_identical'] = (original / 'field.csv').read_bytes() == (native / 'field.csv').read_bytes()
        checks['native_original_every_column_row_identical'] = (original / 'columns.csv').read_bytes() == (native / 'columns.csv').read_bytes()
        with (original / 'cpu.csv').open() as file: left_cpu = list(csv.DictReader(file))
        with (native / 'cpu.csv').open() as file: right_cpu = list(csv.DictReader(file))
        keys = set(left_cpu[0]) - {'interp_insns', 'interp_cpu_cycles'}
        checks['native_original_cpu_timing_scheduler_identical'] = len(left_cpu) == len(right_cpu) and all(all(a[k] == b[k] for k in keys) for a, b in zip(left_cpu, right_cpu))
        removed = sum(int(a['interp_insns']) - int(b['interp_insns']) for a, b in zip(left_cpu, right_cpu))
        report['cases']['native-original']['interpreted_instructions_removed'] = removed
        checks['native_original_positive_native_replacements'] = removed == report['cases']['native-original']['native_lookup_instructions'] > 0
        observed = analyze(base, rom, 'native-original')
        report['native_original_observation'] = observed
        checks['native_original_column_contract_qualified'] = all(observed['checks'].values())
        # These cases deliberately omit the native-columns environment variable:
        # player configuration must select only the original-cost implementation.
        for name, setting, reference in [('config-column-off', 0, original), ('config-column-original', 1, native)]:
            configured = run(name, True, native=None, config_columns=setting)
            checks[name + '_all_guest_snapshots_identical'] = all((reference / 'dump' / (tag + '.' + ext)).read_bytes() == (configured / 'dump' / (tag + '.' + ext)).read_bytes() for tag in tags for ext in EXTENSIONS)
            checks[name + '_complete_cpu_trace_identical'] = (reference / 'cpu.csv').read_bytes() == (configured / 'cpu.csv').read_bytes()
            checks[name + '_field_trace_identical'] = (reference / 'field.csv').read_bytes() == (configured / 'field.csv').read_bytes()
            checks[name + '_every_column_row_identical'] = (reference / 'columns.csv').read_bytes() == (configured / 'columns.csv').read_bytes()
            count = report['cases'][name]['native_lookup_instructions']
            checks[name + '_correct_native_coverage'] = count == 0 if setting == 0 else count == report['cases']['native-original']['native_lookup_instructions'] > 0
            configured_log = (configured / 'host.log').read_text(errors='replace')
            checks[name + '_original_cost_policy_only'] = f'[foundation] native_column_lookup={setting} fast_fetch=0' in configured_log
        exact_pass = all(checks.values())
        if exact_pass:
            saved = run('mid-column-save', False, save_at=130)
            state = saved / 'saves/save0.sav'
            state_sha = sha(state)
            report['mid_column_state_sha256'] = state_sha
            cold_script = 'wait 102\ndump after\nquit\n'
            cold_off = run('cold-column-original', True, state=state, script=cold_script)
            cold_on = run('cold-column-native', True, native='original', state=state, script=cold_script)
            rollback_off = run('rollback-column-original', True, save_at=130, load_at=170)
            rollback_on = run('rollback-column-native', True, native='original', save_at=130, load_at=170)
            for prefix, off, on in [('cold_column', cold_off, cold_on), ('rollback_column', rollback_off, rollback_on)]:
                partial_tags = sorted(p.name[:-len('.wram.bin')] for p in (off / 'dump').glob('*.wram.bin'))
                checks[prefix + '_all_guest_snapshots_identical'] = bool(partial_tags) and all((off / 'dump' / (tag + '.' + ext)).read_bytes() == (on / 'dump' / (tag + '.' + ext)).read_bytes() for tag in partial_tags for ext in EXTENSIONS)
                checks[prefix + '_field_trace_identical'] = (off / 'field.csv').read_bytes() == (on / 'field.csv').read_bytes()
                checks[prefix + '_observed_column_rows_identical'] = (off / 'columns.csv').read_bytes() == (on / 'columns.csv').read_bytes()
                with (off / 'cpu.csv').open() as file: a = list(csv.DictReader(file))
                with (on / 'cpu.csv').open() as file: b = list(csv.DictReader(file))
                checks[prefix + '_cpu_timing_scheduler_identical'] = len(a) == len(b) and all(all(x[k] == y[k] for k in keys) for x, y in zip(a, b))
                removed = sum(int(x['interp_insns']) - int(y['interp_insns']) for x, y in zip(a, b))
                count = report['cases'][on.name]['native_lookup_instructions']
                report['cases'][on.name]['interpreted_instructions_removed'] = removed
                checks[prefix + '_positive_native_replacements'] = count == removed > 0
            with (cold_off / 'columns.csv').open() as file: cold_rows = list(csv.DictReader(file))
            first_entry = next(r for r in cold_rows if r['event'] == 'column_entry')
            report['first_cold_column_entry'] = {k: first_entry[k] for k in ('frame','pc','d','column_caller','constructor_selector','constructor_iteration','dp_layer')}
            checks['saved_copy_really_during_constructor'] = 0 < int(first_entry['constructor_iteration']) < 34 and int(first_entry['d']) == 0x0b00
            checks['rollback_column_load_issued'] = '[overlay_selftest] load issued' in (rollback_on / 'host.log').read_text(errors='replace')
            checks['partial_column_source_preserved'] = sha(state) == state_sha
            exact_pass = all(checks.values())
        if args.fast_proof and exact_pass:
            with (original / 'columns.csv').open() as file: original_rows = list(csv.DictReader(file))
            timing = {'frame', 'cpu_cycles', 'master_cycles', 'beam_master_last', 'beam_h', 'beam_v', 'coprocessor_master', 'column_cpu_delta', 'column_master_delta'}
            port_keys = ('dp_layer', 'store_word_address', 'store_low', 'store_high')
            original_ports = [tuple(r[k] for k in port_keys) for r in original_rows if r['event'] == 'column_store']
            with (original / 'field.csv').open() as file: original_fields = list(csv.DictReader(file))
            def ready(fields):
                # First visible row at the new camera after the natural exit.
                return next(int(r['frame']) for r in fields if int(r['forced_blank']) == 0 and int(r['brightness']) == 15 and int(r['bg1_scroll_x']) == 128 and int(r['bg1_scroll_y']) == 320)
            original_ready = ready(original_fields)
            policies = [('native-fast', '0')]
            if args.combined_fast_clear: policies.append(('combined-fast', 'fast'))
            for name, clear in policies:
                fast = run(name, True, native='fast', clear=clear)
                observed = analyze(base, rom, name, clear)
                report[name + '_observation'] = observed
                checks[name + '_column_contract_qualified'] = all(observed['checks'].values())
                with (fast / 'columns.csv').open() as file: fast_rows = list(csv.DictReader(file))
                semantic_keys = set(original_rows[0]) - timing
                checks[name + '_every_column_semantic_row_identical'] = len(original_rows) == len(fast_rows) and all(all(a[k] == b[k] for k in semantic_keys) for a, b in zip(original_rows, fast_rows))
                fast_ports = [tuple(r[k] for k in port_keys) for r in fast_rows if r['event'] == 'column_store']
                checks[name + '_all_original_port_words_identical'] = original_ports == fast_ports
                checks[name + '_positive_native_replacements'] = report['cases'][name]['native_lookup_instructions'] == report['cases']['native-original']['native_lookup_instructions'] > 0
                with (fast / 'field.csv').open() as file: fields = list(csv.DictReader(file))
                ready_frame = ready(fields)
                report['cases'][name]['first_visible_ready_frame'] = ready_frame
                report['cases'][name]['saved_loading_fields'] = original_ready - ready_frame
                checks[name + '_visible_loading_not_later'] = ready_frame <= original_ready
                checks[name + '_fast_lookup_costs_exact'] = all(key in ('24/178', '24/218') for key in observed['lookup_block_costs']) and sum(observed['lookup_block_costs'].values()) == 1088
                with (fast / 'cpu.csv').open() as file: cpu_rows = list(csv.DictReader(file))
                checks[name + '_no_step_caps_or_resume_evictions'] = all(int(r['step_cap_events']) == int(r['resume_evicted']) == 0 for r in cpu_rows)
                # Before activation these copied paths must still be exact.
                checks[name + '_pre_transition_snapshots_identical'] = all((original / 'dump' / (tag + '.' + ext)).read_bytes() == (fast / 'dump' / (tag + '.' + ext)).read_bytes() for tag in ('before', 'door') for ext in EXTENSIONS)
            report['original_first_visible_ready_frame'] = original_ready
            report['limits'].append('Fast lookup/clear are explicit diagnostic timing modifications; later fixed-field NPC/audio state can differ and is not certified by column parity')
        elif args.fast_proof:
            checks['fast_not_run_until_original_parity'] = False
        checks['all_processes_exit_and_resume'] = all(c['exit'] == 0 and c['resumed'] for c in report['cases'].values())
    if 'native-fast' in report.get('cases', {}):
        def milestones(case):
            with (base / case / 'field.csv').open() as file: fields = list(csv.DictReader(file))
            candidates = [r for r in fields if int(r['forced_blank']) == 0 and int(r['bg1_scroll_x']) == 128 and int(r['bg1_scroll_y']) == 320]
            return {'forced_blank_release': int(candidates[0]['frame']),
                'first_nonblack_field': next(int(r['frame']) for r in candidates if int(r['brightness']) > 0),
                'full_brightness_field': next(int(r['frame']) for r in candidates if int(r['brightness']) == 15)}
        original = milestones('observer-on')
        report['original_transition_milestones'] = original
        for case in ('native-fast', 'combined-fast'):
            if case not in report['cases']: continue
            found = milestones(case)
            report['cases'][case]['transition_milestones'] = found
            report['cases'][case]['saved_forced_blank_fields'] = original['forced_blank_release'] - found['forced_blank_release']
            report['checks'][case + '_original_fade_intervals_preserved'] = all(found[k] - found['forced_blank_release'] == original[k] - original['forced_blank_release'] for k in ('first_nonblack_field', 'full_brightness_field'))
        report['limits'] = ['Read-only/original-cost paths preserve the guest budget; fast-fetch policies are separate diagnostic enhancements' if item.startswith('No CPU budget change,') else item for item in report['limits']]
    report['passed'] = all(report['checks'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps({'passed': report['passed'], 'checks': report['checks'],
        'columns': details['columns'], 'words': details['words'], 'column_cpu_cycles': details['column_cpu_cycles'],
        'lookup_block_cpu_cycles': details['lookup_block_cpu_cycles']}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
