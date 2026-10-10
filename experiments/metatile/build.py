"""Build the excluded original-cost metatile prototype from a fresh public build.

Never modifies its base build/runtime or installs a player binary. Generated
inputs from the caller's owned-ROM build stay inside a fresh ignored local folder.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-build',type=Path,required=True,help='Folder containing source-build-receipt.json and project from tools/build_public_foundation.py')
    p.add_argument('--out',type=Path)
    p.add_argument('--cmake',default=shutil.which('cmake') or 'cmake')
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--indexed-dispatch',action='store_true',help='Apply the separate experimental normalized-key host lookup filter to the copied runtime only')
    a=p.parse_args();base=a.base_build.resolve(strict=True)
    receipt=json.loads((base/'source-build-receipt.json').read_text(encoding='utf-8'))
    assert receipt.get('public_build') and receipt['runtime_pin']=='7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0'
    source=base/'project';manifest=receipt['authored_inputs']
    if not all(sha(source/name)==value for name,value in manifest.items()):raise ValueError('Frozen base authored inputs changed; preserved.')
    if sha(base/'build/SecretOfTheStarsSNESRecomp.exe')!=receipt['executable_sha256']:raise ValueError('Base binary differs from its receipt; preserved.')
    cache=(base/'build/CMakeCache.txt').read_text(errors='replace')
    def option(name):
        match=re.search(r'^'+re.escape(name)+r':[^=]+=([^\r\n]*)',cache,re.M)
        if not match or not match[1]:raise ValueError('Missing base CMake option: '+name)
        return match[1]
    runtime=Path(option('SNESRECOMP_ROOT')).resolve(strict=True)
    runtime_header=(runtime/'runner/src/snes/interp_bridge.h').read_text()
    if 'interp_bridge_native_begin' not in runtime_header:raise ValueError('Required pinned native transaction API missing.')
    out=(a.out or ROOT/'local/experimental-metatile'/time.strftime('%Y%m%d-%H%M%S')).resolve()
    out.relative_to((ROOT/'local').resolve())
    if out.exists():raise ValueError('Output must be fresh; existing files preserved.')
    out.mkdir(parents=True);project=out/'project'
    shutil.copytree(source,project)
    shutil.copytree(runtime,out/'runtime',ignore=shutil.ignore_patterns('.git','__pycache__','build','build-*','.pytest_cache','_triage','cosim','docs','tests','fuzz','recompiler-rs'))
    runtime_before={f.relative_to(out/'runtime').as_posix():sha(f) for f in (out/'runtime').rglob('*') if f.is_file()}
    dispatch=None
    if a.indexed_dispatch:
        bridge=out/'runtime/runner/src/snes/interp_bridge.c'
        if sha(bridge)!='5c1308342c57f84e68e12160e8dc274ed4dbbf9b7e15e505aa71e7a0b11ac1de':
            raise ValueError('Dispatch experiment requires its exact frozen bridge base; no baseline is changed.')
        patch=HERE/'dispatch-index.patch'
        for args in (['git','apply','--ignore-space-change','--check',str(patch)],['git','apply','--ignore-space-change',str(patch)]):
            subprocess.run(args,cwd=out/'runtime',check=True)
        dispatch={'base_bridge_sha256':runtime_before['runner/src/snes/interp_bridge.c'],
            'patch_sha256':sha(patch),'patched_bridge_sha256':sha(bridge),
            'normalized_key_mask':'0x7fffff','key_presence_bytes':1048576,'page_presence_bytes':4096,
            'guest_clock_changes':False,'policy':'Filter enabled in this experimental copy; SNESRECOMP_EXPERIMENT_PREOP_INDEX=0 selects its original ordered scan.'}
    for name in ('foundation_queue_index.c','foundation_queue_index.h'):shutil.copy2(HERE/name,project/'src'/name)
    mainfile=project/'src/main.c';text=mainfile.read_text()
    if '#include "foundation_column_lookup.h"' not in text:raise ValueError('Expected title integration anchor missing.')
    text=text.replace('#include "foundation_column_lookup.h"','#include "foundation_column_lookup.h"\n#include "foundation_queue_index.h"')
    for suffix in ('Init','BeforeFrame','Reset','Shutdown'):
        anchor='    FoundationColumnLookup'+suffix+'();'
        if text.count(anchor)!=1:raise ValueError('Expected title lifecycle anchor missing or duplicated: '+suffix)
        text=text.replace(anchor,anchor+'\n    FoundationQueueIndex'+suffix+'();')
    mainfile.write_text(text)
    cmake=project/'CMakeLists.txt';text=cmake.read_text();anchor='    src/foundation_column_lookup.c'
    if text.count(anchor)!=1:raise ValueError('Expected CMake source anchor missing or duplicated.')
    cmake.write_text(text.replace(anchor,anchor+'\n    src/foundation_queue_index.c'))
    configure=[a.cmake,'-S',str(project),'-B',str(out/'build'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER='+option('CMAKE_C_COMPILER'),'-DCMAKE_CXX_COMPILER='+option('CMAKE_CXX_COMPILER'),
        '-DCMAKE_MAKE_PROGRAM='+option('CMAKE_MAKE_PROGRAM'),'-DSNESRECOMP_ROOT='+str(out/'runtime'),
        '-DSNESRECOMP_FRAME_IMPL=HLE','-DSNESRECOMP_SDL_BACKEND=SDL3','-DSNESRECOMP_ENABLE_NET=OFF']
    try:sdl=option('SDL3_DIR')
    except ValueError:sdl=None
    if sdl:configure.append('-DSDL3_DIR='+sdl)
    for label,cmd in [('configure',configure),('build',[a.cmake,'--build',str(out/'build'),'-j'+str(max(1,min(a.jobs,16)))])]:
        with (out/(label+'.log')).open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    if not all(sha(source/name)==value for name,value in manifest.items()):raise ValueError('Base source changed concurrently; output remains unqualified.')
    if runtime_before!={name:sha(runtime/name) for name in runtime_before}:raise ValueError('Base runtime changed concurrently; output remains unqualified.')
    result={'status':'experimental_compiled_unqualified','installed':False,'base_version':receipt['version'],'base_native_sha256':receipt['executable_sha256'],
        'base_source_receipt_sha256':sha(base/'source-build-receipt.json'),'runtime_pin':receipt['runtime_pin'],'runtime_patch_sha256':receipt['runtime_patch_sha256'],
        'executable_sha256':sha(out/'build/SecretOfTheStarsSNESRecomp.exe'),
        'experiment_inputs':{name:sha(project/name) for name in ('CMakeLists.txt','src/main.c','src/foundation_queue_index.c','src/foundation_queue_index.h')},
        'runtime_copy_before_sha256':runtime_before,'base_authored_inputs':manifest,
        'limits':['Compilation is not gameplay qualification.','Default off; original guest CPU and opcode costs only.','No owner profile, ROM, checkpoint or install is edited.']}
    result['experimental_dispatch_index']=dispatch
    (out/'experimental-build-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(out/'build/SecretOfTheStarsSNESRecomp.exe');print(result['executable_sha256'])

if __name__=='__main__':main()
