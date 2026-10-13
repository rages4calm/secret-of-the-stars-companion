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
CONTINUATION_BINDING=ROOT/'patches/runtime-native-continuations.json'
NATIVE_CONTINUATION_PATCH_SHA256='0644e52f0c41520fb582270f38f06871f6bc9a002bf12765b4063561546c42db'
RMW_BINDING=ROOT/'patches/runtime-memory-rmw.json'
MEMORY_RMW_PATCH_SHA256='bc942791aabf6920b40bf942d874e0f1d4461eb04867acf3266a285412042b32'
MEMORY_BITS_BINDING=ROOT/'patches/runtime-memory-bits.json'
MEMORY_BITS_PATCH_SHA256='bd89ced03845337ff1a15889b74d33d2dfea0c92e08eaa0e61c08cdfd25b6d17'
NATIVE_REGIONS_BINDING=ROOT/'patches/runtime-native-regions.json'
NATIVE_REGIONS_PATCH_SHA256='a156a53a238d18d75841561122a399618d1b1130e692728c2aede630395ba053'

def continuation_binding():
    value=json.loads(CONTINUATION_BINDING.read_bytes())
    if value.get('patch_sha256')!=NATIVE_CONTINUATION_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=12:
        raise RuntimeError('Native continuation twelve-file source binding missing/stale.')
    return value

def validate_continuation_patch(path):
    binding=continuation_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=12 or set(names)!=set(binding['files']):
        raise RuntimeError('Native continuation patch identity/scope changed; preserve build.')
    return names

def validate_continuation_runtime(runtime,normalize=False):
    for name,record in continuation_binding()['files'].items():
        path=runtime/name;reject_links(path);raw=path.read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()!=record['normalized_final_sha256']:
            raise RuntimeError('Native continuation source differs: '+name)
        if normalize and sha(path)!=record['final_sha256']:
            # Git may restore platform line endings. Restore only the exact
            # source-bound representation; content must already match above.
            normalized=raw.replace(b'\r\n',b'\n')
            options=(normalized,normalized.replace(b'\n',b'\r\n'))
            exact=next((item for item in options if hashlib.sha256(item).hexdigest()==record['final_sha256']),None)
            if exact is None:raise RuntimeError('Unrecognized source line-ending contract: '+name)
            path.write_bytes(exact)
        if sha(path)!=record['final_sha256']:
            raise RuntimeError('Native continuation exact source identity differs: '+name)

def rmw_binding():
    value=json.loads(RMW_BINDING.read_bytes())
    if value.get('patch_sha256')!=MEMORY_RMW_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=5:
        raise RuntimeError('Memory RMW 5-file source binding missing/stale.')
    return value

def validate_rmw_patch(path):
    binding=rmw_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=5 or set(names)!=set(binding['files']):
        raise RuntimeError('Memory RMW patch identity/scope changed; preserve build.')
    return names

def memory_bits_binding():
    value=json.loads(MEMORY_BITS_BINDING.read_bytes())
    if value.get('patch_sha256')!=MEMORY_BITS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=3:
        raise RuntimeError('Memory bits 3-file source binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Memory bits predecessor lineage differs: '+name)
    return value

def validate_memory_bits_patch(path):
    binding=memory_bits_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=3 or set(names)!=set(binding['files']):
        raise RuntimeError('Memory bits patch identity/scope changed; preserve build.')
    return names

LEAF_REGIONS_BINDING=ROOT/'patches/runtime-native-leaf-regions.json'
LEAF_REGIONS_PATCH_SHA256='a7a6d68e3e94edd085a254a3c1ec242670289ba1b6cf6051e2d207dae4522b95'
HOOK_HANDOFF_BINDING=ROOT/'patches/runtime-native-hook-handoff.json'
HOOK_HANDOFF_PATCH_SHA256='afe4e1ab4476432f1bcb48ab1fc6e5d35f90b357c21996518d358e2e5bf0ac03'
STACK_PRIMITIVES_BINDING=ROOT/'patches/runtime-native-stack-primitives.json'
STACK_PRIMITIVES_PATCH_SHA256='a4b0541252fa1cc9c87047314b4223aaeb4d2c716a9aa347db33d2a041f1abbd'
RETURN_STEPS_BINDING=ROOT/'patches/runtime-native-return-steps.json'
RETURN_STEPS_PATCH_SHA256='ba71b546cec6c450942870c65ee303b9b6b2cd66eeb60a9e306afa1bbfc77795'
PREFIX_INSTRUCTIONS_BINDING=ROOT/'patches/runtime-native-prefix-instructions.json'
PREFIX_INSTRUCTIONS_PATCH_SHA256='be14f3e131a93189893c5c24c2eed7b298e1aa0d7297af8ddd75aa394fbb727f'

STACK_CONTROLS_BINDING=ROOT/'patches/runtime-native-stack-controls.json'
STACK_CONTROLS_PATCH_SHA256='9743afddec386e3ac989098c51ef32c0a236a63499bb9292e5b26bc8437c2398'


