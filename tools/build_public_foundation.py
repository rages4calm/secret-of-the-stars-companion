"""Build a fresh developer foundation from authored source and a supplied ROM.

Never copies the ROM into the repository, publishes generated code, installs
over an owner profile, or invents a gameplay qualification receipt.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time
from dataclasses import dataclass

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
RUNTIME_EXTENSION_SPECS = ({'name': 'runtime-original-call-retention', 'patch_sha256': 'f89a5e4b7fc3716f4a440353cc1392a3fcb4ee003fc671f033e3ed30fd09b985', 'binding_sha256': '74fd49aad510fbc0f4d3a3e97b7bef768ad56c3913ab171d9c731a18f8c7236f', 'files': ['recompiler/v2/codegen.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_call_prefix.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_original_calls.py', 'recompiler/v2/task_resume.py', 'runner/src/common_rtl.c', 'runner/src/cpu_state.c', 'runner/src/cpu_state.h', 'runner/src/desktop/host_main.c', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/interp816.c', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/snes.c', 'runner/src/task_original_call_contract.h', 'runner/src/task_original_call_contract.inc'], 'new_files': ['recompiler/v2/task_original_calls.py', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/task_original_call_contract.h', 'runner/src/task_original_call_contract.inc'], 'unpatched_predecessors': {'recompiler/v2/codegen.py': '808a83ac6db1dbac912de8d30ca8ef10028e8b65978c153cbc8391a5e22cbbf0', 'recompiler/v2/emit_function.py': '42a3bb0ddf73a3e5db7757a6bd8919a8d36558a249f18dcc202c5083ee4db1a2', 'recompiler/v2/native_call_prefix.py': '9e7488609a26bff99600e21dbcc65d093d3ace1b1f4f43c26ea87fe08eef08dc', 'recompiler/v2/native_regions.py': 'b2dcb0b24b013f2543e91e2a6d11475a474b71d4012cc42214e5ba2294b42268', 'recompiler/v2/program_emit.py': 'f7799a49fd4d331d74ecf5ef2ed347eb4866229406c7a5614f821dd76f624f6a', 'recompiler/v2/task_resume.py': '891b92e35838dcb348cef1ca43635053f15c26dc294d5e3a371bef99cc2b3e30', 'runner/src/common_rtl.c': 'e2146f5de96ff2a236de50f275525e10a7ad038f06448c9c06c38e9d3179ddb1', 'runner/src/cpu_state.c': '0a4b53ca254dd66aa81d0d232fc7ad3d29fb2a8739be16820a83c4129c4de7f7', 'runner/src/cpu_state.h': 'f045d10a22df9d2df8bc898da16d5032166e59744ed49c72aaa5286336d409c4', 'runner/src/desktop/host_main.c': '06adadb980c4eccb4393a3f2abdd258503b1647f66b795bb7bd7a32d517a52f4', 'runner/src/snes/bridge_task_call.inc': 'f470728c8b39ff9767f01da473de9c9f173d473635c466bd9b324c59ca93fe74', 'runner/src/snes/bridge_task_helpers.inc': '86569e088973f03df80407ee37f687f6bc1b74d094b2054d20c2203561c46583', 'runner/src/snes/interp816.c': '658acf8afdac221e02b4eb7672512403c2a5c15f0d27c4822f2411d4451ab665', 'runner/src/snes/interp_bridge.c': '411b6e034dd60cca43010cd999345c6fb45f6572404db4c5937e550337468224', 'runner/src/snes/snes.c': '08dc7f6ab2d38a027bed9251ec1de5f03f9f23866eb2f2f0167b309e6da33245'}, 'metadata': {'cache_format': 22, 'normal_metadata': 9, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-long-jump-stack-indirect-y', 'patch_sha256': 'ec77e0a198c56713763920c1346aa80e7342d7c54d8c055633175781629afeb1', 'binding_sha256': '03c0e6a3c5a28c5aa84d68218ef5e82a6e875c284d6fa66e8ba96faf88dee885', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '4d1e7fcea904e6c48137873ff335600064e51b2a7ec4b434bfd49c4c49980c76', 'recompiler/v2/native_regions.py': 'd7dc1fad195254c9e4477c0378fc00205d61c454334d711490cf859fa4a31b61', 'recompiler/v2/program_emit.py': '2779e661158a722dade40df67883d8dd852ad229ea23cad19beb412fa5357526', 'runner/src/cpu_state.h': 'a9c719580ebaa01f458d383512a89789d0f733abd54888db76125e7d75e71afd', 'runner/src/snes/interp_bridge.c': 'b5979f45857400eaa8127b00c545e5f62b21bed100b02cb87f768d690c1ab478'}, 'metadata': {'cache_format': 23, 'normal_metadata': 10, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-indirect-control', 'patch_sha256': '2b723cefdf7faa6dccad43702281a0fce561277a89900b69b4e8a52968bf5474', 'binding_sha256': '7a07b9f335179b41cb0806dbfe375dc8381646fd3612aca3d03dfe1cf216f2f1', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_indirect_control.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_indirect_control.py'], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '4d678e1baef47e68d0e8db122a7c52b7908e0a32885a77b68748117b64b7231d', 'recompiler/v2/program_emit.py': 'a94ac9107d4302480544ebf921269d01bd792de32e71d059db39a50840a952a7', 'runner/src/cpu_state.h': 'c8b7bc9e132b83e3e2e56b9b6a42d24f8ad7141c4e4301b16291ec6e379e092b', 'runner/src/snes/interp_bridge.c': '1f5345cfdabd7e90040351dc118ea1ffc2e9fa9518baf076632ff40fe1c6fee0'}, 'metadata': {'cache_format': 24, 'normal_metadata': 11, 'task_metadata': 4, 'redirect_metadata': 1}}, {'name': 'runtime-task-original-prefix', 'patch_sha256': 'b992641a8e331dab5f1c2edd7e5c7349163e150ba537179793cbd47c53a56683', 'binding_sha256': 'b3b92cdd08008832fff1caac30f586626e0dcc3e60534831ed6c3417dedac8bc', 'files': ['recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py', 'runner/src/cpu_state.h', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'recompiler/v2/program_emit.py': '55f4d98b9e9f84d0841f7aa57f71424dc75a91e793fbabc9422e1bc6915a87f8', 'recompiler/v2/task_resume.py': '07e5996369b4705e3dff34456730b953245d840f9cb1a99b850710b535a5c554', 'runner/src/cpu_state.h': 'cc3028ac50395b4da840d2f6bc3f43a6da841b2381cc3f84ebf4583a746fe59a', 'runner/src/snes/bridge_task_call.inc': '23248f7c92e1d025f3c2121732d8a9d9657d4848efa053d747d12b3b4e520b41', 'runner/src/snes/bridge_task_original_runtime.inc': 'fc2c3cd95cbda3ef4a6c9b7052378ada8c0e10445c35c79ac44a6afb8d311ed6', 'runner/src/snes/interp_bridge.c': '905b2e047797c39ef9407e6ed2f024481e1775ab71705842e748477e180380e0'}, 'metadata': {'cache_format': 25, 'normal_metadata': 11, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-interrupt-return', 'patch_sha256': '75926f688cc3dbd6dccc4ce3446976b0f6307f93c212533dae5bb25248d071a1', 'binding_sha256': '3ba0770eb6d5f13ae1a794bb7365ebe1f06ddb117ff2172786ee40b56efe3f10', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_interrupt_return.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_interrupt_return.py'], 'unpatched_predecessors': {'recompiler/v2/emit_function.py': '02cf21790a4327524359b3ca504381f4a60cb76277ab816aaa0d941a16dcdb4b', 'recompiler/v2/program_emit.py': 'fe4ed2d530e308b814443c7bfa4419c7eeda2e01a6d0c3a0bd769fe7a081c265', 'runner/src/snes/interp_bridge.c': '0f0518b919603954cd89325a6e4cb5f9c5f12f9b3ded1bb860424bd1a7fc03b2'}, 'metadata': {'cache_format': 26, 'normal_metadata': 12, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-carry-emulation-exchange', 'patch_sha256': '629f510383cd70654d8a43fefe5eec30918a42ee8c7bdbb5343280ebe48a8075', 'binding_sha256': 'a7b94a2a879b6c19e432fc4b896e6159c286f47ee0541a71baf623422175e7b5', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_exchange.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/native_exchange.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 27, 'normal_metadata': 13, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-blockmove', 'patch_sha256': '0a1b15776666a61e2bbedd653fa658298314a2004869963d718061605d092570', 'binding_sha256': '6711b5cfcfdff92c5603784123fcaf16e48f47c7d34cf52f625aea1626567512', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_blockmove.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_blockmove.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 28, 'normal_metadata': 14, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-reset-bootstrap-emulation', 'patch_sha256': '6edc8dfe64015c9c896382627708cfb41db0b6ae5b8e3a6e55b62a1080dc1df9', 'binding_sha256': 'f428d6b7e01959c1de0a9b6ad1168754023b15659830b3d48d7dcacff9a6f199', 'files': ['recompiler/v2/native_bootstrap.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'runner/src/cpu_state.h', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/native_bootstrap.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 29, 'normal_metadata': 15, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-mode-successors', 'patch_sha256': 'b665988c08e87e23bb07da2cf9e7b0d40fcb61a10372fa1d933d2c0aaf851e08', 'binding_sha256': 'cb526acc78c3c26fad6e24fed58c6b6771325dfa1478e693dbb1d7372cb0bfc7', 'files': ['recompiler/v2/decoder.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_mode_successors.py', 'recompiler/v2/program_emit.py', 'tools/v2_emit.py'], 'new_files': ['recompiler/v2/native_mode_successors.py'], 'unpatched_predecessors': {'recompiler/v2/decoder.py': '155edb7da1b0398109d0b00d9ad472f5d9d46e89a79d7f2a713d290db7af708e', 'recompiler/v2/emit_bank.py': '003fbdba518e04145fbcde95e05694173915e602ed85df853dc3feb5ff670fe0', 'tools/v2_emit.py': 'fb7b1a3155618da2fa2f71a6a578fbbb61ae758b88339cde84bafb4d3f354866'}, 'metadata': {'cache_format': 30, 'normal_metadata': 16, 'task_metadata': 5, 'redirect_metadata': 1}}, {'name': 'runtime-source-suspend', 'patch_sha256': 'd833d7dc406ea9d4eb7c93c85af212522782d800ca2f1991ab1aa21e387eb1f4', 'binding_sha256': '7c547ed65e281fae59b304f5f93fed78259f80c5b8630139f2f28993c708b9b3', 'files': ['recompiler/v2/emit_function.py', 'recompiler/v2/native_regions.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/source_redirect.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/task_suspend.py', 'runner/src/common_rtl.c', 'runner/src/cpu_state.c', 'runner/src/cpu_state.h', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_original_runtime.inc', 'runner/src/snes/bridge_task_suspend.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/snes.c', 'runner/src/task_resume_contract.inc', 'runner/src/task_suspend_lineage.h', 'runner/src/task_suspend_lineage.inc'], 'new_files': ['recompiler/v2/task_suspend.py', 'runner/src/snes/bridge_task_suspend.inc', 'runner/src/task_suspend_lineage.h', 'runner/src/task_suspend_lineage.inc'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 31, 'normal_metadata': 16, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-architecture-eligibility', 'patch_sha256': '49127b9014e96faa4d2cc50d1515bc29d4f5d6d78c81e48201ff89caedfaa368', 'binding_sha256': '216ba88dcc9d792fb10c050e66f3090d0bff0249187d8a1f6d4254b9055db4d8', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_ff20_sources.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_ff20_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 32, 'normal_metadata': 17, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-turbo-cadence', 'patch_sha256': 'cfb88676320da4f5ae5f1144e5814a307ecc70c689ed48ba13dc6d6964859dc7', 'binding_sha256': '7495d2b5cfb54642b6d53c38e8d6de2d24f440b5f3abaa0b7d5a216caafcd817', 'files': ['runner/src/common_rtl.c', 'runner/src/common_rtl.h', 'runner/src/desktop/host_main.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/common_rtl.h': 'f6efb33932de8c1adf8d23b1313d3d3af79fc17f30d2e634240e05750d0d6ad8'}, 'metadata': {'cache_format': 32, 'normal_metadata': 17, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-return-instructions', 'patch_sha256': '450ce03ce31486317ad2108cce99a80e6c119ccf3f760f8862bb11baaf4a8fad', 'binding_sha256': '136906a9a6e78c321870d0cf8bba1c19075a3acde5e04387a500d0dc1c10ce27', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_return_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_return_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 33, 'normal_metadata': 18, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-callee-instructions', 'patch_sha256': '9070328b96b9df5c2a32f73c2d927c4ef5467993718d9fc197957740f5efa4c6', 'binding_sha256': '131021104fd513c11750348fd4cef24fa28c4472d2c38ab55c97bfe051dbfb70', 'files': ['recompiler/v2/architecture_callee_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_callee_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 34, 'normal_metadata': 19, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-dynamic-p-instructions', 'patch_sha256': 'c3a2205226e3594f163ae6252f26e9433ab6ddb98824600e5b7769592c64e16c', 'binding_sha256': '76d70ff5f6b58158dff0c945af6c64670f3ed7bc02f4bee0e0c728780b3dbe0e', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_mode_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_mode_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 35, 'normal_metadata': 20, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-nested-instructions', 'patch_sha256': '65bb7bfed0c31b7b7f03c04441344a1aa9a1e46d55b7416246110ecb38f1f2ac', 'binding_sha256': '27beaefc7a9dcb997f88c8115a29784e6a3022e7151910d7d9aaae663ee474f7', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_nested_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_nested_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 36, 'normal_metadata': 21, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-frontier-dynamic-p', 'patch_sha256': '5486f4d47dc5ccb4cc0bc686d1e044c471d85bc142316c8dcbdf2380b7e77348', 'binding_sha256': '15f03ed4f721e84ee8c2a8118b6ae2e33c721f0844a4f8369949636159665627', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_frontier_mode_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_frontier_mode_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 37, 'normal_metadata': 22, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-source-return-steps', 'patch_sha256': '0e0b689fb492bb1369077fb09161f9bb18f0d1ab1acbefa40c6ffdca977c6bab', 'binding_sha256': 'dd0103e5ef9e8136d136726796a04606af63918a083db90012bf0f06e5d87981', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_return_steps.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_return_steps.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 38, 'normal_metadata': 23, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-aftercall-source-closure', 'patch_sha256': '3a85c417735b1bd306249997309ef9bb84edd03d696b5c5d2e9429ced253b8cb', 'binding_sha256': '1173e66d76c869542ba579fbf9e97824f3e7dd6e9d51a425b45dbced923417b3', 'files': ['recompiler/v2/architecture_aftercall_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_aftercall_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 39, 'normal_metadata': 24, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-callable-progress', 'patch_sha256': 'ee55a567f53c2ae3e8a81755bda7954a3b835d19bad8cc56db84156e243cce45', 'binding_sha256': '3cc05733c99b159cad095ad5403b00c7cf1e80c0489db97a92fde5dfb97a1bd0', 'files': ['runner/src/snes/bridge_callable_progress120.inc', 'runner/src/snes/interp_bridge.c'], 'new_files': ['runner/src/snes/bridge_callable_progress120.inc'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 39, 'normal_metadata': 24, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-aftercall-dynamic-p', 'patch_sha256': '60f125101ac09a19597b603b447d94c1a12184489939dd6b4e5bf398962bb086', 'binding_sha256': 'cc4cfefeaf592fae00fe9a4fdbcb44281b8b3400ed610cc16a9a836f6c49485c', 'files': ['recompiler/v2/architecture_aftercall_mode_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_aftercall_mode_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 40, 'normal_metadata': 25, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-aftercall-return-steps', 'patch_sha256': '6b9b70845fba69f83d767bf9b46589faa4c890925fe2a9cd28b10e322fbe0448', 'binding_sha256': 'a9293f1e82cb43b2da71f5d736c7aab1f34a5fb77701a344538629416103fe29', 'files': ['recompiler/v2/architecture_return_steps.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 40, 'normal_metadata': 25, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-program-call-closure', 'patch_sha256': '02850a53c3ab8ea3325c47af212fbbfe9227a4288b917799dd640bcc553a3152', 'binding_sha256': '4eb27f737c789efca37600ab08101f71956b39c160769b207e33b2dbaa64ed6d', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_program_call_sources.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_program_call_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 41, 'normal_metadata': 26, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-program-dynamic-p', 'patch_sha256': '83a9952d653f6093f1c95852f9387c8fb46cc4fccf81b73d17bcb714266fb87f', 'binding_sha256': 'c93de89cb9ab11a8435a5f56b65543e92ddc25d0d75ef41361e88dbcdfa50515', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_program_mode_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_program_mode_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 42, 'normal_metadata': 27, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-emission-bank-policy', 'patch_sha256': '7f0f267443396966a0221d56dca551bcba8c395c29c6e22898fd4d83bb39c137', 'binding_sha256': '367f984ab2fe5d5cf917a0c08d7fcc5f1ced82c6893796d288f326ae3d38f4b7', 'files': ['recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_program_call_sources.py', 'recompiler/v2/architecture_program_mode_sources.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_mode_successors.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_emission_policy.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 43, 'normal_metadata': 28, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-combined-frontier-returns', 'patch_sha256': '9be41b96abd51f81cca9b6bcb2a35fa076e9f544e425d52d517b07cc1f107b16', 'binding_sha256': '36f31d1030f5e2c2088fad1949cb5d0353f1f7c39caad2a6536dfd8a4d46a5f8', 'files': ['recompiler/v2/architecture_architectural_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_program_call_sources.py', 'recompiler/v2/architecture_program_mode_sources.py', 'recompiler/v2/architecture_program_return_sources.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/native_reserved_wdm.py', 'recompiler/v2/program_emit.py', 'runner/src/snes/interp_bridge.c'], 'new_files': ['recompiler/v2/architecture_architectural_sources.py', 'recompiler/v2/architecture_program_return_sources.py', 'recompiler/v2/native_reserved_wdm.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 44, 'normal_metadata': 29, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-task-pure-instructions', 'patch_sha256': 'd29219e692a2b7f4f3050ca1aecaae6d3666ae1b402ab70b62dc15b4d5387aa8', 'binding_sha256': 'f703651bda6e515bc9db1e116dd31e11d49eb049bf9b4f1320348fdd1c06da69', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_task_sources.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py'], 'new_files': ['recompiler/v2/architecture_task_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 45, 'normal_metadata': 30, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-combined-rom-task-members', 'patch_sha256': 'f282b1b84704020de50091065c4eb942cf7736278a6769166b18d8ca49c9aa2c', 'binding_sha256': '6644647c74ee47442d622716ed734f6d0e88e64c278d82a0efa5f7a9ab426f91', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_rom_stack_dispatch_sources.py', 'recompiler/v2/architecture_task_member_sources.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py'], 'new_files': ['recompiler/v2/architecture_rom_stack_dispatch_sources.py', 'recompiler/v2/architecture_task_member_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 46, 'normal_metadata': 31, 'task_metadata': 6, 'redirect_metadata': 1}}, {'name': 'runtime-combined-initial-selected-task', 'patch_sha256': 'f56312d53e80e3d98cf03ba731ee405a963f50c3bb2488fcd5e503de531b86fe', 'binding_sha256': '590d57de7c43a2e2f8dc870def166e685b4b8c7918ecb447315ac4c095fc505d', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_initial_task_sources.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/task_selected_member_sources.py', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/task_selected_member_contract.h'], 'new_files': ['recompiler/v2/architecture_initial_task_sources.py', 'recompiler/v2/task_selected_member_sources.py', 'runner/src/task_selected_member_contract.h'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 47, 'normal_metadata': 32, 'task_metadata': 7, 'redirect_metadata': 1}}, {'name': 'runtime-combined-selected-call-parent-nested', 'patch_sha256': 'fd036fa13264f6bf06c1237330c05507afb83989970fb8b7ed8501d6a8d30f79', 'binding_sha256': '9b41058b1f92fe9908d1219f86f2b26779f72b0562d4ab9daf75a385e8fa8c70', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_initial_task_sources.py', 'recompiler/v2/architecture_nested_initial_task_sources.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_parent_member_sources.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/task_selected_call_sources.py', 'runner/src/snes/bridge_task_call.inc', 'runner/src/snes/bridge_task_helpers.inc', 'runner/src/snes/interp_bridge.c', 'runner/src/task_parent_member_contract.h', 'runner/src/task_selected_call_contract.h'], 'new_files': ['recompiler/v2/architecture_nested_initial_task_sources.py', 'recompiler/v2/task_parent_member_sources.py', 'recompiler/v2/task_selected_call_sources.py', 'runner/src/task_parent_member_contract.h', 'runner/src/task_selected_call_contract.h'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 48, 'normal_metadata': 33, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-turbo-speed', 'patch_sha256': 'de81a499306a5c0c2a798cc3747bc4859c9d2023dc201c64c767290716513033', 'binding_sha256': '21d29cc3a174b6dfe89692ab7c04dcf5bbc39017b45560d1101f4540f1e744a5', 'files': ['runner/src/common_rtl.c', 'runner/src/common_rtl.h', 'runner/src/desktop/host_main.c'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 48, 'normal_metadata': 33, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-refined-ff20-source', 'patch_sha256': 'e4ea45154ee0889fe85e05f4899bb358d6cd004089ca21e1521664a712630a54', 'binding_sha256': 'de0f05e71772a1df5cfdf44836735e516ec0d0b1f0d4d51a2686e643d6c7675f', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_ff20_byte_dispatch_sources.py', 'recompiler/v2/architecture_known_callee_refinement_sources.py', 'recompiler/v2/architecture_nested_initial_task_sources.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_known_callee_refinement_sources.py', 'recompiler/v2/architecture_ff20_byte_dispatch_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 49, 'normal_metadata': 34, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-writer-fact-early-refusal', 'patch_sha256': '5a2f0ebad421b7abc033925766a9c6f2567e0cdcf1a70979b6253f2404e0c391', 'binding_sha256': 'ba5b9a4ce452ece8906c6dd6c9798c18d291309f39b5ab674515caf5836ad018', 'files': ['recompiler/v2/architecture_known_callee_refinement_sources.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 49, 'normal_metadata': 34, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-baseline-architecture-view', 'patch_sha256': 'babde8df16536358e6deb264883c430eaa9b7a1e549c90e6693708813379d325', 'binding_sha256': '61ff850c5d657abba0dab7dd9292ed3378f5c291b059f73c8ebc211f5dc1dba3', 'files': ['recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/emit_bank.py', 'recompiler/v2/emit_function.py', 'recompiler/v2/program_emit.py', 'tools/v2_emit.py'], 'new_files': ['recompiler/v2/architecture_baseline_view.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 50, 'normal_metadata': 35, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-baseline-authored-symbols', 'patch_sha256': '65eb0d3f1d28528cefe04a0a03616c04d2f815a90ff4e1a666900141918c129f', 'binding_sha256': 'd664a35118c41523e1f7ee4ce663cf3004192863b21ab6ea8d603deaed2cf4e2', 'files': ['tools/v2_emit.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 50, 'normal_metadata': 35, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-nested-bank01-initializer', 'patch_sha256': 'a888b1e381b80248c2adc065740609a1f179c946889138b94b91ad712443a883', 'binding_sha256': 'e710b126f4c0b7ab0fc225ba6487a8c80bcfa9e239858dc77af6e21278b9cf1d', 'files': ['recompiler/v2/architecture_initial_task_sources.py', 'recompiler/v2/architecture_nested_initial_task_sources.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 50, 'normal_metadata': 35, 'task_metadata': 8, 'redirect_metadata': 1}}, {'name': 'runtime-declared-wait-call', 'patch_sha256': '3898eff444223ab0662a84f20f5b9c87bf763c5ca5539c4c527a024999184add', 'binding_sha256': '2e843d5216d0e0790103f0de4b234a171652508d791d9a8592bbf10e4594a727', 'files': ['recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_declared_wait_call_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/program_emit.py', 'recompiler/v2/task_resume.py', 'recompiler/v2/task_selected_call_sources.py'], 'new_files': ['recompiler/v2/architecture_declared_wait_call_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 52, 'normal_metadata': 37, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-immutable-rom-digest', 'patch_sha256': 'baf5f1888836c49b988606e4533981d17db5d4f616e1cebd43ad2b0e38eb5d57', 'binding_sha256': '043f5f603bbf883bbd14dc5a020a4f8f83371e45027f19068d14fccd7edbf639', 'files': ['recompiler/v2/architecture_initial_task_sources.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 52, 'normal_metadata': 37, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-terminal-rom-source-tail', 'patch_sha256': '67c5f7480b217eb3acad1422fde383ea4aa19407a822a634c7993ca6222109e7', 'binding_sha256': 'c16a77be2650dc006267ef0a6972ea0132d20ebf569164c563750c9647e7f01a', 'files': ['recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_rom_stack_dispatch_sources.py', 'recompiler/v2/architecture_rom_stack_tail_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_rom_stack_tail_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 54, 'normal_metadata': 39, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-rom-target-call-prefix', 'patch_sha256': '7a3b65e47761554b1590836b53528b0026805489b01019e05bb1140b5252c768', 'binding_sha256': '226b9dfbdfa6a3e09be787b7a699a399d7217b90ee471deaa2b4c2a814779099', 'files': ['recompiler/v2/architecture_rom_stack_dispatch_sources.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_rom_stack_call_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_rom_stack_call_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 56, 'normal_metadata': 41, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-rom-target-aftercall', 'patch_sha256': 'fcd51c1bb5860e0f236ba96df4e5c73e0dc0094e739ddfc9af055b07665be4b6', 'binding_sha256': 'a350b2a2f8af298d4f344999ac4c3540130ca442bb2fedd15f9fb86fd9ebbb8c', 'files': ['recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_rom_stack_aftercall_sources.py', 'recompiler/v2/architecture_rom_stack_dispatch_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_rom_stack_aftercall_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 58, 'normal_metadata': 43, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-ff20-architectural-chain', 'patch_sha256': 'c5a298a4f6bac9f9c95747047901f73ea9422c4ff234bfab0530b7e537010d5a', 'binding_sha256': 'c1dde23669dd0fb1690179ee645d4d0ed3cdeb425d275db66913cfeabd3e7c78', 'files': ['recompiler/v2/architecture_baseline_view.py', 'recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py', 'recompiler/v2/architecture_ff20_architectural_sources.py', 'recompiler/v2/architecture_ff20_byte_dispatch_sources.py', 'recompiler/v2/program_emit.py'], 'new_files': ['recompiler/v2/architecture_ff20_architectural_sources.py'], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-nested-validation-batch', 'patch_sha256': '5905a828635eab8e4d38726008efb15c066539c637ffc639ac11547d46dce4ad', 'binding_sha256': 'bf04e845fb54ef3842add245868dfff6d95e47650e6b7f76505390beda97991e', 'files': ['recompiler/v2/architecture_ff20_architectural_sources.py', 'recompiler/v2/architecture_nested_initial_task_sources.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-upstream-analyzer-identity', 'patch_sha256': '71c532452f0a21978c360efe920bdfe94c66e621a4a430dc9453c97c2b8b72c7', 'binding_sha256': '0a4e85b46516b1c489c27137eb430b59a2961df14fe3210a6111b0a423511a29', 'files': ['snesrecomp_cli.py', 'tools/build_native_analyzer.py', 'tools/native_analyzer_identity.py', 'tools/v2_analyze.py'], 'new_files': ['tools/native_analyzer_identity.py'], 'unpatched_predecessors': {'snesrecomp_cli.py': '9ba8a35b1062d64970f9a194dd1bc70578e0f2a6ccf675afdd94874aba561b8b', 'tools/build_native_analyzer.py': 'e222ce5e5a0ae8318e4e96a2e5333e8a8cbd3b4bc550771da6c339f61f2298d5', 'tools/v2_analyze.py': 'a6822404005b08641ba2f2ff217acf4e721c2409eb48401c8560b40a8123924f'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-requested-analysis-roots', 'patch_sha256': 'fd2b196c1d2438c3f499ebafd7afd21e210e6f6b8fb3212bef5c6d2740363498', 'binding_sha256': 'ccac7e4fe464432f34de70db4597e8f708ca5a4758d1fc9f48cef22a965ed77c', 'files': ['recompiler/v2/program_emit.py', 'tools/v2_emit.py'], 'new_files': [], 'unpatched_predecessors': {'tools/v2_emit.py': '9f98235b5a2705d3f268949b98b9f8d8260d08d15c408f754219576b4ffdf036'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-bank-validation-phase', 'patch_sha256': '300071a8f546481e2cf46b6633b33f2e23aa7bdfa1c4fb6f1f6380faf1270e5c', 'binding_sha256': 'e56e0923bb869f5ec5f5d40107ab8158f2de4ee5ed907898b60bcf2bbf79ba28', 'files': ['recompiler/v2/architecture_eligibility.py', 'recompiler/v2/architecture_emission_policy.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-control', 'patch_sha256': '6b3817f9c907b5fb58e8777868b9294afefd8a77a5704eb2447459f6850c5c83', 'binding_sha256': '389a4f31ad74206733c475cc5e5aa9f03802e1556a144b316c29be24c3a5f8b0', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '72b9fe3a232ef2630b6b4a8a76b0857f782710461d461ccf578d1bfaae3dba90', 'runner/src/snes/interp816.h': '956bd938bbe585f30469c43b54fb7acb6c328a1059a4a7c30e056cf5e53b6fa9', 'runner/src/snes/interp_bridge.c': 'ad25aa1d2e63718b1573276005156f2317b8a8bdd37741350088b4c48ede5a8b', 'runner/src/snes/interp_bridge.h': '4fdcffd52e6c5aa649f7fed253808c7c9a3ecdfaf8bfdf4da5bf714368f03a31'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-stack', 'patch_sha256': '19833ff9d0a0581cf0c51fb28ca415159cdd3b39b5d7a7474a82eea2a5e4837f', 'binding_sha256': 'b0eb1df49de4abdc206d954dedf9b3a6def10002f338e44162c5f1efd7a8a838', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '9e148dd333b095f7f6dec9fbb6e9a851c678ae2631ef5d9347745c5b414680a5', 'runner/src/snes/interp816.h': 'eee14931751ebcbe62d0fb108bc4c8753f2f775a0028759175947cb726d258d4', 'runner/src/snes/interp_bridge.c': '8e885e5f8bb7e663783351435ea66444d495e9a5b8f35253e9ccad36f07ca03c', 'runner/src/snes/interp_bridge.h': '2157814b8cfbca6016e9616eda535b216c3378b40e46964d0b419f4c29071164'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-index-stack', 'patch_sha256': 'd80baf717f828c9cc6b3d3837acca93af59dee81251a5892f301a992cd9f1d17', 'binding_sha256': 'bdfa3864927d619529e90781bb35a12fb740d835c7506813e95a9a1df9dfdd9d', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '809a7ae1bd2a7c554d8d71a39954edaa421aac36328bd6925ed65783af425c77', 'runner/src/snes/interp816.h': '75a9825eea1e49883219387bc263c399ad60b7b767ee079c2e7c4770c67aa7ae', 'runner/src/snes/interp_bridge.c': '677a9cc16f0a41bd84d1fe3880c65c19a23afaa67136d9b701091ac9a076b7cf', 'runner/src/snes/interp_bridge.h': 'b46bd208f6a9993dd6b3546b7f122572430eb498e4bbedf9b6d77eaa4f615822'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-dispatcher', 'patch_sha256': '43df76ebd848096f3e0ca71cd747fab3067ec306be17313c9cbfebe2c67e13f2', 'binding_sha256': '5e923123cbbdc06f107fb2b0a36d242b26837881be3efa1ccc9dfff554f3c445', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'e923b470db291112b3807d262fd0b149f80992590f014cc1dda250d7e81d54b3', 'runner/src/snes/interp816.h': 'fe54c1540948b82a0739f2ee5bde7b211eea173af8413c27cfdd9e002b752a18', 'runner/src/snes/interp_bridge.c': 'b5c8c9b80bc7b2c136e4a11e97fdd6007287110f23dd435b56bcc63b5d42414f', 'runner/src/snes/interp_bridge.h': '0d440bc8037a580719a6f5ad1c0e7b972a7c7de3ad0c761bc1a64209bf24c832'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-field-loop', 'patch_sha256': '98fe1733daa2577297e41caed701cf3fb8892aedd0a0ee930a123e05af5834a2', 'binding_sha256': 'f926e40aa29d217838d4e8518d517328c8cf4efca277e03fc99203eda33308c5', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'c062c075964cb1a310761c58e4d83fcaa12aeff617b7771ef3554bd1f414ae27', 'runner/src/snes/interp816.h': '09e97b62424eff7fe887b495f199b0372d8ddaa14438e20abe5c14087dd6b24e', 'runner/src/snes/interp_bridge.c': 'b4ddf1155fd9fa39cb6481e05b55913f113593900634461a1dc2d6fdb1547abc', 'runner/src/snes/interp_bridge.h': '5bf6e9265e25ef29fca29f35ffe70164e108976d54aeaadc5d46d28e2a955fac'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-scene-condition', 'patch_sha256': '9a2d806594c1e473f45f52458f4d72ee1fa5f57da27759c9199e7a2fab474932', 'binding_sha256': '8d42447c7d4660d597316baad7470e44c51a8d81a80470329976c7e3a816a353', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'f12a88f53ab4835e0808b97859dc96bfb96bb12f87f74c468ec035d1272a251b', 'runner/src/snes/interp816.h': 'cc19d9fd05e507d12591bdafb7bebe0baf6730668a7f470d64379797af42699f', 'runner/src/snes/interp_bridge.c': '740c9d004c7a35ddd5261d1ce709fb923e7b1cf88e27308de91896150c655b4a', 'runner/src/snes/interp_bridge.h': '714610ce5e7bce0f99ea677043c3fbe3b727acb37bb9b9e830e892699c40c175'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-condition-family', 'patch_sha256': '76ee174bf98487d8989dee7601204740e3c636b6c192a888f8e41297af2dbc97', 'binding_sha256': 'e13c0a00890e36e5c004c4e2b9802a4bcb26990f4f3b10ded4dc9cb0bcef9a7f', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'acbbaa2cbb64f8f079a739ddc73b53be788b317dc53b4b0314d070e931417a64', 'runner/src/snes/interp816.h': 'a1bc048bd5b090552e2f2b34a0413295d16eea6e6c265ed519c5dc55d6c843c8', 'runner/src/snes/interp_bridge.c': '70f3cf831cf1823296e786ca4420bc427b6aa3e56d4ba2dec79a1bc13f39740f', 'runner/src/snes/interp_bridge.h': '46fd284bb1bc4b4c97b80bcabab5b982af4e9c9b1cdd70857354c1c87e193514'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-message-window', 'patch_sha256': 'c6287628e00c231ac4d32941ad0f000d1990c1c8a27eb8af063dcf7a6004e5a3', 'binding_sha256': 'b8f5c994f08598c95e6cd7a42b69363a24e48dbb12be5ec068566a5c65a27701', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'daeb315ef4b53d3d0b1ec8c144a3cb9bbc17ee09b1fb06f313d5c1f931e3710a', 'runner/src/snes/interp816.h': 'de0d488bd9bd26a0e483c3df4324ec470f29a1aa39b59742855336a6376b544f', 'runner/src/snes/interp_bridge.c': '5b2b26bb294cbf6545f1a3df899799260f7722191a22b89d8ff343f629c16f63', 'runner/src/snes/interp_bridge.h': 'e9dc1f41aa67550f6336f253ca5b13d882137d3325aaae1c1281d3454003df94'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-field-loader', 'patch_sha256': '06e81547623c6215284a8bb9743423909e4c95e8e550be1daa8d5e588986909f', 'binding_sha256': 'c067bf6d1cc87b5e122e2e99696553115e1d771f4573f3a7cc78b5a432dfcbc8', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '4d16569463b23b700948538a5bd7e7679f59286ce0d1aa0d0f99db42824fcfb4', 'runner/src/snes/interp816.h': 'fd2691ec9f110fbc86aa817771c463b84e5532d4a81c764027e52ac382b15077', 'runner/src/snes/interp_bridge.c': '730bf1693742124f8bb1904b77d5dfd536ec32c1a9e42a8ef5fbd60165bcbf3a', 'runner/src/snes/interp_bridge.h': '19222d6d588cb30fa853d450d5c4dc04b51a06a57f66f9fb320c4265620e3a1d'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-field-tail', 'patch_sha256': '72e68296c8a9aecef9d7a1b4a07fb77f9328c8c7c47ada07f7c351229f9bea2e', 'binding_sha256': 'd9747aa9355593f28a1adf5bc0ec1b5a94e8f24877f8d66e307050727756e2ef', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '13a8db39e3f7198ab4c8c74ee6b87d68381a7a330f88e7658f9311f67ce54ac5', 'runner/src/snes/interp816.h': '2927686fd8267d4500bd3d81ed17d44218fea5cd660784ba2bb7e08872447e16', 'runner/src/snes/interp_bridge.c': '582383a8212f27754afe862ea564f2e5588efc34207a69f00280eaa159fce048', 'runner/src/snes/interp_bridge.h': '2138b223ebc444e256a00b191490fb0075f88187493fa5b97dca2e71386bb07a'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-menu-condition', 'patch_sha256': '2e46821d3759967fadc56c890d39e2928c99a197a9f517f97adb9be795f01d52', 'binding_sha256': 'e11538c1f2dbfc13a643eb1f8552c0e3c9f221a3f9e2f0bacce4b91d466a449c', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'f1eaa092954057427ee8ccdb9c972ede3d68c5631bee275678559a261e0755c7', 'runner/src/snes/interp816.h': 'babdf68f718e9d4f1f59a83e8982e53dfc759f81d9ef0bdc2e191604ac22daf0', 'runner/src/snes/interp_bridge.c': '1faf03a24ecd641cca1162b2b940202517c292fb8270d048ec21c317ca9c58ae'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-item-continuation', 'patch_sha256': '351e844aed03524d108657a4ed816f96f0a85c2228e7067eaff75ae9a5ae39e3', 'binding_sha256': '80a039a00c4108c8e4ff69607e4c0fd5c9c4d01a55dbb07dcbeaa40d26d11b31', 'files': ['runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp_bridge.c': 'a6c862d747c861dcec51249a78a99a1dd4ca68492c6a4448bcdfd6471d285b51'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-final-battle', 'patch_sha256': '3cdafbc3fe817663fc6ed28f308879c76043633fea169c8283a47819a5377c7c', 'binding_sha256': '2149b46a1f75cf89360f3162a040a34dd77937abdde48aa0f117a14354418edd', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '3adf549b98f251263c7b5b92ebcf1e08a8d6a16a3c85f4f308171e675043217d', 'runner/src/snes/interp816.h': '32fd1d571620defebf3b2aba0f7e33170abbc7e478c88afd2a861254473e3125', 'runner/src/snes/interp_bridge.c': '13162dc1dfbbc5e68925a851b7964298821fee55cf784763fca6ac591af85215'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-equipment-change', 'patch_sha256': '43a4b8d74c0b902121ebed533583821b3f2f04a5fa19325e8a5c001b5d943141', 'binding_sha256': 'e3801d3c363e9a03cd41e92b5405403738207c334f74743efadd501c9a126957', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '289184d5a3e391b592b877c07bf3d7bb800f6876ead63609340f1407a1901f0d', 'runner/src/snes/interp816.h': '0047cb581026ebf35b769ce8f7b6d54b790a195c969b514e6942806dde7303cc', 'runner/src/snes/interp_bridge.c': '8a579a1c8088d5a13493f34f0746b7f814e2504f9d179f9423aae36037e57be8'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-item-effects', 'patch_sha256': 'dafb89b12a40702e65aea8412ee22fc17dc557aec83463864540b95e70446872', 'binding_sha256': '112650c1f4f73500f985bc07f017143e7ffcfc479dbbceb1aafb1e1ecd32fc89', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'b821c453797674b527a388dabd8696b6691ecfbc1948fc27131a134694a9774c', 'runner/src/snes/interp816.h': 'af6ff8f5cc797ca98aae91a860cdf859822d3db58e37074fefcc1377283bfbd8', 'runner/src/snes/interp_bridge.c': 'ec9f1b2a79eb4d4946325dc2030dd5d4ab7859633bc75133c37366f37cdd88de'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-field-menus', 'patch_sha256': '0835e0fdf4590c44c6076324ac2c58696290ce4b6f9035c0139e639a17a01444', 'binding_sha256': '9829338a6d40212466a5f8f0b780f6347b123fbc3fbca0f65698ddfb8aa3a923', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '640fd7bd2e05fdbec33502567cf15e9dad80f1b6818b30d1e3570172f7c8be99', 'runner/src/snes/interp816.h': 'fe5f88c67ad6979a379ae93d200e4c5461b9b2fdce6a34600220ec2dc8e0fa09', 'runner/src/snes/interp_bridge.c': '94b61da5ab4e8c6a1618071aa7ade8954d29be5bdd15bdb6c54310a1db8bd00f', 'runner/src/snes/interp_bridge.h': 'f592ec4f325a6d441370b114f9ae7d93d419f3a22299a9f33c232eed330a5092'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-magic', 'patch_sha256': '180832ebe3ca609374a0e6190506173d75d03bacb1e10dafab57c28c9fae0cc4', 'binding_sha256': '76585b2c91a61132055adc82bb5daba9782caae6af4918c6d8cb2bdc61bf8328', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '0fe3926500ee40725820cb812795b62a898e7df7365603b922227fb0c2787dbb', 'runner/src/snes/interp816.h': 'bc17579137f49098d12c6bacfdddddda263c8af4bb13a2d4c20aca2a8969772b', 'runner/src/snes/interp_bridge.c': '53f32ed0f440f505d8b37e022c090319c55146b409b345dd6e5ebbbede402e52'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-battle-magic', 'patch_sha256': 'f69a576738abc89185102a74cab1f8e039baf1383b88848bd8d7bfef9ead5f7a', 'binding_sha256': '076b5ab153fc983352beb3b1e6444aecaf9523f019faf002a6252cbacce7ae99', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': '6752fba37a0000b0ab834f4312b33a71ff3ee479edb5dec090f4836ca008af06', 'runner/src/snes/interp816.h': 'b1e5208583c974ef7a334e350142d5387b2d7c67258a38807dea618b216434f3', 'runner/src/snes/interp_bridge.c': '8378c0df68ff23fdbbd11268782160cfe1ce59363a6943f82f1e90f244bcbe51'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-shop', 'patch_sha256': 'cb80baca6b6d963315dd65a39791b947d8de46e55d58015107b6c9b643ec8dea', 'binding_sha256': '94cf6f1abeeb46c6b4477bd7835a93da1f1c3ded7282dc0f784f789a5a97a32e', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'add999334b81ed0f20edd63716ac263a756cb35b6cf312dc40455bd94d6755bd', 'runner/src/snes/interp816.h': 'a2ce09a4184409a66e8facca46a9e15cd7a080db922ca15b800b0e502e0f5389', 'runner/src/snes/interp_bridge.c': 'b5f2d9c6c67722ff9e79317928cd976637d5c1a9688cd4bdd6ad500a6e23533b'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-source-native-sort', 'patch_sha256': '1388142a496b7219e9649a6ed723623d3d505ec750fcb04dc3a43ab496a26222', 'binding_sha256': 'c5675119d2fc7bd3cd0a6c165896acae674a9a268e8f52110ddd5f9831f74c5e', 'files': ['runner/src/snes/interp816.c', 'runner/src/snes/interp816.h', 'runner/src/snes/interp_bridge.c'], 'new_files': [], 'unpatched_predecessors': {'runner/src/snes/interp816.c': 'c97780a27bc060f5e3b469f2f26b2ad87f543d9a868ef95965a4a751b55ac103', 'runner/src/snes/interp816.h': 'c7309f18915c06071a847ec7de12c71ac92eca85d4cb6ee5f2740320a4b15816', 'runner/src/snes/interp_bridge.c': '9813a70ab1b7554a606716c3d03c60f399eb84a93dea666425d1d3e900a14a6a'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-architectural-native', 'patch_sha256': '199c1e6293958370dfdb37ba4de9ed3d0f4fc0b038b265115a1afbd146b74af5', 'binding_sha256': '3a7b2eb923331b29570a550823aafe05f69bb96372b644f97849da89da83a78f', 'files': ['recompiler/v2/emit_native_blocks.py', 'runner/src/native_blocks.h', 'runner/src/snes/interp_bridge.c', 'runner/src/snes/interp_bridge.h'], 'new_files': ['recompiler/v2/emit_native_blocks.py', 'runner/src/native_blocks.h'], 'unpatched_predecessors': {'recompiler/v2/emit_native_blocks.py': None, 'runner/src/native_blocks.h': None, 'runner/src/snes/interp_bridge.c': 'c940a4cc516696f48ba21541e7466a82becfcc97b298d061173bf45b224071d5', 'runner/src/snes/interp_bridge.h': 'd50d6b22214e58b7ec502fe9b426836e8a9ad5ba1dba57bf31ac0785b7790b10'}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-paired-owner-metadata', 'patch_sha256': '4b53fa4853636af524d05ee9a6d16df52e2a388e157f7778bd3dd86f1d5a48d6', 'binding_sha256': '225196a2abed65fcae09b160f9383922f93a042e92c1fe3797ffd70dcf88e598', 'files': ['runner/src/snes/interp_bridge.c', 'runner/src/cpu_state.c', 'recompiler/v2/emit_function.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}}, {'name': 'runtime-parent-writer-final-source-pin', 'patch_sha256': '14de3cdbf1f7a7842296f6a3866483febb0ff163079d072e3a5af443db04af3c', 'binding_sha256': '714c9a2f69190ce9e4f8ccde37667c53cdd8d8cf3c7458d0ca6aa1d04c320c28', 'files': ['recompiler/v2/task_parent_member_sources.py'], 'new_files': [], 'unpatched_predecessors': {}, 'metadata': {'cache_format': 60, 'normal_metadata': 45, 'task_metadata': 9, 'redirect_metadata': 1}})
RUNTIME_GENERATION_FORMATS = {'cache':59,'normal':44,'task':9,'redirect':1}
BASELINE_GENERATION_FORMATS = {'cache':60,'normal':45,'task':9,'redirect':1}

def target_generation_formats(args):
    return dict(BASELINE_GENERATION_FORMATS if getattr(args,'architecture_discovery_baseline',False) else RUNTIME_GENERATION_FORMATS)

def baseline_output_provenance(args,generated_metadata,region_metadata):
    formats=target_generation_formats(args)
    if type(generated_metadata.get('format_version'))is not int or generated_metadata['format_version']!=formats['cache'] or type(region_metadata.get('format_version'))is not int or region_metadata['format_version']!=formats['normal']:
        raise RuntimeError('Selected architecture discovery mode/generated formats differ')
    proof=region_metadata.get('architecture_source_eligibility',{}).get('baseline_discovery')
    if not getattr(args,'architecture_discovery_baseline',False):
        if proof is not None:raise RuntimeError('Unexpected baseline provenance in default generation')
        return None
    if not isinstance(proof,dict)or proof.get('contract')!='fresh-static-architecture-discovery-subset-v1' or proof.get('fresh_native_producer_once')is not True or proof.get('subset_roots_nodes_exits_sets')is not True or proof.get('external_model_or_rows_accepted')is not False or proof.get('second_program_output')is not False or proof.get('source_limit_changes')is not False or proof.get('new_owner_or_exit_authority')is not False or proof.get('ordinary_callable_view')!='current_profiled' or proof.get('architecture_view')!='fresh_static_only':
        raise RuntimeError('Actual baseline discovery source provenance missing/different')
    if type(proof.get('source_family_count'))is not int or proof['source_family_count']!=25 or any(not isinstance(proof.get(k),str)or re.fullmatch('[0-9a-f]{64}',proof[k])is None for k in ('baseline_model_sha256','profiled_model_sha256','reviewed_root_source_sha256')):
        raise RuntimeError('Baseline source view digests/family schema missing/different')
    # Format/provenance preflight only. This is not a semantic population certificate.
    return {'enabled':True,'formats':formats,'source_provenance':proof,'semantic_population_approved':False,'execution_qualified':False}

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
    value=_read_legacy_normal(metadata);recipe=value.get('reset_bootstrap')
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



"""Private root helper extension: strict old projection + dynamic new rows.
Root inserts before compilation after ONE actual public generation. No full factory
replay, source-tree monkeypatch, unknown-family acceptance or hardcoded new count.
"""
import copy,json,re,sys,hashlib
from pathlib import Path

def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def key(r):return(r['pc24'],r['m'],r['x'])
def _canonical_module_identity(runtime):
    import importlib
    runtime=Path(runtime).resolve(strict=True)
    expected={'v2_analyze':runtime/'tools/v2_analyze.py','snes65816':runtime/'recompiler/snes65816.py','v2.decoder':runtime/'recompiler/v2/decoder.py','v2.emit_function':runtime/'recompiler/v2/emit_function.py','v2.architecture_eligibility':runtime/'recompiler/v2/architecture_eligibility.py','v2.architecture_return_steps':runtime/'recompiler/v2/architecture_return_steps.py','v2.architecture_task_sources':runtime/'recompiler/v2/architecture_task_sources.py'}
    def verify_loaded():
        for name,module in list(sys.modules.items()):
            if name=='v2' or name.startswith('v2.'):
                path=Path(getattr(module,'__file__','')).resolve()
                if not path.is_relative_to(runtime/'recompiler/v2'):raise RuntimeError('Canonical child loaded foreign v2 module: '+name)
        for name,path in expected.items():
            if name in sys.modules and Path(getattr(sys.modules[name],'__file__','')).resolve()!=path:raise RuntimeError('Canonical child module identity differs: '+name)
    verify_loaded()
    sys.path[:0]=[str(runtime/'recompiler'),str(runtime/'tools')]
    for name in expected:importlib.import_module(name)
    verify_loaded()
    return {name:str(Path(sys.modules[name].__file__).resolve())for name in expected}


def _canonical_population_child(payload):
    # Fresh -I/-B interpreter; captured-profile imports from the helper parent
    # cannot provide any canonical decoder/emitter or package namespace here.
    modules=_canonical_module_identity(Path(payload['runtime']))
    if payload['mode']=='identity':return {'status':'CANONICAL_MODULE_IDENTITY_ONLY','modules':modules}
    if payload['mode']!='validate':raise RuntimeError('Unknown canonical child mode')
    path=Path(payload['generated_directory'])/'native_regions.json'
    value=json.loads(path.read_bytes())
    if canonical(value)!=payload['actual_digest']:raise RuntimeError('Canonical child actual metadata differs')
    old=_project_legacy_normal(value)
    if canonical(old)!=payload['old_digest']:raise RuntimeError('Canonical child original projection differs')
    legacy,report=_validate_new_population_local(value,old,rom_path=Path(payload['rom_path']),runtime=Path(payload['runtime']),cfg_dir=Path(payload['cfg_dir']),generated_directory=Path(payload['generated_directory']),allowed_new_families=dict(FAMILIES))
    if canonical(legacy)!=payload['old_digest']:raise RuntimeError('Canonical child changed original projection')
    return {'status':'CANONICAL_NEW_ROWS_VALIDATED_ISOLATED','modules':modules,'report':report,'actual_digest':payload['actual_digest'],'old_digest':payload['old_digest']}


def _run_canonical_population_child(payload):
    import subprocess
    script="import importlib.util,json,sys;sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('canonical_source_helper',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m._canonical_population_child(json.loads(sys.argv[2]));print(json.dumps(r,separators=(',',':')))"
    result=subprocess.run([sys.executable,'-I','-B','-c',script,str(Path(__file__).resolve()),json.dumps(payload,separators=(',',':'))],capture_output=True,text=True,timeout=300)
    if len(result.stdout)>1000000 or len(result.stderr)>1000000:raise RuntimeError('Canonical child exceeded bounded report allowance')
    if result.returncode:raise RuntimeError('Isolated canonical child refused: '+result.stderr[-12000:])
    value=json.loads(result.stdout)
    if not isinstance(value,dict):raise RuntimeError('Canonical child structured report missing')
    return value


def validate_new_population(value,old,*,rom_path,runtime,cfg_dir,generated_directory,allowed_new_families):
    if allowed_new_families!=dict(FAMILIES):raise RuntimeError('Isolated canonical family set differs')
    payload={'mode':'validate','runtime':str(Path(runtime).resolve()),'cfg_dir':str(Path(cfg_dir).resolve()),'rom_path':str(Path(rom_path).resolve()),'generated_directory':str(Path(generated_directory).resolve()),'actual_digest':canonical(value),'old_digest':canonical(old)}
    result=_run_canonical_population_child(payload)
    if result.get('status')!='CANONICAL_NEW_ROWS_VALIDATED_ISOLATED' or result.get('actual_digest')!=payload['actual_digest']or result.get('old_digest')!=payload['old_digest']:raise RuntimeError('Canonical child result identity differs')
    report=result['report'];report['canonical_runtime_modules']=result['modules'];report['canonical_process']='fresh isolated -I -B interpreter; no capture-runtime namespace reuse'
    return copy.deepcopy(old),report


def _validate_new_population_local(value,old,*,rom_path,runtime,cfg_dir,generated_directory,allowed_new_families):
    # allowed_new_families is a ROOT CODE constant {origin:recipe_key}, never an
    # input capture/JSON field. Root sets exact239 name only after frozen source.
    assert value['format_version']==34 and value['rom_sha256']==old['rom_sha256']
    assert value['direct_call_prefix']is old['direct_call_prefix']
    assert value['mode_successors']is True
    rows=value['regions'];fm={key(r):r for r in rows};prior={key(r):r for r in old['regions']}
    if len(fm)!=len(rows)or any(fm.get(k)!=r for k,r in prior.items()):raise RuntimeError('Old whole normal row dictionary changed; retain generation')
    before=old['architecture_source_eligibility'];after=value['architecture_source_eligibility']
    if len(before['sources'])!=19 or after['sources'][:19]!=before['sources']:raise RuntimeError('Old19 source family records changed; retain generation for scoped review')
    for field,v in before.items():
        if field!='sources'and after.get(field)!=v:raise RuntimeError('Old source recipe changed: '+field)
    for field in('contract','ordinary_roots_added','callee_exit_modes_added','task_ownership_changed'):
        if after.get(field)!=before[field]:raise RuntimeError('Architecture admission policy changed')
    fresh_families=after['sources'][19:]
    if {f['origin']for f in fresh_families}!=set(allowed_new_families)or len(fresh_families)!=len(allowed_new_families):raise RuntimeError('Unexpected new family set')
    claimed=set();family_report=[]
    for family in fresh_families:
        added=[tuple(k)for k in family['added']];reused=[tuple(k)for k in family['reused']]
        if family.get('refused')!=[]or len(set(added))!=len(added)or len(set(reused))!=len(reused)or set(added)&set(reused)or family['source_rows']!=len(added)+len(reused):raise RuntimeError('New family accounting/duplicates differ')
        if not set(added)<=set(fm)or not set(reused)<=set(fm)or claimed&set(added):raise RuntimeError('New family output ownership differs')
        recipe=after.get(allowed_new_families[family['origin']])
        if not isinstance(recipe,dict):raise RuntimeError('New source recipe missing')
        # Exact new producer contracts are frozen in root-reviewed runtime code;
        # helper must pin their recipe fields/digests in root code after output,
        # before compilation, if this generic structural gate cannot prove them.
        claimed.update(added);family_report.append((family['origin'],family['source_rows'],len(added),len(reused)))
    fresh=set(fm)-set(prior)
    if not fresh<=claimed:raise RuntimeError('Fresh ordinary/profile rows outside new sealed families; retain output for exact source review')
    sys.path[:0]=[str(Path(runtime)/'recompiler'),str(Path(runtime)/'tools')]
    from v2_analyze import _load_cfgs
    from snes65816 import rom_offset,decode_insn
    from v2.decoder import DecodeKey
    from v2.emit_function import emit_function
    from v2.architecture_eligibility import _independent
    from v2.architecture_return_steps import validate_return
    from v2.architecture_task_sources import PURE_OPS
    for family in fresh_families:
        for ident in [tuple(k)for k in family['added']+family['reused']]:
            if fm[ident]['mnemonic']not in PURE_OPS or any(k in fm[ident]for k in('source_return_contract','original_scheduler_call','causal_suspended_child')):raise RuntimeError('New pure family exported call/return/causal authority')
    rom=Path(rom_path).read_bytes();parsed=_load_cfgs(Path(cfg_dir));forced={p&0x7fffff for _b,_p,c in parsed for p in c.force_lle}
    masks=[r for _b,_p,c in parsed for r in c.data_regions]+[(c.bank,a,b)for _b,_p,c in parsed for a,b in c.authority_data+c.exclude_ranges]
    text=(Path(generated_directory)/'native_regions_v2.c').read_text(encoding='utf8')
    for ident in sorted(fresh):
        row=fm[ident];pc,m,x=ident
        if not _independent(rom,parsed,row):raise RuntimeError('New row is not independent source-owned architecture: '+repr(ident))
        off=rom_offset(pc>>16,pc&65535);ins=decode_insn(rom,off,pc&65535,pc>>16,m,x)
        if ins is None or rom[off:off+ins.length].hex()!=row['bytes']:raise RuntimeError('New source bytes changed')
        cfg=next((c for b,_p,c in parsed if b==pc>>16),None)
        if cfg is None:raise RuntimeError('New row requires exact bank-policy authority; generic validation cannot assume empty policy')
        # One independently decoded member only; no function/callee/exit inference.
        # Existing core emits faithful body into collectors. No source stream or
        # historical ancestry is recreated and no owning callable is emitted.
        collected=[];calls=[]
        emit_function(rom,pc>>16,pc&65535,m,x,func_name='DiscardedCanonicalNewInstruction',data_regions=masks,exclude_ranges=cfg.exclude_ranges,hle_func=cfg.hle_func,hle_spc_upload=cfg.hle_spc_upload,hle_dispatch=cfg.hle_dispatch,native_call_prefix_forced=forced,native_region_collector=collected,native_call_prefix_collector=calls,_native_instruction_members=frozenset({pc}),_native_collector_only=True)
        candidates=[r for r in collected+calls if key(r)==ident]
        # The optional return marker is metadata-only; actual return architecture
        # must independently pass existing exact fullPC24/ordered-pop validator.
        probe=dict(row)
        if probe.pop('source_return_contract',None)is not None and not validate_return(rom,parsed,row):raise RuntimeError('New marked return differs from canonical architecture')
        if not any(r==probe for r in candidates):raise RuntimeError('New body differs from fresh typed single-instruction canonical collector: '+repr(ident))
        compact=lambda s:re.sub(r'\s+','',s)
        if compact(row['body'])not in compact(text):raise RuntimeError('Canonical new body absent from actual generated C')
    # Root applies unchanged old row/28-literal/address validators to this explicit
    # old projection. Physical case count is checked ONCE against full actual
    # rows+reset3, not hidden by old scalar. No generated file is substituted.
    legacy=copy.deepcopy(old);legacy['format_version']=old['format_version']
    return legacy,{'old_rows':len(prior),'actual_rows':len(rows),'new_rows':len(fresh),'new_families':family_report,'source_generation_only':True,'physical_cases_required':len(rows)+3,'new_rows_sha256':canonical([fm[k]for k in sorted(fresh)]),'actual_normal_sha256':canonical(value),'canonical_scope':'NEW per-instruction bodies only, no old oracle/factory replay'}


"""ROOT PREPARATION ONLY: exact241-only metadata fences; source218 deferred before existing240 gate.

