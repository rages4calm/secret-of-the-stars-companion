"""Measure input and host frame time in disposable field-menu fixtures."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe')
    parser.add_argument('--checkpoint', type=Path, default=ROOT / 'local/player-foundation/saves/save0.sav')
    parser.add_argument('--fast-menus', type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    base = ROOT / 'local/runs' / ('menu-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    report = {'executable_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(),
              'checkpoint_sha256': hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
              'fast_menus': args.fast_menus, 'cases': {}}
    for name, enhanced, headless in [('original-headless', 0, True), ('enhanced-headless', 1, True),
                                     ('original-windows', 0, False), ('enhanced-windows', 1, False)]:
        run = base / name
        run.mkdir()
        shutil.copy2(args.exe, run / 'game.exe')
        shutil.copy2(args.checkpoint, run / 'resume.state')
        (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nWindowScale=2\nFullscreen=0\nVSync=1\nNewRenderer=0\n'
            '[Sound]\nEnableAudio=' + str(int(not headless)) + '\nVolume=70\nAudioFreq=32040\nAudioSamples=512\n'
            '[General]\nAutosave=0\nRunAhead=0\nDisableFrameDelay=' + str(int(headless)) + '\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (run / 'input.txt').write_text('wait 30\npress b 1\nwait 89\ndump menu\npress b 1\nwait 120\ndump field\nquit\n')
        (run / 'dump').mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_FOUNDATION_TRACE=str(run / 'foundation.csv'),
            SNESRECOMP_FOUNDATION_FAST_MENUS=str(args.fast_menus),
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced), SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FRAME_TIMING=str(run / 'timing.csv'), SNESRECOMP_HOST_PROFILE='1',
            SNESRECOMP_DUMP_DIR=str(run / 'dump'))
        if headless:
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        if name == 'original-headless':
            env['SNESRECOMP_FOUNDATION_VIDEO_RAW'] = str(run / 'video.bgrx')
        with (run / 'host.log').open('w') as log:
            result = subprocess.run([str(run / 'game.exe'), '--no-launcher', '--rom',
                str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(run / 'resume.state'),
                '--script', str(run / 'input.txt')], cwd=run, env=env, stdout=log, stderr=log,
                timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0
        rows = list(csv.DictReader((run / 'foundation.csv').open()))
        transitions = []
        previous = None
        for i, row in enumerate(rows):
            signature = [int(row[key]) for key in ('mode', 'input', 'brightness', 'forced_blank', 'bgmode', 'ram_02e3')]
            if signature != previous:
                transitions.append({'host_frame': i + 1, 'guest_frame': int(row['frame']),
                    **dict(zip(('mode', 'input', 'brightness', 'forced_blank', 'bgmode', 'ram_02e3'), signature))})
                previous = signature
        timings = list(csv.DictReader((run / 'timing.csv').open()))
        metrics = {key: {'median': statistics.median(float(r[key]) for r in timings),
                         'max': max(float(r[key]) for r in timings)}
                   for key in ('guest_ms', 'raster_ms', 'compose_ms', 'present_ms', 'wait_ms')}
        report['cases'][name] = {'exit': result.returncode, 'transitions': transitions, 'timings_ms': metrics}
    report['enhanced_guest_identical'] = all(
        (base / 'original-headless/dump' / (tag + '.' + suffix)).read_bytes() ==
        (base / 'enhanced-headless/dump' / (tag + '.' + suffix)).read_bytes()
        for tag in ('menu', 'field') for suffix in ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx'))
    report['passed'] = report['enhanced_guest_identical'] and all(case['exit'] == 0 for case in report['cases'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    for name, case in report['cases'].items():
        print(name, 'transitions=', json.dumps(case['transitions']), 'timings=', json.dumps(case['timings_ms']))
    print('Enhanced guest identical:', report['enhanced_guest_identical'])
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
