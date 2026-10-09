"""Reject damaged/foreign v3 checkpoints before any guest state is applied."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'


def seal(data):
    struct.pack_into('<Q', data, 8, len(data) - 52)
    struct.pack_into('<I', data, len(data) - 4, zlib.crc32(data[:-4]))
    return bytes(data)


def main():
    global EXE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    EXE = parser.parse_args().exe.resolve()
    candidates = sorted((ROOT / 'local/runs').glob('audio-*/legacy/saves/save0.sav'))
    original = candidates[-1].read_bytes()
    header = struct.pack('<II', 0x53544F53, 3)
    offset = original.find(header)
    assert offset >= 48 and original.find(header, offset + 1) == -1
    bad_crc = bytearray(original)
    bad_crc[offset + 20] ^= 1
    foreign = bytearray(original)
    foreign[16:48] = b'foreign-title-schema'.ljust(32, b'\0')
    schema = bytearray(original)
    struct.pack_into('<I', schema, offset + 4, 99)
    oversized = bytearray(original[:-4] + b'\0' + original[-4:])
    bad_port = bytearray(original)
    struct.pack_into('<I', bad_port, len(bad_port)-16, 0x00020001)
    cases = {'crc': bytes(bad_crc), 'truncated': original[:-1],
             'foreign-identity': seal(foreign), 'unknown-schema': seal(schema),
             'wrong-layout': seal(oversized), 'invalid-vram-port': seal(bad_port)}
    base = ROOT / 'local/runs' / ('checkpoints-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_RUN_FRAMES='10')
    report = {'executable_sha256': hashlib.sha256(EXE.read_bytes()).hexdigest(),
              'source_checkpoint': str(candidates[-1].relative_to(ROOT)), 'cases': {}}
    reference = None
    for name, data in [('clean-boot', None), *cases.items()]:
        run = base / name
        run.mkdir()
        shutil.copy2(EXE, run / 'game.exe')
        (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (run / 'input.txt').write_text('wait 1\ndump rejected\nquit\n')
        (run / 'dump').mkdir()
        command = [str(run / 'game.exe'), '--no-launcher', '--rom',
                   str(ROOT / 'local/inputs/clean-usa.sfc'), '--script', str(run / 'input.txt')]
        if data is not None:
            (run / 'resume.state').write_bytes(data)
            command += ['--resume-state', str(run / 'resume.state')]
        with (run / 'host.log').open('w') as log:
            result = subprocess.run(command, cwd=run,
                env=dict(env, SNESRECOMP_DUMP_DIR=str(run / 'dump')),
                stdout=log, stderr=log, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0
        dumps = {p.name: p.read_bytes() for p in (run / 'dump').glob('rejected.*')
                 if p.suffix in ('.bin', '.bgrx')}
        assert len(dumps) == 6
        if data is None:
            reference = dumps
            continue
        host = (run / 'host.log').read_text(errors='replace')
        checks = {'rejected': 'resume state FAILED to load (kept):' in host,
                  'source_copy_retained': (run / 'resume.state').read_bytes() == data,
                  'guest_matches_clean_boot': dumps == reference}
        checks['passed'] = all(checks.values())
        report['cases'][name] = checks
    report['passed'] = all(c['passed'] for c in report['cases'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
