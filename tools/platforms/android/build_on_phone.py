"""Generate and build a private native module within the app's setup directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from types import SimpleNamespace


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_path(root, name):
    relative = PurePosixPath(name)
    if not relative.parts or relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise ValueError('Invalid setup input path')
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
        raise ValueError('Setup input escaped its private directory')
    return path


def verified_inputs(capsule, native_dir):
    bundle = json.loads((capsule / 'bundle.json').read_bytes())
    if bundle['format'] != 'sots-android-first-run-v1':
        raise ValueError('Unknown setup capsule format')
    for directory, entries in ((capsule, bundle['files']), (native_dir, bundle['native_tools'])):
        for name, expected in entries.items():
            if sha256(checked_path(directory, name)) != expected:
                raise ValueError('Setup input hash mismatch: ' + name)
    return bundle


def generate(capsule, work, rom, analyzer, bundle):
    sys.path.insert(0, str(capsule / 'repository/tools'))
    import build_public_foundation as helper
    import validate_generated_native as validator

    source = capsule / 'repository/native/foundation'
    runtime = capsule / 'runtime'
    project = work / 'project'
    expected = bundle['rom_sha256']
    if expected != sha256(rom) or rom.stat().st_size != 1_572_864:
        raise ValueError('Use the exact unheadered USA ROM')
    if helper.RUNTIME_PIN != bundle['runtime_pin']:
        raise ValueError('Pinned runtime revision differs')
    print('SOTS_SETUP:runtime', flush=True)
    helper.validate_final_runtime(runtime)
    from optimize_emitter import apply as optimize_emitter
    if '_sots_digest_snapshot' not in sys.builtin_module_names:
        raise RuntimeError('The packaged Android setup launcher is missing its proof cache')
    patched_sources = optimize_emitter(runtime, bundle['patched_sources'])
    _, authored = helper.snapshot_authored(source, project)
    identity = dict(line.split('=', 1) for line in (source / 'rom_identity.txt').read_text().splitlines()
                    if '=' in line and not line.lstrip().startswith('#'))
    identity = {key.strip(): value.strip() for key, value in identity.items()}
    if identity['expected_sha256'].lower() != expected:
        raise ValueError('ROM source identity differs')
    print('SOTS_SETUP:preflight', flush=True)
    helper.reviewed_roots_preflight(runtime, project, identity, True)
    helper.validate_selected_task_recipe(source / 'recomp')
    helper.validate_source_redirect_recipe(source / 'recomp')
    env = {key: value for key, value in os.environ.items() if not key.startswith('SNESRECOMP_')}
    env.update(SNESRECOMP_NATIVE_ANALYZER=str(analyzer), PYTHONDONTWRITEBYTECODE='1')
    print('SOTS_SETUP:generate', flush=True)
    commands = helper.generation_commands(runtime, project, rom, identity)
    with (work / 'generate.log').open('x+b') as log:
        for index, command in enumerate(commands):
            if index == 1:
                print('SOTS_SETUP:headers', flush=True)
            try:
                subprocess.run(list(map(str, command)), cwd=project, env=env,
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=5400)
            except subprocess.CalledProcessError as error:
                end = log.seek(0, os.SEEK_END)
                log.seek(max(0, end - 8192))
                detail = log.read().decode('utf-8', errors='replace').strip()
                raise RuntimeError(detail or f'Generator exited with code {error.returncode}.') from error
            except subprocess.TimeoutExpired as error:
                raise RuntimeError('This setup step timed out after 90 minutes.') from error
    print('SOTS_SETUP:validate', flush=True)
    generated = project / 'src/gen'
    cache = json.loads((generated / '.snesrecomp-cache.json').read_bytes())
    regions = json.loads((generated / 'native_regions.json').read_bytes())
    if cache['format_version'] != helper.RUNTIME_GENERATION_FORMATS['cache'] or regions['rom_sha256'] != expected:
        raise ValueError('Generated cache does not match the expected source format or ROM')
    if cache.get('module') != {'id': 'main', 'prefix': ''} or set(cache['outputs']) != set(bundle['expected_outputs']):
        raise ValueError('Generated module file list differs')
    for name, digest in cache['outputs'].items():
        if sha256(checked_path(generated, name)) != digest:
            raise ValueError('Generated source hash mismatch: ' + name)
    results = validator.validate_current_outputs(generated, cache, rom, runtime, project / 'recomp',
                                                  source_hashes=patched_sources)
    helper.validate_source_redirect_outputs(generated, cache, expected, rom)
    helper.generate_profile_seed_auxiliary_outputs(project, work, rom, expected, authored)
    print('SOTS_SETUP:cpu', flush=True)
    architecture = helper.prepare_architectural_native(SimpleNamespace(
        project=project, out=work, runtime=runtime, rom=rom, architectural_native_preparation=None))
    (work / 'generator-result.json').write_text(json.dumps({'normal_rows': results['normal_rows'],
        'architectural_sha256': architecture['output_sha256']}) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-lib-dir', type=Path, required=True)
    args = parser.parse_args()
    capsule = args.capsule.resolve(strict=True)
    native_dir = args.native_lib_dir.resolve(strict=True)
    rom = args.rom.resolve(strict=True)
    # Android's private directory can have an OS-owned user-storage alias.
    # Resolve the trusted staging parent like the other roots, preserving the output leaf check.
    output = args.output.parent.resolve(strict=True) / args.output.name
    if output.name != 'libmain.so' or output.is_symlink() or output.exists():
        raise ValueError('Use a fresh libmain.so staging path')
    print('SOTS_SETUP:verify', flush=True)
    bundle = verified_inputs(capsule, native_dir)
    work = output.parent / 'native-build'
    work.mkdir(exist_ok=False)
    os.environ['TMPDIR'] = str(work)
    sys.path.insert(0, str(capsule))
    generate(capsule, work, rom, native_dir / 'libanalyzer.so', bundle)
    print('SOTS_SETUP:compile', flush=True)
    from phone_compile import compile_module
    compile_dir = work / 'compile'
    compile_dir.mkdir()
    compile_module(capsule / 'recipe.json', capsule, work, native_dir, compile_dir, output,
                   unit_progress=lambda done, total: print(f'SOTS_UNITS:{done}/{total}', flush=True))
    if not output.is_file() or output.stat().st_size < 64:
        raise RuntimeError('Native linker did not create a shared library')
    print('Native build complete.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        detail = str(error).strip().splitlines()
        print(f'SOTS_ERROR:{detail[-1] if detail else type(error).__name__}', file=sys.stderr, flush=True)
        raise SystemExit(1)
