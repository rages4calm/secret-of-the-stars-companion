"""Read a captured Mode 1 BG3 UI into tile/cell identities and a local preview.

Read-only evidence for future font/window replacement bindings. Does not infer
ROM resource names, compressed storage, text encoding or HD art coverage.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import struct
from PIL import Image
from foundation_assets import decode_tile


def inspect(prefix, out):
    regs = json.loads(prefix.with_suffix('.regs.json').read_text())
    vram = prefix.with_suffix('.vram.bin').read_bytes()
    cgram = prefix.with_suffix('.cgram.bin').read_bytes()
    if len(vram) != 65536 or len(cgram) != 512 or regs['bgmode'] & 7 != 1 or regs['bgmode'] & 0x40:
        raise ValueError('Expected a Mode 1 capture with complete VRAM/CGRAM')
    sc = regs['bgsc'][2]
    width, height = (64 if sc & 1 else 32), (64 if sc & 2 else 32)
    map_base = (sc & 0xfc) << 9  # BGxSC is a VRAM word address; file offsets are bytes.
    char_base = ((regs['bg_tile_adr'] >> 8) & 15) << 13
    cells, resources = [], {}
    palettes = collections.Counter()
    canvas = Image.new('RGBA', (width * 8, height * 8))
    for y in range(height):
        for x in range(width):
            screen = x // 32 + (y // 32) * (width // 32)
            offset = (map_base + screen * 2048 + ((y % 32) * 32 + x % 32) * 2) & 0xffff
            word = struct.unpack_from('<H', vram, offset)[0]
            tile_id, palette = word & 1023, (word >> 10) & 7
            tile_offset = (char_base + tile_id * 16) & 0xffff
            raw = bytes(vram[(tile_offset + i) & 0xffff] for i in range(16))
            identity = hashlib.sha256(raw).hexdigest()
            resources[tile_id] = {'tile_id': tile_id, 'vram_byte_offset': tile_offset,
                                  'content_sha256': identity}
            palettes[palette] += 1
            cells.append({'x': x, 'y': y, 'word': word, 'tile_id': tile_id, 'palette': palette,
                'priority': bool(word & 0x2000), 'flip_x': bool(word & 0x4000),
                'flip_y': bool(word & 0x8000), 'map_byte_offset': offset})
            colors = [(0, 0, 0, 0)]
            for index in range(1, 4):
                color = struct.unpack_from('<H', cgram, (palette * 4 + index) * 2)[0]
                channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
                colors.append(tuple(((v << 3) | (v >> 2)) * (regs['inidisp'] & 15) // 15
                                    for v in channels) + (255,))
            pixels = decode_tile(raw, 2)
            tile = Image.new('RGBA', (8, 8))
            tile.putdata([colors[v] for v in pixels])
            if word & 0x4000:
                tile = tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if word & 0x8000:
                tile = tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            canvas.paste(tile, (x * 8, y * 8))
    out.mkdir(parents=True, exist_ok=False)
    canvas.save(out / 'bg3-layer.png')
    record = {'capture': str(prefix.resolve()), 'frame': regs['frame'],
        'vram_sha256': hashlib.sha256(vram).hexdigest(), 'cgram_sha256': hashlib.sha256(cgram).hexdigest(),
        'bg_mode': 1, 'layer': 'BG3', 'tile_bpp': 2, 'map_base_byte_offset': map_base,
        'character_base_byte_offset': char_base, 'map_size_tiles': [width, height],
        'palette_cell_counts': dict(palettes), 'resources': list(resources.values()), 'cells': cells,
        'limits': ['Captured tile IDs and bytes only; no persistent ROM resource identities inferred',
                   'Layer preview ignores scroll, sprites, priority composition and color math',
                   'No runtime replacement or ROM write performed']}
    (out / 'ui-map.json').write_text(json.dumps(record, indent=2) + '\n')
    print(out / 'ui-map.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_prefix', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    inspect(args.capture_prefix, args.output)


if __name__ == '__main__':
    main()
