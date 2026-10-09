"""Read-only envelope inspector for this foundation's local checkpoints."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zlib

IDENTITY = b'sots-clean-foundation-v1'.ljust(32, b'\0')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('checkpoint', type=Path)
    args = p.parse_args()
    data = args.checkpoint.read_bytes()
    if len(data) < 60 or data[:8] != b'RSGUARD\x01':
        p.error('Missing guarded foundation checkpoint envelope')
    length = struct.unpack_from('<Q', data, 8)[0]
    stored = struct.unpack_from('<I', data, len(data)-4)[0]
    computed = zlib.crc32(data[:-4])
    valid = length == len(data)-52 and data[16:48] == IDENTITY and stored == computed
    print(json.dumps({'path': str(args.checkpoint.resolve()), 'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(), 'identity': data[16:48].rstrip(b'\0').decode('ascii', errors='replace'),
        'declared_payload_bytes': length, 'crc32_stored': f'{stored:08x}',
        'crc32_computed': f'{computed:08x}', 'envelope_valid': valid,
        'limit': 'Envelope validation only. The game also validates its runtime and execution chunk before restoring.'}, indent=2))
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