SELECTED_TASK_BINDING=ROOT/'patches/runtime-selected-task-resume.json'
SELECTED_TASK_PATCH_SHA256='d42e308324f17563412fdee97a21de1904ee38a348ff20cb86eabf39bbb29c60'
SELECTED_TASK_BINDING_SHA256='bee507075d73c569101e91685691f383d69d8c54d4de7a697583fc1e20fb3240'
SELECTED_TASK_SOURCE_NAMES=('recompiler/v2/cfg_loader.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py', 'runner/src/cpu_state.c', 'runner/src/cpu_state.h', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h', 'runner/src/task_resume_contract.h', 'runner/src/task_resume_contract.inc')





# Ordered authored runtime deltas retain exact predecessor and final identities.
# Generated game files are not inputs and compilation never grants qualification.
RUNTIME_EXTENSION_SPECS = ({'name': 'runtime-original-call-retention', 'patch_sha256': 'f89a5e4b7fc3716f4a440353cc1392a3fcb4ee003fc671f033e3ed30fd09b985', 'binding_sha256': '74fd49aad510fbc0f4d3a3e97b7bef768ad56c3913ab171d9c731a18f8c7236f', 'files': ['recompiler/v2/codegen.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_call_prefix.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_original_calls.py', 'recompiler/v2/task_resume.py', 'runner/src/common_rtl.c', 'runner/src/cpu_state.c', 'runner/src/cpu_state.h', 'runner/src/desktop/host_main.c', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/interp816.c', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/snes.c', 'runner/src/task_original_call_contract.h', 'runner/src/task_original_call_contract.inc'], 'new_files': ['recompiler/v2/task_original_calls.py', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/task_original_call_contract.h', 'runner/src/task_original_call_contract.inc'], 'unpatched_predecessors': {'recompiler/v2/codegen.py': '808a83ac6db1dbac912de8d30ca8ef10028e8b65978c153cbc8391a5e22cbbf0', 'recompiler/v2/emit_function.py': '42a3bb0ddf73a3e5db7757a6bd8919a8d36558a249f18dcc202c5083ee4db1a2', 'recompiler/v2/native_call_prefix.py': '9e7488609a26bff99600e21dbcc65d093d3ace1b1f4f43c26ea87fe08eef08dc', 'recompiler/v2/native_regions.py': 'b2dcb0b24b013f2543e91e2a6d11475a474b71d4012cc42214e5ba2294b42268', 'recompiler/v2/program_emit.py': 'f7799a49fd4d331d74ecf5ef2ed347eb4866229406c7a5614f821dd76f624f6a', 'recompiler/v2/task_resume.py': '891b92e35838dcb348cef1ca43635053f15c26dc294d5e3a371bef99cc2b3e30', 'runner/src/common_rtl.c': 'e2146f5de96ff2a236de50f275525e10a7ad038f06448c9c06c38e9d3179ddb1', 'runner/src/cpu_state.c': '0a4b53ca254dd66aa81d0d232fc7ad3d29fb2a8739be16820a83c4129c4de7f7', 'runner/src/cpu_state.h': 'f045d10a22df9d2df8bc898da16d5032166e59744ed49c72aaa5286336d409c4', 'runner/src/desktop/host_main.c': '06adadb980c4eccb4393a3f2abdd258503b1647f66b795bb7bd7a32d517a52f4', 'runner/src/snes/bridge_task_call.inc': 'f470728c8b39ff9767f01da473de9c9f173d473635c466bd9b324c59ca93fe74', 'runner/src/snes/bridge_task_helpers.inc': '86569e088973f03df80407ee37f687f6bc1b74d094b2054d20c2203561c46583', 'runner/src/snes/interp816.c': '658acf8afdac221e02b4eb7672512403c2a5c15f0d27c4822f2411d4451ab665', 'runner/src/snes/interp_bridge.c': '411b6e034dd60cca43010cd999345c6fb45f6572404db4c5937e550337468224', 'runner/src/snes/snes.c': '08dc7f6ab2d38a027bed9251ec1de5f03f9f23866eb2f2f0167b309e6da33245'}, 'metadata': {'cache_format': 22, 'normal_metadata': 9, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-long-jump-stack-indirect-y', 'patch_sha256': 'ec77e0a198c56713763920c1346aa80e7342d7c54d8c055633175781629afeb1', 'binding_sha256': '03c0e6a3c5a28c5aa84d68218ef5e82a6e875c284d6fa66e8ba96faf88dee885', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '4d1e7fcea904e6c48137873ff335600064e51b2a7ec4b434bfd49c4c49980c76', 'recompiler/v2/native_regions.py': 'd7dc1fad195254c9e4477c0378fc00205d61c454334d711490cf859fa4a31b61', 'recompiler/v2/program_emit.py': '2779e661158a722dade40df67883d8dd852ad229ea23cad19beb412fa5357526', 'runner/src/cpu_state.h': 'a9c719580ebaa01f458d383512a89789d0f733abd54888db76125e7d75e71afd', 'runner/src/snes/interp_bridge.c': 'b5979f45857400eaa8127b00c545e5f62b21bed100b02cb87f768d690c1ab478'}, 'metadata': {'cache_format': 23, 'normal_metadata': 10, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-indirect-control', 'patch_sha256': '2b723cefdf7faa6dccad43702281a0fce561277a89900b69b4e8a52968bf5474', 'binding_sha256': '7a07b9f335179b41cb0806dbfe375dc8381646fd3612aca3d03dfe1cf216f2f1', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_indirect_control.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_indirect_control.py'], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '4d678e1baef47e68d0e8db122a7c52b7908e0a32885a77b68748117b64b7231d', 'recompiler/v2/program_emit.py': 'a94ac9107d4302480544ebf921269d01bd792de32e71d059db39a50840a952a7', 'runner/src/cpu_state.h': 'c8b7bc9e132b83e3e2e56b9b6a42d24f8ad7141c4e4301b16291ec6e379e092b', 'runner/src/snes/interp_bridge.c': '1f5345cfdabd7e90040351dc118ea1ffc2e9fa9518baf076632ff40fe1c6fee0'}, 'metadata': {'cache_format': 24, 'normal_metadata': 11, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-task-original-prefix', 'patch_sha256': 'b992641a8e331dab5f1c2edd7e5c7349163e150ba537179793cbd47c53a56683', 'binding_sha256': 'b3b92cdd08008832fff1caac30f586626e0dcc3e60534831ed6c3417dedac8bc', 'files': ['recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py', 'runner/src/cpu_state.h', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'recompiler/v2/program_emit.py': '55f4d98b9e9f84d0841f7aa57f71424dc75a91e793fbabc9422e1bc6915a87f8', 'recompiler/v2/task_resume.py': '07e5996369b4705e3dff34456730b953245d840f9cb1a99b850710b535a5c554', 'runner/src/cpu_state.h': 'cc3028ac50395b4da840d2f6bc3f43a6da841b2381cc3f84ebf4583a746fe59a', 'runner/src/snes/bridge_task_call.inc': '23248f7c92e1d025f3c2121732d8a9d9657d4848efa053d747d12b3b4e520b41', 'runner/src/snes/bridge_task_original_runtime.inc': 'fc2c3cd95cbda3ef4a6c9b7052378ada8c0e10445c35c79ac44a6afb8d311ed6', 'runner/src/snes/interp_bridge.c': '905b2e047797c39ef9407e6ed2f024481e1775ab71705842e748477e180380e0'}, 'metadata': {'cache_format': 25, 'normal_metadata': 11, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-interrupt-return', 'patch_sha256': '75926f688cc3dbd6dccc4ce3446976b0f6307f93c212533dae5bb25248d071a1', 'binding_sha256': '3ba0770eb6d5f13ae1a794bb7365ebe1f06ddb117ff2172786ee40b56efe3f10', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_interrupt_return.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_interrupt_return.py'], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '02cf21790a4327524359b3ca504381f4a60cb76277ab816aaa0d941a16dcdb4b', 'recompiler/v2/program_emit.py': 'fe4ed2d530e308b814443c7bfa4419c7eeda2e01a6d0c3a0bd769fe7a081c265', 'runner/src/snes/interp_bridge.c': '0f0518b919603954cd89325a6e4cb5f9c5f12f9b3ded1bb860424bd1a7fc03b2'}, 'metadata': {'cache_format': 26, 'normal_metadata': 12, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-carry-emulation-exchange', 'patch_sha256': '629f510383cd70654d8a43fefe5eec30918a42ee8c7bdbb5343280ebe48a8075', 'binding_sha256': 'a7b94a2a879b6c19e432fc4b896e6159c286f47ee0541a71baf623422175e7b5', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_exchange.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/native_exchange.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 27, 'normal_metadata': 13, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-blockmove', 'patch_sha256': '0a1b15776666a61e2bbedd653fa658298314a2004869963d718061605d092570', 'binding_sha256': '6711b5cfcfdff92c5603784123fcaf16e48f47c7d34cf52f625aea1626567512', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_blockmove.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_blockmove.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 28, 'normal_metadata': 14, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-reset-bootstrap-emulation', 'patch_sha256': '6edc8dfe64015c9c896382627708cfb41db0b6ae5b8e3a6e55b62a1080dc1df9', 'binding_sha256': 'f428d6b7e01959c1de0a9b6ad1168754023b15659830b3d48d7dcacff9a6f199', 'files': ['recompiler/v2/native_bootstrap.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_bootstrap.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 29, 'normal_metadata': 15, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-mode-successors', 'patch_sha256': 'b665988c08e87e23bb07da2cf9e7b0d40fcb61a10372fa1d933d2c0aaf851e08', 'binding_sha256': 'cb526acc78c3c26fad6e24fed58c6b6771325dfa1478e693dbb1d7372cb0bfc7', 'files': ['recompiler/v2/decoder.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_mode_successors.py', 'recompiler/v2/program_emit.py', 'tools/v2_emit.py'], 'new_files': ['recompiler/v2/native_mode_successors.py'], 'unpatched_predecessors': {'recompiler/v2/decoder.py': '155edb7da1b0398109d0b00d9ad472f5d9d46e89a79d7f2a713d290db7af708e', 'recompiler/v2/emit_bank.py': '003fbdba518e04145fbcde95e05694173915e602ed85df853dc3feb5ff670fe0', 'tools/v2_emit.py': 'fb7b1a3155618da2fa2f71a6a578fbbb61ae758b88339cde84bafb4d3f354866'}, 'metadata': {'cache_format': 30, 'normal_metadata': 16, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-source-suspend', 'patch_sha256': 'd833d7dc406ea9d4eb7c93c85af212522782d800ca2f1991ab1aa21e387eb1f4', 'binding_sha256': '7c547ed65e281fae59b304f5f93fed78259f80c5b8630139f2f28993c708b9b3', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/source_redirect.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/task_suspend.py', 'runner/src/common_rtl.c', 'runner/src/cpu_state.c', 'runner/src/cpu_state.h', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/bridge_task_suspend.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/snes.c', 'runner/src/task_resume_contract.inc', 'runner/src/task_suspend_lineage.h', 'runner/src/task_suspend_lineage.inc'], 'new_files': ['recompiler/v2/task_suspend.py', 'runner/src/snes/bridge_task_suspend.inc', 'runner/src/task_suspend_lineage.h', 'runner/src/task_suspend_lineage.inc'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 31, 'normal_metadata': 16, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-architecture-eligibility', 'patch_sha256': '49127b9014e96faa4d2cc50d1515bc29d4f5d6d78c81e48201ff89caedfaa368', 'binding_sha256': '216ba88dcc9d792fb10c050e66f3090d0bff0249187d8a1f6d4254b9055db4d8', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_ff20_sources.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_ff20_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 32, 'normal_metadata': 17, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-turbo-cadence', 'patch_sha256': 'cfb88676320da4f5ae5f1144e5814a307ecc70c689ed48ba13dc6d6964859dc7', 'binding_sha256': '7495d2b5cfb54642b6d53c38e8d6de2d24f440b5f3abaa0b7d5a216caafcd817', 'files': ['runner/src/common_rtl.c', 'runner/src/common_rtl.h', 'runner/src/desktop/host_main.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/common_rtl.h': 'f6efb33932de8c1adf8d23b1313d3d3af79fc17f30d2e634240e05750d0d6ad8'}, 'metadata': {'cache_format': 32, 'normal_metadata': 17, 'task_metadata': 6, 'redirect_metadata': 1}})
RUNTIME_GENERATION_FORMATS = {'cache':32,'normal':17,'task':6,'redirect':1}
TASK_GENERATED_ROW_COUNT = 235

def runtime_extension_bindings():
    predecessors={}
    for fn in (continuation_binding,rmw_binding,memory_bits_binding,native_regions_binding,leaf_regions_binding,hook_handoff_binding,stack_primitives_binding,return_steps_binding,prefix_instructions_binding,stack_controls_binding,selected_task_binding,source_redirect_binding,indirect_y_binding,task_callee_binding,stack_direct_binding,host_proof_idle_binding,redirect_observer_idle_binding,selected_case_binding,direct_call_binding):
        predecessors.update(fn()['files'])
    prior_patch=DIRECT_CALL_PATCH_SHA256;prior_binding=sha(DIRECT_CALL_BINDING);result=[]
    for spec in RUNTIME_EXTENSION_SPECS:
        binding=ROOT/'patches'/(spec['name']+'.json');reject_links(binding)
        if sha(binding)!=spec['binding_sha256']:raise RuntimeError('Runtime extension binding differs: '+spec['name'])
        value=json.loads(binding.read_bytes())
        if value.get('patch_sha256')!=spec['patch_sha256']or value.get('predecessor_patch_sha256')!=prior_patch or value.get('predecessor_binding_sha256')!=prior_binding or set(value.get('files',{}))!=set(spec['files']):raise RuntimeError('Runtime extension sequential identity differs: '+spec['name'])
        if {k:value.get(k)for k in spec['metadata']}!=spec['metadata']:raise RuntimeError('Runtime extension formats differ.')
        if value.get('artifact_qualification')is not False or value.get('native_AOT_complete')is not False:raise RuntimeError('Source extension cannot grant execution qualification.')
        for name,record in value['files'].items():
            expected=predecessors[name]['final_sha256']if name in predecessors else spec['unpatched_predecessors'].get(name)
            if record.get('predecessor_sha256')!=expected or(expected is None and name not in spec['new_files']):raise RuntimeError('Runtime extension source predecessor differs: '+name)
            if Path(name).is_absolute()or'..'in Path(name).parts:raise RuntimeError('Runtime extension source escapes runtime.')
            if any(re.fullmatch('[0-9a-f]{64}',record.get(k,''))is None for k in('final_sha256','normalized_final_sha256')):raise RuntimeError('Runtime extension final hash missing: '+name)
        predecessors.update(value['files']);result.append(value)
        prior_patch=value['patch_sha256'];prior_binding=sha(binding)
    return result

def runtime_extension_records():
    return [{'name':s['name'],'patch_sha256':s['patch_sha256'],'source_binding_sha256':s['binding_sha256']}for s in RUNTIME_EXTENSION_SPECS]

def prepare_runtime_extension_patches(out):
    result=[]
    for spec,value in zip(RUNTIME_EXTENSION_SPECS,runtime_extension_bindings()):
        path=out/(spec['name']+'.patch');shutil.copy2(ROOT/'patches'/path.name,path)
        text=path.read_text(encoding='utf8')
        names=re.findall(r'^diff --git a/(\S+) b/\S+$',text,re.M)
        before=re.findall(r'^--- (?:a/(\S+)|(/dev/null))$',text,re.M)
        after=re.findall(r'^\+\+\+ b/(\S+)$',text,re.M)
        if sha(path)!=spec['patch_sha256']or len(names)!=len(spec['files'])or set(names)!=set(spec['files'])or len(before)!=len(after)or after!=names:raise RuntimeError('Runtime extension patch paths differ.')
        for (old,null),new in zip(before,after):
            if(old!=new or null)if value['files'][new]['predecessor_sha256']is not None else(null!='/dev/null'or old):raise RuntimeError('Runtime extension patch predecessor path differs.')
        result.append(path)
    return result

def apply_runtime_extensions(runtime,patches):
    for patch,value in zip(patches,runtime_extension_bindings()):
        for name,record in value['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256']is None:
                if path.exists():raise RuntimeError('New extension source already exists; preserve cache: '+name)
            else:
                if not path.is_file()or sha(path)!=record['predecessor_sha256']:raise RuntimeError('Extension apply predecessor differs; preserve cache: '+name)
                raw=path.read_bytes()
                if b'\r\n'in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',patch],runtime);command(['git','apply',patch],runtime)
        for name,record in value['files'].items():
            path=runtime/name;raw=path.read_bytes();normalized=raw.replace(b'\r\n',b'\n')
            if hashlib.sha256(normalized).hexdigest()!=record['normalized_final_sha256']:raise RuntimeError('Extension apply source content differs; preserve cache: '+name)
            if sha(path)!=record['final_sha256']:
                exact=next((v for v in(normalized,normalized.replace(b'\n',b'\r\n'))if hashlib.sha256(v).hexdigest()==record['final_sha256']),None)
                if exact is None:raise RuntimeError('Extension line-ending identity differs; preserve cache: '+name)
                path.write_bytes(exact)
            if sha(path)!=record['final_sha256']:raise RuntimeError('Extension apply final source differs; preserve cache: '+name)

DIRECT_CALL_BINDING=ROOT/'patches/runtime-direct-call-prefix.json'
DIRECT_CALL_PATCH_SHA256='772c7d58026c57a5b8c7efff3312ab54e3ccfa81bf2c8ddec7b842774d97c991'
DIRECT_CALL_BINDING_SHA256='c00d3caa8195abe1ac362133a92452089c8d72bf0642320bf314a5456636b56e'
DIRECT_CALL_SOURCE_NAMES=('recompiler/v2/native_call_prefix.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/program_emit.py', 'tools/v2_emit.py', 'runner/src/snes/interp_bridge.c', 'runner/src/cpu_state.h')
DIRECT_CALL_UNPATCHED_PREDECESSORS={'recompiler/v2/emit_bank.py': '68511ffd064c2546365d31c0c82a1567e5729f124c20c9ab6a0acbf160cc5585', 'tools/v2_emit.py': 'bf7b1d6b3fab9a223e58a5597902c813c4e0315be934ab33e9febe7ca8aea380'}

def direct_call_binding():
    if sha(DIRECT_CALL_BINDING)!=DIRECT_CALL_BINDING_SHA256:raise RuntimeError('Direct call binding identity changed.')
    value=json.loads(DIRECT_CALL_BINDING.read_bytes())
    if value.get('patch_sha256')!=DIRECT_CALL_PATCH_SHA256 or set(value.get('files',{}))!=set(DIRECT_CALL_SOURCE_NAMES) or value.get('predecessor_patch_sha256')!=SELECTED_CASE_PATCH_SHA256 or value.get('predecessor_binding_sha256')!=sha(SELECTED_CASE_BINDING):raise RuntimeError('Direct call seven-file sequential binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files'],**task_callee_binding()['files'],**stack_direct_binding()['files'],**host_proof_idle_binding()['files'],**redirect_observer_idle_binding()['files'],**selected_case_binding()['files']}
    for name,record in value['files'].items():
        expected=predecessors[name]['final_sha256']if name in predecessors else DIRECT_CALL_UNPATCHED_PREDECESSORS.get(name)
        if record.get('predecessor_sha256')!=expected:raise RuntimeError('Direct call predecessor differs: '+name)
        if expected is None and name!='recompiler/v2/native_call_prefix.py':raise RuntimeError('Unknown new direct call source.')
        for key in ('final_sha256','normalized_final_sha256'):
            if re.fullmatch('[0-9a-f]{64}',record.get(key,''))is None:raise RuntimeError('Direct call source hash missing.')
    return value

def validate_direct_call_patch(path):
    value=direct_call_binding();text=Path(path).read_text(encoding='utf-8')
    before=re.findall(r'^--- (?:a/(\S+)|(/dev/null))$',text,re.M);after=re.findall(r'^\+\+\+ b/(\S+)$',text,re.M)
    if sha(Path(path))!=DIRECT_CALL_PATCH_SHA256 or len(after)!=7 or set(after)!=set(value['files'])or len(before)!=len(after):raise RuntimeError('Direct call patch identity/scope differs.')
    for (old,null),new in zip(before,after):
        if (old!=new or null)if value['files'][new]['predecessor_sha256']is not None else (null!='/dev/null' or old):raise RuntimeError('Direct call patch predecessor path differs.')
    return after

def validate_reset_bootstrap_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);raw=Path(rom).read_bytes()
    metadata=directory/'native_regions.json';source=directory/'native_regions_v2.c'
    value=json.loads(metadata.read_bytes());recipe=value.get('reset_bootstrap')
    if sha(Path(rom))!=rom_sha or value.get('rom_sha256')!=rom_sha or not isinstance(recipe,dict):raise RuntimeError('Reset bootstrap source metadata/ROM missing.')
    if recipe.get('source_contract')!='declared-reset-vector-three-step-e1-bootstrap-v1' or recipe.get('ordinary_roots_added')is not False or recipe.get('source_declared_name')!='I_RESET' or recipe.get('entry')!=0x8000 or recipe.get('vector_pc')!=0xfffc or recipe.get('prefix_pc')!=0x8000 or recipe.get('successor')!=0x8004:raise RuntimeError('Reset bootstrap declared source owner differs.')
    if recipe.get('vector_bytes')!=raw[0x7ffc:0x7ffe].hex() or recipe.get('prefix_bytes')!=raw[:4].hex():raise RuntimeError('Reset bootstrap actual mapped source bytes differ.')
    rows=recipe.get('rows');code=source.read_text(encoding='utf-8')
    if not isinstance(rows,list)or len(rows)!=3 or recipe.get('exit_e')!='dynamic_live_C_after_source_REP09':raise RuntimeError('Reset bootstrap separate E1 recipe differs.')
    for row,(pc,mnemonic,length,cycles,opcode) in zip(rows,((0x8000,'SEI',1,2,0x78),(0x8001,'REP',2,3,0xc2),(0x8003,'XCE',1,2,0xfb))):
        if row.get('pc24')!=pc or row.get('e')!=1 or row.get('m')!=1 or row.get('x')!=1 or row.get('mnemonic')!=mnemonic or row.get('length')!=length or row.get('cycles')!=cycles or row.get('contract')!='source-reset-e1-bootstrap-step-v1':raise RuntimeError('Reset bootstrap typed architectural row differs.')
        data=bytes.fromhex(row['bytes'])
        if len(data)!=length or data[0]!=opcode or raw[pc-0x8000:pc-0x8000+length]!=data or mnemonic=='REP'and data[1]!=9 or not isinstance(row.get('body'),str)or row['body']not in code:raise RuntimeError('Reset bootstrap cached source row/body differs.')
    if 'cpu_source_reset_bootstrap_match'not in code or 'cpu->emulation!=1'not in code or 'cart_getRomPtr'not in code or 'cpu_source_reset_bootstrap_step'not in code:raise RuntimeError('Reset bootstrap live mode/source guard missing.')
    for path in(metadata,source):
        if cache.get('outputs',{}).get(path.name)!=sha(path):raise RuntimeError('Reset bootstrap output/cache mismatch.')
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'separate_e1_rows':3,'declared_entry':recipe['entry'],'ordinary_roots_added':False,'execution_qualified':False}

def normal_source_row_count(value):
    enabled=value.get('direct_call_prefix')
    if value.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal'] or enabled is not True and enabled is not False or value.get('direct_call_contract')!='source-direct-call-architectural-prefix-v1':raise RuntimeError('Direct call source metadata/option missing.')
    if value.get('mode_successors')is not True or value.get('mode_successor_contract')!='source-owned-live-mx-instruction-successors-v1':raise RuntimeError('Live mode successor metadata/option missing.')
    meta=value.get('architecture_source_eligibility',{})
    sources=meta.get('sources',[])
    if meta.get('contract')!='source-reviewed-independent-instruction-union-v1' or meta.get('ordinary_roots_added')is not False or meta.get('callee_exit_modes_added')is not False or meta.get('task_ownership_changed')is not False or len(sources)!=2:raise RuntimeError('Independent architecture source policy missing.')
    expected=(7,83)if enabled else(7,79)
    if any(source.get('origin')!=origin or source.get('source_rows')!=count or len(source.get('added',[]))!=count or source.get('reused')!=[] or source.get('refused')!=[] for source,origin,count in zip(sources,('reviewed_original_task_child','reviewed_original_ff20_receiving_starts'),expected)):raise RuntimeError('Independent architecture source union differs.')
    return 9615 if enabled else 9375

def validate_direct_call_outputs(directory,cache,rom_sha,rom,enabled):
    directory=Path(directory);raw=Path(rom).read_bytes()
    metadata=directory/'native_regions.json';source=directory/'native_regions_v2.c'
    value=json.loads(metadata.read_bytes());rows=value.get('regions');code=source.read_text(encoding='utf-8')
    if sha(Path(rom))!=rom_sha or value.get('rom_sha256')!=rom_sha or value.get('direct_call_prefix')is not enabled or len(rows)!=normal_source_row_count(value):raise RuntimeError('Direct call source metadata/ROM/count differs.')
    subset=[r for r in rows if r.get('contract')=='source-direct-call-architectural-prefix-v1']
    if len(subset)!=(240 if enabled else 0):raise RuntimeError('Direct call source mode row count differs.')
    if enabled and (len({r['pc24']for r in subset})!=227 or sum(r['mnemonic']=='JSR'for r in subset)!=132 or sum(r['mnemonic']=='JSL'for r in subset)!=108):raise RuntimeError('Direct call source family count differs.')
    keys=[(r['pc24'],r['m'],r['x'])for r in rows]
    if len(set(keys))!=len(keys):raise RuntimeError('Duplicate original scheduler mode row.')
    for row in subset:
        pc=row.get('pc24');body=row.get('body');mnemonic=row.get('mnemonic');length=3 if mnemonic=='JSR'else 4;frame=length-1
        if mnemonic not in('JSR','JSL')or row.get('m')not in(0,1)or row.get('x')not in(0,1)or row.get('length')!=length or row.get('cycles')!=(6 if mnemonic=='JSR'else 8)or row.get('frame_bytes')!=frame or row.get('original_scheduler_call')is not True:raise RuntimeError('Direct call typed row differs.')
        data=bytes.fromhex(row['bytes']);offset=(pc>>16)*32768+(pc&32767)
        target=int.from_bytes(data[1:],'little')if length==4 else (pc&0xff0000)|int.from_bytes(data[1:],'little')
        if len(data)!=length or data[0]!=(0x20 if length==3 else 0x22)or raw[offset:offset+length]!=data or row.get('next_pc')!=target:raise RuntimeError('Direct call bytes/source target differs.')
        if not isinstance(body,str)or body not in code or body.count('cpu_aot_get_direct_call_operands(')!=1 or body.count('cpu_source_call_native_push(')!=1 or body.count('cpu_aot_write8(')!=frame or '*next_pc=_call_target;'not in body or body.count('cpu->PB=(uint8)(_call_target>>16);')!=(1 if length==4 else 0)or any(t in body for t in('cpu_aot_begin','cpu_aot_commit','cpu_aot_read','host_return_valid','cpu_dispatch','interp_tier')):raise RuntimeError('Direct call cached operand/original byte frame body differs.')
    for path in(metadata,source):
        if cache.get('outputs',{}).get(path.name)!=sha(path):raise RuntimeError('Direct call output/cache mismatch.')
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'call_mode_rows':len(subset),'call_distinct_pcs':len({r['pc24']for r in subset}),'default_enabled':enabled,'closed_call_authority':False,'execution_qualified':False}

SELECTED_CASE_BINDING=ROOT/'patches/runtime-selected-task-cases.json'
SELECTED_CASE_PATCH_SHA256='b9212c9e0df961d1d99f344db9ad2eef7105a3b86ff2c48dced864c1836659be'
SELECTED_CASE_BINDING_SHA256='2b275779f15e85be21f1c881d04d5de0b6a1de7c41534b7cc575504ab9cd2a42'
SELECTED_CASE_SOURCE_NAMES=('recompiler/v2/cfg_loader.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/program_emit.py', 'runner/src/task_resume_contract.h', 'runner/src/task_resume_contract.inc')

def selected_case_binding():
    if sha(SELECTED_CASE_BINDING)!=SELECTED_CASE_BINDING_SHA256:raise RuntimeError('Selected task case binding identity changed.')
    value=json.loads(SELECTED_CASE_BINDING.read_bytes())
    if value.get('patch_sha256')!=SELECTED_CASE_PATCH_SHA256 or set(value.get('files',{}))!=set(SELECTED_CASE_SOURCE_NAMES):raise RuntimeError('Selected task case five-file binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files'],**task_callee_binding()['files'],**stack_direct_binding()['files'],**host_proof_idle_binding()['files'],**redirect_observer_idle_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:raise RuntimeError('Selected task case predecessor differs: '+name)
        for key in ('final_sha256','normalized_final_sha256'):
            if re.fullmatch('[0-9a-f]{64}',record.get(key,''))is None:raise RuntimeError('Selected task case source hash missing.')
    return value

def validate_selected_case_patch(path):
    value=selected_case_binding();text=Path(path).read_text(encoding='utf-8')
    before=re.findall(r'^--- a/(\S+)$',text,re.M);after=re.findall(r'^\+\+\+ b/(\S+)$',text,re.M)
    if sha(Path(path))!=SELECTED_CASE_PATCH_SHA256 or before!=after or len(before)!=5 or set(before)!=set(value['files']):raise RuntimeError('Selected task case patch identity/scope differs.')
    return before

REDIRECT_OBSERVER_IDLE_BINDING=ROOT/'patches/runtime-redirect-observer-idle.json'
REDIRECT_OBSERVER_IDLE_PATCH_SHA256='8721710970d4c0a5d21549a55519fbf66a6d8da6642125b104a27f48141d28ab'
REDIRECT_OBSERVER_IDLE_BINDING_SHA256='c89019161e29ad7f7334d35c219f8b55fdc5f191a69b5e1c50f1c8658dca6522'
REDIRECT_OBSERVER_IDLE_SOURCE_NAMES=('runner/src/snes/bridge_redirect_helpers.inc', 'recompiler/v2/program_emit.py')

def redirect_observer_idle_binding():
    if sha(REDIRECT_OBSERVER_IDLE_BINDING)!=REDIRECT_OBSERVER_IDLE_BINDING_SHA256:raise RuntimeError('Redirect observer idle binding identity changed.')
    value=json.loads(REDIRECT_OBSERVER_IDLE_BINDING.read_bytes())
    if value.get('patch_sha256')!=REDIRECT_OBSERVER_IDLE_PATCH_SHA256 or set(value.get('files',{}))!=set(REDIRECT_OBSERVER_IDLE_SOURCE_NAMES):raise RuntimeError('Redirect observer idle two-file binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files'],**task_callee_binding()['files'],**stack_direct_binding()['files'],**host_proof_idle_binding()['files']}
    records={}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']or re.fullmatch('[0-9a-f]{64}',record.get('final_sha256',''))is None:raise RuntimeError('Redirect observer idle predecessor/final lineage differs: '+name)
        records[name]={**record,'normalized_final_sha256':record['final_sha256']}
    return {**value,'files':records}

