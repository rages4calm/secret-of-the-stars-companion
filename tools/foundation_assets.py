"""Export editable 2bpp/4bpp tile sheets; verify an exact indexed PNG round trip.

Only reads a local capture. This does not infer ROM compression, map events,
animation identities or HD replacement coverage from a rendered screenshot.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from PIL import Image


def decode_tile(data, bpp=4):
    if bpp not in (2, 4) or len(data) != bpp * 8:
        raise ValueError('Use one complete SNES 2bpp or 4bpp tile')
    return [sum(((data[(plane // 2) * 16 + y * 2 + plane % 2] >> (7 - x)) & 1) << plane
                for plane in range(bpp)) for y in range(8) for x in range(8)]


def encode_tile(pixels, bpp=4):
    if bpp not in (2, 4) or len(pixels) != 64:
        raise ValueError('Use 64 palette indices for a 2bpp or 4bpp tile')
    out = bytearray(bpp * 8)
    for y in range(8):
        for x in range(8):
            value = pixels[y * 8 + x]
            if not 0 <= value < (1 << bpp):
                raise ValueError(f'A {bpp}bpp tile requires indices 0..{(1 << bpp)-1}')
            for plane in range(bpp):
                out[(plane // 2) * 16 + y * 2 + plane % 2] |= ((value >> plane) & 1) << (7 - x)
    return bytes(out)


def export(prefix, out, base, count, palette, bpp=4):
    size, colors_per_bank = bpp * 8, 1 << bpp
    if base % size or base < 0 or base + count * size > 0x10000 or count <= 0:
        raise ValueError('Use an aligned range inside the 64 KiB captured VRAM')
    if not 0 <= palette < 256 // colors_per_bank:
        raise ValueError('Use a palette bank inside the captured CGRAM')
    vram = prefix.with_suffix('.vram.bin').read_bytes()
    cgram = prefix.with_suffix('.cgram.bin').read_bytes()
    if len(vram) != 65536 or len(cgram) != 512:
        raise ValueError('Unexpected capture layout')
    out.mkdir(parents=True, exist_ok=False)
    rows = (count + 15) // 16
    image = Image.new('P', (128, rows * 8))
    colors = []
    for word in struct.unpack_from(f'<{colors_per_bank}H', cgram, palette * colors_per_bank * 2):
        colors.extend(((word & 31) * 255 // 31, ((word >> 5) & 31) * 255 // 31, ((word >> 10) & 31) * 255 // 31))
    image.putpalette(colors + [0] * (768 - len(colors)))
    tiles = []
    reconstructed = bytearray()
    for i in range(count):
        raw = vram[base + i * size:base + (i + 1) * size]
        pixels = decode_tile(raw, bpp)
        tile = Image.new('P', (8, 8))
        tile.putdata(pixels)
        image.paste(tile, ((i % 16) * 8, (i // 16) * 8))
        reconstructed.extend(encode_tile(pixels, bpp))
        tiles.append({'index': i, 'vram_byte_offset': base + i * size,
                      'content_sha256': hashlib.sha256(raw).hexdigest()})
    assert bytes(reconstructed) == vram[base:base + count * size]
    image.save(out / 'tiles-indexed.png')
    loaded = Image.open(out / 'tiles-indexed.png')
    result = bytearray()
    for i in range(count):
        result.extend(encode_tile(list(loaded.crop(((i % 16) * 8, (i // 16) * 8,
             (i % 16) * 8 + 8, (i // 16) * 8 + 8)).get_flattened_data()), bpp))
    original = vram[base:base + count * size]
    assert bytes(result) == original
    (out / f'roundtrip.{bpp}bpp').write_bytes(result)
    receipt = {'capture': str(prefix.resolve()), 'format': f'SNES {bpp}bpp planar',
        'base_byte_offset': base, 'tile_count': count, 'palette_bank': palette,
        'vram_sha256': hashlib.sha256(vram).hexdigest(), 'cgram_sha256': hashlib.sha256(cgram).hexdigest(),
        'roundtrip_sha256': hashlib.sha256(result).hexdigest(), 'roundtrip_identical': bytes(result) == original,
        'tiles': tiles, 'limits': ['Capture tile identity only; ROM storage and animation mappings unproven',
                                  'Lossless editable export is not replacement HD art']}
    (out / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(out / 'manifest.json')


def import_sheet(manifest, sheet, out):
    record = json.loads(manifest.read_text())
    count = record['tile_count']
    if record['format'] not in ('SNES 2bpp planar', 'SNES 4bpp planar'):
        raise ValueError('Unsupported tile manifest')
    bpp = 2 if record['format'] == 'SNES 2bpp planar' else 4
    size = bpp * 8
    if not 0 < count <= 65536 // size or len(record['tiles']) != count:
        raise ValueError('Unsupported tile manifest')
    image = Image.open(sheet)
    if image.mode != 'P' or image.size != (128, ((count + 15) // 16) * 8):
        raise ValueError('Keep the exported indexed PNG dimensions and palette indices')
    data, changes = bytearray(), []
    for i in range(count):
        raw = encode_tile(list(image.crop(((i % 16) * 8, (i // 16) * 8,
            (i % 16) * 8 + 8, (i // 16) * 8 + 8)).get_flattened_data()), bpp)
        data.extend(raw)
        if hashlib.sha256(raw).hexdigest() != record['tiles'][i]['content_sha256']:
            changes.append(i)
    out.mkdir(parents=True, exist_ok=False)
    (out / f'import.{bpp}bpp').write_bytes(data)
    result = {'source_manifest': str(manifest.resolve()), 'source_sheet': str(sheet.resolve()),
        'tile_count': count, 'format': record['format'], 'changed_tiles': changes, 'sha256': hashlib.sha256(data).hexdigest(),
        'palette_policy': 'Indexed tile bytes only; CGRAM palette is a separate asset',
        'limits': ['No ROM write, guest-memory injection or runtime asset binding performed']}
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(out / 'receipt.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_prefix', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--base', type=lambda x: int(x, 0), default=0)
    parser.add_argument('--count', type=int, default=512)
    parser.add_argument('--palette', type=int, default=0)
    parser.add_argument('--bpp', type=int, choices=(2, 4), default=4)
    parser.add_argument('--import-sheet', type=Path, help='Treat capture_prefix as an exported manifest and encode this edited indexed sheet')
    args = parser.parse_args()
    if args.import_sheet:
        import_sheet(args.capture_prefix, args.import_sheet, args.output)
    else:
        export(args.capture_prefix, args.output, args.base, args.count, args.palette, args.bpp)


if __name__ == '__main__':
    main()
