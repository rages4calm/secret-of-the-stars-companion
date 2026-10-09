"""Qualify native field-menu batching on copied checkpoints and finite inputs."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx')
MENU = 'wait 30\npress b 1\nwait 89\ndump menu\npress b 1\nwait 120\ndump field\nquit\n'
QUICK = 'wait 30\npress b 1\nwait 4\npress a 1\nwait 20\ndump submenu\npress b 1\nwait 20\npress b 1\nwait 40\ndump field\nquit\n'
READY = 'wait 30\npress b 1\nwait 40\npress a 1\nwait 90\ndump submenu\npress b 1\nwait 90\npress b 1\nwait 90\ndump field\nquit\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    parser.add_argument('--reference-exe', type=Path, required=True, help='Previously qualified original executable')
    args = parser.parse_args()
    base = ROOT / 'local/runs' / ('fast-menus-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    state = ROOT / 'local/runs/clean-to-outdoors/saves/save0.sav'
    report = {'executable_sha256': digest(args.exe), 'reference_executable_sha256': digest(args.reference_exe),
              'source_checkpoint_sha256': digest(state), 'cases': {}, 'checks': {}}

    def run(name, script, checkpoint=state, fast=1, reference=False, save=None, video=False):
        directory = base / name
        directory.mkdir()
        (directory / 'dump').mkdir()
        shutil.copy2(args.reference_exe if reference else args.exe, directory / 'game.exe')
        shutil.copy2(checkpoint, directory / 'resume.state')
        (directory / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (directory / 'input.txt').write_text(script)
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
            SNESRECOMP_FOUNDATION_FAST_MENUS=str(fast), SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0', SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
            SNESRECOMP_FOUNDATION_MENU_TRACE='1', SNESRECOMP_FOUNDATION_TRACE=str(directory / 'foundation.csv'))
        if video:
            env['SNESRECOMP_FOUNDATION_VIDEO_RAW'] = str(directory / 'video.bgrx')
        if save is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save), SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom',
                str(ROOT / 'local/inputs/clean-usa.sfc'), '--resume-state', str(directory / 'resume.state'),
                '--script', str(directory / 'input.txt')], cwd=directory, env=env,
                stdout=log, stderr=log, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
        host = (directory / 'host.log').read_text(errors='replace')
        report['cases'][name] = {'exit': result.returncode, 'resumed': 'resume state loaded:' in host,
            'native_batches': host.count('[foundation_menu]'),
            'passed': result.returncode == 0 and 'resume state loaded:' in host}
        return directory

    def equal(a, b, tags, extensions=EXTENSIONS):
        return all((a / 'dump' / (tag + '.' + ext)).read_bytes() ==
            (b / 'dump' / (tag + '.' + ext)).read_bytes() for tag in tags for ext in extensions)

    old = run('previous-original', MENU, reference=True, fast=0)
    slow = run('original', MENU, fast=0, video=True)
    fast = run('fast', MENU, save=80, video=True)
    checks = report['checks']
    checks['disabled_matches_previous_six_guest_captures'] = equal(old, slow, ('menu', 'field'))
    checks['sram_palette_preserved'] = equal(slow, fast, ('menu', 'field'), ('sram.bin', 'cgram.bin'))
    checks['field_vram_restored'] = equal(slow, fast, ('field',), ('vram.bin',))
    checks['field_queue_idle'] = (fast / 'dump/field.wram.bin').read_bytes()[0x2a0] == 0
    checks['same_guest_frame_count'] = len((slow / 'foundation.csv').read_text().splitlines()) == len((fast / 'foundation.csv').read_text().splitlines())

    def frames(directory):
        raw = (directory / 'video.bgrx').read_bytes()
        size = 256 * 224 * 4
        assert len(raw) % size == 0
        return [Image.frombytes('RGB', (256, 224), raw[i:i+size], 'raw', 'BGRX') for i in range(0, len(raw), size)]

    videos = {name: frames(directory) for name, directory in [('original', slow), ('fast', fast)]}
    boxes = [(24, 16, 64, 128), (64, 153, 233, 173)]  # Menu labels and HP/MP; exclude blinking cursor.
    targets = [Image.open(slow / 'dump/menu.fb.bmp').crop(box).tobytes() for box in boxes]
    opening = {}
    closing = {}
    for name, images in videos.items():
        opening[name] = next(i + 1 for i, im in enumerate(images) if all(im.crop(box).tobytes() == target for box, target in zip(boxes, targets)))
        # The solid interior of both menu panels is distinct from this outdoor scene.
        menu_color = images[119].getpixel((60, 100))
        closing[name] = next(i + 1 for i, im in enumerate(images) if i >= 121 and
            menu_color not in im.get_flattened_data())
    report['latency'] = {'press_frame': 31, 'menu_complete_frame': opening,
        'open_delay_guest_frames': {k: v - 31 for k, v in opening.items()},
        'close_press_frame': 122, 'panels_gone_frame': closing,
        'close_delay_guest_frames': {k: v - 122 for k, v in closing.items()}, 'nominal_hz': 60,
        'limit': 'Guest frame measurement; excludes physical controller and display latency'}
    checks['open_within_four_frames'] = opening['fast'] - 31 <= 4
    checks['close_within_two_frames'] = closing['fast'] - 122 <= 2
    checks['opening_improved'] = opening['fast'] < opening['original']
    contact = Image.new('RGB', (4 * 256, 2 * 244))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(contact)
    for y, name in enumerate(('original', 'fast')):
        for x, frame in enumerate((34, 52, 122, 123)):
            contact.paste(videos[name][frame-1], (x * 256, y * 244 + 20))
            draw.text((x*256+4, y*244+4), f'{name} frame {frame}', fill='white')
    contact.save(base / 'menu-comparison.png')

    quick = run('quick', QUICK)
    delayed = run('quick-original', QUICK, fast=0)
    report['early_confirm_surface_differs_from_original'] = not equal(quick, delayed, ('submenu',), ('vram.bin',))
    # Different field durations change animated graphic tiles. Check the actual
    # BG3 menu tilemap footprint, not unrelated time-dependent graphics.
    report['rapid_back_during_original_submenu_construction_returns_field'] = (quick / 'dump/field.vram.bin').read_bytes()[0xa000:0xb000] == \
        (fast / 'dump/field.vram.bin').read_bytes()[0xa000:0xb000]
    # Interactive row producers deliberately retain original timing after the
    # clipping repair. Keep rapid-input results visible: different VRAM alone
    # did not prove early confirm was consumed. Require stable menu interaction
    # and return on the original-ready schedule instead.
    ready = run('ready-back', READY)
    ready_original = run('ready-back-original', READY, fast=0)
    checks['back_after_submenu_ready_restores_bg3_tilemap'] = (ready / 'dump/field.vram.bin').read_bytes()[0xa000:0xb000] == \
        (ready_original / 'dump/field.vram.bin').read_bytes()[0xa000:0xb000]
    checks['ready_submenu_matches_original_bg3'] = (ready/'dump/submenu.vram.bin').read_bytes()[0xa000:0xb000] == (ready_original/'dump/submenu.vram.bin').read_bytes()[0xa000:0xb000]
    field_image=Image.open(ready/'dump/field.fb.bmp')
    checks['ready_back_reaches_field_pixels']=field_image.crop((24,16,64,128)).tobytes()==Image.open(fast/'dump/field.fb.bmp').crop((24,16,64,128)).tobytes()
    saved = fast / 'saves/save0.sav'
    probe = run('checkpoint-probe', 'wait 1\ndump begin\nquit\n', saved)
    first = json.loads((probe / 'dump/begin.info.json').read_text())['frame']
    target = json.loads((fast / 'dump/menu.info.json').read_text())['frame']
    resumed = run('checkpoint-resumed', f'wait {target-first+1}\ndump menu\npress b 1\nwait 120\ndump field\nquit\n', saved)
    checks['menu_checkpoint_replay_exact'] = equal(fast, resumed, ('menu', 'field'))
    report['saved_menu_checkpoint_sha256'] = digest(saved)

    battle_script = (ROOT / 'local/runs/native-damage-original/input.txt').read_text()
    battle_state = ROOT / 'local/runs/world-cave-a/saves/save0.sav'
    battle_old = run('battle-original', battle_script, battle_state, fast=0, reference=True)
    battle_new = run('battle-fast', battle_script, battle_state)
    tags = [p.name[:-len('.wram.bin')] for p in (battle_old / 'dump').glob('*.wram.bin')]
    checks['battle_replay_exact'] = equal(battle_old, battle_new, tags)
    checks['no_field_batches_in_battle'] = report['cases']['battle-fast']['native_batches'] == 0
    dialogue_state = ROOT / 'local/runs/david-final-a/saves/save0.sav'
    dialogue_script = (ROOT / 'local/david-dialogue.txt').read_text()
    dialogue_old = run('dialogue-original', dialogue_script, dialogue_state, fast=0, reference=True)
    dialogue_new = run('dialogue-fast', dialogue_script, dialogue_state)
    tags = [p.name[:-len('.wram.bin')] for p in (dialogue_old / 'dump').glob('*.wram.bin')]
    checks['dialogue_replay_exact'] = bool(tags) and equal(dialogue_old, dialogue_new, tags)
    checks['no_field_batches_in_dialogue'] = report['cases']['dialogue-fast']['native_batches'] == 0
    checks['source_checkpoint_unchanged'] = digest(state) == report['source_checkpoint_sha256']
    report['passed'] = all(checks.values()) and all(c['passed'] for c in report['cases'].values())
    report['limits'] = ['Single-party outdoor menu plus copied two-Red-Slime battle and David dialogue',
        'Interactive submenu rows keep original animation timing; rapid back during construction is not buffered',
        'Unknown UI records retain original waits; future AOT UI paths must explicitly integrate batching',
        'Reference-core timing/NPC differences remain unresolved; no campaign or HD/widescreen qualification']
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