def validate_redirect_observer_idle_patch(path):
    binding=redirect_observer_idle_binding();names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=REDIRECT_OBSERVER_IDLE_PATCH_SHA256 or len(names)!=2 or set(names)!=set(binding['files']):raise RuntimeError('Redirect observer idle patch identity/scope changed.')
    return names

HOST_PROOF_IDLE_BINDING=ROOT/'patches/runtime-host-proof-idle.json'
HOST_PROOF_IDLE_PATCH_SHA256='058143dee58cbf9d7bba1856ee703a08ff3bc970248dc62b7cb9c5a2aa28429d'
HOST_PROOF_IDLE_BINDING_SHA256='900e284d5973983d3efcdaa2cef6a5e8dc97ed351ea0f439029b050c6b6284a8'
HOST_PROOF_IDLE_SOURCE_NAMES=('runner/src/snes/bridge_task_call.inc', 'recompiler/v2/program_emit.py')

def host_proof_idle_binding():
    if sha(HOST_PROOF_IDLE_BINDING)!=HOST_PROOF_IDLE_BINDING_SHA256:raise RuntimeError('Host proof idle binding identity changed.')
    value=json.loads(HOST_PROOF_IDLE_BINDING.read_bytes())
    if value.get('patch_sha256')!=HOST_PROOF_IDLE_PATCH_SHA256 or set(value.get('files',{}))!=set(HOST_PROOF_IDLE_SOURCE_NAMES):raise RuntimeError('Host proof idle two-file binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files'],**task_callee_binding()['files'],**stack_direct_binding()['files']}
    records={}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']or re.fullmatch('[0-9a-f]{64}',record.get('final_sha256',''))is None:raise RuntimeError('Host proof idle predecessor/final lineage differs: '+name)
        records[name]={**record,'normalized_final_sha256':record['final_sha256']}
    return {**value,'files':records}

def validate_host_proof_idle_patch(path):
    binding=host_proof_idle_binding();names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=HOST_PROOF_IDLE_PATCH_SHA256 or len(names)!=2 or set(names)!=set(binding['files']):raise RuntimeError('Host proof idle patch identity/scope changed.')
    return names

STACK_DIRECT_BINDING=ROOT/'patches/runtime-stack-direct.json'
STACK_DIRECT_PATCH_SHA256='15216693a15553b6c0b3a71a9b96e281300dc31a07cee51a1612d92789f2e39c'
STACK_DIRECT_BINDING_SHA256='25a03769d286abcee36af97b94562a7189a530beecef490c449cf86f002d44f8'
STACK_DIRECT_SOURCE_NAMES=('recompiler/v2/native_regions.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py')

def stack_direct_binding():
    if sha(STACK_DIRECT_BINDING)!=STACK_DIRECT_BINDING_SHA256:raise RuntimeError('Stack direct binding identity changed.')
    value=json.loads(STACK_DIRECT_BINDING.read_bytes())
    if value.get('patch_sha256')!=STACK_DIRECT_PATCH_SHA256 or set(value.get('files',{}))!=set(STACK_DIRECT_SOURCE_NAMES):raise RuntimeError('Stack direct three-file binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files'],**task_callee_binding()['files']}
    records={}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']or re.fullmatch('[0-9a-f]{64}',record.get('sha256',''))is None:raise RuntimeError('Stack direct predecessor/final lineage differs: '+name)
        records[name]={'predecessor_sha256':record['predecessor_sha256'],'final_sha256':record['sha256'],'normalized_final_sha256':record['sha256']}
    return {**value,'files':records}

def validate_stack_direct_patch(path):
    binding=stack_direct_binding();names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=STACK_DIRECT_PATCH_SHA256 or len(names)!=3 or set(names)!=set(binding['files']):raise RuntimeError('Stack direct patch identity/scope changed.')
    return names

def validate_stack_direct_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);rom=Path(rom);raw=rom.read_bytes()
    value=json.loads((directory/'native_regions.json').read_bytes());rows=value.get('regions');code=(directory/'native_regions_v2.c').read_text(encoding='utf-8')
    if sha(rom)!=rom_sha or value.get('rom_sha256')!=rom_sha or value.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal'] or not isinstance(rows,list)or len(rows)!=normal_source_row_count(value):raise RuntimeError('Stack direct actualROM/metadata9/count differs.')
    subset=[r for r in rows if r.get('contract')=='native-e0-source-cached-stack-direct-v1']
    opcodes={'ORA':0x03,'AND':0x23,'EOR':0x43,'ADC':0x63,'STA':0x83,'LDA':0xa3,'CMP':0xc3,'SBC':0xe3}
    if len(subset)!=6:raise RuntimeError('Stack direct six source-derived mode rows required.')
    for row in subset:
        pc=row.get('pc24');b=row.get('bytes');body=row.get('body');mnemonic=row.get('mnemonic');offset=(pc>>16)*32768+(pc&32767)
        if row.get('m')not in(0,1)or row.get('x')not in(0,1)or row.get('length')!=2 or row.get('next_pc')!=((pc+2)&65535)or mnemonic not in opcodes or not isinstance(b,str)or len(b)!=4 or bytes.fromhex(b)[0]!=opcodes[mnemonic]or raw[offset:offset+2].hex()!=b:raise RuntimeError('Stack direct typed source row/ROM/mode differs.')
        expected='uint32 _ea = (uint16)(cpu->S + 0x%04X);'%bytes.fromhex(b)[1]
        if not isinstance(body,str)or body not in code or body.count('cpu->S')!=1 or body.count(expected)!=1 or 'cpu_aot_begin' in body or 'cpu_aot_commit' in body or '*next_pc=((uint32)cpu->PB<<16)|'not in body:raise RuntimeError('Stack direct readonly S/single bankzero EA/body differs.')
    if cache.get('outputs',{}).get('native_regions_v2.c')!=sha(directory/'native_regions_v2.c')or cache.get('outputs',{}).get('native_regions.json')!=sha(directory/'native_regions.json'):raise RuntimeError('Stack direct output/cache mismatch.')
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'normal_rows':len(rows),'stack_direct_rows':len(subset),'execution_qualified':False}

TASK_CALLEE_BINDING=ROOT/'patches/runtime-native-task-callee.json'
TASK_CALLEE_PATCH_SHA256='ad6077aab910fbdff3d579452d156dc69993b462427cbcd6808e207cb5204ea6'
TASK_CALLEE_BINDING_SHA256='92ec2e1cf404f69204b00ffbcdba61416ae79f9865ab5a93acaae2b0dcf169a4'
TASK_CALLEE_SOURCE_NAMES=('recompiler/v2/task_resume.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/bridge_task_call.inc')

