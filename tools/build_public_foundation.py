"""Build a fresh developer foundation from authored source and a supplied ROM.

Never copies the ROM into the repository, publishes generated code, installs
over an owner profile, or invents a gameplay qualification receipt.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
RUNTIME_URL='https://github.com/RetroPortingToolKit/snesrecomp.git'
RUNTIME_PIN='7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0'
FAITHFUL_INSTRUCTION_PATCH_SHA256='0d342317b3f997c2f56517c02363a9162d68194ce8e473a43207c25da62050a3'
HOST_AUDIO_PATCH_SHA256='6381bc9937a9ed478bc27b3cdcd29e5653921478fe1ee2c536dd9d7cb6d7ec5e'
HOST_NAVIGATION_PATCH_SHA256='91fea10b53d3eca67364eceebfb802a2c1c79432ff7424d02c5f8755438dc028'
AUTOMATIC_FAITHFUL_PATCH_SHA256='3909fc5f917461da99c18c1ac5f44267d11f7f0c287f2f93ecc68506139d5e40'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,cwd=None):
    result=subprocess.run([str(v) for v in args],cwd=cwd,check=True,capture_output=True,text=True)
    return result.stdout.strip()

def reject_links(path):
    for item in (path,*path.parents):
        try: stat=item.lstat()
        except FileNotFoundError: continue
        if item.is_symlink() or getattr(stat,'st_file_attributes',0)&0x400:
            raise ValueError('Linked build input/output preserved: '+str(item))

def snapshot_authored(source,project):
    reject_links(source.absolute());reject_links(project.absolute())
    path=source/'authored-files.json';reject_links(path)
    manifest=json.loads(path.read_text());actual={}
    if not isinstance(manifest,dict) or not manifest:raise ValueError('Empty or invalid authored manifest')
    for name,expected in manifest.items():
        if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Authored input escapes snapshot')
        src=source/name;reject_links(src)
        if not src.resolve(strict=True).is_relative_to(source.resolve(strict=True)):
            raise ValueError('Authored input escapes source')
        actual[name]=sha(src)
        if actual[name]!=expected:raise ValueError('Modified authored input preserved: '+name)
    if project.exists():raise ValueError('Existing project preserved')
    project.mkdir(parents=True,exist_ok=False)
    for name in manifest:
        dst=project/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,dst)
    if any(sha(project/n)!=h or sha(source/n)!=h for n,h in actual.items()):
        raise RuntimeError('Authored snapshot changed during copy; build refused')
    return manifest,actual

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--runtime-cache-dir',type=Path,help='Optional isolated runtime cache directory; same pinned five-patch key and validation')
    p.add_argument('--sdl3-dir',type=Path,help='Optional existing SDL3 CMake package; otherwise upstream fetches SDL3')
    p.add_argument('--cmake',default='cmake');p.add_argument('--cc',default='clang');p.add_argument('--cxx',default='clang++')
    p.add_argument('--ninja',default='ninja');p.add_argument('--jobs',type=int,default=8)
    args=p.parse_args()
    reject_links(args.rom.absolute());reject_links(ROOT.absolute())
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
    reject_links(out)
    out.mkdir(parents=True,exist_ok=False)
    patch=out/'runtime-foundation.patch'
    shutil.copy2(ROOT/'patches/runtime-foundation.patch',patch)
    # A separate title-input extension cannot change serialized machine state.
    # Retain the original execution patch hash for checkpoint ABI comparison.
    host_patch=out/'runtime-navigation-map.patch'
    shutil.copy2(ROOT/'patches/runtime-navigation-map.patch',host_patch)
    if sha(host_patch)!=HOST_NAVIGATION_PATCH_SHA256:
        raise RuntimeError('Navigation input patch changed; audit its execution compatibility before building.')
    host_names=re.findall(r'^diff --git a/(\S+) b/',host_patch.read_text(encoding='utf-8'),re.M)
    if set(host_names)!={'runner/src/desktop/config.h','runner/src/desktop/mmx_config.c','runner/src/desktop/host_main.c'} or len(host_names)!=3:
        raise RuntimeError('Navigation extension exceeds its host-input source boundary.')
    faithful_patch=out/'runtime-faithful-clear.patch'
    shutil.copy2(ROOT/'patches/runtime-faithful-clear.patch',faithful_patch)
    if sha(faithful_patch)!=FAITHFUL_INSTRUCTION_PATCH_SHA256:
        raise RuntimeError('Faithful instruction patch changed; audit its state and timing compatibility before building.')
    faithful_names=re.findall(r'^diff --git a/(\S+) b/',faithful_patch.read_text(encoding='utf-8'),re.M)
    if set(faithful_names)!={'runner/src/snes/interp_bridge.c','runner/src/snes/interp_bridge.h'} or len(faithful_names)!=2:
        raise RuntimeError('Faithful extension exceeds its two-file transaction API boundary.')
    audio_patch=out/'runtime-modal-audio.patch'
    shutil.copy2(ROOT/'patches/runtime-modal-audio.patch',audio_patch)
    if sha(audio_patch)!=HOST_AUDIO_PATCH_SHA256:
        raise RuntimeError('Modal audio patch changed; audit its host-only scope before building.')
    audio_names=re.findall(r'^diff --git a/(\S+) b/',audio_patch.read_text(encoding='utf-8'),re.M)
    if audio_names!=['runner/src/desktop/host_main.c']:
        raise RuntimeError('Modal audio extension exceeds its host-only source boundary.')
    automatic_patch=out/'runtime-automatic-faithful.patch'
    shutil.copy2(ROOT/'patches/runtime-automatic-faithful.patch',automatic_patch)
    if sha(automatic_patch)!=AUTOMATIC_FAITHFUL_PATCH_SHA256:
        raise RuntimeError('Automatic instruction patch changed; explicitly review its architectural, bus and scheduler compatibility before building.')
    automatic_names=re.findall(r'^diff --git a/(\S+) b/',automatic_patch.read_text(encoding='utf-8'),re.M)
    if set(automatic_names)!={'recompiler/v2/emit_function.py','recompiler/v2/codegen.py','runner/src/cpu_state.h','runner/src/snes/interp_bridge.c'} or len(automatic_names)!=4:
        raise RuntimeError('Automatic instruction extension exceeds its four-file generator/bridge boundary.')
    # A new patch gets its own checkout. Previously built or intentionally
    # modified runtimes remain available rather than being reset in place.
    cache_root=args.runtime_cache_dir.absolute() if args.runtime_cache_dir else ROOT/'local/upstream'
    reject_links(cache_root)
    runtime=cache_root/(RUNTIME_PIN[:12]+'-'+sha(patch)[:12]+'-'+sha(host_patch)[:12]+'-'+sha(faithful_patch)[:12]+'-'+sha(audio_patch)[:12]+'-'+sha(automatic_patch)[:12])
    marker=runtime.parent/(runtime.name+'-patch-receipt.json')
    reject_links(runtime);reject_links(marker)
    if not runtime.exists():
        runtime.parent.mkdir(parents=True,exist_ok=True)
        print('Fetching pinned runtime and its upstream submodules.',flush=True)
        command(['git','clone','--no-checkout',RUNTIME_URL,runtime])
        command(['git','checkout','--detach',RUNTIME_PIN],runtime)
        command(['git','submodule','update','--init','--recursive'],runtime)
    if command(['git','rev-parse','HEAD'],runtime)!=RUNTIME_PIN:
        raise RuntimeError('Existing runtime is at another revision; it has been preserved.')
    patch_names=sorted(set(re.findall(r'^diff --git a/(\S+) b/',patch.read_text(encoding='utf-8'),re.M))|set(host_names)|set(faithful_names)|set(audio_names)|set(automatic_names))
    if marker.exists():
        receipt=json.loads(marker.read_text(encoding='utf-8'))
        if (receipt['patch_sha256']!=sha(patch) or receipt.get('host_navigation_patch_sha256')!=sha(host_patch)
                or receipt.get('faithful_instruction_patch_sha256')!=sha(faithful_patch)
                or receipt.get('host_modal_audio_patch_sha256')!=sha(audio_patch)
                or receipt.get('automatic_faithful_patch_sha256')!=sha(automatic_patch)
                or set(receipt['patched_sources'])!=set(patch_names)
                or any(sha(runtime/n)!=h for n,h in receipt['patched_sources'].items())):
            raise RuntimeError('Existing patched runtime differs from its receipt; it has been preserved.')
        if set(command(['git','diff','--name-only'],runtime).splitlines())!=set(patch_names):
            raise RuntimeError('Unexpected runtime changes; preserved without reset.')
    else:
        if command(['git','diff','--name-only'],runtime):
            raise RuntimeError('Unrecognized runtime modifications; preserved without reset.')
        command(['git','apply','--check',patch],runtime);command(['git','apply',patch],runtime)
        command(['git','apply','--check',host_patch],runtime);command(['git','apply',host_patch],runtime)
        command(['git','apply','--check',faithful_patch],runtime);command(['git','apply',faithful_patch],runtime)
        command(['git','apply','--check',audio_patch],runtime);command(['git','apply',audio_patch],runtime)
        command(['git','apply','--check',automatic_patch],runtime);command(['git','apply',automatic_patch],runtime)
        marker.write_text(json.dumps({'runtime_pin':RUNTIME_PIN,'patch_sha256':sha(patch),
          'host_navigation_patch_sha256':sha(host_patch),
          'faithful_instruction_patch_sha256':sha(faithful_patch),
          'host_modal_audio_patch_sha256':sha(audio_patch),
          'automatic_faithful_patch_sha256':sha(automatic_patch),
          'patched_sources':{n:sha(runtime/n) for n in patch_names}},indent=2)+'\n',encoding='utf-8')
    pins=dict(line.split('=',1) for line in (source/'framework_pins.txt').read_text().splitlines() if '=' in line)
    for key,name in [('rbengine','retcomm-rbengine'),('recomp-net','recomp-net')]:
        if command(['git','rev-parse','HEAD'],runtime/'lib'/name)!=pins[key]:
            raise RuntimeError('Upstream submodule pin mismatch: '+name)
    project=out/'project'
    manifest,actual=snapshot_authored(source,project)
    (project/'mods/preloaded/packages').mkdir(parents=True)
    print('Generating private local code from the verified ROM.',flush=True)
    generate=[sys.executable,runtime/'snesrecomp_cli.py','generate','--rom',rom,
      '--cfg-dir','recomp','--out-dir','src/gen','--funcs-h','recomp/funcs.h','--project-root',project,
      '--expected-crc32',identity['expected_crc32'],'--expected-sha256',expected,'--cfg-roots']
    with (out/'generate.log').open('w',encoding='utf-8') as log:
        r=subprocess.run(list(map(str,generate)),cwd=project,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Generation failed; inspect '+str(out/'generate.log'))
    automatic_manifest_path=project/'src/gen/program_manifest.json'
    reject_links(automatic_manifest_path)
    automatic_manifest=json.loads(automatic_manifest_path.read_text(encoding='utf-8'))
    if (automatic_manifest.get('format_version')!=3
            or not isinstance(automatic_manifest.get('nodes'),dict)
            or not automatic_manifest['nodes']
            or not isinstance(automatic_manifest.get('roots'),list)):
        raise RuntimeError('Unrecognized automatic generation manifest; preserve this build and explicitly review its contract.')
    dispositions={};diagnostic_targets=set()
    for node in automatic_manifest['nodes'].values():
        key=node.get('key',{});pc=key.get('pc24');disposition=node.get('disposition')
        if (type(pc)is not int or not 0<=pc<=0xffffff
                or key.get('m')not in (0,1) or key.get('x')not in (0,1)
                or disposition not in ('aot_eligible','lle_only')):
            raise RuntimeError('Unrecognized automatic node context; preserve this build without assuming native eligibility.')
        dispositions[disposition]=dispositions.get(disposition,0)+1
        diagnostic_targets.add(pc)
    # Private derived list, not published guest code. The existing runtime
    # diagnostic can refuse every discovered entry, including interrupt calls;
    # bounce=0 alone does not do that. Runtime hit counts must still confirm
    # an actual original-byte oracle for each qualification route.
    diagnostic_target_path=project/'src/gen/automatic-original-targets.txt'
    reject_links(diagnostic_target_path)
    with diagnostic_target_path.open('x',encoding='ascii',newline='\n')as diagnostic:
        diagnostic.write(''.join(f'{pc:06X}\n'for pc in sorted(diagnostic_targets)))
    clear_generator=project/'tools/generate_faithful_clear.py'
    if not clear_generator.is_file():raise RuntimeError('Authored snapshot is missing the faithful-clear generator; refresh its manifest before building.')
    with (out/'generate-faithful-clear.log').open('w',encoding='utf-8') as log:
        r=subprocess.run([sys.executable,str(clear_generator),'--rom',str(rom),'--project-root',str(project)],
                         cwd=project,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Faithful clear generation failed; inspect '+str(out/'generate-faithful-clear.log'))
    clear_provenance_path=project/'src/gen/faithful_clear.provenance.json'
    clear_provenance=json.loads(clear_provenance_path.read_text(encoding='utf-8'))
    if (clear_provenance.get('generator_sha256')!=actual['tools/generate_faithful_clear.py']
        or clear_provenance.get('rom_sha256')!=expected
        or clear_provenance.get('output_sha256')!=sha(project/'src/gen/faithful_clear.generated.h')):
        raise RuntimeError('Generated clear provenance does not match the authored snapshot and ROM.')
    constructor_generator=project/'tools/generate_constructor.py'
    if not constructor_generator.is_file():raise RuntimeError('Authored constructor generator missing; refresh manifest before building.')
    with (out/'generate-constructor.log').open('w',encoding='utf-8') as log:
        r=subprocess.run([sys.executable,str(constructor_generator),'--rom',str(rom),'--project-root',str(project)],cwd=project,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Constructor generation failed; inspect '+str(out/'generate-constructor.log'))
    constructor_provenance_path=project/'src/gen/constructor.provenance.json'
    constructor_provenance=json.loads(constructor_provenance_path.read_text(encoding='utf-8'))
    if (constructor_provenance.get('module')!='secret-of-the-stars-faithful-constructor-v1'
        or constructor_provenance.get('generator_sha256')!=actual['tools/generate_constructor.py']
        or constructor_provenance.get('rom_sha256')!=expected
        or constructor_provenance.get('output_sha256')!=sha(project/'src/gen/constructor.generated.h')
        or constructor_provenance.get('sites_sha256')!=sha(project/'src/gen/constructor_sites.generated.h')):
        raise RuntimeError('Generated constructor provenance differs from authored snapshot and ROM.')
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
    if any(sha(source/n)!=h or sha(project/n)!=h for n,h in actual.items()):
        raise RuntimeError('Authored inputs changed during build; compilation retained unqualified.')
    binary=out/'build/SecretOfTheStarsSNESRecomp.exe'
    if not binary.exists():raise RuntimeError('Windows executable missing after build.')
    profile=out/'profile';profile.mkdir();shutil.copy2(binary,profile/binary.name)
    (profile/'config.ini').write_text('[Graphics]\nRenderer=direct3d11\nFullscreen=0\nVSync=1\nNewRenderer=0\nWidescreen=0\n[Sound]\nEnableAudio=1\nAudioFreq=32040\nAudioChannels=2\nAudioSamples=512\n[General]\nAutosave=0\nSkipLauncher=1\n',encoding='ascii')
    (profile/'foundation.ini').write_text('[Enhancements]\nEnhancedPixels=1\nBattleInfo=1\nFastMenus=1\nJournal=1\nNavigationMap=1\nNavigationMapObjective=1\nExperimentalFieldWide=0\nExperimentalFieldActors=0\nNativeClear=0\nNativeColumns=0\nHdMenuFrames=0\nXpMultiplierPercent=100\nGoldMultiplierPercent=100\nMovementSpeedPercent=200\nFastForwardToggle=0\nLegacyControllerGestures=1\n',encoding='ascii')
    assert sha(rom)==expected
    state_source=(project/'src/foundation_state.c').read_text()
    schema=re.search(r'#define FOUNDATION_VERSION (\d+)u',state_source)
    state_identity=re.search(r'FoundationStateIdentity\(void\).*?return "([^"]+)"',state_source)
    if not schema or not state_identity or 'header[1] < 1 || header[1] > FOUNDATION_VERSION' not in state_source:
        raise RuntimeError('Checkpoint contract changed; preserve this build and explicitly update its compatibility declaration before adoption.')
    schema_version=int(schema.group(1))
    result={'status':'compiled_unqualified','public_build':True,'executable_sha256':sha(binary),
      'version':(project/'VERSION').read_text().strip(),'rom_sha256':expected,'rom_copied':False,
      'authored_inputs':actual,'matches_authored_snapshot':actual==manifest,
      'runtime_pin':RUNTIME_PIN,'runtime_patch_sha256':sha(patch),
      'host_navigation_patch_sha256':sha(host_patch),
          'faithful_instruction_patch_sha256':sha(faithful_patch),
          'host_modal_audio_patch_sha256':sha(audio_patch),
      'automatic_faithful_patch_sha256':sha(automatic_patch),
      'automatic_faithful_patch_scope':'Upstream decoded instruction/IR emission with original bus transfers and internal clocks, per-instruction scheduler commits, cached effective addresses, native flag/return semantics and faithful unsupported continuation. No serialized guest fields or checkpoint/SRAM layout changes.',
      'automatic_generation':{'mode':'upstream-faithful-instruction','cfg_roots':True,
          'manifest':automatic_manifest_path.relative_to(out).as_posix(),'manifest_sha256':sha(automatic_manifest_path),
          'root_mode_contexts':len(automatic_manifest['roots']),'discovered_mode_nodes':len(automatic_manifest['nodes']),
          'dispositions':dispositions,'eligibility_is_execution_coverage':False,
          'guarded_clear_constructor_default':'Existing authored guarded islands remain enabled simultaneously in normal player launches; exact automatic-native qualification separately disables both using explicit environment controls.',
          'original_byte_diagnostic':{'target_file':diagnostic_target_path.relative_to(out).as_posix(),
              'target_file_sha256':sha(diagnostic_target_path),'unique_entry_targets':len(diagnostic_targets),
              'enabled_by_default':False,'environment':{
                  'SNESRECOMP_LLE_INTERP_TARGET_FILE':'<absolute path to this generated target file>',
                  'SNESRECOMP_FOUNDATION_GENERATED_CLEAR':'0','SNESRECOMP_FOUNDATION_GENERATED_CONSTRUCTOR':'0'},
              'limits':'Diagnostic configuration only; actual compiled-call/instruction evidence must verify original-byte admission. Does not change normal profile settings.'}},
      'host_navigation_patch_scope':'Appended map hotkey, parser/defaults and host dispatch only; existing command ids and serialized guest execution unchanged.',
      'host_modal_audio_patch_scope':'Host playback pause/prefill resume and overlay request consumption only; no guest machine or checkpoint layout changes.',
      'faithful_instruction_patch_scope':'Byte transaction wrapper/declaration only; existing bus/clock and checkpoint layout unchanged.',
      'checkpoint_schema':{'identity':state_identity.group(1),'writes':schema_version,'reads':list(range(1,schema_version+1))},
      'save_compatibility':'secret-of-the-stars-usa-sram-v1',
      'execution_state_abi_sha256':hashlib.sha256(('\n'.join(actual[name] for name in ('src/foundation_state.c','src/foundation_state.h','src/game_rtl.c','src/game_rtl.h','src/variables.h'))+'\n'+RUNTIME_PIN+'\n'+sha(patch)).encode()).hexdigest(),
      'private_generated_files':[p.relative_to(out).as_posix() for p in (project/'src/gen').rglob('*') if p.is_file()],
      'generated_guest_islands':{'faithful_constructor':{
          'generator_input':'tools/generate_constructor.py','generator_sha256':actual['tools/generate_constructor.py'],
          'provenance_file':constructor_provenance_path.relative_to(out).as_posix(),'provenance_sha256':sha(constructor_provenance_path),
          'generated_header':'project/src/gen/constructor.generated.h','generated_header_sha256':constructor_provenance['output_sha256'],
          'sites_header':'project/src/gen/constructor_sites.generated.h','sites_header_sha256':constructor_provenance['sites_sha256'],
          'instruction_bytes_sha256':constructor_provenance['instruction_bytes_sha256'],'entry_pcs':[node['pc'] for node in constructor_provenance['nodes']],
          'default_variant':'guarded-outer-constructor','scope':constructor_provenance['scope']},'faithful_clear':{
          'generator_input':'tools/generate_faithful_clear.py','generator_sha256':actual['tools/generate_faithful_clear.py'],
          'provenance_file':clear_provenance_path.relative_to(out).as_posix(),'provenance_sha256':sha(clear_provenance_path),
          'generated_header':'project/src/gen/faithful_clear.generated.h','generated_header_sha256':clear_provenance['output_sha256'],
          'instruction_bytes_sha256':clear_provenance['instruction_bytes_sha256'],'entry_pcs':[node['pc'] for node in clear_provenance['nodes']],
          'scope':'Complete guarded CB19-CB34 routine with original C45E call/CB34 RTS; existing scheduler frontend retained.',
          'default_variant':'whole-routine','legacy_variant':'three-instruction','legacy_entry_pcs':[node['pc'] for node in clear_provenance['legacy_nodes']]}},
      'profile':profile.relative_to(ROOT).as_posix(),
      'limits':'Fresh developer compilation only; gameplay qualification and owner installation remain separate.'}
    (out/'source-build-receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Built: '+str(binary));print('Fresh profile: '+str(profile))
    print('Run from the fresh profile: SecretOfTheStarsSNESRecomp.exe --no-launcher --rom "<your original ROM path>"')

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
