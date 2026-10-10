"""Package a relocatable, ROM-free Companion EXE and its authored build source.

Native game binaries, generated game bodies and player profiles are excluded.
This package is a source-first launcher; native compilation still needs tools.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, subprocess, zipfile
from check_public_source import DOCUMENTATION_CAPTURES

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {'.sfc', '.smc', '.srm', '.sav', '.state', '.dll', '.pcm', '.wav', '.ogg', '.png', '.jpg', '.pdb', '.obj', '.bin'}

def digest(data): return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--companion-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New ZIP; existing archives are preserved')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists(): raise ValueError('Output already exists; choose a new archive.')
    receipt = json.loads(args.companion_receipt.read_text(encoding='utf-8'))
    if receipt.get('status') != 'compiled_unqualified' or receipt.get('component') != 'Companion':
        raise ValueError('Supply a real Companion source compilation receipt.')
    binary = Path(receipt['executable']).resolve(strict=True)
    data = binary.read_bytes()
    if digest(data) != receipt['executable_sha256']: raise ValueError('Companion executable differs from its receipt.')
    manifest = json.loads((ROOT/'Companion/authored-files.json').read_text())
    if manifest != receipt['authored_inputs']: raise ValueError('Companion candidate differs from the current source snapshot.')
    # Publication checker examines exactly the Git-tracked authored boundary.
    check = json.loads(subprocess.check_output(['python', str(ROOT/'tools/check_public_source.py')], cwd=ROOT, text=True))
    if not check['passed']: raise ValueError('Public source checks failed.')
    names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().rstrip('\0').split('\0')
    entries = {}
    for name in names:
        parts = PurePosixPath(name)
        if (parts.is_absolute() or '..' in parts.parts
                or (parts.suffix.lower() in FORBIDDEN and name not in DOCUMENTATION_CAPTURES)
                or parts.suffix.lower()=='.exe'):
            raise ValueError('Forbidden package source: '+name)
        path = ROOT/name
        if path.is_symlink(): raise ValueError('Linked package source: '+name)
        entries[name] = path.read_bytes()
    executable = 'Secret of the Stars Companion.exe'
    entries[executable] = data
    metadata = {'schema':1,'component':'Companion','status':'compiled_unqualified',
        'version':receipt['version'],'executable':executable,'executable_sha256':digest(data),
        'source_manifest_sha256':digest(entries['Companion/authored-files.json']),
        'files':{name:digest(value) for name,value in sorted(entries.items())},
        'game_data_included':False,'native_game_included':False,
        'limits':'ROM-free self-contained GUI, authored source and five reviewed documentation captures. Native source build needs an owned ROM and development tools; no gameplay qualification is implied.'}
    entries['portable-companion.json'] = (json.dumps(metadata,indent=2)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,value in sorted(entries.items()): archive.writestr(name,value)
    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist())==sorted(entries)
        assert all(archive.read(name)==value for name,value in entries.items())
    result={'passed':True,'archive_sha256':digest(output.read_bytes()),'archive':str(output),
        'files':len(entries),'companion_sha256':digest(data),'version':receipt['version'],
        'publication_check':check,'boundary':'Authored source, five reviewed documentation captures and one ROM-free GUI EXE; no native game, ROM, extracted asset packs, generated code or profiles'}
    output.with_suffix('.receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
