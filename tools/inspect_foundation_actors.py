"""Inspect exact Likado regular actor records and their original OAM producer.

Read-only inputs and copied diagnostic runs only. Reports retain ROM-derived
descriptors under ignored local/. This does not add actors to the renderer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'regs.json', 'fb.bgrx')
SCRIPT = ('wait 2\ndump start\nwait 1\ndump start_next\n'
          'press right 32\ndump edge\nwait 1\ndump edge_next\n'
          'press right 8\ndump entered\nwait 1\ndump entered_next\n'
          'press right 24\ndump further\nwait 1\ndump further_next\n'
          'press left 40\ndump return\nwait 1\ndump return_next\nquit\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def word(data, address):
    return int.from_bytes(data[address:address + 2], 'little')


def signed(value):
    value &= 65535
    return value - 65536 if value & 32768 else value


def rom_slice(rom, address, length):
    bank, low = address >> 16, address & 65535
    offset = (bank & 127) * 32768 + (low & 32767)
    if low < 32768 or low + length > 65536 or offset + length > len(rom):
        raise ValueError(f'Unsupported LoROM read {address:06X}+{length}')
    return rom[offset:offset + length]


def oam_piece(oam, slot):
    x, y, tile, attr = oam[slot * 4:slot * 4 + 4]
    high = (oam[512 + slot // 4] >> ((slot % 4) * 2)) & 3
    return {'slot': slot, 'x9': x + ((high & 1) << 8), 'y8': y,
            'tile': tile, 'attr': attr, 'large': high >> 1}


def original_gate(value, stop):
    value &= 65535
    return value >= 0xfff1 or value < stop


def inspect(prefix, rom):
    inputs = {ext: Path(str(prefix) + '.' + ext).read_bytes() for ext in EXTENSIONS}
    ram, vram, oam = (inputs[ext] for ext in ('wram.bin', 'vram.bin', 'oam.bin'))
    regs = json.loads(inputs['regs.json'])
    if (len(ram), len(vram), len(oam)) != (131072, 65536, 544):
        raise ValueError('Complete WRAM/VRAM/OAM dump required')
    checks = {
        'scene5': word(ram, 0x40e) == 5,
        'no_wrap': ram[0x407] == 0,
        'regular_producer_state': ram[0x531] == 0,
        'field_presentation': regs['bgmode'] == 9 and regs['bgsc'][:3] == [73, 89, 81] and regs['obsel'] == 3,
        'regular_map_resources': int.from_bytes(ram[0x513:0x516], 'little') == 0x0996a2 and
            int.from_bytes(ram[0x516:0x519], 'little') == 0x099700,
        'zero_sprite_offsets': word(ram, 0x471) == word(ram, 0x473) == 0,
        'checked_draw_route': ram[0x401] == 12,
        'no_variable_sprite_records': all(ram[0x4300 + i * 21] == 0 for i in range(8)),
        'one_regular_party_actor': ram[0x4000] != 255 and word(ram, 0x4003) != 0xb0 and
            all(ram[0x4000 + i * 18] == 255 for i in range(1, 5)),
        'no_special_actor_records': all(ram[0x4100 + i * 25] == 255 for i in (17, 18)),
    }
    if not all(checks.values()):
        raise ValueError('Unsupported actor capture: ' + ', '.join(k for k, v in checks.items() if not v))
    camera = [signed(word(ram, address)) for address in (0x2ad, 0x2af)]
    # D803 consumes four pieces for the one checked party actor at slot12.
    # This fixture excludes variable sprites and the B0 special constructor.
    slot = 16
    mask = 0xefff if ram[0x400] else 0xffff
    actors, assets = [], {}
    comparisons = 0
    for index in range(19):
        address = 0x4100 + index * 25
        record = ram[address:address + 25]
        active = record[0] != 255
        actor = {'index': index, 'record_wram': f'7E:{address:04X}',
                 'record_sha256': sha(record), 'raw_record_hex': record.hex(),
                 'active_draw_record': active, 'flags': record[0]}
        if not active:
            actors.append(actor)
            continue
        if word(record, 5) == 0xb0 or index >= 17:
            raise ValueError('Special regular-actor constructor remains unqualified')
        world = [word(record, 1), word(record, 3)]
        screen = [signed(world[i] - camera[i]) for i in range(2)]
        visible = original_gate(screen[0], 255) and original_gate(screen[1], 239)
        gfx = (word(record, 5) + ((record[0] * 2) & 255) + (ram[0x475] >> 7)) & 65535
        source = 0x0e9800 + gfx * 8
        table = rom_slice(rom, source, 8)
        pieces = []
        for part, (dx, dy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            tileword = word(table, part * 2) & mask
            x, y = screen[0] + dx, screen[1] - 1 + dy
            piece = {'part': part, 'screen': [x, y], 'x9': x & 511, 'y8': y & 255,
                     'tile': tileword & 255, 'attr': tileword >> 8, 'large': 0}
            # Current VRAM graphics are authoritative for this frame. A unique
            # exact clean-ROM tile match supplies a stable original-art ID.
            tile_base = 0xe000 if tileword & 256 else 0xc000
            offset = tile_base + (tileword & 255) * 32
            pixels = vram[offset:offset + 32]
            key = f'{offset:04X}'
            if key not in assets:
                hits, at = [], rom.find(pixels)
                while at >= 0 and len(hits) < 2:
                    hits.append((at // 32768 << 16) | (at % 32768 + 32768))
                    at = rom.find(pixels, at + 1)
                assets[key] = {'vram_byte': offset, 'tile_sha256': sha(pixels),
                    'unique_rom_source': f'{hits[0]:06X}' if len(hits) == 1 else None,
                    'stable_id': f'sots-usa-0/{hits[0]:06X}/4bpp-8x8' if len(hits) == 1 else None}
            piece['asset'] = key
            if visible:
                piece['slot'] = slot + part
                actual = oam_piece(ram[0x2200:0x2420], slot + part)
                piece['staging_exact'] = all(actual[k] == piece[k] for k in ('x9', 'y8', 'tile', 'attr', 'large'))
                comparisons += 1
            pieces.append(piece)
        actor.update(world=world, screen_anchor=screen, original_draw_gate=visible,
                     within400_margin=screen[0] < 328 and screen[0] + 16 > -72 and
                         screen[1] - 1 < 224 and screen[1] + 15 > 0,
                     descriptor_rom=f'{source:06X}', descriptor_sha256=sha(table),
                     sprite_base=word(record, 5), frame_phase=ram[0x475] >> 7,
                     original_art_mask=f'{mask:04X}', pieces=pieces)
        if visible:
            slot += 4
        actors.append(actor)
    checks['exact_staging_regular_actor_pieces'] = comparisons > 0 and all(
        p['staging_exact'] for a in actors for p in a.get('pieces', []) if 'staging_exact' in p)
    checks['original_allocation_cursor'] = word(ram, 0x46b) == slot * 4
    return {'prefix': str(prefix.resolve()), 'frame': regs['frame'], 'camera': camera,
            'ppu_scroll': [regs['hscroll'][0], regs['vscroll'][0]],
            'phase': ram[0x475] >> 7, 'checks': checks, 'piece_comparisons': comparisons,
            'input_hashes': {ext: sha(data) for ext, data in inputs.items()},
            'actors': actors, 'original_tile_assets': list(assets.values())}


def capture(base, exe, fixture, rom_path):
    input_hashes = {str(p.resolve()): sha(p.read_bytes()) for p in (exe, fixture, rom_path)}
    frozen = base / 'immutable.exe'
    shutil.copy2(exe, frozen)
    cases = {}
    for name, scope in [('observer-off', None), ('oam-observer', '2200:241f'), ('actor-observer', '4100:42da')]:
        directory = base / name
        directory.mkdir()
        (directory / 'dump').mkdir()
        shutil.copy2(frozen, directory / 'game.exe')
        shutil.copy2(fixture, directory / 'resume.state')
        (directory / 'input.txt').write_text(SCRIPT)
        (directory / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
            SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
            SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory / 'cpu.csv'),
            SNESRECOMP_FOUNDATION_TRACE=str(directory / 'field.csv'),
            SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0', SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',
            SNESRECOMP_FOUNDATION_FAST_MENUS='0', SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FOUNDATION_JOURNAL='0', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
            SNESRECOMP_FOUNDATION_HD_MENU_FRAMES='0', SNESRECOMP_FOUNDATION_WIDE='0')
        if scope:
            env.update(SNESRECOMP_WLOG_ADDR=f'{scope}:{directory / "writes.tsv"}', SNESRECOMP_WLOG_ADDR_CAP='200000')
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom', str(rom_path),
                '--resume-state', str(directory / 'resume.state'), '--script', str(directory / 'input.txt')],
                cwd=directory, env=env, stdout=log, stderr=log, timeout=45,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        text = (directory / 'host.log').read_text(errors='replace')
        cases[name] = {'exit': result.returncode, 'resumed': 'resume state loaded:' in text,
            'gamepad_input_disabled': 'enable_gamepad=[0,0]' in text,
            'script_sha256': sha((directory / 'input.txt').read_bytes()),
            'write_rows': len((directory / 'writes.tsv').read_text().splitlines()) if scope else 0}
    left = base / 'observer-off'
    tags = sorted(p.name[:-len('.wram.bin')] for p in (left / 'dump').glob('*.wram.bin'))
    checks = {'all_cases_exit_resume_and_disable_gamepads': all(
        c['exit'] == 0 and c['resumed'] and c['gamepad_input_disabled'] for c in cases.values()),
        'frozen_binary_identity': all(sha((base / name / 'game.exe').read_bytes()) == sha(frozen.read_bytes()) for name in cases),
        'source_inputs_preserved': all(sha(Path(p).read_bytes()) == h for p, h in input_hashes.items())}
    for name in ('oam-observer', 'actor-observer'):
        right = base / name
        checks[name + '_same_snapshot_tags'] = tags == sorted(p.name[:-len('.wram.bin')] for p in (right / 'dump').glob('*.wram.bin'))
        checks[name + '_guest_and_pixels_exact'] = bool(tags) and all(
            (left / 'dump' / (tag + '.' + ext)).read_bytes() == (right / 'dump' / (tag + '.' + ext)).read_bytes()
            for tag in tags for ext in EXTENSIONS)
        checks[name + '_cpu_schedule_exact'] = (left / 'cpu.csv').read_bytes() == (right / 'cpu.csv').read_bytes()
        checks[name + '_field_trace_exact'] = (left / 'field.csv').read_bytes() == (right / 'field.csv').read_bytes()
    return {'input_hashes': input_hashes, 'cases': cases, 'checks': checks}, [left / 'dump' / tag for tag in tags]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/inputs/clean-usa.sfc')
    parser.add_argument('--prefix', type=Path, action='append', default=[])
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--fixture', type=Path, default=ROOT / 'local/runs/likado-east-a/saves/save0.sav')
    parser.add_argument('--output', type=Path, default=ROOT / 'local/evidence' / ('wide-actors-' + time.strftime('%Y%m%d-%H%M%S')))
    args = parser.parse_args()
    rom_path = args.rom.resolve()
    rom = rom_path.read_bytes()
    if sha(rom) != ROM_SHA:
        raise ValueError('Exact clean USA ROM required')
    base = args.output.resolve()
    if not base.is_relative_to((ROOT / 'local').resolve()) or base.exists():
        raise ValueError('Use a fresh output directory under project local/')
    if args.capture and not args.exe:
        parser.error('--capture requires --exe; never implicitly use the owner installation')
    if not args.capture and not args.prefix:
        parser.error('Provide copied --prefix input(s) or --capture with an explicit diagnostic --exe')
    base.mkdir(parents=True)
    report = {'rom_sha256': ROM_SHA, 'inspector_sha256': sha(Path(__file__).read_bytes()),
        'source_contract': {'actor_route': {'start': '01DA56', 'end_exclusive': '01DB2D',
            'sha256': sha(rom_slice(rom, 0x01da56, 0xdb2d - 0xda56))},
            'four_piece_emitter': {'start': '01DE2A', 'end_exclusive': '01DED3',
                'sha256': sha(rom_slice(rom, 0x01de2a, 0xded3 - 0xde2a))},
            'read_only_capture_candidate_pc': '01DAB6', 'original_word_store_pc': '01DE5D',
            'world_x_update_pc': '01C1E0', 'offscreen_timer_store_pc': '01C100'},
        'limits': ['No guest writes or actor rendering changes', 'Exact nonwrapping Likado regular four-piece actors only',
            'Current WRAM staging and scanned-out OAM are different phases', 'FF inactive records and parked OAM are never actors',
            'Other maps, special B0/composite actors, actor spawning and campaign coverage remain unqualified']}
    prefixes = [p.resolve() for p in args.prefix]
    if args.capture:
        report['capture'], captured = capture(base, args.exe.resolve(), args.fixture.resolve(), rom_path)
        prefixes += captured
    snapshots = sorted([inspect(p, rom) for p in prefixes], key=lambda s: s['frame'])
    report['snapshots'] = snapshots
    checks = report.setdefault('checks', {})
    checks['all_supported_snapshots_exact'] = bool(snapshots) and all(all(s['checks'].values()) for s in snapshots)
    linked = []
    for previous, current in zip(snapshots, snapshots[1:]):
        if current['frame'] != previous['frame'] + 1:
            continue
        oam = Path(current['prefix'] + '.oam.bin').read_bytes()
        pieces = [p for a in previous['actors'] for p in a.get('pieces', []) if 'slot' in p]
        matches = sum(all(oam_piece(oam, p['slot'])[k] == p[k] for k in ('x9', 'y8', 'tile', 'attr', 'large')) for p in pieces)
        linked.append({'producer_frame': previous['frame'], 'scanout_frame': current['frame'],
                       'pieces': len(pieces), 'exact_matches': matches})
    report['one_field_oam_lineage'] = linked
    if args.capture:
        checks['adjacent_original_oam_lineage_exact'] = bool(linked) and all(r['pieces'] == r['exact_matches'] for r in linked)
        samples = [s['actors'][3] for s in snapshots]
        checks['same_edge_actor_record_exists_before_and_after_draw'] = all(a['active_draw_record'] and a['world'] == [272, 208] and a['sprite_base'] == 0x268 for a in samples)
        checks['edge_actor_has_culled_and_original_drawn_samples'] = any(not a['original_draw_gate'] and a['within400_margin'] for a in samples) and any(a['original_draw_gate'] for a in samples)
        report['edge_actor_samples'] = [{'frame': s['frame'], 'camera': s['camera'],
            'flags': s['actors'][3]['flags'], 'screen': s['actors'][3]['screen_anchor'],
            'drawn': s['actors'][3]['original_draw_gate'], 'margin': s['actors'][3]['within400_margin']} for s in snapshots]
        checks.update(report['capture']['checks'])
    report['passed'] = all(checks.values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(base), 'passed': report['passed'], 'checks': checks,
                      'snapshots': len(snapshots), 'piece_comparisons': sum(s['piece_comparisons'] for s in snapshots)}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
