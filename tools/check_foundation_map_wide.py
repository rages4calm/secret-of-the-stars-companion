"""Finite multi-map widescreen proof using frozen binaries and copied states.

Every process is headless, silent and isolated under ignored local/. Original
width is paired against expanded width at the same enhanced-pixel setting.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
GUEST = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'regs.json', 'fb.bgrx')
IDLE = 'wait 2\ndump start\nwait 90\ndump end\nquit\n'
SWEEP = ('wait 2\ndump start\npress right 32\ndump right\npress left 40\n'
         'dump left\nwait 30\ndump end\nquit\n')
TRANSITION = ('wait 10\ndump before\npress down 96\ndump door\nwait 17\n'
              'dump loading\nwait 2\ndump clear\nwait 102\ndump after\nquit\n')
WARM_ENTRY = ('wait 2\ndump world\npress left 80\npress up 180\ndump encounter\n'
              'wait 120\ndump battle\nquit\n')
MENU = ('wait 30\ndump field\npress b 1\nwait 90\ndump menu\npress b 1\n'
        'wait 90\ndump closed\nquit\n')
BATTLE = ('wait 60\ndump command\npress a 1\nwait 90\ndump fight\npress a 1\n'
          'wait 90\ndump target\npress a 1\nwait 10\ndump action10\nwait 40\n'
          'dump action50\nwait 90\ndump action140\n' +
          ''.join('press a 1\nwait 180\ndump damage'+str(i)+'\n' for i in range(1, 7)) + 'quit\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_surface(path):
    frame, width, height = map(int, re.search(r'frame-(\d+)-(\d+)x(\d+)', path.name).groups())
    data = path.read_bytes()
    if len(data) != width * height * 4:
        raise ValueError('Incomplete composed capture: ' + str(path))
    return frame, np.frombuffer(data, np.uint8).reshape(height, width, 4)


def rows(path):
    if not path.exists():
        return []
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def number(row, key, default=0):
    value = row.get(key)
    return default if value is None or value == '' else int(value, 0)


def protected_owner():
    owner = ROOT / 'local/player-foundation'
    paths = [p for p in owner.iterdir() if p.is_file()] if owner.exists() else []
    paths += list((owner / 'saves').rglob('*')) if (owner / 'saves').exists() else []
    return {str(p): sha(p) for p in paths if p.is_file()}


def packet_lineage(data):
    completed = {}
    active = []
    matched = []
    captures = []
    for row in data:
        key = (number(row, 'generation'), number(row, 'epoch'))
        if row['event'] == 'capture':
            captures.append(row)
        if row['event'] == 'dma_complete' and number(row, 'packet_valid'):
            completed[key] = row
        if row['event'] == 'frame' and number(row, 'packet_valid'):
            packet = completed.get(key)
            active.append(row)
            matched.append(packet is not None and number(packet, 'packet_match') == 1 and
                           number(packet, 'producer_frame') == number(row, 'producer_frame') and
                           number(packet, 'scene') == number(row, 'scene') and
                           number(packet, 'start_slot') == number(row, 'start_slot') and
                           number(packet, 'mask') == number(row, 'mask'))
    resets = [r for r in data if r['event'] == 'reset']
    return {'active_frames': len(active), 'capture_events': len(captures),
            'scenes': sorted({number(r, 'scene') for r in active}),
            'start_slots': sorted({number(r, 'start_slot') for r in active}),
            'masks': sorted({number(r, 'mask') for r in active}),
            'generations': sorted({number(r, 'generation') for r in data}),
            'checks': {
                'actual_completed_packet_lineage': bool(matched) and all(matched),
                'capture_original_cpu_context': bool(captures) and all(
                    tuple(number(r, k) for k in ('cpu_d', 'cpu_db', 'cpu_m', 'cpu_x')) ==
                    (0x0e00, 1, 0, 1) for r in captures),
                'captured_cursor_and_original_mask': bool(active) and all(
                    12 <= number(r, 'start_slot') <= 124 and number(r, 'mask') in (0xefff, 0xffff) and
                    number(r, 'rotation') == 0 for r in active),
                'restore_resets_empty_cache': bool(resets) and all(
                    not number(r, 'packet_valid') and not number(r, 'cached_actors') for r in resets)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--reference-exe', type=Path, help='Frozen earlier0.1.6 for separate legacy-world crash reproduction')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--house-state', type=Path, default=ROOT/'local/runs/likado-inside-a/saves/save0.sav')
    parser.add_argument('--town-state', type=Path, default=ROOT/'local/runs/likado-east-a/saves/save0.sav')
    parser.add_argument('--world-state', type=Path, default=ROOT/'local/runs/likado-loop-exit-a/saves/save0.sav')
    parser.add_argument('--opening-state', type=Path, default=ROOT/'local/runs/first-room/saves/save0.sav')
    parser.add_argument('--island-state', type=Path, default=ROOT/'local/runs/clean-to-outdoors/saves/save0.sav')
    parser.add_argument('--battle-state', type=Path, default=ROOT/'local/runs/world-cave-a/saves/save0.sav')
    parser.add_argument('--legacy-state', type=Path, default=ROOT/'local/runs/battle-return-a/saves/save0.sav')
    parser.add_argument('--title-state', type=Path, help='Optional copied visible-title checkpoint; otherwise generate a fresh private one from cold boot')
    parser.add_argument('--title-wait', type=int, help='Explicit wait for a prelude checkpoint; visible-title state defaults240')
    parser.add_argument('--only', help='Comma-separated case names for focused diagnostics; omitted runs full coverage')
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    states = {k: getattr(args, k+'_state').resolve(strict=True)
              for k in ('house', 'town', 'world', 'opening', 'island', 'battle')}
    if args.title_state:
        states['title'] = args.title_state.resolve(strict=True)
    if args.reference_exe:
        states['legacy'] = args.legacy_state.resolve(strict=True)
    rom = ROOT / 'local/inputs/clean-usa.sfc'
    if sha(rom) != ROM_SHA:
        raise ValueError('Exact original clean USA ROM required')
    base = (args.out or ROOT/'local/runs'/('map-wide-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if not base.is_relative_to((ROOT/'local').resolve()) or base.exists():
        raise ValueError('Use a fresh private output directory under local/')
    base.mkdir(parents=True)
    frozen = base / 'candidate.exe'
    shutil.copy2(args.exe, frozen)
    inputs = {str(p): sha(p) for p in [args.exe, rom] + list(states.values())}
    reference = None
    if args.reference_exe:
        args.reference_exe = args.reference_exe.resolve(strict=True)
        inputs[str(args.reference_exe)] = sha(args.reference_exe)
        reference = base/'reference.exe'
        shutil.copy2(args.reference_exe, reference)
    owner = protected_owner()
    report = {'executable_sha256': sha(frozen), 'checker_sha256': sha(Path(__file__)),
              'source_inputs': inputs, 'checks': {}, 'cases': {}, 'surfaces': {}, 'actor_packets': {},
              'selected_cases': args.only, 'full_suite': args.only is None}
    checks = report['checks']
    selection = set(args.only.split(',')) if args.only else None
    sequence = sorted(set(list(range(1, 25)) + list(range(30, 250, 5)) +
                          [61, 73, 100, 105, 106, 107, 110, 115, 120, 123, 124, 125, 126, 127,
                           150, 180, 210, 225, 230, 235, 260, 300, 350, 400, 450, 500, 550, 600,
                           650, 700, 750, 800, 900, 1000, 1100, 1200, 1400, 6500, 6600, 6700,
                           6800, 6900, 7000, 10600, 10700, 10800, 10900, 11000]) )

    def wanted(name):
        return selection is None or name in selection

    def run(name, state, script, wide, enhanced=0, actors=None, save=None, load=None, executable=None):
        directory = base / name
        directory.mkdir(); (directory/'dump').mkdir(); (directory/'captures').mkdir()
        shutil.copy2(executable or frozen, directory/'game.exe')
        if state:
            shutil.copy2(state, directory/'resume.state')
        (directory/'input.txt').write_text(script)
        (directory/'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n[Controller]\nSourceP1=1\nSourceP2=0\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
            SNESRECOMP_DUMP_DIR=str(directory/'dump'), SNESRECOMP_FOUNDATION_WIDE=str(wide),
            SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(wide if actors is None else actors),
            SNESRECOMP_STATE_TRACE=str(directory/'state.csv'),
            SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory/'cpu.csv'),
            SNESRECOMP_FOUNDATION_TRACE=str(directory/'field.csv'),
            SNESRECOMP_FOUNDATION_FIELD_TRACE=str(directory/'terrain.csv'),
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced),
            SNESRECOMP_FOUNDATION_BATTLE_INFO='0', SNESRECOMP_FOUNDATION_JOURNAL='0',
            SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_HD_MENU_FRAMES='0',
            SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0', SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',
            SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE=','.join(map(str, sequence)),
            SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(directory/'captures'))
        if wide:
            env['SNESRECOMP_FOUNDATION_ACTORS_TRACE'] = str(directory/'actors.csv')
        if save is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save), SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load), SNESRECOMP_RUN_FRAMES=str(load+100))
        command = [str(directory/'game.exe'), '--no-launcher', '--rom', str(rom)]
        if state:
            command += ['--resume-state', str(directory/'resume.state')]
        command += ['--script', str(directory/'input.txt')]
        with (directory/'host.log').open('w') as log:
            result = subprocess.run(command, cwd=directory, env=env, stdout=log, stderr=log,
                timeout=180, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        text = (directory/'host.log').read_text(errors='replace')
        report['cases'][name] = {'exit': result.returncode, 'resume_requested': bool(state),
            'executable_sha256': sha(directory/'game.exe'),
            'resumed': 'resume state loaded:' in text, 'gamepads_disabled': 'enable_gamepad=[0,0]' in text,
            'script_sha256': hashlib.sha256(script.encode()).hexdigest(), 'wide': wide, 'enhanced': enhanced,
            'snapshot_scenes': {}, 'terrain_summary': {}}
        for p in (directory/'dump').glob('*.wram.bin'):
            ram = p.read_bytes(); tag = p.name[:-len('.wram.bin')]
            report['cases'][name]['snapshot_scenes'][tag] = {
                'scene': int.from_bytes(ram[0x40e:0x410], 'little'), 'mode': ram[0x20], 'wrap': ram[0x407]}
        data = rows(directory/'terrain.csv')
        for key in ('accepted_lines', 'rejected_lines', 'tile_mismatches', 'pixel_mismatches',
                    'stale_margin_words', 'title_lines', 'battle_lines'):
            report['cases'][name]['terrain_summary'][key] = sum(number(r, key) for r in data)
        return directory

    def pair(name, state, script, enhanced=0, **kwargs):
        off = run(name+'-off', state, script, 0, enhanced=enhanced, **kwargs)
        on = run(name+'-on', state, script, 1, enhanced=enhanced, **kwargs)
        a_tags = sorted(p.name[:-len('.wram.bin')] for p in (off/'dump').glob('*.wram.bin'))
        b_tags = sorted(p.name[:-len('.wram.bin')] for p in (on/'dump').glob('*.wram.bin'))
        checks[name+'_snapshot_tags_match'] = bool(a_tags) and a_tags == b_tags
        checks[name+'_all_guest_files_identical'] = bool(a_tags) and all(
            (off/'dump'/f'{tag}.{ext}').read_bytes() == (on/'dump'/f'{tag}.{ext}').read_bytes()
            for tag in a_tags for ext in GUEST)
        for trace in ('cpu', 'state', 'field'):
            checks[name+'_'+trace+'_identical'] = (off/(trace+'.csv')).read_bytes() == (on/(trace+'.csv')).read_bytes()
        a = {read_surface(p)[0]: p for p in (off/'captures').glob('*.bgrx')}
        b = {read_surface(p)[0]: p for p in (on/'captures').glob('*.bgrx')}
        checks[name+'_capture_steps_match'] = bool(a) and set(a) == set(b)
        metrics = {}
        for frame in sorted(set(a) & set(b)):
            _, original = read_surface(a[frame]); _, expanded = read_surface(b[frame])
            scale = 2 if enhanced else 1; left = 72*scale; right = 328*scale
            dimensions = original.shape == (224*scale, 256*scale, 4) and expanded.shape == (224*scale, 400*scale, 4)
            center = np.array_equal(original, expanded[:, left:right]) if dimensions else False
            sides = np.concatenate((expanded[:, :left, :3], expanded[:, right:, :3]), axis=1)
            nonblack = np.any(sides != 0, axis=2)
            metrics[str(frame)] = {'original_width': original.shape[1], 'width': expanded.shape[1],
                'height': expanded.shape[0], 'dimensions_correct': dimensions,
                'original256_center_identical': center, 'nonblack_margin_pixels': int(nonblack.sum()),
                'margin_colors': len(np.unique(sides.reshape(-1, 3), axis=0))}
        checks[name+'_all_requested_widths_stable400'] = bool(metrics) and all(m['dimensions_correct'] for m in metrics.values())
        checks[name+'_composed_center256_identical'] = bool(metrics) and all(m['original256_center_identical'] for m in metrics.values())
        report['surfaces'][name] = metrics
        # Export only representative private pixels, not every compositor frame.
        samples = [f for f in sorted(b) if metrics[str(f)]['nonblack_margin_pixels'] > 0]
        for frame in ([samples[0], samples[-1]] if samples else []):
            _, pixels = read_surface(b[frame])
            Image.fromarray(pixels[:, :, :3][:, :, ::-1]).save(b[frame].with_suffix('.png'))
        return off, on

    def qualify_map(name, scene):
        on = base/(name+'-on')
        seen = report['cases'][name+'-on']['snapshot_scenes']
        checks[name+'_expected_scene_observed'] = any(s['scene'] == scene and s['mode'] == 1 for s in seen.values())
        data = rows(on/'terrain.csv')
        checks[name+'_actual_map_lines_presented'] = any(number(r, 'accepted_lines') > 0 for r in data)
        checks[name+'_positive_original_scenery_margins'] = any(m['nonblack_margin_pixels'] > 0 and m['margin_colors'] > 2
            for m in report['surfaces'][name].values())
        checks[name+'_no_published_pixel_mismatch'] = not any(number(r, 'pixel_mismatches') for r in data)
        if scene in (5, 12):
            packets = packet_lineage(rows(on/'actors.csv'))
            report['actor_packets'][name] = packets
            for key, value in packets['checks'].items():
                checks[name+'_'+key] = value
            checks[name+'_expected_packet_scene_active'] = scene in packets['scenes']

    try:
        fields = [('house', 12, IDLE), ('town', 5, SWEEP), ('world', 0, SWEEP),
                  ('opening', 38, IDLE), ('island', 39, SWEEP)]
        for name, scene, script in fields:
            for enhanced in (0, 1):
                case = name + ('-enhanced' if enhanced else '')
                if wanted(case):
                    pair(case, states[name], script, enhanced=enhanced)
                    qualify_map(case, scene)
        for name, state, script in [('transition', states['house'], TRANSITION),
                                    ('menu', states['town'], MENU)]:
            if wanted(name):
                pair(name, state, script, enhanced=1)
                if name == 'transition':
                    observed = report['cases'][name+'-on']['snapshot_scenes']
                    checks['natural_house_to_town_both_scenes_observed'] = {12, 5} <= {s['scene'] for s in observed.values()}
                    data = rows(base/(name+'-on')/'actors.csv')
                    packets = packet_lineage(data); report['actor_packets'][name] = packets
                    checks['transition_completed_packet_lineage'] = packets['checks']['actual_completed_packet_lineage']
                    checks['transition_both_packet_scene_identities'] = {12, 5} <= set(packets['scenes'])
                    checks['transition_invalidates_old_resource_packet'] = any(r['event'] == 'reject_scene' for r in data)
        if wanted('warm-entry'):
            pair('warm-entry', states['world'], WARM_ENTRY, enhanced=1)
            seen = report['cases']['warm-entry-on']['snapshot_scenes']
            checks['warm_entry_natural_world_and_battle_observed'] = any(s['mode'] == 1 for s in seen.values()) and any(s['mode'] == 5 for s in seen.values())
            checks['warm_entry_actual_forest_lines_presented'] = any(number(r, 'battle_lines') > 0
                for r in rows(base/'warm-entry-on/terrain.csv'))
        if reference and wanted('legacy-replay'):
            old = run('legacy-reference', states['legacy'], SWEEP, 0, executable=reference)
            pair('legacy-replay', states['legacy'], SWEEP, enhanced=1)
            old_log = (old/'host.log').read_text(errors='replace')
            report['legacy_reference_crash'] = {'exit': report['cases']['legacy-reference']['exit'],
                'reproduced_access_violation': 'SEH CRASH code=0xC0000005' in old_log,
                'executable_sha256': sha(reference), 'scope': 'Earlier-build failure control; candidate must exit normally'}
            checks['legacy_reference_reproduces_known_access_violation'] = (
                report['cases']['legacy-reference']['exit'] != 0 and 'SEH CRASH code=0xC0000005' in old_log and
                report['cases']['legacy-reference']['resumed'] and report['cases']['legacy-reference']['gamepads_disabled'])
            checks['legacy_candidate_original_width_and_wide_exit_zero'] = all(
                report['cases']['legacy-replay-'+suffix]['exit'] == 0 for suffix in ('off', 'on'))
            for trace in ('cpu', 'field'):
                earlier = (old/(trace+'.csv')).read_bytes().splitlines()
                current = (base/'legacy-replay-off'/(trace+'.csv')).read_bytes().splitlines()
                checks['legacy_'+trace+'_matches_reference_until_crash'] = bool(earlier) and current[:len(earlier)] == earlier
            earlier_state = (old/'state.csv').read_bytes().splitlines()
            current_state = (base/'legacy-replay-off/state.csv').read_bytes().splitlines()
            report['legacy_reference_state_trace'] = {'available_rows': len(earlier_state),
                'scope': ('Compare flushed reference rows only' if earlier_state else
                    'Unavailable: host_main.c writes buffered state_trace and closes only on normal exit; reference hard-crashes before flush'),
                'source': 'snesrecomp/runner/src/desktop/host_main.c:4219-4249'}
            if earlier_state:
                checks['legacy_available_state_trace_matches_reference_until_crash'] = current_state[:len(earlier_state)] == earlier_state
            survived = sorted(p.name[:-len('.wram.bin')] for p in (old/'dump').glob('*.wram.bin'))
            details = {tag: {ext: (old/'dump'/f'{tag}.{ext}').read_bytes() ==
                (base/'legacy-replay-off/dump'/f'{tag}.{ext}').read_bytes() for ext in GUEST} for tag in survived}
            report['legacy_precrash_snapshot_comparison'] = details
            checks['legacy_available_precrash_guest_snapshots_all_exact'] = bool(details) and all(
                exact for comparison in details.values() for exact in comparison.values())
        if (wanted('title') or wanted('title-enhanced')) and not args.title_state:
            generated = run('save-title-source', None, 'wait 6900\ndump title\nquit\n', 1, save=6700)
            states['title'] = generated/'saves/save0.sav'
            checks['fresh_cold_title_checkpoint_generated'] = states['title'].exists()
            if states['title'].exists():
                inputs[str(states['title'])] = sha(states['title'])
            checks['cold_boot_reaches_visible_title_panorama'] = any(
                number(r, 'title_lines') > 0 for r in rows(generated/'terrain.csv'))
        for enhanced in (0, 1):
            name = 'title' + ('-enhanced' if enhanced else '')
            if wanted(name):
                wait = args.title_wait if args.title_wait is not None else 240
                script = 'wait '+str(wait)+'\ndump title\nquit\n'
                pair(name, states.get('title'), script, enhanced=enhanced)
                data = rows(base/(name+'-on')/'terrain.csv')
                checks[name+'_actual_title_lines_presented'] = any(number(r, 'title_lines') > 0 for r in data)
                checks[name+'_positive_panorama_margin_pixels'] = any(m['nonblack_margin_pixels'] > 0 and m['margin_colors'] > 2
                    for m in report['surfaces'][name].values())
                # Actual per-line scroll range establishes HDMA/parallax scanout.
                checks[name+'_actual_raster_scroll_varies'] = any(
                    number(r, 'title_bg2_max_hscroll') > number(r, 'title_bg2_min_hscroll') for r in data)
        for enhanced in (0, 1):
            name = 'battle' + ('-enhanced' if enhanced else '')
            if wanted(name):
                pair(name, states['battle'], BATTLE, enhanced=enhanced)
                data = rows(base/(name+'-on')/'terrain.csv')
                checks[name+'_actual_forest_background_lines'] = any(number(r, 'battle_lines') > 0 for r in data)
                checks[name+'_nonblank_background_margins'] = any(m['nonblack_margin_pixels'] > 0 and m['margin_colors'] > 2
                    for m in report['surfaces'][name].values())
                checks[name+'_command_target_action_all_battle'] = all(
                    report['cases'][name+'-on']['snapshot_scenes'].get(tag, {}).get('mode') == 5
                    for tag in ('command', 'target', 'action10'))
                hp = {}
                for tag in ['command', 'target', 'action10', 'action50', 'action140'] + ['damage'+str(i) for i in range(1, 7)]:
                    ram = (base/(name+'-on')/'dump'/f'{tag}.wram.bin').read_bytes()
                    hp[tag] = {'mode': ram[0x20], 'hp': [int.from_bytes(ram[0x6101+i*0x1c:0x6103+i*0x1c], 'little')
                        for i in range(4) if not ram[0x6100+i*0x1c] & 0x80]}
                report['cases'][name+'-on']['enemy_hp_snapshots'] = hp
                initial = sum(hp['command']['hp'])
                checks[name+'_real_attack_reduces_enemy_hp'] = bool(hp['command']['hp']) and any(
                    sample['mode'] == 5 and sum(sample['hp']) < initial for sample in hp.values())
        if wanted('cold') or wanted('rollback'):
            saved = run('save-source', states['town'], 'wait 92\ndump end\nquit\n', 1, save=32)
            copied = saved/'saves/save0.sav'
            checks['generated_copied_checkpoint_exists'] = copied.exists()
            if wanted('cold'):
                pair('cold', copied, IDLE, enhanced=1)
                packets = packet_lineage(rows(base/'cold-on/actors.csv')); report['actor_packets']['cold'] = packets
                for key, value in packets['checks'].items(): checks['cold_'+key] = value
            if wanted('rollback'):
                pair('rollback', states['town'], MENU, enhanced=1, save=32, load=150)
                data = rows(base/'rollback-on/actors.csv')
                packets = packet_lineage(data); report['actor_packets']['rollback'] = packets
                for key, value in packets['checks'].items(): checks['rollback_'+key] = value
                checks['actual_rollback_load_issued'] = '[overlay_selftest] load issued' in (base/'rollback-on/host.log').read_text(errors='replace')
                checks['rollback_frame_moves_back_and_derived_cache_clears'] = any(
                    current['event'] == 'reset' and number(current, 'frame') < number(previous, 'frame') and
                    not number(current, 'packet_valid') and not number(current, 'cached_actors')
                    for previous, current in zip(data, data[1:]))
        if 'transition' in report['surfaces']:
            data = rows(base/'transition-on/terrain.csv')
            fallback = [i+1 for i, r in enumerate(data) if not any(number(r, k)
                for k in ('accepted_lines', 'title_lines', 'battle_lines'))]
            captured = report['surfaces']['transition']
            checks['unsupported_transition_has_stable_black_margins'] = any(
                str(i) in captured and captured[str(i)]['nonblack_margin_pixels'] == 0 for i in fallback)
        checks['all_processes_exit_resume_and_disable_gamepads'] = bool(report['cases']) and all(
            c['exit'] == 0 and c['gamepads_disabled'] and (not c['resume_requested'] or c['resumed'])
            for name, c in report['cases'].items() if name != 'legacy-reference')
        checks['source_inputs_preserved'] = all(sha(Path(path)) == value for path, value in inputs.items())
        checks['owner_profile_files_preserved'] = all(Path(path).exists() and sha(Path(path)) == value for path, value in owner.items())
    except Exception as error:
        report['error'] = repr(error)
        checks['suite_completed_without_error'] = False
    report['limits'] = [
        'Finite copied maps and forest battle; original artwork upscale is distinct from replacement HD art',
        'Other map/story variants, world wrap seams, party/composite/effect margin actors and other battle themes remain unqualified',
        'Cold title/raster positivity must pass; black startup is not positive title panorama evidence',
        'Headless original-center/guest parity is separate from paced GPU/audio and physical-controller coverage',
        'Wide output stays400 with guarded black margins on unsupported presentation; Original View remains256',
        'All ROM-derived captures, checkpoints and extracts remain private under local/']
    report['passed'] = bool(checks) and all(checks.values())
    (base/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(base)
    print(json.dumps({'passed': report['passed'], 'checks': checks, 'error': report.get('error')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
