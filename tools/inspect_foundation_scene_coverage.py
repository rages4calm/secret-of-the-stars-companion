"""Read-only original scene/primary-resource inventory, not campaign coverage.

Decode every selector entry and validate reachable original primary map data.
Private reports contain identities/counts, never a redistributable art pack.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import time

from inspect_foundation_maps import OriginalMaps, ROM_SHA256

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_primary(maps, variant):
    width, height = variant['dimensions']
    index, cell_index, tile_index = (variant[k] for k in ('map_index', 'cell_index', 'tile_attribute_index'))
    grid = 0x090000 | maps.tables['maps'][index]
    cells = 0x0a0000 | maps.tables['cells'][cell_index]
    tiles = 0x030000 | maps.tables['tiles'][tile_index]
    attributes = 0x090000 | maps.tables['attributes'][tile_index]
    result = {'map_index': index, 'cell_index': cell_index, 'tile_attribute_index': tile_index,
              'dimensions_segments': [width, height], 'wrap': variant['wrap'],
              'grid': f'{grid:06X}', 'cells': f'{cells:06X}', 'tiles': f'{tiles:06X}',
              'attributes': f'{attributes:06X}', 'errors': [], 'warnings': [],
              'secondary_optional_stream_decoded': False}
    if not 1 <= width <= 15 or not 1 <= height <= 15:
        result['errors'].append('Primary header has empty/out-of-contract dimensions; field eligibility must reject')
        result['resource_valid'] = False
        return result
    try:
        spans = {name: maps.span(name, pointer) for name, pointer in
                 [('maps', grid), ('cells', cells), ('tiles', tiles), ('attributes', attributes)]}
        result['spans_bytes'] = spans
        for name, pointer in [('cells', cells), ('tiles', tiles)]:
            if not any(p > (pointer & 65535) for p in maps.tables[name]):
                result['warnings'].append(name+' final end is bank containment, not an independently established resource boundary')
        if width*height*2 > spans['maps']:
            raise ValueError('Primary grid dimensions exceed next original map pointer')
        segments = {maps.read(grid+i*2, 2) for i in range(width*height)}
        if any(segment >= len(maps.tables['segments']) for segment in segments):
            raise ValueError('Reachable segment index exceeds original segment table')
        cell_ids = set()
        for segment in segments:
            pointer = maps.tables['segments'][segment]
            maps.read(pointer+63)  # prove entire authored 8x8 segment stays mapped
            cell_ids.update(maps.read(pointer+i) for i in range(64))
        metatiles = {0}  # nonwrapping original boundary is also a required resource
        for cell in cell_ids:
            if cell*4+4 > spans['cells']:
                raise ValueError('Reachable cell exceeds original cell-definition record')
            metatiles.update(maps.read(cells+cell*4+i) for i in range(4))
        attributes_by_class = Counter()
        conditional = {14: [], 15: []}
        for tile in metatiles:
            if tile >= spans['attributes']:
                raise ValueError('Reachable metatile attribute exceeds original record')
            if tile*8+8 > spans['tiles']:
                raise ValueError('Reachable metatile words exceed original definition record')
            kind = maps.read(attributes+tile) & 15
            attributes_by_class[kind] += 1
            if kind >= 14:
                conditional[kind].append(tile)
            for word in range(4):
                maps.read(tiles+tile*8+word*2, 2)
        if conditional[14]:
            if 2*8+8 > spans['tiles']:
                raise ValueError('Conditional E replacement metatile2 exceeds original definition record')
            result['warnings'].append('Conditional E requires live location records and restored flag state; static references alone do not qualify replacement')
        if conditional[15]:
            result['warnings'].append('Conditional F live record alternatives/stage/selector branches are not determined by primary header alone')
        result.update(resource_valid=True, unique_segments=len(segments),
                      unique_cell_ids=len(cell_ids), unique_metatile_ids=len(metatiles),
                      attribute_class_counts=dict(sorted(attributes_by_class.items())),
                      conditional_e_metatile_ids=sorted(conditional[14]),
                      conditional_f_metatile_ids=sorted(conditional[15]),
                      active_primary_tile_extent=[width*32, height*32])
    except ValueError as error:
        result['errors'].append(str(error))
        result['resource_valid'] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/inputs/clean-usa.sfc')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    rom_path = args.rom.resolve(strict=True)
    before = sha(rom_path)
    maps = OriginalMaps(rom_path.read_bytes())
    output = (args.out or ROOT/'local/evidence'/('scene-coverage-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if not output.is_relative_to((ROOT/'local').resolve()) or output.exists():
        parser.error('Use a fresh private directory under project local/')
    output.mkdir(parents=True)
    scenes = []
    selectors = Counter()
    streams = {}
    tuples = {}
    syntax_errors = []
    for scene in range(len(maps.tables['scenes'])):
        entry = {'scene_table_index': scene, 'selector_pointer': f'08{maps.tables["scenes"][scene]:04X}'}
        try:
            variants = maps.scene_primary_variants(scene)
            entry['variants'] = variants
            entry['variant_count'] = len(variants)
            entry['conditional_selector_types'] = sorted({v['selector'] for v in variants if v['selector'] != 255})
            for variant in variants:
                selectors[variant['selector']] += 1
                stream = variant['stream']
                streams.setdefault(stream, {'scene_indices': [], 'variant': variant})['scene_indices'].append(scene)
                key = (variant['map_index'], variant['cell_index'], variant['tile_attribute_index'],
                       *variant['dimensions'], variant['wrap'])
                if key not in tuples:
                    tuples[key] = inspect_primary(maps, variant)
                    tuples[key]['streams'] = []
                    tuples[key]['scene_indices'] = []
                tuples[key]['streams'].append(stream)
                tuples[key]['scene_indices'].append(scene)
                variant['resource_tuple'] = list(key)
        except ValueError as error:
            entry['syntax_error'] = str(error)
            syntax_errors.append({'scene_table_index': scene, 'error': str(error)})
        scenes.append(entry)
    resources = list(tuples.values())
    for resource in resources:
        resource['streams'] = sorted(set(resource['streams']))
        resource['scene_indices'] = sorted(set(resource['scene_indices']))
    invalid = [r for r in resources if not r['resource_valid']]
    e = [r for r in resources if r.get('conditional_e_metatile_ids')]
    f = [r for r in resources if r.get('conditional_f_metatile_ids')]
    summary = {'scene_table_entries_scanned': len(scenes), 'selector_syntax_failures': len(syntax_errors),
               'scene_variant_references': sum(s.get('variant_count', 0) for s in scenes),
               'unique_variant_streams': len(streams), 'unique_primary_resource_tuples': len(resources),
               'static_primary_resource_valid_tuples': len(resources)-len(invalid),
               'unsupported_primary_resource_tuples': len(invalid),
               'wrapping_primary_resource_tuples': sum(r['wrap'] != 0 for r in resources),
               'conditional_e_primary_resource_tuples': len(e),
               'conditional_f_primary_resource_tuples': len(f),
               'conditional_selector_reference_counts': dict(sorted(selectors.items())),
               'referenced_primary_map_table_indices': len({r['map_index'] for r in resources}),
               'resource_dimension_counts': dict(sorted(Counter('x'.join(map(str, r['dimensions_segments'])) for r in resources).items()))}
    report = {'rom_sha256': ROM_SHA256, 'inspector_sha256': sha(Path(__file__)),
              'original_maps_helper_sha256': sha(ROOT/'tools/inspect_foundation_maps.py'),
              'table_entries': {name: len(values) for name, values in maps.tables.items()},
              'summary': summary, 'scenes': scenes, 'primary_resources': resources,
              'syntax_errors': syntax_errors, 'resource_exceptions': invalid,
              'checks': {'all_original_selector_entries_decoded': not syntax_errors and len(scenes) == 337,
                         'original_rom_unchanged': before == sha(rom_path)},
              'limits': [
                  'Counts describe original table/selector references and unique primary resource tuples, not playable maps or campaign testing',
                  'Static reachable original grid/cell/metatile/attribute checks are distinct from live PPU rendering and actor behavior',
                  'Primary header only; complete optional secondary stream layout and secondary resource provenance are not decoded',
                  'Conditional selectors are enumerated, not dynamically chosen against every story/save state',
                  'Conditional F alternative metatiles depend on live location records; their targets are not proven here',
                  'Final cells/tiles resource extents are bounded by ROM bank containment until their exact end is independently established',
                  'No ROM bytes, art pixels, checkpoints or generated original code are emitted into authored source']}
    report['passed'] = all(report['checks'].values())
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(output), 'passed': report['passed'], 'summary': summary,
                      'exceptions': [{'scenes': r['scene_indices'], 'errors': r['errors']} for r in invalid]}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
