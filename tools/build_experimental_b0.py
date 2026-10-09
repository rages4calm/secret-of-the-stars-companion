"""Build the isolated B0 prototype from an existing matching public source build.

Normal foundation source/builds and owner profiles are never modified. This
experimental receipt deliberately cannot be adopted by Companion Setup.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time

ROOT = Path(__file__).resolve().parents[1]
PIN = '7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inside(path, parent):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(parent.resolve(strict=True)): raise ValueError('Input is outside its source-build boundary: '+str(path))
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-receipt', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 64: raise ValueError('--jobs must be 1..64')
    base_receipt = inside(args.base_receipt, ROOT/'local/source-builds')
    base = base_receipt.parent; receipt = json.loads(base_receipt.read_text())
    source = ROOT/'native/foundation'; manifest = json.loads((source/'authored-files.json').read_text())
    rom = args.rom.resolve(strict=True)
    if (receipt.get('status') != 'compiled_unqualified' or receipt.get('public_build') is not True or
        receipt.get('authored_inputs') != manifest or receipt.get('runtime_pin') != PIN or
        receipt.get('rom_sha256') != sha(rom) or sha(rom) != '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'):
        raise ValueError('Supply a real matching canonical source-build receipt and clean USA ROM.')
    if sha(base/'build/SecretOfTheStarsSNESRecomp.exe') != receipt['executable_sha256']: raise ValueError('Canonical executable changed.')
    for name, digest in manifest.items():
        if sha(source/name) != digest or sha(base/'project'/name) != digest: raise ValueError('Canonical source changed: '+name)
    cache = {}
    for line in (base/'build/CMakeCache.txt').read_text().splitlines():
        if '=' in line and ':' in line.split('=',1)[0]: cache[line.split(':',1)[0]] = line.split('=',1)[1]
    runtime = inside(cache['SNESRECOMP_ROOT'], ROOT/'local/upstream')
    marker_path = runtime.parent/(runtime.name+'-patch-receipt.json'); marker = json.loads(marker_path.read_text())
    if marker['patch_sha256'] != receipt['runtime_patch_sha256'] or any(sha(runtime/n) != h for n,h in marker['patched_sources'].items()):
        raise ValueError('Runtime changed; it has been preserved.')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=runtime,text=True).strip() != PIN: raise ValueError('Runtime pin changed.')
    changed = set(subprocess.check_output(['git','diff','--name-only'],cwd=runtime,text=True).splitlines())
    if changed != set(marker['patched_sources']): raise ValueError('Unexpected runtime edits; preserved without reset.')
    protected = {p:sha(p) for p in [rom,base_receipt,base/'build/SecretOfTheStarsSNESRecomp.exe',marker_path,
        *(base/'project').rglob('*')] if p.is_file()}
    out = ROOT/'local/experimental-b0'/time.strftime('%Y%m%d-%H%M%S'); out.mkdir(parents=True,exist_ok=False)
    project = out/'project'
    for name in manifest:
        destination=project/name; destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source/name,destination)
    shutil.copytree(base/'project/src/gen',project/'src/gen')
    shutil.copy2(base/'project/recomp/funcs.h',project/'recomp/funcs.h')
    (project/'mods/preloaded/packages').mkdir(parents=True)
    module = ROOT/'experiments/b0/foundation_wide_actors.c'
    shutil.copy2(module,project/'src/foundation_wide_actors.c')
    for name in ('foundation_large_actor_canary.c','foundation_large_actor_canary.h'): shutil.copy2(ROOT/'tools'/name,project/'src'/name)
    cmake_file = project/'CMakeLists.txt'
    cmake_file.write_text(cmake_file.read_text().replace('    src/foundation_wide_actors.c','    src/foundation_wide_actors.c\n    src/foundation_large_actor_canary.c'))
    env=os.environ.copy(); env['PATH']=str(Path(cache['CMAKE_C_COMPILER']).parent)+';'+str(Path(cache['CMAKE_MAKE_PROGRAM']).parent)+';'+env.get('PATH','')
    configure=[cache.get('CMAKE_COMMAND',shutil.which('cmake')),'-S',str(project),'-B',str(out/'build'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER='+cache['CMAKE_C_COMPILER'],'-DCMAKE_CXX_COMPILER='+cache['CMAKE_CXX_COMPILER'],'-DCMAKE_MAKE_PROGRAM='+cache['CMAKE_MAKE_PROGRAM'],
        '-DSNESRECOMP_ROOT='+str(runtime),'-DSNESRECOMP_FRAME_IMPL=HLE','-DSNESRECOMP_SDL_BACKEND=SDL3','-DSNESRECOMP_ENABLE_NET=OFF','-DSDL3_DIR='+cache['SDL3_DIR'],
        '-DSNESRECOMP_BUILD_VERSION=experimental-b0-v1']
    for name, command in [('configure',configure),('build',[configure[0],'--build',str(out/'build'),'-j'+str(args.jobs)])]:
        with (out/(name+'.log')).open('w') as log: subprocess.run(command,cwd=out,env=env,stdout=log,stderr=log,check=True)
    binary=out/'build/SecretOfTheStarsSNESRecomp.exe'
    if any(sha(p)!=h for p,h in protected.items()) or any(sha(source/n)!=h for n,h in manifest.items()) or any(sha(runtime/n)!=h for n,h in marker['patched_sources'].items()):
        raise RuntimeError('An input changed during compilation; preserve this output and investigate before using it.')
    result={'status':'compiled_unqualified_experimental','component':'NativeExperimentalB0','public_build':False,'matches_authored_snapshot':False,
        'installed':False,'executable':str(binary),'executable_sha256':sha(binary),'version':'experimental-b0-v1','base_receipt':str(base_receipt),
        'base_receipt_sha256':sha(base_receipt),'baseline_inputs':manifest,'experimental_module_sha256':sha(module),
        'candidate_inputs':{p.relative_to(project).as_posix():sha(p) for p in project.rglob('*') if p.is_file()},
        'rom_sha256':sha(rom),'runtime_pin':PIN,'runtime_patch_sha256':receipt['runtime_patch_sha256'],
        'limits':'Experimental B0 producer/packet/PPU source only. No natural B0 artwork, campaign, paced audio/GPU or playable release qualification. Companion Setup must refuse this receipt.'}
    (out/'experimental-build-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('baseline_inputs','candidate_inputs')},indent=2))

if __name__=='__main__': main()