def task_callee_binding():
    if sha(TASK_CALLEE_BINDING)!=TASK_CALLEE_BINDING_SHA256:raise RuntimeError('Task callee binding identity changed.')
    value=json.loads(TASK_CALLEE_BINDING.read_bytes())
    if value.get('patch_sha256')!=TASK_CALLEE_PATCH_SHA256 or set(value.get('files',{}))!=set(TASK_CALLEE_SOURCE_NAMES):raise RuntimeError('Task callee five-file binding differs.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files'],**indirect_y_binding()['files']}
    records={}
    for name,record in value['files'].items():
        if record.get('predecessor_sha256')!=(predecessors[name]['final_sha256'] if name in predecessors else None):raise RuntimeError('Task callee predecessor differs: '+name)
        if re.fullmatch('[0-9a-f]{64}',record.get('final_sha256',''))is None:raise RuntimeError('Task callee final hash missing.')
        records[name]={**record,'normalized_final_sha256':record['final_sha256']}
    return {**value,'files':records}

def validate_task_callee_patch(path):
    binding=task_callee_binding();names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=TASK_CALLEE_PATCH_SHA256 or len(names)!=5 or set(names)!=set(binding['files']):raise RuntimeError('Task callee patch identity/scope changed.')
    return names

INDIRECT_Y_BINDING=ROOT/'patches/runtime-indirect-y.json'
INDIRECT_Y_PATCH_SHA256='e2b7b7da6944d2aec3b0e4724b422cc2359f93f2782235f3ebf1c2bf742d08a5'
INDIRECT_Y_BINDING_SHA256='fb74e71b35d46c2863eb970d576efeda1869f8819de8f72ecf23816ad8d850ba'
INDIRECT_Y_SOURCE_NAMES=('recompiler/v2/native_regions.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c')

def indirect_y_binding():
    if sha(INDIRECT_Y_BINDING)!=INDIRECT_Y_BINDING_SHA256:raise RuntimeError('IndirectY binding identity changed.')
    value=json.loads(INDIRECT_Y_BINDING.read_bytes())
    if value.get('patch_sha256')!=INDIRECT_Y_PATCH_SHA256 or set(value.get('files',{}))!=set(INDIRECT_Y_SOURCE_NAMES):raise RuntimeError('IndirectY four-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files'],**source_redirect_binding()['files']}
    records={}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256'] or re.fullmatch('[0-9a-f]{64}',record.get('sha256','')) is None:raise RuntimeError('IndirectY predecessor/final lineage differs: '+name)
        # Frozen24 authored sources are exactLF; do not rewrite binding JSON.
        records[name]={'predecessor_sha256':record['predecessor_sha256'],'final_sha256':record['sha256'],'normalized_final_sha256':record['sha256']}
    return {**value,'files':records}

def validate_indirect_y_patch(path):
    binding=indirect_y_binding();names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=4 or set(names)!=set(binding['files']):raise RuntimeError('IndirectY patch identity/scope changed; preserve build.')
    return names

def validate_indirect_y_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);rom=Path(rom);raw=rom.read_bytes()
    if sha(rom)!=rom_sha:raise RuntimeError('IndirectY supplied ROM identity differs.')
    value=json.loads((directory/'native_regions.json').read_bytes());rows=value.get('regions');code=(directory/'native_regions_v2.c').read_text(encoding='utf-8')
    if value.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal'] or value.get('rom_sha256')!=rom_sha or not isinstance(rows,list) or len(rows)!=normal_source_row_count(value):raise RuntimeError('IndirectY metadata9/source-scoped normal generation differs.')
    subset=[r for r in rows if r.get('contract')=='native-e0-source-cached-indirect-y-v1']
    opcodes={'ORA':0x11,'AND':0x31,'EOR':0x51,'ADC':0x71,'STA':0x91,'LDA':0xb1,'CMP':0xd1,'SBC':0xf1}
    if len(subset)!=16:raise RuntimeError('IndirectY sixteen source-derived mode rows required.')
    for row in subset:
        pc=row.get('pc24');m=row.get('m');x=row.get('x');body=row.get('body');b=row.get('bytes');mnemonic=row.get('mnemonic');offset=(pc>>16)*32768+(pc&32767)
        if m not in (0,1) or x not in (0,1) or row.get('length')!=2 or row.get('next_pc')!=((pc+2)&65535) or mnemonic not in opcodes or not isinstance(b,str) or len(b)!=4 or bytes.fromhex(b)[0]!=opcodes[mnemonic] or raw[offset:offset+2].hex()!=b:raise RuntimeError('IndirectY typed source row/ROM/mode differs.')
        if not isinstance(body,str) or body not in code or body.count('uint16 _ea_lo = cpu_aot_read16(cpu, 0x00, _ea_p);')!=1 or 'cpu_aot_begin' in body or 'cpu_aot_commit' in body or '*next_pc=((uint32)cpu->PB<<16)|' not in body:raise RuntimeError('IndirectY faithful pointer/body/fullPC differs.')
    for name,count in (('native_regions_v2.c',normal_source_row_count(value)+3),('native_task_resume_v2.c',TASK_GENERATED_ROW_COUNT),('native_source_redirect_v2.c',3)):
        path=directory/name;reject_links(path);source=path.read_text(encoding='utf-8')
        if source.count('cpu_aot_begin_scheduler_region(')!=count or 'cpu_aot_begin_region(' in source:raise RuntimeError('IndirectY common one-use scheduler scope missing: '+name)
        if cache.get('outputs',{}).get(name)!=sha(path):raise RuntimeError('IndirectY scoped output/cache mismatch: '+name)
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'normal_rows':len(rows),'indirect_y_rows':len(subset),'execution_qualified':False}

def selected_task_binding():
    if sha(SELECTED_TASK_BINDING)!=SELECTED_TASK_BINDING_SHA256:
        raise RuntimeError('Selected task binding exact identity changed.')
    value=json.loads(SELECTED_TASK_BINDING.read_bytes())
    if value.get('patch_sha256')!=SELECTED_TASK_PATCH_SHA256 or set(value.get('files',{}))!=set(SELECTED_TASK_SOURCE_NAMES):
        raise RuntimeError('Selected task eleven-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files']}
    for name,record in value['files'].items():
        if name in predecessors and record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Selected task predecessor lineage differs: '+name)
        for key in ('final_sha256','normalized_final_sha256'):
            if re.fullmatch('[0-9a-f]{64}',record.get(key,'')) is None:raise RuntimeError('Selected task final hash missing.')
    return value

def validate_selected_task_patch(path):
    binding=selected_task_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=11 or set(names)!=set(binding['files']):
        raise RuntimeError('Selected task patch identity/scope changed; preserve build.')
    return names

def validate_selected_task_recipe(cfg_dir):
    expected='source_task_resume_v1 00FF03 008461 0083E2 008429 00842F 01D878 01840A'
    records=[]
    for path in Path(cfg_dir).glob('*.cfg'):
        for line in path.read_text(encoding='utf-8').splitlines():
            clean=line.split('#',1)[0].strip()
            if clean.startswith('source_task_resume'):records.append((path.name,' '.join(clean.split())))
    if records!=[('bank00.cfg',expected)]:raise RuntimeError('Exactly one source-selected task recipe in bank00.cfg is required.')
    cases=[]
    for path in Path(cfg_dir).glob('*.cfg'):
        for line in path.read_text(encoding='utf-8').splitlines():
            clean=line.split('#',1)[0].strip()
            if clean.startswith('source_task_case'):cases.append((path.name,' '.join(clean.split())))
    if cases!=[('bank00.cfg','source_task_case_v1 01E000 01E056 01E05A 1 0')]:raise RuntimeError('Exactly one named selected task E056/E05A source case is required.')

SOURCE_REDIRECT_BINDING=ROOT/'patches/runtime-source-redirect.json'
SOURCE_REDIRECT_PATCH_SHA256='0d5dcadea5529cc7e86e9d584c31321b8ae1c732ec82262be04d5d6a1832d40e'
SOURCE_REDIRECT_BINDING_SHA256='10fac75b53b43f46dfc9fc72d1fad6e4bf4322f8c530662296343ba54bc5a62b'
SOURCE_REDIRECT_SOURCE_NAMES=('recompiler/v2/cfg_loader.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/source_redirect.py', 'runner/src/cpu_state.c', 'runner/src/snes/interp_bridge.c', 'runner/src/redirect_contract.h', 'runner/src/redirect_contract.inc', 'runner/src/snes/bridge_redirect_helpers.inc')

def source_redirect_binding():
    if sha(SOURCE_REDIRECT_BINDING)!=SOURCE_REDIRECT_BINDING_SHA256:
        raise RuntimeError('Source redirect binding exact identity changed.')
    value=json.loads(SOURCE_REDIRECT_BINDING.read_bytes())
    if value.get('patch_sha256')!=SOURCE_REDIRECT_PATCH_SHA256 or set(value.get('files',{}))!=set(SOURCE_REDIRECT_SOURCE_NAMES):
        raise RuntimeError('Source redirect eight-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files'],**stack_controls_binding()['files'],**selected_task_binding()['files']}
    for name,record in value['files'].items():
        if name in predecessors and record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Source redirect predecessor lineage differs: '+name)
        if name not in predecessors and record.get('predecessor_sha256') is not None:raise RuntimeError('Source redirect undeclared predecessor: '+name)
        for key in ('final_sha256','normalized_final_sha256'):
            if re.fullmatch('[0-9a-f]{64}',record.get(key,'')) is None:raise RuntimeError('Source redirect final hash missing.')
    return value

def validate_source_redirect_patch(path):
    binding=source_redirect_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=8 or set(names)!=set(binding['files']):
        raise RuntimeError('Source redirect patch identity/scope changed; preserve build.')
    return names

def validate_source_redirect_recipe(cfg_dir):
    expected='source_redirect_v1 01D111 00FF20 0084D9 0084FA 01D119 02 01D176'
    records=[]
    for path in Path(cfg_dir).glob('*.cfg'):
        for line in path.read_text(encoding='utf-8').splitlines():
            clean=line.split('#',1)[0].strip()
            if clean.startswith('source_redirect'):records.append((path.name,' '.join(clean.split())))
    if records!=[('bank01.cfg',expected)]:raise RuntimeError('Exactly one source-source redirect recipe in bank01.cfg is required.')


SUSPEND_TASK_FAMILY_SHA256='ee1db8462b1461ca99ce652cddc3d5212353df831ae63f48b78ec123846ef9e3'
SUSPEND_TASK_PRIOR_ROWS_SHA256='eea81f1dc726eeb28fbe6cb875dab3417fe1f9f8022e8ae33d91b0b9a5753d64'
SUSPEND_TASK_ADDED_ROWS_SHA256='e7499822fd11a8140aaf63ae2a728191ba9d352e49ed10eacecbb2890e20e2fb'

