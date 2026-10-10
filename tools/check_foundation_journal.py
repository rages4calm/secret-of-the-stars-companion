"""Bounded original-state journal, real SDL hotkeys and copied cold-load checks."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp'
EXTENSIONS = ['wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=PROOF / 'build/SecretOfTheStarsSNESRecomp.exe')
    parser.add_argument('--cc', type=Path, default=Path.home() / '.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
    args = parser.parse_args()
    base = ROOT / 'local/runs' / ('journal-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    report = {'executable_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(), 'checks': {}, 'cases': {}}
    checks = report['checks']
    after = ROOT / 'local/runs/david-dialogue-a/saves/save0.sav'
    before = ROOT / 'local/runs/david-final-a/saves/save0.sav'
    other = ROOT / 'local/runs/sonya-talk/saves/save0.sav'
    simple = 'wait 60\ndump shown\nwait 90\ndump hidden\nquit\n'

    def run(name, state, enabled, method='keyboard', script=simple, save=False, capture=60, load_at=None):
        directory = base / name
        directory.mkdir(); (directory / 'dump').mkdir()
        shutil.copy2(args.exe, directory / 'game.exe')
        shutil.copy2(state, directory / 'resume.state')
        (directory / 'input.txt').write_text(script)
        (directory / 'foundation.ini').write_text('[Presentation]\nJournal=' + str(enabled) + '\n')
        (directory / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nControls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
            '[Controller]\nSourceP1=2\nSourceP2=0\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_DUMP_DIR=str(directory / 'dump'),
            SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST=method, SNESRECOMP_FOUNDATION_JOURNAL_TRACE=str(directory / 'journal.csv'),
            SNESRECOMP_FOUNDATION_BATTLE_INFO='0', SNESRECOMP_FOUNDATION_FAST_MENUS='1', SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(directory / 'present.bgrx'), SNESRECOMP_FOUNDATION_CAPTURE_AT=str(capture))
        if save:
            env.update(SNESRECOMP_OVERLAY_SELFTEST='80', SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load_at is not None:
            env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load_at), SNESRECOMP_RUN_FRAMES=str(load_at + 100))
        with (directory / 'host.log').open('w') as log:
            result = subprocess.run([str(directory / 'game.exe'), '--no-launcher', '--rom', str(ROOT / 'local/inputs/clean-usa.sfc'),
                '--resume-state', str(directory / 'resume.state'), '--script', str(directory / 'input.txt')],
                cwd=directory, env=env, stdout=log, stderr=log, timeout=40,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        log = (directory / 'host.log').read_text(errors='replace')
        rows = list(csv.DictReader((directory / 'journal.csv').open()))
        report['cases'][name] = {'exit': result.returncode, 'source_checkpoint_sha256': hashlib.sha256(state.read_bytes()).hexdigest(),
            'resumed': 'resume state loaded:' in log, 'shown': log.count('journal shown'), 'hidden': log.count('journal hidden'),
            'virtual_pad_attached': 'virtual pad attached' in log, 'initial_lead': int(rows[0]['has_lead']),
            'initial_stage': int(rows[0]['stage']), 'initial_flags': int(rows[0]['flags']),
            'lead_values': sorted({int(row['has_lead']) for row in rows})}
        return directory

    def parity(left, right):
        files = list((left / 'dump').glob('*.wram.bin'))
        return bool(files) and all((left / 'dump' / (p.name[:-9] + '.' + ext)).read_bytes() ==
            (right / 'dump' / (p.name[:-9] + '.' + ext)).read_bytes() for p in files for ext in EXTENSIONS)

    for name, state, expected in [('before', before, 0), ('after', after, 1), ('other-dialogue', other, 0)]:
        off = run(name + '-off', state, 0)
        on = run(name + '-on', state, 1)
        checks[name + '_guest_unchanged'] = parity(off, on)
        checks[name + '_lead_derived_from_original_state'] = report['cases'][name + '-on']['lead_values'] == [expected]
        checks[name + '_card_changes_host_surface'] = (off / 'present.bgrx').read_bytes() != (on / 'present.bgrx').read_bytes()
        original = (off / 'present.bgrx').read_bytes()
        composed = (on / 'present.bgrx').read_bytes()
        checks[name + '_card_does_not_clip_into_field'] = all(
            original[(y * 256 + x) * 4:(y * 256 + x + 1) * 4] == composed[(y * 256 + x) * 4:(y * 256 + x + 1) * 4]
            for y in range(224) for x in range(256) if not (8 <= x < 248 and 6 <= y < 81))
        case = report['cases'][name + '-on']
        checks[name + '_keyboard_once_per_press'] = case['shown'] == case['hidden'] == 1
    pad_off = run('pad-off', after, 0, 'pad')
    pad_on = run('pad-on', after, 1, 'pad')
    checks['pad_guest_unchanged'] = parity(pad_off, pad_on)
    checks['pad_real_sdl_virtual_event_path'] = report['cases']['pad-on']['virtual_pad_attached']
    checks['pad_once_per_press'] = report['cases']['pad-on']['shown'] == report['cases']['pad-on']['hidden'] == 1
    checks['keyboard_and_pad_same_card'] = (base / 'after-on/present.bgrx').read_bytes() == (pad_on / 'present.bgrx').read_bytes()
    closed_off = run('closed-off', after, 0, capture=150)
    closed_on = run('closed-on', after, 1, capture=150)
    checks['closed_card_restores_original_host_surface'] = (closed_off / 'present.bgrx').read_bytes() == (closed_on / 'present.bgrx').read_bytes()

    # Natural full introduction from the known pre-introduction checkpoint.
    dialogue_script = (ROOT / 'local/runs/david-dialogue-a/input.txt').read_text()
    off = run('natural-intro-off', before, 0, script=dialogue_script)
    on = run('natural-intro-on', before, 1, script=dialogue_script)
    checks['natural_intro_guest_unchanged'] = parity(off, on)
    checks['natural_intro_lead_appears_only_after_original_flag'] = report['cases']['natural-intro-on']['lead_values'] == [0, 1]

    # New saved copies, no journal serialization: restore the original state.
    modal = run('modal-reset', after, 1, save=True)
    modal_rows = list(csv.DictReader((modal / 'journal.csv').open()))
    checks['host_modal_reset_closes_card_and_next_press_reopens'] = (
        report['cases']['modal-reset']['shown'] == 2 and report['cases']['modal-reset']['hidden'] == 0 and
        any(int(row['frame']) > 80 and int(row['frame']) < 91 and int(row['visible']) == 0 for row in modal_rows))
    saved = modal / 'saves/save0.sav'
    replay_a = run('cold-replay-a', saved, 1)
    replay_b = run('cold-replay-b', saved, 1)
    checks['cold_replay_guest_identical'] = parity(replay_a, replay_b)
    checks['cold_restore_derives_lead_on_first_frame'] = report['cases']['cold-replay-a']['initial_lead'] == report['cases']['cold-replay-b']['initial_lead'] == 1
    checks['cold_restore_card_identical'] = (replay_a / 'present.bgrx').read_bytes() == (replay_b / 'present.bgrx').read_bytes()
    rollback_off = run('in-process-rollback-off', before, 0, method='none', script=dialogue_script, save=True, load_at=1000)
    rollback_on = run('in-process-rollback-on', before, 1, method='none', script=dialogue_script, save=True, load_at=1000)
    rollback = list(csv.DictReader((rollback_on / 'journal.csv').open()))
    checks['in_process_rollback_guest_unchanged'] = parity(rollback_off, rollback_on)
    checks['in_process_load_reconciles_lead_without_native_history'] = (
        any(int(row['frame']) < 1000 and int(row['has_lead']) == 1 for row in rollback) and
        all(int(row['has_lead']) == 0 for row in rollback if 1001 <= int(row['frame']) <= 1010) and
        '[overlay_selftest] load issued' in (rollback_on / 'host.log').read_text(errors='replace'))

    # Pure synthetic stage logic only: never alter guest RAM/checkpoints.
    unit = base / 'stage-unit.c'
    unit.write_text('#include "foundation_journal.h"\nint main(void) {\n'
        'for(unsigned s=0;s<256;s++) for(unsigned f=0;f<256;f++) {\n'
        'unsigned expected=s==1?2:(s==0 && (f&0x40)?1:0);\n'
        'if(FoundationJournalLead(s,f)!=expected) return 1;\n'
        'if(FoundationJournalHasLead(s,f)!=(expected!=0)) return 2; }\n'
        'return 0; }\n')
    compiled = subprocess.run([str(args.cc), str(unit), '-I', str(ROOT / 'native/foundation/src'), '-I',
        str(PROOF / 'snesrecomp/runner/src/desktop'), '-o', str(base / 'stage-unit.exe')], capture_output=True, text=True)
    (base / 'stage-unit.log').write_text(compiled.stdout + compiled.stderr)
    checks['synthetic_stage_reset_has_no_stale_lead'] = compiled.returncode == 0 and subprocess.run([str(base / 'stage-unit.exe')]).returncode == 0

    from PIL import Image, ImageDraw
    contact = Image.new('RGB', (256 * 3, 244), '#080e1c')
    draw = ImageDraw.Draw(contact)
    for col, name in enumerate(['before-on', 'after-on', 'other-dialogue-on']):
        pixels = (base / name / 'present.bgrx').read_bytes()
        image = Image.frombytes('RGB', (256, 224), pixels, 'raw', 'BGRX')
        image.save(base / name / 'present.png')
        contact.paste(image, (256 * col, 20)); draw.text((256 * col + 5, 4), name, fill='white')
    contact.save(base / 'journal-cards.png')
    report['limits'] = ['Stage-zero David introduction and stage-one Bosen current lead; no Crest completion rule',
        'Stage-one event and restoration use the separate explicit-fixture progression checker; other-stage rejection here is a synthetic predicate unit',
        'Cold checkpoint restores covered; actual interactive rewind timeline not exercised here',
        'Keyboard events and SDL virtual L3 covered; physical controller not newly certified',
        'No persistent native journal history; card derives from original restored guest state']
    report['passed'] = all(checks.values()) and all(case['exit'] == 0 and case['resumed'] for case in report['cases'].values())
    (base / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base); print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
