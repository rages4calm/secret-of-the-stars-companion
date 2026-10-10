"""ROM-free checks for the exact files Git will publish."""
from pathlib import Path, PurePosixPath
import ast
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

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
    for name in tracked:
        parts = PurePosixPath(name).parts
        path = ROOT / name
        if (parts[0] in {'local', 'research', 'fixtures'}
                or 'gen' in parts or name.endswith('/recomp/funcs.h')
                or any(part in {'bin', 'obj', '__pycache__', 'saves', 'screenshots'} for part in parts)
                or PurePosixPath(name).suffix.lower() in FORBIDDEN_SUFFIXES
                or re.search(r'\.state', name, re.I)
                or PurePosixPath(name).name.startswith('.env')):
            errors.append('Forbidden publication path: ' + name)
        if path.is_symlink():
            errors.append('Symlink requires publication review: ' + name)
            continue
        data = path.read_bytes()
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
        manifest = json.loads((ROOT / base / 'authored-files.json').read_text())
        counts[base] = len(manifest)
        for name, digest in manifest.items():
            full = base + '/' + name
            if full not in tracked or sha(ROOT / full) != digest:
                errors.append('Authored snapshot mismatch: ' + full)
    provenance = json.loads((ROOT / 'SOURCE-PROVENANCE.json').read_text())
    if provenance['native_version'] != (ROOT / 'native/foundation/VERSION').read_text().strip():
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
    pins = (ROOT / 'native/foundation/framework_pins.txt').read_text()
    helper = (ROOT / 'tools/build_public_foundation.py').read_text()
    if provenance['runtime_commit'] not in pins or provenance['runtime_commit'] not in helper:
        errors.append('Runtime pin mismatch.')
    if 'PolyForm Noncommercial' not in (ROOT / 'LICENSE').read_text():
        errors.append('Missing native license.')
    if 'MIT License' not in (ROOT / 'Companion/LICENSE').read_text():
        errors.append('Missing Companion license.')
    for name in ('README.md', 'BUILDING.md', 'CREDITS.md', 'THIRD_PARTY_NOTICES.md',
                 'ROADMAP.md', 'CONTRIBUTING.md', 'docs/VALIDATION.md'):
        for link in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text()):
            if '://' in link or link.startswith('#'):
                continue
            destination = (ROOT / name).parent / link.split('#', 1)[0]
            if not destination.exists():
                errors.append('Missing documentation link: ' + name + ' -> ' + link)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(json.dumps({'passed': True, 'tracked_files': len(tracked),
                      'python_syntax_checks': python_count, 'authored_inputs': counts,
                      'experiment_manifests': len(experiments),
                      'verbatim_notices': len(provenance['verbatim_notices']),
                      'limits': 'Source publication checks only; no gameplay qualification.'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
