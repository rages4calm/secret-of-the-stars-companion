"""Build an isolated presentation prototype from a matching public source build.

Normal foundation source/builds and owner profiles are never modified. This
experimental receipt deliberately cannot be adopted by Companion Setup.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
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
    source = base/'project'; manifest = receipt['authored_inputs']
    rom = args.rom.resolve(strict=True)
    if (receipt.get('status') != 'compiled_unqualified' or receipt.get('public_build') is not True or
        receipt.get('authored_inputs') != manifest or receipt.get('runtime_pin') != PIN or
        receipt.get('rom_sha256') != sha(rom) or sha(rom) != '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'):
        raise ValueError('Supply a real matching canonical source-build receipt and clean USA ROM.')
    if sha(base/'build/SecretOfTheStarsSNESRecomp.exe') != receipt['executable_sha256']: raise ValueError('Canonical executable changed.')
    for name, digest in manifest.items():
        if sha(source/name) != digest or sha(base/'project'/name) != digest: raise ValueError('Canonical source changed: '+name)
    expected_baseline = {'src/foundation_wide_actors.c': '69348ed2de92fe69fc3b4cb73e6cf84c504979b2cde8d0df729840ec4476eb7a', 'src/foundation_large_actor_canary.c': '76bc6a53a27de0a858a677a67c07a61a4617f65dc72522396320c4739e04c8b0', 'src/foundation_large_actor_canary.h': '070dabbc102889f198082f111820be19809d430df6c5666ed368e53e948545f4', 'src/foundation_wide.c': '1dffc24ae5b4222f2b4f337530e39ad08804fc589ae1105c4e1345b604374af8', 'src/foundation_wide_actors.h': '9cef473607a2ffbf9534d33d841eb041c1ae41a069a30f7f0833e54b6daed763'}
    if any(manifest.get(n)!=h for n,h in expected_baseline.items()):
        raise ValueError('This prototype requires the documented unchanged 0.2.1/0.2.2 actor/canary inputs.')
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
    protected = {p:sha(p) for p in [Path(__file__),rom,base_receipt,base/'build/SecretOfTheStarsSNESRecomp.exe',marker_path,
        *(base/'project').rglob('*')] if p.is_file()}
    experimental_names = ('foundation_wide_actors.c','foundation_large_actor_canary.c','foundation_large_actor_canary.h','foundation_wide.c','foundation_wide_actors.h')
    experimental_inputs = {HERE/name: sha(HERE/name) for name in experimental_names}
    protected.update(experimental_inputs)
    out = ROOT/'local/experimental-wrapping-b0'/time.strftime('%Y%m%d-%H%M%S'); out.mkdir(parents=True,exist_ok=False)
    project = out/'project'
    for name in manifest:
        destination=project/name; destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source/name,destination)
    shutil.copytree(base/'project/src/gen',project/'src/gen')
    shutil.copy2(base/'project/recomp/funcs.h',project/'recomp/funcs.h')
    (project/'mods/preloaded/packages').mkdir(parents=True)
    module = HERE/experimental_names[0]
    for path in experimental_inputs:
        shutil.copy2(path,project/'src'/path.name)
    version = 'private-wrap-periodic-v2'
    env=os.environ.copy(); env['PATH']=str(Path(cache['CMAKE_C_COMPILER']).parent)+';'+str(Path(cache['CMAKE_MAKE_PROGRAM']).parent)+';'+env.get('PATH','')
    configure=[cache.get('CMAKE_COMMAND',shutil.which('cmake')),'-S',str(project),'-B',str(out/'build'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER='+cache['CMAKE_C_COMPILER'],'-DCMAKE_CXX_COMPILER='+cache['CMAKE_CXX_COMPILER'],'-DCMAKE_MAKE_PROGRAM='+cache['CMAKE_MAKE_PROGRAM'],
        '-DSNESRECOMP_ROOT='+str(runtime),'-DSNESRECOMP_FRAME_IMPL=HLE','-DSNESRECOMP_SDL_BACKEND=SDL3','-DSNESRECOMP_ENABLE_NET=OFF','-DSDL3_DIR='+cache['SDL3_DIR'],
        '-DSNESRECOMP_BUILD_VERSION='+version]
    for name, command in [('configure',configure),('build',[configure[0],'--build',str(out/'build'),'-j'+str(args.jobs)])]:
        with (out/(name+'.log')).open('w') as log: subprocess.run(command,cwd=out,env=env,stdout=log,stderr=log,check=True)
    binary=out/'build/SecretOfTheStarsSNESRecomp.exe'
    if any(sha(p)!=h for p,h in protected.items()) or any(sha(source/n)!=h for n,h in manifest.items()) or any(sha(runtime/n)!=h for n,h in marker['patched_sources'].items()):
        raise RuntimeError('An input changed during compilation; preserve this output and investigate before using it.')
    result={'status':'compiled_unqualified_experimental','component':'NativeExperimentalWrappingB0','public_build':False,'matches_authored_snapshot':False,
        'installed':False,'build_helper_sha256':sha(Path(__file__)),'executable':str(binary),'executable_sha256':sha(binary),'version':version,'base_receipt':str(base_receipt),
        'base_receipt_sha256':sha(base_receipt),'baseline_inputs':manifest,'experimental_module_sha256':sha(module),
        'experimental_inputs':{str(p):h for p,h in experimental_inputs.items()},
        'candidate_inputs':{p.relative_to(project).as_posix():sha(p) for p in project.rglob('*') if p.is_file()},
        'rom_sha256':sha(rom),'runtime_pin':PIN,'runtime_patch_sha256':receipt['runtime_patch_sha256'],
        'limits':'Isolated wrapping B0 prototype compilation only. Original/staged gameplay, graphics, campaign and paced audio/GPU qualification are separate. Companion Setup must refuse this receipt.'}
    (out/'experimental-build-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('baseline_inputs','candidate_inputs')},indent=2))

if __name__=='__main__': main()
