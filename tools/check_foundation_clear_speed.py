"""Qualify reduced clear computation cost on private copied finite fixtures.

Measures guest loading fields and instruction clocks, never host FPS. The two
policies share an executable; unrelated presentation/fast-menu features are off.
All ROM-derived evidence, changed diagnostic states and progress remain local.
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
import struct
import subprocess
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / 'local/inputs/clean-usa.sfc'
ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'regs.json', 'fb.bgrx')
PREFIX = 'wait 10\ndump before\npress down 96\ndump door\n'
PROBE = PREFIX + 'wait 140\ndump after\nquit\n'
ROLLBACK_SCRIPT = PREFIX + 'wait 17\ndump loading\nwait 2\ndump clear\nwait 102\ndump after\nquit\n'
TIME_KEYS = {'frame', 'cpu_cycles', 'master_cycles', 'beam_master_last', 'beam_h', 'beam_v',
             'pass_cpu_delta', 'pass_master_delta'}
CLEAR_EVENTS = {'clear_entry', 'entry', 'store', 'after_store', 'after_dey', 'exit'}
MENU = ('wait 30\npress b 1\nwait 40\npress a 1\nwait 90\ndump submenu\n'
        'press b 1\nwait 90\npress b 1\nwait 90\ndump field\nquit\n')
TOWN = ('wait 60\ndump before\npress left 90\nwait 30\npress right 160\nwait 30\n'
        'press down 60\nwait 30\ndump after\nquit\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    return list(csv.DictReader(path.open(newline='')))


def semantic_rows(rows):
    return [{k: v for k, v in row.items() if k not in TIME_KEYS}
            for row in rows if row['event'] in CLEAR_EVENTS]


def differences(left, right):
    if len(left) != len(right):
        return {'equal': False, 'left_size': len(left), 'right_size': len(right)}
    offsets = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    return {'equal': not offsets, 'size': len(left), 'different_bytes': len(offsets),
            'first_offsets_hex': [f'{i:05X}' for i in offsets[:128]]}


def instruction_costs(rows, mode):
    phases = [r for r in rows if r['event'] in ('store', 'after_store', 'after_dey', 'exit')]
    counters = collections.defaultdict(collections.Counter)
    valid = bool(phases)
    raw_master = 0
    refresh_events = 0
    for left, right in zip(phases, phases[1:]):
        if left['event'] == 'exit':
            continue
        if left['event'] == 'store':
            cpu, master = (2, 12) if mode == 'fast' else (5, 36)
        elif left['event'] == 'after_store':
            cpu, master = {'original': (2, 14), 'reduced': (1, 8), 'fast': (1, 6)}[mode]
        elif mode == 'fast':
            cpu, master = 1, 6
        elif int(left['y']) == 0:
            cpu, master = 2, 16
        else:
            cpu, master = (3, 22) if mode == 'original' else (2, 16)
        dc = int(right['cpu_cycles']) - int(left['cpu_cycles'])
        dm = int(right['master_cycles']) - int(left['master_cycles'])
        valid &= dc == cpu and dm in (master, master + 40)
        counters[left['event']][f'{dc}/{dm}'] += 1
        raw_master += master
        refresh_events += dm == master + 40
    return {'valid': valid, 'phase_rows': len(phases), 'raw_loop_master_clocks': raw_master,
            'refresh_events': refresh_events,
            'instruction_deltas': {k: dict(v) for k, v in counters.items()}}


def loading_span(field_rows, cpu_rows):
    blank = [i for i, r in enumerate(field_rows) if int(r['forced_blank'])]
    if not blank:
        raise ValueError('Natural transition has no forced-blank loading fields')
    if blank != list(range(blank[0], blank[-1] + 1)):
        raise ValueError('Fixture has more than one loading-blank span')
    ready = next(i for i in range(blank[-1] + 1, len(field_rows))
                 if not int(field_rows[i]['forced_blank']) and int(field_rows[i]['brightness']) > 0
                 and int(field_rows[i]['mode']) == 1)
    full = next(i for i in range(ready, len(field_rows))
                if int(field_rows[i]['brightness']) == 15 and not int(field_rows[i]['forced_blank']))
    first_frame = int(field_rows[0]['frame'])
    return {'first_simulated_guest_frame': first_frame,
            'forced_blank_fields': len(blank),
            'first_blank_guest_frame': int(field_rows[blank[0]]['frame']),
            'last_blank_guest_frame': int(field_rows[blank[-1]]['frame']),
            'first_visible_guest_frame': int(field_rows[ready]['frame']),
            'full_brightness_ready_guest_frame': int(field_rows[full]['frame']),
            'first_visible_elapsed_fields': ready + 1,
            'full_brightness_elapsed_fields': full + 1,
            'first_visible_state': {k: field_rows[ready][k] for k in
                ('mode', 'brightness', 'forced_blank', 'bgmode', 'bg1_scroll_x', 'bg1_scroll_y')},
            'full_brightness_state': {k: field_rows[full][k] for k in
                ('mode', 'brightness', 'forced_blank', 'bgmode', 'bg1_scroll_x', 'bg1_scroll_y')},
            'ready_nmi_wait_seen': bool(int(cpu_rows[full]['nmi_wait_iterations']))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--modes', nargs='+', choices=('original', 'reduced', 'fast'),
                        default=['original', 'reduced'])
    args = parser.parse_args()
    if len(args.modes) != 2 or 'original' not in args.modes or len(set(args.modes)) != 2:
        parser.error('This qualification pairs original with exactly one of reduced or fast')
    enhanced = next(mode for mode in args.modes if mode != 'original')
    exe = args.exe.resolve(strict=True)
    if digest(ROM) != ROM_SHA:
        raise ValueError('Exact original private clean ROM required')
    base = ROOT / 'local/runs' / ('clear-speed-' + enhanced + '-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    supplied_exe = exe
    exe = base / 'qualified-source.exe'
    shutil.copy2(supplied_exe, exe)
    states = {
        'transition': ROOT / 'local/runs/likado-inside-a/saves/save0.sav',
        'town': ROOT / 'local/runs/likado-east-a/saves/save0.sav',
        'battle': ROOT / 'local/runs/world-cave-a/saves/save0.sav'}
    report = {'executable_sha256': digest(exe), 'rom_sha256': ROM_SHA,
              'compared_modes': args.modes,
              'source_checkpoint_sha256': {k: digest(v) for k, v in states.items()},
              'cases': {}, 'checks': {}, 'limits': [
                  'Natural house exit only; no manufactured CPU stress or broad campaign',
                  'Guest clocks/fields measured; process duration is not a performance conclusion',
                  'Reduced clear cost is diagnostic and does not change global CPU budget or world update rate',
                  'Ready snapshots occur at matching semantic field readiness, potentially at different absolute times',
                  'All ready snapshot byte differences are reported; no unnamed timer/NPC bytes are silently masked',
                  'Headless audio disabled; not audible audio, physical controller, or display scanout certification']}
    checks = report['checks']

    def run(name, mode, state, script, save_at=None, load_at=None):
        directory = base / name
        directory.mkdir()
        (directory / 'dump').mkdir()
        shutil.copy2(exe, directory / 'game.exe')
        shutil.copy2(state, directory / 'resume.state')
        (directory / 'input.txt').write_text(script, encoding='utf-8')
        (directory / 'config.ini').write_text(
            '[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n', encoding='utf-8')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
                   SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory / 'cpu.csv'),
                   SNESRECOMP_FOUNDATION_TRACE=str(directory / 'field.csv'),
                   SNESRECOMP_FOUNDATION_LOADING_TRACE=str(directory / 'loading.csv'),
                   SNESRECOMP_FOUNDATION_NATIVE_CLEAR=mode,
                   SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
                   SNESRECOMP_FOUNDATION_JOURNAL='0', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
                   SNESRECOMP_FOUNDATION_WIDE='0')
        if save_at is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save_at), SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load_at is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load_at), SNESRECOMP_RUN_FRAMES='400')
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom', str(ROM),
                                     '--resume-state', str(directory / 'resume.state'),
                                     '--script', str(directory / 'input.txt')], cwd=directory,
                                    env=env, stdout=log, stderr=log, timeout=50,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        host = (directory / 'host.log').read_text(errors='replace')
        native = re.search(r'\[foundation_clear\] native_instructions=(\d+)', host)
        data = {'directory': directory, 'rows': read_csv(directory / 'loading.csv'),
                'fields': read_csv(directory / 'field.csv'), 'cpu': read_csv(directory / 'cpu.csv')}
        report['cases'][name] = {'exit': result.returncode, 'resumed': 'resume state loaded:' in host,
                                'native_instructions': int(native.group(1)) if native else 0,
                                'event_counts': dict(collections.Counter(r['event'] for r in data['rows']))}
        checks[name + '_cpu_observation_valid'] = bool(data['cpu']) and all(
            int(r['valid']) == 1 and int(r['resume_evicted']) == 0 and int(r['step_cap_events']) == 0
            for r in data['cpu'])
        return data

    def exact(name, left, right, tags):
        checks[name + '_guest_snapshots_identical'] = all(
            (left['directory'] / 'dump' / f'{tag}.{ext}').read_bytes() ==
            (right['directory'] / 'dump' / f'{tag}.{ext}').read_bytes()
            for tag in tags for ext in EXTENSIONS)
        checks[name + '_field_trace_identical'] = left['fields'] == right['fields']
        checks[name + '_cpu_trace_identical'] = left['cpu'] == right['cpu']
        checks[name + '_seam_trace_identical'] = left['rows'] == right['rows']

    def partial(name, data):
        entries = [r for r in data['rows'] if r['event'] == 'entry']
        valid = bool(entries) and 0 < int(entries[0]['entry_remaining']) < 6144 and \
            int(entries[0]['prologue_observed']) == 0 and \
            int(entries[0]['vram_pointer']) == 0x6000 - int(entries[0]['y'])
        checks[name + '_coherent_partial_clear'] = valid
        checks[name + '_positive_native_continuation'] = report['cases'][name]['native_instructions'] > 0
        exits = [r for r in data['rows'] if r['event'] == 'exit']
        checks[name + '_observed_partial_completes'] = bool(exits) and int(exits[-1]['completed']) == 1
        return entries[0] if entries else None

    try:
        probes = {mode: run('probe-' + mode, mode, states['transition'], PROBE) for mode in args.modes}
        for mode, data in probes.items():
            case = report['cases']['probe-' + mode]
            case['loading_span'] = loading_span(data['fields'], data['cpu'])
            case['instruction_costs'] = instruction_costs(data['rows'], mode)
            stores = [r for r in data['rows'] if r['event'] == 'store']
            exits = [r for r in data['rows'] if r['event'] == 'exit']
            checks[mode + '_all_6144_words_written'] = len(stores) == 6144 and \
                [int(r['store_word_address']) for r in stores] == list(range(0x4800, 0x6000))
            checks[mode + '_all_store_contexts_valid'] = bool(stores) and all(
                int(r['store_bytes_valid']) == int(r['context_ok']) == int(r['sequence_ok']) == 1 and
                int(r['store_low']) == int(r['store_high']) == 0 for r in stores)
            checks[mode + '_complete_clear_semantics'] = len(exits) == 1 and \
                int(exits[0]['completed']) == int(exits[0]['full_range']) == 1
            checks[mode + '_native_18432_instructions'] = case['native_instructions'] == 18432
            checks[mode + '_instruction_cost_policy_valid'] = case['instruction_costs']['valid'] and \
                case['instruction_costs']['phase_rows'] == 18433
        original, candidate = probes['original'], probes[enhanced]
        checks['all_clear_write_phase_and_exit_semantics_identical'] = semantic_rows(original['rows']) == semantic_rows(candidate['rows'])
        old = report['cases']['probe-original']
        new = report['cases']['probe-' + enhanced]
        old_exit = next(r for r in original['rows'] if r['event'] == 'exit')
        new_exit = next(r for r in candidate['rows'] if r['event'] == 'exit')
        report['measured_savings'] = {
            'clear_cpu_cycles': int(old_exit['pass_cpu_delta']) - int(new_exit['pass_cpu_delta']),
            'clear_elapsed_master_clocks_including_refresh': int(old_exit['pass_master_delta']) - int(new_exit['pass_master_delta']),
            'raw_loop_master_clocks': old['instruction_costs']['raw_loop_master_clocks'] - new['instruction_costs']['raw_loop_master_clocks'],
            'forced_blank_fields': old['loading_span']['forced_blank_fields'] - new['loading_span']['forced_blank_fields'],
            'first_visible_fields': old['loading_span']['first_visible_elapsed_fields'] - new['loading_span']['first_visible_elapsed_fields'],
            'full_brightness_ready_fields': old['loading_span']['full_brightness_elapsed_fields'] - new['loading_span']['full_brightness_elapsed_fields']}
        expected_cpu, expected_master = (12287, 73722) if enhanced == 'reduced' else (36863, 294906)
        checks['only_measured_title_computation_cost_removed'] = report['measured_savings']['clear_cpu_cycles'] == expected_cpu and \
            report['measured_savings']['raw_loop_master_clocks'] == expected_master
        checks['loading_visible_ready_not_later'] = report['measured_savings']['first_visible_fields'] >= 0 and \
            report['measured_savings']['full_brightness_ready_fields'] >= 0

        ready = {}
        for mode, data in probes.items():
            span = report['cases']['probe-' + mode]['loading_span']
            door = json.loads((data['directory'] / 'dump/door.regs.json').read_text())['frame']
            # The script dump counter names the NEXT field, whereas the field
            # observer names the field just simulated. Include that simulation
            # rather than capturing the previous brightness-14 field.
            wait = span['full_brightness_ready_guest_frame'] - door + 1
            ready[mode] = run('ready-' + mode, mode, states['transition'], PREFIX + f'wait {wait}\ndump ready\nquit\n')
            regs = json.loads((ready[mode]['directory'] / 'dump/ready.regs.json').read_text())
            checks[mode + '_ready_capture_at_measured_field'] = regs['frame'] == span['full_brightness_ready_guest_frame'] + 1
            checks[mode + '_ready_capture_actually_full_brightness'] = regs['inidisp'] == 15
        left, right = [ready[m]['directory'] / 'dump/ready' for m in ('original', enhanced)]
        report['ready_snapshot_comparison'] = {ext: differences(
            Path(str(left) + '.' + ext).read_bytes(), Path(str(right) + '.' + ext).read_bytes())
            for ext in EXTENSIONS}
        lv, rv = [Path(str(p) + '.vram.bin').read_bytes() for p in (left, right)]
        lw, rw = [Path(str(p) + '.wram.bin').read_bytes() for p in (left, right)]
        checks['semantic_ready_all_three_tilemap_rings_identical'] = lv[0x9000:0xc000] == rv[0x9000:0xc000]
        checks['semantic_ready_sram_identical'] = Path(str(left) + '.sram.bin').read_bytes() == Path(str(right) + '.sram.bin').read_bytes()
        checks['semantic_ready_verified_story_flags_identical'] = lw[0x5300:0x5400] == rw[0x5300:0x5400]
        # Camera and loader resource records have already been observed directly;
        # preserve the exact records, without guessing names for unrelated RAM.
        checks['semantic_ready_scene_camera_resource_records_identical'] = all(
            lw[a:b] == rw[a:b] for a, b in [(0x20, 0x21), (0x02ad, 0x02b5), (0x0407, 0x0410),
                                          (0x046d, 0x0471), (0x0500, 0x0519), (0x0531, 0x0532),
                                          (0x0537, 0x053a), (0x055c, 0x055f)])

        # The fast clear may finish before any whole-field checkpoint boundary.
        # Reuse one genuinely observed original-cost v3 mid-clear copy as the
        # common anchor. This deliberately tests changing the optional policy
        # after restore; it does not pretend a fast full-run midpoint was saved.
        saved = run('save-natural-original', 'original', states['transition'], ROLLBACK_SCRIPT, save_at=126)
        shared_partial = saved['directory'] / 'saves/save0.sav'
        for mode in args.modes:
            anchored = run('anchor-' + mode, mode, shared_partial, 'wait 102\ndump after\nquit\n', save_at=0)
            state = anchored['directory'] / 'saves/save0.sav'
            raw = state.read_bytes()
            checks[mode + '_copied_midclear_schema_v3'] = raw.count(struct.pack('<II', 0x53544f53, 3)) == 1
            cold = run('cold-' + mode, mode, state, 'wait 102\ndump after\nquit\n')
            entry = partial('cold-' + mode, cold)
            checks[mode + '_cold_matches_uninterrupted_after'] = all(
                (anchored['directory'] / 'dump' / f'after.{ext}').read_bytes() ==
                (cold['directory'] / 'dump' / f'after.{ext}').read_bytes() for ext in EXTENSIONS)
            rollback = run('rollback-' + mode, mode, shared_partial, 'wait 102\ndump after\nquit\n', save_at=0, load_at=40)
            entries = [r for r in rollback['rows'] if r['event'] == 'entry']
            checks[mode + '_rollback_reenters_coherent_partial'] = len(entries) == 2 and all(
                int(r['prologue_observed']) == 0 and 0 < int(r['entry_remaining']) < 6144 and
                int(r['vram_pointer']) == 0x6000 - int(r['y']) for r in entries)
            checks[mode + '_rollback_really_native_again'] = report['cases']['rollback-' + mode]['native_instructions'] > \
                report['cases']['cold-' + mode]['native_instructions'] > 0
            host = (rollback['directory'] / 'host.log').read_text(errors='replace')
            checks[mode + '_rollback_load_issued'] = '[overlay_selftest] load issued' in host
            if entry:
                target = json.loads((rollback['directory'] / 'dump/after.regs.json').read_text())['frame']
                elapsed = target - int(entry['frame'])
                continuation = run('rollback-continuation-' + mode, mode, state, f'wait {elapsed}\ndump after\nquit\n')
                checks[mode + '_rollback_matches_uninterrupted_continuation'] = all(
                    (continuation['directory'] / 'dump' / f'after.{ext}').read_bytes() ==
                    (rollback['directory'] / 'dump' / f'after.{ext}').read_bytes() for ext in EXTENSIONS)
            # Valid but unsupported hardware settings, in a disposable state
            # copy only. These are guard tests, not manufactured CPU stress.
            for name, flags in [('increment-32', 0x200001), ('remap-1', 0x010101)]:
                changed = bytearray(raw)
                struct.pack_into('<I', changed, len(changed) - 16, flags)
                struct.pack_into('<I', changed, len(changed) - 4, zlib.crc32(changed[:-4]))
                path = base / f'{name}-{mode}.state'
                path.write_bytes(changed)
                off = run(f'{name}-{mode}-off', '0', path, 'wait 102\ndump after\nquit\n')
                on = run(f'{name}-{mode}-on', mode, path, 'wait 102\ndump after\nquit\n')
                exact(name + '-' + mode + '-fallback', off, on, ('after',))
                checks[name + '-' + mode + '_guard_native_count_zero'] = report['cases'][f'{name}-{mode}-on']['native_instructions'] == 0

        # Pacing controls contain ordinary movement, a finite two-Red-Slime
        # battle, and ready submenu/back actions. No clear should be replaced.
        battle = (ROOT / 'local/runs/native-damage-original/input.txt').read_text()
        battle_tags = tuple(re.findall(r'^dump (\S+)$', battle, re.MULTILINE))
        for name, state, script, tags in [('town', states['town'], TOWN, ('before', 'after')),
                                           ('battle', states['battle'], battle, battle_tags),
                                           ('menu', states['town'], MENU, ('submenu', 'field'))]:
            left = run(name + '-original', 'original', state, script)
            right = run(name + '-' + enhanced, enhanced, state, script)
            exact(name + '_original_pacing', left, right, tags)
            checks[name + '_clear_stays_inactive'] = report['cases'][name + '-original']['native_instructions'] == \
                report['cases'][name + '-' + enhanced]['native_instructions'] == 0
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        checks['checker_completed'] = False
    checks['source_checkpoints_preserved'] = all(digest(states[k]) == v for k, v in report['source_checkpoint_sha256'].items())
    checks['source_rom_preserved'] = digest(ROM) == ROM_SHA
    checks['all_processes_exit_and_resume'] = bool(report['cases']) and all(
        c['exit'] == 0 and c['resumed'] for c in report['cases'].values())
    report['passed'] = all(checks.values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