def validate_selected_task_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);metadata_path=directory/'native_task_resume.json';source_path=directory/'native_task_resume_v2.c'
    reject_links(metadata_path);reject_links(source_path)
    value=json.loads(metadata_path.read_bytes())
    recipe={'callee': 65283, 'calls': [120952, 99338], 'return': 33839, 'select': 33833, 'subcall': {'call': 120847, 'callee': 120959, 'entry_m': 1, 'entry_x': [0, 1], 'exit_m': 0, 'exit_x': 0, 'landing': 120850, 'return': 121008, 'rows': [{'branch': 0, 'bytes': 'c230', 'fall': 120961, 'length': 2, 'm': 1, 'opcode': 194, 'pc24': 120959, 'x': 0}, {'branch': 0, 'bytes': 'a95555', 'fall': 120964, 'length': 3, 'm': 0, 'opcode': 169, 'pc24': 120961, 'x': 0}, {'branch': 0, 'bytes': '8f00247e', 'fall': 120968, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 120964, 'x': 0}, {'branch': 0, 'bytes': '8f01247e', 'fall': 120972, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 120968, 'x': 0}, {'branch': 0, 'bytes': '8f1e247e', 'fall': 120976, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 120972, 'x': 0}, {'branch': 0, 'bytes': 'a980f0', 'fall': 120979, 'length': 3, 'm': 0, 'opcode': 169, 'pc24': 120976, 'x': 0}, {'branch': 0, 'bytes': 'a23000', 'fall': 120982, 'length': 3, 'm': 0, 'opcode': 162, 'pc24': 120979, 'x': 0}, {'branch': 0, 'bytes': 'ca', 'fall': 120983, 'length': 1, 'm': 0, 'opcode': 202, 'pc24': 120982, 'x': 0}, {'branch': 0, 'bytes': 'ca', 'fall': 120984, 'length': 1, 'm': 0, 'opcode': 202, 'pc24': 120983, 'x': 0}, {'branch': 0, 'bytes': 'ca', 'fall': 120985, 'length': 1, 'm': 0, 'opcode': 202, 'pc24': 120984, 'x': 0}, {'branch': 0, 'bytes': 'ca', 'fall': 120986, 'length': 1, 'm': 0, 'opcode': 202, 'pc24': 120985, 'x': 0}, {'branch': 0, 'bytes': '9f00227e', 'fall': 120990, 'length': 4, 'm': 0, 'opcode': 159, 'pc24': 120986, 'x': 0}, {'branch': 120982, 'bytes': 'd0f6', 'fall': 120992, 'length': 2, 'm': 0, 'opcode': 208, 'pc24': 120990, 'x': 0}, {'branch': 0, 'bytes': '8ff0237e', 'fall': 120996, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 120992, 'x': 0}, {'branch': 0, 'bytes': '8ff4237e', 'fall': 121000, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 120996, 'x': 0}, {'branch': 0, 'bytes': '8ff8237e', 'fall': 121004, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 121000, 'x': 0}, {'branch': 0, 'bytes': '8ffc237e', 'fall': 121008, 'length': 4, 'm': 0, 'opcode': 143, 'pc24': 121004, 'x': 0}, {'branch': 0, 'bytes': '60', 'fall': 120850, 'length': 1, 'm': 0, 'opcode': 96, 'pc24': 121008, 'x': 0}, {'branch': 0, 'bytes': 'c230', 'fall': 120961, 'length': 2, 'm': 1, 'opcode': 194, 'pc24': 120959, 'x': 1}], 'same_owner': True}}
    recipe['cases']=[{'callsite':pc,'landing':pc+4,'p_mask':0x20,'p_value':0x20}for pc in recipe['calls']]+[{'callsite':0x01e056,'landing':0x01e05a,'p_mask':0x30,'p_value':0x20}]
    if value.get('format_version')!=RUNTIME_GENERATION_FORMATS['task'] or value.get('kind')!='source_selected_task_resume' or value.get('rom_sha256')!=rom_sha or {k:v for k,v in value.get('recipe',{}).items()if k not in ('original_calls','original_prefix_keys','suspended_child')}!=recipe:
        raise RuntimeError('Selected task generated source recipe/ROM metadata mismatch.')
    family=value.get('recipe',{}).get('original_calls')
    if not isinstance(family,dict)or family.get('maximum_frames')!=2 or family.get('maximum_stack_bytes')!=5 or len(family.get('graphs',[]))!=12:raise RuntimeError('Original call source family differs.')
    sites=[(0x01d858,0x01d809),(0x01d862,0x01d803),(0x01d86c,0x01d806),(0x01d870,0x01d80c)]
    if [(r.get('source'),r.get('target'))for r in family.get('calls',[])]!=sites:raise RuntimeError('Original source call edges differ.')
    source_rows=[r for g in family['graphs']for r in g['rows']]
    if len(source_rows)!=1471 or any(g.get('errors')for g in family['graphs']):raise RuntimeError('Original call source graph closure differs.')
    raw=Path(rom).read_bytes()
    for r in source_rows:
        pc=r.get('pc24');b=bytes.fromhex(r.get('bytes',''));offset=(pc>>16)*32768+(pc&32767)
        if r.get('m')not in(0,1)or r.get('x')not in(0,1)or not b or len(b)!=r.get('length')or raw[offset:offset+len(b)]!=b:raise RuntimeError('Original call source graph row/ROM differs.')
    rows=value.get('rows');graphs=value.get('graphs')
    if not isinstance(rows,list) or len(rows)!=TASK_GENERATED_ROW_COUNT or len({(r.get('pc24'),r.get('m'),r.get('x'))for r in rows})!=TASK_GENERATED_ROW_COUNT or not isinstance(graphs,list) or len(graphs)<5:
        raise RuntimeError('Selected task source-scoped generation count differs.')
    child=value.get('recipe',{}).get('suspended_child')
    canonical=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if canonical(child)!=SUSPEND_TASK_FAMILY_SHA256:raise RuntimeError('Causal suspended-child exact source recipe differs.')
    old_rows=[r for r in rows if not r.get('causal_suspended_child')]
    new_rows=[r for r in rows if r.get('causal_suspended_child')]
    if len(old_rows)!=228 or canonical(old_rows)!=SUSPEND_TASK_PRIOR_ROWS_SHA256:raise RuntimeError('Existing228task fields/keys/bodies differ.')
    if len(new_rows)!=7 or canonical(new_rows)!=SUSPEND_TASK_ADDED_ROWS_SHA256:raise RuntimeError('Seven causal BRA fields/keys/bodies differ.')
    if any(r.get('mnemonic')!='BRA' or r.get('contract')!='native-e0-causal-suspended-child-v1' for r in new_rows):raise RuntimeError('New child rows cross exact BRA contract.')
    child_keys={(r['pc24'],r['m'],r['x'])for r in new_rows}
    if child_keys!={(p,1,1)for p in (0x1f033,0x1f0a5,0x1f0ed,0x1f17c,0x1f1c4,0x1f255,0x1f29d)}:raise RuntimeError('Child selected keys differ.')
    for r in child['architecture']+child['parent_architecture']:
        pc=r['pc'];b=bytes.fromhex(r['bytes']);off=(pc>>16)*32768+(pc&32767)
        if r['m']not in(0,1)or r['x']not in(0,1)or len(b)!=r['length']or raw[off:off+len(b)]!=b:raise RuntimeError('Child/parent architecture source bytes differ.')
    for r in child['spans']:
        pc=r['pc24'];b=bytes.fromhex(r['bytes']);off=(pc>>16)*32768+(pc&32767)
        if raw[off:off+len(b)]!=b:raise RuntimeError('Child protected source span differs.')
    child_code=source_path.read_text(encoding='utf-8')
    if child_code.count('if(!cpu_source_suspend_region_active(cpu,pc24,mx)) return false;')!=7:raise RuntimeError('Seven causal child begin guards missing.')
    if any(r.get('contract')not in ('native-e0-source-selected-task-resume-v1','native-e0-original-owned-callee-prefix-v1','native-e0-causal-suspended-child-v1') or r.get('mnemonic')in('JSR','JSL','RTS','RTL','TCS','TXS','PLP','PHA','PHX','PHY','PHD','PHB','PHK','PHP','PLA','PLX','PLY','PLD','PLB') for r in rows):
        raise RuntimeError('Selected task rows cross original call/stack/return barrier.')
    prefix_keys=value.get('recipe',{}).get('original_prefix_keys')
    expected_keys={(0x01d806,1,0),(0x01d80c,1,0),(0x01ddf8,1,0)}
    expected_keys.update((pc,1,0)for pc in (0x01da56,0x01da58,0x01da5a,0x01da5d,0x01da5f,0x01da61,0x01da64,0x01da66,0x01da68,0x01da6a,0x01da6c))
    expected_keys.update((pc,0,0)for pc in (0x01da6e,0x01da71,0x01da73))
    if not isinstance(prefix_keys,list)or len(prefix_keys)!=17 or {(r.get('pc24'),r.get('m'),r.get('x'))for r in prefix_keys}!=expected_keys:raise RuntimeError('Original-owned prefix source keys differ.')
    prefix_map={(r['pc24'],r['m'],r['x']):r for r in prefix_keys}
    for row in rows:
        key=(row['pc24'],row['m'],row['x']);entry=prefix_map.get(key)
        if key in child_keys:continue
        if entry is None:
            if row.get('contract')!='native-e0-source-selected-task-resume-v1' or 'original_contexts'in row:raise RuntimeError('Selected row borrows original-owned authority.')
            continue
        contexts=[n for n,g in enumerate(family['graphs'])if any((r['pc24'],r['m'],r['x'])==key for r in g['rows'])]
        if not contexts or entry.get('contexts')!=contexts or row.get('original_contexts')!=contexts or row.get('contract')!='native-e0-original-owned-callee-prefix-v1':raise RuntimeError('Original-owned prefix context membership differs.')
    rom=Path(rom);raw=rom.read_bytes();code=source_path.read_text(encoding='utf-8')
    if sha(rom)!=rom_sha:raise RuntimeError('Task callee actual ROM differs.')
    for row in rows:
        pc=row.get('pc24');b=row.get('bytes');body=row.get('body');offset=(pc>>16)*32768+(pc&32767)
        if row.get('m')not in(0,1)or row.get('x')not in(0,1)or not isinstance(b,str)or row.get('length')!=len(bytes.fromhex(b))or raw[offset:offset+row['length']].hex()!=b or not isinstance(body,str)or body not in code:raise RuntimeError('Task callee typed row/ROM/body differs.')
    for row in recipe['subcall']['rows']:
        pc=row['pc24'];offset=(pc>>16)*32768+(pc&32767)
        if raw[offset:offset+row['length']].hex()!=row['bytes']:raise RuntimeError('Task callee original subcall/return source differs.')
    for name in ('native_task_resume.json','native_task_resume_v2.c'):
        if cache.get('outputs',{}).get(name)!=sha(directory/name):raise RuntimeError('Selected task output missing or changed: '+name)
    return value

def validate_source_redirect_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);rom=Path(rom);raw=rom.read_bytes()
    if sha(rom)!=rom_sha or len(raw)!=1572864:raise RuntimeError('Source redirect supplied ROM identity mismatch.')
    metadata=directory/'native_source_redirect.json';source=directory/'native_source_redirect_v2.c';reject_links(metadata);reject_links(source)
    value=json.loads(metadata.read_bytes());recipe={'entry':0x01d111,'return':0x0084fa,'selector':2,'table':0x01d119,'landing':0x01d176,'decimal':0,'barrier':0x01d17e}
    if value.get('format_version')!=1 or value.get('kind')!='source_bound_original_redirect' or value.get('recipe')!=recipe:raise RuntimeError('Source redirect generated source recipe mismatch.')
    specs=((0x01d176,1,0,'REP','c220',3,0xd178),(0x01d178,0,0,'LDA','a90300',3,0xd17b),(0x01d17b,0,0,'STA','8d4f04',5,0xd17e))
    rows=value.get('rows');code=source.read_text(encoding='utf-8')
    if not isinstance(rows,list) or len(rows)!=3:raise RuntimeError('Source redirect source-scoped three rows required.')
    for row,spec in zip(rows,specs):
        pc,m,x,mnemonic,b,cycles,next_pc=spec;offset=(pc>>16)*32768+(pc&32767)
        if (row.get('pc24'),row.get('m'),row.get('x'),row.get('mnemonic'),row.get('bytes'),row.get('cycles'),row.get('next_pc'))!=spec or row.get('length')!=len(bytes.fromhex(b)) or row.get('contract')!='native-e0-source-original-redirect-v1' or raw[offset:offset+len(bytes.fromhex(b))].hex()!=b:raise RuntimeError('Source redirect typed architectural row/ROM differs.')
        if not isinstance(row.get('body'),str) or row['body'] not in code:raise RuntimeError('Source redirect generated row body missing.')
    for guard in ('if(!cpu_source_redirect_active(cpu,pc24,mx))return false;','cpu_source_redirect_recipe_matches','*next_pc=((uint32)cpu->PB<<16)|0xD178u','*next_pc=((uint32)cpu->PB<<16)|0xD17Bu','*next_pc=((uint32)cpu->PB<<16)|0xD17Eu'):
        if guard not in code:raise RuntimeError('Source redirect generated typed/owner guard missing.')
    spans=((0x00a403,'4cfda8'),(0x00a8fd,'e220a9028d42042206c401'),(0x01c406,'4c07d1'),(0x01d107,'e220ad4204c9ffd0016b2220ff00'),(0x00ff20,'4cd984'),(0x0084d9,'088bc23029ff000aaae220a30548abc2208a386303a8b9000038e901008303ab286b'),(0x01d119,'76d1'))
    for pc,hexbytes in spans:
        b=bytes.fromhex(hexbytes);offset=(pc>>16)*32768+(pc&32767)
        if raw[offset:offset+len(b)]!=b:raise RuntimeError('Source redirect dispatcher ROM recipe differs.')
        for i,v in enumerate(b):
            if f'if(!peek(ctx,{pc+i}u,&b)||b!={v}u)return 0;' not in code:raise RuntimeError('Source redirect generated dispatcher byte guard missing.')
    for name in ('native_source_redirect.json','native_source_redirect_v2.c'):
        if cache.get('outputs',{}).get(name)!=sha(directory/name):raise RuntimeError('Source redirect generated output/cache mismatch: '+name)
    return value

def stack_controls_binding():
    value=json.loads(STACK_CONTROLS_BINDING.read_bytes())
    if value.get('patch_sha256')!=STACK_CONTROLS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=3:
        raise RuntimeError('Native stack control three-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files'],**prefix_instructions_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native stack control predecessor lineage differs: '+name)
    return value

def validate_stack_controls_patch(path):
    binding=stack_controls_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=3 or set(names)!=set(binding['files']):
        raise RuntimeError('Native stack control patch identity/scope changed; preserve build.')
    return names

def prefix_instructions_binding():
    value=json.loads(PREFIX_INSTRUCTIONS_BINDING.read_bytes())
    if value.get('patch_sha256')!=PREFIX_INSTRUCTIONS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=3:
        raise RuntimeError('Native prefix instruction three-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files'],**return_steps_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native prefix instruction predecessor lineage differs: '+name)
    return value

def validate_prefix_instructions_patch(path):
    binding=prefix_instructions_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=3 or set(names)!=set(binding['files']):
        raise RuntimeError('Native prefix instruction patch identity/scope changed; preserve build.')
    return names

def return_steps_binding():
    value=json.loads(RETURN_STEPS_BINDING.read_bytes())
    if value.get('patch_sha256')!=RETURN_STEPS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=4:
        raise RuntimeError('Native return step four-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files'],**stack_primitives_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native return step predecessor lineage differs: '+name)
    return value

def validate_return_steps_patch(path):
    binding=return_steps_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=4 or set(names)!=set(binding['files']):
        raise RuntimeError('Native return step patch identity/scope changed; preserve build.')
    return names

def stack_primitives_binding():
    value=json.loads(STACK_PRIMITIVES_BINDING.read_bytes())
    if value.get('patch_sha256')!=STACK_PRIMITIVES_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=2:
        raise RuntimeError('Native stack primitive two-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files'],**hook_handoff_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native stack primitive predecessor lineage differs: '+name)
    return value

def validate_stack_primitives_patch(path):
    binding=stack_primitives_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=2 or set(names)!=set(binding['files']):
        raise RuntimeError('Native stack primitive patch identity/scope changed; preserve build.')
    return names

def hook_handoff_binding():
    value=json.loads(HOOK_HANDOFF_BINDING.read_bytes())
    if value.get('patch_sha256')!=HOOK_HANDOFF_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=4:
        raise RuntimeError('Native hook handoff four-file source binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files'],**native_regions_binding()['files'],**leaf_regions_binding()['files']}
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native hook handoff predecessor lineage differs: '+name)
    return value

def validate_hook_handoff_patch(path):
    binding=hook_handoff_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=4 or set(names)!=set(binding['files']):
        raise RuntimeError('Native hook handoff patch identity/scope changed; preserve build.')
    return names

def leaf_regions_binding():
    value=json.loads(LEAF_REGIONS_BINDING.read_bytes())
    if value.get('patch_sha256')!=LEAF_REGIONS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=3:
        raise RuntimeError('Native leaf region three-file source binding missing/stale.')
    predecessors=native_regions_binding()['files']
    for name,record in value['files'].items():
        if name not in predecessors or record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native leaf region predecessor lineage differs: '+name)
    return value

def validate_leaf_regions_patch(path):
    binding=leaf_regions_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=3 or set(names)!=set(binding['files']):
        raise RuntimeError('Native leaf region patch identity/scope changed; preserve build.')
    return names

