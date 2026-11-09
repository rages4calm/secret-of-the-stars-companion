"""Package all Git-tracked ROM-free source, patches, notices and documentation."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New source ZIP, preferably in Temp; existing files preserved')
    args=parser.parse_args();output=args.output.resolve()
    if output.exists():raise ValueError('Output already exists; choose a fresh path.')
    check=subprocess.run([sys.executable,'-B',str(ROOT/'tools/check_public_source.py')],cwd=ROOT,capture_output=True,text=True,check=True)
    if not json.loads(check.stdout)['passed']:raise ValueError('Public source boundary did not pass.')
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf8').split('\0');entries={}
    for name in filter(None,names):
        path=ROOT/name
        if path.is_symlink()or not path.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Linked or escaping source: '+name)
        entries[name]=path.read_bytes()
    digest=lambda data:hashlib.sha256(data).hexdigest()
    manifest={name:digest(data)for name,data in sorted(entries.items())}
    entries['BUNDLE-MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode('utf8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED)as archive:
        for name,data in sorted(entries.items()):archive.writestr(name,data)
    with zipfile.ZipFile(output)as archive:
        assert sorted(archive.namelist())==sorted(entries)
        assert all(archive.read(name)==data for name,data in entries.items())
    result={'passed':True,'archive':str(output),'sha256':digest(output.read_bytes()),'source_files':len(manifest),'private_game_data_included':False,'scope':'Tracked authored source, reviewed documentation images and notices; no game binary.'}
    output.with_suffix('.receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
