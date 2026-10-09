"""Check bounded native Likado terrain margins using paired copied fixtures."""
from pathlib import Path
import argparse
import csv
import contextlib
import hashlib
import json
import io
import os
import re
import shutil
import struct
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GUEST = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'regs.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    args = parser.parse_args()
    base = ROOT / 'local/runs' / ('field-wide-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    report = {'executable_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(),
              'cases': {}, 'checks': {}, 'limits': [
                  'Likado scene 5 only; terrain side columns do not establish actor visibility outside the original viewport',
                  'No original CPU budget, collision, event, VRAM, OAM or save-state changes',
                  'Headless captures do not certify physical display scanout or controller behavior']}
    cases = [
        ('town', 'likado-east-a', 'wait 60\ndump initial\npress left 90\ndump left\npress right 160\ndump horizontal\n'
         'press down 181\ndump vertical\nwait 30\npress b 1\nwait 40\ndump menu\n'
         'press down 3\nwait 10\npress a 1\nwait 90\ndump submenu\n'
         'press b 1\nwait 40\npress b 1\nwait 90\ndump closed\nquit\n'),
        ('transition', 'likado-inside-a', 'wait 10\ndump inside\npress down 96\nwait 120\ndump outside\nquit\n'),
        ('battle', 'world-cave-a', 'wait 92\ndump end\nquit\n'),
    ]

    def run(name, state, script, enabled, save=False, enhanced=False):
        directory = base / name
        directory.mkdir(); (directory / 'dump').mkdir()
        (directory / 'captures').mkdir()
        shutil.copy2(args.exe, directory / 'game.exe')
        shutil.copy2(state, directory / 'resume.state')
        (directory / 'input.txt').write_text(script)
        (directory / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
            SNESRECOMP_DUMP_DIR=str(directory / 'dump'), SNESRECOMP_FOUNDATION_WIDE=str(enabled),
            SNESRECOMP_FOUNDATION_BATTLE_INFO='0', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(int(enhanced)),
            SNESRECOMP_FOUNDATION_FAST_MENUS='1', SNESRECOMP_FOUNDATION_JOURNAL='0',
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(directory / 'present.bgrx'),
            SNESRECOMP_FOUNDATION_CAPTURE_AT='60', SNESRECOMP_FOUNDATION_FIELD_TRACE=str(directory / 'field.csv'),
            SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE=','.join(map(str, [10, 60, *range(64, 72), 100, 151, 200, 220,
                312, *range(320, 328), 400, 450, 494, 550, 600, 672, 700, 800, 850])),
            SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(directory / 'captures'))
        if save:
            env.update(SNESRECOMP_OVERLAY_SELFTEST='80', SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        with (directory / 'host.log').open('w') as log:
            started = time.perf_counter()
            result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom',
                str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(directory / 'resume.state'),
                '--script', str(directory / 'input.txt')], cwd=directory, env=env,
                stdout=log, stderr=log, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
        rows = list(csv.DictReader((directory / 'field.csv').open())) if (directory / 'field.csv').exists() else []
        report['cases'][name] = {'exit': result.returncode, 'source_state_sha256': hashlib.sha256(state.read_bytes()).hexdigest(),
            'seconds': time.perf_counter() - started, 'wide_fields': len(rows),
            'accepted_lines': sum(int(r['accepted_lines']) for r in rows),
            'rejected_lines': sum(int(r['rejected_lines']) for r in rows),
            'tile_mismatches': sum(int(r['tile_mismatches']) for r in rows),
            'pixel_mismatches': sum(int(r['pixel_mismatches']) for r in rows),
            'stale_ring_margin_words_replaced': sum(int(r['stale_margin_words']) for r in rows),
            'camera_positions': sorted({(int(r['camera_x']), int(r['camera_y'])) for r in rows})}
        return directory

    def compare(name, off, on):
        tags = [p.name[:-len('.wram.bin')] for p in (off / 'dump').glob('*.wram.bin')]
        report['checks'][name + '_guest_state_identical'] = bool(tags) and all(
            (off / 'dump' / (tag + '.' + ext)).read_bytes() == (on / 'dump' / (tag + '.' + ext)).read_bytes()
            for tag in tags for ext in GUEST)
        centers = {}; widths = {}
        for tag in tags:
            a = Image.open(off / 'dump' / (tag + '.fb.bmp')).convert('RGB')
            b = Image.open(on / 'dump' / (tag + '.fb.bmp')).convert('RGB')
            centers[tag] = a.tobytes() == b.crop(((b.width - 256)//2, 0, (b.width + 256)//2, 224)).tobytes()
        composed_centers = {}
        for p in (on / 'captures').glob('*.bgrx'):
            frame, width, height = map(int, re.search(r'frame-(\d+)-(\d+)x(\d+)', p.name).groups())
            original = list((off / 'captures').glob(f'frame-{frame}-*.bgrx'))
            if len(original) != 1: continue
            raw = p.read_bytes()
            center_width = 256 * (height // 224)
            center = b''.join(raw[(y * width + (width-center_width)//2)*4:
                (y*width+(width+center_width)//2)*4] for y in range(height))
            composed_centers[frame] = center == original[0].read_bytes()
            widths[frame] = width
            Image.frombytes('RGB', (width, height), raw, 'raw', 'BGRX').save(p.with_suffix('.png'))
        report['checks'][name + '_original_center_identical'] = all(centers.values())
        report['checks'][name + '_composed_center_identical'] = bool(composed_centers) and all(composed_centers.values())
        report['cases'][name + '-on']['composed_widths'] = widths
        report['cases'][name + '-on']['composed_center_comparisons'] = composed_centers
        report['cases'][name + '-on']['center_comparisons'] = centers

    for name, fixture, script in cases:
        state = ROOT / 'local/runs' / fixture / 'saves/save0.sav'
        off = run(name + '-off', state, script, 0, save=name == 'town')
        on = run(name + '-on', state, script, 1, save=name == 'town')
        compare(name, off, on)
    # State copies produced by the same title state schema, independent cold processes.
    for enabled in (0, 1):
        run('cold-' + ('on' if enabled else 'off'), base / 'town-on/saves/save0.sav',
            'wait 92\ndump end\nquit\n', enabled)
    compare('cold', base / 'cold-off', base / 'cold-on')
    for enabled in (0, 1):
        run('enhanced-' + ('on' if enabled else 'off'), ROOT / 'local/runs/likado-east-a/saves/save0.sav',
            'wait 92\ndump end\nquit\n', enabled, enhanced=True)
    compare('enhanced', base / 'enhanced-off', base / 'enhanced-on')
    town = report['cases']['town-on']
    rows = list(csv.DictReader((base / 'town-on/field.csv').open()))
    report['checks']['terrain_lines_verified'] = town['accepted_lines'] > 224 * 100
    report['checks']['town_no_center_tile_or_pixel_mismatches'] = town['tile_mismatches'] == town['pixel_mismatches'] == 0
    report['checks']['stale_guest_columns_replaced'] = town['stale_ring_margin_words_replaced'] > 0
    report['checks']['horizontal_subtile_positions_exercised'] = len({int(r['camera_x']) % 8 for r in rows}) == 8
    report['checks']['vertical_subtile_positions_exercised'] = len({int(r['camera_y']) % 8 for r in rows}) == 8
    report['checks']['vertical_256_pixel_segment_crossed'] = min(int(r['camera_y']) for r in rows) < 256 <= max(int(r['camera_y']) for r in rows)
    # Some initially unloaded right-hand cells later enter the authentic view.
    # Their ordinary streamed words must equal the independently decoded map.
    from inspect_foundation_field import inspect
    decoded = base / 'decoded-initial'
    with contextlib.redirect_stdout(io.StringIO()):
        inspect(base / 'town-off/dump/initial', ROOT / 'local/inputs/clean-usa.sfc', decoded, export_cache=True)
    first_ram = (base / 'town-off/dump/initial.wram.bin').read_bytes()
    later_ram = (base / 'town-off/dump/horizontal.wram.bin').read_bytes()
    first_vram = (base / 'town-off/dump/initial.vram.bin').read_bytes()
    later_vram = (base / 'town-off/dump/horizontal.vram.bin').read_bytes()
    entered = initially_stale = differences = 0
    for layer in range(2):
        words = (decoded / f'bg{layer+1}-map.words.bin').read_bytes()
        size = 64 if layer == 0 else 128
        cx, cy = struct.unpack_from('<hh', first_ram, 0x2ad + layer*4)
        nx, ny = struct.unpack_from('<hh', later_ram, 0x2ad + layer*4)
        for y in range(cy, cy+224, 8):
            for x in range(cx+256, cx+328, 8):
                if not (nx <= x < nx+256 and ny <= y < ny+224 and 0 <= x < size*8 and 0 <= y < size*8): continue
                at = (0x9000 if layer == 0 else 0xb000) + ((x//8)&31)*2 + ((y//8)&31)*64 + (2048 if (x//8)&32 else 0)
                expected = struct.unpack_from('<H', words, (y//8*size+x//8)*2)[0]
                initially_stale += struct.unpack_from('<H', first_vram, at)[0] != expected
                differences += struct.unpack_from('<H', later_vram, at)[0] != expected
                entered += 1
    report['later_original_view_comparison'] = {'word_count': entered, 'initially_stale': initially_stale, 'later_mismatches': differences}
    report['checks']['new_margin_terrain_later_matches_original_streaming'] = entered > 0 and initially_stale > 0 and differences == 0
    report['checks']['battle_falls_back_to_256'] = report['cases']['battle-on']['composed_widths'][60] == 256
    report['checks']['unsupported_house_falls_back_to_256'] = report['cases']['transition-on']['composed_widths'][10] == 256
    report['checks']['natural_likado_entry_expands_to_400'] = report['cases']['transition-on']['composed_widths'][220] == 400
    report['checks']['all_processes_exit_zero'] = all(c['exit'] == 0 for c in report['cases'].values())
    source = Image.open(base / 'town-on/captures/frame-60-400x224.png')
    source.resize((source.width * 3, source.height * 3), Image.Resampling.NEAREST).save(base / 'likado-wide.png')
    report['passed'] = all(report['checks'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base); print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
