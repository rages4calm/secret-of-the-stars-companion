"""Explicit staged developer fixtures for the current-possession journal.

This does not manufacture an original award/removal event or campaign milestone.
Inputs remain byte-identical; all writes stay under the supplied evidence root.
"""
from pathlib import Path
import argparse, csv, hashlib, importlib.util, json, os, shutil, subprocess

ROOT = Path(__file__).resolve().parents[2]
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('exe', 'reference', 'rom', 'fixture', 'runtime', 'cc', 'out', 'evidence-root'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--feature-env', choices=('SNESRECOMP_EXPERIMENTAL_JOURNAL_POSSESSION',
        'SNESRECOMP_FOUNDATION_JOURNAL_POSSESSION'), default='SNESRECOMP_EXPERIMENTAL_JOURNAL_POSSESSION')
    a = p.parse_args()
    a.exe = a.exe.resolve(strict=True); a.reference = a.reference.resolve(strict=True)
    a.fixture = a.fixture.resolve(strict=True); a.rom = a.rom.resolve(strict=True)
    evidence = a.evidence_root.resolve(strict=True); out = a.out.resolve()
    if not out.is_relative_to(evidence) or out == evidence or out.exists():
        raise ValueError('Choose a new output subdirectory of the explicit evidence root.')
    if sha(a.rom) != '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600':
        raise ValueError('Unsupported ROM.')
    protected = {path: sha(path) for path in (a.rom, a.fixture, a.exe, a.reference)}
    spec = importlib.util.spec_from_file_location('stage_checkpoint', ROOT/'tools/stage_foundation_checkpoint.py')
    staging = importlib.util.module_from_spec(spec); spec.loader.exec_module(staging)
    original = a.fixture.read_bytes(); offset = staging.wram_offset(original); ram = original[offset:offset+0x20000]
    if ram[0x20] != 1:
        raise ValueError('This journal-card proof requires a normal field-mode fixture; battle/menu states do not open the card.')
    if ram[0x5373:0x53b3] != b'\xff'*64 or ram[0x4ba:0x4bc] != bytes((0, 0x20)):
        raise ValueError('This focused proof requires two empty inventories and their original empty cursors.')
    out.mkdir(); (out/'staged').mkdir(); (out/'runs').mkdir()
    checks = {}; cases = {}; stage_receipts = {}
    def check(name, value):
        checks[name] = bool(value)
        if not value:
            (out/'failure.json').write_text(json.dumps({'passed':False,'failed_check':name,'checks':checks,'cases':cases},indent=2)+'\n')
            raise AssertionError(name)
    unit = out/'possession-unit.exe'
    compiled = subprocess.run([str(a.cc), str(ROOT/'experiments/journal/check_possession.c'), '-I',
        str(a.runtime/'runner/src/desktop'), '-o', str(unit)], capture_output=True, text=True)
    (out/'unit-build.log').write_text(compiled.stdout+compiled.stderr)
    check('same_inline_predicate_compiles', compiled.returncode == 0)
    tested = subprocess.run([str(unit)], capture_output=True, text=True, check=True)
    unit_report = json.loads(tested.stdout); (out/'unit-report.json').write_text(json.dumps(unit_report, indent=2)+'\n')
    check('pure_predicate_all64slots_bounds_readonly_removal', unit_report['passed'] and unit_report['checks'] == 199)
    def staged(name, source, edits):
        receipt = staging.stage(source, out/'staged'/name, edits,
            'Explicit manufactured inventory fixture for mutable possession; not original acquisition/completion.', evidence)
        stage_receipts[name] = receipt
        return Path(receipt['checkpoint'])
    first = staged('first-group', a.fixture, ['5373=ff:40', '04ba=00:01'])
    second = staged('second-group', a.fixture, ['5393=ff:40', '04bb=20:21'])
    both = staged('both-groups', first, ['5393=ff:40', '04bb=20:21'])
    absent = staged('removed-fixture', both, ['5373=40:ff', '5393=40:ff', '04ba=01:00', '04bb=21:20'])
    shifted = staged('two-first-items', a.fixture, ['5373=ffff:0140', '04ba=00:02'])
    compacted = staged('compacted-fixture', shifted, ['5373=0140:40ff', '04ba=02:01'])
    no_lead = staged('held-without-david-bit', first, [f'5360={ram[0x5360]:02x}:{ram[0x5360]&~0x40:02x}'])
    later = staged('held-other-stage', first, [f'5372={ram[0x5372]:02x}:01'])
    fixtures = {'absent':(a.fixture,0), 'first':(first,1), 'second':(second,2), 'both':(both,3),
        'removed':(absent,0), 'shifted':(shifted,1), 'compacted':(compacted,1), 'without-lead':(no_lead,1), 'other-stage':(later,1)}
    config = ('[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
        '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
        '[KeyMap]\nJournal=J\nTurbo=None\nMovementBoost=None\nBattleInfo=None\nReset=Ctrl+R\n'
        '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nJournal=L3\n'
        'Controls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
        '[Controller]\nSourceP1=2\nSourceP2=0\n')
    def run(name, state, exe=a.exe, possession=1, method='keyboard', capture=60, load=None, reset=False):
        directory = out/'runs'/name; directory.mkdir(); (directory/'dump').mkdir()
        shutil.copy2(exe, directory/'game.exe'); shutil.copy2(state, directory/'resume.state')
        (directory/'config.ini').write_text(config.replace('Journal=J\n','Journal=I\n') if method == 'pad' else config)
        (directory/'foundation.ini').write_text('Journal=1\nEnhancedPixels=0\nBattleInfo=0\nFastMenus=1\n')
        (directory/'input.txt').write_text('wait 60\ndump shown\nwait 90\ndump hidden\n'+('wait 30\ndump reset\n' if reset else '')+'quit\n')
        env = {k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',
            SNESRECOMP_DUMP_DIR=str(directory/'dump'), SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST=method,
            SNESRECOMP_FOUNDATION_JOURNAL_TRACE=str(directory/'journal.csv'),
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(directory/'present.bgrx'), SNESRECOMP_FOUNDATION_CAPTURE_AT=str(capture))
        env[a.feature_env] = str(possession)
        if method == 'pad':
            # This already-qualified hook gives its virtual device an explicit
            # player index when a physical controller is also connected.
            env.update(SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST='none',
                SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST='pad', SNESRECOMP_FOUNDATION_HOTKEY_OVERLAY_TEST='journal')
        if load is not None:
            (directory/'saves').mkdir(); shutil.copy2(load, directory/'saves/save0.sav')
            env['SNESRECOMP_OVERLAY_SELFTEST_LOADAT'] = '80'
        if reset:
            env.update(SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST='keyboard', SNESRECOMP_FOUNDATION_HOTKEY_SAFETY_TEST='reset')
        with (directory/'host.log').open('w') as log:
            result = subprocess.run([str(directory/'game.exe'), '--no-launcher', '--rom', str(a.rom),
                '--resume-state', str(directory/'resume.state'), '--script', str(directory/'input.txt')], cwd=directory,
                env=env, stdout=log, stderr=log, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        rows = list(csv.DictReader((directory/'journal.csv').open())); text = (directory/'host.log').read_text(errors='replace')
        check(name+'_native_resume', result.returncode == 0 and 'resume state loaded:' in text and not (directory/'resume.state').exists())
        cases[name] = {'exit':result.returncode, 'source_checkpoint_sha256':sha(state), 'method':method,
            'shown':text.count('journal shown'), 'hidden':text.count('journal hidden'),
            'inventory_groups':sorted({int(r['inventory_groups']) for r in rows}) if 'inventory_groups' in rows[0] else None,
            'virtual_pad_attached':'virtual pad attached' in text}
        return directory, rows
    def parity(left, right, prefixes=('shown','hidden')):
        return all((left/'dump'/(prefix+'.'+extension)).read_bytes() == (right/'dump'/(prefix+'.'+extension)).read_bytes()
            for prefix in prefixes for extension in EXTENSIONS)
    def surface(left, right): return (left/'present.bgrx').read_bytes() == (right/'present.bgrx').read_bytes()
    results = {}
    for name, (state, expected) in fixtures.items():
        reference, _ = run(name+'-reference', state, exe=a.reference, possession=0)
        off, _ = run(name+'-off', state, possession=0)
        on, rows = run(name+'-on', state)
        check(name+'_six_guest_captures_unchanged', parity(reference,off) and parity(off,on))
        check(name+'_feature_off_preserves_canonical_host_card', surface(reference,off))
        check(name+'_current_inventory_derived_first_frame', int(rows[0]['inventory_groups']) == expected and cases[name+'-on']['inventory_groups'] == [expected])
        check(name+'_keyboard_once_per_press', cases[name+'-on']['shown'] == cases[name+'-on']['hidden'] == 1)
        check(name+'_host_card_changes_only_when_item_present', surface(off,on) == (expected == 0))
        original_picture = (off/'present.bgrx').read_bytes(); composed = (on/'present.bgrx').read_bytes()
        # Positive cards shorten the inherited overflowing title. Require their
        # outside pixels to match the exact original guest framebuffer, rather
        # than reproducing the old title's out-of-box glyphs. Absence keeps the
        # original off/on card byte-for-byte.
        if expected: original_picture = (on/'dump/shown.fb.bgrx').read_bytes()
        check(name+'_host_card_stays_within_existing_rectangle', len(original_picture) == len(composed) == 256*224*4 and all(
            original_picture[(y*256+x)*4:(y*256+x+1)*4] == composed[(y*256+x)*4:(y*256+x+1)*4]
            for y in range(224) for x in range(256) if not (8<=x<248 and 6<=y<81)))
        results[name] = on
    check('removal_returns_exact_absent_card', surface(results['absent'],results['removed']))
    check('compaction_does_not_change_current_possession_card', surface(results['first'],results['shifted']) and surface(results['first'],results['compacted']))
    pad, _ = run('both-pad', both, method='pad')
    check('virtual_controller_actual_journal_toggle', cases['both-pad']['virtual_pad_attached'] and cases['both-pad']['shown'] == cases['both-pad']['hidden'] == 1)
    check('keyboard_controller_same_guest_and_card', parity(results['both'],pad) and surface(results['both'],pad))
    rollback_off, _ = run('restore-absent-off', both, possession=0, capture=100, load=absent)
    rollback_on, rows = run('restore-absent-on', both, capture=100, load=absent)
    check('in_process_restore_removal_has_no_stale_possession', int(rows[0]['inventory_groups']) == 3 and all(int(r['inventory_groups']) == 0 for r in rows if int(r['frame']) >= 81))
    check('in_process_restore_guest_parity', parity(rollback_off,rollback_on))
    check('in_process_restore_closes_and_next_press_reopens', cases['restore-absent-on']['shown'] == 2 and cases['restore-absent-on']['hidden'] == 0 and
        any(81<=int(r['frame'])<=89 and int(r['visible']) == 0 for r in rows) and '[overlay_selftest] load issued' in (rollback_on/'host.log').read_text())
    check('absent_after_restore_host_card_has_no_possession_overlay', surface(rollback_off,rollback_on))
    restored, _ = run('cold-removed-replay', absent)
    check('cold_restore_absence_matches_original_absent', parity(results['removed'],restored) and surface(results['removed'],restored))
    reset_off, _ = run('reset-off', both, possession=0, capture=175, reset=True)
    reset_on, rows = run('reset-on', both, capture=175, reset=True)
    check('real_reset_has_no_retained_possession', 'console reset' in (reset_on/'host.log').read_text() and all(int(r['inventory_groups']) == 0 for r in rows if int(r['frame']) >= 165))
    check('real_reset_guest_and_host_picture_unchanged', parity(reset_off,reset_on,('shown','hidden','reset')) and surface(reset_off,reset_on))
    check('input_rom_binaries_original_fixture_unchanged', all(sha(path) == digest for path,digest in protected.items()))
    from PIL import Image, ImageDraw
    contact = Image.new('RGB',(256*3,244*2),'#080e1c'); draw = ImageDraw.Draw(contact)
    for i,name in enumerate(('absent','first','second','both','without-lead','removed')):
        image = Image.frombytes('RGB',(256,224),(results[name]/'present.bgrx').read_bytes(),'raw','BGRX')
        image.save(results[name]/'present.png'); x,y=(i%3)*256,(i//3)*244; contact.paste(image,(x,y+20)); draw.text((x+4,y+4),name,fill='white')
    contact.save(out/'journal-possession-cards.png')
    report = {'passed':all(checks.values()), 'executable_sha256':sha(a.exe), 'reference_sha256':sha(a.reference), 'checks':checks,
        'cases':cases, 'staging':stage_receipts, 'pure_predicate':unit_report,
        'limits':['Staged developer inventories; no original acquisition/consumption event observed',
            'Current mutable possession only; no completed quest or historical journal',
            'Keyboard and SDL virtual-controller input; no new physical controller certification',
            'Software/headless host composition; paced GPU/audio qualification remains separate',
            'No canonical source, installed binary, ROM or owner profile writes']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'passed':report['passed'],'checks':len(checks),'output':str(out)},indent=2))

if __name__ == '__main__': main()
