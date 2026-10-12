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
                or 'ordered-thirteen-full-patch-hashes' not in helper):
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
