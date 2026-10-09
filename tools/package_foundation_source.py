"""Create an additive authored-source bundle, excluding private game data."""
from pathlib import Path
import hashlib
import json
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'native/foundation'
    manifest = json.loads((source/'authored-files.json').read_text())
    files = [source/name for name in manifest]
    files += [source/'README.md', source/'authored-files.json', ROOT/'AGENTS.md',
              ROOT/'HANDOFF-2026-10-08-Secret-of-the-Stars.md', ROOT/'.gitignore', ROOT/'patches/runtime-foundation.patch']
    files += sorted((ROOT/'tools').glob('*.py')) + sorted((ROOT/'tools').glob('*.ps1'))
    files += sorted((ROOT/'tools').glob('*.c')) + sorted((ROOT/'tools').glob('*.h'))
    files += sorted((ROOT/'docs').glob('FOUNDATION-*.md'))
    files += sorted((ROOT/'docs/porting-references').glob('*.md'))
    files += sorted(ROOT.glob('Start*.cmd')) + sorted(ROOT.glob('Resume*.cmd'))
    companion = ROOT/'Companion'
    companion_manifest = json.loads((companion/'authored-files.json').read_text())
    files += [companion/name for name in companion_manifest]
    files += [companion/'authored-files.json']
    files = sorted(set(files))
    allowed = {'.c','.h','.cs','.csproj','.md','.py','.ps1','.cmd','.patch','.json','.toml','.cfg','.txt','.sh'}
    entries={}
    for p in files:
        rel=p.relative_to(ROOT).as_posix()
        assert not rel.startswith('local/') and '/src/gen/' not in rel, rel
        assert p.suffix.lower() in allowed or p.name in {'CMakeLists.txt','VERSION','.gitmodules','.gitignore'}, rel
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if p.is_relative_to(companion) and p.relative_to(companion).as_posix() in companion_manifest:
            assert digest==companion_manifest[p.relative_to(companion).as_posix()], rel
        if p.is_relative_to(source) and p.relative_to(source).as_posix() in manifest:
            assert digest==manifest[p.relative_to(source).as_posix()], rel
        entries[rel]=digest
    out=ROOT/'local/packages'
    out.mkdir(exist_ok=True)
    archive=out/('secret-of-the-stars-authored-'+time.strftime('%Y%m%d-%H%M%S')+'.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('BUNDLE-MANIFEST.json',json.dumps(entries,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in entries.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    report={'archive':archive.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'authored_files':len(entries),'private_payloads_excluded':True,
            'contents':'Authored source, tools, documentation and runtime patch; no game binary or original data',
            'passed':True}
    archive.with_suffix('.receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
