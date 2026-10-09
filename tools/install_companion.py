"""Install only the exact qualified Companion bytes; protect the game profile."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected():
    profile = ROOT / 'local/player-foundation'
    files = [p for p in profile.iterdir() if p.is_file()]
    files += [p for p in (profile / 'saves').rglob('*') if p.is_file()]
    return {p.relative_to(profile).as_posix(): sha(p) for p in files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--qualification', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.qualification.read_text())
    candidate = args.candidate.resolve()
    name = 'Secret of the Stars Companion.exe'
    assert report['passed'] and report['companion_sha256'] == sha(candidate / name)
    manifest = json.loads((ROOT / 'Companion/authored-files.json').read_text())
    assert all(sha(ROOT / 'Companion' / path) == digest for path, digest in manifest.items())
    before = protected()
    assert report['native_executable_sha256'] == before['SecretOfTheStarsSNESRecomp.exe'], 'Companion routes must qualify the currently installed game artifact'
    profile = ROOT / 'local/player-foundation'
    backup = ROOT / 'local/owner-backups' / ('companion-release-' + time.strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(exist_ok=False)
    for relative, digest in before.items():
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(profile / relative, target)
        assert sha(target) == digest
    (backup / 'receipt.json').write_text(json.dumps({'passed': True, 'files': before}, indent=2) + '\n')
    installed = ROOT / 'local/companion'
    if installed.exists():
        previous = ROOT / 'local/owner-backups' / ('companion-previous-' + time.strftime('%Y%m%d-%H%M%S'))
        shutil.copytree(installed, previous)
        assert all(sha(p) == sha(previous / p.relative_to(installed)) for p in installed.rglob('*') if p.is_file())
    installed.mkdir(exist_ok=True)
    root_executable = ROOT / name
    if root_executable.exists():
        shutil.copy2(root_executable, backup / ('previous-root-' + name))
    shutil.copy2(candidate / name, installed / name)
    shutil.copy2(candidate / name, root_executable)
    assets = json.loads((ROOT / 'Companion/obj/project.assets.json').read_text())
    packages = Path(next(iter(assets['packageFolders'])))
    notices = {
        'DOTNET-LICENSE.txt': packages / 'microsoft.netcore.app.runtime.win-x64/8.0.27/LICENSE.TXT',
        'DOTNET-THIRD-PARTY-NOTICES.txt': packages / 'microsoft.netcore.app.runtime.win-x64/8.0.27/THIRD-PARTY-NOTICES.TXT',
        'WINDOWS-DESKTOP-LICENSE.txt': packages / 'microsoft.windowsdesktop.app.runtime.win-x64/8.0.27/LICENSE',
        'COMPANION-NOTICES.md': ROOT / 'Companion/THIRD-PARTY-NOTICES.md',
    }
    for destination, source in notices.items():
        shutil.copy2(source, installed / destination)
        assert sha(installed / destination) == sha(source)
    assert sha(installed / name) == report['companion_sha256']
    assert sha(root_executable) == report['companion_sha256']
    assert protected() == before
    receipt = {
        'version': ET.parse(ROOT / 'Companion/Companion.csproj').findtext('.//Version'), 'qualified': True, 'installed': True,
        'executable': (installed / name).relative_to(ROOT).as_posix(), 'executable_sha256': sha(installed / name),
        'game_version': json.loads((ROOT / 'local/evidence/build-receipt.json').read_text())['release_version'],
        'game_executable_sha256': before['SecretOfTheStarsSNESRecomp.exe'],
        'root_executable': name, 'root_executable_sha256': sha(root_executable),
        'qualification_report': args.qualification.resolve().relative_to(ROOT).as_posix(),
        'backend_checks': report['backend_checks'], 'ui_interaction_checks': report['ui_interaction_checks'],
        'owner_backup': backup.relative_to(ROOT).as_posix(), 'owner_files_preserved': before,
        'authored_manifest': 'Companion/authored-files.json', 'runtime': '.NET / Windows Desktop 8.0.27 self-contained win-x64',
        'installed_files': {p.name: sha(p) for p in installed.iterdir() if p.is_file()},
        'scope': 'Visible settings GUI/direct root EXE, explicit title/selected-copy resume, Original View, and separately qualified Likado wider-view/menu previews.'
    }
    (ROOT / 'local/evidence/companion-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
