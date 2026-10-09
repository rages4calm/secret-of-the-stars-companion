"""Verify keyboard H and SDL virtual-pad right-stick HUD toggles independently of guest input."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,default=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe')
    args=parser.parse_args()
    base=ROOT/'local/runs'/('hud-input-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir(exist_ok=False)
    report={'executable_sha256':hashlib.sha256(args.exe.read_bytes()).hexdigest(),'cases':{},'checks':{}}
    for method in ['keyboard','pad']:
        for info in [0,1]:
            run=base/f'{method}-{info}';run.mkdir();(run/'dump').mkdir()
            shutil.copy2(args.exe,run/'game.exe');shutil.copy2(ROOT/'local/runs/world-cave-a/saves/save0.sav',run/'resume.state')
            (run/'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n'
                '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
                '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nControls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
                '[Controller]\nSourceP1=2\nSourceP2=0\n')
            (run/'input.txt').write_text('wait 60\ndump hidden\nwait 90\ndump shown\nquit\n')
            env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(run/'dump'),
                SNESRECOMP_FOUNDATION_HUD_INPUT_TEST=method,SNESRECOMP_FOUNDATION_BATTLE_INFO=str(info),
                SNESRECOMP_FOUNDATION_FAST_MENUS='1',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
                SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(run/'present.bgrx'),SNESRECOMP_FOUNDATION_CAPTURE_AT='60')
            with (run/'host.log').open('w') as log:
                result=subprocess.run([str(run/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                    '--resume-state',str(run/'resume.state'),'--script',str(run/'input.txt')],cwd=run,env=env,stdout=log,stderr=log,
                    timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
            host=(run/'host.log').read_text(errors='replace')
            report['cases'][f'{method}-{info}']={'exit':result.returncode,'hidden_messages':host.count('battle info hidden'),
                'shown_messages':host.count('battle info shown'),'virtual_pad_attached':'virtual pad attached' in host}
        off,on=base/f'{method}-0',base/f'{method}-1'
        c=report['cases'][f'{method}-1']
        report['checks'][method+'_toggles_once_per_press']=c['hidden_messages']==c['shown_messages']==1
        report['checks'][method+'_hidden_surface_matches_original']=(on/'present.bgrx').read_bytes()==(off/'present.bgrx').read_bytes()
        report['checks'][method+'_guest_unchanged']=all((on/'dump'/f'{tag}.{ext}').read_bytes()==(off/'dump'/f'{tag}.{ext}').read_bytes()
            for tag in ['hidden','shown'] for ext in ['wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','fb.bgrx'])
    report['checks']['right_stick_uses_real_sdl_virtual_events']=report['cases']['pad-1']['virtual_pad_attached']
    report['passed']=all(report['checks'].values()) and all(c['exit']==0 for c in report['cases'].values())
    report['limits']=['Native SDL keyboard event path and virtual-device right-stick path; physical owner hardware not newly certified']
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
