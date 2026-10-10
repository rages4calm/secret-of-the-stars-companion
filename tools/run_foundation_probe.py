"""Run a finite developer replay beside a copied EXE in a fresh private profile.

cwd alone cannot isolate the native runtime: it anchors saves/config beside its
EXE. This helper verifies that anchor and retains hashes/logs without modifying
the supplied executable, ROM, script or checkpoint. Execution is not qualification.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess

ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_script(script):
    frames = 0
    for line in script.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'(wait|press (?:a|b|x|y|l|r|start|select|up|down|left|right)) ([1-9][0-9]*)', line)
        if match:
            frames += int(match[2])
        elif line != 'quit' and not re.fullmatch(r'dump [A-Za-z][A-Za-z0-9_-]{0,63}', line):
            raise ValueError('Unsupported command or unsafe dump name: ' + line)
    if not 1 <= frames <= 100000:
        raise ValueError('Replay must request 1 to 100000 guest frames')


def run(args):
    sources = {'executable': args.exe.resolve(strict=True), 'rom': args.rom.resolve(strict=True),
               'script': args.script.resolve(strict=True)}
    if args.state:
        sources['checkpoint'] = args.state.resolve(strict=True)
    hashes = {name: sha(path) for name, path in sources.items()}
    if sources['rom'].stat().st_size != 1572864 or hashes['rom'] != ROM_SHA:
        raise ValueError('Expected the supported clean unheadered USA ROM')
    if args.expected_exe_sha256 and hashes['executable'] != args.expected_exe_sha256:
        raise ValueError('Executable differs from the requested frozen artifact')
    script = sources['script'].read_text(encoding='utf-8-sig')
    validate_script(script)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.name):
        raise ValueError('Name must be a single simple directory component')
    evidence = args.evidence_root.resolve(strict=True)
    folder = (evidence / args.name).resolve()
    if folder.parent != evidence or folder.exists():
        raise ValueError('Choose a fresh direct child of the explicit evidence root')
    watch = args.watch
    if watch and not re.fullmatch(r'[0-9A-Fa-f]{1,6}:[0-9A-Fa-f]{1,6}', watch):
        raise ValueError('Watch expects hexadecimal start:end addresses')
    if watch and not 0 <= int(watch.split(':')[0], 16) <= int(watch.split(':')[1], 16) <= 0xffffff:
        raise ValueError('Watch range is invalid')
    folder.mkdir()
    (folder / 'dump').mkdir()
    shutil.copy2(sources['executable'], folder / 'game.exe')
    shutil.copy2(sources['script'], folder / 'input.txt')
    if args.state:
        shutil.copy2(sources['checkpoint'], folder / 'resume.state')
    (folder / 'config.ini').write_bytes(b'[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\nFullscreen=0\n'
        b'[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
        b'[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n[Controller]\nSourceP1=1\nSourceP2=0\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
        SNESRECOMP_DUMP_DIR=str(folder / 'dump'), SNESRECOMP_STATE_TRACE=str(folder / 'state.csv'),
        SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_JOURNAL='0',
        SNESRECOMP_FOUNDATION_BATTLE_INFO='0', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(int(args.enhanced)),
        SNESRECOMP_FOUNDATION_WIDE=str(int(args.wide)), SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(int(args.wide)),
        SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0', SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0')
    if watch:
        env.update(SNESRECOMP_WLOG_ADDR=watch + ':' + str(folder / 'writes.tsv'),
                   SNESRECOMP_WLOG_STATE='1', SNESRECOMP_WLOG_ADDR_CAP='20000')
    if args.cpu_trace:
        env['SNESRECOMP_FOUNDATION_CPU_TRACE'] = str(folder / 'cpu.csv')
    if args.actor_trace:
        env['SNESRECOMP_FOUNDATION_ACTORS_TRACE'] = str(folder / 'actors.csv')
    command = [str(folder / 'game.exe'), '--no-launcher', '--rom', str(sources['rom']),
               '--script', str(folder / 'input.txt')]
    if args.state:
        command += ['--resume-state', str(folder / 'resume.state')]
    timeout = False
    with (folder / 'host.log').open('wb') as log:
        try:
            result = subprocess.run(command, cwd=folder, env=env, stdout=log, stderr=log,
                timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            code = result.returncode
        except subprocess.TimeoutExpired:
            code, timeout = None, True
    output = (folder / 'host.log').read_text(encoding='utf-8', errors='replace')
    anchor = re.search(r"Config/saves anchored to '([^\r\n']+)'", output)
    anchored_here = bool(anchor and Path(anchor[1]).resolve() == folder)
    checks = {'exit_zero': code == 0, 'finite_run_completed': not timeout,
        'copied_executable_exact': sha(folder / 'game.exe') == hashes['executable'],
        'private_profile_anchor': anchored_here,
        'requested_checkpoint_loaded': not args.state or 'resume state loaded:' in output,
        'source_inputs_unchanged': all(sha(path) == hashes[name] for name, path in sources.items())}
    report = {'passed': all(checks.values()), 'status': 'developer_replay_only', 'checks': checks,
        'exit_code': code, 'profile': str(folder), 'sources': {k: str(v) for k, v in sources.items()},
        'source_sha256': hashes, 'headless': True, 'silent': True,
        'limits': 'Isolated replay/anchor verification only; no gameplay, campaign or audio qualification.'}
    (folder / 'probe-report.json').write_bytes((json.dumps(report, indent=2) + '\n').encode('utf-8'))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('exe', 'rom', 'script', 'evidence-root'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--state', type=Path)
    p.add_argument('--expected-exe-sha256')
    p.add_argument('--watch', help='Original bus writes in hexadecimal start:end range')
    for key in ('wide', 'enhanced', 'cpu-trace', 'actor-trace'):
        p.add_argument('--' + key, action='store_true')
    args = p.parse_args()
    try:
        report = run(args)
    except (OSError, ValueError) as error:
        p.error(str(error))
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