No CLI, cache/helper writes, generation, tests or build. Root may incorporate this
code after source review. Metadata validates an existing producer output; it is
never supplied to a source factory as a graph/role/caller certificate.
"""
import copy,hashlib,json

FAMILIES=(
 ('source_original_FF20_byte_dispatch_pure_instructions','ff20_byte_dispatch_graphs'),
)
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rowkey(row):return tuple(row[name]for name in('pc24','m','x'))

def fence_projection_and_recipes(value,old,rom,*,root_chosen_normal_format):
    if type(root_chosen_normal_format)is not int or value.get('format_version')!=root_chosen_normal_format:raise RuntimeError('Root must bind exact final normal format')
    before=old['architecture_source_eligibility'];after=value['architecture_source_eligibility']
    sources=after['sources']
    if len(before['sources'])!=19 or len(sources)!=20 or sources[:19]!=before['sources']:raise RuntimeError('Original19 family records changed')
    if [s.get('origin')for s in sources[19:]]!=[p[0]for p in FAMILIES]:raise RuntimeError('Wrong final241-only ordered family set')
    fm={rowkey(r):r for r in value['regions']};prior={rowkey(r):r for r in old['regions']}
    if len(fm)!=len(value['regions'])or len(prior)!=len(old['regions'])or any(fm.get(k)!=row for k,row in prior.items()):raise RuntimeError('Original full normal rows changed')
    allowed_fields=set(before)|{name for _origin,name in FAMILIES}
    if set(after)!=allowed_fields:raise RuntimeError('Unexpected source metadata fields')
    # This projects from ACTUAL metadata, not a replacement copy of trusted old.
    projected=copy.deepcopy(value)
    projected['format_version']=old['format_version']
    projected['regions']=[r for r in value['regions']if rowkey(r)in prior]
    projected['architecture_source_eligibility']['sources']=sources[:19]
    for _origin,name in FAMILIES:projected['architecture_source_eligibility'].pop(name)
    if projected!=old:raise RuntimeError('Complete actual original19 metadata projection changed')
    byte=after[FAMILIES[0][1]]
    if byte.get('contract')!='source-original-FF20-byte-selector-D0-pure-v1' or byte.get('source_cases')!=['D0/E0_mapped_ROM_only'] or byte.get('D1_source_case')!='unknown_original_barrier':raise RuntimeError('241 partial D0 contract changed')
    if (byte.get('graph_bound'),byte.get('start_bound'),byte.get('ancestry_bound'))!=(128,504,8)or not 0<=byte.get('attempted_starts',505)<=504:raise RuntimeError('241 source limits changed')
    if any(byte.get(k)is not False for k in('ordinary_roots_added','callee_exit_modes_added','task_ownership_changed','runtime_entry_D_guard','native_calls_or_returns_added','actual_original_dispatch_changed')):raise RuntimeError('241 exported new runtime authority')
    for graph in byte['graphs']:
        if graph.get('depth')!=1 or not 0<=graph.get('typed_instructions',128)<128:raise RuntimeError('241 target ancestry/graph limit changed')
    for domain in byte['producer_domains']:
        if domain.get('selector_domain')!=[0,125]or domain.get('discovery_D')!=0 or domain.get('runtime_entry_D_guard')is not False or domain.get('intentional_table_cardinality')is not None:raise RuntimeError('241 mathematical selector proof changed')
        wrapper=domain['wrapper_entry'];bank=wrapper[0]>>16
        keys=domain['wrapper_keys'];call=keys[-1][0];saved=(call+3)&65535
        if domain.get('saved_return')!=saved:raise RuntimeError('241 saved source return differs')
        reads=[]
        for s in range(126):
            low=(saved+2*s+1)&65535
            if low<0x8000 or low==0xffff:raise RuntimeError('241 D0 word is outside whole mapped bank')
            off=(bank&0x7f)*32768+(low&32767)
            if off+2>len(rom):raise RuntimeError('241 ROM word read out of bounds')
            reads.append([s,(bank<<16)|low,int.from_bytes(rom[off:off+2],'little')])
        if reads!=domain.get('mathematical_reads')or sorted({(bank<<16)|r[2]for r in reads})!=domain.get('unique_targets'):raise RuntimeError('241 whole D0 read/target domain changed')
    for family,(_origin,name)in zip(sources[19:],FAMILIES):
        admitted={tuple(k)for graph in after[name]['graphs']for k in graph['instruction_keys']}
        claimed={tuple(k)for kind in('added','reused')for k in family[kind]}
        if admitted!=claimed or len(claimed)!=family['source_rows']:raise RuntimeError('New family whole source-member accounting differs')
    fresh=[r for r in value['regions']if rowkey(r)not in prior]
    # Existing240 then proves each NEW row against the one-instruction original
    # canonical collector and actual C. Original28 literal/old address/return
    # validators receive the proven projection, with their old scalar scopes.
    return projected,{
      'original_projection_sha256':canonical(projected),
      'actual_full_metadata_sha256':canonical(value),
      'new_recipe_sha256':{name:canonical(after[name])for _origin,name in FAMILIES},
      'new_rows_sha256':canonical(fresh),'old_rows':len(prior),'actual_rows':len(fm),'new_rows':len(fresh),
      'full_call_rows':sum(r['mnemonic']in('JSR','JSL')for r in value['regions']),
      'full_call_distinct_pcs':len({r['pc24']for r in value['regions']if r['mnemonic']in('JSR','JSL')}),
      'full_JSR_rows':sum(r['mnemonic']=='JSR'for r in value['regions']),
      'full_JSL_rows':sum(r['mnemonic']=='JSL'for r in value['regions']),
      'physical_normal_plus_reset_cases':len(fm)+3,
      'scope':'ACTUAL generation metadata only; not compiled/qualified/native execution',
    }


"""Helper-only actual metadata projection and precompile source gate."""
_COMBINED_NORMAL={}

def _project_legacy_normal(value):
    import copy
    meta=value.get('architecture_source_eligibility',{})
    families=meta.get('sources',[])
    if value.get('format_version')!=34 or len(families)!=20 or [r.get('origin')for r in families[19:]]!=[x[0]for x in FAMILIES]:raise RuntimeError('Combined20 source format/family identity differs')
    fresh=set()
    for family in families[19:]:
        fresh.update(tuple(k)for k in family.get('added',[]))
    result=copy.deepcopy(value);result['format_version']=33
    result['regions']=[r for r in value['regions']if rowkey(r)not in fresh]
    result['architecture_source_eligibility']['sources']=copy.deepcopy(families[:19])
    for _origin,recipe in FAMILIES:result['architecture_source_eligibility'].pop(recipe,None)
    # EXACT original whole-metadata digest, all19 recipes/rows and old scalars.
    # No generated old dictionary or profile is substituted or published.
    _legacy_normal_source_row_count(result)
    return result

def normal_source_row_count(value):
    if value.get('format_version')==33:return _legacy_normal_source_row_count(value)
    _project_legacy_normal(value)
    return len(value['regions'])

def _read_legacy_normal(path):
    path=Path(path);ident=str(path.resolve())
    if ident not in _COMBINED_NORMAL:raise RuntimeError('Combined normal precompile proof must precede old output validators')
    value=json.loads(path.read_bytes());record=_COMBINED_NORMAL[ident]
    if canonical(value)!=record['actual_digest']:raise RuntimeError('Actual normal metadata changed after source proof')
    return _project_legacy_normal(value)

def _actual_normal_total(directory):
    ident=str((Path(directory)/'native_regions.json').resolve())
    if ident not in _COMBINED_NORMAL:raise RuntimeError('Physical C count needs actual validated source total')
    return _COMBINED_NORMAL[ident]['actual_rows']

def prepare_combined_source_population(directory,out,rom,runtime,cfg_dir):
    directory=Path(directory);out=Path(out);path=directory/'native_regions.json';reject_links(path)
    value=json.loads(path.read_bytes())
    meta=value.get('architecture_source_eligibility',{});families=meta.get('sources',[])
    hot={0x1e5cc,0x1e5e8,0x1e5e1,0x1e5fb,0x1e5d1,0x1e602}
    # Original native_regions.json already serializes FULL actual rows/recipes.
    # Preserve a bound prevalidation population receipt BEFORE any baseline guard.
    hot_claimed=[]
    if len(families)>19:
        claimed={tuple(k)for k in families[19].get('added',[])}
        hot_claimed=[r for r in value.get('regions',[])if rowkey(r)in claimed and r.get('pc24')in hot]
    pending={'status':'ACTUAL_GENERATION_UNVALIDATED','actual_metadata_path':str(path),'actual_metadata_sha256':sha(path),'full_rows_serialized_in_actual_metadata':True,'full_recipes_serialized_in_actual_metadata':True,'format':value.get('format_version'),'actual_rows':len(value.get('regions',[])),'families':[{'origin':f.get('origin'),'source_rows':f.get('source_rows'),'added':len(f.get('added',[])),'reused':len(f.get('reused',[]))}for f in families],'hot_claimed_added_keys':[list(rowkey(r))for r in hot_claimed],'native_execution_qualified':False}
    pending_path=out/'actual-source-population-before-validation.json'
    with pending_path.open('x',encoding='utf8',newline='\n')as f:json.dump(pending,f,indent=2);f.write('\n')
    old=_project_legacy_normal(value)
    projected,recipe_report=fence_projection_and_recipes(value,old,Path(rom).read_bytes(),root_chosen_normal_format=34)
    if projected!=old:raise RuntimeError('Original33 projection differs between strict gates')
    _unused,population_report=validate_new_population(value,old,rom_path=rom,runtime=runtime,cfg_dir=cfg_dir,generated_directory=directory,allowed_new_families=dict(FAMILIES))
    if not hot_claimed:raise RuntimeError('No genuinely new hot241 source key; stop BEFORE compile and preserve actual output')
    # Added keys have now passed whole old projection, source-member recipes,
    # exact one-step canonical body/ROM/masks and actual generated C presence.
    record={'actual_digest':canonical(value),'actual_rows':len(value['regions'])}
    _COMBINED_NORMAL[str(path.resolve())]=record
    report={'status':'ACTUAL_SOURCE_POPULATION_VALIDATED_PRECOMPILE','recipe':recipe_report,'population':population_report,'genuinely_new_hot241_keys':[list(rowkey(r))for r in hot_claimed],'native_execution_qualified':False,'old_projection_format':33,'new_actual_format':34}
    with(out/'actual-source-population-validated.json').open('x',encoding='utf8',newline='\n')as f:json.dump(report,f,indent=2);f.write('\n')
    return report


def _legacy_normal_source_row_count(value):
    enabled=value.get('direct_call_prefix')
    if value.get('format_version')!=33 or enabled is not True and enabled is not False or value.get('direct_call_contract')!='source-direct-call-architectural-prefix-v1':raise RuntimeError('Direct call source metadata/option missing.')
    if value.get('mode_successors')is not True or value.get('mode_successor_contract')!='source-owned-live-mx-instruction-successors-v1':raise RuntimeError('Live mode successor metadata/option missing.')
    meta=value.get('architecture_source_eligibility',{})
    sources=meta.get('sources',[])
    if meta.get('contract')!='source-reviewed-independent-instruction-union-v1' or meta.get('ordinary_roots_added')is not False or meta.get('callee_exit_modes_added')is not False or meta.get('task_ownership_changed')is not False or len(sources)!=19:raise RuntimeError('Independent architecture source policy missing.')
    expected=((7, 7, 0), (83, 83, 0), (99, 99, 0), (48, 46, 2), (12, 7, 5), (73, 14, 59), (4, 3, 1), (24, 14, 10), (91, 89, 2), (4, 4, 0), (12192, 5862, 6330), (401, 235, 166), (44, 36, 8), (141, 27, 114), (204, 121, 83), (439, 427, 12), (230, 24, 206), (260, 260, 0), (116, 116, 0))if enabled else((7, 7, 0), (79, 79, 0), (95, 95, 0), (44, 44, 0), (12, 7, 5), (73, 14, 59), (4, 3, 1), (24, 14, 10), (67, 67, 0), (4, 4, 0), (11566, 5445, 6121), (384, 222, 162), (40, 33, 7), (141, 27, 114), (204, 121, 83), (439, 427, 12), (217, 12, 205), (252, 252, 0), (104, 104, 0))
    origins=('reviewed_original_task_child', 'reviewed_original_ff20_receiving_starts', 'source_direct_call_return_instructions', 'source_direct_callee_instructions', 'source_dynamic_P_boundaries', 'source_nested_direct_call_instructions', 'source_nested_dynamic_P_frontier', 'source_architectural_return_steps', 'source_direct_aftercall_closure', 'source_aftercall_dynamic_P_frontier', 'source_program_direct_call_closure', 'source_program_dynamic_P_frontier', 'source_program_architectural_frontier', 'source_program_dynamic_P_architectural_returns', 'source_task_pure_architectural_instructions', 'source_ROM_stack_dispatch_pure_instructions', 'source_task_graph_architectural_members', 'source_original_initial_task_instructions', 'source_nested_initial_task_instructions')
    if any(source.get('origin')!=origin or source.get('source_rows')!=count or len(source.get('added',[]))!=added or len(source.get('reused',[]))!=reused or source.get('refused')!=[] for source,origin,(count,added,reused)in zip(sources,origins,expected)):raise RuntimeError('Independent architecture source union differs.')
    return_calls={0x01f4da:0x01f4dd,0x01f508:0x01f50b,0x01f547:0x01f54a,0x01f591:0x01f594}
    callee_calls={0x01f504:0x01f689,0x01f525:0x01f533,0x01f566:0x01f689,0x01f5c7:0x01f5d5}
    for name,target_key,authority in(('return_instruction_graphs','return_pc',return_calls),('callee_instruction_graphs','callee_pc',callee_calls)):
        graphs=meta.get(name,[])
        if len(graphs)!=16 or {(g.get('source_call'),g.get('parameter_m'),g.get('parameter_x'))for g in graphs}!={(pc,m,x)for pc in authority for m,x in((0,0),(0,1),(1,0),(1,1))}:raise RuntimeError('Independent instruction graph identity differs.')
        if any(g.get(target_key)!=authority[g['source_call']] or g.get('callee_exit_modes_added')is not False or g.get('caller_ownership_added')is not False or g.get('unknown_indirects')!=0 for g in graphs):raise RuntimeError('Independent source graph cannot add owner or exit facts.')
    mode=value.get('architecture_source_eligibility',{}).get('mode_instruction_graphs')
    if hashlib.sha256(json.dumps(mode,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='7f9e42ba901b74d42829571e114adb0087d9b2114acaf448e7e49cd35a1cbd20':raise RuntimeError('Source dynamic-P exact independent graphs differ.')
    nested=meta.get('nested_instruction_graphs')
    if hashlib.sha256(json.dumps(nested,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='5989bd4566d391a80630a02a640d38703dc4dd28d5ee5037cfa1582efd14a65b':raise RuntimeError('Nested source exact independent graphs differ.')
    frontier=meta.get('frontier_mode_instruction_graphs')
    if hashlib.sha256(json.dumps(frontier,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='1fe5fa601efee3184029cd98e9f6f0d9579673b859a05171faf50a1655c4c2c7':raise RuntimeError('Nested dynamic-P exact source frontier differs.')
    returns=meta.get('return_step_graphs')
    if hashlib.sha256(json.dumps(returns,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='ac3ed69d6485655d4b25f38749c8434dcf590b1c871ffd4c67ddf86dcc82598b':raise RuntimeError('Source-return exact barrier graph differs.')
    after_modes=meta.get('aftercall_mode_graphs')
    if hashlib.sha256(json.dumps(after_modes,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='1771c7afad4fa6e86cea603bf42cfabc5abcfe864ce5ce47340885dbd602465a':raise RuntimeError('Aftercall dynamic-P exact source graph differs.')
    after=meta.get('aftercall_graphs')
    expected_after='789716fb90ff49b3d10d5f8f0226a20f719e727459509b40f2e9a67756e3a0b3'if enabled else'636b051859fda8ef7778a13a67a3f3b876b214016e0b4d3514de6acd3bac9d5f'
    if hashlib.sha256(json.dumps(after,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=expected_after:raise RuntimeError('After-call exact original source graph differs.')
    program=meta.get('program_call_graphs')
    expected_program='ffe2e01b51ef0b26932c0a39f16dbe0ca9e5ec97e03ea7a5bc7cc55dc48a5b93'if enabled else'b7df3b50715c4cd13c8a5c856ed699a07cc3351bd9e0525872183e0ee5ee9d7c'
    if hashlib.sha256(json.dumps(program,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=expected_program:raise RuntimeError('Original program-call sealed source graph differs.')
    views=program.get('emission_policy_views')
    expected_views='099d726650a72ea33c8bb6f64d0b6b3f104532f1a3e13ab4a0e7eadbda1f4cde'if enabled else'9cf7749266276fd99a9eafecb11dffd775e3dc6042cd5cdd403b5ce229eb2c21'
    if hashlib.sha256(json.dumps(views,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=expected_views:raise RuntimeError('Actual original emitter policy-view source receipt differs.')
    if not isinstance(views,list)or [v.get('bank')for v in views]!=[0,1,2,28]or any(v.get('external_policy_accepted')is not False for v in views):raise RuntimeError('Original bank policy cannot accept external cfg or roots.')
    bank1c=views[3]
    if bank1c.get('local_cfg_present')is not False or any(dict(bank1c.get('explicit_local_options',[])).get(k)is not None for k in('data_regions','exclude_ranges','hle_func','hle_spc_upload','hle_dispatch')):raise RuntimeError('Bank1C must bind actual absent local options, not a manufactured cfg.')
    expected_stream={'contract':'internal-program-typed-direct-call-stream-v1','call_mode_rows':236,'sha256':'0ca41e6372f09ef043019af148ff0be036b6cbbbd802aecc2c4433eeb894fc99','external_rows_or_roots_accepted':False}
    if program.get('source_stream')!=expected_stream or program.get('bound')!=512 or program.get('depth_bound')!=8 or program.get('starts_processed')!=458 or program.get('callee_exit_modes_added')is not False or program.get('caller_owner_added')is not False:raise RuntimeError('Program-call stream cannot add root/owner/exit authority.')
    program_modes=meta.get('program_mode_graphs')
    expected_modes='fe322d6f77813301d3fd293387b4d88f215ccb461be2c54a07eaf25cfa4704ea'if enabled else'441fe1b3c9a134851b4f6ee05061b0ef08c5021104ba96ca1477aea68220d4f2'
    if hashlib.sha256(json.dumps(program_modes,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=expected_modes:raise RuntimeError('Original program dynamic-P sealed source graph differs.')
    if hashlib.sha256(json.dumps(meta.get('architectural_frontier_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('ff39cac51c4d02036fe8e214939178a0fd561d4acccfafec41e1890849cdc1a0'if enabled else'95a26888216c731078c5f62dc2125f4faec893f15667a75fe9ac50bb007adec1'):raise RuntimeError('New source frontier graph differs.')
    if hashlib.sha256(json.dumps(meta.get('program_return_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('75ba3b0a909eaceb7bc21615e42bcf9ef58ccfa169a2e6bec35f8037bb8a37fe'if enabled else'75ba3b0a909eaceb7bc21615e42bcf9ef58ccfa169a2e6bec35f8037bb8a37fe'):raise RuntimeError('New source frontier graph differs.')
    frontier=meta['architectural_frontier_graphs'];terminal=meta['program_return_graphs']
    if frontier.get('caller_owner_added')is not False or frontier.get('callee_exit_modes_added')is not False or frontier.get('status_history_added')is not False or frontier.get('interrupt_admission_added')is not False or frontier.get('limits')!={'graph_instructions':128,'starts':512,'call_depth':8}:raise RuntimeError('Architectural frontier cannot add ownership or relaxed bounds.')
    if any(terminal.get(k)is not False for k in('external_rows_or_roots_accepted','static_return_target_exported','successor_mode_exported','callee_exit_modes_added','caller_owner_added','ordinary_roots_added'))or terminal.get('original_scheduler_owned')is not True or terminal.get('source_stream')!=expected_stream:raise RuntimeError('Terminal return cannot add caller/target/exit/root facts.')
    task_source=meta.get('task_architecture_graphs')
    if hashlib.sha256(json.dumps(task_source,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='503db042f8fc979109457d1f643ff9ea2dc442b02cd746768016e676ef8ce76d':raise RuntimeError('Actual original task graph instruction source differs.')
    if any(task_source.get(k)is not False for k in('savedP_history_exported','task_selector_or_owner_exported','callee_exit_modes_added','caller_owner_added','ordinary_roots_added','task_dispatch_priority_changed','external_JSON_rows_accepted'))or task_source.get('live_E0_MX_per_instruction')is not True:raise RuntimeError('Task instructions cannot export owner/history/exit/root facts.')
    fresh={tuple(k)for k in sources[14]['added']}
    ordered=sorted((r for r in value['regions']if(r['pc24'],r['m'],r['x'])in fresh),key=lambda r:(r['pc24'],r['m'],r['x']))
    if len(ordered)!=121 or hashlib.sha256(json.dumps(ordered,sort_keys=True,separators=(',',':')).encode()).hexdigest()!='748fd6349b4bcfb362d10476e53d7e4d4a2d14b22d4fcc816f978bb34204ccf6':raise RuntimeError('New task instruction exact canonical bodies differ.')
    if hashlib.sha256(json.dumps(meta.get('rom_stack_dispatch_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('257464e7f9522396d15a58a45fa4cbcdbe27da9b44d118d9110be55d44b36c53' if enabled else '257464e7f9522396d15a58a45fa4cbcdbe27da9b44d118d9110be55d44b36c53'):raise RuntimeError('New combined source recipe differs: rom_stack_dispatch_graphs')
    if hashlib.sha256(json.dumps(meta.get('task_member_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('bde1f959de185b82d193d3f382e9e527c0e17f7a33df934e47c40f1cb6c234f4' if enabled else '991e139ecb88969a07f12e3952a06e28a96b0ba0ec6b4c992b62cebbf44389ef'):raise RuntimeError('New combined source recipe differs: task_member_graphs')
    newkeys={tuple(k)for k in sources[15]['added']}
    newrows=sorted((r for r in value['regions']if(r['pc24'],r['m'],r['x'])in newkeys),key=lambda r:(r['pc24'],r['m'],r['x']))
    if hashlib.sha256(json.dumps(newrows,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('dc5d40076d4f834650894ed650de06d55da35866995ec3bdc6593055325d1bea' if enabled else 'dc5d40076d4f834650894ed650de06d55da35866995ec3bdc6593055325d1bea'):raise RuntimeError('New combined canonical added bodies differ.')
    newkeys={tuple(k)for k in sources[16]['added']}
    newrows=sorted((r for r in value['regions']if(r['pc24'],r['m'],r['x'])in newkeys),key=lambda r:(r['pc24'],r['m'],r['x']))
    if hashlib.sha256(json.dumps(newrows,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('e84639e6e17153ba8ade3f18c29a27122584b3a94cee14a334c2e40f035b8180' if enabled else 'd28eca6b6a98c7a23a695182b8d9b70736f102b314aa512a20d4c001d5beabee'):raise RuntimeError('New combined canonical added bodies differ.')
    if hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('ac7d7c6031057a08887c106d76f21db56ab3835cb08003322e208e6ab5f3f930' if enabled else '9ba62228d3bd163828756873ad6a5277d5469693e33aefa6cf542722ec30c18b'):raise RuntimeError('Complete combined compositional source metadata differs; actual producer must match.')
    if hashlib.sha256(json.dumps(meta.get('initial_task_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('dd92d7688f9e3e88d691ee71e1b5ffed1281bcbcf17873952df11924652786b3' if enabled else 'a187e8377acd07ecc1ae7c6b7be94e2aff25bc9e2137295d4f99c543adbc0bdc'):raise RuntimeError('New combined source recipe differs: initial_task_graphs')
    newkeys={tuple(k)for k in sources[17]['added']}
    newrows=sorted((r for r in value['regions']if(r['pc24'],r['m'],r['x'])in newkeys),key=lambda r:(r['pc24'],r['m'],r['x']))
    if hashlib.sha256(json.dumps(newrows,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('16200f069a828eb1da33681b535351def60042c3463bd681c640fc34a0369999' if enabled else '02bd476f04ad9da192ee982fdd42ccfbee8a264769f3041c8d8098ae5550cbd8'):raise RuntimeError('New combined canonical added bodies differ.')
    if hashlib.sha256(json.dumps(meta.get('nested_initial_task_graphs'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('f7fb8160321ec95df09d9a1e5012d283dc8471fb561facd4a381187ed2ed2582' if enabled else '87eb310cc767b38f677ec8df74ecb931395a8f496cad4c4ccea7be33842ccfa5'):raise RuntimeError('New combined source recipe differs: nested_initial_task_graphs')
    newkeys={tuple(k)for k in sources[18]['added']}
    newrows=sorted((r for r in value['regions']if(r['pc24'],r['m'],r['x'])in newkeys),key=lambda r:(r['pc24'],r['m'],r['x']))
    if hashlib.sha256(json.dumps(newrows,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=('9410e3538604ad91b47a9fba2c09bcb9c3e884ac32e4aa78b4392056ff4c5753' if enabled else '398e4a5fc0154b25b870f3947ac5564b3e2aac01abc5f5d5bf56428ac1f3ce43'):raise RuntimeError('New combined canonical added bodies differ.')
    return 16999 if enabled else 16266

def validate_new_program_source_returns(runtime,directory,rom,architecture,rows):
    import json,os,subprocess,sys
    from pathlib import Path
    source=architecture['sources'][10]
    recipe=architecture['program_call_graphs']
    key=lambda row:(row['pc24'],row['m'],row['x'])
    fresh={tuple(k)for graph in recipe['graphs']for k in graph['source_return_keys']} & {tuple(k)for k in source['added']}
    selected=[row for row in rows if key(row)in fresh]
    if source['origin']!='source_program_direct_call_closure' or len(fresh)!=158 or len(selected)!=158 or len({key(r)for r in selected})!=158:
        raise RuntimeError('New sealed program-source return scope differs.')
    if sum(r['mnemonic']=='RTS'for r in selected)!=83 or sum(r['mnemonic']=='RTL'for r in selected)!=75:
        raise RuntimeError('New source-return architectural family differs.')
    generated=(Path(directory)/'native_regions_v2.c').read_text(encoding='utf-8')
    if any(not isinstance(row.get('body'),str)or row['body']not in generated for row in selected):raise RuntimeError('New scoped canonical return body absent from generated source.')
    # Parent normal_source_row_count MUST already bind exact graph hash, opaque
    # producer236stream pin and original root/exit/owner flags, before this call.
    # Child imports ONLY the already verified runtime. No old factories run.
    script=r"""import json,pathlib,sys
