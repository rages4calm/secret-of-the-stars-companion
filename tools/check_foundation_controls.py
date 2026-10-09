"""Exercise SDL virtual-pad gameplay and overlay exits in disposable profiles."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'
STATE = ROOT / 'local/runs/clean-to-outdoors/saves/save0.sav'
CONFIG = '''[Graphics]
Renderer=software
VSync=0
[Sound]
EnableAudio=0
[General]
DisableFrameDelay=1
Autosave=0
RunAhead=0
[GamepadMap]
EnableGamepad1=1
EnableGamepad2=1
Controls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1
[KeyMap]
SaveStateMenu=F7
Rewind=F8
'''
# Virtual-device events set after the event pump arrive on the following frame.
STEPS = [(11, None), (20, 'right'), (19, None), (20, 'down'), (19, None),
         (2, 'b'), (27, None), (2, 'a'), (27, None), (2, 'b'),
         (27, None), (2, 'b'), (57, None)]


def main():
    global EXE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    EXE = parser.parse_args().exe.resolve()
    base = ROOT / 'local/runs' / ('controls-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(parents=True, exist_ok=False)
    report = {'binary_sha256': hashlib.sha256(EXE.read_bytes()).hexdigest(),
              'physical_controller': 'Owner confirmed repaired controls, original video/audio and basic combat on 2026-10-08; new enhanced presentation is automated only',
              'profiles': {}}
    for kind in ('virtual', 'script', 'idle', 'pad-exit', 'escape', 'toggle', 'cancel'):
        run = base / kind
        run.mkdir()
        shutil.copy2(EXE, run / EXE.name)
        shutil.copy2(STATE, run / 'resume.state')
        (run / 'config.ini').write_text(CONFIG)
        env = os.environ.copy()
        for key in list(env):
            if key.startswith('SNESRECOMP_'):
                env.pop(key)
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   SNESRECOMP_RUN_FRAMES='242', SNESRECOMP_DUMP_DIR=str(run),
                   SNESRECOMP_STATE_TRACE=str(run / 'state.csv'))
        env.update(SNESRECOMP_FOUNDATION_BATTLE_INFO='1', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',
                   SNESRECOMP_FOUNDATION_FAST_MENUS='1')
        if kind == 'virtual':
            env['SNESRECOMP_GAMEPAD_GAMEPLAY_SELFTEST'] = '1'
        elif kind not in ('script', 'idle'):
            env['SNESRECOMP_OVERLAY_SELFTEST_PAD'] = '30'
            if kind != 'pad-exit':
                env['SNESRECOMP_OVERLAY_SELFTEST_EXIT'] = kind
        script = []
        for index, (frames, button) in enumerate(STEPS):
            # The script runner consumes one release frame after a press.
            script.append(f'press {button} {frames}' if button and kind == 'script'
                          else f'wait {frames + bool(button)}')
            script.append(f'dump step{index:02}')
        (run / 'inputs.txt').write_text('\n'.join(script) + '\n')
        args = [str(run / EXE.name), '--no-launcher', '--rom', str(ROOT / 'local/inputs/clean-usa.sfc'),
                '--resume-state', str(run / 'resume.state'), '--script', str(run / 'inputs.txt')]
        with (run / 'host.log').open('w') as log:
            result = subprocess.run(args, cwd=run, env=env, stdout=log, stderr=log, timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        log = (run / 'host.log').read_text(errors='replace')
        ok = result.returncode == 0 and 'resume state loaded:' in log
        if kind not in ('virtual', 'script', 'idle'):
            ok &= 'ok: browser and rewind both opened and closed from the pad' in log
            ok &= 'FAIL' not in log
        report['profiles'][kind] = {'exit_code': result.returncode, 'passed': bool(ok)}
    virtual = (base / 'virtual/state.csv').read_bytes()
    scripted = (base / 'script/state.csv').read_bytes()
    report['virtual_guest_trace_matches_script'] = virtual == scripted
    report['virtual_changes_guest_vs_idle'] = virtual != (base / 'idle/state.csv').read_bytes()
    report['guest_dumps_match'] = all(
        p.read_bytes() == (base / 'script' / p.name).read_bytes()
        for p in (base / 'virtual').glob('step*.*'))
    report['passed'] = all(p['passed'] for p in report['profiles'].values()) and \
        report['virtual_guest_trace_matches_script'] and report['virtual_changes_guest_vs_idle'] and report['guest_dumps_match']
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
