"""Create a disposable, explicitly staged foundation checkpoint for developer tests.

Only the supported clean-USA RTLS v10 layout is accepted. No input is rewritten.
Edits use hexadecimal WRAM offsets and expected/replacement bytes: 5372=00:11.
This is a test-state tool, not a gameplay qualification or campaign progression.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zlib

IDENTITY = b'sots-clean-foundation-v1'.ljust(32, b'\0')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def wram_offset(data):
    if (len(data) < 60 or data[:8] != b'RSGUARD\x01'
            or data[16:48] != IDENTITY
            or struct.unpack_from('<Q', data, 8)[0] != len(data)-52
            or struct.unpack_from('<I', data, len(data)-4)[0] != zlib.crc32(data[:-4])):
        raise ValueError('Invalid foundation envelope, identity, length or CRC')
    if struct.unpack_from('<II', data, 48) != (0x52544c53, 10):
        raise ValueError('Only RTLS v10 checkpoints are supported')
    headers = [i for i in range(56, len(data)-8)
               if data[i:i+8] == b'PPU0'+struct.pack('<I', 66656)]
    if len(headers) != 1:
        raise ValueError('Expected exactly one supported PPU serialization header')
    # snes_saveload: PPU block, clean-USA 8-KiB SRAM, pinned 96-byte SNES tail,
    # 128-KiB WRAM, 70-byte v10 joypad/port tail, then the foundation extension.
    offset = headers[0]+8+66656+8192+96
    extension = offset+0x20000+70
    if extension+12 >= len(data)-4:
        raise ValueError('Truncated WRAM or foundation execution extension')
    magic, version, execution_size = struct.unpack_from('<III', data, extension)
    if magic != 0x53544f53 or version not in (2, 3):
        raise ValueError('Unsupported foundation execution extension')
    extra = 40+(8 if version == 3 else 0)
    if extension+12+execution_size+extra != len(data)-4:
        raise ValueError('Foundation execution extension length does not match layout')
    if data[extension+12:extension+16] != b'RBRS':
        raise ValueError('Missing pinned execution-state residue header')
    return offset


def stage(source, output_dir, specifications, reason, evidence_root):
    source = source.resolve(strict=True)
    output_dir = output_dir.resolve()
    evidence_root = evidence_root.resolve(strict=True)
    if not output_dir.is_relative_to(evidence_root) or output_dir == evidence_root:
        raise ValueError('Output must be a fresh subdirectory of the explicit evidence root')
    if output_dir.exists():
        raise ValueError('Output already exists; retain earlier evidence and choose a fresh directory')
    original = source.read_bytes()
    offset = wram_offset(original)
    staged = bytearray(original)
    edits = []
    seen = set()
    for specification in specifications:
        address, values = specification.split('=', 1)
        before, after = values.split(':', 1)
        address = int(address, 16)
        before, after = bytes.fromhex(before), bytes.fromhex(after)
        if not before or len(before) != len(after) or address < 0 or address+len(before) > 0x20000:
            raise ValueError('Edits must have equal nonempty byte lengths within WRAM')
        locations = set(range(address, address+len(before)))
        if locations & seen:
            raise ValueError('Overlapping edits are refused')
        seen |= locations
        actual = original[offset+address:offset+address+len(before)]
        if actual != before:
            raise ValueError(f'Expected bytes mismatch at WRAM {address:05x}: {actual.hex()} != {before.hex()}')
        staged[offset+address:offset+address+len(after)] = after
        edits.append({'wram_offset': f'{address:05x}', 'expected': before.hex(), 'replacement': after.hex()})
    if not edits or not reason.strip():
        raise ValueError('Explicit edits and a staging reason are required')
    struct.pack_into('<I', staged, len(staged)-4, zlib.crc32(staged[:-4]))
    if wram_offset(staged) != offset:
        raise ValueError('Staged checkpoint failed structural validation')
    changed = {i for i, (a, b) in enumerate(zip(original, staged)) if a != b}
    if not changed <= {offset+i for i in seen} | set(range(len(staged)-4, len(staged))):
        raise ValueError('Unexpected changes outside explicit WRAM bytes and envelope CRC')
    if source.read_bytes() != original:
        raise ValueError('Source changed during staging')
    output_dir.mkdir(parents=True, exist_ok=False)
    target = output_dir/'staged.state'
    with target.open('xb') as stream:
        stream.write(staged)
    receipt = {'provenance': 'staged-developer-state', 'campaign_progression': False,
        'reason': reason, 'source': str(source), 'source_sha256': digest(original),
        'checkpoint': str(target), 'checkpoint_sha256': digest(staged),
        'wram_file_offset': offset, 'edits': edits, 'source_unchanged': source.read_bytes() == original,
        'limit': 'Structure and explicit byte edits only. Actual loaders, graphics, state coherence and gameplay require separate execution checks.'}
    (output_dir/'staging-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--edit', action='append', required=True)
    parser.add_argument('--reason', required=True)
    args = parser.parse_args()
    try:
        receipt = stage(args.checkpoint, args.output_dir, args.edit, args.reason, args.evidence_root)
    except (ValueError, OSError, struct.error) as error:
        parser.error(str(error))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
