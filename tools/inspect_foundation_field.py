"""Inspect the checked Likado field resource contract using copied guest dumps.

Read-only ROM/capture inputs. Derived tile caches and reports must stay under
this project's ignored local directory. This does not change or enable a game
renderer, stream guest tiles, or produce a replacement-art/widescreen feature.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct


ROM_SHA256 = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
ROOT = Path(__file__).resolve().parents[1]
GRAPHICS = [0x17A000, 0x178000, 0x169000, 0x15C000,
            0x168000, 0x15A000, 0x17C000, 0x17B000]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_uint(data, offset, size):
    if offset < 0 or offset + size > len(data):
        raise ValueError(f'Out-of-range read at {offset:#x}, length {size}')
    return int.from_bytes(data[offset:offset + size], 'little')


def inspect(prefix, rom_path, output, export_cache=False):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'local').resolve()):
        raise ValueError('ROM-derived reports/caches must remain under project local/')
    if output.exists():
        raise ValueError('Use a fresh output directory; existing evidence is never replaced')
    rom = rom_path.read_bytes()
    if sha(rom) != ROM_SHA256:
        raise ValueError('Unsupported ROM identity: exact clean USA input required')
    paths = {kind: Path(str(prefix) + '.' + kind) for kind in
             ('wram.bin', 'vram.bin', 'regs.json', 'cgram.bin')}
    wram, vram, cgram = (paths[k].read_bytes() for k in
                         ('wram.bin', 'vram.bin', 'cgram.bin'))
    regs = json.loads(paths['regs.json'].read_text())
    if (len(wram), len(vram), len(cgram)) != (131072, 65536, 512):
        raise ValueError('Expected complete guest WRAM/VRAM/CGRAM dumps')

    def wr(a, n=1):
        return read_uint(wram, a, n)

    def rr(a, n=1):
        bank, address = a >> 16, a & 0xffff
        if bank >= 0x30 or address < 0x8000 or address + n > 0x10000:
            raise ValueError(f'Unsupported LoROM resource read {a:06X}, length {n}')
        return read_uint(rom, bank * 32768 + address - 0x8000, n)

    checks = {
        'scene_selector': wr(0x040e, 2) == 5,
        'no_map_wrap': wr(0x0407) == 0,
        'regular_producer_state': wr(0x0531) == 0,
        'mode1_bg3_priority': regs['bgmode'] == 9,
        'field_rings': regs['bgsc'][:3] == [0x49, 0x59, 0x51],
        'field_character_bases': regs['bg_tile_adr'] == 0x0400,
    }
    for l in range(2):
        checks[f'layer{l + 1}_map_pointer'] = wr(0x0513 + l * 3, 3) == [0x0996a2, 0x099700][l]
        checks[f'layer{l + 1}_dimensions'] = [wr(0x046d + l * 2), wr(0x046e + l * 2)] == [[2, 2], [4, 4]][l]
        checks[f'layer{l + 1}_metatile_definitions'] = wr(0x0500 + l * 3, 3) == 0x038f58
        checks[f'layer{l + 1}_cell_definitions'] = wr(0x0506 + l * 3, 3) == 0x0a8818
        attr = wr([0x0537, 0x055c][l], 3)
        checks[f'layer{l + 1}_attribute_pointer'] = attr == 0x098210
        checks[f'layer{l + 1}_no_conditional_metatiles'] = (
            attr == 0x098210 and all(rr(attr + i) & 15 not in (14, 15) for i in range(256)))
    if not all(checks.values()):
        raise ValueError('Capture outside the checked Likado contract: ' +
                         ', '.join(k for k, passed in checks.items() if not passed))

    blocks = []
    for index, source in enumerate(GRAPHICS):
        offset = index * 4096
        source_data = bytes(rr(source + i) for i in range(4096))
        actual = vram[offset:offset + 4096]
        matched = actual == source_data
        blocks.append({'vram_byte_offset': offset, 'length': 4096,
                       'rom_source': f'{source:06X}', 'source_sha256': sha(source_data),
                       'capture_sha256': sha(actual), 'source_matches_capture': matched,
                       'source_difference_bytes': sum(a != b for a, b in zip(actual, source_data)),
                       'source_difference_tile_ids': [index * 128 + tile for tile in range(128)
                           if actual[tile * 32:tile * 32 + 32] != source_data[tile * 32:tile * 32 + 32]],
                       'identity_status': 'exact-source-match' if matched else 'mutable-capture-unqualified',
                       'stable_id': f'sots-usa-0/{source:06X}/4bpp-128-tiles' if matched else None})
        # The last block is observed to mutate in this scene. Its animation
        # loader/variant identity is not established by a byte-source scan.
        if index < 7:
            checks[f'graphics_block_{index}_source_matches'] = matched

    layers = []
    caches = {}
    for l in range(2):
        width, height = wr(0x046d + l * 2), wr(0x046e + l * 2)
        map_pointer = wr(0x0513 + l * 3, 3)
        cell_pointer = wr(0x0506 + l * 3, 3)
        tile_pointer = wr(0x0500 + l * 3, 3)
        camera = [int.from_bytes(wram[a:a + 2], 'little', signed=True)
                  for a in (0x02ad + 4 * l, 0x02af + 4 * l)]
        # The proof fixtures intentionally use tile-aligned final camera values.
        # A nonaligned display footprint requires 33x29 cells rather than 32x28.
        if any(v % 8 for v in camera):
            raise ValueError('Use a tile-aligned capture for this exact 32x28 comparison')
        if regs['hscroll'][l] != camera[0] & 1023 or regs['vscroll'][l] != camera[1] & 1023:
            raise ValueError('PPU and guest camera values disagree')
        segment_records = {}
        metatile_ids = set()

        def tile_word(px, py):
            gx, gy = px // 256, py // 256
            metatile = 0
            if 0 <= gx < width and 0 <= gy < height:
                segment = rr(map_pointer + 2 * (gy * width + gx), 2)
                segment_pointer = rr(0x09b000 + 3 * segment, 3)
                segment_records[segment] = segment_pointer
                cell = rr(segment_pointer + ((py >> 5) & 7) * 8 + ((px >> 5) & 7))
                metatile = rr(cell_pointer + cell * 4 + ((py >> 4) & 1) * 2 + ((px >> 4) & 1))
            metatile_ids.add(metatile)
            return rr(tile_pointer + metatile * 8 + ((py >> 3) & 1) * 4 + ((px >> 3) & 1) * 2, 2)

        def ring_word(px, py):
            tx, ty = (px // 8) % 64, (py // 8) % 32
            offset = [0x9000, 0xb000][l] + tx // 32 * 2048 + (ty * 32 + tx % 32) * 2
            return read_uint(vram, offset, 2)

        comparisons = {}
        for region, start, stop in [('center', 0, 256), ('left', -72, 0), ('right', 256, 328)]:
            count, mismatch, inside = 0, 0, 0
            examples = []
            for sy in range(0, 224, 8):
                for sx in range(start, stop, 8):
                    px, py = camera[0] + sx, camera[1] + sy
                    expected, actual = tile_word(px, py), ring_word(px, py)
                    count += 1
                    inside += int(0 <= px < width * 256 and 0 <= py < height * 256)
                    if expected != actual:
                        mismatch += 1
                        if len(examples) < 8:
                            examples.append({'world_pixel': [px, py], 'decoded_word': expected,
                                             'ring_word': actual})
            comparisons[region] = {'compared_tile_words': count, 'ring_mismatch_count': mismatch,
                                   'inside_authored_bounds_count': inside, 'mismatch_examples': examples}
        checks[f'layer{l + 1}_center_exact'] = comparisons['center']['ring_mismatch_count'] == 0
        words = [tile_word(x * 8, y * 8) for y in range(height * 32) for x in range(width * 32)]
        cache = struct.pack('<' + 'H' * len(words), *words)
        name = f'bg{l + 1}-map.words.bin'
        if export_cache:
            caches[name] = cache
        layers.append({'layer': f'BG{l + 1}', 'camera_world_pixels': camera,
                       'map_pointer': f'{map_pointer:06X}', 'map_table_index': [5, 13][l],
                       'map_size_segments': [width, height], 'map_size_tiles': [width * 32, height * 32],
                       'cell_definition_pointer': f'{cell_pointer:06X}',
                       'metatile_definition_pointer': f'{tile_pointer:06X}',
                       'segments': [{'segment_id': i, 'rom_pointer': f'{p:06X}'}
                                    for i, p in sorted(segment_records.items())],
                       'metatile_ids': sorted(metatile_ids), 'comparison': comparisons,
                       'cache': {'file': name if export_cache else None, 'sha256': sha(cache),
                                 'encoding': 'row-major little-endian uint16 SNES tile words',
                                 'length': len(cache)},
                       'stable_id': f'sots-usa-0/map-{map_pointer:06X}/cells-{cell_pointer:06X}/tiles-{tile_pointer:06X}'})
    report = {'status': 'pass' if all(checks.values()) else 'fail',
              'rom_sha256': ROM_SHA256, 'capture_prefix': str(prefix.resolve()),
              'capture_frame': regs['frame'], 'scene_selector': 5,
              'input_hashes': {k: sha(p.read_bytes()) for k, p in paths.items()},
              'checks': checks, 'center_comparisons': sum(
                  l['comparison']['center']['compared_tile_words'] for l in layers),
              'center_mismatches': sum(l['comparison']['center']['ring_mismatch_count'] for l in layers),
              'layers': layers, 'graphics_blocks': blocks,
              'graphics_all_source_matches': all(b['source_matches_capture'] for b in blocks),
              'limits': ['Read-only captured map/resource proof, no gameplay run or guest mutation',
                         'Checked nonwrapping scene-5 resource contract only',
                         'Caches retain original tile words; replacement HD art is not supplied',
                         'Tile animation/loader dispatch and actor visibility remain unqualified',
                         'Player widescreen remains off; no live compositor binding implemented']}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in caches.items():
        (output / name).write_bytes(data)
    (output / 'field-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(output / 'field-report.json')
    print(json.dumps({'status': report['status'], 'center_compared': report['center_comparisons'],
                      'center_mismatches': report['center_mismatches']}))
    return report['status'] == 'pass'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_prefix', type=Path)
    parser.add_argument('rom', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--export-cache', action='store_true')
    args = parser.parse_args()
    try:
        return 0 if inspect(args.capture_prefix, args.rom, args.output, args.export_cache) else 1
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f'Refused field inspection: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
