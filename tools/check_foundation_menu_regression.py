"""Reproduce clipped submenus and qualify repeated UI transitions on copies."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=EXE)
    parser.add_argument('--broken-exe', type=Path, required=True)
    args = parser.parse_args()
    base = ROOT / 'local/runs' / ('menu-regression-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    script = 'wait 30\n'
    for choice in range(6):
        script += 'press b 1\nwait 40\n' + 'press down 1\nwait 12\n' * choice
        script += f'press a 1\nwait 90\ndump choice{choice}\npress b 1\nwait 40\ndump returned{choice}\npress b 1\nwait 90\ndump field{choice}\n'
    script += 'quit\n'
    report = {'executable_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(),
        'broken_executable_sha256': hashlib.sha256(args.broken_exe.read_bytes()).hexdigest(), 'cases': {}, 'checks': {}}
    states = {'house': ROOT / 'local/runs/likado-inside-a/saves/save0.sav',
              'outdoors': ROOT / 'local/runs/clean-to-outdoors/saves/save0.sav'}
    for scene, state in states.items():
        for kind, executable, enabled in [('original', args.exe, 0), ('fixed', args.exe, 1), ('broken', args.broken_exe, 1)]:
            run = base / (scene + '-' + kind)
            run.mkdir(); (run / 'dump').mkdir()
            shutil.copy2(executable, run / 'game.exe');shutil.copy2(state, run / 'resume.state')
            (run / 'input.txt').write_text(script)
            (run / 'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
                '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
                '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
            env = {k: v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                SNESRECOMP_FOUNDATION_FAST_MENUS=str(enabled), SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
                SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0', SNESRECOMP_DUMP_DIR=str(run/'dump'))
            with (run/'host.log').open('w') as log:
                result = subprocess.run([str(run/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                    '--resume-state',str(run/'resume.state'),'--script',str(run/'input.txt')],cwd=run,env=env,
                    stdout=log,stderr=log,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
            assert result.returncode==0
            report['cases'][scene+'-'+kind]={'exit':result.returncode,'source_checkpoint_sha256':hashlib.sha256(state.read_bytes()).hexdigest()}
    for scene in states:
        original, fixed, broken = [base/(scene+'-'+kind)/'dump' for kind in ['original','fixed','broken']]
        differences = {}
        broken_differences = {}
        for tag in [f'{phase}{n}' for phase in ['choice','returned','field'] for n in range(6)]:
            ref=(original/(tag+'.vram.bin')).read_bytes()
            def diff(directory):
                actual=(directory/(tag+'.vram.bin')).read_bytes()
                # Cursor palette blinks can be phase-shifted by shorter outer
                # animations. Normalize only bit 11 of identical tile IDs.
                return sum((struct.unpack_from('<H',actual,i)[0]&~0x0800)!=(struct.unpack_from('<H',ref,i)[0]&~0x0800)
                           for i in range(0xa000,0xb000,2))
            differences[tag]=diff(fixed);broken_differences[tag]=diff(broken)
        report['cases'][scene+'-fixed']['bg3_tilemap_differences']=differences
        report['cases'][scene+'-broken']['bg3_tilemap_differences']=broken_differences
        report['checks'][scene+'_fixed_menu_maps_match_original']=not any(differences.values())
        report['checks'][scene+'_broken_build_reproduces_mismatch']=any(broken_differences.values())
        contact=Image.new('RGB',(3*256,244))
        from PIL import ImageDraw
        draw=ImageDraw.Draw(contact)
        for col,kind in enumerate(['broken','original','fixed']):
            contact.paste(Image.open(base/(scene+'-'+kind)/'dump/choice3.fb.bmp'),(col*256,20))
            draw.text((col*256+4,4),kind,fill='white')
        contact.save(base/(scene+'-status-comparison.png'))
    report['passed']=all(report['checks'].values())
    report['limits']=['Six submenu selections in two single-party scenes; not a campaign/menu certification',
                      'Tilemap comparison normalizes only the cursor palette blink bit']
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
