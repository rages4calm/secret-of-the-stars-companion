"""Finite actual SDL keyboard/virtual-pad hotkey checks in private profiles."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def overlay_check(exe: Path, rom: Path, output: Path, state: Path, action: str, method: str) -> dict:
    """Use copied actual field/battle states; compare host surfaces and guest bytes."""
    runs = []
    for enabled in (0, 1):
        profile = output / f'{action}-{method}-{enabled}'
        profile.mkdir(); (profile / 'dump').mkdir(); (profile / 'capture').mkdir()
        local_exe = profile / exe.name
        shutil.copy2(exe, local_exe); shutil.copy2(state, profile / 'resume.state')
        for dll in exe.parent.glob('*.dll'): shutil.copy2(dll, profile / dll.name)
        (profile / 'config.ini').write_text(
            '[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[Controller]\nSourceP1=2\nSourceP2=0\n'
            '[KeyMap]\nBattleInfo=U\nJournal=I\nTurbo=None\nMovementBoost=None\n'
            '[GamepadMap]\nBattleInfo=R3\nJournal=L3\nTurbo=None\nMovementBoost=None\n', encoding='utf-8')
        (profile / 'foundation.ini').write_text(
            f'BattleInfo={enabled if action == "hud" else 0}\n'
            f'Journal={enabled if action == "journal" else 0}\nEnhancedPixels=0\n', encoding='utf-8')
        (profile / 'input.txt').write_text('wait 60\ndump open\nwait 90\ndump closed\nquit\n', encoding='utf-8')
        env = {key: value for key, value in os.environ.items() if not key.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',
                   SNESRECOMP_HOTKEY_TRACE='1', SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST=method,
                   SNESRECOMP_FOUNDATION_HOTKEY_OVERLAY_TEST=action, SNESRECOMP_DUMP_DIR=str(profile / 'dump'),
                   SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE='60,150',
                   SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(profile / 'capture'))
        result = subprocess.run([str(local_exe), '--no-launcher', '--rom', str(rom),
                                 '--resume-state', str(profile / 'resume.state'), '--script', str(profile / 'input.txt')],
                                cwd=profile, env=env, capture_output=True, timeout=30)
        log = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        (profile / 'runtime.log').write_text(log, encoding='utf-8')
        runs.append((profile, log, result.returncode))
    off, on = runs
    text = 'battle info' if action == 'hud' else 'journal'
    toggles = on[1].count(text + ' shown') == on[1].count(text + ' hidden') == 1
    checks = {'once_per_press_and_old_keys_unbound': toggles,
              'open_changes_surface': (off[0] / 'capture/frame-60-256x224.bgrx').read_bytes() != (on[0] / 'capture/frame-60-256x224.bgrx').read_bytes(),
              'close_matches_original': (off[0] / 'capture/frame-150-256x224.bgrx').read_bytes() == (on[0] / 'capture/frame-150-256x224.bgrx').read_bytes(),
              'guest_unchanged': all((off[0] / 'dump' / f'{tag}.{ext}').read_bytes() ==
                                     (on[0] / 'dump' / f'{tag}.{ext}').read_bytes()
                                     for tag in ('open', 'closed') for ext in
                                     ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx'))}
    if action == 'hud':
        # HUD starts shown; its first press hides and the second shows it.
        checks.pop('open_changes_surface'); checks.pop('close_matches_original')
        checks['hidden_matches_original'] = (off[0] / 'capture/frame-60-256x224.bgrx').read_bytes() == (on[0] / 'capture/frame-60-256x224.bgrx').read_bytes()
        checks['shown_changes_surface'] = (off[0] / 'capture/frame-150-256x224.bgrx').read_bytes() != (on[0] / 'capture/frame-150-256x224.bgrx').read_bytes()
    if method == 'pad': checks['actual_sdl_virtual_device'] = 'virtual pad attached' in on[1]
    return dict(name=f'{action}-{method}-actual-overlay', checks=checks,
                passed=all(checks.values()) and all(run[2] == 0 for run in runs),
                copied_checkpoint_sha256=hashlib.sha256(state.read_bytes()).hexdigest())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--battle-state', type=Path, help='Optional copied battle checkpoint for actual HUD open/close parity')
    parser.add_argument('--field-state', type=Path, help='Optional copied field checkpoint for actual journal open/close parity')
    args = parser.parse_args()
    exe, rom, output = args.exe.resolve(), args.rom.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    original_rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()
    checks = []
    for mode in ('keyboard', 'pad', 'combined', 'modifier', 'unbound', 'gestures-off', 'reset', 'restore', 'disconnect',
                 'overlay-pad', 'overlay-escape', 'overlay-toggle', 'overlay-cancel'):
        safety = mode if mode in ('reset', 'restore', 'disconnect') else 'overlay' if mode.startswith('overlay-') else None
        input_mode = mode if mode in ('keyboard', 'pad', 'combined') else 'pad' if mode in ('disconnect', 'gestures-off') else 'combined' if mode == 'unbound' else 'keyboard'
        for toggle in (1,) if safety else (0, 1):
            label = f'{mode}-{"toggle" if toggle else "hold"}'
            profile = output / label
            profile.mkdir()
            local_exe = profile / exe.name
            shutil.copy2(exe, local_exe)
            for dll in exe.parent.glob('*.dll'):
                shutil.copy2(dll, profile / dll.name)
            config = ('[Graphics]\nOutputMethod=SDLSoftware\nVSync=0\n'
                      '[General]\nDisableFrameDelay=1\nAutosave=0\n'
                      '[Sound]\nEnableAudio=0\n'
                      '[Controller]\nSourceP1=2\nSourceP2=0\n'
                      '[KeyMap]\nTurbo=T\nMovementBoost=M\nBattleInfo=U\nJournal=I\n'
                      'Rewind=F8\nSaveStateMenu=F7\nReset=Ctrl+R\n'
                      'Load=,,,,,,,,,,,,,,,,,,,\nSave=,,,,,,,,,,,,,,,,,,,\n'
                      '[GamepadMap]\nTurbo=R2\nMovementBoost=L2\nBattleInfo=R3\nJournal=L3\n')
            if mode == 'modifier':
                config = config.replace('Turbo=T\nMovementBoost=M', 'Turbo=Ctrl+T\nMovementBoost=Left Shift')
            if mode == 'unbound':
                config = config.replace('[KeyMap]\n', '[KeyMap]\nMap=None\n')
                config = config.replace('[GamepadMap]\n', '[GamepadMap]\nMap=None\n')
                for value in ('T', 'M', 'U', 'I', 'R2', 'L2', 'R3', 'L3'):
                    config = re.sub(r'(?m)(Turbo|MovementBoost|BattleInfo|Journal)=' + value + r'$', r'\1=None', config)
            if mode == 'restore': config = config.replace('Load=,', 'Load=F2,')
            if mode == 'gestures-off':
                for value in ('T', 'M', 'U', 'I', 'R2', 'L2', 'L3'):
                    config = re.sub(r'(?m)(Turbo|MovementBoost|BattleInfo|Journal)=' + value + r'$', r'\1=None', config)
                config = config.replace('BattleInfo=R3', 'BattleInfo=Back+R3')
            (profile / 'config.ini').write_text(config, encoding='utf-8')
            (profile / 'foundation.ini').write_text(
                f'FastForwardToggle={toggle}\nLegacyControllerGestures={0 if mode == "gestures-off" else 1}\n'
                'BattleInfo=1\nJournal=1\nEnhancedPixels=0\n',
                encoding='utf-8')
            env = {key: value for key, value in os.environ.items() if not key.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                       SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',
                       SNESRECOMP_RUN_FRAMES='180', SNESRECOMP_HOTKEY_TRACE='1',
                       SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST=input_mode)
            if mode == 'modifier': env['SNESRECOMP_FOUNDATION_HOTKEY_MODIFIER_TEST'] = '1'
            if mode == 'gestures-off': env['SNESRECOMP_FOUNDATION_HOTKEY_GESTURE_TEST'] = '1'
            if safety: env['SNESRECOMP_FOUNDATION_HOTKEY_SAFETY_TEST'] = safety
            if mode == 'restore':
                env.update(SNESRECOMP_OVERLAY_SELFTEST='80', SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
            if safety == 'overlay':
                env.update(SNESRECOMP_OVERLAY_SELFTEST_PAD='50', SNESRECOMP_OVERLAY_SELFTEST_EXIT=mode[8:])
            result = subprocess.run([str(local_exe), '--no-launcher', '--rom', str(rom)],
                                    cwd=profile, env=env, capture_output=True, timeout=30)
            log = (result.stdout + result.stderr).decode('utf-8', errors='replace')
            (profile / 'runtime.log').write_text(log, encoding='utf-8')
            turbo = [(int(a), int(b)) for a, b in
                     re.findall(r'Turbo pressed=(\d) active=(\d) toggle=\d', log)]
            expected = ([(1, 1), (0, 1), (1, 0), (0, 0)] if toggle else
                        [(1, 1), (0, 0), (1, 1), (0, 0)])
            if mode == 'combined':
                expected = ([(1, 1), (1, 1), (0, 1), (0, 1),
                             (1, 0), (1, 0), (0, 0), (0, 0)] if toggle else
                            [(1, 1), (1, 1), (0, 1), (0, 0),
                             (1, 1), (1, 1), (0, 1), (0, 0)])
            expected += ([(1, 1), (0, 1)] if toggle else [(1, 1), (0, 0)])
            if mode == 'combined':
                expected = expected[:-2] + ([(1, 1), (1, 1), (0, 1), (0, 1)] if toggle else
                                           [(1, 1), (1, 1), (0, 1), (0, 0)])
            if mode in ('unbound', 'gestures-off'): expected = []
            if safety in ('reset', 'restore', 'disconnect'): expected += [(1, 1), (0, 1)]
            if safety == 'overlay': expected = [(1, 1), (0, 1), (1, 1), (0, 1)]
            commands = [(int(a), int(b)) for a, b in
                        re.findall(r'foundation_hotkey\] command=(\d+) pressed=(\d)', log)]
            movement_presses = sum(down == 1 for _, down in commands)
            good = result.returncode == 0 and turbo == expected and movement_presses == (0 if mode == 'unbound' else 1 if mode == 'gestures-off' else 3)
            if input_mode in ('pad', 'combined'): good &= 'virtual pad attached' in log
            good &= '[host_hotkey] reset active=0' in log
            if toggle and mode not in ('unbound', 'gestures-off'): good &= 'reset active=0 previous=1' in log
            if safety in ('reset', 'restore', 'disconnect'):
                good &= log.count('reset active=0 previous=1') >= 2
            if mode == 'reset': good &= 'console reset' in log
            if mode == 'disconnect': good &= 'pad disconnected' in log
            if mode == 'restore':
                good &= (profile / 'saves/save0.sav').exists()
                good &= 'Load' in log or 'load' in log
            if safety == 'overlay':
                good &= 'ok: browser and rewind both opened and closed from the pad' in log
                good &= log.count('reset active=0 previous=1') >= 2
            checks.append(dict(name=label, passed=bool(good), exit_code=result.returncode,
                               turbo=turbo, expected=expected, native_commands=commands))
            print(f'{label}: {"PASS" if good else "FAIL"}')
    for action, state in (('hud', args.battle_state), ('journal', args.field_state)):
        if state:
            state = state.resolve()
            before_hash = hashlib.sha256(state.read_bytes()).hexdigest()
            for method in ('keyboard', 'pad'):
                check = overlay_check(exe, rom, output, state, action, method)
                check['source_checkpoint_unchanged'] = hashlib.sha256(state.read_bytes()).hexdigest() == before_hash
                check['passed'] &= check['source_checkpoint_unchanged']
                checks.append(check)
                print(f'{check["name"]}: {"PASS" if check["passed"] else "FAIL"}')
    report = dict(checks=checks, passed=all(c['passed'] for c in checks),
                  executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                  rom_unchanged=hashlib.sha256(rom.read_bytes()).hexdigest() == original_rom_hash,
                  scope='Actual SDL hotkeys, finite cold boot; no physical-pad, campaign or audible qualification.')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if not report['passed'] or not report['rom_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
