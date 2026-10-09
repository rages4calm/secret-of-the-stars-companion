"""Check real battle rewards and held field movement in private copied fixtures.

No ROM/checkpoints are distributed. A developer supplies the clean image and
their qualified opening battle/town/house fixture directory. This finite probe
uses dummy SDL devices and audio off; it does not certify a campaign or hardware.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guest(run, tag):
    ram = (run / 'dump' / (tag + '.wram.bin')).read_bytes()
    value = lambda at, count=1: int.from_bytes(ram[at:at + count], 'little')
    return dict(mode=value(0x20), xp=value(0x5009, 3), gold=value(0x53b3, 3),
                scene=value(0x40e, 2), primary=[value(0x2ad, 2), value(0x2af, 2)],
                secondary=[value(0x2b1, 2), value(0x2b3, 2)], motion=value(0x408))


def same(a, b, tags):
    return all((a / 'dump' / (tag + '.' + ext)).read_bytes() ==
               (b / 'dump' / (tag + '.' + ext)).read_bytes()
               for tag in tags for ext in EXTENSIONS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--fixtures-root', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, default=ROOT / 'local/upstream/snesrecomp')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    args.rom = args.rom.resolve(strict=True)
    args.fixtures_root = args.fixtures_root.resolve(strict=True)
    if args.reference:
        args.reference = args.reference.resolve(strict=True)
    states = {name: args.fixtures_root / folder / 'saves/save0.sav' for name, folder in
              [('battle', 'world-cave-a'), ('town', 'likado-east-a'),
               ('house', 'likado-inside-a')]}
    protected = {str(p): sha(p) for p in [args.rom, *states.values()]}
    base = (args.out or ROOT / 'local/runs' / ('qol-' + time.strftime('%Y%m%d-%H%M%S'))).resolve()
    base.mkdir(parents=True, exist_ok=False)
    checks, cases = {}, {}
    report = {'candidate_sha256': sha(args.exe), 'checks': checks, 'cases': cases,
              'protected_inputs_before': protected,
              'scope': 'Natural copied two-Red-Slime battle and ordinary opening field routes; dummy SDL/software/audio off',
              'limits': ['No full-campaign, physical-controller or audible-audio certification',
                         'Movement enhancement supports matched ordinary Mode80 layers, original one-pixel walking and zero currents; other movement falls back',
                         'Reward arithmetic saturates the original per-battle16-bit total; original24-bit XP/wallet caps remain',
                         'Synthetic guards are separate from genuine guest execution']}
    battle_script = 'wait 60\ndump before\n' + ''.join(
        'press a 1\nwait 180\n' for _ in range(12)) + 'dump after\nquit\n'

    def run(name, state, script, xp=100, gold=100, speed=200, held=None, executable=None):
        directory = base / name
        directory.mkdir(); (directory / 'dump').mkdir()
        shutil.copy2(executable or args.exe, directory / 'game.exe')
        if state:
            shutil.copy2(states[state], directory / 'resume.state')
        (directory / 'input.txt').write_text(script)
        (directory / 'config.ini').write_text(
            '[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nMovementBoost=L2\n'
            '[KeyMap]\nMovementBoost=M\nTurbo=None\nBattleInfo=None\nJournal=None\n')
        (directory / 'foundation.ini').write_text(
            f'[Foundation]\nXpMultiplierPercent={xp}\nGoldMultiplierPercent={gold}\nMovementSpeedPercent={speed}\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
                   SNESRECOMP_FOUNDATION_QOL_TRACE='1', SNESRECOMP_HOTKEY_TRACE='1')
        if held:
            env['SNESRECOMP_FOUNDATION_MOVEMENT_INPUT_TEST'] = held
        command = [str(directory / 'game.exe'), '--no-launcher', '--rom', str(args.rom)]
        if state:
            command += ['--resume-state', str(directory / 'resume.state')]
        command += ['--script', str(directory / 'input.txt')]
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run(command, cwd=directory, env=env, stdout=log, stderr=log,
                                    timeout=80, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        text = (directory / 'host.log').read_text(errors='replace')
        cases[name] = dict(exit=result.returncode, before=guest(directory, 'before'),
                           after=guest(directory, 'after'),
                           boost_events=[line for line in text.splitlines()
                                         if 'foundation_qol_walk' in line and re.search(r'step=[23]\b', line)],
                           victories=[line for line in text.splitlines() if 'foundation_qol_victory' in line])
        checks[name + '_normal_exit'] = result.returncode == 0
        if state:
            checks[name + '_guarded_resume'] = 'resume state loaded:' in text
        print(name, cases[name]['after'], flush=True)
        return directory

    original = run('battle100', 'battle', battle_script)
    for xp, gold in [(125, 125), (200, 200), (150, 300), (1000, 1000)]:
        name = f'battle{xp}-{gold}'
        directory = run(name, 'battle', battle_script, xp=xp, gold=gold)
        expected_xp = cases['battle100']['after']['xp'] * xp // 100
        expected_gold = cases['battle100']['after']['gold'] * gold // 100
        checks[name + '_actual_party_xp_and_gold'] = (
            cases[name]['after']['xp'] == expected_xp and
            cases[name]['after']['gold'] == expected_gold)
        checks[name + '_one_completed_reward_handoff'] = len(cases[name]['victories']) == 1
    checks['battle100_original_positive_rewards'] = (cases['battle100']['after']['xp'] == 4 and
                                                     cases['battle100']['after']['gold'] == 4)
    if args.reference:
        reference = run('battle-reference', 'battle', battle_script, executable=args.reference)
        checks['battle_default_six_dumps_exact_reference'] = same(original, reference, ['before', 'after'])

    for direction in ('right', 'left', 'down', 'up'):
        duration = 150 if direction == 'right' else 20
        script = f'wait 5\ndump before\npress {direction} {duration}\nwait 40\ndump after\nquit\n'
        normal = run('walk-' + direction + '-100', 'town', script, speed=100, held='keyboard')
        unheld = run('walk-' + direction + '-unheld', 'town', script, speed=200)
        checks[direction + '_unheld_exact_original'] = same(normal, unheld, ['before', 'after'])
        for speed in (150, 200, 300):
            name = 'walk-' + direction + '-' + str(speed)
            run(name, 'town', script, speed=speed, held='keyboard')
            checks[name + '_layers_and_tile_completion'] = (
                cases[name]['after']['primary'] == cases[name]['after']['secondary'] and
                all(v % 16 == 0 for v in cases[name]['after']['primary']) and
                cases[name]['after']['motion'] in (0, 255))
            checks[name + '_genuine_boost_events'] = bool(cases[name]['boost_events'])
            # A long held route reaches the original collision stop; speed may
            # change arrival time but cannot move through that blocked tile.
            if direction == 'right':
                checks[name + '_original_blocked_endpoint'] = (
                    cases[name]['after']['primary'] == cases['walk-' + direction + '-100']['after']['primary'])
    pad = run('walk-pad200', 'town', 'wait 5\ndump before\npress right 150\nwait 40\ndump after\nquit\n',
              speed=200, held='pad')
    checks['keyboard_pad_same_genuine_movement'] = same(pad, base / 'walk-right-200', ['before', 'after'])
    for speed in (100, 300):
        name = 'door-' + str(speed)
        run(name, 'house', 'wait 5\ndump before\npress down 120\nwait 120\ndump after\nquit\n',
            speed=speed, held='keyboard')
    checks['door_original_transition_preserved'] = (
        cases['door-100']['before']['scene'] != cases['door-100']['after']['scene'] and
        cases['door-100']['after']['scene'] == cases['door-300']['after']['scene'] and
        cases['door-300']['after']['mode'] == 1)
    checks['door_actual_boost_before_transition'] = bool(cases['door-300']['boost_events'])

    compiler = shutil.which('clang')
    guard_exe = base / ('qol-guards.exe' if os.name == 'nt' else 'qol-guards')
    with (base / 'guard-build.log').open('w') as log:
        subprocess.run([compiler or 'clang', '-std=c11', '-I', str(ROOT / 'native/foundation/src'),
                        '-I', str(args.runtime / 'runner/src'), str(ROOT / 'tools/check_foundation_qol.c'),
                        '-o', str(guard_exe)], stdout=log, stderr=log, check=True)
    guarded = subprocess.run([str(guard_exe)], capture_output=True, text=True, check=True)
    report['synthetic_guards'] = json.loads(guarded.stdout)
    checks['synthetic_arithmetic_and_pending_layer_guards'] = report['synthetic_guards']['passed']
    report['protected_inputs_after'] = {path: sha(Path(path)) for path in protected}
    checks['all_original_inputs_preserved'] = protected == report['protected_inputs_after']
    report['passed'] = all(checks.values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(checks, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
