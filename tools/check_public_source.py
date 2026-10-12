"""ROM-free checks for the exact files Git will publish."""
from pathlib import Path, PurePosixPath
import ast
import hashlib
import json
import re
import subprocess
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {
    '.sfc', '.smc', '.srm', '.sav', '.exe', '.dll', '.pdb', '.obj', '.o',
    '.a', '.lib', '.zip', '.7z', '.rar', '.bin', '.pcm', '.wav', '.flac',
    '.ogg', '.mp3', '.bmp', '.png', '.jpg', '.mp4', '.webm', '.pem', '.key',
}
SECRET = re.compile(
    rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}'
    rb'|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)'
)

# Owner-requested documentation captures only; game payload/art packs stay out.
DOCUMENTATION_CAPTURES = {
    'docs/screenshots/widescreen-world.png',
    'docs/screenshots/battle-health-sidebar.png',
    'docs/screenshots/quest-journal.png',
    'docs/screenshots/companion-enhancements.png',
    'docs/screenshots/companion-hotkeys.png',
    'docs/screenshots/navigation-map.png',
}


def capture_dimensions(data):
    """Accept bounded ordinary PNG captures, with no metadata/extra payload."""
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data) > 5 * 1024 * 1024:
        raise ValueError('Invalid or oversized documentation capture')
    offset = 8
    dimensions = None
    pixel_bytes = 0
    image_data = []
    ended = False
    while offset + 12 <= len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('Truncated PNG chunk')
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from('>I', data, offset + 8 + length)[0]
        if kind not in {b'IHDR', b'IDAT', b'IEND', b'sRGB', b'gAMA', b'cHRM', b'pHYs'}:
            raise ValueError('Unexpected capture chunk')
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        if offset == 8:
            if kind != b'IHDR' or length != 13:
                raise ValueError('Missing PNG header')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if not (256 <= width <= 2048 and 224 <= height <= 1600 and depth == 8
                    and color in (2, 6) and compression == filtering == interlace == 0):
                raise ValueError('Unsupported capture layout')
            dimensions = (width, height)
            pixel_bytes = 3 if color == 2 else 4
        elif kind == b'IHDR':
            raise ValueError('Repeated PNG header')
        elif kind == b'IDAT':
            image_data.append(body)
        offset = end
        if kind == b'IEND':
            if length or offset != len(data):
                raise ValueError('Unexpected trailing capture payload')
            ended = True
            break
    if not ended or dimensions is None:
        raise ValueError('Incomplete PNG capture')
    row_bytes = dimensions[0] * pixel_bytes + 1
    expected = row_bytes * dimensions[1]
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(b''.join(image_data), expected + 1)
    if (len(pixels) != expected or not decoder.eof or decoder.unused_data
            or decoder.unconsumed_tail or any(v > 4 for v in pixels[::row_bytes])):
        raise ValueError('Invalid or oversized PNG pixel stream')
    return dimensions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_experiment_manifest(root, name, tracked):
    """Check an authored experiment snapshot, without granting qualification."""
    errors = []
    try:
        manifest = json.loads((root / name).read_text(encoding='utf-8'))
        inputs = manifest['source_sha256']
        if not isinstance(inputs, dict) or not inputs:
            raise ValueError('source_sha256 must be a nonempty object')
        base = PurePosixPath(name).parent
        for relative, digest in inputs.items():
            path = PurePosixPath(relative)
            if (not relative or path.is_absolute() or '..' in path.parts
                    or '\\' in relative or ':' in relative
                    or not isinstance(digest, str)
                    or not re.fullmatch(r'[0-9a-f]{64}', digest)):
                errors.append('Invalid experiment input: ' + name + ' -> ' + relative)
                continue
            full = (base / path).as_posix()
            source = root / full
            if (full not in tracked or not source.is_file() or source.is_symlink()
                    or sha(source) != digest):
                errors.append('Experiment snapshot mismatch: ' + full)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append('Invalid experiment manifest: ' + name + ': ' + str(exc))
    return errors


