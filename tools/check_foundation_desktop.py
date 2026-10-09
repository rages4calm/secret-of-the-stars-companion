"""Verify first launch, Windows fullscreen/audio and refused-resume handling."""
from pathlib import Path
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def launcher(profile, *options):
    return subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                           '-File', str(ROOT / 'tools/Start-Foundation.ps1'),
                           '-ProfileDirectory', str(profile), *options],
                          cwd=ROOT, capture_output=True, text=True, timeout=30,
                          creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    base = ROOT / 'local/runs' / ('desktop-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    profile = base / 'first-start'
    result = launcher(profile, '-VerifyFrames', '180')
    (base / 'launcher.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        print(result.stdout + result.stderr)
        return 1
    report = {'first_launch_exit': result.returncode,
              'first_start_marked': (profile / 'first-start.done').exists(),
              'normal_launch_does_not_resume': not any('resume state loaded:' in p.read_text(errors='replace') for p in (profile / 'logs').glob('*stderr.log'))}
    report['enhanced_defaults_enabled'] = any(
        'battle_info=1 enhanced_pixels=1 experimental_field_wide=0' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    report['fast_menus_default_enabled'] = any('fast_menus=1' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    report['journal_default_enabled'] = any('journal enabled=1' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    # Test Original View against explicitly enabled new options in this private
    # profile, rather than passing vacuously because their defaults are zero.
    ini = profile / 'foundation.ini'
    settings_text = ini.read_text()
    import re
    for key in ('HdMenuFrames', 'NativeColumns', 'NativeClear'):
        settings_text = re.sub(r'(?m)^\s*'+key+r'\s*=.*$', key+'=1', settings_text)
    ini.write_text(settings_text)
    settings = ini.read_bytes()
    original = launcher(profile, '-OriginalView', '-VerifyFrames', '120')
    (base / 'original-view.log').write_text(original.stdout + original.stderr)
    report['original_view_exit'] = original.returncode
    report['original_view_disables_enhancements'] = any(
        'battle_info=0 enhanced_pixels=0 experimental_field_wide=0' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    report['original_view_preserves_preferences'] = (profile / 'foundation.ini').read_bytes() == settings
    report['original_view_disables_fast_menus'] = any('fast_menus=0' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    report['original_view_disables_journal'] = any('journal enabled=0' in p.read_text(errors='replace')
        for p in (profile / 'logs').glob('*stderr.log'))
    original_logs = [p.read_text(errors='replace') for p in (profile / 'logs').glob('*stderr.log')]
    report['original_view_disables_new_options'] = any(
        'hd_menu_frames=0 ' in log and 'native_column_lookup=0 fast_fetch=0' in log and
        'native_clear_original_cost=0' in log and 'battle_info=0 enhanced_pixels=0' in log
        for log in original_logs)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('SNESRECOMP_'):
            env.pop(key)
    env.update(SNESRECOMP_RUN_FRAMES='180', SNESRECOMP_FULLSCREEN_SELFTEST='1', SNESRECOMP_HOST_PROFILE='1')
    with (base / 'fullscreen.log').open('w') as log:
        fullscreen = subprocess.run([str(profile / 'SecretOfTheStarsSNESRecomp.exe'),
                                     '--no-launcher', '--rom', str(ROOT / 'local/inputs/clean-usa.sfc')],
                                    cwd=profile, env=env, stdout=log, stderr=log, timeout=20,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
    log = (base / 'fullscreen.log').read_text(errors='replace')
    report.update(fullscreen_exit=fullscreen.returncode,
                  fullscreen_transitions_passed=all(f'frame {frame} fullscreen={flag}' in log
                    for frame, flag in [(30, 1), (90, 0), (120, 1), (150, 0)]),
                  windows_video='video=windows' in log,
                  gpu_vsync_enabled='Renderer: direct3d11 (vsync=1 ' in log,
                  audio_opened='audio device opened:' in log,
                  controller_assigned_player_one='assigning to player 1' in log)
    bad = base / 'refused-resume'
    prepared = launcher(bad, '-PrepareOnly')
    (bad / 'fixture-resume.state').write_bytes(b'invalid fixture checkpoint')
    rejected = launcher(bad, '-ResumeFixture', '-VerifyFrames', '120')
    (base / 'refused-resume.log').write_text(rejected.stdout + rejected.stderr)
    report.update(refused_resume_reported=prepared.returncode == 0 and rejected.returncode != 0,
                  refused_resume_preserved=(bad / 'fixture-resume.state').read_bytes() == b'invalid fixture checkpoint',
                  refused_resume_unmarked=not (bad / 'first-start.done').exists())
    report['passed'] = report['first_launch_exit'] == report['fullscreen_exit'] == report['original_view_exit'] == 0 and all(
        value for key, value in report.items() if key not in ('first_launch_exit', 'fullscreen_exit', 'original_view_exit', 'controller_assigned_player_one'))
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
