"""Check reward checkpoint replay and movement exclusions with copied private inputs.

Supply the same qualified battle/town fixture layout as check_foundation_qol.py.
This finite dummy-SDL probe tests actual guest execution; it does not certify a
campaign, physical controller, or audible audio. Input files stay unmodified.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import time

from check_foundation_qol import guest, same, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--fixtures-root', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    executable, rom = args.exe.resolve(strict=True), args.rom.resolve(strict=True)
    fixtures = args.fixtures_root.resolve(strict=True)
    battle = fixtures / 'world-cave-a/saves/save0.sav'
    town = fixtures / 'likado-east-a/saves/save0.sav'
    protected = {str(path): sha(path) for path in [rom, battle, town]}
    base = (args.out or ROOT / 'local/runs' /
            ('qol-restore-' + time.strftime('%Y%m%d-%H%M%S'))).resolve()
    base.mkdir(parents=True, exist_ok=False)
    checks, cases = {}, {}
    report = dict(candidate_sha256=sha(executable), checks=checks, cases=cases,
                  protected_inputs_before=protected,
                  scope='Copied opening battle/town and first 600 cold opening frames; dummy SDL/software/audio off',
                  limits=['No campaign, physical-controller or audible-audio certification',
                          'Checkpoint times are specific to the qualified two-Red-Slime fixture'])

    def run(name, state, script, held=False, percent=100, save_frame=None):
        directory = base / name
        directory.mkdir(); (directory / 'dump').mkdir()
        shutil.copy2(executable, directory / 'game.exe')
        if state:
            shutil.copy2(state, directory / 'resume.state')
        (directory / 'input.txt').write_text(script)
        (directory / 'config.ini').write_text(
            '[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n'
            '[KeyMap]\nMovementBoost=M\nTurbo=None\nBattleInfo=None\nJournal=None\n')
        (directory / 'foundation.ini').write_text(
            f'[Foundation]\nXpMultiplierPercent={percent}\nGoldMultiplierPercent={percent}\nMovementSpeedPercent=300\n')
        env = {key: value for key, value in os.environ.items() if not key.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
                   SNESRECOMP_FOUNDATION_QOL_TRACE='1')
        if held:
            env['SNESRECOMP_FOUNDATION_MOVEMENT_INPUT_TEST'] = 'keyboard'
        if save_frame is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save_frame),
                       SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        command = [str(directory / 'game.exe'), '--no-launcher', '--rom', str(rom)]
        if state:
            command += ['--resume-state', str(directory / 'resume.state')]
        command += ['--script', str(directory / 'input.txt')]
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run(command, cwd=directory, env=env, stdout=log, stderr=log,
                                    timeout=80,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        text = (directory / 'host.log').read_text(errors='replace').splitlines()
        cases[name] = dict(exit=result.returncode, before=guest(directory, 'before'),
                           after=guest(directory, 'after'),
                           boost_events=[line for line in text if 'foundation_qol_walk' in line and
                                         ('step=2' in line or 'step=3' in line)],
                           victory_events=[line for line in text if 'foundation_qol_victory' in line])
        checks[name + '_clean_exit'] = result.returncode == 0
        print(name, cases[name]['after'], flush=True)
        return directory

    try:
        menu_script = 'press b 1\nwait 30\ndump before\npress right 20\nwait 30\ndump after\nquit\n'
        normal = run('menu-unheld', town, menu_script)
        held = run('menu-held', town, menu_script, held=True)
        checks['held_menu_guest_exact'] = same(normal, held, ['before', 'after'])
        checks['held_menu_has_no_boost'] = not cases['menu-held']['boost_events']

        intro_script = 'wait 5\ndump before\nwait 600\ndump after\nquit\n'
        normal = run('intro-unheld', None, intro_script)
        held = run('intro-held', None, intro_script, held=True)
        checks['held_opening_guest_exact'] = same(normal, held, ['before', 'after'])
        checks['held_opening_has_no_boost'] = not cases['intro-held']['boost_events']

        battle_script = 'wait 60\ndump before\n' + ''.join(
            'press a 1\nwait 180\n' for _ in range(12)) + 'dump after\nquit\n'
        for frame, label in [(2050, 'before-victory'), (2100, 'after-victory')]:
            saved = run('save-' + label, battle, battle_script, percent=125, save_frame=frame)
            state = saved / 'saves/save0.sav'
            checks[label + '_checkpoint_saved'] = state.exists()
            state_hash = sha(state)
            # The first state is waiting for the original result confirmation;
            # the second has already passed the single reward handoff.
            script = ('wait 12\ndump before\npress a 1\nwait 190\ndump after\nquit\n'
                      if label == 'before-victory' else
                      'wait 1\ndump before\nwait 190\ndump after\nquit\n')
            name = 'cold-' + label
            run(name, state, script, percent=125)
            checks[label + '_checkpoint_copy_preserved'] = sha(state) == state_hash
            checks[label + '_actual_xp5_gold5'] = (
                cases[name]['after']['xp'] == 5 and cases[name]['after']['gold'] == 5)
            checks[label + '_single_or_no_handoff'] = len(cases[name]['victory_events']) == (
                1 if label == 'before-victory' else 0)
    except Exception as error:
        report['error'] = repr(error)
        checks['all_routes_completed'] = False
    finally:
        report['protected_inputs_after'] = {path: sha(Path(path)) for path in protected}
        checks['original_inputs_preserved'] = report['protected_inputs_after'] == protected
        report['passed'] = all(checks.values())
        (base / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(checks, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
