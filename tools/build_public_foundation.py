"""Build a fresh developer foundation from authored source and a supplied ROM.

Never copies the ROM into the repository, publishes generated code, installs
over an owner profile, or invents a gameplay qualification receipt.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
RUNTIME_URL='https://github.com/RetroPortingToolKit/snesrecomp.git'
RUNTIME_PIN='7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0'
FAITHFUL_INSTRUCTION_PATCH_SHA256='0d342317b3f997c2f56517c02363a9162d68194ce8e473a43207c25da62050a3'
HOST_AUDIO_PATCH_SHA256='6381bc9937a9ed478bc27b3cdcd29e5653921478fe1ee2c536dd9d7cb6d7ec5e'
HOST_NAVIGATION_PATCH_SHA256='91fea10b53d3eca67364eceebfb802a2c1c79432ff7424d02c5f8755438dc028'
AUTOMATIC_FAITHFUL_PATCH_SHA256='3909fc5f917461da99c18c1ac5f44267d11f7f0c287f2f93ecc68506139d5e40'
LIFECYCLE_PATCH_SHA256='d8828f856964d8f9331fd1b9432ebff72c78a65109a75395e02a3e8fa6bf345a'
PREFIX_PATCH_SHA256='32905d2a9be83e62a84cc0fb0286433ef0e509fe21fb60c64b38532834e0bf0f'
FAITHFUL_HOOK_BOUNDARY_PATCH_SHA256='410d54a4e1e782dbabf2a11f8d4211035621ae77a8ed68138523dde32588024c'
REVIEWED_ROOTS_PATCH_SHA256='80bde334f29c7c29cba8ebb9b4f743f4d082abd23f2a808bf9f2c85817652521'
REVIEWED_ROOTS_PATCH_NAMES=('recompiler/v2/reviewed_roots.py','tools/v2_emit.py','tools/sdk_generate.py','snesrecomp_cli.py')
REVIEWED_ROOTS_INPUT='recomp/reviewed-roots.json'
CONVERGED_EXIT_PATCH_SHA256='7788775dad2fcaced635b3c9805358471dbd4943815ea762a7bba8f4bfdc27a4'
CONVERGED_EXIT_PATCH_NAMES=('recompiler-rs/src/bin/analyze.rs', 'tools/v2_analyze.py', 'tools/v2_emit.py', 'tools/sdk_generate.py', 'snesrecomp_cli.py')

FOUNDATION_PATCH_SHA256='526f7d87b5cf736ce8b57da9db5f4435cce8d33ed1686a587a6a02ca66d73318'
ACCUMULATOR_PATCH_SHA256='aee2cf5169754cf5a9d7c652387e47055643ad7adc0c6e5b2df2eb8bf5fea216'
ACCUMULATOR_EMITTER_SHA256='1d667783bd9deae9ac52507aeaf13dae4ba59abd6ec7e5590d6c4c9c9b74dd8b'
ACCUMULATOR_UNIT_SHA256='1c2dea4f5c973ce732adebdafe5331fd09d5411088aadfab2674e06b316bc267'
ACCUMULATOR_PREDECESSOR_CRLF_SHA256='9848f8cdcc1c546b3830924551b8cba2aef43be8d77a934122ca4035b4a775a3'
ACCUMULATOR_PREDECESSOR_LF_SHA256='8b395ddd799dc556a4955fb1d0c427509325e93e20447410906b126992183622'
ACCUMULATOR_OUTPUT_CRLF_SHA256='b70f61231eec6ea4fad829a06c5fd766c716d96d79842a08fb19974834bf322d'

def runtime_source_accounting(runtime,patch_names,new_names=()):
    tracked=set(command(['git','diff','--name-only'],runtime).splitlines())
    untracked=set(command(['git','ls-files','--others','--exclude-standard'],runtime).splitlines())
    if tracked!=set(patch_names)-set(new_names)or untracked!=set(new_names):
        raise RuntimeError('Unexpected tracked or new runtime sources; preserved without reset.')

def runtime_cache_identity(patch_hashes):
    hashes=list(patch_hashes)
    if len(hashes)!=11 or any(not isinstance(d,str)or (re.fullmatch('[0-9a-f]{64}',d)is None or d=='0'*64) for d in hashes):
        raise ValueError('Runtime cache requires exactly eleven ordered full patch hashes')
    combined=hashlib.sha256(('\n'.join(hashes)+'\n').encode('ascii')).hexdigest()
    return {'runtime_pin':RUNTIME_PIN,'algorithm':'sha256-newline-terminated-ordered-eleven-full-patch-hashes',
      'ordered_patch_sha256':hashes,'combined_patch_sha256':combined,'directory_key':RUNTIME_PIN[:12]+'-'+combined[:16]}

def check_cache_marker_identity(marker,identity):
    if marker.get('runtime_cache_identity')!=identity:
        raise RuntimeError('Existing compact runtime cache identity differs from its full ordered patch receipt; preserved without reset.')

def validate_faithful_hook_boundary_patch(path):
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=FAITHFUL_HOOK_BOUNDARY_PATCH_SHA256 or names!=['runner/src/snes/interp_bridge.c']:
        raise RuntimeError('Faithful hook-boundary patch identity/single-file scope changed; preserve build.')
    return names

def check_faithful_hook_boundary_marker(marker,digest):
    if marker.get('faithful_hook_boundary_patch_sha256')!=digest:
        raise RuntimeError('Existing runtime hook-boundary patch identity missing/stale; preserve cache.')


def validate_reviewed_roots_patch(path):
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=REVIEWED_ROOTS_PATCH_SHA256 or set(names)!=set(REVIEWED_ROOTS_PATCH_NAMES) or len(names)!=len(REVIEWED_ROOTS_PATCH_NAMES) or not REVIEWED_ROOTS_PATCH_NAMES:
        raise RuntimeError('Reviewed analysis-root patch identity/scope changed; preserve build.')
    return names

def check_reviewed_roots_marker(marker,digest):
    if marker.get('reviewed_roots_patch_sha256')!=digest:
        raise RuntimeError('Existing runtime reviewed-root patch identity missing/stale; preserve cache.')

def validate_converged_exit_patch(path):
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=CONVERGED_EXIT_PATCH_SHA256 or set(names)!=set(CONVERGED_EXIT_PATCH_NAMES) or len(names)!=len(CONVERGED_EXIT_PATCH_NAMES):
        raise RuntimeError('Converged exit patch identity/five-file scope changed; preserve build.')
    return names

def check_converged_exit_marker(marker,digest):
    if marker.get('converged_exit_patch_sha256')!=digest:
        raise RuntimeError('Existing runtime converged exit patch identity missing/stale; preserve cache.')

def validate_accumulator_patch(path):
    # The frozen source-bound proposal is an ordinary unified one-file diff.
    content=Path(path).read_text(encoding='utf-8')
    before=re.findall(r'^--- a/(\S+)$',content,re.M)
    after=re.findall(r'^\+\+\+ b/(\S+)$',content,re.M)
    git_names=re.findall(r'^diff --git a/(\S+) b/',content,re.M)
    names=['recompiler/v2/emit_function.py']
    if sha(Path(path))!=ACCUMULATOR_PATCH_SHA256 or before!=names or after!=names or git_names not in ([],names):
        raise RuntimeError('Accumulator admission patch identity/exact one-file scope changed; preserve build.')
    return names

def check_accumulator_marker(marker,digest):
    if marker.get('runtime_accumulator_patch_sha256')!=digest or marker.get('runtime_accumulator_emitter_sha256')!=ACCUMULATOR_EMITTER_SHA256:
        raise RuntimeError('Existing accumulator marker missing/stale; preserve cache.')
    lineage=marker.get('runtime_accumulator_source_lineage',{})
    if (not isinstance(lineage,dict) or lineage.get('predecessor_sha256') not in (ACCUMULATOR_PREDECESSOR_CRLF_SHA256,ACCUMULATOR_PREDECESSOR_LF_SHA256)
            or lineage.get('normalized_predecessor_sha256')!=ACCUMULATOR_PREDECESSOR_LF_SHA256
            or lineage.get('patch_output_sha256') not in (ACCUMULATOR_OUTPUT_CRLF_SHA256,ACCUMULATOR_EMITTER_SHA256)
            or lineage.get('final_emitter_sha256')!=ACCUMULATOR_EMITTER_SHA256
            or lineage.get('normalization_performed') is not (lineage.get('patch_output_sha256')==ACCUMULATOR_OUTPUT_CRLF_SHA256)
            or lineage.get('patch_output_line_endings')!=('CRLF' if lineage.get('patch_output_sha256')==ACCUMULATOR_OUTPUT_CRLF_SHA256 else 'LF')
            or lineage.get('final_line_endings')!='LF'
            or lineage.get('line_ending_contract')!='Exact source-bound CRLF-to-LF only; no instruction/source-line changes.'):
        raise RuntimeError('Existing accumulator source-lineage marker missing/stale; preserve cache.')

def accumulator_predecessor(runtime):
    path=runtime/'recompiler/v2/emit_function.py';reject_links(path)
    raw=path.read_bytes();before=hashlib.sha256(raw).hexdigest()
    normalized=hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
    if before not in (ACCUMULATOR_PREDECESSOR_CRLF_SHA256,ACCUMULATOR_PREDECESSOR_LF_SHA256) or normalized!=ACCUMULATOR_PREDECESSOR_LF_SHA256:
        raise RuntimeError('Accumulator predecessor differs from frozen ten-patch source; preserve cache.')
    return {'predecessor_sha256':before,'normalized_predecessor_sha256':normalized}

def finalize_accumulator_source(runtime,lineage):
    path=runtime/'recompiler/v2/emit_function.py';reject_links(path)
    if (not isinstance(lineage,dict) or lineage.get('predecessor_sha256') not in (ACCUMULATOR_PREDECESSOR_CRLF_SHA256,ACCUMULATOR_PREDECESSOR_LF_SHA256)
            or lineage.get('normalized_predecessor_sha256')!=ACCUMULATOR_PREDECESSOR_LF_SHA256):
        raise RuntimeError('Accumulator source predecessor proof missing/stale; no normalization performed.')
    raw=path.read_bytes();patch_output=hashlib.sha256(raw).hexdigest()
    normalized=raw.replace(b'\r\n',b'\n')
    if patch_output not in (ACCUMULATOR_OUTPUT_CRLF_SHA256,ACCUMULATOR_EMITTER_SHA256) or hashlib.sha256(normalized).hexdigest()!=ACCUMULATOR_EMITTER_SHA256:
        raise RuntimeError('Accumulator patch output differs from frozen source; no normalization performed.')
    # Git on Windows restores CRLF. Normalize only the exact independently proved
    # candidate so the actual source receipt binds the field's frozen LF bytes.
    if raw!=normalized:path.write_bytes(normalized)
    validate_accumulator_runtime(runtime)
    return {**lineage,'patch_output_sha256':patch_output,'final_emitter_sha256':sha(path),
      'normalization_performed':raw!=normalized,'patch_output_line_endings':'CRLF' if raw!=normalized else 'LF','final_line_endings':'LF',
      'line_ending_contract':'Exact source-bound CRLF-to-LF only; no instruction/source-line changes.'}

def validate_accumulator_runtime(runtime):
    if sha(runtime/'recompiler/v2/emit_function.py')!=ACCUMULATOR_EMITTER_SHA256:
        raise RuntimeError('Patched accumulator emitter differs from exact proved source; preserve cache.')



def reviewed_roots_preflight(runtime,project,identity,enabled=True):
    # Isolate target SDK imports from optional original-five-patch profile audit.
    # This executes only the strict schema/CFG reader, never the analyzer.
    path=project/REVIEWED_ROOTS_INPUT;reject_links(path)
    source_digest=sha(path)
    if not enabled:
        return {'enabled':False,'authored_input':REVIEWED_ROOTS_INPUT,'source_sha256':source_digest,
          'diagnostic_optout':'--no-reviewed-roots','admission_is_execution_qualification':False}
    script="""import json,sys,pathlib
