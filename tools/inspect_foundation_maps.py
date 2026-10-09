"""Read-only map contracts from exact original ROM and copied guest dumps.

Reports contain ROM-derived identities and must remain in ignored local/.
Scene/table entry counts describe data structure coverage, never playable maps.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class OriginalMaps:
    def __init__(self, rom):
        if len(rom) != 1572864 or sha(rom) != ROM_SHA256:
            raise ValueError('Exact headerless clean USA ROM required')
        self.rom = rom
        self.tables = {
            'scenes': [self.read(0x088000 + i * 2, 2) for i in range(337)],
            'maps': [self.read(0x099000 + i * 2, 2) for i in range(328)],
            'segments': [self.read(0x09b000 + i * 3, 3) for i in range(1280)],
            'cells': [self.read(0x0a8000 + i * 2, 2) for i in range(16)],
            'tiles': [self.read(0x038000 + i * 2, 2) for i in range(16)],
            'attributes': [self.read(0x098000 + i * 2, 2) for i in range(16)],
        }

    def read(self, address, count=1):
        bank, low = address >> 16, address & 65535
        if bank >= 48 or low < 32768 or low + count > 65536:
            raise ValueError(f'Unsupported LoROM read {address:06X}/{count}')
        offset = bank * 32768 + low - 32768
        if offset + count > len(self.rom):
            raise ValueError('ROM read exceeds image')
        return int.from_bytes(self.rom[offset:offset + count], 'little')

    def span(self, kind, pointer):
        bank = {'maps': 9, 'cells': 10, 'tiles': 3, 'attributes': 9}[kind]
        if pointer >> 16 != bank or pointer & 65535 not in self.tables[kind]:
            raise ValueError(f'{kind} pointer lacks original table membership')
        low = pointer & 65535
        following = [p for p in self.tables[kind] if p > low]
        end = min(following) if following else {'maps': 0xb000, 'cells': 0xbca8,
                                               'tiles': 0xf270, 'attributes': 0x9000}[kind]
        # Final cells/tiles extents are not independently established; permit
        # only bank-contained reads there and expose that limitation in report.
        if not following and kind in ('cells', 'tiles'):
            end = 0x10000
        return end - low

    def scene_primary_variants(self, scene):
        if not 0 <= scene < 337:
            return []
        pointer = 0x080000 + self.tables['scenes'][scene]
        result = []
        for _ in range(52):
            if not 0x0882a2 <= pointer < 0x0887e5:
                raise ValueError('Scene selector left original record region')
            selector = self.read(pointer)
            if selector != 255 and selector > 7:
                raise ValueError('Unknown scene condition selector')
            size = 3 if selector == 255 else 4 if selector == 7 else 5
            stream = 0x080000 + self.read(pointer + size - 2, 2)
            flags = self.read(stream, 2)
            definitions = self.read(stream + 2)
            map_index = self.read(stream + 3, 2) & 0x3fff
            dimensions = self.read(stream + 5)
            if map_index >= 328:
                raise ValueError('Scene primary map index exceeds original table')
            result.append({'selector': selector, 'record': f'{pointer:06X}',
                           'stream': f'{stream:06X}', 'flags': flags,
                           'map_index': map_index, 'wrap': (flags >> 15) & 1,
                           'dimensions': [dimensions >> 4, dimensions & 15],
                           'cell_index': definitions >> 4,
                           'tile_attribute_index': definitions & 15})
            if selector == 255:
                return result
            pointer += size
        raise ValueError('Scene variant record limit exceeded')

    @staticmethod
    def flag_value(wram, selector, threshold):
        if selector < 0x78:
            return wram[0x5360 + bool(selector & 8)] & (128 >> (selector & 7))
        if selector == 0x7e:
            return wram[0x5361] & 15
        if selector == 255:
            return (wram[0x5362 + (threshold >> 1)] >> (0 if threshold & 1 else 4)) & 15
        return wram[0x5362 + ((selector & 127) >> 3)] & (128 >> (selector & 7))

    def conditional(self, wram, attribute, metatile, px, py, observed):
        kind = self.read(attribute + metatile) & 15
        if kind < 14:
            return metatile
        location = (((px >> 4) & 255) << 8) | ((py >> 4) & 255)
        pointer = int.from_bytes(wram[(0x453 if kind == 14 else 0x456):
                                      (0x456 if kind == 14 else 0x459)], 'little')
        stride = 4 if kind == 14 else 5
        for offset in range(0, 256 - stride + 1, stride):
            key = self.read(pointer + offset, 2)
            if key == 65535:
                observed.add((kind, metatile, location, 'absent-record', pointer, -1))
                return metatile
            if key != location:
                continue
            if kind == 14:
                index = self.read(pointer + offset + 2, 2)
                value = wram[0x53f9 + ((index >> 3) & 255)] & (128 >> (index & 7))
                replacement = 2 if value else metatile
            else:
                threshold, selector, alternative = (self.read(pointer + offset + i)
                                                       for i in (2, 3, 4))
                value = self.flag_value(wram, selector, threshold)
                stage = wram[0x5372]
                apply = bool(value) if threshold == 255 else (
                    threshold < stage or (threshold == stage and (selector == 255 or bool(value))))
                replacement = alternative if apply else metatile
            observed.add((kind, metatile, location, 'matched-record', pointer, offset))
            return replacement
        raise ValueError('Conditional record lacks sentinel/match before 8-bit index limit')


def inspect(maps, prefix):
    prefix = prefix.resolve()
    paths = {kind: Path(str(prefix) + '.' + kind) for kind in
             ('wram.bin', 'vram.bin', 'regs.json')}
    raw = {kind: path.read_bytes() for kind, path in paths.items()}
    wram, vram, regs = raw['wram.bin'], raw['vram.bin'], json.loads(raw['regs.json'])
    if len(wram) != 131072 or len(vram) != 65536:
        raise ValueError('Complete WRAM/VRAM snapshots required')
    wr = lambda a, n=1: int.from_bytes(wram[a:a + n], 'little')
    scene = wr(0x40e, 2)
    variants = maps.scene_primary_variants(scene)
    layers, observed = [], set()
    for layer in range(2):
        grid, cell, tile = (wr(a + layer * 3, 3) for a in (0x513, 0x506, 0x500))
        attr = wr((0x537, 0x55c)[layer], 3)
        width, height = wram[0x46d + layer * 2:0x46f + layer * 2]
        if not 1 <= width <= 15 or not 1 <= height <= 15:
            raise ValueError('Dimension nibble contract failed')
        grid_span, cell_span, tile_span, attr_span = (maps.span(k, p) for k, p in
            (('maps', grid), ('cells', cell), ('tiles', tile), ('attributes', attr)))
        if width * height * 2 > grid_span:
            raise ValueError('Grid dimensions exceed original map record span')
        tile_indices = [i for i, p in enumerate(maps.tables['tiles']) if p == tile & 65535
                        and maps.tables['attributes'][i] == attr & 65535]
        if not tile_indices:
            raise ValueError('Tile and attribute tables lack shared original index')
        camera = [int.from_bytes(wram[a:a + 2], 'little', signed=True)
                  for a in (0x2ad + layer * 4, 0x2af + layer * 4)]
        scroll = [regs['hscroll'][layer], regs['vscroll'][layer]]
        actual = [v + ((s - (v & 1023) + 512) % 1024 - 512)
                  for v, s in zip(camera, scroll)]
        active = bool(wram[0x50c + layer])
        def word(px, py):
            if wram[0x407]:
                px %= width * 256
                py %= height * 256
            metatile = 0
            if 0 <= px < width * 256 and 0 <= py < height * 256:
                segment = maps.read(grid + 2 * ((py // 256) * width + px // 256), 2)
                if segment >= 1280:
                    raise ValueError('Segment index exceeds original pointer table')
                pointer = maps.tables['segments'][segment]
                cell_id = maps.read(pointer + ((py >> 5) & 7) * 8 + ((px >> 5) & 7))
                offset = cell_id * 4 + ((py >> 4) & 1) * 2 + ((px >> 4) & 1)
                if offset >= cell_span:
                    raise ValueError('Cell definition exceeds original table record')
                metatile = maps.read(cell + offset)
                if metatile >= attr_span:
                    raise ValueError('Attribute exceeds original table record')
                metatile = maps.conditional(wram, attr, metatile, px, py, observed)
            offset = metatile * 8 + ((py >> 3) & 1) * 4 + ((px >> 3) & 1) * 2
            if offset + 2 > tile_span:
                raise ValueError('Tile word exceeds original table record')
            return maps.read(tile + offset, 2)
        compared = mismatch_count = 0
        examples = []
        if active:
            for ty in range(actual[1] // 8, (actual[1] + 223) // 8 + 1):
                for tx in range(actual[0] // 8, (actual[0] + 255) // 8 + 1):
                    expected = word(tx * 8, ty * 8)
                    rx, ry = tx % 64, ty % 32
                    offset = (0x9000, 0xb000)[layer] + rx // 32 * 2048 + (ry * 32 + rx % 32) * 2
                    current = int.from_bytes(vram[offset:offset + 2], 'little')
                    compared += 1
                    if expected != current:
                        mismatch_count += 1
                        if len(examples) < 8:
                            examples.append({'world': [tx * 8, ty * 8],
                                             'decoded': expected, 'original_ring': current})
        layers.append({'layer': layer + 1, 'active_producer': active,
                       'dimensions_segments': [width, height], 'camera_world': camera,
                       'raster_world': actual, 'raster_matches_camera': actual == camera,
                       'map_pointer': f'{grid:06X}', 'cell_pointer': f'{cell:06X}',
                       'tile_pointer': f'{tile:06X}', 'attribute_pointer': f'{attr:06X}',
                       'map_table_indices': [i for i, p in enumerate(maps.tables['maps']) if p == grid & 65535],
                       'cell_table_indices': [i for i, p in enumerate(maps.tables['cells']) if p == cell & 65535],
                       'tile_attribute_indices': tile_indices,
                       'center_compared': compared, 'center_mismatch_count': mismatch_count,
                       'center_exact': mismatch_count == 0 if active else None,
                       'mismatch_examples': examples,
                       'inactive_policy': None if active else 'Retain original ring; do not populate decoded metatile zero'})
    primary = layers[0]
    links = [v for v in variants if v['map_index'] in primary['map_table_indices']
             and v['cell_index'] in primary['cell_table_indices']
             and v['tile_attribute_index'] in primary['tile_attribute_indices']
             and v['dimensions'] == primary['dimensions_segments'] and v['wrap'] == wr(0x407)]
    return {'prefix': str(prefix), 'input_sha256': {k: sha(v) for k, v in raw.items()},
            'scene': scene, 'guest_mode': wr(0x20), 'wrap': wr(0x407),
            'regular_producer_state': wr(0x531), 'scene_primary_variants': variants,
            'scene_primary_resource_links': links, 'stage_byte_5372': wr(0x5372),
            'conditional_pointers': [f'{wr(a, 3):06X}' for a in (0x453, 0x456)],
            'conditional_records_observed': [list(v) for v in sorted(observed)],
            'flag_state_sha256': sha(wram[0x5360:0x54f9]),
            'layout': {k: regs.get(k) for k in ('inidisp', 'bgmode', 'mosaic', 'setini',
                                              'tm', 'ts', 'bgsc', 'bg_tile_adr')},
            'layers': layers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/inputs/clean-usa.sfc')
    parser.add_argument('--prefix', type=Path, required=True, action='append')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'local').resolve()) or output.exists():
        parser.error('Use a fresh ignored local/ output directory')
    maps = OriginalMaps(args.rom.read_bytes())
    captures = [inspect(maps, prefix) for prefix in args.prefix]
    report = {'rom_sha256': ROM_SHA256, 'inspector_sha256': sha(Path(__file__).read_bytes()),
              'table_entries': {k: len(v) for k, v in maps.tables.items()},
              'observed_scenes': sorted({c['scene'] for c in captures}),
              'captures': captures, 'all_active_centers_exact': all(
                  l['center_exact'] is not False for c in captures for l in c['layers']),
              'all_scene_primary_links_present': all(c['scene_primary_resource_links'] for c in captures),
              'limits': ['Snapshot-derived center words, not gameplay/campaign certification',
                         'Counts describe ROM table entries, not distinct playable maps',
                         'Selected scene variant condition evaluation is not dynamically certified',
                         'Secondary optional scene stream syntax is not parsed here',
                         'Last cells/tiles table end inferred only from bank containment',
                         'Modulo wrap extension needs natural world edge fixtures',
                         'Inactive layers retain original rings',
                         'Raster journal changes within frame require compositor integration checks']}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'observed_scenes': report['observed_scenes'],
                      'all_active_centers_exact': report['all_active_centers_exact'],
                      'all_scene_primary_links_present': report['all_scene_primary_links_present']}))
    return 0 if report['all_active_centers_exact'] and report['all_scene_primary_links_present'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
