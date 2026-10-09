"""Run a finite input fixture in a fresh, isolated local installation."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('script', type=Path)
    parser.add_argument('--frames', type=int, default=1200)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--coverage', action='store_true')
    parser.add_argument('--copy-saves', type=Path)
    parser.add_argument('--save-at', type=int, help='Save slot 0 through the runtime overlay at this frame')
    parser.add_argument('--entry-trace', help='Log compiled function entries in a frame window, e.g. 50-52')
    parser.add_argument('--wram-watch', help='Read-only store trace range, e.g. 624c:624d (hex)')
    parser.add_argument('--damage-proof', choices=['trace', '2'], help='Bounded native Red Slime damage proof, disposable profile only')
    parser.add_argument('--fast-menus', choices=['0', '1'], help='Explicit native field-menu batching policy')
    parser.add_argument('--exe', type=Path, help='Explicit local diagnostic executable')
    parser.add_argument('--rom', type=Path, help='Explicit input for a separately regenerated variant')
    parser.add_argument('--resume-copy', type=Path, help='Copy a checkpoint before using the one-shot resume option')
    args = parser.parse_args()
    if not args.name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.name):
        parser.error('Use a simple lowercase fixture name')
    run = ROOT / 'local/runs' / args.name
    run.mkdir(parents=True, exist_ok=False)
    exe = run / 'SecretOfTheStarsSNESRecomp.exe'
    shutil.copy2(args.exe.resolve(strict=True) if args.exe else PROOF / 'build' / exe.name, exe)
    script = args.script.resolve(strict=True)
    shutil.copy2(script, run / 'input.txt')
    if args.copy_saves:
        shutil.copytree(args.copy_saves.resolve(strict=True), run / 'saves')
    (run / 'config.ini').write_text(
        '[Graphics]\nRenderer=software\nVSync=0\nFullscreen=0\nWidescreen=0\n'
        '[Sound]\nEnableAudio=0\n'
        '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
        '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n', encoding='utf-8')
    dump = run / 'dump'
    dump.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
               SNESRECOMP_RUN_FRAMES=str(args.frames), SNESRECOMP_DUMP_DIR=str(dump),
               SNESRECOMP_STATE_TRACE=str(run / 'state.csv'),
               SNESRECOMP_TIER2_CAPTURE='1' if args.coverage else '0',
               SNESRECOMP_TIER2_MANIFEST=str(run / 'coverage.json'))
    env['SNESRECOMP_FOUNDATION_TRACE'] = str(run / 'foundation.csv')
    if args.damage_proof:
        env['SNESRECOMP_FOUNDATION_DAMAGE_PROOF'] = args.damage_proof
    if args.fast_menus:
        env['SNESRECOMP_FOUNDATION_FAST_MENUS'] = args.fast_menus
    if args.save_at is not None:
        env.update(SNESRECOMP_OVERLAY_SELFTEST=str(args.save_at),
                   SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
    if args.entry_trace:
        env['SNESRECOMP_DBTRACE'] = args.entry_trace
    if args.wram_watch:
        bounds = args.wram_watch.split(':')
        if len(bounds) != 2 or not 0 <= int(bounds[0], 16) <= int(bounds[1], 16) < 0x10000:
            parser.error('Use a valid WRAM byte range')
        env['SNESRECOMP_WLOG_ADDR'] = args.wram_watch + ':' + str(run / 'writes.tsv')
        env['SNESRECOMP_WLOG_STATE'] = '1'
    rom = args.rom.resolve(strict=True) if args.rom else ROOT / 'local/inputs/clean-usa.sfc'
    command = [str(exe), '--no-launcher', '--rom', str(rom),
               '--script', str(run / 'input.txt')]
    if args.resume_copy:
        shutil.copy2(args.resume_copy.resolve(strict=True), run / 'resume.state')
        command += ['--resume-state', str(run / 'resume.state')]
    start = time.monotonic()
    with (run / 'host.log').open('w', encoding='utf-8') as log:
        try:
            result = subprocess.run(command, cwd=run, env=env, stdout=log, stderr=log,
                                    timeout=args.timeout,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    log_text = (run / 'host.log').read_text(encoding='utf-8', errors='replace')
    resumed = 'resume state loaded:' in log_text if args.resume_copy else None
    if args.resume_copy and not resumed:
        code = 'resume-failed' if code == 0 else code
    report = {'fixture': args.name, 'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
              'rom_sha256': hashlib.sha256(rom.read_bytes()).hexdigest(),
              'input_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
              'returncode': code, 'elapsed_seconds': round(time.monotonic() - start, 3),
              'headless': True, 'audio_enabled': False, 'frame_limit': args.frames,
              'gamepad_enabled': False, 'save_at': args.save_at, 'resumed': resumed}
    report['damage_proof'] = args.damage_proof
    (run / 'run.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    print(log_text[-4500:])
    return 0 if code == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