ACCUMULATOR_SOURCE_REVIEW = {'patch_sha256': 'aee2cf5169754cf5a9d7c652387e47055643ad7adc0c6e5b2df2eb8bf5fea216', 'emitter_sha256': '1d667783bd9deae9ac52507aeaf13dae4ba59abd6ec7e5590d6c4c9c9b74dd8b', 'offline_unit_report_sha256': '1c2dea4f5c973ce732adebdafe5331fd09d5411088aadfab2674e06b316bc267', 'predecessor_crlf_sha256': '9848f8cdcc1c546b3830924551b8cba2aef43be8d77a934122ca4035b4a775a3', 'predecessor_lf_sha256': '8b395ddd799dc556a4955fb1d0c427509325e93e20447410906b126992183622', 'patch_output_crlf_sha256': 'b70f61231eec6ea4fad829a06c5fd766c716d96d79842a08fb19974834bf322d', 'runtime_file': 'recompiler/v2/emit_function.py', 'scope': 'Exact one-byte ASL/LSR/ROL/ROR accumulator admission through existing faithful bodies; memory RMW/INC/DEC remain original. Original buses, clocks, callback boundaries and serialized ABI remain unchanged.', 'normalization': 'Exact source-bound CRLF-to-LF only; no instruction/source-line changes.', 'qualification': 'Reviewed offline instruction/source proof only; actual public compilation and exact-artifact gameplay qualification are separate.'}


def check_accumulator_source_audit(patch, provenance, helper):
    """Bind authored patch/source metadata; no runtime or ROM execution."""
    errors = []
    expected = ACCUMULATOR_SOURCE_REVIEW
    try:
        if (sha(patch) != expected['patch_sha256']
                or provenance.get('runtime_accumulator_patch_sha256') != expected['patch_sha256']
                or provenance.get('runtime_accumulator_source_review') != expected):
            errors.append('Accumulator patch/source review differs from the audited snapshot.')
        content = patch.read_text(encoding='utf-8')
        # An ordinary unified patch has no diff --git header. Both file headers
        # must occur exactly once; exact digest binds every hunk and all bytes.
        before = re.findall(r'^--- (.+)$', content, re.M)
        after = re.findall(r'^\+\+\+ (.+)$', content, re.M)
        git_headers = re.findall(r'^diff --git (.+)$', content, re.M)
        target = expected['runtime_file']
        if (before != ['a/' + target] or after != ['b/' + target]
                or git_headers or len(re.findall(r'^@@ ', content, re.M)) != 3):
            errors.append('Accumulator patch must retain its exact one-file/three-hunk scope.')
        constants = {}
        for node in ast.parse(helper).body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for name in node.targets:
                    if isinstance(name, ast.Name):
                        constants[name.id] = node.value.value
        bindings = {
            'ACCUMULATOR_PATCH_SHA256': 'patch_sha256',
            'ACCUMULATOR_EMITTER_SHA256': 'emitter_sha256',
            'ACCUMULATOR_UNIT_SHA256': 'offline_unit_report_sha256',
            'ACCUMULATOR_PREDECESSOR_CRLF_SHA256': 'predecessor_crlf_sha256',
            'ACCUMULATOR_PREDECESSOR_LF_SHA256': 'predecessor_lf_sha256',
            'ACCUMULATOR_OUTPUT_CRLF_SHA256': 'patch_output_crlf_sha256',
        }
        if any(constants.get(name) != expected[field] for name, field in bindings.items()):
            errors.append('Accumulator helper/source-review full hashes differ.')
    except (OSError, UnicodeError, SyntaxError, TypeError, ValueError) as exc:
        errors.append('Invalid accumulator source audit: ' + str(exc))
    return errors