sys.dont_write_bytecode=True
runtime=pathlib.Path(sys.argv[1]);project=pathlib.Path(sys.argv[2])
sys.path[:0]=[str(runtime/'recompiler'),str(runtime/'tools')]
from v2.reviewed_roots import load_reviewed_roots
from v2_analyze import _load_cfgs
value=load_reviewed_roots(project/'recomp/reviewed-roots.json',cfg_dir=project/'recomp',parsed=_load_cfgs(project/'recomp'),expected_rom=sys.argv[3],expected_module='main',expected_mapper=sys.argv[4],rom_size=int(sys.argv[5]))
print(json.dumps(value.metadata(),sort_keys=True))
"""
    env={k:v for k,v in os.environ.items()if not k.startswith('SNESRECOMP_')}
    env['PYTHONDONTWRITEBYTECODE']='1'
    result=subprocess.run([sys.executable,'-B','-c',script,str(runtime),str(project),identity['expected_sha256'],identity['mapping'],identity['rom_size']],capture_output=True,text=True,env=env)
    if result.returncode:raise ValueError('Target reviewed-root preflight refused: '+result.stderr.strip())
    metadata=json.loads(result.stdout)
    if metadata.get('source_sha256')!=source_digest or sha(path)!=source_digest:
        raise ValueError('Reviewed-root input identity changed during preflight; preserve build.')
    metadata['path']=REVIEWED_ROOTS_INPUT
    return {'enabled':True,'default':True,'authored_input':REVIEWED_ROOTS_INPUT,
      'source_sha256':source_digest,'metadata':metadata,
      'generic_loader_sha256':sha(runtime/'recompiler/v2/reviewed_roots.py'),
      'cfg_loader_sha256':sha(runtime/'tools/v2_analyze.py'),
      'wrapper_optout':'--no-reviewed-roots','generator_option':'--reviewed-root-manifest',
      'local_profile_dependency':False,'admission_is_execution_qualification':False}

def source_runtime_preflight(runtime,preflight):
    if preflight is None:
        if runtime:raise ValueError('--profile-runtime-dir requires --profile-manifest')
        return None
    if runtime is None:raise ValueError('Profiles require explicit original --profile-runtime-dir; target generator is a separate identity')
    runtime=Path(runtime).absolute();reject_links(runtime);runtime=runtime.resolve(strict=True)
    marker=profile_file(runtime.parent/(runtime.name+'-patch-receipt.json'),4*1024*1024)
    receipt=json.loads(marker.read_bytes())
    expected={'runtime_pin':RUNTIME_PIN,'patch_sha256':FOUNDATION_PATCH_SHA256,
      'host_navigation_patch_sha256':HOST_NAVIGATION_PATCH_SHA256,
      'faithful_instruction_patch_sha256':FAITHFUL_INSTRUCTION_PATCH_SHA256,
      'host_modal_audio_patch_sha256':HOST_AUDIO_PATCH_SHA256,
      'automatic_faithful_patch_sha256':AUTOMATIC_FAITHFUL_PATCH_SHA256}
    if any(receipt.get(k)!=v for k,v in expected.items())or receipt.get('prefix_patch_sha256')or receipt.get('lifecycle_patch_sha256')or 'faithful_hook_boundary_patch_sha256' in receipt or 'reviewed_roots_patch_sha256' in receipt:
        raise ValueError('Only original five-patch3909 captures are currently supported; newer source captures require explicit compatibility review')
    sources=receipt.get('patched_sources',{})
    if not isinstance(sources,dict)or not sources:raise ValueError('Original runtime source marker missing')
    if command(['git','rev-parse','HEAD'],runtime)!=RUNTIME_PIN:raise ValueError('Original runtime pin changed')
    runtime_source_accounting(runtime,sources)
    for name,digest in sources.items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise ValueError('Original runtime marker path escapes source')
        path=profile_file(runtime/name)
        if sha(path)!=digest:raise ValueError('Original runtime patched source changed: '+name)
        preflight['protected'][str(path)]=digest
    preflight['protected'][str(marker)]=sha(marker);preflight['source_runtime']=runtime
    return runtime

def generation_commands(runtime,project,rom,identity,profiles=(),prefixes=True,reviewed=True,certify=True):
    if prefixes:
        emit=[sys.executable,runtime/'tools/v2_emit.py','--rom',rom,'--cfg-dir',project/'recomp',
          '--out-dir',project/'src/gen','--analysis-backend','native','--cfg-roots','--no-host-root-scan','--faithful-prefixes']
        sync=[sys.executable,runtime/'tools/v2_sync_funcs_h.py','--cfg-dir',project/'recomp','--out',project/'recomp/funcs.h']
    else:
        emit=[sys.executable,runtime/'snesrecomp_cli.py','generate','--rom',rom,'--cfg-dir','recomp',
          '--out-dir','src/gen','--funcs-h','recomp/funcs.h','--project-root',project,
          '--expected-crc32',identity['expected_crc32'],'--expected-sha256',identity['expected_sha256'],'--cfg-roots','--no-host-root-scan']
        sync=None
    if reviewed:emit+=['--reviewed-root-manifest',project/REVIEWED_ROOTS_INPUT]
    if certify:emit+=['--certify-converged-exits']
    for profile in profiles:emit+=['--profile-manifest',profile]
    return [emit,sync]if sync else[emit]

def admit_manifest(manifest,prefixes=False,force_lle=()):
    if manifest.get('format_version')!=3 or not isinstance(manifest.get('nodes'),dict)or not manifest['nodes']or not isinstance(manifest.get('roots'),list):
        raise RuntimeError('Unrecognized automatic generation manifest; preserve build.')
    dispositions={};targets=set();forced=set(force_lle)
    forced|={pc^0x800000 for pc in forced if pc>>16<0x40 and pc&0xffff>=0x8000}
    for node in manifest['nodes'].values():
        key=node.get('key',{});pc=key.get('pc24');disposition=node.get('disposition')
        if type(pc)is not int or not 0<=pc<=0xffffff or type(key.get('m'))is not int or key['m']not in(0,1)or type(key.get('x'))is not int or key['x']not in(0,1)or disposition not in('aot_eligible','lle_only','aot_prefix'):
            raise RuntimeError('Unrecognized automatic node context; preserve build.')
        if disposition=='aot_prefix':
            reasons=set(node.get('reasons',[]));base={'unproven_callee_exit','truncated_call_continuation'}
            calls={r for r in reasons if re.fullmatch(r'unproven_call_at_[0-9A-F]{6}_to_[0-9A-F]{6}_m[01]x[01]',r)}
            if not prefixes or pc in forced or pc>>16 in(0x7e,0x7f)or not calls or not base<=reasons or reasons!=base|calls:
                raise RuntimeError('Unproved/forced prefix disposition refused; preserve build.')
        elif disposition=='aot_eligible'and pc in forced:raise RuntimeError('Forced-LLE context emitted as full native; preserve build.')
        dispositions[disposition]=dispositions.get(disposition,0)+1;targets.add(pc)
    return dispositions,targets

def diagnostic_dispatch_targets(path,expected_sha256):
    reject_links(path)
    if sha(path)!=expected_sha256:raise RuntimeError('Diagnostic dispatch source differs from generation cache; preserve build.')
    text=path.read_text(encoding='utf-8')
    tables=re.findall(r'const DispatchEntry g_dispatch_table\[\] = \{\s*\n(.*?)\n\};',text,re.S)
    if len(tables)!=1:raise RuntimeError('Unrecognized actual generated dispatch table; refuse incomplete original-byte oracle.')
    targets=set();rows=0
    for line in tables[0].splitlines():
        line=re.sub(r'/\*.*?\*/','',line).strip()
        if not line:continue
        row=re.fullmatch(r'\{\s*0x([0-9A-Fa-f]{6})u,\s*\{\s*([A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*)\s*\},\s*(?:0x[0-9A-Fa-f]+|[0-9]+)u?\s*\},',line)
        if row is None:raise RuntimeError('Unparsed actual dispatch row; refuse incomplete original-byte oracle.')
        pc=int(row[1],16)
        if pc in targets:raise RuntimeError('Duplicate actual dispatch PC; preserve build.')
        targets.add(pc);rows+=1
    if not targets:raise RuntimeError('Empty actual dispatch table; refuse incomplete original-byte oracle.')
    return targets,rows

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_runtime_marker(path,receipt):
    reject_links(path)
    with path.open('x',encoding='utf-8')as marker_file:
        marker_file.write(json.dumps(receipt,indent=2)+'\n')
def command(args,cwd=None):
    result=subprocess.run([str(v) for v in args],cwd=cwd,check=True,capture_output=True,text=True)
    return result.stdout.strip()

def reject_links(path):
    for item in (path,*path.parents):
        try: stat=item.lstat()
        except FileNotFoundError: continue
        if item.is_symlink() or getattr(stat,'st_file_attributes',0)&0x400:
            raise ValueError('Linked build input/output preserved: '+str(item))

def profile_file(path, maximum=64*1024*1024):
    path=Path(path).absolute();reject_links(path);path=path.resolve(strict=True)
    if not path.is_file() or not 0<path.stat().st_size<=maximum:
        raise ValueError('Missing, empty or oversized local profile input: '+str(path))
    return path

def profile_records(path):
    # The upstream reader tolerates a torn last journal line. An explicit
    # source build requires complete observations, so refuse that case here.
    raw=path.read_bytes()
    if path.suffix=='.jsonl':
        if not raw.endswith(b'\n'):raise ValueError('Incomplete profile journal preserved: '+str(path))
        records=[json.loads(line) for line in raw.decode('utf-8').splitlines()]
    elif path.suffix=='.json':records=[json.loads(raw)]
    else:raise ValueError('Local profiles must be JSON checkpoints or JSONL journals')
    def unpack(record,depth=0):
        if depth>8:raise ValueError('Profile bundle nesting exceeds eight levels')
        if isinstance(record,dict) and record.get('schema')=='snesrecomp tier2 bundle v2':
            children=record.get('records')
            if not isinstance(children,list) or not children:raise ValueError('Empty profile bundle')
            for child in children:yield from unpack(child,depth+1)
        else:yield record
    for record in records:yield from unpack(record)

def profile_preflight(paths,receipt_path,program_path,expected,source,analyzer_path=None):
    if not paths:
        if receipt_path or program_path or analyzer_path:raise ValueError('Original profile identity inputs require --profile-manifest')
        return None
    if not receipt_path or not program_path or not analyzer_path:
        raise ValueError('Profiles require original --profile-build-receipt, --profile-program-manifest and --profile-analyzer')
    if len(paths)>32:raise ValueError('At most32 explicit profile files per build')
    profiles=[profile_file(p)for p in paths]
    if len(set(profiles))!=len(profiles):raise ValueError('Repeated local profile path')
    if sum(p.stat().st_size for p in profiles)>128*1024*1024:raise ValueError('Local profile bundle exceeds128MiB')
    receipt_path=profile_file(receipt_path,4*1024*1024);program_path=profile_file(program_path)
    receipt=json.loads(receipt_path.read_bytes());program=json.loads(program_path.read_bytes())
    if receipt.get('status')!='compiled_unqualified' or receipt.get('public_build')is not True:
        raise ValueError('Unrecognized original public build receipt; historical/experimental builds are preserved')
    if receipt.get('rom_sha256')!=expected or receipt.get('runtime_pin')!=RUNTIME_PIN:
        raise ValueError('Original profile ROM/runtime identity mismatch')
    if receipt.get('automatic_faithful_patch_sha256')!=AUTOMATIC_FAITHFUL_PATCH_SHA256:
        raise ValueError('Original profile generator patch is unrecognized; explicit compatibility review required')
    for field,digest in [('runtime_patch_sha256',FOUNDATION_PATCH_SHA256),('host_navigation_patch_sha256',HOST_NAVIGATION_PATCH_SHA256),('faithful_instruction_patch_sha256',FAITHFUL_INSTRUCTION_PATCH_SHA256),('host_modal_audio_patch_sha256',HOST_AUDIO_PATCH_SHA256)]:
        if receipt.get(field)!=digest:raise ValueError('Original build patch identity mismatch: '+field)
    if receipt.get('prefix_patch_sha256')or receipt.get('lifecycle_patch_sha256')or receipt.get('automatic_generation',{}).get('faithful_prefixes')or 'faithful_hook_boundary_patch_sha256' in receipt or 'reviewed_roots_patch_sha256' in receipt:
        raise ValueError('New prefix/lifecycle captures require explicit source-generation compatibility review; current import supports original3909 captures only')
    automatic=receipt.get('automatic_generation',{})
    relative=automatic.get('manifest','')
    if Path(relative).is_absolute()or'..'in Path(relative).parts or not relative:
        raise ValueError('Invalid original program manifest location')
    if (receipt_path.parent/relative).resolve(strict=True)!=program_path or sha(program_path)!=automatic.get('manifest_sha256'):
        raise ValueError('Original program manifest does not match its build receipt')
    if program.get('format_version')!=3 or not isinstance(program.get('nodes'),dict)or not program.get('nodes'):
        raise ValueError('Unrecognized original program manifest')
    executable=profile_file(receipt_path.parent/'build/SecretOfTheStarsSNESRecomp.exe',128*1024*1024)
    analyzer=profile_file(analyzer_path,128*1024*1024)
    if sha(executable)!=receipt.get('executable_sha256'):raise ValueError('Original executable identity mismatch')
    cache_path=profile_file(program_path.parent/'.snesrecomp-cache.json',4*1024*1024);cache=json.loads(cache_path.read_bytes())
    if cache.get('format_version')!=5 or cache.get('module')!={'id':'main','prefix':''}:
        raise ValueError('Unrecognized original generation cache/module')
    outputs=cache.get('outputs',{})
    if not isinstance(outputs,dict)or outputs.get('program_manifest.json')!=sha(program_path):raise ValueError('Original generation output identity mismatch')
    protected={str(p):sha(p)for p in [receipt_path,program_path,executable,cache_path,analyzer,*profiles]}
    for name,digest in outputs.items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise ValueError('Original generated output escapes its directory')
        output=profile_file(program_path.parent/name)
        if sha(output)!=digest:raise ValueError('Original generated output changed: '+name)
        protected[str(output)]=digest
    authored=receipt.get('authored_inputs',{})
    if not isinstance(authored,dict)or not authored:raise ValueError('Original authored provenance missing')
    # Do not replace current authority/configuration with historical contents.
    # Original captured config and current authored config must agree exactly.
    for name,digest in authored.items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise ValueError('Original authored input escapes source')
        old=profile_file(receipt_path.parent/'project'/name)
        if sha(old)!=digest:raise ValueError('Original authored input changed: '+name)
        protected[str(old)]=digest
        if name.startswith('recomp/'):
            current=profile_file(source/name)
            if sha(current)!=digest:raise ValueError('Current CFG/authority differs from captured build: '+name)
            protected[str(current)]=digest
    generator=cache.get('generator_digest');config=cache.get('config_digest')
    if any(not re.fullmatch('[0-9a-f]{64}',str(v))for v in [generator,config]):raise ValueError('Original generator/config identity missing')
    generation=hashlib.sha256((generator+config+program_path.read_text(encoding='utf-8')).encode()).hexdigest()
    module=(program_path.parent/'module_v2.c').read_text(encoding='utf-8')
    if f'g_program_module.program_digest = "{sha(program_path)}";'not in module or f'g_program_module.build_digest = "{generation}";'not in module:
        raise ValueError('Original emitted module identity mismatch')
    identity={'rom_sha256':expected,'module_id':'main','mapper':'lorom','program_digest':sha(program_path),'build_digest':sha(executable),'generation_digest':generation}
    captures={};journals={}
    for path in profiles:
        for record in profile_records(path):
            if not isinstance(record,dict)or record.get('schema')not in ['snesrecomp tier2 coverage v2','snesrecomp tier2 discovery v2']:
                raise ValueError('Only current identity-bound Tier2v2 observations are admitted')
            observed=record.get('identity',{})
            if any(observed.get(k)!=v for k,v in identity.items()):raise ValueError('Profile does not match original ROM/module/program/executable/generator')
            capture=record.get('capture_id');sequence=record.get('sequence')
            if not isinstance(capture,str)or not 1<=len(capture)<=256 or type(sequence)is not int or sequence<0:raise ValueError('Profile capture/sequence invalid')
            for key in ['overflowed_tuples','dropped_cost_samples','journal_write_failures','ram_routines_overflow']:
                value=record.get(key,0)
                if type(value)is not int or value!=0:raise ValueError('Profile capture is incomplete: '+key)
            if record['schema']=='snesrecomp tier2 discovery v2':journals[capture]=max(sequence,journals.get(capture,-1))
            elif record.get('checkpoint_complete')is True:captures[capture]=max(sequence,captures.get(capture,-1))
            else:raise ValueError('Profile checkpoint is not complete')
    if not captures or any(seq>captures.get(cap,-1)for cap,seq in journals.items()):raise ValueError('Journal extends beyond complete checkpoint')
    return {'identity':identity,'profiles':profiles,'receipt':receipt_path,'program':program_path,'analyzer':analyzer,'protected':protected,'captures':sorted(captures),'original_generator_digest':generator,'original_config_digest':config}

def profile_audit(preflight,runtime,source):
    if preflight is None:return None
    # The pinned SDK's documented generate command forwards these same repeated
    # paths to v2_emit. Audit with its exact reader first; warnings are fatal.
    sys.path.insert(0,str(runtime/'recompiler'));sys.path.insert(0,str(runtime/'tools'))
    from v2.coverage_profile import load_profiles
    from tier2_ingest import audit
    import v2_emit
    if Path(v2_emit.__file__).resolve()!=runtime/'tools/v2_emit.py':raise ValueError('Profile auditor imported another runtime')
    analyzer=preflight['analyzer']
    paths=[runtime/'recompiler/v2',runtime/'tools/v2_emit.py',runtime/'recompiler/snes65816.py',runtime/'tools/v2_analyze.py',runtime/'tools/disassembly_layout.py',runtime/'tools/sync_symbols.py',runtime/'tools/ingest_disassembly_authority.py',runtime/'recompiler-rs/src',runtime/'recompiler-rs/Cargo.toml',runtime/'recompiler-rs/Cargo.lock',analyzer]
    generator=hashlib.sha256((v2_emit._tree_digest(paths)+'\0aot_deny_gate=0').encode()).hexdigest()
    if generator!=preflight['original_generator_digest']:
        raise ValueError('Original profile generator/analyzer is not the recognized pinned build; explicit compatibility review required')
    for root in paths:
        reject_links(root)
        files=sorted(p for p in root.rglob('*')if p.is_file()and p.suffix in ['.py','.rs','.toml'])if root.is_dir()else[root]
        for file in files:reject_links(file);preflight['protected'][str(file.resolve())]=sha(file)
    for path in [runtime/'tools/sdk_generate.py',runtime/'tools/tier2_ingest.py']:
        reject_links(path);preflight['protected'][str(path.resolve())]=sha(path)
    # SDK syncs funcs.h AFTER emission; the captured build's final generated
    # header is not a generation input. Reconstruct from the receipt-matching
    # authored CFG directory, exactly as a fresh snapshot supplies it.
    parsed=[(int(path.stem[-2:],16),path,None)for path in sorted((source/'recomp').glob('bank[0-9a-fA-F][0-9a-fA-F].cfg'))]
    if v2_emit._config_digest(parsed)!=preflight['original_config_digest']:raise ValueError('Original configuration digest does not match actual CFG inputs')
    profile=load_profiles(preflight['profiles'],expected_rom=preflight['identity']['rom_sha256'],expected_module='main')
    if profile.warnings:raise ValueError('Profile audit refused: '+'; '.join(profile.warnings))
    declared=set()
    for path in(source/'recomp').glob('bank*.cfg'):
        bank=re.fullmatch('bank([0-9a-fA-F]{2})',path.stem)
        if bank:
            for line in path.read_text(encoding='utf-8').splitlines():
                m=re.match(r'\s*func\s+\S+\s+([0-9a-fA-F]+)',line)
                if m:declared.add(int(bank[1],16)<<16|int(m[1],16))
    report=audit(profile,declared,json.loads(preflight['program'].read_bytes()))
    if report['warnings']:raise ValueError('Profile ingest warnings are fatal')
    return report

def snapshot_profiles(preflight,out):
    if preflight is None:return []
    folder=out/'profile-inputs';folder.mkdir(exist_ok=False);copies=[]
    for index,path in enumerate(preflight['profiles']):
        copy=folder/(f'capture-{index:02d}'+path.suffix);shutil.copy2(path,copy)
        if sha(copy)!=preflight['protected'][str(path)]or sha(path)!=sha(copy):raise RuntimeError('Profile changed during immutable snapshot')
        copies.append(copy)
    for label,key in [('original-source-build-receipt.json','receipt'),('original-program-manifest.json','program')]:
        path=preflight[key];copy=folder/label;shutil.copy2(path,copy)
        if sha(copy)!=preflight['protected'][str(path)]:raise RuntimeError('Profile identity changed during snapshot')
    return copies

def snapshot_authored(source,project):
    reject_links(source.absolute());reject_links(project.absolute())
    path=source/'authored-files.json';reject_links(path)
    manifest=json.loads(path.read_text());actual={}
    if not isinstance(manifest,dict) or len(manifest)!=62 or REVIEWED_ROOTS_INPUT not in manifest or 'src/foundation_guide_data.h' not in manifest:
        raise ValueError('Expected62 authored inputs including reviewed roots and story-guide data; preserve source')
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
    p.add_argument('--profile-manifest',type=Path,action='append',default=[],help='Optional owned local Tier2v2 JSON checkpoint/JSONL journal (repeatable); never a release default')
    p.add_argument('--profile-build-receipt',type=Path,help='Original public source-build receipt belonging to these captures')
    p.add_argument('--profile-program-manifest',type=Path,help='Exact original generated program manifest belonging to these captures')
    p.add_argument('--profile-analyzer',type=Path,help='Exact existing original native analyzer; actual generator digest must match captured build, no cache path guessing')
    p.add_argument('--profile-runtime-dir',type=Path,help='Explicit unchanged original five-patch capture runtime, separately validated from target runtime')
    p.set_defaults(emit_proven_prefixes=True,reviewed_roots=True,certify_converged_exits=True)
    p.add_argument('--no-proven-prefixes',dest='emit_proven_prefixes',action='store_false',help='Diagnostic: disable faithful prefix analysis')
    p.add_argument('--no-converged-exits',dest='certify_converged_exits',action='store_false',help='Diagnostic: retain original exit-fact quarantine without final re-certification')
    p.add_argument('--no-reviewed-roots',dest='reviewed_roots',action='store_false',help='Diagnostic: omit reviewed authored analysis seeds; retain baseline CFG roots')
    p.add_argument('--emit-proven-prefixes',action='store_true',help='Enable the distinct proved aot_prefix disposition via pinned v2_emit --faithful-prefixes; unknown calls continue in original code')
    p.add_argument('--runtime-cache-dir',type=Path,help='Reuse an explicit pinned runtime cache; eleven full ordered patch hashes choose a new key, old keys are preserved')
    p.add_argument('--sdl3-dir',type=Path,help='Optional existing SDL3 CMake package; otherwise upstream fetches SDL3')
    p.add_argument('--cmake',default='cmake');p.add_argument('--cc',default='clang');p.add_argument('--cxx',default='clang++')
    p.add_argument('--ninja',default='ninja');p.add_argument('--jobs',type=int,default=8)
    p.add_argument('--output-dir',type=Path,help='Optional new build directory; refuses an existing path. Default: local/source-builds/timestamp.')
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
    profile_inputs=profile_preflight(args.profile_manifest,args.profile_build_receipt,args.profile_program_manifest,expected,source,args.profile_analyzer)
    capture_runtime=source_runtime_preflight(args.profile_runtime_dir,profile_inputs)
    profile_report=profile_audit(profile_inputs,capture_runtime,source)
    for tool in ('git','cargo',args.cmake,args.cc,args.cxx,args.ninja):
        if not shutil.which(tool):raise RuntimeError('Required tool is unavailable: '+tool)
    out=args.output_dir.absolute() if args.output_dir else ROOT/'local/source-builds'/time.strftime('%Y%m%d-%H%M%S')
    reject_links(out)
    out.mkdir(parents=True,exist_ok=False)
    patch=out/'runtime-foundation.patch'
    shutil.copy2(ROOT/'patches/runtime-foundation.patch',patch)
    if sha(patch)!=FOUNDATION_PATCH_SHA256:raise RuntimeError('Original foundation patch changed; preserve build.')
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
    lifecycle_patch=out/'runtime-paired-lifecycle.patch';prefix_patch=out/'runtime-proven-prefix.patch'
    shutil.copy2(ROOT/'patches/runtime-paired-lifecycle.patch',lifecycle_patch)
    shutil.copy2(ROOT/'patches/runtime-proven-prefix.patch',prefix_patch)
    lifecycle_names=re.findall(r'^diff --git a/(\S+) b/',lifecycle_patch.read_text(encoding='utf-8'),re.M)
    prefix_names=re.findall(r'^diff --git a/(\S+) b/',prefix_patch.read_text(encoding='utf-8'),re.M)
    if sha(lifecycle_patch)!=LIFECYCLE_PATCH_SHA256 or lifecycle_names!=['runner/src/cpu_state.c']:
        raise RuntimeError('Lifecycle patch identity/single-file scope changed; preserve build.')
    if sha(prefix_patch)!=PREFIX_PATCH_SHA256 or len(prefix_names)!=6 or set(prefix_names)!={'recompiler/v2/program_analysis.py','recompiler/v2/faithful_prefix.py','recompiler/v2/program_emit.py','recompiler/v2/emit_function.py','tools/v2_emit.py','runner/src/snes/interp_bridge.c'}:
        raise RuntimeError('Proved prefix patch identity/six-file scope changed; preserve build.')
    hook_boundary_patch=out/'runtime-faithful-hook-boundary.patch'
    shutil.copy2(ROOT/'patches/runtime-faithful-hook-boundary.patch',hook_boundary_patch)
    hook_boundary_names=validate_faithful_hook_boundary_patch(hook_boundary_patch)
    reviewed_patch=out/'runtime-reviewed-roots.patch'
    shutil.copy2(ROOT/'patches/runtime-reviewed-roots.patch',reviewed_patch)
    reviewed_names=validate_reviewed_roots_patch(reviewed_patch)
    converged_patch=out/'runtime-converged-exits.patch'
    shutil.copy2(ROOT/'patches/runtime-converged-exits.patch',converged_patch)
    converged_names=validate_converged_exit_patch(converged_patch)
    accumulator_patch=out/'runtime-accumulator.patch'
    shutil.copy2(ROOT/'patches/runtime-accumulator.patch',accumulator_patch)
    accumulator_names=validate_accumulator_patch(accumulator_patch)
    new_patch_names={'recompiler/v2/faithful_prefix.py','recompiler/v2/reviewed_roots.py'}
    # A new patch gets its own checkout. Previously built or intentionally
    # modified runtimes remain available rather than being reset in place.
    cache_root=args.runtime_cache_dir.absolute() if args.runtime_cache_dir else ROOT/'local/upstream'
    reject_links(cache_root)
    cache_identity=runtime_cache_identity([sha(patch),sha(host_patch),sha(faithful_patch),sha(audio_patch),sha(automatic_patch),sha(lifecycle_patch),sha(prefix_patch),sha(hook_boundary_patch),sha(reviewed_patch),sha(converged_patch),sha(accumulator_patch)])
    runtime=cache_root/cache_identity['directory_key']
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
    patch_names=sorted(set(re.findall(r'^diff --git a/(\S+) b/',patch.read_text(encoding='utf-8'),re.M))|set(host_names)|set(faithful_names)|set(audio_names)|set(automatic_names)|set(lifecycle_names)|set(prefix_names)|set(hook_boundary_names)|set(reviewed_names)|set(converged_names)|set(accumulator_names))
    if marker.exists():
        receipt=json.loads(marker.read_text(encoding='utf-8'))
        check_cache_marker_identity(receipt,cache_identity)
        check_faithful_hook_boundary_marker(receipt,sha(hook_boundary_patch))
        check_reviewed_roots_marker(receipt,sha(reviewed_patch))
        check_converged_exit_marker(receipt,sha(converged_patch))
        check_accumulator_marker(receipt,sha(accumulator_patch))
        accumulator_lineage=receipt['runtime_accumulator_source_lineage']
        if (receipt.get('runtime_pin')!=RUNTIME_PIN or receipt['patch_sha256']!=sha(patch) or receipt.get('host_navigation_patch_sha256')!=sha(host_patch)
                or receipt.get('faithful_instruction_patch_sha256')!=sha(faithful_patch)
                or receipt.get('host_modal_audio_patch_sha256')!=sha(audio_patch)
                or receipt.get('automatic_faithful_patch_sha256')!=sha(automatic_patch)
                or receipt.get('lifecycle_patch_sha256')!=sha(lifecycle_patch)
                or receipt.get('prefix_patch_sha256')!=sha(prefix_patch)
                or set(receipt.get('new_patched_sources',[]))!=new_patch_names
                or set(receipt['patched_sources'])!=set(patch_names)
                or any(sha(runtime/n)!=h for n,h in receipt['patched_sources'].items())):
            raise RuntimeError('Existing patched runtime differs from its receipt; it has been preserved.')
        runtime_source_accounting(runtime,patch_names,new_patch_names)
    else:
        if command(['git','diff','--name-only'],runtime)or command(['git','ls-files','--others','--exclude-standard'],runtime):
            raise RuntimeError('Unrecognized runtime modifications; preserved without reset.')
        command(['git','apply','--check',patch],runtime);command(['git','apply',patch],runtime)
        command(['git','apply','--check',host_patch],runtime);command(['git','apply',host_patch],runtime)
        command(['git','apply','--check',faithful_patch],runtime);command(['git','apply',faithful_patch],runtime)
        command(['git','apply','--check',audio_patch],runtime);command(['git','apply',audio_patch],runtime)
        command(['git','apply','--check',automatic_patch],runtime);command(['git','apply',automatic_patch],runtime)
        command(['git','apply','--check',lifecycle_patch],runtime);command(['git','apply',lifecycle_patch],runtime)
        command(['git','apply','--check',prefix_patch],runtime);command(['git','apply',prefix_patch],runtime)
        command(['git','apply','--check',hook_boundary_patch],runtime);command(['git','apply',hook_boundary_patch],runtime)
        command(['git','apply','--check',reviewed_patch],runtime);command(['git','apply',reviewed_patch],runtime)
        command(['git','apply','--check',converged_patch],runtime);command(['git','apply',converged_patch],runtime)
        accumulator_lineage=accumulator_predecessor(runtime)
        command(['git','apply','--check',accumulator_patch],runtime);command(['git','apply',accumulator_patch],runtime)
        accumulator_lineage=finalize_accumulator_source(runtime,accumulator_lineage)
        validate_accumulator_runtime(runtime)
        runtime_source_accounting(runtime,patch_names,new_patch_names)
        write_runtime_marker(marker,{'runtime_pin':RUNTIME_PIN,'patch_sha256':sha(patch),
          'runtime_cache_identity':cache_identity,
          'host_navigation_patch_sha256':sha(host_patch),
          'faithful_instruction_patch_sha256':sha(faithful_patch),
          'host_modal_audio_patch_sha256':sha(audio_patch),
          'automatic_faithful_patch_sha256':sha(automatic_patch),
          'lifecycle_patch_sha256':sha(lifecycle_patch),'prefix_patch_sha256':sha(prefix_patch),
          'faithful_hook_boundary_patch_sha256':sha(hook_boundary_patch),
          'reviewed_roots_patch_sha256':sha(reviewed_patch),
          'converged_exit_patch_sha256':sha(converged_patch),
          'runtime_accumulator_patch_sha256':sha(accumulator_patch),
          'runtime_accumulator_emitter_sha256':ACCUMULATOR_EMITTER_SHA256,
          'runtime_accumulator_source_lineage':accumulator_lineage,
          'new_patched_sources':sorted(new_patch_names),
          'patched_sources':{n:sha(runtime/n) for n in patch_names}})
    validate_accumulator_runtime(runtime)
    target_sources={n:sha(runtime/n)for n in patch_names};target_marker_digest=sha(marker)
    pins=dict(line.split('=',1) for line in (source/'framework_pins.txt').read_text().splitlines() if '=' in line)
    for key,name in [('rbengine','retcomm-rbengine'),('recomp-net','recomp-net')]:
        if command(['git','rev-parse','HEAD'],runtime/'lib'/name)!=pins[key]:
            raise RuntimeError('Upstream submodule pin mismatch: '+name)
    project=out/'project'
    manifest,actual=snapshot_authored(source,project)
    reviewed_report=reviewed_roots_preflight(runtime,project,identity,args.reviewed_roots)
    profile_snapshots=snapshot_profiles(profile_inputs,out)
    if profile_report is not None:
        with(out/'profile-ingest.json').open('x',encoding='utf-8')as report_file:report_file.write(json.dumps(profile_report,indent=2)+'\n')
    (project/'mods/preloaded/packages').mkdir(parents=True)
    print('Generating private local code from the verified ROM.',flush=True)
    generates=generation_commands(runtime,project,rom,identity,profile_snapshots,args.emit_proven_prefixes,args.reviewed_roots,args.certify_converged_exits)
    generation_env={k:v for k,v in os.environ.items()if not k.startswith('SNESRECOMP_')}
    generation_env['PYTHONDONTWRITEBYTECODE']='1'
    if profile_inputs is not None:generation_env['SNESRECOMP_NATIVE_ANALYZER']=str(profile_inputs['analyzer'])
    with (out/'generate.log').open('w',encoding='utf-8') as log:
        for generate in generates:
            r=subprocess.run(list(map(str,generate)),cwd=project,stdout=log,stderr=subprocess.STDOUT,env=generation_env)
            if r.returncode:raise RuntimeError('Generation failed; inspect '+str(out/'generate.log'))
    automatic_manifest_path=project/'src/gen/program_manifest.json'
    reject_links(automatic_manifest_path)
    automatic_manifest=json.loads(automatic_manifest_path.read_text(encoding='utf-8'))
    generated_cache=project/'src/gen/.snesrecomp-cache.json'
    reject_links(generated_cache);generated_metadata=json.loads(generated_cache.read_bytes())
    if generated_metadata.get('format_version')!=5 or generated_metadata.get('module')!={'id':'main','prefix':''}or generated_metadata.get('outputs',{}).get('program_manifest.json')!=sha(automatic_manifest_path):
        raise RuntimeError('Target generated cache/module identity mismatch; preserve build.')
    for name,digest in generated_metadata.get('outputs',{}).items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise RuntimeError('Target generated output escapes build; preserve build.')
        output=project/'src/gen'/name;reject_links(output)
        if sha(output)!=digest:raise RuntimeError('Target generated output/cache mismatch; preserve build.')
    from_cfg=set()
    sys.path.insert(0,str(runtime/'recompiler'))
    from v2.cfg_loader import load_bank_cfg
    for cfg_path in(project/'recomp').glob('bank*.cfg'):
        from_cfg.update(load_bank_cfg(str(cfg_path)).force_lle)
    dispositions,diagnostic_targets=admit_manifest(automatic_manifest,args.emit_proven_prefixes,from_cfg)
    manifest_targets=set(diagnostic_targets)
    dispatch_path=project/'src/gen/dispatch_v2.c'
    dispatch_targets,dispatch_rows=diagnostic_dispatch_targets(dispatch_path,generated_metadata['outputs'].get('dispatch_v2.c'))
    diagnostic_targets|=dispatch_targets
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
    if profile_inputs is not None and any(sha(Path(path))!=digest for path,digest in profile_inputs['protected'].items()):
        raise RuntimeError('Original profile/source identity changed during build; compilation retained unqualified.')
    if sha(marker)!=target_marker_digest or any(sha(runtime/n)!=digest for n,digest in target_sources.items()):
        raise RuntimeError('Target patched source identity changed during build; compilation retained unqualified.')
    runtime_source_accounting(runtime,patch_names,new_patch_names)
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
      'runtime_accumulator_patch_sha256':sha(accumulator_patch),'runtime_accumulator_emitter_sha256':ACCUMULATOR_EMITTER_SHA256,'runtime_accumulator_source_review':{'offline_unit_report_sha256':ACCUMULATOR_UNIT_SHA256,'scope':'Pinned reviewed offline instruction/source proof; public Setup does not consume private fixtures or infer actual-artifact gameplay qualification.'},
      'runtime_accumulator_source_lineage':accumulator_lineage,
      'runtime_accumulator_patch_scope':'Exact one-byte ASL/LSR/ROL/ROR accumulator admission through existing faithful bodies. MemoryRMW/INC/DEC/refusals and original buses/timing/ABI remain.',
      'version':(project/'VERSION').read_text().strip(),'rom_sha256':expected,'rom_copied':False,
      'authored_inputs':actual,'matches_authored_snapshot':actual==manifest,
      'runtime_pin':RUNTIME_PIN,'runtime_patch_sha256':sha(patch),
      'runtime_source_provenance':{'runtime_dir':str(runtime),'runtime_cache_identity':cache_identity,'marker_sha256':target_marker_digest,'patched_sources':target_sources,'new_patched_sources':sorted(new_patch_names)},
      'host_navigation_patch_sha256':sha(host_patch),
          'faithful_instruction_patch_sha256':sha(faithful_patch),
          'host_modal_audio_patch_sha256':sha(audio_patch),
      'automatic_faithful_patch_sha256':sha(automatic_patch),
      'lifecycle_patch_sha256':sha(lifecycle_patch),'prefix_patch_sha256':sha(prefix_patch),
          'faithful_hook_boundary_patch_sha256':sha(hook_boundary_patch),
          'reviewed_roots_patch_sha256':sha(reviewed_patch),
          'converged_exit_patch_sha256':sha(converged_patch),
      'reviewed_root_generation':reviewed_report,
      'converged_exit_patch_scope':'Generic post-convergence double fresh-decode certificate for previously unstable exact exit facts. Structural masks, forced-original entries and unresolved, conflicting, recursive or unstable dependencies remain authoritative. No decoded opcode emission or runtime instruction changes.',
      'reviewed_roots_patch_scope':'Strict metadata-only authored PC/M/X seeds through normal additional_roots; CFG masks and force-LLE remain authoritative. No decoded bodies, exit facts or eligibility override.',
      'lifecycle_patch_scope':'Scoped paired host return-tag lifecycle in three original dispatch branches; no guest/checkpoint layout or instruction timing change.',
      'faithful_hook_boundary_patch_scope':'Single interp_bridge pre-opcode hook boundary refusal preserves original callback producers; no generated opcode executes across that boundary and original transfer/timing remain authoritative.',
      'prefix_patch_scope':'Distinct aot_prefix disposition with exact unknown-call stop and original hard masks; never guesses callee exit modes or full-function eligibility. Generator option is explicit and recorded separately.',
      'automatic_faithful_patch_scope':'Upstream decoded instruction/IR emission with original bus transfers and internal clocks, per-instruction scheduler commits, cached effective addresses, native flag/return semantics and faithful unsupported continuation. No serialized guest fields or checkpoint/SRAM layout changes.',
      'automatic_generation':{'mode':'upstream-faithful-instruction','cfg_roots':True,'host_root_scan':False,
          'faithful_prefixes':args.emit_proven_prefixes,'prefix_wrapper_option':'--emit-proven-prefixes','prefix_generator_option':'--faithful-prefixes',
          'certify_converged_exits':args.certify_converged_exits,'converged_exit_generator_option':'--certify-converged-exits','converged_exit_diagnostic_optout':'--no-converged-exits',
          'generation_commands':[list(map(str,cmd))for cmd in generates],
          'generator_digest':generated_metadata['generator_digest'],'config_digest':generated_metadata['config_digest'],
          'cache_sha256':sha(generated_cache),'emitted_output_hashes':generated_metadata['outputs'],
          'manifest':automatic_manifest_path.relative_to(out).as_posix(),'manifest_sha256':sha(automatic_manifest_path),
          'root_mode_contexts':len(automatic_manifest['roots']),'discovered_mode_nodes':len(automatic_manifest['nodes']),
          'dispositions':dispositions,'eligibility_is_execution_coverage':False,
          'guarded_clear_constructor_default':'Existing authored guarded islands remain enabled simultaneously in normal player launches; exact automatic-native qualification separately disables both using explicit environment controls.',
          'original_byte_diagnostic':{'target_file':diagnostic_target_path.relative_to(out).as_posix(),
              'target_file_sha256':sha(diagnostic_target_path),'unique_entry_targets':len(diagnostic_targets),
              'manifest_unique_entry_targets':len(manifest_targets),'actual_dispatch_unique_entry_targets':len(dispatch_targets),
              'actual_dispatch_rows':dispatch_rows,'dispatch_source_sha256':sha(dispatch_path),'target_policy':'Union of every actual manifest entry and strictly parsed generated DispatchEntry row, including original interrupt entries and aliases.',
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
      'profile':profile.relative_to(ROOT).as_posix() if profile.is_relative_to(ROOT) else str(profile),
      'limits':'Fresh developer compilation only; gameplay qualification and owner installation remain separate.'}
    if profile_inputs is not None:
        generated_cache=project/'src/gen/.snesrecomp-cache.json'
        generated_metadata=json.loads(generated_cache.read_bytes())
        captured_roots=json.loads(profile_inputs['program'].read_bytes())['roots']
        key=lambda item:(item['pc24'],item['m'],item['x'])
        original_roots={key(item)for item in captured_roots}
        result['local_profile_generation']={'enabled':True,'default':False,'capture_identity':profile_inputs['identity'],
          'original_receipt_sha256':sha(profile_inputs['receipt']),'original_program_manifest_sha256':sha(profile_inputs['program']),
          'original_generator_digest':profile_inputs['original_generator_digest'],'original_config_digest':profile_inputs['original_config_digest'],
          'original_runtime_dir':str(profile_inputs['source_runtime']),
          'analyzer_path':str(profile_inputs['analyzer']),'analyzer_sha256':sha(profile_inputs['analyzer']),
          'capture_ids':profile_inputs['captures'],'profile_inputs':[{'original_path':str(original),'sha256':sha(copy),'snapshot':copy.relative_to(out).as_posix()}for original,copy in zip(profile_inputs['profiles'],profile_snapshots)],
          'protected_source_provenance':profile_inputs['protected'],'ingest_report':'profile-ingest.json','ingest_sha256':sha(out/'profile-ingest.json'),
          'target_generator_digest':generated_metadata['generator_digest'],'target_config_digest':generated_metadata['config_digest'],
          'generated_cache_sha256':sha(generated_cache),'emitted_outputs':{p.relative_to(out).as_posix():sha(p)for p in(project/'src/gen').rglob('*')if p.is_file()},
          'new_observed_root_contexts':[r for r in automatic_manifest['roots']if key(r)not in original_roots],
          'admission_is_execution_qualification':False,'historical_or_legacy_import':False,
          'limits':'Optional exact original-build local observations seed normal pinned analysis. CFG authority/force-LLE remain authoritative; observations and compiled source are not gameplay or release qualification. No captures are bundled into public source.'}
    with(out/'source-build-receipt.json').open('x',encoding='utf-8')as receipt_file:receipt_file.write(json.dumps(result,indent=2)+'\n')
    print('Built: '+str(binary));print('Fresh profile: '+str(profile))
    print('Run from the fresh profile: SecretOfTheStarsSNESRecomp.exe --no-launcher --rom "<your original ROM path>"')

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,OSError,KeyError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