sys.dont_write_bytecode=True
runtime=pathlib.Path(sys.argv[1]).resolve();cfgdir=pathlib.Path(sys.argv[2]);rom=pathlib.Path(sys.argv[3]).read_bytes()
sys.path.insert(0,str(runtime/'recompiler'))
from v2.cfg_loader import load_bank_cfg
import v2.architecture_return_steps as canonical
if pathlib.Path(canonical.__file__).resolve()!=runtime/'recompiler/v2/architecture_return_steps.py':raise RuntimeError('Foreign canonical return validator')
parsed=[]
for path in sorted(cfgdir.glob('bank*.cfg')):
 c=load_bank_cfg(path);parsed.append((c.bank,str(path),c))
if not parsed or len({b for b,p,c in parsed})!=len(parsed):raise RuntimeError('Source cfg identities differ')
rows=json.load(sys.stdin)
if len(rows)!=158 or any(not canonical.validate_return(rom,parsed,row)for row in rows):raise RuntimeError('Scoped source return violates original typed architecture/masks')
print(json.dumps({'validated':len(rows),'RTS':sum(r['mnemonic']=='RTS'for r in rows),'RTL':sum(r['mnemonic']=='RTL'for r in rows),'old_factory_derivation_run':False}))
"""
    env={k:v for k,v in os.environ.items()if not k.startswith(('SNESRECOMP_','PRIVATE_','SDL_'))}
    env['PYTHONDONTWRITEBYTECODE']='1'
    result=subprocess.run([sys.executable,'-I','-B','-c',script,str(runtime),str(Path(directory).parent.parent/'recomp'),str(rom)],input=json.dumps(selected),capture_output=True,text=True,env=env,timeout=30)
    if result.returncode:raise RuntimeError('Scoped canonical return validator refused: '+result.stderr.strip())
    receipt=json.loads(result.stdout)
    if receipt!={'validated':158,'RTS':83,'RTL':75,'old_factory_derivation_run':False}:raise RuntimeError('Scoped canonical validator receipt differs.')
    return receipt

def validate_new_program_mode_returns(runtime,directory,rom,architecture,rows):
    import json,os,subprocess,sys
    from pathlib import Path
    source=architecture['sources'][13]
    recipe=architecture['program_return_graphs']
    key=lambda row:(row['pc24'],row['m'],row['x'])
    fresh={tuple(g['return_key'])for g in recipe['origins']} & {tuple(k)for k in source['added']}
    if fresh!={(175049, 0, 1), (173482, 0, 1), (34513, 1, 0), (173257, 0, 1), (173257, 1, 0), (128053, 0, 1), (34513, 0, 1), (172482, 1, 0), (34452, 1, 0), (175049, 0, 0), (172482, 0, 1), (34452, 0, 1), (173482, 0, 0), (173482, 1, 1), (182443, 1, 1), (173257, 0, 0), (175049, 1, 1), (128053, 0, 0), (34513, 0, 0), (172482, 0, 0), (34452, 0, 0), (34513, 1, 1), (173482, 1, 0), (173257, 1, 1), (175049, 1, 0), (34452, 1, 1), (172482, 1, 1)}:raise RuntimeError('New terminal return exact scope differs.')
    selected=[row for row in rows if key(row)in fresh]
    if source['origin']!='source_program_dynamic_P_architectural_returns' or len(fresh)!=27 or len(selected)!=27 or len({key(r)for r in selected})!=27:
        raise RuntimeError('New sealed terminal-mode-source return scope differs.')
    if sum(r['mnemonic']=='RTS'for r in selected)!=17 or sum(r['mnemonic']=='RTL'for r in selected)!=10:
        raise RuntimeError('New terminal-mode architectural family differs.')
    generated=(Path(directory)/'native_regions_v2.c').read_text(encoding='utf-8')
    if any(not isinstance(row.get('body'),str)or row['body']not in generated for row in selected):raise RuntimeError('New scoped canonical return body absent from generated source.')
    # Parent normal_source_row_count MUST already bind exact graph hash, opaque
    # producer236stream pin and original root/exit/owner flags, before this call.
    # Child imports ONLY the already verified runtime. No old factories run.
    script=r"""import json,pathlib,sys
