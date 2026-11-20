"""Stage the ROM-free inputs for an Android phone setup APK, then create Gradle files."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from shutil import copyfile
import subprocess
import zipfile

from android_project import ANDROID, android_sdl_sources, write_android_project

REPO = Path(__file__).resolve().parents[2]
TOOL_NAMES = {
    'libanalyzer.so', 'libzig.so', 'libpython-launcher.so', 'libpython3.14.so',
    'libcrypto_python.so', 'libssl_python.so', 'libsqlite3.so',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git_names(root, *arguments):
    output = subprocess.check_output(['git', '-C', str(root), *arguments])
    return {item for item in output.decode('utf-8').split('\0') if item}


def checked_copy(source, target, name, digest=None):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise ValueError('Setup input path escapes its root')
    original = source.joinpath(*relative.parts)
    if original.is_symlink() or not original.resolve(strict=True).is_relative_to(source):
        raise ValueError('Setup input points outside source directory: ' + name)
    if digest is not None and sha(original) != digest:
        raise ValueError('Setup source hash mismatch: ' + name)
    result = target.joinpath(*relative.parts)
    result.parent.mkdir(parents=True, exist_ok=True)
    copyfile(original, result)


def stage(args):
    private = args.source_build.resolve(strict=True)
    runtime = args.runtime.resolve(strict=True)
    stamp = json.loads((private / 'source-build-receipt.json').read_bytes())
    if stamp.get('status') != 'compiled_unqualified' or stamp.get('public_build') is not True:
        raise ValueError('Use a verified current private build as the source donor')
    revision = subprocess.check_output(['git', '-C', str(runtime), 'rev-parse', 'HEAD'], text=True).strip()
    provenance = stamp['runtime_source_provenance']
    patches = provenance['patched_sources']
    new_files = set(provenance['new_patched_sources'])
    tracked_delta = git_names(runtime, 'diff', '--name-only', '-z', 'HEAD')
    untracked = git_names(runtime, 'ls-files', '--others', '--exclude-standard', '-z')
    if revision != stamp['runtime_pin'] or tracked_delta != set(patches) - new_files or untracked != new_files:
        raise ValueError('Patched runtime checkout no longer matches its compilation receipt')
    if any(sha(runtime / name) != digest for name, digest in patches.items()):
        raise ValueError('Patched runtime bytes differ')
    capsule = args.capsule.resolve()
    capsule.mkdir(parents=True, exist_ok=False)
    repository = capsule / 'repository'
    source = REPO / 'native/foundation'
    manifest = json.loads((source / 'authored-files.json').read_bytes())
    if manifest != stamp['authored_inputs']:
        raise ValueError('Current authored source differs from the verified build inputs')
    for name, digest in manifest.items():
        checked_copy(source, repository / 'native/foundation', name, digest)
    checked_copy(source, repository / 'native/foundation', 'authored-files.json')
    for name in ('tools/build_public_foundation.py', 'tools/validate_generated_native.py', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        checked_copy(REPO, repository, name)
    for name in git_names(REPO, 'ls-files', '-z', '--', 'patches', 'licenses'):
        checked_copy(REPO, repository, name)
    for name in git_names(runtime, 'ls-files', '-z', '--', 'recompiler', 'recompiler-rs', 'tools') | set(patches):
        if name in patches or (runtime / name).is_file():
            checked_copy(runtime, capsule / 'runtime', name, patches.get(name))
    checked_copy(runtime, capsule / 'runtime', 'LICENSE')
    for name in ('build_on_phone.py',):
        checked_copy(ANDROID, capsule, name)
    python = args.python_prefix.resolve(strict=True)
    # Preserve the stdlib layout expected by PyConfig, including Android extension modules.
    for path in sorted((python / 'lib/python3.14').rglob('*')):
        if path.is_file():
            name = path.relative_to(python).as_posix()
            parts = set(path.relative_to(python / 'lib/python3.14').parts)
            if not parts.intersection({'test', 'tests', 'ensurepip', 'idlelib', 'tkinter', '__pycache__'}):
                checked_copy(python, capsule / 'pyhome', name)
    cache = json.loads((private / 'project/src/gen/.snesrecomp-cache.json').read_bytes())
    meta = {'format':'sots-android-first-run-v1', 'rom_sha256':stamp['rom_sha256'],
            'runtime_pin':revision, 'patched_sources':patches, 'expected_outputs':sorted(cache['outputs'])}
    # Only names and hashes cross the public boundary. The generator must create these on the phone.
    (capsule / 'setup-inputs.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    print(f'Staged source and Python standard library in {capsule}')


def finish(args):
    capsule = args.capsule.resolve(strict=True)
    native = args.native_tools.resolve(strict=True)
    output = args.output.resolve()
    sdl = args.sdl_source.resolve(strict=True)
    android_sdl_sources(sdl)
    if {p.name for p in native.iterdir()} != TOOL_NAMES:
        raise ValueError('Unexpected tool payload file. The game shared library must never be packaged here.')
    record = json.loads((capsule / 'setup-inputs.json').read_bytes())
    recipe = json.loads((capsule / 'recipe.json').read_bytes())
    for name, digest in recipe['capsule_files'].items():
        if sha(capsule / name) != digest:
            raise ValueError('Compiler recipe input differs: ' + name)
    for name in ('phone_compile.py',):
        checked_copy(ANDROID, capsule, name)
    checked_copy(args.zig_license.parent.resolve(), capsule / 'notices', args.zig_license.name)
    ndk_notices = args.ndk_notices.resolve(strict=True)
    for name in ('NOTICE', 'NOTICE.toolchain'):
        checked_copy(ndk_notices, capsule / 'notices/android-ndk', name)
    paths = sorted(p for p in capsule.rglob('*') if p.is_file())
    if (capsule / 'bundle.json').exists():
        raise ValueError('Use a fresh staged capsule')
    if any(p.suffix in {'.sfc', '.srm', '.sav'} or p.name == 'libmain.so' for p in paths):
        raise ValueError('Private game data was found in the setup capsule')
    record['files'] = {p.relative_to(capsule).as_posix():sha(p) for p in paths}
    record['native_tools'] = {name:sha(native / name) for name in sorted(TOOL_NAMES)}
    seal = capsule / 'bundle.json'
    seal.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    archive = output.with_suffix('.setup.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=4) as zip_out:
        for path in [*paths, seal]:
            zip_out.write(path, path.relative_to(capsule).as_posix())
    output.mkdir(parents=True, exist_ok=False)
    cmake = output / 'CMakeLists.txt'
    copyfile(ANDROID / 'SDLOnly.cmake.in', cmake)
    write_android_project(output, sdl, cmake, [
        '-DSNESRECOMP_SDL3_SOURCE_DIR=' + sdl.as_posix(), '-DANDROID_STL=c++_static',
    ], 'SDL3-shared', local_module=True, phone_capsule=archive, native_tools=native,
        capsule_sha256=sha(archive))
    print(f'Android first-run Gradle project: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    staging = commands.add_parser('stage')
    for arg in ('capsule', 'source-build', 'runtime', 'python-prefix'):
        staging.add_argument('--' + arg, type=Path, required=True)
    packaging = commands.add_parser('finish')
    for arg in ('capsule', 'native-tools', 'output', 'sdl-source', 'zig-license', 'ndk-notices'):
        packaging.add_argument('--' + arg, type=Path, required=True)
    args = parser.parse_args()
    (stage if args.action == 'stage' else finish)(args)


if __name__ == '__main__':
    main()
