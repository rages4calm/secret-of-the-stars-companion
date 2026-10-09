"""Verify native HP HUD and bounded additional-field rendering on copied states."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'


def main():
    base = ROOT / 'local/runs' / ('presentation-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    cases = [('battle-original', 'world-cave-a', 0, 0, False),
             ('battle-info', 'world-cave-a', 1, 0, False),
             ('battle-x-original', 'world-cave-a', 0, 0, True),
             ('battle-x-info', 'world-cave-a', 1, 0, True),
             ('field-original', 'battle-return-a', 0, 0, False),
             ('field-wide', 'battle-return-a', 0, 1, False),
             ('battle-wide-request', 'world-cave-a', 0, 1, False),
             ('battle-enhanced', 'world-cave-a', 0, 0, False),
             ('battle-enhanced-info', 'world-cave-a', 1, 0, False),
             ('field-enhanced', 'battle-return-a', 0, 0, False)]
    report = {'executable_sha256': hashlib.sha256(EXE.read_bytes()).hexdigest(), 'cases': {}}
    for name, checkpoint, info, wide, toggle in cases:
        run = base / name
        run.mkdir()
        (run / 'dump').mkdir()
        shutil.copy2(EXE, run / 'game.exe')
        shutil.copy2(ROOT / 'local/runs' / checkpoint / 'saves/save0.sav', run / 'resume.state')
        (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (run / 'input.txt').write_text(('wait 30\npress x 2\nwait 58\n' if toggle else 'wait 92\n') + 'dump end\nquit\n')
        env = dict(clean_env, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
            SNESRECOMP_FOUNDATION_BATTLE_INFO=str(info), SNESRECOMP_FOUNDATION_WIDE=str(wide),
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1' if 'enhanced' in name else '0',
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(run / 'present.bgrx'),
            SNESRECOMP_FOUNDATION_CAPTURE_AT='60', SNESRECOMP_DUMP_DIR=str(run / 'dump'))
        with (run / 'host.log').open('w') as log:
            result = subprocess.run([str(run / 'game.exe'), '--no-launcher', '--rom',
                str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(run / 'resume.state'),
                '--script', str(run / 'input.txt')], cwd=run, env=env,
                stdout=log, stderr=log, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        raw = (run / 'present.bgrx').read_bytes()
        width, height = map(int, re.search(r'composed capture (\d+)x(\d+)', (run / 'host.log').read_text()).groups())
        assert len(raw) == width * height * 4
        Image.frombytes('RGB', (width, height), raw, 'raw', 'BGRX').save(run / 'present.png')
        report['cases'][name] = {'exit': result.returncode, 'width': width, 'height': height,
            'composed_sha256': hashlib.sha256(raw).hexdigest()}
    def same_guest(a, b):
        return all((base / a / 'dump' / ('end.' + ext)).read_bytes() ==
                   (base / b / 'dump' / ('end.' + ext)).read_bytes()
                   for ext in ['wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin'])
    def surface(name):
        return (base / name / 'present.bgrx').read_bytes()
    report['hud_preserves_guest'] = same_guest('battle-original', 'battle-info')
    report['hud_changes_composed_pixels'] = surface('battle-original') != surface('battle-info')
    report['x_hide_preserves_guest'] = same_guest('battle-x-original', 'battle-x-info')
    report['x_hide_restores_original_surface'] = surface('battle-x-original') == surface('battle-x-info')
    report['wide_preserves_guest'] = same_guest('field-original', 'field-wide')
    wide, original = surface('field-wide'), surface('field-original')
    report['unsupported_field_request_retains_original_view'] = \
        report['cases']['field-wide']['width'] == 256 and wide == original
    report['battle_retains_original_width'] = report['cases']['battle-wide-request']['width'] == 256
    for scene in ['battle', 'field']:
        report[scene + '_enhanced_preserves_guest'] = same_guest(scene + '-original', scene + '-enhanced')
        a, b = surface(scene + '-original'), surface(scene + '-enhanced')
        colors = {a[i:i+4] for i in range(0, len(a), 4)}
        report[scene + '_enhanced_preserves_source_colors'] = all(b[i:i+4] in colors for i in range(0, len(b), 4))
        nearest = b''.join(b''.join(a[(y*256+x)*4:(y*256+x+1)*4] * 2 for x in range(256)) * 2 for y in range(224))
        report[scene + '_enhanced_changes_diagonal_edges'] = b != nearest
    report['enhanced_hud_preserves_guest'] = same_guest('battle-enhanced', 'battle-enhanced-info')
    report['passed'] = all(v for k, v in report.items() if isinstance(v, bool)) and \
        all(case['exit'] == 0 for case in report['cases'].values())
    report['wide_visual_gate_passed'] = False
    report['wide_visual_limitation'] = 'Campaign widescreen remains unqualified. Likado terrain has its own focused checker; this fixture uses original width.'
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
