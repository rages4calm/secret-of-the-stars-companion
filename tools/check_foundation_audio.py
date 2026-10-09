"""Measure actual SDL callback PCM after cold loading copied checkpoints."""
from pathlib import Path
import argparse
import array
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'


def main():
    global EXE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    EXE = parser.parse_args().exe.resolve()
    base = ROOT / 'local/runs' / ('audio-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    original = ROOT / 'local/runs/clean-to-outdoors/saves/save0.sav'
    report = {'executable_sha256': hashlib.sha256(EXE.read_bytes()).hexdigest(), 'cases': {}}
    for name in ['legacy', 'current-a', 'current-b']:
        run = base / name
        run.mkdir()
        shutil.copy2(EXE, run / 'game.exe')
        shutil.copy2(original if name == 'legacy' else base / 'legacy/saves/save0.sav', run / 'resume.state')
        (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
            '[Sound]\nEnableAudio=1\nVolume=70\nAudioFreq=32040\nAudioChannels=2\n'
            '[General]\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (run / 'input.txt').write_text('wait 180\ndump idle\nquit\n')
        (run / 'dump').mkdir()
        case_env = dict(env, SNESRECOMP_AUDIO_OUTPUT_RAW=str(run / 'output.pcm'),
                        SNESRECOMP_FOUNDATION_TRACE=str(run / 'foundation.csv'),
                        SNESRECOMP_DUMP_DIR=str(run / 'dump'))
        if name == 'legacy':
            case_env.update(SNESRECOMP_OVERLAY_SELFTEST='120', SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        with (run / 'host.log').open('w') as log:
            result = subprocess.run([str(run / 'game.exe'), '--no-launcher', '--rom',
                str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(run / 'resume.state'),
                '--script', str(run / 'input.txt')], cwd=run, env=case_env,
                stdout=log, stderr=log, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
        pcm = array.array('h', (run / 'output.pcm').read_bytes())
        first = next((i // 2 / 32040 for i, value in enumerate(pcm) if value), None)
        report['cases'][name] = {'exit': result.returncode, 'first_nonzero_seconds': first,
            'peak': max(map(abs, pcm), default=0), 'stereo_frames': len(pcm) // 2,
            'resume_consumed': not (run / 'resume.state').exists(),
            'passed': result.returncode == 0 and first is not None and first < 0.5}
    report['current_replays_identical'] = all(
        (base / 'current-a/dump' / ('idle.' + suffix)).read_bytes() ==
        (base / 'current-b/dump' / ('idle.' + suffix)).read_bytes()
        for suffix in ['wram.bin', 'vram.bin', 'sram.bin', 'fb.bgrx'])
    report['passed'] = all(case['passed'] for case in report['cases'].values()) and report['current_replays_identical']
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
