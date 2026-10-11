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