def main():
    tracked = subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=ROOT
    ).decode('utf-8').split('\0')
    tracked = [name for name in tracked if name]
    if not tracked:
        raise ValueError('No tracked files. Stage the intended public source first.')
    errors = []
    python_count = 0
    capture_count = 0
    if 'docs/screenshots/captures.json' not in tracked:
        errors.append('Capture provenance manifest is not tracked')
    capture_manifest = json.loads((ROOT / 'docs/screenshots/captures.json').read_text(encoding='utf-8'))
    if set(capture_manifest['captures']) != DOCUMENTATION_CAPTURES:
        errors.append('Unexpected documentation capture manifest')
    for name in tracked:
        parts = PurePosixPath(name).parts
        path = ROOT / name
        if (parts[0] in {'local', 'research', 'fixtures'}
                or 'gen' in parts or name.endswith('/recomp/funcs.h')
                or any(part in {'bin', 'obj', '__pycache__', 'saves'} for part in parts)
                or ('screenshots' in parts and name not in DOCUMENTATION_CAPTURES
                    and name != 'docs/screenshots/captures.json')
                or (PurePosixPath(name).suffix.lower() in FORBIDDEN_SUFFIXES
                    and name not in DOCUMENTATION_CAPTURES)
                or re.search(r'\.state', name, re.I)
                or PurePosixPath(name).name.startswith('.env')):
            errors.append('Forbidden publication path: ' + name)
        if path.is_symlink():
            errors.append('Symlink requires publication review: ' + name)
            continue
        data = path.read_bytes()
        if name in DOCUMENTATION_CAPTURES:
            # Only these reviewed screenshots bypass the binary/source check.
            try:
                dimensions = capture_dimensions(data)
                entry = capture_manifest['captures'][name]
                if sha(path) != entry['sha256'] or list(dimensions) != entry['dimensions']:
                    raise ValueError('Capture differs from provenance manifest')
                capture_count += 1
            except (KeyError, TypeError, ValueError, zlib.error) as exc:
                errors.append('Invalid documentation capture: ' + name + ': ' + str(exc))
            continue
        if data.startswith((b'MZ', b'\x7fELF', b'PK\x03\x04')) or b'\0' in data:
            errors.append('Unexpected binary content: ' + name)
        if SECRET.search(data):
            errors.append('Potential credential material: ' + name)
        if name.endswith('.py'):
            ast.parse(data.decode('utf-8-sig'), filename=name)
            python_count += 1
    counts = {}
    experiments = [name for name in tracked
                   if name.startswith('experiments/')
                   and name.endswith('/experiment-manifest.json')]
    for name in experiments:
        errors.extend(check_experiment_manifest(ROOT, name, tracked))
    for base in ('native/foundation', 'Companion'):
        manifest = json.loads((ROOT / base / 'authored-files.json').read_text(encoding='utf-8'))
        counts[base] = len(manifest)
        for name, digest in manifest.items():
            full = base + '/' + name
            if full not in tracked or sha(ROOT / full) != digest:
                errors.append('Authored snapshot mismatch: ' + full)
    provenance = json.loads((ROOT / 'SOURCE-PROVENANCE.json').read_text(encoding='utf-8'))
    # Current generation formats are explicit authored declarations. Historical
    # predecessor patch formats remain pinned inside their source bindings.
    try:
        import importlib.util
        tree=ast.parse((ROOT/'tools/build_public_foundation.py').read_text(encoding='utf8'))
        formats=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='RUNTIME_GENERATION_FORMATS'for t in n.targets))
        if formats!={'cache':26,'normal':12,'task':5,'redirect':1}or formats!=provenance.get('current_runtime_generation_formats'):raise ValueError('Current runtime formats differ.')
        spec=importlib.util.spec_from_file_location('public_runtime_bindings',ROOT/'tools/build_public_foundation.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        bindings=module.runtime_extension_bindings()
        expected=('runtime-original-call-retention','runtime-long-jump-stack-indirect-y','runtime-indirect-control','runtime-task-original-prefix','runtime-interrupt-return')
        if tuple(r['name']for r in module.RUNTIME_EXTENSION_SPECS)!=expected or len(bindings)!=5 or provenance.get('current_ordered_runtime_patch_count')!=35:raise ValueError('Current extension sequence differs.')
        for name in ('runtime-selected-task-cases','runtime-direct-call-prefix',*expected):
            binding=ROOT/'patches'/(name+'.json');patch=binding.with_suffix('.patch');v=json.loads(binding.read_bytes())
            key=name.removeprefix('runtime-').replace('-','_')
            if patch.relative_to(ROOT).as_posix()not in tracked or binding.relative_to(ROOT).as_posix()not in tracked or sha(patch)!=v['patch_sha256']or sha(patch)!=provenance[key+'_patch_sha256']or sha(binding)!=provenance[key+'_source_binding_sha256']:raise ValueError('Current patch identity differs: '+name)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,StopIteration) as exc:
        errors.append('Current grouped runtime source binding differs: '+str(exc))
    if provenance['native_version'] != (ROOT / 'native/foundation/VERSION').read_text(encoding='utf-8').strip():
        errors.append('Native version differs from source provenance.')
    companion_version = ET.parse(ROOT / 'Companion/Companion.csproj').findtext('.//Version')
    if provenance['companion_version'] != companion_version:
        errors.append('Companion version differs from source provenance.')
    for name, digest in provenance['verbatim_notices'].items():
        full = 'licenses/' + name
        if full not in tracked or sha(ROOT / full) != digest:
            errors.append('Retained notice mismatch: ' + full)
    patch = ROOT / 'patches/runtime-foundation.patch'
    if sha(patch) != provenance['runtime_patch_sha256']:
        errors.append('Runtime patch differs from the recorded snapshot.')
    host_patch = ROOT / 'patches/runtime-navigation-map.patch'
    if sha(host_patch) != provenance.get('host_navigation_patch_sha256'):
        errors.append('Navigation input patch differs from the audited snapshot.')
    pins = (ROOT / 'native/foundation/framework_pins.txt').read_text(encoding='utf-8')
    helper = (ROOT / 'tools/build_public_foundation.py').read_text(encoding='utf-8')
    if sha(host_patch) not in helper:
        errors.append('Navigation patch audit hash is missing from the build helper.')
    faithful_patch = ROOT / 'patches/runtime-faithful-clear.patch'
    if ('patches/runtime-faithful-clear.patch' not in tracked
            or not faithful_patch.is_file()
            or sha(faithful_patch) != provenance.get('faithful_instruction_patch_sha256')):
        errors.append('Faithful instruction patch differs from the audited snapshot.')
    elif sha(faithful_patch) not in helper:
        errors.append('Faithful instruction patch audit hash is missing from the build helper.')
    audio_patch = ROOT / 'patches/runtime-modal-audio.patch'
    if ('patches/runtime-modal-audio.patch' not in tracked or not audio_patch.is_file()
            or sha(audio_patch) != provenance.get('host_modal_audio_patch_sha256')):
        errors.append('Modal audio patch differs from the audited snapshot.')
    elif sha(audio_patch) not in helper:
        errors.append('Modal audio audit hash is missing from the build helper.')
    automatic_patch = ROOT / 'patches/runtime-automatic-faithful.patch'
    if ('patches/runtime-automatic-faithful.patch' not in tracked or not automatic_patch.is_file()
            or sha(automatic_patch) != provenance.get('automatic_faithful_patch_sha256')):
        errors.append('Automatic instruction patch differs from the audited snapshot.')
    elif sha(automatic_patch) not in helper:
        errors.append('Automatic instruction patch audit hash is missing from the build helper.')
    for patch_name, identity, label in (
            ('runtime-paired-lifecycle.patch', 'lifecycle_patch_sha256', 'Paired return lifecycle'),
            ('runtime-proven-prefix.patch', 'prefix_patch_sha256', 'Proved instruction prefix'),
            ('runtime-faithful-hook-boundary.patch', 'faithful_hook_boundary_patch_sha256', 'Original callback boundary'),
            ('runtime-reviewed-roots.patch', 'reviewed_roots_patch_sha256', 'Reviewed analysis roots'),
            ('runtime-converged-exits.patch', 'converged_exit_patch_sha256', 'Converged exit certification'),
            ('runtime-accumulator.patch', 'runtime_accumulator_patch_sha256', 'Faithful accumulator admission')):
        extension = ROOT / 'patches' / patch_name
        if ('patches/' + patch_name not in tracked or not extension.is_file()
                or sha(extension) != provenance.get(identity)):
            errors.append(label + ' patch differs from the audited snapshot.')
        elif sha(extension) not in helper:
            errors.append(label + ' audit hash is missing from the build helper.')
    errors.extend(check_accumulator_source_audit(
        ROOT / 'patches/runtime-accumulator.patch', provenance, helper))
    continuation=ROOT/'patches/runtime-native-continuations.patch'
    continuation_binding=ROOT/'patches/runtime-native-continuations.json'
    try:
        binding=json.loads(continuation_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',continuation.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-continuations.patch' not in tracked
                or 'patches/runtime-native-continuations.json' not in tracked
                or sha(continuation)!=binding['patch_sha256']
                or sha(continuation)!=provenance.get('native_continuation_patch_sha256')
                or sha(continuation_binding)!=provenance.get('native_continuation_source_binding_sha256')
                or len(names)!=12 or set(names)!=set(binding['files'])
                or 'validate_continuation_runtime' not in helper
                or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes' not in helper):
            errors.append('Native continuation patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native continuation source binding unreadable: '+str(error))
    rmw=ROOT/'patches/runtime-memory-rmw.patch'
    rmw_source=ROOT/'patches/runtime-memory-rmw.json'
    try:
        binding=json.loads(rmw_source.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',rmw.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-memory-rmw.patch' not in tracked
                or 'patches/runtime-memory-rmw.json' not in tracked
                or sha(rmw)!=binding['patch_sha256']
                or sha(rmw)!=provenance.get('memory_rmw_patch_sha256')
                or sha(rmw_source)!=provenance.get('memory_rmw_source_binding_sha256')
                or len(names)!=5 or set(names)!=set(binding['files'])
                or sha(rmw) not in helper or 'validate_final_runtime' not in helper):
            errors.append('Memory RMW patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Memory RMW source binding unreadable: '+str(error))
    rmw=ROOT/'patches/runtime-memory-bits.patch'
    rmw_source=ROOT/'patches/runtime-memory-bits.json'
    try:
        binding=json.loads(rmw_source.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',rmw.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-memory-bits.patch' not in tracked
                or 'patches/runtime-memory-bits.json' not in tracked
                or sha(rmw)!=binding['patch_sha256']
                or sha(rmw)!=provenance.get('memory_bits_patch_sha256')
                or sha(rmw_source)!=provenance.get('memory_bits_source_binding_sha256')
                or len(names)!=3 or set(names)!=set(binding['files'])
                or sha(rmw) not in helper or 'validate_memory_bits_patch' not in helper):
            errors.append('Memory bits patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Memory bits source binding unreadable: '+str(error))
    region_patch=ROOT/'patches/runtime-native-regions.patch'
    region_binding=ROOT/'patches/runtime-native-regions.json'
    try:
        binding=json.loads(region_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',region_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-regions.patch' not in tracked
                or 'patches/runtime-native-regions.json' not in tracked
                or sha(region_patch)!=binding['patch_sha256']
                or sha(region_patch)!=provenance.get('native_regions_patch_sha256')
                or sha(region_binding)!=provenance.get('native_regions_source_binding_sha256')
                or len(names)!=6 or set(names)!=set(binding['files'])
                or sha(region_patch) not in helper or 'validate_native_regions_patch' not in helper):
            errors.append('Native regions patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native regions source binding unreadable: '+str(error))
    leaf_patch=ROOT/'patches/runtime-native-leaf-regions.patch'
    leaf_binding=ROOT/'patches/runtime-native-leaf-regions.json'
    try:
        binding=json.loads(leaf_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',leaf_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-leaf-regions.patch' not in tracked
                or 'patches/runtime-native-leaf-regions.json' not in tracked
                or sha(leaf_patch)!=binding['patch_sha256']
                or sha(leaf_patch)!=provenance.get('native_leaf_regions_patch_sha256')
                or sha(leaf_binding)!=provenance.get('native_leaf_regions_source_binding_sha256')
                or len(names)!=3 or set(names)!=set(binding['files'])
                or sha(leaf_patch) not in helper or 'validate_leaf_regions_patch' not in helper):
            errors.append('Native leaf region patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native leaf region source binding unreadable: '+str(error))
    handoff_patch=ROOT/'patches/runtime-native-hook-handoff.patch'
    handoff_binding=ROOT/'patches/runtime-native-hook-handoff.json'
    try:
        binding=json.loads(handoff_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',handoff_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-hook-handoff.patch' not in tracked
                or 'patches/runtime-native-hook-handoff.json' not in tracked
                or sha(handoff_patch)!=binding['patch_sha256']
                or sha(handoff_patch)!=provenance.get('native_hook_handoff_patch_sha256')
                or sha(handoff_binding)!=provenance.get('native_hook_handoff_source_binding_sha256')
                or len(names)!=4 or set(names)!=set(binding['files'])
                or sha(handoff_patch) not in helper or 'validate_hook_handoff_patch' not in helper):
            errors.append('Native hook handoff patch/source binding differs from the current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native hook handoff source binding unreadable: '+str(error))
    stack_patch=ROOT/'patches/runtime-native-stack-primitives.patch'
    stack_binding=ROOT/'patches/runtime-native-stack-primitives.json'
    try:
        binding=json.loads(stack_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',stack_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-stack-primitives.patch' not in tracked
                or 'patches/runtime-native-stack-primitives.json' not in tracked
                or sha(stack_patch)!=binding['patch_sha256']
                or sha(stack_patch)!=provenance.get('native_stack_primitives_patch_sha256')
                or sha(stack_binding)!=provenance.get('native_stack_primitives_source_binding_sha256')
                or len(names)!=2 or set(names)!=set(binding['files'])
                or sha(stack_patch) not in helper or 'validate_stack_primitives_patch' not in helper
                or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper
                or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper
                or 'source_cfg_scheduler_instruction' not in helper):
            errors.append('Native stack primitive patch/source binding differs from current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native stack primitive binding unreadable: '+str(error))
    return_patch=ROOT/'patches/runtime-native-return-steps.patch'
    return_binding=ROOT/'patches/runtime-native-return-steps.json'
    try:
        binding=json.loads(return_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',return_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-return-steps.patch' not in tracked
                or 'patches/runtime-native-return-steps.json' not in tracked
                or sha(return_patch)!=binding['patch_sha256']
                or sha(return_patch)!=provenance.get('native_return_steps_patch_sha256')
                or sha(return_binding)!=provenance.get('native_return_steps_source_binding_sha256')
                or len(names)!=4 or set(names)!=set(binding['files'])
                or sha(return_patch) not in helper or 'validate_return_steps_patch' not in helper
                or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper
                or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper
                or "region_metadata.get('result_contract')!='full_pc24_transient_original_scheduler'" not in helper):
            errors.append('Native return step patch/source binding differs from current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native return step binding unreadable: '+str(error))
    prefix_instruction_patch=ROOT/'patches/runtime-native-prefix-instructions.patch'
    prefix_instruction_binding=ROOT/'patches/runtime-native-prefix-instructions.json'
    try:
        binding=json.loads(prefix_instruction_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',prefix_instruction_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-prefix-instructions.patch' not in tracked
                or 'patches/runtime-native-prefix-instructions.json' not in tracked
                or sha(prefix_instruction_patch)!=binding['patch_sha256']
                or sha(prefix_instruction_patch)!=provenance.get('native_prefix_instructions_patch_sha256')
                or sha(prefix_instruction_binding)!=provenance.get('native_prefix_instructions_source_binding_sha256')
                or len(names)!=3 or set(names)!=set(binding['files'])
                or sha(prefix_instruction_patch) not in helper or 'validate_prefix_instructions_patch' not in helper
                or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper
                or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper
                or "region_metadata.get('result_contract')!='full_pc24_transient_original_scheduler'" not in helper
                or "region_metadata.get('instruction_source')!='source_faithful_and_typed_architectural_before_activation_plumbing'" not in helper):
            errors.append('Native prefix instruction patch/source binding differs from current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native prefix instruction binding unreadable: '+str(error))
    task_patch=ROOT/'patches/runtime-selected-task-resume.patch'
    task_binding=ROOT/'patches/runtime-selected-task-resume.json'
    try:
        binding=json.loads(task_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',task_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-selected-task-resume.patch' not in tracked or 'patches/runtime-selected-task-resume.json' not in tracked
                or sha(task_patch)!=binding['patch_sha256'] or sha(task_patch)!=provenance.get('selected_task_resume_patch_sha256')
                or sha(task_binding)!=provenance.get('selected_task_resume_source_binding_sha256') or binding.get('scope')!=provenance.get('selected_task_resume_scope')
                or len(names)!=11 or set(names)!=set(binding['files']) or sha(task_patch) not in helper or sha(task_binding) not in helper
                or 'validate_selected_task_recipe' not in helper or 'validate_selected_task_outputs' not in helper):
            errors.append('Selected task patch/source binding differs from current snapshot.')
        recipe='source_task_resume_v1 00FF03 008461 0083E2 008429 00842F 01D878 01840A'
        recipes=[]
        for path in (ROOT/'native/foundation/recomp').glob('*.cfg'):
            for line in path.read_text(encoding='utf-8').splitlines():
                clean=line.split('#',1)[0].strip()
                if clean.startswith('source_task_resume'):recipes.append((path.name,' '.join(clean.split())))
        if recipes!=[('bank00.cfg',recipe)]:errors.append('Exactly one bounded source-selected task recipe required.')
    except Exception as error:errors.append('Selected task source binding unreadable: '+str(error))

    redirect_patch=ROOT/'patches/runtime-source-redirect.patch'
    redirect_binding=ROOT/'patches/runtime-source-redirect.json'
    try:
        binding=json.loads(redirect_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',redirect_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-source-redirect.patch' not in tracked or 'patches/runtime-source-redirect.json' not in tracked
                or sha(redirect_patch)!=binding['patch_sha256'] or sha(redirect_patch)!=provenance.get('source_redirect_patch_sha256')
                or sha(redirect_binding)!=provenance.get('source_redirect_source_binding_sha256') or binding.get('scope')!=provenance.get('source_redirect_scope')
                or len(names)!=8 or set(names)!=set(binding['files']) or sha(redirect_patch) not in helper or sha(redirect_binding) not in helper
                or 'validate_source_redirect_recipe' not in helper or 'validate_source_redirect_outputs' not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes' not in helper or 'Source-first25 generated output allowlist differs.' not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper or 'native-e0-source-original-redirect-v1' not in helper or 'Source redirect typed architectural row/ROM differs.' not in helper):
            errors.append('Source redirect patch/source binding differs from current snapshot.')
        recipe='source_redirect_v1 01D111 00FF20 0084D9 0084FA 01D119 02 01D176'
        recipes=[]
        for path in (ROOT/'native/foundation/recomp').glob('*.cfg'):
            for line in path.read_text(encoding='utf-8').splitlines():
                clean=line.split('#',1)[0].strip()
                if clean.startswith('source_redirect'):recipes.append((path.name,' '.join(clean.split())))
        if recipes!=[('bank01.cfg',recipe)]:errors.append('Exactly one bounded source-source redirect recipe required.')
    except Exception as error:errors.append('Source redirect source binding unreadable: '+str(error))

    stack_control_patch=ROOT/'patches/runtime-native-stack-controls.patch'
    stack_control_binding=ROOT/'patches/runtime-native-stack-controls.json'
    try:
        binding=json.loads(stack_control_binding.read_bytes())
        names=re.findall(r'^diff --git a/(\S+) b/',stack_control_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-stack-controls.patch' not in tracked
                or 'patches/runtime-native-stack-controls.json' not in tracked
                or sha(stack_control_patch)!=binding['patch_sha256']
                or sha(stack_control_patch)!=provenance.get('native_stack_controls_patch_sha256')
                or sha(stack_control_binding)!=provenance.get('native_stack_controls_source_binding_sha256')
                or binding.get('scope')!=provenance.get('native_stack_controls_scope')
                or len(names)!=3 or set(names)!=set(binding['files'])
                or sha(stack_control_patch) not in helper or 'validate_stack_controls_patch' not in helper
                or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper
                or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper
                or "region_metadata.get('result_contract')!='full_pc24_transient_original_scheduler'" not in helper
                or "region_metadata.get('stack_control_contract')!='native-e0-typed-architectural-stack-v1'" not in helper
                or "region_metadata.get('instruction_source')!='source_faithful_and_typed_architectural_before_activation_plumbing'" not in helper):
            errors.append('Native stack control patch/source binding differs from current snapshot.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        errors.append('Native stack control binding unreadable: '+str(error))
    indirect_patch=ROOT/'patches/runtime-indirect-y.patch';indirect_binding=ROOT/'patches/runtime-indirect-y.json'
    try:
        binding=json.loads(indirect_binding.read_bytes());names=re.findall(r'^diff --git a/(\S+) b/',indirect_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-indirect-y.patch' not in tracked or 'patches/runtime-indirect-y.json' not in tracked or sha(indirect_patch)!=binding['patch_sha256'] or sha(indirect_patch)!=provenance.get('indirect_y_patch_sha256') or sha(indirect_binding)!=provenance.get('indirect_y_source_binding_sha256') or binding.get('scope')!=provenance.get('indirect_y_scope') or len(names)!=4 or set(names)!=set(binding['files']) or sha(indirect_patch) not in helper or sha(indirect_binding) not in helper or 'validate_indirect_y_patch' not in helper or 'validate_indirect_y_outputs' not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes' not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper or 'native-e0-source-cached-indirect-y-v1' not in helper or 'cpu_aot_begin_scheduler_region' not in helper):errors.append('IndirectY patch/source binding differs from current snapshot.')
    except Exception as error:errors.append('IndirectY binding unreadable: '+str(error))
    callee_patch=ROOT/'patches/runtime-native-task-callee.patch';callee_binding=ROOT/'patches/runtime-native-task-callee.json'
    try:
        binding=json.loads(callee_binding.read_bytes());names=re.findall(r'^diff --git a/(\S+) b/',callee_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-native-task-callee.patch' not in tracked or 'patches/runtime-native-task-callee.json' not in tracked or sha(callee_patch)!=binding['patch_sha256'] or sha(callee_patch)!=provenance.get('task_callee_patch_sha256') or sha(callee_binding)!=provenance.get('task_callee_source_binding_sha256') or binding.get('scope')!=provenance.get('task_callee_scope') or len(names)!=5 or set(names)!=set(binding['files']) or sha(callee_patch) not in helper or sha(callee_binding) not in helper or 'validate_task_callee_patch' not in helper or 'task_callee_binding' not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes' not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']" not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']" not in helper or "'selected_task_resume_generation':{'metadata_format':RUNTIME_GENERATION_FORMATS['task']" not in helper or 'Task callee original subcall/return source differs.' not in helper):errors.append('Task callee patch/source binding differs from current snapshot.')
    except Exception as exc:errors.append('Task callee patch/source binding failed: '+str(exc))
    stack_direct_patch=ROOT/'patches/runtime-stack-direct.patch';stack_direct_binding=ROOT/'patches/runtime-stack-direct.json'
    try:
        binding=json.loads(stack_direct_binding.read_bytes());names=re.findall(r'^diff --git a/(\S+) b/',stack_direct_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-stack-direct.patch'not in tracked or 'patches/runtime-stack-direct.json'not in tracked or sha(stack_direct_patch)!=binding['patch_sha256']or sha(stack_direct_patch)!=provenance.get('stack_direct_patch_sha256')or sha(stack_direct_binding)!=provenance.get('stack_direct_source_binding_sha256')or binding.get('scope')!=provenance.get('stack_direct_scope')or len(names)!=3 or set(names)!=set(binding['files'])or sha(stack_direct_patch)not in helper or sha(stack_direct_binding)not in helper or 'validate_stack_direct_patch'not in helper or 'validate_stack_direct_outputs'not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes'not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']"not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']"not in helper or 'native-e0-source-cached-stack-direct-v1'not in helper):errors.append('Stack direct patch/source binding differs from current snapshot.')
    except Exception as exc:errors.append('Stack direct patch/source binding failed: '+str(exc))
    host_proof_idle_patch=ROOT/'patches/runtime-host-proof-idle.patch';host_proof_idle_binding=ROOT/'patches/runtime-host-proof-idle.json'
    try:
        binding=json.loads(host_proof_idle_binding.read_bytes());names=re.findall(r'^diff --git a/(\S+) b/',host_proof_idle_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-host-proof-idle.patch'not in tracked or 'patches/runtime-host-proof-idle.json'not in tracked or sha(host_proof_idle_patch)!=binding['patch_sha256']or sha(host_proof_idle_patch)!=provenance.get('host_proof_idle_patch_sha256')or sha(host_proof_idle_binding)!=provenance.get('host_proof_idle_source_binding_sha256')or binding.get('scope')!=provenance.get('host_proof_idle_scope')or len(names)!=2 or set(names)!=set(binding['files'])or sha(host_proof_idle_patch)not in helper or sha(host_proof_idle_binding)not in helper or 'validate_host_proof_idle_patch'not in helper or 'host_proof_idle_binding'not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes'not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']"not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']"not in helper):errors.append('Host proof idle patch/source binding differs from current snapshot.')
    except Exception as exc:errors.append('Host proof idle patch/source binding failed: '+str(exc))
    redirect_observer_idle_patch=ROOT/'patches/runtime-redirect-observer-idle.patch';redirect_observer_idle_binding=ROOT/'patches/runtime-redirect-observer-idle.json'
    try:
        binding=json.loads(redirect_observer_idle_binding.read_bytes());names=re.findall(r'^diff --git a/(\S+) b/',redirect_observer_idle_patch.read_text(encoding='utf-8'),re.M)
        if ('patches/runtime-redirect-observer-idle.patch'not in tracked or 'patches/runtime-redirect-observer-idle.json'not in tracked or sha(redirect_observer_idle_patch)!=binding['patch_sha256']or sha(redirect_observer_idle_patch)!=provenance.get('redirect_observer_idle_patch_sha256')or sha(redirect_observer_idle_binding)!=provenance.get('redirect_observer_idle_source_binding_sha256')or binding.get('scope')!=provenance.get('redirect_observer_idle_scope')or len(names)!=2 or set(names)!=set(binding['files'])or sha(redirect_observer_idle_patch)not in helper or sha(redirect_observer_idle_binding)not in helper or 'validate_redirect_observer_idle_patch'not in helper or 'redirect_observer_idle_binding'not in helper or 'sha256-newline-terminated-ordered-{len(hashes)}-full-patch-hashes'not in helper or "generated_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['cache']"not in helper or "region_metadata.get('format_version')!=RUNTIME_GENERATION_FORMATS['normal']"not in helper):errors.append('Redirect observer idle patch/source binding differs from current snapshot.')
    except Exception as exc:errors.append('Redirect observer idle patch/source binding failed: '+str(exc))
    reviewed = ROOT / 'native/foundation/recomp/reviewed-roots.json'
    if ('native/foundation/recomp/reviewed-roots.json' not in tracked
            or sha(reviewed) != provenance.get('reviewed_analysis_roots_sha256')):
        errors.append('Reviewed root configuration differs from the audited snapshot.')
    if provenance['runtime_commit'] not in pins or provenance['runtime_commit'] not in helper:
        errors.append('Runtime pin mismatch.')
    if 'PolyForm Noncommercial' not in (ROOT / 'LICENSE').read_text(encoding='utf-8'):
        errors.append('Missing native license.')
    if 'MIT License' not in (ROOT / 'Companion/LICENSE').read_text(encoding='utf-8'):
        errors.append('Missing Companion license.')
    for name in ('README.md', 'BUILDING.md', 'CREDITS.md', 'THIRD_PARTY_NOTICES.md',
                 'ROADMAP.md', 'CONTRIBUTING.md', 'docs/VALIDATION.md'):
        for link in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):
                continue
            destination = (ROOT / name).parent / link.split('#', 1)[0]
            if not destination.exists():
                errors.append('Missing documentation link: ' + name + ' -> ' + link)
    if capture_count != len(DOCUMENTATION_CAPTURES):
        errors.append('Missing reviewed documentation captures')
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(json.dumps({'passed': True, 'tracked_files': len(tracked),
                      'documentation_screenshots': capture_count,
                      'python_syntax_checks': python_count, 'authored_inputs': counts,
                      'experiment_manifests': len(experiments),
                      'verbatim_notices': len(provenance['verbatim_notices']),
                      'limits': 'Source publication checks only; no gameplay qualification.'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
