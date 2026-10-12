"""Build the ROM-free Companion GUI from a frozen authored source snapshot.

Requires the .NET 8 SDK on Windows. The output is a local source compilation,
not a gameplay qualification or a native game distribution.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys, time, uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, help='New immutable output folder; default is local/public-companion/builds/<timestamp>')
    parser.add_argument('--no-select', action='store_true', help='Build a separate candidate without replacing the public launcher selection receipt')
    parser.add_argument('--source-dir',type=Path,help='Optional new frozen-source/build folder; default: local/companion-build-sources/timestamp.')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise RuntimeError('Companion is a Windows WinForms application; build it on Windows with the .NET 8 SDK.')
    if not shutil.which('dotnet'):
        raise RuntimeError('Install the .NET 8 SDK and make dotnet available on PATH. See BUILDING.md.')
    stamp = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    output = (args.output_dir or ROOT/'local/public-companion/builds'/stamp).resolve()
    if output.exists():
        raise RuntimeError('Output folder already exists; it has been preserved. Choose a new output folder.')
    source = ROOT/'Companion'
    manifest = json.loads((source/'authored-files.json').read_text(encoding='utf-8'))
    frozen = args.source_dir.absolute() if args.source_dir else ROOT/'local/companion-build-sources'/stamp
    frozen.mkdir(parents=True, exist_ok=False)
    actual = {}
    for name in manifest:
        path = (source/name).resolve(strict=True)
        if not path.is_relative_to(source.resolve()):
            raise RuntimeError('Authored source path leaves Companion: ' + name)
        destination = frozen/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        actual[name] = sha(destination)
    if actual != manifest:
        raise RuntimeError('Companion source differs from authored-files.json. Preserve edits and refresh the deliberate source manifest before building.')
    version = ET.parse(frozen/'Companion.csproj').getroot().findtext('./PropertyGroup/Version')
    output.mkdir(parents=True, exist_ok=False)
    command = ['dotnet', 'publish', str(frozen/'Companion.csproj'), '-c', 'Release', '-r', 'win-x64', '--self-contained', 'true',
               '-p:PublishSingleFile=true', '-o', str(output)]
    print('Publishing frozen Companion ' + str(version) + '...', flush=True)
    with (output/'build.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Companion publish failed. Inspect ' + str(output/'build.log'))
    binary = output/'Secret of the Stars Companion.exe'
    if not binary.is_file():
        raise RuntimeError('Published Companion executable is missing; output has been preserved.')
    notices = {}
    for src, name in [(source/'LICENSE', 'LICENSE.txt'), (source/'THIRD-PARTY-NOTICES.md', 'THIRD-PARTY-NOTICES.md'),
                      (ROOT/'licenses/DOTNET-LICENSE.txt', 'licenses/DOTNET-LICENSE.txt'),
                      (ROOT/'licenses/WINDOWS-DESKTOP-LICENSE.txt', 'licenses/WINDOWS-DESKTOP-LICENSE.txt'),
                      (ROOT/'licenses/DOTNET-THIRD-PARTY-NOTICES.txt', 'licenses/DOTNET-THIRD-PARTY-NOTICES.txt')]:
        destination = output/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, destination)
        notices[name] = sha(destination)
    receipt = {'status': 'compiled_unqualified', 'public_build': True, 'component': 'Companion', 'version': version,
               'executable': str(binary), 'executable_sha256': sha(binary), 'authored_inputs': actual,
               'source_snapshot': str(frozen), 'source_manifest_sha256': sha(source/'authored-files.json'),
               'notices': notices, 'rom_included': False, 'gameplay_qualification': False,
               'limits': 'ROM-free GUI source compilation only. Native game setup and gameplay qualification are separate.'}
    text = json.dumps(receipt, indent=2) + '\n'
    (output/'source-companion-receipt.json').write_text(text, encoding='utf-8')
    if not args.no_select:
        public = ROOT/'local/public-companion'
        public.mkdir(parents=True, exist_ok=True)
        selected = public/'source-companion-receipt.json'
        temporary = public/('selection-' + uuid.uuid4().hex + '.tmp')
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(selected)
    print('Built: ' + str(binary))
    print('Receipt: ' + str(output/'source-companion-receipt.json'))
    print('Run: "' + str(binary) + '" --root "' + str(ROOT) + '" --setup')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
