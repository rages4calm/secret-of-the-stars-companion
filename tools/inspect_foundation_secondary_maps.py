"""Read-only original scene-stream provenance; reports and ROM-derived data stay local.

Static variant coverage is not campaign traversal or dynamic story certification.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json

from inspect_foundation_maps import OriginalMaps


def scene_records(maps, scene):
    pointer = 0x080000 | maps.tables['scenes'][scene]
    records = []
    for _ in range(52):
        if not 0x0882a2 <= pointer < 0x0887e5:
            raise ValueError('Selector record outside original extent')
        selector = maps.read(pointer)
        if selector != 255 and selector > 7:
            raise ValueError('Unknown selector')
        # CA95..CAA4 consumes two operands even though selector7 ignores them.
        size = 3 if selector == 255 else 5
        record = {'record': pointer, 'selector': selector,
                  'operands': [] if selector == 255 else
                  [maps.read(pointer + 1), maps.read(pointer + 2)],
                  'stream': 0x080000 | maps.read(pointer + size - 2, 2)}
        records.append(record)
        if selector == 255:
            return records
        pointer += size
    raise ValueError('Unterminated scene record list')


def parse_stream(maps, start):
    flags = maps.read(start, 2)
    definitions = maps.read(start + 2)
    grid = maps.read(start + 3, 2) & 0x3fff
    dimensions = maps.read(start + 5)
    if grid >= 328:
        raise ValueError('Primary grid index outside original table')

    def layer(grid, cell, tile, dims=None):
        return {'map_index': grid, 'cell_index': cell, 'tile_index': tile,
                'grid': 0x090000 | maps.tables['maps'][grid],
                'cells': 0x0a0000 | maps.tables['cells'][cell],
                'tiles': 0x030000 | maps.tables['tiles'][tile],
                'attributes': 0x090000 | maps.tables['attributes'][tile],
                'dimensions': dims}

    primary = layer(grid, definitions >> 4, definitions & 15,
                    [dimensions >> 4, dimensions & 15])
    cursor = start + 15
    optional = []

    def take(name, size):
        nonlocal cursor
        value = maps.read(cursor, size)
        optional.append({'name': name, 'address': cursor, 'size': size, 'value': value})
        cursor += size
        return value

    for mask, size, name in [(0x6000, 2, 'special_list'),
                             (0x1000, 1, 'cursor_list'),
                             (0x0080, 2, 'event_list'),
                             (0x0040, 1, 'overlay_selector'),
                             (0x0020, 1, 'flag_tiles'),
                             (0x0010, 2, 'stage_tiles')]:
        if flags & mask:
            take(name, size)
    secondary = None
    if flags & 8:
        address = cursor
        mode = take('secondary_mode', 1)
        definitions = take('secondary_definitions', 1)
        grid = take('secondary_grid', 2)  # Original does not mask secondary ID.
        if grid >= 328:
            raise ValueError('Secondary grid outside original table')
        dims = None
        velocity = None
        if mode & 128:
            dimensions = take('secondary_dimensions', 1)
            dims = [dimensions >> 4, dimensions & 15]
            if not all(1 <= value <= 15 for value in dims):
                raise ValueError('Invalid active secondary dimensions')
        else:
            velocity = [take('secondary_velocity_x', 2),
                        take('secondary_velocity_y', 2)]
        secondary = layer(grid, definitions & 15, definitions >> 4, dims)
        secondary.update({'address': address, 'mode': mode,
                          'active': bool(mode & 128), 'velocity_words': velocity})
    for mask, size, name in [(4, 2, 'cursor_script_list'),
                             (2, 1, 'party_value'), (1, 1, 'music')]:
        if flags & mask:
            take(name, size)
    return {'stream': start, 'flags': flags, 'wrap': bool(flags & 0x8000),
            'primary': primary, 'secondary': secondary, 'optional': optional,
            'end': cursor, 'bytes': cursor - start}


def story_value(ram, selector, nibble=0):
    # Original D375 accessor, without its scratch/043/044 writes.
    if selector < 0x78:
        return ram[0x5360 + bool(selector & 8)] & (128 >> (selector & 7))
    if selector == 0x7e:
        return ram[0x5361] & 15
    if selector == 255:
        return (ram[0x5362 + (nibble >> 1)] >> (0 if nibble & 1 else 4)) & 15
    return ram[0x5362 + ((selector & 127) >> 3)] & (128 >> (selector & 7))


def selected_record(records, ram):
    stage = ram[0x5372]
    for record in records:
        selector = record['selector']
        if selector == 255:
            return record
        a, b = record['operands']
        value = story_value(ram, b, b)
        conditions = [stage < a or (stage == a and not value),
                      stage == a and bool(value), stage <= a,
                      stage == a and story_value(ram, 0x7e) == b,
                      bool(story_value(ram, a | 128, b)),
                      not story_value(ram, a | 128, b),
                      story_value(ram, 255, a) == b,
                      bool(ram[0x04b6] & 128)]
        if conditions[selector]:
            return record
    raise ValueError('Missing scene fallback')


def inspect_dump(maps, inventory, prefix):
    raw = Path(str(prefix) + '.wram.bin').read_bytes()
    if len(raw) != 131072:
        raise ValueError('Complete copied WRAM required')
    read = lambda a, n=1: int.from_bytes(raw[a:a + n], 'little')
    scene = read(0x040e, 2)
    if scene >= 337:
        raise ValueError('Scene outside original table')
    selected = selected_record(scene_records(maps, scene), raw)
    stream = inventory[selected['stream']]
    observed = []
    for index in range(2):
        expected = stream['primary'] if not index else stream['secondary']
        actual = {'grid': read(0x0513 + index * 3, 3),
                  'cells': read(0x0506 + index * 3, 3),
                  'tiles': read(0x0500 + index * 3, 3),
                  'attributes': read(0x055c if index else 0x0537, 3),
                  'dimensions': [read(0x046d + index * 2), read(0x046e + index * 2)],
                  'active': bool(read(0x050c + index)),
                  'camera': [read(0x02ad + index * 4, 2), read(0x02af + index * 4, 2)]}
        checked = ['grid', 'cells', 'tiles', 'attributes', 'dimensions']
        active_expected = True if not index else bool(expected and expected['active'])
        tuple_matches = bool(expected and all(actual[key] == expected[key] for key in checked))
        # Inactive fields retain old pointers/dimensions. They must not decode.
        authenticated = actual['active'] == active_expected and (tuple_matches if active_expected else True)
        observed.append({'layer': index, 'expected': expected, 'actual': actual,
                         'active_expected': active_expected,
                         'tuple_matches': tuple_matches, 'authenticated': authenticated})
    optional = {entry['name']: entry['value'] for entry in stream['optional']}
    expected_stage = 0x080000 | maps.read(0x08f600 + optional.get('stage_tiles', 0) * 2, 2)
    expected_flag = (0x080000 | maps.read(0x08e900 + optional['flag_tiles'] * 2, 2)
                     if 'flag_tiles' in optional else None)
    return {'prefix': str(prefix), 'wram_sha256': hashlib.sha256(raw).hexdigest(),
            'scene': scene, 'selected': selected, 'layers': observed,
            'wrap_matches': bool(read(0x0407)) == stream['wrap'],
            'mode_matches': read(0x0452) == (stream['secondary']['mode'] if stream['secondary'] and stream['secondary']['active'] else 0),
            'condition_pointers': {'stage_expected': expected_stage,
                                   'stage_actual': read(0x0456, 3),
                                   'stage_matches': expected_stage == read(0x0456, 3),
                                   'flag_expected': expected_flag,
                                   'flag_actual': read(0x0453, 3),
                                   'flag_matches': None if expected_flag is None else expected_flag == read(0x0453, 3)}}


def optional_tables(maps, streams):
    referenced = collections.defaultdict(set)
    for stream in streams:
        for entry in stream['optional']:
            referenced[entry['name']].add(entry['value'])
    cursor_lists = []
    for index in sorted(referenced['cursor_list']):
        start = 0x0a0000 | maps.read(0x0ad800 + index * 2, 2)
        pointer = start
        variants = []
        for _ in range(52):
            selector = maps.read(pointer)
            if selector != 255 and selector > 7:
                raise ValueError('Unknown cursor-list condition')
            size = 3 if selector == 255 else 5
            payload = 0x0a0000 | maps.read(pointer + size - 2, 2)
            cursor = payload
            sizes = []
            for _ in range(36):
                if maps.read(cursor, 2) == 65535:
                    break
                kind = maps.read(cursor + 6)
                if kind > 2:
                    raise ValueError('Unknown cursor payload kind')
                stride = 9 if kind == 2 else 7
                sizes.append(stride)
                cursor += stride
                if cursor - payload > 254:
                    raise ValueError('Cursor payload exceeds original byte index')
            else:
                raise ValueError('Missing cursor payload sentinel')
            variants.append({'record': pointer, 'selector': selector,
                             'payload': payload, 'record_count': len(sizes),
                             'record_sizes': dict(collections.Counter(sizes)),
                             'payload_bytes': cursor + 2 - payload})
            if selector == 255:
                break
            pointer += size
        else:
            raise ValueError('Missing cursor-list fallback')
        cursor_lists.append({'index': index, 'start': start, 'variants': variants})
    conditions = []
    for name, table, stride in [('flag_tiles', 0x08e900, 4), ('stage_tiles', 0x08f600, 5)]:
        indices = referenced[name] | ({0} if name == 'stage_tiles' else set())
        for index in sorted(indices):
            pointer = 0x080000 | maps.read(table + index * 2, 2)
            cursor = pointer
            count = 0
            while maps.read(cursor, 2) != 65535:
                cursor += stride
                count += 1
                if cursor - pointer > 254:
                    raise ValueError('Conditional tile list exceeds original byte index')
            conditions.append({'kind': name, 'index': index, 'pointer': pointer,
                               'record_count': count, 'bytes': cursor + 2 - pointer})
    return {'cursor_lists': cursor_lists, 'conditional_tiles': conditions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--dump-prefix', action='append', type=Path, default=[])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.relative_to((root / 'local').resolve())
    maps = OriginalMaps(args.rom.read_bytes())
    scenes = [{'scene': i, 'variants': scene_records(maps, i)} for i in range(337)]
    starts = sorted({record['stream'] for scene in scenes for record in scene['variants']})
    streams = [parse_stream(maps, start) for start in starts]
    inventory = {stream['stream']: stream for stream in streams}
    gaps = []
    for index, stream in enumerate(streams[:-1]):
        gap = starts[index + 1] - stream['end']
        if gap < 0:
            raise ValueError('Stream crosses next original stream')
        gaps.append(gap)
    records = {record['record']: record for scene in scenes for record in scene['variants']}
    report = {'kind': 'static original-stream grammar plus copied WRAM provenance, no campaign claim',
              'scenes': scenes, 'streams': streams,
              'summary': {'scene_entries': 337, 'variant_links': sum(len(s['variants']) for s in scenes),
                          'unique_records': len(records), 'distinct_streams': len(streams),
                          'selectors': dict(collections.Counter(r['selector'] for r in records.values())),
                          'secondary_modes': dict(collections.Counter(s['secondary']['mode'] for s in streams if s['secondary'])),
                          'stream_gaps': dict(collections.Counter(gaps))},
              'optional_tables': optional_tables(maps, streams),
              'dumps': [inspect_dump(maps, inventory, p) for p in args.dump_prefix]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'dump_count': len(report['dumps'])}, indent=2))


if __name__ == '__main__':
    main()
