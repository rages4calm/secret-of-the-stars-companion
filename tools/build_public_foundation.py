"""Build a fresh developer foundation from authored source and a supplied ROM.

Never copies the ROM into the repository, publishes generated code, installs
over an owner profile, or invents a gameplay qualification receipt.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
RUNTIME_URL='https://github.com/RetroPortingToolKit/snesrecomp.git'
RUNTIME_PIN='7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,cwd=None):
    result=subprocess.run([str(v) for v in args],cwd=cwd,check=True,capture_output=True,text=True)
    return result.stdout.strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--sdl3-dir',type=Path,help='Optional existing SDL3 CMake package; otherwise upstream fetches SDL3')
    p.add_argument('--cmake',default='cmake');p.add_argument('--cc',default='clang');p.add_argument('--cxx',default='clang++')
    p.add_argument('--ninja',default='ninja');p.add_argument('--jobs',type=int,default=8)
    args=p.parse_args()
    rom=args.rom.resolve(strict=True);source=ROOT/'native/foundation'
    identity={}
    for line in (source/'rom_identity.txt').read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);identity[k.strip()]=v.strip()
    expected=identity['expected_sha256'].lower()
    if sha(rom)!=expected or rom.stat().st_size!=int(identity['rom_size']):
        raise RuntimeError('Unsupported input. Supply the exact unheadered clean USA ROM specified in rom_identity.txt.')
    if args.jobs<1 or args.jobs>64:raise ValueError('--jobs must be 1..64')
    for tool in ('git','cargo',args.cmake,args.cc,args.cxx,args.ninja):
        if not shutil.which(tool):raise RuntimeError('Required tool is unavailable: '+tool)
    out=ROOT/'local/source-builds'/time.strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True,exist_ok=False)
    patch=out/'runtime-foundation.patch'
    shutil.copy2(ROOT/'patches/runtime-foundation.patch',patch)
    # A new patch gets its own checkout. Previously built or intentionally
    # modified runtimes remain available rather than being reset in place.
    runtime=ROOT/'local/upstream'/(RUNTIME_PIN[:12]+'-'+sha(patch)[:12])
    marker=runtime.parent/(runtime.name+'-patch-receipt.json')
    if not runtime.exists():
        runtime.parent.mkdir(parents=True,exist_ok=True)
        print('Fetching pinned runtime and its upstream submodules.',flush=True)
        command(['git','clone','--no-checkout',RUNTIME_URL,runtime])
        command(['git','checkout','--detach',RUNTIME_PIN],runtime)
        command(['git','submodule','update','--init','--recursive'],runtime)
    if command(['git','rev-parse','HEAD'],runtime)!=RUNTIME_PIN:
        raise RuntimeError('Existing runtime is at another revision; it has been preserved.')
    patch_names=re.findall(r'^diff --git a/(\S+) b/',patch.read_text(encoding='utf-8'),re.M)
    if marker.exists():
        receipt=json.loads(marker.read_text(encoding='utf-8'))
        if receipt['patch_sha256']!=sha(patch) or any(sha(runtime/n)!=h for n,h in receipt['patched_sources'].items()):
            raise RuntimeError('Existing patched runtime differs from its receipt; it has been preserved.')
        if set(command(['git','diff','--name-only'],runtime).splitlines())!=set(patch_names):
            raise RuntimeError('Unexpected runtime changes; preserved without reset.')
    else:
        if command(['git','diff','--name-only'],runtime):
            raise RuntimeError('Unrecognized runtime modifications; preserved without reset.')
        command(['git','apply','--check',patch],runtime);command(['git','apply',patch],runtime)
        marker.write_text(json.dumps({'runtime_pin':RUNTIME_PIN,'patch_sha256':sha(patch),
          'patched_sources':{n:sha(runtime/n) for n in patch_names}},indent=2)+'\n',encoding='utf-8')
    pins=dict(line.split('=',1) for line in (source/'framework_pins.txt').read_text().splitlines() if '=' in line)
    for key,name in [('rbengine','retcomm-rbengine'),('recomp-net','recomp-net')]:
        if command(['git','rev-parse','HEAD'],runtime/'lib'/name)!=pins[key]:
            raise RuntimeError('Upstream submodule pin mismatch: '+name)
    manifest=json.loads((source/'authored-files.json').read_text());project=out/'project'
    actual={}
    for name in manifest:
        src=source/name;dest=project/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest);actual[name]=sha(src)
    (project/'mods/preloaded/packages').mkdir(parents=True)
    print('Generating private local code from the verified ROM.',flush=True)
    generate=[sys.executable,runtime/'snesrecomp_cli.py','generate','--rom',rom,
      '--cfg-dir','recomp','--out-dir','src/gen','--funcs-h','recomp/funcs.h','--project-root',project,
      '--expected-crc32',identity['expected_crc32'],'--expected-sha256',expected]
    with (out/'generate.log').open('w',encoding='utf-8') as log:
        r=subprocess.run(list(map(str,generate)),cwd=project,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Generation failed; inspect '+str(out/'generate.log'))
    cmake=[args.cmake,'-S',project,'-B',out/'build','-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
      '-DCMAKE_C_COMPILER='+args.cc,'-DCMAKE_CXX_COMPILER='+args.cxx,
      '-DCMAKE_MAKE_PROGRAM='+str(Path(shutil.which(args.ninja)).resolve()),
      '-DSNESRECOMP_ROOT='+str(runtime),'-DSNESRECOMP_FRAME_IMPL=HLE',
      '-DSNESRECOMP_SDL_BACKEND=SDL3','-DSNESRECOMP_ENABLE_NET=OFF']
    if args.sdl3_dir:cmake.append('-DSDL3_DIR='+str(args.sdl3_dir.resolve(strict=True)))
    for name,cmd in [('configure',cmake),('build',[args.cmake,'--build',out/'build','-j'+str(args.jobs)])]:
        print(name.capitalize()+'...',flush=True)
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            r=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError(name+' failed; inspect '+str(out/(name+'.log')))
    binary=out/'build/SecretOfTheStarsSNESRecomp.exe'
    if not binary.exists():raise RuntimeError('Windows executable missing after build.')
    profile=out/'profile';profile.mkdir();shutil.copy2(binary,profile/binary.name)
    (profile/'config.ini').write_text('[Graphics]\nRenderer=direct3d11\nFullscreen=0\nVSync=1\nNewRenderer=0\nWidescreen=0\n[Sound]\nEnableAudio=1\nAudioFreq=32040\nAudioChannels=2\nAudioSamples=512\n[General]\nAutosave=0\nSkipLauncher=1\n',encoding='ascii')
    (profile/'foundation.ini').write_text('[Enhancements]\nEnhancedPixels=1\nBattleInfo=1\nFastMenus=1\nJournal=1\nExperimentalFieldWide=0\nExperimentalFieldActors=0\nNativeClear=0\nNativeColumns=0\nHdMenuFrames=0\nXpMultiplierPercent=100\nGoldMultiplierPercent=100\nMovementSpeedPercent=200\nFastForwardToggle=0\nLegacyControllerGestures=1\n',encoding='ascii')
    assert sha(rom)==expected
    result={'status':'compiled_unqualified','public_build':True,'executable_sha256':sha(binary),
      'version':(project/'VERSION').read_text().strip(),'rom_sha256':expected,'rom_copied':False,
      'authored_inputs':actual,'matches_authored_snapshot':actual==manifest,
      'runtime_pin':RUNTIME_PIN,'runtime_patch_sha256':sha(patch),
      'private_generated_files':[p.relative_to(out).as_posix() for p in (project/'src/gen').rglob('*') if p.is_file()],
      'profile':profile.relative_to(ROOT).as_posix(),
      'limits':'Fresh developer compilation only; gameplay qualification and owner installation remain separate.'}
    (out/'source-build-receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Built: '+str(binary));print('Fresh profile: '+str(profile))
    print('Run from the fresh profile: SecretOfTheStarsSNESRecomp.exe --no-launcher --rom "<your original ROM path>"')

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