sys.dont_write_bytecode=True
runtime=pathlib.Path(sys.argv[1]).resolve();cfgdir=pathlib.Path(sys.argv[2]);rom=pathlib.Path(sys.argv[3]).read_bytes()
sys.path.insert(0,str(runtime/'recompiler'))
from v2.cfg_loader import load_bank_cfg
import v2.architecture_return_steps as canonical
if pathlib.Path(canonical.__file__).resolve()!=runtime/'recompiler/v2/architecture_return_steps.py':raise RuntimeError('Foreign canonical return validator')
parsed=[]
for path in sorted(cfgdir.glob('bank*.cfg')):
 c=load_bank_cfg(path);parsed.append((c.bank,str(path),c))
if not parsed or len({b for b,p,c in parsed})!=len(parsed):raise RuntimeError('Source cfg identities differ')
rows=json.load(sys.stdin)
if len(rows)!=27 or any(not canonical.validate_return(rom,parsed,row)for row in rows):raise RuntimeError('Scoped source return violates original typed architecture/masks')
print(json.dumps({'validated':len(rows),'RTS':sum(r['mnemonic']=='RTS'for r in rows),'RTL':sum(r['mnemonic']=='RTL'for r in rows),'old_factory_derivation_run':False}))
"""
    env={k:v for k,v in os.environ.items()if not k.startswith(('SNESRECOMP_','PRIVATE_','SDL_'))}
    env['PYTHONDONTWRITEBYTECODE']='1'
    result=subprocess.run([sys.executable,'-I','-B','-c',script,str(runtime),str(Path(directory).parent.parent/'recomp'),str(rom)],input=json.dumps(selected),capture_output=True,text=True,env=env,timeout=30)
    if result.returncode:raise RuntimeError('Scoped canonical return validator refused: '+result.stderr.strip())
    receipt=json.loads(result.stdout)
    if receipt!={'validated':27,'RTS':17,'RTL':10,'old_factory_derivation_run':False}:raise RuntimeError('Scoped canonical validator receipt differs.')
    return receipt

def validate_direct_call_outputs(directory,cache,rom_sha,rom,enabled,runtime):
    directory=Path(directory);raw=Path(rom).read_bytes()
    metadata=directory/'native_regions.json';source=directory/'native_regions_v2.c'
    value=_read_legacy_normal(metadata);rows=value.get('regions');code=source.read_text(encoding='utf-8')
    if sha(Path(rom))!=rom_sha or value.get('rom_sha256')!=rom_sha or value.get('direct_call_prefix')is not enabled or len(rows)!=normal_source_row_count(value):raise RuntimeError('Direct call source metadata/ROM/count differs.')
    # Preserve the prior return family and only fresh source-certified aftercall returns.
    architecture=value['architecture_source_eligibility'];family=architecture['sources'][7];after_family=architecture['sources'][8]
    marked_all=[r for r in rows if 'source_return_contract'in r]
    new_mode_return_metadata=validate_new_program_mode_returns(runtime,directory,rom,architecture,rows)
    new_mode_scope={tuple(k)for k in architecture['sources'][13]['added']}
    if len(marked_all)!=213 or len(new_mode_scope)!=27:raise RuntimeError('Terminal/old return union differs.')
    marked_all=[r for r in marked_all if(r['pc24'],r['m'],r['x'])not in new_mode_scope]
    prior={tuple(k)for k in family['added']}
    certified={tuple(k)for graph in architecture['aftercall_graphs']['graphs']for k in graph['source_return_keys']}
    added={tuple(k)for k in after_family['added']};fresh=certified & added
    old_scope=prior|fresh
    program_family=architecture['sources'][10];program_graphs=architecture['program_call_graphs']
    program_scope={tuple(k)for g in program_graphs['graphs']for k in g['source_return_keys']} & {tuple(k)for k in program_family['added']}
    if program_family['origin']!='source_program_direct_call_closure' or len(program_scope)!=158 or old_scope & program_scope or {(r['pc24'],r['m'],r['x'])for r in marked_all}!=old_scope|program_scope or len(marked_all)!=186:raise RuntimeError('Sealed scoped source-return union differs.')
    marked=[r for r in marked_all if(r['pc24'],r['m'],r['x'])in old_scope]
    if family['origin']!='source_architectural_return_steps' or after_family['origin']!='source_direct_aftercall_closure' or len(prior)!=14 or len(fresh)!=14 or prior & fresh or {(r['pc24'],r['m'],r['x'])for r in marked}!=prior | fresh or len(marked)!=28:raise RuntimeError('Scoped source-return metadata differs.')
    for row in marked:
        pc=row['pc24'];offset=(pc>>16)*32768+(pc&32767)
        if row.get('source_return_contract')!='source-e0-scheduler-architectural-return-v1' or row['mnemonic']!='RTS' or row['bytes']!='60' or row['length']!=1 or row['cycles']!=6 or row['next_pc']!=((pc+1)&65535) or raw[offset]!=0x60:raise RuntimeError('Source return must retain exact original RTS architecture.')
        exact=['{ uint16 _ret_s = cpu->S;','cpu->S = (uint16)(cpu->S + 1);','uint16 _rpcl = (uint16)cpu_aot_read8(cpu, 0x00, cpu->S);','cpu->S = (uint16)(cpu->S + 1);','uint16 _rpch = (uint16)cpu_aot_read8(cpu, 0x00, cpu->S);','uint8 _rpb = cpu->PB;','uint32 _rpc = (uint32)((((_rpch << 8) | _rpcl) + 1) & 0xFFFFu);','uint32 _rpc24 = ((uint32)_rpb << 16) | _rpc;','*next_pc=_rpc24;',f'cpu_source_call_return_stage(cpu,0x{pc:06x}u,0x60u,_ret_s,(uint8)_rpcl,(uint8)_rpch,_rpb,_rpc24);','}']
        clean=lambda code:re.sub(r'\s+','',re.sub(r'/\*.*?\*/','',code,flags=re.S))
        if clean(row['body'])!=clean(''.join(exact)):raise RuntimeError('Source return bank0 wrap/fullPC/pop-stage body differs.')
    new_return_metadata=validate_new_program_source_returns(runtime,directory,rom,architecture,rows)
    subset=[r for r in rows if r.get('contract')=='source-direct-call-architectural-prefix-v1']
    if len(subset)!=(733 if enabled else 0):raise RuntimeError('Direct call source mode row count differs.')
    if enabled and (len({r['pc24']for r in subset})!=360 or sum(r['mnemonic']=='JSR'for r in subset)!=354 or sum(r['mnemonic']=='JSL'for r in subset)!=379):raise RuntimeError('Direct call source family count differs.')
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

ADDRESS_CONTRACT_SCOPES = {'native-e0-source-cached-indirect-y-v1': {'old_keys': [[43553, 1, 1], [46175, 1, 1], [46180, 1, 1], [46185, 1, 1], [46195, 1, 1], [46200, 1, 1], [46203, 1, 1], [46213, 1, 1], [46220, 1, 1], [46225, 1, 1], [46239, 1, 1], [46244, 1, 1], [46249, 1, 1], [46276, 1, 1], [46283, 1, 1], [46288, 1, 1]], 'old_count': 16, 'old_rows_sha256': 'fea69583fd2aad20cccd20a0bf13f80cea5728fcbbb332594baabe287f196ee5', 'new_count': 7, 'new_rows_sha256': '10065f29c776b3897f0f03f8bd05dba470d5dc7e1d4a440b6c72f98b03d23491', 'total': 23}, 'native-e0-source-cached-stack-direct-v1': {'old_keys': [[34083, 1, 1], [34088, 1, 1], [34111, 1, 1], [34119, 0, 1], [34128, 0, 1], [182320, 0, 1]], 'old_count': 6, 'old_rows_sha256': '2e22c4d1edc331583492c7c2b29fe53e2e6d9d3a639688ce6471b626242dfc68', 'new_count': 47, 'new_rows_sha256': 'e848c1f6ca019e35647897dff25119c8a8c4e50bc378ee45dabb55bbfea3aac4', 'total': 53}, 'native-e0-source-cached-stack-indirect-y-v1': {'old_keys': [], 'old_count': 0, 'old_rows_sha256': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'new_count': 8, 'new_rows_sha256': '8f4389841394b6c92b08ecfe5a6338ca6d55371f663328dcc147b41406dad53c', 'total': 8}}

# ONLY the five independently source191-certified address rows are partitioned.
# ADDRESS_CONTRACT_SCOPES and the original source53 validator stay unchanged.
ADDRESS_SOURCE191_SCOPES = {'native-e0-source-cached-indirect-y-v1': {'keys': [[181951, 0, 1]], 'row_count': 1, 'canonical_rows_sha256': '8863ed2fc198177222d54379422e359e71d84714536fdf63062e2383db53f576', 'total_after': 24}, 'native-e0-source-cached-stack-direct-v1': {'keys': [[166436, 0, 1], [184322, 0, 1], [192677, 0, 1]], 'row_count': 3, 'canonical_rows_sha256': '3b65d86dad00bf4515a86b8a857d3a4f30fd79d3ce11dd793f5ca6bbbbc6ee61', 'total_after': 56}, 'native-e0-source-cached-stack-indirect-y-v1': {'keys': [[189967, 0, 1]], 'row_count': 1, 'canonical_rows_sha256': '309e5d1f3a8bc2b1d81c470d4a1c283e9eb9db5c188792b8fa99bfcd70955e07', 'total_after': 9}}


def partition_source191_address_rows(value,subset,contract):
    # Parent output validators already call normal_source_row_count, whose
    # unchanged seventeen-family/recipe/wholemetadata seals bind this artifact.
    spec=ADDRESS_SOURCE191_SCOPES[contract]
    key=lambda r:(r['pc24'],r['m'],r['x'])
    canonical=lambda rows:hashlib.sha256(json.dumps(sorted(rows,key=key),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    wanted=set(map(tuple,spec['keys']))
    selected=[r for r in subset if key(r)in wanted]
    architecture=value['architecture_source_eligibility'];families=architecture['sources']
    if len(families)!=19 or families[15]['origin']!='source_ROM_stack_dispatch_pure_instructions' or hashlib.sha256(json.dumps(architecture['rom_stack_dispatch_graphs'],sort_keys=True,separators=(',',':')).encode()).hexdigest()!='257464e7f9522396d15a58a45fa4cbcdbe27da9b44d118d9110be55d44b36c53':raise RuntimeError('Source191 address recipe/family differs: '+contract)
    source_members={tuple(k)for g in architecture['rom_stack_dispatch_graphs']['graphs']for k in g['instruction_keys']}
    if len(subset)!=spec['total_after'] or len(selected)!=spec['row_count'] or {key(r)for r in selected}!=wanted or canonical(selected)!=spec['canonical_rows_sha256'] or not wanted<={tuple(k)for k in families[15]['added']} & source_members:raise RuntimeError('Source191 address rows lack exact new canonical graph scope: '+contract)
    return [r for r in subset if key(r)not in wanted]


def validate_address_contract_scope(value,subset,contract):
    subset=partition_source191_address_rows(value,subset,contract)
    spec=ADDRESS_CONTRACT_SCOPES[contract]
    key=lambda r:(r['pc24'],r['m'],r['x'])
    canonical=lambda rows:hashlib.sha256(json.dumps(sorted(rows,key=key),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    keys=[key(r)for r in subset];old_keys={tuple(k)for k in spec['old_keys']}
    prior=[r for r in subset if key(r)in old_keys];fresh=[r for r in subset if key(r)not in old_keys]
    architecture=value['architecture_source_eligibility'];family=architecture['sources'][10]
    source_members={tuple(k)for g in architecture['program_call_graphs']['graphs']for k in g['instruction_keys']}
    if family['origin']!='source_program_direct_call_closure' or len(subset)!=spec['total'] or len(set(keys))!=len(keys) or {key(r)for r in prior}!=old_keys or len(prior)!=spec['old_count'] or canonical(prior)!=spec['old_rows_sha256']:raise RuntimeError('Original address-contract rows changed: '+contract)
    if len(fresh)!=spec['new_count'] or canonical(fresh)!=spec['new_rows_sha256'] or not {key(r)for r in fresh}<={tuple(k)for k in family['added']} & source_members:raise RuntimeError('New address-contract rows lack exact source53 scope: '+contract)
    return {'legacy_rows':len(prior),'program_source_rows':len(fresh)}

def validate_stack_direct_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);rom=Path(rom);raw=rom.read_bytes()
    value=_read_legacy_normal(directory/'native_regions.json');rows=value.get('regions');code=(directory/'native_regions_v2.c').read_text(encoding='utf-8')
    if sha(rom)!=rom_sha or value.get('rom_sha256')!=rom_sha or value.get('format_version')!=33 or not isinstance(rows,list)or len(rows)!=normal_source_row_count(value):raise RuntimeError('Stack direct actualROM/metadata9/count differs.')
    subset=[r for r in rows if r.get('contract')=='native-e0-source-cached-stack-direct-v1']
    opcodes={'ORA':0x03,'AND':0x23,'EOR':0x43,'ADC':0x63,'STA':0x83,'LDA':0xa3,'CMP':0xc3,'SBC':0xe3}
    address_scope=validate_address_contract_scope(value,subset,'native-e0-source-cached-stack-direct-v1')
    for row in subset:
        pc=row.get('pc24');b=row.get('bytes');body=row.get('body');mnemonic=row.get('mnemonic');offset=(pc>>16)*32768+(pc&32767)
        if row.get('m')not in(0,1)or row.get('x')not in(0,1)or row.get('length')!=2 or row.get('next_pc')!=((pc+2)&65535)or mnemonic not in opcodes or not isinstance(b,str)or len(b)!=4 or bytes.fromhex(b)[0]!=opcodes[mnemonic]or raw[offset:offset+2].hex()!=b:raise RuntimeError('Stack direct typed source row/ROM/mode differs.')
        expected='uint32 _ea = (uint16)(cpu->S + 0x%04x);'%bytes.fromhex(b)[1]
        if not isinstance(body,str)or body not in code or body.count('cpu->S')!=1 or body.count(expected)!=1 or 'cpu_aot_begin' in body or 'cpu_aot_commit' in body or '*next_pc=((uint32)cpu->PB<<16)|'not in body:raise RuntimeError('Stack direct readonly S/single bankzero EA/body differs.')
    stack_indirect=[r for r in rows if r.get('contract')=='native-e0-source-cached-stack-indirect-y-v1']
    stack_indirect_scope=validate_address_contract_scope(value,stack_indirect,'native-e0-source-cached-stack-indirect-y-v1')
    for row in stack_indirect:
        pc=row['pc24'];data=bytes.fromhex(row['bytes']);body=row['body'];offset=(pc>>16)*32768+(pc&32767)
        if row['m']not in(0,1)or row['x']not in(0,1)or row['length']!=2 or row['next_pc']!=((pc+2)&65535)or row['mnemonic']not in opcodes or data[0]!=opcodes[row['mnemonic']]+0x10 or raw[offset:offset+2]!=data:raise RuntimeError('Stack indirectY original typed source differs.')
        expected='uint16 _ea_p = (uint16)(cpu->S + 0x%04x);'%data[1]
        if body not in code or body.count('cpu->S')!=1 or body.count(expected)!=1 or body.count('uint16 _ea_lo = cpu_aot_read16(cpu, 0x00, _ea_p);')!=1 or body.count('uint32 _ea = (((uint32)cpu->DB << 16) + _ea_lo + cpu->Y) & 0xffffffu;')!=1 or any(x in body for x in('cpu_aot_extra(', 'cpu_aot_begin', 'cpu_aot_commit'))or '*next_pc=((uint32)cpu->PB<<16)|'not in body:raise RuntimeError('Stack indirectY single readonlyS/pointer/bank24 original body differs.')
    if cache.get('outputs',{}).get('native_regions_v2.c')!=sha(directory/'native_regions_v2.c')or cache.get('outputs',{}).get('native_regions.json')!=sha(directory/'native_regions.json'):raise RuntimeError('Stack direct output/cache mismatch.')
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'normal_rows':len(rows),'stack_direct_rows':len(subset),'legacy_stack_direct_rows':address_scope['legacy_rows'],'program_stack_direct_rows':address_scope['program_source_rows'],'stack_indirect_y_rows':len(stack_indirect),'execution_qualified':False}

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
    value=_read_legacy_normal(directory/'native_regions.json');rows=value.get('regions');code=(directory/'native_regions_v2.c').read_text(encoding='utf-8')
    if value.get('format_version')!=33 or value.get('rom_sha256')!=rom_sha or not isinstance(rows,list) or len(rows)!=normal_source_row_count(value):raise RuntimeError('IndirectY metadata9/source-scoped normal generation differs.')
    subset=[r for r in rows if r.get('contract')=='native-e0-source-cached-indirect-y-v1']
    opcodes={'ORA':0x11,'AND':0x31,'EOR':0x51,'ADC':0x71,'STA':0x91,'LDA':0xb1,'CMP':0xd1,'SBC':0xf1}
    address_scope=validate_address_contract_scope(value,subset,'native-e0-source-cached-indirect-y-v1')
    for row in subset:
        pc=row.get('pc24');m=row.get('m');x=row.get('x');body=row.get('body');b=row.get('bytes');mnemonic=row.get('mnemonic');offset=(pc>>16)*32768+(pc&32767)
        if m not in (0,1) or x not in (0,1) or row.get('length')!=2 or row.get('next_pc')!=((pc+2)&65535) or mnemonic not in opcodes or not isinstance(b,str) or len(b)!=4 or bytes.fromhex(b)[0]!=opcodes[mnemonic] or raw[offset:offset+2].hex()!=b:raise RuntimeError('IndirectY typed source row/ROM/mode differs.')
        if not isinstance(body,str) or body not in code or body.count('uint16 _ea_lo = cpu_aot_read16(cpu, 0x00, _ea_p);')!=1 or 'cpu_aot_begin' in body or 'cpu_aot_commit' in body or '*next_pc=((uint32)cpu->PB<<16)|' not in body:raise RuntimeError('IndirectY faithful pointer/body/fullPC differs.')
    for name,count in (('native_regions_v2.c',_actual_normal_total(directory)+3),('native_task_resume_v2.c',task_scheduler_scope_count(json.loads((directory/'native_task_resume.json').read_bytes()))),('native_source_redirect_v2.c',3)):
        path=directory/name;reject_links(path);source=path.read_text(encoding='utf-8')
        if source.count('cpu_aot_begin_scheduler_region(')!=count or 'cpu_aot_begin_region(' in source:raise RuntimeError('IndirectY common one-use scheduler scope missing: '+name)
        if cache.get('outputs',{}).get(name)!=sha(path):raise RuntimeError('IndirectY scoped output/cache mismatch: '+name)
    return {'metadata_format':RUNTIME_GENERATION_FORMATS['normal'],'normal_rows':len(rows),'indirect_y_rows':len(subset),'legacy_indirect_y_rows':address_scope['legacy_rows'],'program_indirect_y_rows':address_scope['program_source_rows'],'execution_qualified':False}

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

TASK_SEPARATE_FIELDS = ('selected_architectural_members', 'selected_architectural_calls', 'retained_parent_architectural_members')
TASK_EXTENSION_SEALS = {'on': {'whole_metadata': '2f54327ad99bae2c11eaa0de9cf80bb66f9e1edc031e00bf09c4795f2f839eb8', 'C_sha256': 'd85816d9ed11b226a1f389d621219efa08af25d5b7a2080dc7ad70762ce77445', 'counts': {'selected_architectural_members': 5, 'selected_architectural_calls': 10, 'retained_parent_architectural_members': 1}, 'scope': 251, 'fields': {'selected_architectural_members': 'ebe4cb49b561a4e55b4b7c239712b78f2495d91e9cb71c45dad68e50a01b81d9', 'selected_architectural_calls': 'a687af5796b3cc4ea73e88c396b0c861e14a3eff7b9e474b4debaad555677453', 'retained_parent_architectural_members': 'd81e1e24c0c32752cdf3f4c556426f3ffcc099281cb7008942641d1da05c359f'}, 'old_rows': 'e9cc56788163d2159f425e90c383a3eaf6a442224cb7a8b1f85c8ce1034123af', 'old_recipe': '8bbedf0ffd121f97956a79a96721a81d53a9379fa446b99022cc7ac76e70fa72', 'old_graphs': 'ac2994f66b32622ba5d608dc5a2945334a8853bc689bcd28198661aef5f9f36b', 'prefix235_200_bytes': 322329, 'prefix235_200_sha256': 'fc2d8999c66dff236354d8293d9e0c996758846df09a0a60b47877a252f85364', 'prefix207_bytes': 331985, 'prefix207_sha256': '24f5374849a987f5286bf35a133edf5bc4f11f6a8e4c89b209e9c0749335c732', 'parent_append_sha256': '5692f64790697c52c27bdc6dbfe0ef4f4a230f051c08b3210ec12a5d67e1d8b7'}, 'off': {'whole_metadata': 'c033390d8c292c7d38bc3def8c79f71053baee83ed2b44eeae499d9e009e1d88', 'C_sha256': '0b877eac16296246e0f0e74e0ad45c121d61b94946c06d90eed9973d10159fd3', 'counts': {'selected_architectural_members': 5, 'selected_architectural_calls': 0, 'retained_parent_architectural_members': 1}, 'scope': 241, 'fields': {'selected_architectural_members': 'ebe4cb49b561a4e55b4b7c239712b78f2495d91e9cb71c45dad68e50a01b81d9', 'selected_architectural_calls': '0f8b0745ecbe560f08d072fa396da7790d1d6e18a8f6694d684608647fa0b158', 'retained_parent_architectural_members': '9406d44a1845d9813e351301d0a13d2b3ea0e158f629bf22c2ec652038d28b26'}, 'old_rows': 'e9cc56788163d2159f425e90c383a3eaf6a442224cb7a8b1f85c8ce1034123af', 'old_recipe': '8bbedf0ffd121f97956a79a96721a81d53a9379fa446b99022cc7ac76e70fa72', 'old_graphs': 'ac2994f66b32622ba5d608dc5a2945334a8853bc689bcd28198661aef5f9f36b', 'prefix235_200_bytes': 322329, 'prefix235_200_sha256': 'fc2d8999c66dff236354d8293d9e0c996758846df09a0a60b47877a252f85364', 'prefix207_bytes': 323344, 'prefix207_sha256': 'f77a4132cd0be1a6f8c1bc8fca197aaa67bb3c6db5542061642079cf533ecd1c', 'parent_append_sha256': '5692f64790697c52c27bdc6dbfe0ef4f4a230f051c08b3210ec12a5d67e1d8b7'}}

def task_scheduler_scope_count(value):
    call=value.get('selected_architectural_calls',{}).get('recipe',{}).get('direct_call_prefix')
    if type(call)is not bool or value.get('format_version')!=RUNTIME_GENERATION_FORMATS['task']:raise RuntimeError('Task8 direct CALL option/schema missing.')
    seal=TASK_EXTENSION_SEALS['on'if call else'off']
    if len(value.get('rows',[]))!=TASK_GENERATED_ROW_COUNT or any(not isinstance(value.get(f),dict)or set(value[f])!={'rows','recipe'}or len(value[f]['rows'])!=seal['counts'][f]for f in TASK_SEPARATE_FIELDS):raise RuntimeError('Task8 separate source scopes differ.')
    count=len(value['rows'])+sum(len(value[f]['rows'])for f in TASK_SEPARATE_FIELDS)
    if count!=seal['scope']:raise RuntimeError('Task8 total scheduler scope differs.')
    return count

def validate_selected_member_extension(value,code,raw):
    canonical=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    count=task_scheduler_scope_count(value);enabled=value['selected_architectural_calls']['recipe']['direct_call_prefix'];seal=TASK_EXTENSION_SEALS['on'if enabled else'off']
    if canonical(value)!=seal['whole_metadata']:raise RuntimeError('Complete task8 merged source metadata differs.')
    if canonical(value['rows'])!=seal['old_rows']or canonical(value['recipe'])!=seal['old_recipe']or canonical(value['graphs'])!=seal['old_graphs']:raise RuntimeError('Old235 fields/recipe/graphs changed.')
    data=code.encode('utf-8')
    if hashlib.sha256(data).hexdigest()!=seal['C_sha256']or hashlib.sha256(data[:seal['prefix235_200_bytes']]).hexdigest()!=seal['prefix235_200_sha256']or hashlib.sha256(data[:seal['prefix207_bytes']]).hexdigest()!=seal['prefix207_sha256']or hashlib.sha256(data[seal['prefix207_bytes']:]).hexdigest()!=seal['parent_append_sha256']:raise RuntimeError('Old235/200/207 Cprefix or exact parent append changed.')
    if code.count('cpu_aot_begin_scheduler_region(')!=count:raise RuntimeError('Complete task scheduler scope differs.')
    tail=data[seal['prefix235_200_bytes']:]
    if tail.count(b'if(!cpu_source_task_resume_active(cpu,pc24,mx)) return false;')!=seal['counts']['selected_architectural_calls']or tail.count(b'if(!cpu_source_task_parent_admitted(cpu,pc24,mx))return false;')!=seal['counts']['retained_parent_architectural_members']:raise RuntimeError('New CALL/parent current owner guard missing.')
    keys={(r['pc24'],r['m'],r['x'])for r in value['rows']}
    for field in TASK_SEPARATE_FIELDS:
        extension=value[field]
        if canonical(extension)!=seal['fields'][field]:raise RuntimeError('Separate task row/recipe source seal changed: '+field)
        for row in extension['rows']:
            key=(row['pc24'],row['m'],row['x']);pc=key[0];b=bytes.fromhex(row['bytes']);off=(pc>>16)*32768+(pc&32767)
            if key in keys or key[1]not in(0,1)or key[2]not in(0,1)or len(b)!=row['length']or raw[off:off+len(b)]!=b or row['body']not in code:raise RuntimeError('Task field overlaps old authority or typed wholebytes/body differ.')
            keys.add(key)
            if field=='selected_architectural_members'and row['mnemonic']not in('PHP','PLP','PLD'):raise RuntimeError('Old200 NONCALL scope changed.')
            if field=='selected_architectural_calls':
                long=row['mnemonic']=='JSL';frame=3 if long else 2;length=4 if long else 3;body=row['body']
                target=int.from_bytes(b[1:],'little')if long else(pc&0xff0000)|int.from_bytes(b[1:],'little')
                if row['mnemonic']not in('JSR','JSL')or row.get('original_scheduler_call')is not True or row.get('contract')!='source-direct-call-architectural-prefix-v1'or len(b)!=length or b[0]!=(0x22 if long else 0x20)or row['cycles']!=(8 if long else 6)or row['frame_bytes']!=frame or row['next_pc']!=target:raise RuntimeError('Selected CALL canonical original typed frame differs.')
                if body.count('cpu_aot_get_direct_call_operands(')!=1 or body.count('cpu_source_call_native_push(')!=1 or body.count('cpu_aot_write8(')!=frame or body.count('cpu->PB=(uint8)(_call_target>>16);')!=int(long)or '*next_pc=_call_target;'not in body:raise RuntimeError('Selected CALL actual cached operands/ordered frame observer differ.')
            elif field=='retained_parent_architectural_members'and row['mnemonic']in('JSR','JSL','RTS','RTL','RTI','TCS','TXS'):raise RuntimeError('Parent NONCALL field gained call/return/owner authority.')
    return value['selected_architectural_members']

def validate_selected_task_outputs(directory,cache,rom_sha,rom):
    directory=Path(directory);metadata_path=directory/'native_task_resume.json';source_path=directory/'native_task_resume_v2.c'
    reject_links(metadata_path);reject_links(source_path)
    value=json.loads(metadata_path.read_bytes())
    validate_selected_member_extension(value,source_path.read_text(encoding='utf-8'),Path(rom).read_bytes())
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


CURRENT61_PROFILE_RECEIPT_SHA256 = 'a4a6c34cf68fa7a95d3f9dc312397b3898b1a6c763a41a779b24c1f633c5b9a7'
CURRENT61_PROFILE_MARKER_SHA256 = '9be61835f6e511a08756463177761301b31c141b690d32c578edf03dfa8287e6'
CURRENT61_PROFILE_IDENTITY = {'rom_sha256': '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600', 'module_id': 'main', 'mapper': 'lorom', 'program_digest': '84ee2d0224f5857be9dac61d8b9a187d3a94ccfa2c43a67a5b1cc81de4994210', 'build_digest': 'ea89f70a2ec85c9dfda4a5a19e826d34435366c90ccdcb4ef7c4c08e0273dcd2', 'generation_digest': '5dec7b7890744e01a163ec900f62b2ab217e0c06ec91a9a4bd72c1bccb455c78'}

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
    if preflight.get('current61_profile'):
        if sha(marker)!=CURRENT61_PROFILE_MARKER_SHA256:raise ValueError('Exact current61 capture runtime marker changed')
    else:
        if any(receipt.get(k)!=v for k,v in expected.items())or receipt.get('prefix_patch_sha256')or receipt.get('lifecycle_patch_sha256')or 'faithful_hook_boundary_patch_sha256' in receipt or 'reviewed_roots_patch_sha256' in receipt:
            raise ValueError('Only original five-patch3909 captures are currently supported; newer source captures require explicit compatibility review')
    sources=receipt.get('patched_sources',{})
    if not isinstance(sources,dict)or not sources:raise ValueError('Original runtime source marker missing')
    if command(['git','rev-parse','HEAD'],runtime)!=RUNTIME_PIN:raise ValueError('Original runtime pin changed')
    new_names=()
    if preflight.get('current61_profile'):
        new_names=receipt.get('new_patched_sources')
        if not isinstance(new_names,list)or any(not isinstance(n,str)for n in new_names)or len(new_names)!=len(set(new_names))or not set(new_names)<=set(sources):
            raise ValueError('Exact current61 runtime new-source partition is invalid')
    runtime_source_accounting(runtime,sources,new_names)
    for name,digest in sources.items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise ValueError('Original runtime marker path escapes source')
        path=profile_file(runtime/name)
        if sha(path)!=digest:raise ValueError('Original runtime patched source changed: '+name)
        preflight['protected'][str(path)]=digest
    preflight['protected'][str(marker)]=sha(marker);preflight['source_runtime']=runtime
    return runtime

def generation_commands(runtime,project,rom,identity,profiles=(),prefixes=True,reviewed=True,certify=True,continuations=True,direct_calls=True,architecture_baseline=False,analysis_roots=()):
    # Source-owned live-mode alternatives are independent of prefix/call diagnostics.
    emit=[sys.executable,runtime/'tools/v2_emit.py','--rom',rom,'--cfg-dir',project/'recomp',
      '--out-dir',project/'src/gen','--analysis-backend','native','--cfg-roots','--no-host-root-scan','--native-mode-successors']
    if architecture_baseline:emit+=['--architecture-discovery-baseline']
    if prefixes:emit+=['--faithful-prefixes']
    if direct_calls:emit+=['--native-direct-call-prefix']
    sync=[sys.executable,runtime/'tools/v2_sync_funcs_h.py','--cfg-dir',project/'recomp','--out',project/'recomp/funcs.h']
    if reviewed:emit+=['--reviewed-root-manifest',project/REVIEWED_ROOTS_INPUT]
    if certify:emit+=['--certify-converged-exits']
    if continuations:emit+=['--certify-native-continuations']
    for seed in analysis_roots:emit+=['--analysis-roots-file',seed]
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

def profile_preflight(paths,receipt_path,program_path,expected,source,analyzer_path=None,profile_source_binding=None,profile_source_binding_sha256=None):
    if not paths:
        if receipt_path or program_path or analyzer_path or profile_source_binding or profile_source_binding_sha256:raise ValueError('Original profile identity inputs require --profile-manifest')
        return None
    if not receipt_path or not program_path or not analyzer_path:
        raise ValueError('Profiles require original --profile-build-receipt, --profile-program-manifest and --profile-analyzer')
    if len(paths)>64:raise ValueError('At most64 explicit profile files; legacy captures remain limited to32')
    profiles=[profile_file(p)for p in paths]
    if len(set(profiles))!=len(profiles):raise ValueError('Repeated local profile path')
    if sum(p.stat().st_size for p in profiles)>128*1024*1024:raise ValueError('Local profile bundle exceeds128MiB')
    receipt_path=profile_file(receipt_path,4*1024*1024);program_path=profile_file(program_path)
    receipt=json.loads(receipt_path.read_bytes());program=json.loads(program_path.read_bytes())
    current61_profile=sha(receipt_path)==CURRENT61_PROFILE_RECEIPT_SHA256
    if len(paths)>32 and not current61_profile:raise ValueError('At most32 explicit legacy profile files per build')
    explicit_profile_binding=None
    if current61_profile:
        if not profile_source_binding or not profile_source_binding_sha256:raise ValueError('Current61 profiles require explicit root-reviewed profile binding path and SHA256')
        explicit_profile_binding=profile_file(profile_source_binding,4*1024*1024)
        if not re.fullmatch('[0-9a-f]{64}',profile_source_binding_sha256)or sha(explicit_profile_binding)!=profile_source_binding_sha256:raise ValueError('Current61 profile binding changed')
        binding=json.loads(explicit_profile_binding.read_bytes())
        if binding.get('schema')!='source61-build27-owned-profile-binding-v1' or binding.get('original_receipt_sha256')!=CURRENT61_PROFILE_RECEIPT_SHA256 or binding.get('identity')!=CURRENT61_PROFILE_IDENTITY:raise ValueError('Unreviewed current61 capture producer binding')
        if binding.get('profiles')!={str(p.resolve()):sha(p)for p in profiles}:raise ValueError('Profile path/bytes differ from explicit reviewed binding')
    elif profile_source_binding or profile_source_binding_sha256:raise ValueError('Current61 binding cannot admit another capture build')

    if receipt.get('status')!='compiled_unqualified' or receipt.get('public_build')is not True:
        raise ValueError('Unrecognized original public build receipt; historical/experimental builds are preserved')
    if receipt.get('rom_sha256')!=expected or receipt.get('runtime_pin')!=RUNTIME_PIN:
        raise ValueError('Original profile ROM/runtime identity mismatch')
    if receipt.get('automatic_faithful_patch_sha256')!=AUTOMATIC_FAITHFUL_PATCH_SHA256:
        raise ValueError('Original profile generator patch is unrecognized; explicit compatibility review required')
    for field,digest in [('runtime_patch_sha256',FOUNDATION_PATCH_SHA256),('host_navigation_patch_sha256',HOST_NAVIGATION_PATCH_SHA256),('faithful_instruction_patch_sha256',FAITHFUL_INSTRUCTION_PATCH_SHA256),('host_modal_audio_patch_sha256',HOST_AUDIO_PATCH_SHA256)]:
        if receipt.get(field)!=digest:raise ValueError('Original build patch identity mismatch: '+field)
    if not current61_profile and (receipt.get('prefix_patch_sha256')or receipt.get('lifecycle_patch_sha256')or receipt.get('automatic_generation',{}).get('faithful_prefixes')or 'faithful_hook_boundary_patch_sha256' in receipt or 'reviewed_roots_patch_sha256' in receipt):
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
    cache_path=profile_file(program_path.parent/'.snesrecomp-cache.json',(8 if current61_profile else 4)*1024*1024);cache=json.loads(cache_path.read_bytes())
    if cache.get('format_version')!=(48 if current61_profile else 5) or cache.get('module')!={'id':'main','prefix':''}:
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
    if current61_profile and identity!=CURRENT61_PROFILE_IDENTITY:raise ValueError('Current61 original capture identity changed')
    if explicit_profile_binding:protected[str(explicit_profile_binding)]=sha(explicit_profile_binding)
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
    return {'current61_profile':current61_profile,'identity':identity,'profiles':profiles,'receipt':receipt_path,'program':program_path,'analyzer':analyzer,'protected':protected,'captures':sorted(captures),'original_generator_digest':generator,'original_config_digest':config}

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
    suffix='\0aot_deny_gate=0'+('\0faithful_prefixes=1' if preflight.get('current61_profile') else '')
    generator=hashlib.sha256((v2_emit._tree_digest(paths)+suffix).encode()).hexdigest()
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

def profile_generation_policy(preflight,audit_only,runtime,source):
    if preflight is None:
        if audit_only:raise ValueError('--profile-audit-only requires explicit exact current61 profiles and binding')
        return None
    if not audit_only:return {'mode':'analysis_roots','profiles_forwarded_as_generation_roots':True,'default':False}
    if not preflight.get('current61_profile')or sha(preflight['receipt'])!=CURRENT61_PROFILE_RECEIPT_SHA256 or preflight['identity']!=CURRENT61_PROFILE_IDENTITY:raise ValueError('--profile-audit-only supports only recognized exact current61 binding')
    # Original source identity, explicit binding and reader audit already passed.
    # SDK computes candidate keys only: no decoder/emitter or root promotion.
    from v2.program_emit import discover_profile_roots
    from v2.cfg_loader import load_bank_cfg
    if Path(sys.modules[discover_profile_roots.__module__].__file__).resolve()!=runtime/'recompiler/v2/program_emit.py' or Path(sys.modules[load_bank_cfg.__module__].__file__).resolve()!=runtime/'recompiler/v2/cfg_loader.py':raise ValueError('Profile candidate audit imported another original runtime')
    cfgs=[load_bank_cfg(str(p))for p in sorted((source/'recomp').glob('bank[0-9a-fA-F][0-9a-fA-F].cfg'))]
    declared={((cfg.bank&255)<<16)|(entry.start&65535)for cfg in cfgs for entry in cfg.entries}
    forced=set()
    roots=discover_profile_roots(preflight['profiles'],declared,forced,expected_rom=preflight['identity']['rom_sha256'],expected_module='main')
    candidate=[{'pc24':pc,'m':m,'x':x}for pc,m,x in sorted({(k.pc24,k.m,k.x)for k in roots})]
    return {'mode':'audit_only','default':False,'profiles_forwarded_as_generation_roots':False,'unpromoted_candidate_roots':candidate,'unpromoted_candidate_root_count':len(candidate),'unpromoted_candidate_original_targets':sorted(forced),'unpromoted_candidate_original_target_count':len(forced),'source_conversion':'Reviewed source241 partial original FF20 D0 discovery; source218 refinement deferred; observations confer no source ownership','native_execution_qualified':False}


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
    if not isinstance(manifest,dict) or len(manifest)!=83 or REVIEWED_ROOTS_INPUT not in manifest or 'src/foundation_guide_data.h' not in manifest or 'src/foundation_current_data.h' not in manifest:
        raise ValueError('Expected83 authored inputs including original guide/advice and the five declared architectural backend inputs; preserve source')
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

def validate_seed_preparation_mode(args):
    source_only=getattr(args,'source_seed_prepare',False)
    if source_only:
        if args.profile_seed_prepare or args.profile_audit_only or args.profile_manifest or any(getattr(args,n,None) for n in ('profile_build_receipt','profile_program_manifest','profile_analyzer','profile_runtime_dir','profile_source_binding','profile_source_binding_sha256')):
            raise ValueError('Source-only preparation cannot claim historical profile inputs')
        if not args.architecture_discovery_baseline or not args.analysis_roots_file:
            raise ValueError('Source-only preparation requires explicit baseline and source-analysis seed files')
        args.profile_seed_prepare=True
    elif getattr(args,'analysis_roots_file',None):
        raise ValueError('Explicit source seed files require --source-seed-prepare')
    if getattr(args,'architecture_discovery_baseline',False)and not args.profile_seed_prepare:
        raise ValueError('--architecture-discovery-baseline initially requires --profile-seed-prepare; actual population review/compile continuation remain separate')
    if not args.profile_seed_prepare:
        return
    if args.profile_audit_only or (not args.profile_manifest and not source_only):
        raise ValueError('--profile-seed-prepare requires explicit profiles and cannot combine --profile-audit-only')
    if not all(getattr(args,n)for n in ('emit_proven_prefixes','reviewed_roots','certify_converged_exits','native_continuations','native_direct_calls')):
        raise ValueError('Seed preparation requires the complete declared source analysis policy; no diagnostic feature disabling')


def generate_profile_seed_auxiliary_outputs(project,out,rom,expected,actual):
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


def freeze_profile_seed_preparation(out,project,runtime,rom,expected,actual,target_sources,target_marker_digest,profile_inputs,profile_report,profile_snapshots,generated_metadata,automatic_manifest,args):
    # This is an immutable UNREVIEWED source population, not a compilation or
    # semantic qualification receipt. Stop before legacy population assertions.
    if (not profile_inputs and not getattr(args,'source_seed_prepare',False)) or args.profile_audit_only or not args.profile_seed_prepare:
        raise ValueError('Explicit seed preparation context missing')
    def tree(root):
        result={}
        for folder,dirs,files in os.walk(root,followlinks=False):
            parent=Path(folder);reject_links(parent)
            dirs[:]=sorted(n for n in dirs if n not in ('.git','__pycache__','target','build'))
            for name in sorted(files):
                path=parent/name;reject_links(path)
                result[path.relative_to(root).as_posix()]=sha(path)
        return result
    outputs=generated_metadata.get('outputs')
    if not isinstance(outputs,dict)or not outputs:raise RuntimeError('Complete generated output map missing')
    for name,digest in outputs.items():
        if Path(name).is_absolute()or '..'in Path(name).parts:raise RuntimeError('Generated output escape')
        path=project/'src/gen'/name;reject_links(path)
        if sha(path)!=digest:raise RuntimeError('Generated output changed before preparation freeze')
    metadata={}
    for name in ('program_manifest.json','native_regions.json','native_task_resume.json','native_source_redirect.json','.snesrecomp-cache.json'):
        path=project/'src/gen'/name;reject_links(path);metadata[name]=json.loads(path.read_bytes())
    if metadata['program_manifest.json']!=automatic_manifest or metadata['.snesrecomp-cache.json']!=generated_metadata:raise RuntimeError('Actual metadata differs while freezing')
    for path,digest in (profile_inputs['protected'] if profile_inputs else {}).items():
        if sha(Path(path))!=digest:raise RuntimeError('Protected capture identity/source changed during preparation')
    for name,digest in actual.items():
        # funcs.h is an SDK-owned post-emission derivative, separately sealed.
        if name!='recomp/funcs.h'and sha(project/name)!=digest:raise RuntimeError('Authored project input changed: '+name)
    toolchain={}
    for name in ('cmake','cc','cxx','ninja'):
        resolved=Path(shutil.which(getattr(args,name))).resolve(strict=True);reject_links(resolved)
        toolchain[name]={'path':str(resolved),'sha256':sha(resolved)}
    runtime_files={}
    for folder in ('recompiler','recompiler-rs/src','runner','tools','lib'):
        root=runtime/folder
        if root.exists():
            for name,digest in tree(root).items():runtime_files[folder+'/'+name]=digest
    for name in ('CMakeLists.txt','Cargo.toml','Cargo.lock','runtime-source-provenance.json'):
        path=runtime/name
        if path.is_file():runtime_files[name]=sha(path)
    receipt={'schema':'profile-seed-preparation-v1','status':'generated_unreviewed_uncompiled',
      'helper_path':str(Path(__file__).resolve()),'helper_sha256':sha(Path(__file__)),'rom_sha256':expected,'rom':str(rom),
      'output_dir':str(out.resolve()),'project':str(project.resolve()),'runtime':str(runtime.resolve()),
      'authored_input_hashes':actual,'project_tree_hashes':tree(project),
      'runtime_tree_hashes':runtime_files,'runtime_patched_sources':target_sources,'runtime_marker_sha256':target_marker_digest,
      'profile_snapshot_hashes':{str(path.relative_to(out)):sha(path)for path in profile_snapshots},
      'profile_original_protected_hashes':profile_inputs['protected'] if profile_inputs else {},'profile_identity':profile_inputs['identity'] if profile_inputs else None,
      'seed_input_kind':'source_analysis_requests' if getattr(args,'source_seed_prepare',False) else 'historical_profiles',
      'analysis_seed_hashes':{str(p):sha(Path(p)) for p in getattr(args,'analysis_roots_file',[])},
      'profile_audit':profile_report,'actual_analysis_roots':automatic_manifest['roots'],
      'actual_complete_metadata':metadata,'generated_output_hashes':outputs,
      'callable_source_hashes':{name:digest for name,digest in tree(project/'src/gen').items()if name.endswith(('.c','.h','.inc'))},
      'toolchain':toolchain,'arguments':{k:str(v)if isinstance(v,Path)else[str(x)for x in v]if isinstance(v,list)else v for k,v in vars(args).items()},
      'legacy_population_assertions_executed':False,'compilation_started':False,'native_execution_qualified':False,
      'review_requirement':'A separate root-reviewed source validator must check actual full old/new row/call/return/owner/mask/bounds deltas. This JSON is never a factory certificate or permission to bypass original guards.',
      'resume_requirement':'Compile only these untouched generated outputs after the separate reviewed source validator and strict reviewed handoff verify. Do not rerun the whole producer to derive expected metadata. First compilation receipt must be create-new compiled_unqualified.'}
    if getattr(args,'architecture_discovery_baseline',False):
        receipt['architecture_discovery_baseline']=baseline_output_provenance(args,generated_metadata,metadata['native_regions.json'])
        receipt['generation_lineage']={'helper_sha256':sha(Path(__file__)),'runtime_marker_sha256':target_marker_digest,'ordered_runtime_extensions':runtime_extension_records(),'expected_formats':target_generation_formats(args),'compilation_helper_sha256':None,'compilation_started':False}
    path=out/'profile-seed-preparation.json'
    with path.open('x',encoding='utf-8')as f:f.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'receipt':str(path),'sha256':sha(path),'compilation_started':False}),flush=True)
    return receipt



@dataclass(frozen=True,kw_only=True)
class CompilationFinalizerContext:
    """Explicit values from validated main; construction grants no semantic authority."""
    accumulator_lineage: object
    accumulator_patch: object
    actual: object
    args: object
    audio_patch: object
    automatic_manifest: object
    automatic_manifest_path: object
    automatic_patch: object
    cache_identity: object
    clear_provenance: object
    clear_provenance_path: object
    combined_source_population: object
    constructor_provenance: object
    constructor_provenance_path: object
    continuation_patch: object
    converged_patch: object
    diagnostic_target_path: object
    diagnostic_targets: object
    direct_call_metadata: object
    direct_call_patch: object
    dispatch_path: object
    dispatch_rows: object
    dispatch_targets: object
    dispositions: object
    expected: object
    faithful_patch: object
    generated_cache: object
    generated_metadata: object
    generates: object
    hook_boundary_patch: object
    hook_handoff_patch: object
    host_patch: object
    host_proof_idle_patch: object
    indirect_y_generation: object
    indirect_y_patch: object
    leaf_regions_patch: object
    lifecycle_patch: object
    manifest: object
    manifest_targets: object
    marker: object
    memory_bits_patch: object
    native_regions_patch: object
    new_patch_names: object
    out: object
    patch: object
    patch_names: object
    prefix_instructions_patch: object
    prefix_patch: object
    profile_inputs: object
    profile_policy: object
    profile_snapshots: object
    project: object
    redirect_observer_idle_patch: object
    region_metadata: object
    region_metadata_path: object
    region_source_path: object
    reset_bootstrap_generation: object
    return_steps_patch: object
    reviewed_patch: object
    reviewed_report: object
    rmw_patch: object
    rom: object
    runtime: object
    selected_case_patch: object
    selected_task_metadata: object
    selected_task_patch: object
    source: object
    source_redirect_metadata: object
    source_redirect_patch: object
    stack_controls_patch: object
    stack_direct_metadata: object
    stack_direct_patch: object
    stack_primitives_patch: object
    target_marker_digest: object
    target_sources: object
    task_callee_patch: object
    task_scheduler_mode_rows: object
    continuation_record: object
    architectural_native_preparation: object = None


def prepare_architectural_native(context):
    """Validate/generate or reuse private architectural C before the first compile."""
    project=context.project;out=context.out;runtime=context.runtime
    generator=project/'tools/generate_architectural_native.py'
    manifest=project/'config/architectural-native/manifest.json'
    keys=project/'config/architectural-native/native.keys.json'
    for path in(generator,manifest,keys):reject_links(path)
    destination=out/'arch_native';destination.mkdir(exist_ok=False)
    output=destination/'sots_arch78.generated.c';receipt=destination/'architectural-native-generation.json'
    argv=[sys.executable,'-I','-B',str(generator),'--rom',str(context.rom),'--sdk',str(runtime),'--manifest',str(manifest),'--keys',str(keys),'--output',str(output)]
    preparation=context.architectural_native_preparation
    if preparation is not None:
        if preparation.get('status')!='BOUND':raise ValueError('Architectural preparation remains unbound')
        previous=Path(preparation['path']);reject_links(previous)
        if sha(previous)!=preparation['sha256']:raise ValueError('Architectural preparation changed')
        record=json.loads(previous.read_bytes());source=Path(record['output']);reject_links(source)
        if record['generator_sha256']!=sha(generator)or sha(source)!=record['output_sha256']:raise ValueError('Prepared architectural generator/output identity differs')
        argv+=['--reuse-source',str(source),'--reuse-receipt',str(previous)]
    # The isolated authored wrapper validates original ROM, manifest/keys,
    # generator self identity and every normalized SDK import, including ABI.
    with(out/'architectural-native-generation.log').open('xb')as log:
        result=subprocess.run(argv,cwd=project,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
    if result.returncode:raise RuntimeError('Architectural generation refused; preserve generation log and outputs')
    if(out/'architectural-native-generation.log').stat().st_size>5000000:raise RuntimeError('Architectural generation log bound exceeded')
    record=json.loads(receipt.read_bytes())
    if record['status']!='generated_private_architectural_native_unqualified'or record['generator_sha256']!=sha(generator)or record['output_sha256']!=sha(output):raise RuntimeError('Architectural generation receipt differs')
    record.update(receipt_path=str(receipt),receipt_sha256=sha(receipt),output=str(output),legacy_generated_code_regenerated=False,execution_qualified=False,native_AOT_complete=False)
    return record


def finalize_compilation(context):
    """Shared original compile/profile/receipt tail; caller must validate every input."""
    baseline_provenance=baseline_output_provenance(context.args,context.generated_metadata,context.region_metadata)
    if baseline_provenance is not None and context.continuation_record is None:
        raise RuntimeError('Baseline compilation requires a separately reviewed exact-output continuation context')
    accumulator_lineage=context.accumulator_lineage
    accumulator_patch=context.accumulator_patch
    actual=context.actual
    args=context.args
    audio_patch=context.audio_patch
    automatic_manifest=context.automatic_manifest
    automatic_manifest_path=context.automatic_manifest_path
    automatic_patch=context.automatic_patch
    cache_identity=context.cache_identity
    clear_provenance=context.clear_provenance
    clear_provenance_path=context.clear_provenance_path
    combined_source_population=context.combined_source_population
    constructor_provenance=context.constructor_provenance
    constructor_provenance_path=context.constructor_provenance_path
    continuation_patch=context.continuation_patch
    converged_patch=context.converged_patch
    diagnostic_target_path=context.diagnostic_target_path
    diagnostic_targets=context.diagnostic_targets
    direct_call_metadata=context.direct_call_metadata
    direct_call_patch=context.direct_call_patch
    dispatch_path=context.dispatch_path
    dispatch_rows=context.dispatch_rows
    dispatch_targets=context.dispatch_targets
    dispositions=context.dispositions
    expected=context.expected
    faithful_patch=context.faithful_patch
    generated_cache=context.generated_cache
    generated_metadata=context.generated_metadata
    generates=context.generates
    hook_boundary_patch=context.hook_boundary_patch
    hook_handoff_patch=context.hook_handoff_patch
    host_patch=context.host_patch
    host_proof_idle_patch=context.host_proof_idle_patch
    indirect_y_generation=context.indirect_y_generation
    indirect_y_patch=context.indirect_y_patch
    leaf_regions_patch=context.leaf_regions_patch
    lifecycle_patch=context.lifecycle_patch
    manifest=context.manifest
    manifest_targets=context.manifest_targets
    marker=context.marker
    memory_bits_patch=context.memory_bits_patch
    native_regions_patch=context.native_regions_patch
    new_patch_names=context.new_patch_names
    out=context.out
    patch=context.patch
    patch_names=context.patch_names
    prefix_instructions_patch=context.prefix_instructions_patch
    prefix_patch=context.prefix_patch
    profile_inputs=context.profile_inputs
    profile_policy=context.profile_policy
    profile_snapshots=context.profile_snapshots
    project=context.project
    redirect_observer_idle_patch=context.redirect_observer_idle_patch
    region_metadata=context.region_metadata
    region_metadata_path=context.region_metadata_path
    region_source_path=context.region_source_path
    reset_bootstrap_generation=context.reset_bootstrap_generation
    return_steps_patch=context.return_steps_patch
    reviewed_patch=context.reviewed_patch
    reviewed_report=context.reviewed_report
    rmw_patch=context.rmw_patch
    rom=context.rom
    runtime=context.runtime
    selected_case_patch=context.selected_case_patch
    selected_task_metadata=context.selected_task_metadata
    selected_task_patch=context.selected_task_patch
    source=context.source
    source_redirect_metadata=context.source_redirect_metadata
    source_redirect_patch=context.source_redirect_patch
    stack_controls_patch=context.stack_controls_patch
    stack_direct_metadata=context.stack_direct_metadata
    stack_direct_patch=context.stack_direct_patch
    stack_primitives_patch=context.stack_primitives_patch
    target_marker_digest=context.target_marker_digest
    target_sources=context.target_sources
    task_callee_patch=context.task_callee_patch
    task_scheduler_mode_rows=context.task_scheduler_mode_rows
    continuation_record=context.continuation_record
    # Freeze authored artwork and its packaging code before the native build.
    icon_folder=out/'application-icon';icon_folder.mkdir()
    icon_sources=[ROOT/'assets/icons/sots-game.ico',ROOT/'tools/embed_pe_icon.py']
    icon_inputs={str(path.relative_to(ROOT)):sha(path) for path in icon_sources}
    for path in icon_sources:shutil.copy2(path,icon_folder/path.name)
    architectural_native_generation=prepare_architectural_native(context)
    cmake=[args.cmake,'-S',project,'-B',out/'build','-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
      '-DCMAKE_C_COMPILER='+args.cc,'-DCMAKE_CXX_COMPILER='+args.cxx,
      '-DCMAKE_MAKE_PROGRAM='+str(Path(shutil.which(args.ninja)).resolve()),
      '-DSNESRECOMP_ROOT='+str(runtime),'-DSNESRECOMP_FRAME_IMPL=HLE',
      '-DSNESRECOMP_SDL_BACKEND=SDL3','-DSNESRECOMP_ENABLE_NET=OFF']
    cmake.append('-DSOTS_ARCH_NATIVE_SOURCE='+architectural_native_generation['output'])
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
    if sha(Path(architectural_native_generation['output']))!=architectural_native_generation['output_sha256']:raise RuntimeError('Architectural native C changed during compile; preserve unqualified output')
    architectural_native_generation['post_compile_output_sha256']=sha(Path(architectural_native_generation['output']))
    architectural_native_generation['post_compile_output_unchanged']=True
    binary=out/'build/SecretOfTheStarsSNESRecomp.exe'
    if not binary.exists():raise RuntimeError('Windows executable missing after build.')
    # Resource-only packaging happens before the first compiled receipt/profile.
    for path in icon_sources:
        if sha(path)!=icon_inputs[str(path.relative_to(ROOT))] or sha(icon_folder/path.name)!=sha(path):
            raise RuntimeError('Application icon packaging inputs changed; preserve unqualified output.')
    import importlib.util
    icon_spec=importlib.util.spec_from_file_location('sots_frozen_icon',icon_folder/'embed_pe_icon.py')
    icon_module=importlib.util.module_from_spec(icon_spec);icon_spec.loader.exec_module(icon_module)
    icon_bytes,icon_report=icon_module.embed(binary.read_bytes(),(icon_folder/'sots-game.ico').read_bytes())
    binary.write_bytes(icon_bytes)
    if sha(binary)!=icon_report['output_sha256']:raise RuntimeError('Icon packaging output identity mismatch.')
    icon_report['authored_packaging_inputs']=icon_inputs
    (icon_folder/'resource-packaging.json').write_text(json.dumps(icon_report,indent=2)+'\n',encoding='utf-8')

    profile=out/'profile';profile.mkdir();shutil.copy2(binary,profile/binary.name)
    (profile/'config.ini').write_text('[Graphics]\nRenderer=direct3d11\nFullscreen=0\nVSync=1\nNewRenderer=0\nWidescreen=0\n[Sound]\nEnableAudio=1\nAudioFreq=32040\nAudioChannels=2\nAudioSamples=512\n[General]\nAutosave=0\nSkipLauncher=1\n',encoding='ascii')
    (profile/'foundation.ini').write_text('[Enhancements]\nEnhancedPixels=1\nBattleInfo=1\nFastMenus=1\nJournal=1\nNavigationMap=1\nNavigationMapObjective=1\nExperimentalFieldWide=0\nExperimentalFieldActors=0\nNativeClear=0\nNativeColumns=0\nHdMenuFrames=0\nXpMultiplierPercent=100\nGoldMultiplierPercent=100\nMovementSpeedPercent=200\nStartingShopDiscount=1\nFastForwardToggle=0\nLegacyControllerGestures=1\n',encoding='ascii')
    assert sha(rom)==expected
    state_source=(project/'src/foundation_state.c').read_text()
    schema=re.search(r'#define FOUNDATION_VERSION (\d+)u',state_source)
    state_identity=re.search(r'FoundationStateIdentity\(void\).*?return "([^"]+)"',state_source)
    if not schema or not state_identity or 'header[1] < 1 || header[1] > FOUNDATION_VERSION' not in state_source:
        raise RuntimeError('Checkpoint contract changed; preserve this build and explicitly update its compatibility declaration before adoption.')
    schema_version=int(schema.group(1))
    result={'status':'compiled_unqualified','public_build':True,'executable_sha256':sha(binary),
      'application_icon_packaging':icon_report,
      'architectural_native_generation':architectural_native_generation,
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
      'selected_task_resume_generation':{'metadata_format':RUNTIME_GENERATION_FORMATS['task'],'mode_rows':len(selected_task_metadata['rows']),'selected_architectural_member_rows':len(selected_task_metadata['selected_architectural_members']['rows']),'selected_architectural_call_rows':len(selected_task_metadata['selected_architectural_calls']['rows']),'retained_parent_architectural_member_rows':len(selected_task_metadata['retained_parent_architectural_members']['rows']),'total_scheduler_mode_rows':task_scheduler_mode_rows,'distinct_pcs':len({r['pc24']for r in selected_task_metadata['rows']}),'metadata_sha256':sha(project/'src/gen/native_task_resume.json'),'source_sha256':sha(project/'src/gen/native_task_resume_v2.c'),'execution_qualified':False},
      'direct_call_prefix_generation':direct_call_metadata,
      'reset_bootstrap_generation':reset_bootstrap_generation,
      'combined_source_population':combined_source_population,
      'native_region_generation':{'cache_format':generated_metadata['format_version'],'metadata_format':region_metadata['format_version'],'stack_control_contract':region_metadata['stack_control_contract'],'result_contract':region_metadata['result_contract'],'instruction_source':region_metadata['instruction_source'],'source_cfg_scheduler_rows':len(region_metadata['regions']),'metadata_sha256':sha(region_metadata_path),'source_sha256':sha(region_source_path),'diagnostic_disable':'SNESRECOMP_DISABLE_NATIVE_REGIONS=1','execution_qualified':False},
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
        result['local_profile_generation']={'enabled':not args.profile_audit_only,'audit_enabled':True,'mode':'audit_only' if args.profile_audit_only else 'analysis_roots','generation_policy':profile_policy,'default':False,'capture_identity':profile_inputs['identity'],
          'original_receipt_sha256':sha(profile_inputs['receipt']),'original_program_manifest_sha256':sha(profile_inputs['program']),
          'original_generator_digest':profile_inputs['original_generator_digest'],'original_config_digest':profile_inputs['original_config_digest'],
          'original_runtime_dir':str(profile_inputs['source_runtime']),
          'analyzer_path':str(profile_inputs['analyzer']),'analyzer_sha256':sha(profile_inputs['analyzer']),
          'capture_ids':profile_inputs['captures'],'profile_inputs':[{'original_path':str(original),'sha256':sha(copy),'snapshot':copy.relative_to(out).as_posix()}for original,copy in zip(profile_inputs['profiles'],profile_snapshots)],
          'protected_source_provenance':profile_inputs['protected'],'ingest_report':'profile-ingest.json','ingest_sha256':sha(out/'profile-ingest.json'),
          'target_generator_digest':generated_metadata['generator_digest'],'target_config_digest':generated_metadata['config_digest'],
          'generated_cache_sha256':sha(generated_cache),'emitted_outputs':{p.relative_to(out).as_posix():sha(p)for p in(project/'src/gen').rglob('*')if p.is_file()},
          'new_observed_root_contexts':[] if args.profile_audit_only else[r for r in automatic_manifest['roots']if key(r)not in original_roots],
          'actual_root_contexts_new_vs_capture':[r for r in automatic_manifest['roots']if key(r)not in original_roots],
          'admission_is_execution_qualification':False,'historical_or_legacy_import':False,
          'limits':('Exact current61 captures were validated/audited and immutably snapshotted only. SDK candidate roots/exclusions remain unpromoted and were not forwarded to generation; source241 supplies the independently source-certified conversion; source218 remains deferred. No claim that observed roots became native.' if args.profile_audit_only else 'Optional exact original-build local observations seed normal pinned analysis. CFG authority/force-LLE remain authoritative; observations and compiled source are not gameplay or release qualification. No captures are bundled into public source.')}
    if baseline_provenance is not None:
        result['architecture_discovery_baseline']=baseline_provenance
        result['compilation_lineage']={'helper_sha256':sha(Path(__file__)),'runtime_marker_sha256':target_marker_digest,'reviewed_generation_continuation':continuation_record,'generation_commands':[list(map(str,cmd))for cmd in generates],'generated_cache_sha256':sha(generated_cache)}
    if continuation_record is not None:
        result['same_output_continuation']=continuation_record
    with(out/'source-build-receipt.json').open('x',encoding='utf-8')as receipt_file:receipt_file.write(json.dumps(result,indent=2)+'\n')
    print('Built: '+str(binary));print('Fresh profile: '+str(profile))
    print('Run from the fresh profile: SecretOfTheStarsSNESRecomp.exe --no-launcher --rom "<your original ROM path>"')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--runtime-prepare-only',action='store_true',help='Prepare verified patched runtime only; no project snapshot, analyzer, generation or compilation')
    p.add_argument('--source-seed-prepare',action='store_true',help='Prepare source-only analysis with explicit requested roots; no historical capture claims')
    p.add_argument('--analysis-roots-file',type=Path,action='append',default=[],help='Source-analysis root requests, independently analyzed; never execution authority')
    p.add_argument('--profile-manifest',type=Path,action='append',default=[],help='Optional owned local Tier2v2 JSON checkpoint/JSONL journal (repeatable); never a release default')
    p.add_argument('--profile-audit-only',action='store_true',help='Validate/snapshot exact current61 captures and record unpromoted SDK candidates without forwarding profiles as generation roots')
    p.add_argument('--architecture-discovery-baseline',action='store_true',help='Fresh original static discovery view for architecture families; requires profile seed preparation and stops uncompiled for actual delta review')
    p.add_argument('--profile-seed-prepare',action='store_true',help='Explicit source-analysis epoch: seed validated profiles, freeze complete actual unreviewed generated population, then stop before legacy population assertions and compilation')
    p.add_argument('--profile-build-receipt',type=Path,help='Original public source-build receipt belonging to these captures')
    p.add_argument('--profile-program-manifest',type=Path,help='Exact original generated program manifest belonging to these captures')
    p.add_argument('--profile-analyzer',type=Path,help='Exact existing original native analyzer; actual generator digest must match captured build, no cache path guessing')
    p.add_argument('--profile-runtime-dir',type=Path,help='Explicit unchanged original five-patch capture runtime, separately validated from target runtime')
    p.add_argument('--profile-source-binding',type=Path,help='Explicit root-reviewed owned current61 capture binding; never a default')
    p.add_argument('--profile-source-binding-sha256',help='Exact reviewed profile source binding SHA256')
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
    validate_seed_preparation_mode(args)
    if args.runtime_prepare_only and (args.source_seed_prepare or args.profile_seed_prepare or args.profile_audit_only or args.profile_manifest or args.analysis_roots_file):raise ValueError('Runtime-only preparation cannot consume generation/profile inputs')
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
    profile_inputs=profile_preflight(args.profile_manifest,args.profile_build_receipt,args.profile_program_manifest,expected,source,args.profile_analyzer,args.profile_source_binding,args.profile_source_binding_sha256)
    capture_runtime=source_runtime_preflight(args.profile_runtime_dir,profile_inputs)
    profile_report=profile_audit(profile_inputs,capture_runtime,source)
    profile_policy=profile_generation_policy(profile_inputs,args.profile_audit_only,capture_runtime,source)
    if profile_report is not None:profile_report['generation_policy']=profile_policy
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
    if args.runtime_prepare_only:
        record={'status':'runtime_prepared_no_generation','helper_sha256':sha(Path(__file__)),'runtime_dir':str(runtime.resolve()),'runtime_pin':RUNTIME_PIN,'runtime_cache_identity':cache_identity,'runtime_marker':str(marker.resolve()),'runtime_marker_sha256':target_marker_digest,'runtime_patched_sources':target_sources,'runtime_extensions':runtime_extension_records(),'submodule_pins':pins,'generation_performed':False,'compilation_started':False,'native_execution_qualified':False,'native_AOT_complete':False}
        with(out/'runtime-preparation.json').open('x',encoding='utf-8')as stream:stream.write(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record),flush=True)
        return
    project=out/'project'
    manifest,actual=snapshot_authored(source,project)
    reviewed_report=reviewed_roots_preflight(runtime,project,identity,args.reviewed_roots)
    profile_snapshots=snapshot_profiles(profile_inputs,out)
    if profile_report is not None:
        with(out/'profile-ingest.json').open('x',encoding='utf-8')as report_file:report_file.write(json.dumps(profile_report,indent=2)+'\n')
    (project/'mods/preloaded/packages').mkdir(parents=True)
    print('Generating private local code from the verified ROM.',flush=True)
    seed_pins={str(p):sha(profile_file(p,1024*1024)) for p in args.analysis_roots_file}
    generation_profiles=[] if args.profile_audit_only else profile_snapshots
    generates=generation_commands(runtime,project,rom,identity,generation_profiles,args.emit_proven_prefixes,args.reviewed_roots,args.certify_converged_exits,args.native_continuations,args.native_direct_calls,args.architecture_discovery_baseline,args.analysis_roots_file)
    generation_env={k:v for k,v in os.environ.items()if not k.startswith('SNESRECOMP_')}
    generation_env['PYTHONDONTWRITEBYTECODE']='1'
    if profile_inputs is not None:generation_env['SNESRECOMP_NATIVE_ANALYZER']=str(profile_inputs['analyzer'])
    with (out/'generate.log').open('w',encoding='utf-8') as log:
        for generate in generates:
            r=subprocess.run(list(map(str,generate)),cwd=project,stdout=log,stderr=subprocess.STDOUT,env=generation_env)
            if r.returncode:raise RuntimeError('Generation failed; inspect '+str(out/'generate.log'))
    if any(sha(Path(p))!=digest for p,digest in seed_pins.items()):raise RuntimeError('Analysis seed changed during generation')
    automatic_manifest_path=project/'src/gen/program_manifest.json'
    reject_links(automatic_manifest_path)
    automatic_manifest=json.loads(automatic_manifest_path.read_text(encoding='utf-8'))
    generated_cache=project/'src/gen/.snesrecomp-cache.json'
    reject_links(generated_cache);generated_metadata=json.loads(generated_cache.read_bytes())
    if generated_metadata.get('format_version')!=target_generation_formats(args)['cache'] or generated_metadata.get('module')!={'id':'main','prefix':''}or generated_metadata.get('outputs',{}).get('program_manifest.json')!=sha(automatic_manifest_path):
        raise RuntimeError('Target generated cache/module identity mismatch; preserve build.')
    if args.profile_seed_prepare:
        generate_profile_seed_auxiliary_outputs(project,out,rom,expected,actual)
        freeze_profile_seed_preparation(out,project,runtime,rom,expected,actual,target_sources,target_marker_digest,profile_inputs,profile_report,profile_snapshots,generated_metadata,automatic_manifest,args)
        return
    if set(generated_metadata.get('outputs',{}))!=set(('bank00_v2.c', 'bank01_part00_v2.c', 'bank01_part01_v2.c', 'bank01_part02_v2.c', 'bank01_part03_v2.c', 'bank01_part06_v2.c', 'bank01_part08_v2.c', 'bank01_part09_v2.c', 'bank01_part0a_v2.c', 'bank01_part0b_v2.c', 'bank01_part0c_v2.c', 'bank01_part0d_v2.c', 'bank01_part0e_v2.c', 'bank02_v2.c', 'bank1c_v2.c', 'dispatch_v2.c', 'module_v2.c', 'native_regions.json', 'native_regions_v2.c', 'native_source_redirect.json', 'native_source_redirect_v2.c', 'native_task_resume.json', 'native_task_resume_v2.c', 'program_manifest.json', 'unresolved_stubs_v2.c')):raise RuntimeError('Source-first25 generated output allowlist differs.')
    for name,digest in generated_metadata.get('outputs',{}).items():
        if Path(name).is_absolute()or'..'in Path(name).parts:raise RuntimeError('Target generated output escapes build; preserve build.')
        output=project/'src/gen'/name;reject_links(output)
        if sha(output)!=digest:raise RuntimeError('Target generated output/cache mismatch; preserve build.')
    validate_selected_task_recipe(ROOT/'native/foundation/recomp')
    validate_source_redirect_recipe(ROOT/'native/foundation/recomp')
    combined_source_population=prepare_combined_source_population(project/'src/gen',out,rom,runtime,project/'recomp')
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
    direct_call_metadata=validate_direct_call_outputs(project/'src/gen',generated_metadata,expected,rom,args.native_direct_calls,runtime)
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
    finalize_compilation(CompilationFinalizerContext(
        accumulator_lineage=accumulator_lineage,
        accumulator_patch=accumulator_patch,
        actual=actual,
        args=args,
        audio_patch=audio_patch,
        automatic_manifest=automatic_manifest,
        automatic_manifest_path=automatic_manifest_path,
        automatic_patch=automatic_patch,
        cache_identity=cache_identity,
        clear_provenance=clear_provenance,
        clear_provenance_path=clear_provenance_path,
        combined_source_population=combined_source_population,
        constructor_provenance=constructor_provenance,
        constructor_provenance_path=constructor_provenance_path,
        continuation_patch=continuation_patch,
        converged_patch=converged_patch,
        diagnostic_target_path=diagnostic_target_path,
        diagnostic_targets=diagnostic_targets,
        direct_call_metadata=direct_call_metadata,
        direct_call_patch=direct_call_patch,
        dispatch_path=dispatch_path,
        dispatch_rows=dispatch_rows,
        dispatch_targets=dispatch_targets,
        dispositions=dispositions,
        expected=expected,
        faithful_patch=faithful_patch,
        generated_cache=generated_cache,
        generated_metadata=generated_metadata,
        generates=generates,
        hook_boundary_patch=hook_boundary_patch,
        hook_handoff_patch=hook_handoff_patch,
        host_patch=host_patch,
        host_proof_idle_patch=host_proof_idle_patch,
        indirect_y_generation=indirect_y_generation,
        indirect_y_patch=indirect_y_patch,
        leaf_regions_patch=leaf_regions_patch,
        lifecycle_patch=lifecycle_patch,
        manifest=manifest,
        manifest_targets=manifest_targets,
        marker=marker,
        memory_bits_patch=memory_bits_patch,
        native_regions_patch=native_regions_patch,
        new_patch_names=new_patch_names,
        out=out,
        patch=patch,
        patch_names=patch_names,
        prefix_instructions_patch=prefix_instructions_patch,
        prefix_patch=prefix_patch,
        profile_inputs=profile_inputs,
        profile_policy=profile_policy,
        profile_snapshots=profile_snapshots,
        project=project,
        redirect_observer_idle_patch=redirect_observer_idle_patch,
        region_metadata=region_metadata,
        region_metadata_path=region_metadata_path,
        region_source_path=region_source_path,
        reset_bootstrap_generation=reset_bootstrap_generation,
        return_steps_patch=return_steps_patch,
        reviewed_patch=reviewed_patch,
        reviewed_report=reviewed_report,
        rmw_patch=rmw_patch,
        rom=rom,
        runtime=runtime,
        selected_case_patch=selected_case_patch,
        selected_task_metadata=selected_task_metadata,
        selected_task_patch=selected_task_patch,
        source=source,
        source_redirect_metadata=source_redirect_metadata,
        source_redirect_patch=source_redirect_patch,
        stack_controls_patch=stack_controls_patch,
        stack_direct_metadata=stack_direct_metadata,
        stack_direct_patch=stack_direct_patch,
        stack_primitives_patch=stack_primitives_patch,
        target_marker_digest=target_marker_digest,
        target_sources=target_sources,
        task_callee_patch=task_callee_patch,
        task_scheduler_mode_rows=task_scheduler_scope_count(selected_task_metadata),
        continuation_record=None,
    ))


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