def native_regions_binding():
    value=json.loads(NATIVE_REGIONS_BINDING.read_bytes())
    if value.get('patch_sha256')!=NATIVE_REGIONS_PATCH_SHA256 or not isinstance(value.get('files'),dict) or len(value['files'])!=6:
        raise RuntimeError('Native region six-file binding missing/stale.')
    predecessors={**continuation_binding()['files'],**rmw_binding()['files'],**memory_bits_binding()['files']}
    for name,record in value['files'].items():
        if name in predecessors and record.get('predecessor_sha256')!=predecessors[name]['final_sha256']:
            raise RuntimeError('Native region predecessor lineage differs: '+name)
    if value['files']['recompiler/v2/native_regions.py'].get('predecessor_sha256') is not None:
        raise RuntimeError('Native region new source must have no predecessor.')
    return value

def validate_native_regions_patch(path):
    binding=native_regions_binding()
    names=re.findall(r'^diff --git a/(\S+) b/',Path(path).read_text(encoding='utf-8'),re.M)
    if sha(Path(path))!=binding['patch_sha256'] or len(names)!=6 or set(names)!=set(binding['files']):
        raise RuntimeError('Native region patch identity/scope changed; preserve build.')
    return names

def validate_final_runtime(runtime,normalize=False,memory_bits=True,native_regions=True,leaf_regions=True,hook_handoff=True,stack_primitives=True,return_steps=True,prefix_instructions=True,stack_controls=True,selected_task=True,source_redirect=True,indirect_y=True,task_callee=True,stack_direct=True,host_proof_idle=True,redirect_observer_idle=True,selected_case=True,direct_call=True,extensions=True):
    # Earlier patches remain frozen. The final delta replaces only its exact
    # predecessors; unaffected continuation inputs retain their final binding.
    files={**continuation_binding()['files'],**rmw_binding()['files']}
    if memory_bits:files.update(memory_bits_binding()['files'])
    if native_regions:files.update(native_regions_binding()['files'])
    if native_regions and leaf_regions:files.update(leaf_regions_binding()['files'])
    if native_regions and leaf_regions and hook_handoff:files.update(hook_handoff_binding()['files'])
    if native_regions and leaf_regions and hook_handoff and stack_primitives:files.update(stack_primitives_binding()['files'])
    if native_regions and leaf_regions and hook_handoff and stack_primitives and return_steps:files.update(return_steps_binding()['files'])
    if native_regions and leaf_regions and hook_handoff and stack_primitives and return_steps and prefix_instructions:files.update(prefix_instructions_binding()['files'])
    if native_regions and leaf_regions and hook_handoff and stack_primitives and return_steps and prefix_instructions and stack_controls:files.update(stack_controls_binding()['files'])
    if stack_controls and selected_task and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(selected_task_binding()['files'])
    if source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(source_redirect_binding()['files'])
    if indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(indirect_y_binding()['files'])
    if task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(task_callee_binding()['files'])
    if stack_direct and task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(stack_direct_binding()['files'])
    if host_proof_idle and stack_direct and task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(host_proof_idle_binding()['files'])
    if redirect_observer_idle and host_proof_idle and stack_direct and task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(redirect_observer_idle_binding()['files'])
    if selected_case and redirect_observer_idle and host_proof_idle and stack_direct and task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:files.update(selected_case_binding()['files'])
    if direct_call and selected_case and redirect_observer_idle and host_proof_idle and stack_direct and task_callee and indirect_y and source_redirect and selected_task and stack_controls and prefix_instructions and return_steps and stack_primitives and hook_handoff and leaf_regions and native_regions:
        files.update(direct_call_binding()['files'])
        if extensions:
            for binding in runtime_extension_bindings():files.update(binding['files'])
    for name,record in files.items():
        path=runtime/name;reject_links(path);raw=path.read_bytes()
        normalized=raw.replace(b'\r\n',b'\n')
        if hashlib.sha256(normalized).hexdigest()!=record['normalized_final_sha256']:
            raise RuntimeError('Final runtime source differs: '+name)
        if normalize and sha(path)!=record['final_sha256']:
            options=(normalized,normalized.replace(b'\n',b'\r\n'))
            exact=next((item for item in options if hashlib.sha256(item).hexdigest()==record['final_sha256']),None)
            if exact is None:raise RuntimeError('Unrecognized final source representation: '+name)
            path.write_bytes(exact)
        if sha(path)!=record['final_sha256']:
            raise RuntimeError('Final runtime exact source identity differs: '+name)

def runtime_source_accounting(runtime,patch_names,new_names=()):
    tracked=set(command(['git','diff','--name-only'],runtime).splitlines())
    untracked=set(command(['git','ls-files','--others','--exclude-standard'],runtime).splitlines())
    if tracked!=set(patch_names)-set(new_names)or untracked!=set(new_names):
        raise RuntimeError('Unexpected tracked or new runtime sources; preserved without reset.')

