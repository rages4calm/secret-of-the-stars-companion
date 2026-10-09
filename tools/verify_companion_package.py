"""Check an extracted source-first package without running its executable."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json

def verify(root):
    root=Path(root).resolve(strict=True)
    metadata=json.loads((root/'portable-companion.json').read_text())
    if metadata.get('schema')!=1 or metadata.get('component')!='Companion' or metadata.get('game_data_included') is not False or metadata.get('native_game_included') is not False:
        raise ValueError('Unsupported package metadata.')
    files=metadata['files']
    if metadata['executable']!='Secret of the Stars Companion.exe' or files.get(metadata['executable'])!=metadata['executable_sha256']:
        raise ValueError('Executable identity is inconsistent.')
    if files.get('Companion/authored-files.json')!=metadata['source_manifest_sha256']:
        raise ValueError('Source manifest identity is inconsistent.')
    for name,digest in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Package path escapes root: '+name)
        resolved=(root/name).resolve(strict=True)
        if not resolved.is_relative_to(root) or any(p.is_symlink() for p in [root/name,*list((root/name).parents)[:-1]]):
            raise ValueError('Linked package file: '+name)
        if hashlib.sha256(resolved.read_bytes()).hexdigest()!=digest:
            raise ValueError('Package file changed: '+name)
    return {'passed':True,'version':metadata['version'],'files_checked':len(files),'companion_sha256':metadata['executable_sha256'],
        'limits':'Integrity check against local metadata; does not authenticate a publisher or qualify gameplay.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    print(json.dumps(verify(parser.parse_args().root),indent=2))
