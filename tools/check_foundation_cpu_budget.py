"""Verify read-only CPU-field telemetry with paired, copied finite fixtures."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
GUEST_EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx')
CAUSES = ('deadline_events', 'deadline_unwind_events', 'quiescent_events',
          'stable_poll_events', 'wai_events', 'irq_events', 'step_cap_events', 'other_events')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(rows):
    result = {'measured_fields': len(rows), 'valid_fields': sum(int(r['valid']) for r in rows),
              'resume_evictions': sum(int(r['resume_evicted']) for r in rows),
              'resume_events': sum(int(r['resume_events']) for r in rows),
              'guest_modes': sorted({int(r['mode']) for r in rows}),
              'causes': {name: sum(int(r[name]) for r in rows) for name in CAUSES}}
    for key in ('cpu_cycles', 'master_cycles', 'interp_cpu_cycles', 'interp_insns'):
        values = [int(r[key]) for r in rows]
        result[key] = {'min': min(values), 'median': statistics.median(values), 'max': max(values)}
    result['deadline_resume_pcs'] = dict(collections.Counter(
        f"{int(r['last_deadline_pc']):06X}" for r in rows if int(r['last_deadline_pc'])))
    waiting = [r for r in rows if int(r['nmi_wait_iterations'])]
    result['nmi_wait_observed_fields'] = len(waiting)
    result['nmi_wait_deadline_fields'] = sum(int(r['last_deadline_pc']) in (0x8414, 0x8417) for r in rows)
    result['other_deadline_fields'] = sum(int(r['last_deadline_pc']) not in (0, 0x8414, 0x8417) for r in rows)
    if waiting:
        for key in ('pre_wait_master_cycles', 'pre_wait_cpu_cycles', 'nmi_wait_iterations'):
            values = [int(r[key]) for r in waiting]
            result[key] = {'min': min(values), 'median': statistics.median(values), 'max': max(values)}
    held_segments = []
    start = 0
    while start < len(rows):
        end = start + 1
        key = int(rows[start]['input'])
        while end < len(rows) and int(rows[end]['input']) == key:
            end += 1
        if key:
            deltas = []
            for index in range(start + 1, end):
                prev, current = rows[index - 1], rows[index]
                deltas.append(tuple((int(current[field]) - int(prev[field]) + 512) % 1024 - 512
                                    for field in ('bg1_scroll_x', 'bg1_scroll_y')))
            held_segments.append({'input': key, 'frames': end - start,
                'camera_delta_counts': {str(k): v for k, v in collections.Counter(deltas).items()}})
        start = end
    result['held_input_camera_segments'] = held_segments
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path,
        default=ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build-menu/SecretOfTheStarsSNESRecomp.exe')
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    base = ROOT / 'local/runs' / ('cpu-budget-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    cases = [
        ('town', ROOT / 'local/runs/likado-east-a/saves/save0.sav',
         'wait 60\ndump before\npress left 90\nwait 30\npress right 160\nwait 30\n'
         'press down 60\nwait 30\ndump after\nquit\n'),
        ('battle', ROOT / 'local/runs/world-cave-a/saves/save0.sav',
         (ROOT / 'local/runs/native-damage-original/input.txt').read_text()),
        ('transition', ROOT / 'local/runs/likado-inside-a/saves/save0.sav',
         'wait 10\ndump before\npress down 96\nwait 120\ndump after\nquit\n'),
    ]
    report = {'executable_sha256': digest(args.exe), 'cases': {}, 'checks': {},
        'source_checkpoint_sha256': {name: digest(state) for name, state, _ in cases},
        'measurement_scope': 'Guest CPU half between BeginFrame and Frame; total master clocks and interpreted CPU cycles are different units',
        'limits': ['Finite town, two-Red-Slime battle and indoor exit fixtures; no manufactured CPU stress',
            'Observer equality proves the observer is read-only, not complete game timing fidelity',
            'Deadline events alone do not establish a missed productive update',
            'Original CPU budget remains in place; no overclock or slowdown-removal enhancement is implemented',
            'Headless output and audio disabled; this is not physical controller/display or audible-audio qualification']}
    for name, state, script in cases:
        pair = {}
        for enabled in (False, True):
            label = name + ('-on' if enabled else '-off')
            run = base / label
            run.mkdir()
            (run / 'dump').mkdir()
            shutil.copy2(args.exe, run / 'game.exe')
            shutil.copy2(state, run / 'resume.state')
            (run / 'input.txt').write_text(script)
            (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
                '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
                '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
            env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                SNESRECOMP_DUMP_DIR=str(run / 'dump'),
                SNESRECOMP_FOUNDATION_TRACE=str(run / 'foundation.csv'),
                SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
                SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0', SNESRECOMP_FOUNDATION_WIDE='0')
            if enabled:
                env['SNESRECOMP_FOUNDATION_CPU_TRACE'] = str(run / 'cpu.csv')
            with (run / 'host.log').open('w') as log:
                result = subprocess.run([str(run / 'game.exe'), '--no-launcher', '--rom',
                    str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(run / 'resume.state'),
                    '--script', str(run / 'input.txt')], cwd=run, env=env, stdout=log, stderr=log,
                    timeout=40, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            host = (run / 'host.log').read_text(errors='replace')
            report['cases'][label] = {'exit': result.returncode,
                'resumed': 'resume state loaded:' in host, 'cpu_trace_exists': (run / 'cpu.csv').exists()}
            pair[enabled] = run
        off, on = pair[False], pair[True]
        tags = [p.name[:-len('.wram.bin')] for p in (off / 'dump').glob('*.wram.bin')]
        report['checks'][name + '_six_guest_dumps_identical'] = bool(tags) and all(
            (off / 'dump' / (tag + '.' + ext)).read_bytes() ==
            (on / 'dump' / (tag + '.' + ext)).read_bytes() for tag in tags for ext in GUEST_EXTENSIONS)
        report['checks'][name + '_existing_field_trace_identical'] = (
            off / 'foundation.csv').read_bytes() == (on / 'foundation.csv').read_bytes()
        report['checks'][name + '_off_creates_no_cpu_trace'] = not (off / 'cpu.csv').exists()
        rows = list(csv.DictReader((on / 'cpu.csv').open()))
        report['cases'][name + '-on']['cpu_summary'] = summary(rows)
        report['checks'][name + '_all_fields_measured'] = len(rows) == len(
            list(csv.DictReader((on / 'foundation.csv').open())))
        report['checks'][name + '_counters_valid_no_eviction'] = bool(rows) and all(
            int(r['valid']) == 1 and int(r['resume_evicted']) == 0 for r in rows)
        report['checks'][name + '_causes_accounted'] = all(
            sum(int(r[key]) for key in CAUSES) == int(r['resume_events']) for r in rows)
        report['checks'][name + '_no_step_cap'] = all(int(r['step_cap_events']) == 0 for r in rows)
        report['checks'][name + '_guarded_wait_hook_registered'] = all(int(r['nmi_wait_hook']) == 1 for r in rows)
        if name == 'transition':
            field_rows = list(csv.DictReader((on / 'foundation.csv').open()))
            blank = sum(int(r['forced_blank']) for r in field_rows)
            report['transition_evidence'] = {'forced_blank_fields': blank,
                'before_after_vram_differs': (on / 'dump/before.vram.bin').read_bytes() !=
                    (on / 'dump/after.vram.bin').read_bytes(),
                'last_mode': int(field_rows[-1]['mode']),
                'non_wait_deadlines': [dict(frame=int(c['frame']), pc=f"{int(c['last_deadline_pc']):06X}",
                    forced_blank=int(f['forced_blank'])) for c, f in zip(rows, field_rows)
                    if int(c['last_deadline_pc']) not in (0, 0x8414, 0x8417)]}
            report['checks']['transition_has_loading_blank_and_returns_field'] = (
                blank > 0 and report['transition_evidence']['before_after_vram_differs'] and
                report['transition_evidence']['last_mode'] == 1)
        report['checks'][name + '_source_checkpoint_preserved'] = digest(state) == report['source_checkpoint_sha256'][name]
    report['passed'] = all(report['checks'].values()) and all(
        case['exit'] == 0 and case['resumed'] for case in report['cases'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