def runtime_cache_identity(patch_hashes):
    hashes=list(patch_hashes)
    if len(hashes)!=30+len(RUNTIME_EXTENSION_SPECS) or any(not isinstance(d,str)or (re.fullmatch('[0-9a-f]{64}',d)is None or d=='0'*64) for d in hashes):
        raise ValueError('Runtime cache requires the complete pinned ordered patch list')
    combined=hashlib.sha256(('\n'.join(hashes)+'\n').encode('ascii')).hexdigest()
    return {'runtime_pin':RUNTIME_PIN,'algorithm':f'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes',
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

def generation_commands(runtime,project,rom,identity,profiles=(),prefixes=True,reviewed=True,certify=True,continuations=True,direct_calls=True):
    # Source-owned live-mode alternatives are independent of prefix/call diagnostics.
    emit=[sys.executable,runtime/'tools/v2_emit.py','--rom',rom,'--cfg-dir',project/'recomp',
      '--out-dir',project/'src/gen','--analysis-backend','native','--cfg-roots','--no-host-root-scan','--native-mode-successors']
    if prefixes:emit+=['--faithful-prefixes']
    if direct_calls:emit+=['--native-direct-call-prefix']
    sync=[sys.executable,runtime/'tools/v2_sync_funcs_h.py','--cfg-dir',project/'recomp','--out',project/'recomp/funcs.h']
    if reviewed:emit+=['--reviewed-root-manifest',project/REVIEWED_ROOTS_INPUT]
    if certify:emit+=['--certify-converged-exits']
    if continuations:emit+=['--certify-native-continuations']
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
    if not isinstance(manifest,dict) or len(manifest)!=63 or REVIEWED_ROOTS_INPUT not in manifest or 'src/foundation_guide_data.h' not in manifest or 'src/foundation_current_data.h' not in manifest:
        raise ValueError('Expected63 authored inputs including reviewed roots, story-guide and Current advice data; preserve source')
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
    p.set_defaults(emit_proven_prefixes=True,reviewed_roots=True,certify_converged_exits=True,native_continuations=True,native_direct_calls=True)
    p.add_argument('--no-native-continuations',dest='native_continuations',action='store_false',help='Diagnostic: omit isolated native continuation certificates')
    p.add_argument('--no-native-direct-call-prefix',dest='native_direct_calls',action='store_false',help='Diagnostic: omit source-exact architectural direct JSR/JSL instruction rows; original callee scheduler ownership remains')
    p.add_argument('--no-proven-prefixes',dest='emit_proven_prefixes',action='store_false',help='Diagnostic: disable faithful prefix analysis')
    p.add_argument('--no-converged-exits',dest='certify_converged_exits',action='store_false',help='Diagnostic: retain original exit-fact quarantine without final re-certification')
    p.add_argument('--no-reviewed-roots',dest='reviewed_roots',action='store_false',help='Diagnostic: omit reviewed authored analysis seeds; retain baseline CFG roots')
    p.add_argument('--emit-proven-prefixes',action='store_true',help='Enable the distinct proved aot_prefix disposition via pinned v2_emit --faithful-prefixes; unknown calls continue in original code')
    p.add_argument('--runtime-cache-dir',type=Path,help='Reuse an explicit pinned runtime cache; all pinned ordered patch hashes choose a new key, old keys are preserved')
    p.add_argument('--sdl3-dir',type=Path,help='Optional existing SDL3 CMake package; otherwise upstream fetches SDL3')
    p.add_argument('--cmake',default='cmake');p.add_argument('--cc',default='clang');p.add_argument('--cxx',default='clang++')
    p.add_argument('--ninja',default='ninja');p.add_argument('--jobs',type=int,default=8)
    p.add_argument('--output-dir',type=Path,help='Optional new build directory; refuses an existing path. Default: local/source-builds/timestamp.')
    args=p.parse_args()
    validate_selected_task_recipe(ROOT/'native/foundation/recomp')
    validate_source_redirect_recipe(ROOT/'native/foundation/recomp')
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
    continuation_patch=out/'runtime-native-continuations.patch'
    shutil.copy2(ROOT/'patches/runtime-native-continuations.patch',continuation_patch)
    continuation_names=validate_continuation_patch(continuation_patch)
    rmw_patch=out/'runtime-memory-rmw.patch'
    shutil.copy2(ROOT/'patches/runtime-memory-rmw.patch',rmw_patch)
    rmw_names=validate_rmw_patch(rmw_patch)
    memory_bits_patch=out/'runtime-memory-bits.patch'
    shutil.copy2(ROOT/'patches/runtime-memory-bits.patch',memory_bits_patch)
    memory_bits_names=validate_memory_bits_patch(memory_bits_patch)
    native_regions_patch=out/'runtime-native-regions.patch'
    shutil.copy2(ROOT/'patches/runtime-native-regions.patch',native_regions_patch)
    native_regions_names=validate_native_regions_patch(native_regions_patch)
    leaf_regions_patch=out/'runtime-native-leaf-regions.patch'
    shutil.copy2(ROOT/'patches/runtime-native-leaf-regions.patch',leaf_regions_patch)
    leaf_regions_names=validate_leaf_regions_patch(leaf_regions_patch)
    hook_handoff_patch=out/'runtime-native-hook-handoff.patch'
    shutil.copy2(ROOT/'patches/runtime-native-hook-handoff.patch',hook_handoff_patch)
    hook_handoff_names=validate_hook_handoff_patch(hook_handoff_patch)
    stack_primitives_patch=out/'runtime-native-stack-primitives.patch'
    shutil.copy2(ROOT/'patches/runtime-native-stack-primitives.patch',stack_primitives_patch)
    stack_primitives_names=validate_stack_primitives_patch(stack_primitives_patch)
    return_steps_patch=out/'runtime-native-return-steps.patch'
    shutil.copy2(ROOT/'patches/runtime-native-return-steps.patch',return_steps_patch)
    return_steps_names=validate_return_steps_patch(return_steps_patch)
    prefix_instructions_patch=out/'runtime-native-prefix-instructions.patch'
    shutil.copy2(ROOT/'patches/runtime-native-prefix-instructions.patch',prefix_instructions_patch)
    prefix_instructions_names=validate_prefix_instructions_patch(prefix_instructions_patch)
    stack_controls_patch=out/'runtime-native-stack-controls.patch'
    shutil.copy2(ROOT/'patches/runtime-native-stack-controls.patch',stack_controls_patch)
    stack_controls_names=validate_stack_controls_patch(stack_controls_patch)
    selected_task_patch=out/'runtime-selected-task-resume.patch'
    shutil.copy2(ROOT/'patches/runtime-selected-task-resume.patch',selected_task_patch)
    selected_task_names=validate_selected_task_patch(selected_task_patch)
    source_redirect_patch=out/'runtime-source-redirect.patch'
    shutil.copy2(ROOT/'patches/runtime-source-redirect.patch',source_redirect_patch)
    source_redirect_names=validate_source_redirect_patch(source_redirect_patch)
    indirect_y_patch=out/'runtime-indirect-y.patch'
    shutil.copy2(ROOT/'patches/runtime-indirect-y.patch',indirect_y_patch)
    indirect_y_names=validate_indirect_y_patch(indirect_y_patch)
    task_callee_patch=out/'runtime-native-task-callee.patch'
    shutil.copy2(ROOT/'patches/runtime-native-task-callee.patch',task_callee_patch)
    task_callee_names=validate_task_callee_patch(task_callee_patch)
    stack_direct_patch=out/'runtime-stack-direct.patch'
    shutil.copy2(ROOT/'patches/runtime-stack-direct.patch',stack_direct_patch)
    stack_direct_names=validate_stack_direct_patch(stack_direct_patch)
    host_proof_idle_patch=out/'runtime-host-proof-idle.patch'
    shutil.copy2(ROOT/'patches/runtime-host-proof-idle.patch',host_proof_idle_patch)
    host_proof_idle_names=validate_host_proof_idle_patch(host_proof_idle_patch)
    redirect_observer_idle_patch=out/'runtime-redirect-observer-idle.patch'
    shutil.copy2(ROOT/'patches/runtime-redirect-observer-idle.patch',redirect_observer_idle_patch)
    redirect_observer_idle_names=validate_redirect_observer_idle_patch(redirect_observer_idle_patch)
    selected_case_patch=out/'runtime-selected-task-cases.patch'
    shutil.copy2(ROOT/'patches/runtime-selected-task-cases.patch',selected_case_patch)
    selected_case_names=validate_selected_case_patch(selected_case_patch)
    direct_call_patch=out/'runtime-direct-call-prefix.patch'
    shutil.copy2(ROOT/'patches/runtime-direct-call-prefix.patch',direct_call_patch)
    direct_call_names=validate_direct_call_patch(direct_call_patch)
    extension_patches=prepare_runtime_extension_patches(out)
    extension_names={name for value in runtime_extension_bindings()for name in value['files']}
    new_patch_names={'recompiler/v2/faithful_prefix.py','recompiler/v2/reviewed_roots.py','recompiler/v2/native_regions.py'}
    new_patch_names.update(name for name,record in selected_task_binding()['files'].items() if record['predecessor_sha256'] is None)
    new_patch_names.update(name for name,record in source_redirect_binding()['files'].items() if record['predecessor_sha256'] is None)
    new_patch_names.update(name for name,record in task_callee_binding()['files'].items()if record['predecessor_sha256']is None)
    new_patch_names.update(name for name,record in direct_call_binding()['files'].items()if record['predecessor_sha256']is None)
    new_patch_names.update(name for value in runtime_extension_bindings()for name,record in value['files'].items()if record['predecessor_sha256']is None)
    # A new patch gets its own checkout. Previously built or intentionally
    # modified runtimes remain available rather than being reset in place.
    cache_root=args.runtime_cache_dir.absolute() if args.runtime_cache_dir else ROOT/'local/upstream'
    reject_links(cache_root)
    cache_identity=runtime_cache_identity([sha(patch),sha(host_patch),sha(faithful_patch),sha(audio_patch),sha(automatic_patch),sha(lifecycle_patch),sha(prefix_patch),sha(hook_boundary_patch),sha(reviewed_patch),sha(converged_patch),sha(accumulator_patch),sha(continuation_patch),sha(rmw_patch),sha(memory_bits_patch),sha(native_regions_patch),sha(leaf_regions_patch),sha(hook_handoff_patch),sha(stack_primitives_patch),sha(return_steps_patch),sha(prefix_instructions_patch),sha(stack_controls_patch),sha(selected_task_patch),sha(source_redirect_patch),sha(indirect_y_patch),sha(task_callee_patch),sha(stack_direct_patch),sha(host_proof_idle_patch),sha(redirect_observer_idle_patch),sha(selected_case_patch),sha(direct_call_patch)]+[sha(p)for p in extension_patches])
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
    patch_names=sorted(set(re.findall(r'^diff --git a/(\S+) b/',patch.read_text(encoding='utf-8'),re.M))|set(host_names)|set(faithful_names)|set(audio_names)|set(automatic_names)|set(lifecycle_names)|set(prefix_names)|set(hook_boundary_names)|set(reviewed_names)|set(converged_names)|set(accumulator_names)|set(continuation_names)|set(rmw_names)|set(memory_bits_names)|set(native_regions_names)|set(leaf_regions_names)|set(hook_handoff_names)|set(stack_primitives_names)|set(return_steps_names)|set(prefix_instructions_names)|set(stack_controls_names)|set(selected_task_names)|set(source_redirect_names)|set(indirect_y_names)|set(task_callee_names)|set(stack_direct_names)|set(host_proof_idle_names)|set(redirect_observer_idle_names)|set(selected_case_names)|set(direct_call_names)|extension_names)
    if marker.exists():
        receipt=json.loads(marker.read_text(encoding='utf-8'))
        check_cache_marker_identity(receipt,cache_identity)
        check_faithful_hook_boundary_marker(receipt,sha(hook_boundary_patch))
        check_reviewed_roots_marker(receipt,sha(reviewed_patch))
        check_converged_exit_marker(receipt,sha(converged_patch))
        check_accumulator_marker(receipt,sha(accumulator_patch))
        if receipt.get('native_continuation_patch_sha256')!=sha(continuation_patch):
            raise RuntimeError('Native continuation marker missing/stale; preserve cache.')
        if receipt.get('memory_rmw_patch_sha256')!=sha(rmw_patch):
            raise RuntimeError('Memory RMW marker missing/stale; preserve cache.')
        if receipt.get('memory_bits_patch_sha256')!=sha(memory_bits_patch):
            raise RuntimeError('Memory bits marker missing/stale; preserve cache.')
        if receipt.get('native_regions_patch_sha256')!=sha(native_regions_patch):
            raise RuntimeError('Native regions marker missing/stale; preserve cache.')
        if receipt.get('native_leaf_regions_patch_sha256')!=sha(leaf_regions_patch):
            raise RuntimeError('Native leaf regions marker missing/stale; preserve cache.')
        if receipt.get('native_hook_handoff_patch_sha256')!=sha(hook_handoff_patch):
            raise RuntimeError('Native hook handoff marker missing/stale; preserve cache.')
        if receipt.get('native_stack_primitives_patch_sha256')!=sha(stack_primitives_patch):
            raise RuntimeError('Native stack primitive marker missing/stale; preserve cache.')
        if receipt.get('native_return_steps_patch_sha256')!=sha(return_steps_patch):
            raise RuntimeError('Native return step marker missing/stale; preserve cache.')
        if receipt.get('native_prefix_instructions_patch_sha256')!=sha(prefix_instructions_patch):
            raise RuntimeError('Native prefix instruction marker missing/stale; preserve cache.')
        if receipt.get('native_stack_controls_patch_sha256')!=sha(stack_controls_patch):
            raise RuntimeError('Native stack control marker missing/stale; preserve cache.')
        if receipt.get('selected_task_resume_patch_sha256')!=sha(selected_task_patch):raise RuntimeError('Selected task marker missing/stale; preserve cache.')
        if receipt.get('source_redirect_patch_sha256')!=sha(source_redirect_patch) or receipt.get('source_redirect_source_binding_sha256')!=sha(SOURCE_REDIRECT_BINDING):raise RuntimeError('Source redirect marker missing/stale; preserve cache.')
        if receipt.get('indirect_y_patch_sha256')!=sha(indirect_y_patch) or receipt.get('indirect_y_source_binding_sha256')!=sha(INDIRECT_Y_BINDING):raise RuntimeError('IndirectY marker missing/stale; preserve cache.')
        if receipt.get('task_callee_patch_sha256')!=sha(task_callee_patch) or receipt.get('task_callee_source_binding_sha256')!=sha(TASK_CALLEE_BINDING):raise RuntimeError('Task callee marker missing/stale; preserve cache.')
        if receipt.get('stack_direct_patch_sha256')!=sha(stack_direct_patch)or receipt.get('stack_direct_source_binding_sha256')!=sha(STACK_DIRECT_BINDING):raise RuntimeError('Stack direct marker missing/stale; preserve cache.')
        if receipt.get('host_proof_idle_patch_sha256')!=sha(host_proof_idle_patch)or receipt.get('host_proof_idle_source_binding_sha256')!=sha(HOST_PROOF_IDLE_BINDING):raise RuntimeError('Host proof idle marker missing/stale; preserve cache.')
        if receipt.get('redirect_observer_idle_patch_sha256')!=sha(redirect_observer_idle_patch)or receipt.get('redirect_observer_idle_source_binding_sha256')!=sha(REDIRECT_OBSERVER_IDLE_BINDING):raise RuntimeError('Redirect observer idle marker missing/stale; preserve cache.')
        if receipt.get('selected_task_case_patch_sha256')!=sha(selected_case_patch)or receipt.get('selected_task_case_source_binding_sha256')!=sha(SELECTED_CASE_BINDING):raise RuntimeError('Selected task case marker missing/stale; preserve cache.')
        if receipt.get('direct_call_prefix_patch_sha256')!=sha(direct_call_patch)or receipt.get('direct_call_prefix_source_binding_sha256')!=sha(DIRECT_CALL_BINDING):raise RuntimeError('Direct call marker missing/stale; preserve cache.')
        if receipt.get('runtime_extensions')!=runtime_extension_records():raise RuntimeError('Runtime extension marker missing/stale; preserve cache.')
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
        for name,record in continuation_binding()['files'].items():
            if sha(runtime/name)!=record['predecessor_sha256']:
                raise RuntimeError('Native continuation predecessor differs: '+name)
        command(['git','apply','--check',continuation_patch],runtime);command(['git','apply',continuation_patch],runtime)
        validate_continuation_runtime(runtime,normalize=True)
        for name,record in rmw_binding()['files'].items():
            reject_links(runtime/name)
            if sha(runtime/name)!=record['predecessor_sha256']:
                raise RuntimeError('Memory RMW predecessor differs: '+name)
            # Unified patch context is LF. Convert only bytes whose exact
            # predecessor hash was checked, including untouched upstream
            # helpers Git restored as CRLF on Windows.
            raw=(runtime/name).read_bytes()
            if b'\r\n' in raw:(runtime/name).write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',rmw_patch],runtime);command(['git','apply',rmw_patch],runtime)
        validate_final_runtime(runtime,normalize=True,memory_bits=False,native_regions=False)
        for name,record in memory_bits_binding()['files'].items():
            reject_links(runtime/name)
            if sha(runtime/name)!=record['predecessor_sha256']:
                raise RuntimeError('Memory bits predecessor differs: '+name)
        command(['git','apply','--check',memory_bits_patch],runtime);command(['git','apply',memory_bits_patch],runtime)
        validate_final_runtime(runtime,normalize=True,native_regions=False)
        for name,record in native_regions_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256'] is None:
                if path.exists():raise RuntimeError('New native region source already exists; preserve cache.')
                continue
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native region predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',native_regions_patch],runtime);command(['git','apply',native_regions_patch],runtime)
        validate_final_runtime(runtime,normalize=True,leaf_regions=False)
        for name,record in leaf_regions_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native leaf region predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',leaf_regions_patch],runtime);command(['git','apply',leaf_regions_patch],runtime)
        validate_final_runtime(runtime,normalize=True,hook_handoff=False)
        for name,record in hook_handoff_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native hook handoff predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',hook_handoff_patch],runtime);command(['git','apply',hook_handoff_patch],runtime)
        validate_final_runtime(runtime,normalize=True,stack_primitives=False)
        for name,record in stack_primitives_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native stack primitive predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',stack_primitives_patch],runtime);command(['git','apply',stack_primitives_patch],runtime)
        validate_final_runtime(runtime,normalize=True,return_steps=False)
        for name,record in return_steps_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native return step predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',return_steps_patch],runtime);command(['git','apply',return_steps_patch],runtime)
        validate_final_runtime(runtime,normalize=True,prefix_instructions=False)
        for name,record in prefix_instructions_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native prefix instruction predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',prefix_instructions_patch],runtime);command(['git','apply',prefix_instructions_patch],runtime)
        validate_final_runtime(runtime,normalize=True,stack_controls=False)
        for name,record in stack_controls_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:
                raise RuntimeError('Native stack control predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',stack_controls_patch],runtime);command(['git','apply',stack_controls_patch],runtime)
        validate_final_runtime(runtime,normalize=True,selected_task=False,source_redirect=False)
        for name,record in selected_task_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256'] is None:
                if path.exists():raise RuntimeError('New selected task source already exists: '+name)
                continue
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Selected task predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',selected_task_patch],runtime);command(['git','apply',selected_task_patch],runtime)
        validate_final_runtime(runtime,normalize=True,source_redirect=False)
        for name,record in source_redirect_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256'] is None:
                if path.exists():raise RuntimeError('New source redirect source already exists: '+name)
                continue
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Source redirect predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',source_redirect_patch],runtime);command(['git','apply',source_redirect_patch],runtime)
        validate_final_runtime(runtime,normalize=True,indirect_y=False)
        for name,record in indirect_y_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('IndirectY predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',indirect_y_patch],runtime);command(['git','apply',indirect_y_patch],runtime)
        validate_final_runtime(runtime,normalize=True,task_callee=False)
        for name,record in task_callee_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256']is None:
                if path.exists():raise RuntimeError('New task callee source already exists: '+name)
                continue
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Task callee predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n' in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',task_callee_patch],runtime);command(['git','apply',task_callee_patch],runtime)
        validate_final_runtime(runtime,normalize=True,stack_direct=False)
        for name,record in stack_direct_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Stack direct predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n'in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',stack_direct_patch],runtime);command(['git','apply',stack_direct_patch],runtime)
        validate_final_runtime(runtime,normalize=True,host_proof_idle=False)
        for name,record in host_proof_idle_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Host proof idle predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n'in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',host_proof_idle_patch],runtime);command(['git','apply',host_proof_idle_patch],runtime)
        validate_final_runtime(runtime,normalize=True,redirect_observer_idle=False)
        for name,record in redirect_observer_idle_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Redirect observer idle predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n'in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',redirect_observer_idle_patch],runtime);command(['git','apply',redirect_observer_idle_patch],runtime)
        validate_final_runtime(runtime,normalize=True,selected_case=False)
        for name,record in selected_case_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Selected task case predecessor differs: '+name)
            # Frozen071 C diff hunks retain exactCRLF; Python hunks retainLF.
            # Preserve the binding's exact predecessor representation for apply.
        command(['git','apply','--check',selected_case_patch],runtime);command(['git','apply',selected_case_patch],runtime)
        validate_final_runtime(runtime,normalize=True,direct_call=False)
        for name,record in direct_call_binding()['files'].items():
            path=runtime/name;reject_links(path)
            if record['predecessor_sha256']is None:
                if path.exists():raise RuntimeError('New direct call source already exists; preserve cache.')
                continue
            if sha(path)!=record['predecessor_sha256']:raise RuntimeError('Direct call predecessor differs: '+name)
            raw=path.read_bytes()
            if b'\r\n'in raw:path.write_bytes(raw.replace(b'\r\n',b'\n'))
        command(['git','apply','--check',direct_call_patch],runtime);command(['git','apply',direct_call_patch],runtime)
        validate_final_runtime(runtime,normalize=True,extensions=False)
        apply_runtime_extensions(runtime,extension_patches)
        validate_final_runtime(runtime,normalize=True)
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
          'native_continuation_patch_sha256':sha(continuation_patch),
          'memory_rmw_patch_sha256':sha(rmw_patch),
          'memory_bits_patch_sha256':sha(memory_bits_patch),
          'native_regions_patch_sha256':sha(native_regions_patch),
          'native_leaf_regions_patch_sha256':sha(leaf_regions_patch),
          'native_hook_handoff_patch_sha256':sha(hook_handoff_patch),
          'native_stack_primitives_patch_sha256':sha(stack_primitives_patch),
          'native_return_steps_patch_sha256':sha(return_steps_patch),
          'native_prefix_instructions_patch_sha256':sha(prefix_instructions_patch),
          'native_stack_controls_patch_sha256':sha(stack_controls_patch),
          'selected_task_resume_patch_sha256':sha(selected_task_patch),
          'selected_task_resume_source_binding_sha256':sha(SELECTED_TASK_BINDING),
          'source_redirect_patch_sha256':sha(source_redirect_patch),
          'source_redirect_source_binding_sha256':sha(SOURCE_REDIRECT_BINDING),
          'indirect_y_patch_sha256':sha(indirect_y_patch),
          'indirect_y_source_binding_sha256':sha(INDIRECT_Y_BINDING),
          'task_callee_patch_sha256':sha(task_callee_patch),
          'task_callee_source_binding_sha256':sha(TASK_CALLEE_BINDING),
          'stack_direct_patch_sha256':sha(stack_direct_patch),
          'stack_direct_source_binding_sha256':sha(STACK_DIRECT_BINDING),
          'host_proof_idle_patch_sha256':sha(host_proof_idle_patch),
          'host_proof_idle_source_binding_sha256':sha(HOST_PROOF_IDLE_BINDING),
          'redirect_observer_idle_patch_sha256':sha(redirect_observer_idle_patch),
          'redirect_observer_idle_source_binding_sha256':sha(REDIRECT_OBSERVER_IDLE_BINDING),
          'selected_task_case_patch_sha256':sha(selected_case_patch),
          'selected_task_case_source_binding_sha256':sha(SELECTED_CASE_BINDING),
          'direct_call_prefix_patch_sha256':sha(direct_call_patch),
          'direct_call_prefix_source_binding_sha256':sha(DIRECT_CALL_BINDING),
          'runtime_extensions':runtime_extension_records(),
          'new_patched_sources':sorted(new_patch_names),
          'patched_sources':{n:sha(runtime/n) for n in patch_names}})
    validate_final_runtime(runtime)
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
    generates=generation_commands(runtime,project,rom,identity,profile_snapshots,args.emit_proven_prefixes,args.reviewed_roots,args.certify_converged_exits,args.native_continuations,args.native_direct_calls)
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
    if generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache'] or generated_metadata.get('module')!={'id':'main','prefix':''}or generated_metadata.get('outputs',{}).get('program_manifest.json')!=sha(automatic_manifest_path):
        raise RuntimeError('Target generated cache/module identity mismatch; preserve build.')
    if set(generated_metadata.get('outputs',{}))!=set(('bank00_v2.c', 'bank01_part00_v2.c', 'bank01_part01_v2.c', 'bank01_part02_v2.c', 'bank01_part03_v2.c', 'bank01_part06_v2.c', 'bank01_part08_v2.c', 'bank01_part09_v2.c', 'bank01_part0a_v2.c', 'bank01_part0b_v2.c', 'bank01_part0c_v2.c', 'bank01_part0d_v2.c', 'bank01_part0e_v2.c', 'bank02_v2.c', 'bank1c_v2.c', 'dispatch_v2.c', 'module_v2.c', 'native_regions.json', 'native_regions_v2.c', 'native_source_redirect.json', 'native_source_redirect_v2.c', 'native_task_resume.json', 'native_task_resume_v2.c', 'program_manifest.json', 'unresolved_stubs_v2.c')):raise RuntimeError('Source-first25 generated output allowlist differs.')
    for name,digest in generated_metadata.get('outputs',{}).items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise RuntimeError('Target generated output escapes build; preserve build.')
        output=project/'src/gen'/name;reject_links(output)
        if sha(output)!=digest:raise RuntimeError('Target generated output/cache mismatch; preserve build.')
    validate_selected_task_recipe(ROOT/'native/foundation/recomp')
    validate_source_redirect_recipe(ROOT/'native/foundation/recomp')
    selected_task_metadata=validate_selected_task_outputs(project/'src/gen',generated_metadata,expected,rom)
    source_redirect_metadata=validate_source_redirect_outputs(project/'src/gen',generated_metadata,expected,rom)
    region_metadata_path=project/'src/gen/native_regions.json'
    region_source_path=project/'src/gen/native_regions_v2.c'
    reject_links(region_metadata_path);reject_links(region_source_path)
    region_metadata=json.loads(region_metadata_path.read_bytes())
    if region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal'] or region_metadata.get('result_contract')!='full_pc24_transient_original_scheduler' or region_metadata.get('instruction_source')!='source_faithful_and_typed_architectural_before_activation_plumbing' or region_metadata.get('stack_control_contract')!='native-e0-typed-architectural-stack-v1' or region_metadata.get('kind')!='source_cfg_scheduler_instruction' or region_metadata.get('rom_sha256')!=expected or not isinstance(region_metadata.get('regions'),list):
        raise RuntimeError('Target native-region metadata identity mismatch; preserve build.')
    if generated_metadata.get('outputs',{}).get('native_regions.json')!=sha(region_metadata_path) or generated_metadata.get('outputs',{}).get('native_regions_v2.c')!=sha(region_source_path):
        raise RuntimeError('Target native-region output/cache mismatch; preserve build.')
    reset_bootstrap_generation=validate_reset_bootstrap_outputs(project/'src/gen',generated_metadata,expected,rom)
    direct_call_metadata=validate_direct_call_outputs(project/'src/gen',generated_metadata,expected,rom,args.native_direct_calls)
    indirect_y_generation=validate_indirect_y_outputs(project/'src/gen',generated_metadata,expected,rom)
    stack_direct_metadata=validate_stack_direct_outputs(project/'src/gen',generated_metadata,expected,rom)
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
      'native_continuation_patch_sha256':sha(continuation_patch),
      'native_continuation_source_binding_sha256':sha(CONTINUATION_BINDING),
      'native_continuation_scope':continuation_binding()['scope'],
      'memory_rmw_patch_sha256':sha(rmw_patch),
      'memory_rmw_source_binding_sha256':sha(RMW_BINDING),
      'memory_rmw_scope':rmw_binding()['scope'],
      'memory_bits_patch_sha256':sha(memory_bits_patch),
      'native_regions_patch_sha256':sha(native_regions_patch),
          'native_leaf_regions_patch_sha256':sha(leaf_regions_patch),
          'native_hook_handoff_patch_sha256':sha(hook_handoff_patch),
          'native_stack_primitives_patch_sha256':sha(stack_primitives_patch),
          'native_return_steps_patch_sha256':sha(return_steps_patch),
          'native_prefix_instructions_patch_sha256':sha(prefix_instructions_patch),
          'native_stack_controls_patch_sha256':sha(stack_controls_patch),
          'selected_task_resume_patch_sha256':sha(selected_task_patch),
      'memory_bits_source_binding_sha256':sha(MEMORY_BITS_BINDING),
      'memory_bits_scope':memory_bits_binding()['scope'],
      'native_regions_source_binding_sha256':sha(NATIVE_REGIONS_BINDING),
      'native_regions_scope':native_regions_binding()['scope'],
      'native_leaf_regions_source_binding_sha256':sha(LEAF_REGIONS_BINDING),
      'native_leaf_regions_scope':leaf_regions_binding()['scope'],
      'native_hook_handoff_source_binding_sha256':sha(HOOK_HANDOFF_BINDING),
      'native_hook_handoff_scope':hook_handoff_binding()['scope'],
      'native_stack_primitives_source_binding_sha256':sha(STACK_PRIMITIVES_BINDING),
      'native_stack_primitives_scope':stack_primitives_binding()['scope'],
      'native_return_steps_source_binding_sha256':sha(RETURN_STEPS_BINDING),
      'native_return_steps_scope':return_steps_binding()['scope'],
      'native_prefix_instructions_source_binding_sha256':sha(PREFIX_INSTRUCTIONS_BINDING),
      'native_prefix_instructions_scope':prefix_instructions_binding()['scope'],
      'native_stack_controls_source_binding_sha256':sha(STACK_CONTROLS_BINDING),
      'native_stack_controls_scope':stack_controls_binding()['scope'],
      'selected_task_resume_source_binding_sha256':sha(SELECTED_TASK_BINDING),
      'selected_task_resume_scope':selected_task_binding()['scope'],
      'source_redirect_patch_sha256':sha(source_redirect_patch),
      'source_redirect_source_binding_sha256':sha(SOURCE_REDIRECT_BINDING),
      'source_redirect_scope':source_redirect_binding()['scope'],
      'indirect_y_patch_sha256':sha(indirect_y_patch),
      'indirect_y_source_binding_sha256':sha(INDIRECT_Y_BINDING),
      'indirect_y_scope':indirect_y_binding()['scope'],
      'redirect_observer_idle_patch_sha256':sha(redirect_observer_idle_patch),
      'redirect_observer_idle_source_binding_sha256':sha(REDIRECT_OBSERVER_IDLE_BINDING),
      'selected_task_case_patch_sha256':sha(selected_case_patch),
      'selected_task_case_source_binding_sha256':sha(SELECTED_CASE_BINDING),
      'direct_call_prefix_patch_sha256':sha(direct_call_patch),
      'direct_call_prefix_source_binding_sha256':sha(DIRECT_CALL_BINDING),
      'redirect_observer_idle_scope':redirect_observer_idle_binding()['scope'],
      'selected_task_case_scope':selected_case_binding()['scope'],
      'direct_call_prefix_scope':direct_call_binding()['scope'],
      'host_proof_idle_patch_sha256':sha(host_proof_idle_patch),
      'host_proof_idle_source_binding_sha256':sha(HOST_PROOF_IDLE_BINDING),
      'host_proof_idle_scope':host_proof_idle_binding()['scope'],
      'stack_direct_patch_sha256':sha(stack_direct_patch),
      'stack_direct_source_binding_sha256':sha(STACK_DIRECT_BINDING),
      'stack_direct_scope':stack_direct_binding()['scope'],
      'stack_direct_generation':stack_direct_metadata,
      'task_callee_patch_sha256':sha(task_callee_patch),
      'task_callee_source_binding_sha256':sha(TASK_CALLEE_BINDING),
      'task_callee_scope':task_callee_binding()['scope'],
      'indirect_y_generation':indirect_y_generation,
      'source_redirect_generation':{'metadata_format':1,'mode_rows':len(source_redirect_metadata['rows']),'distinct_pcs':len({r['pc24']for r in source_redirect_metadata['rows']}),'metadata_sha256':sha(project/'src/gen/native_source_redirect.json'),'source_sha256':sha(project/'src/gen/native_source_redirect_v2.c'),'execution_qualified':False},
      'selected_task_resume_generation':{'metadata_format':RUNTIME_GENERATION_FORMATS['task'],'mode_rows':len(selected_task_metadata['rows']),'distinct_pcs':len({r['pc24']for r in selected_task_metadata['rows']}),'metadata_sha256':sha(project/'src/gen/native_task_resume.json'),'source_sha256':sha(project/'src/gen/native_task_resume_v2.c'),'execution_qualified':False},
      'direct_call_prefix_generation':direct_call_metadata,
      'reset_bootstrap_generation':reset_bootstrap_generation,
      'native_region_generation':{'cache_format':RUNTIME_GENERATION_FORMATS['cache'],'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'stack_control_contract':region_metadata['stack_control_contract'],'result_contract':region_metadata['result_contract'],'instruction_source':region_metadata['instruction_source'],'source_cfg_scheduler_rows':len(region_metadata['regions']),'metadata_sha256':sha(region_metadata_path),'source_sha256':sha(region_source_path),'diagnostic_disable':'SNESRECOMP_DISABLE_NATIVE_REGIONS=1','execution_qualified':False},
      'runtime_accumulator_patch_sha256':sha(accumulator_patch),'runtime_accumulator_emitter_sha256':ACCUMULATOR_EMITTER_SHA256,'runtime_accumulator_source_review':{'offline_unit_report_sha256':ACCUMULATOR_UNIT_SHA256,'scope':'Pinned reviewed offline instruction/source proof; public Setup does not consume private fixtures or infer actual-artifact gameplay qualification.'},
      'runtime_accumulator_source_lineage':accumulator_lineage,
      'runtime_accumulator_patch_scope':'Exact one-byte ASL/LSR/ROL/ROR accumulator admission through existing faithful bodies. MemoryRMW/INC/DEC/refusals and original buses/timing/ABI remain.',
      'version':(project/'VERSION').read_text().strip(),'rom_sha256':expected,'rom_copied':False,
      'authored_inputs':actual,'matches_authored_snapshot':actual==manifest,
      'runtime_pin':RUNTIME_PIN,'runtime_patch_sha256':sha(patch),
      'runtime_extensions':runtime_extension_records(),
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
          'native_continuations':args.native_continuations,
          'native_direct_call_prefix':args.native_direct_calls,'direct_call_generator_option':'--native-direct-call-prefix','direct_call_diagnostic_optout':'--no-native-direct-call-prefix',
          'native_mode_successors':True,'mode_successor_generator_option':'--native-mode-successors',
          'mode_successor_contract':region_metadata['mode_successor_contract'],
          'native_continuation_certificates':len(automatic_manifest.get('native_continuations',[])),
          'native_continuation_generator_option':'--certify-native-continuations',
          'native_continuation_diagnostic_optout':'--no-native-continuations',
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
                  'SNESRECOMP_DISABLE_NATIVE_CONTINUATIONS':'1',
                  'SNESRECOMP_DISABLE_NATIVE_REGIONS':'1',
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


# The sequential validation graph revisits earlier bindings. Cache its pure
# decoded results for this invocation, while checking every binding file at
# each outer request so a cached descendant cannot conceal a changed ancestor.
_binding_inputs={str(path):(path,sha(path))for name,path in tuple(globals().items())if name.endswith('_BINDING')and isinstance(path,Path)}
for _spec in RUNTIME_EXTENSION_SPECS:
    _path=ROOT/'patches'/(_spec['name']+'.json')
    _binding_inputs[str(_path)]=(_path,sha(_path))
_binding_validation_depth=0

def _check_binding_inputs():
    for path,digest in _binding_inputs.values():
        reject_links(path)
        if sha(path)!=digest:raise RuntimeError('A source binding changed during validation; preserve build: '+str(path))

def _cache_binding_result(fn):
    cached=[]
    def checked():
        global _binding_validation_depth
        outer=_binding_validation_depth==0
        if outer:_check_binding_inputs()
        _binding_validation_depth+=1
        try:
            if not cached:cached.append(fn())
            return cached[0]
        finally:
            _binding_validation_depth-=1
            if outer:_check_binding_inputs()
    checked.__name__=fn.__name__
    return checked

for _name in ('continuation_binding','rmw_binding','memory_bits_binding','native_regions_binding','leaf_regions_binding','hook_handoff_binding','stack_primitives_binding','return_steps_binding','prefix_instructions_binding','stack_controls_binding','selected_task_binding','source_redirect_binding','indirect_y_binding','task_callee_binding','stack_direct_binding','host_proof_idle_binding','redirect_observer_idle_binding','selected_case_binding','direct_call_binding'):
    globals()[_name]=_cache_binding_result(globals()[_name])

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,OSError,KeyError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
