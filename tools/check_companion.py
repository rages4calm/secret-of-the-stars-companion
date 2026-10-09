"""Qualify the actual Windows Companion artifact using protected copied profiles."""
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owner_hashes():
    owner = ROOT / 'local/player-foundation'
    paths = list(owner.glob('*')) + list((owner / 'saves').rglob('*'))
    return {p.relative_to(owner).as_posix(): digest(p) for p in paths if p.is_file()}


def main():
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=ROOT, help='Optional complete staged project root for qualification before installation')
    args = parser.parse_args()
    ROOT = args.root.resolve(strict=True)
    exe = args.exe.resolve()
    base = ROOT / 'local/runs' / ('companion-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    before = owner_hashes()
    checks = {}

    def run(name, options, expected=0):
        with (base / (name + '.stdout.log')).open('w') as stdout, (base / (name + '.stderr.log')).open('w') as stderr:
            result = subprocess.run([str(exe), '--root', str(ROOT), *options], cwd=ROOT, stdout=stdout, stderr=stderr,
                                    timeout=65, creationflags=subprocess.CREATE_NO_WINDOW)
        checks[name + '_exit'] = result.returncode == expected
        assert checks[name + '_exit'], (name, result.returncode)

    run('backend', ['--self-test', str(base / 'backend'), '--report', str(base / 'backend-error.json')])
    backend = json.loads((base / 'backend/report.json').read_text())
    checks['backend_passed'] = backend['passed']
    run('capture', ['--capture', str(base / 'captures'), '--report', str(base / 'capture-error.json')])
    checks['six_pages_captured'] = all((base / 'captures' / (p + '.png')).stat().st_size > 10000
                                     for p in ('play', 'display', 'audio', 'controls', 'enhancements', 'saves'))

    def profile(name):
        directory = base / name
        directory.mkdir()
        owner = ROOT / 'local/player-foundation'
        for file in owner.iterdir():
            if file.is_file(): shutil.copy2(file, directory / file.name)
        shutil.copytree(owner / 'saves', directory / 'saves')
        config = directory / 'config.ini'
        data = re.sub(rb'(?m)^(\s*Fullscreen\s*=\s*)1\s*$', rb'\g<1>0', config.read_bytes())
        data = re.sub(rb'(?m)^(\s*Volume\s*=\s*)70\s*$', rb'\g<1>61', data)
        config.write_bytes(data)
        return directory

    interaction = profile('UI interaction profile')
    run('ui-interaction', ['--ui-test', str(base / 'ui-interaction.json'), '--profile', str(interaction)])
    ui = json.loads((base / 'ui-interaction.json').read_text())
    checks['ui_interaction_passed'] = ui['passed']

    for mode in ('Play', 'OriginalView', 'Resume', 'LegacyResume', 'WidescreenPreview', 'HdMenuPreview'):
        directory = profile(mode + ' profile with spaces')
        protected = {p.relative_to(directory).as_posix(): digest(p) for p in (directory / 'saves').rglob('*') if p.is_file()}
        foundation_hash = digest(directory / 'foundation.ini')
        options = ['--launch-test', 'Resume' if mode == 'LegacyResume' else mode, '--profile', str(directory), '--verify-frames', '180', '--report', str(base / (mode + '-launch.json'))]
        if mode in ('Resume', 'LegacyResume'):
            slot = directory / 'saves/save4.sav'
            source = ROOT / 'local/runs/likado-east-a/saves/save0.sav' if mode == 'Resume' else directory / 'saves/save0.sav'
            shutil.copy2(source, slot)
            protected['saves/save4.sav'] = digest(slot)
            options += ['--save', str(slot)]
        run(mode, options)
        report = json.loads((base / (mode + '-launch.json')).read_text())
        logs = report['stdout'].split('Launch diagnostics: ')[-1].strip()
        stderr_files = sorted(Path(logs).glob('*stderr.log'))
        assert stderr_files, report
        text = stderr_files[-1].read_text(errors='replace')
        checks[mode + '_main_loop'] = 'entering main loop' in text
        checks[mode + '_saves_preserved'] = all(digest(directory / p) == sha for p, sha in protected.items())
        checks[mode + '_preferences_preserved'] = digest(directory / 'foundation.ini') == foundation_hash
        if mode in ('Play', 'OriginalView'):
            checks[mode + '_title_first'] = 'resume state loaded:' not in text
        else:
            checks[mode + '_restored'] = 'resume state loaded:' in text
        if mode in ('Resume', 'LegacyResume'):
            checks[mode + '_selected_nondefault_checkpoint_consumed'] = not (directory / 'fixture-resume.state').exists()
            if mode == 'Resume':
                checks['resume_selected_town_fixture'] = protected['saves/save4.sav'] == 'aabd365c8b4a64dd17cfec34476c8864c9a538a73e44b97c19aeab4bd9c0fa51'
        if mode == 'OriginalView':
            checks['original_overrides'] = 'battle_info=0 enhanced_pixels=0 experimental_field_wide=0' in text
            checks['original_actor_observer_disabled'] = 'experimental_field_actors=0 observer=0' in text
        if mode in ('WidescreenPreview', 'HdMenuPreview'):
            checks[mode + '_isolated'] = Path(logs).parent != directory and 'preview-' in str(Path(logs).parent)
            preview_settings = (Path(logs).parent / 'config.ini').read_bytes()
            checks[mode + '_uses_selected_source_profile'] = bool(re.search(rb'(?m)^\s*Fullscreen\s*=\s*0\s*$', preview_settings)) and bool(re.search(rb'(?m)^\s*Volume\s*=\s*61\s*$', preview_settings))
            if mode == 'WidescreenPreview':
                preview_foundation = (Path(logs).parent / 'foundation.ini').read_bytes()
                checks['wide_preview_paired_flags'] = all(re.search(rb'(?m)^\s*' + key + rb'\s*=\s*1\s*$', preview_foundation)
                                                          for key in (b'ExperimentalFieldWide', b'ExperimentalFieldActors'))
                actor_stats = re.search(r'\[foundation_wide_actors\] captured=(\d+) packets=(\d+) side_pieces=(\d+) side_pixels=(\d+)', text)
                checks['wide_preview_actual_actor_margins'] = bool(actor_stats) and all(int(value) > 0 for value in actor_stats.groups())

    guard = profile('Raw helper checkpoint guards')
    pending = guard / 'fixture-resume.state'
    pending.write_bytes(b'preserve conflicting checkpoint')
    pending_hash = digest(pending)
    for name, selected in [('foreign', ROOT / 'local/player-foundation/saves/save0.sav'), ('conflict', guard / 'saves/save0.sav')]:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'tools/Start-Foundation.ps1'),
                                 '-ProfileDirectory', str(guard), '-ResumeCheckpoint', str(selected), '-VerifyFrames', '90'],
                                cwd=ROOT, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        (base / (name + '-guard.log')).write_text(result.stdout + result.stderr)
        checks[name + '_raw_helper_rejected'] = result.returncode != 0 and 'Game started.' not in result.stdout
        checks[name + '_raw_helper_pending_preserved'] = digest(pending) == pending_hash

    checks['owner_profile_preserved'] = owner_hashes() == before
    report = {'passed': all(checks.values()), 'companion_sha256': digest(exe),
              'project_root': str(ROOT),
              'native_executable_sha256': digest(ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'),
              'backend_checks': backend['checks'], 'ui_interaction_checks': ui['checks'],
              'checks': checks, 'owner_files_before': before, 'owner_files_after': owner_hashes(),
              'coverage': 'Real Windows Companion load/capture/backend plus paced GPU game launch through all six routes, including selected v1/v3 resumes and positive Likado actor margins. No new physical-controller or full-campaign certification.'}
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
