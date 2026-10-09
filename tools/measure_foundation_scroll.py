"""Measure real Windows pacing and guest camera cadence on copied town fixtures."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,default=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe')
    parser.add_argument('--broken-exe',type=Path,required=True)
    parser.add_argument('--renderer',default='software')
    parser.add_argument('--fullscreen',action='store_true')
    parser.add_argument('--walk-only',action='store_true')
    args=parser.parse_args()
    base=ROOT/'local/runs'/('scroll-pacing-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir(exist_ok=False)
    report={'executable_sha256':hashlib.sha256(args.exe.read_bytes()).hexdigest(),'requested_renderer':args.renderer,'fullscreen':args.fullscreen,'cases':{}}
    walk='wait 60\npress left 90\nwait 30\npress right 160\nwait 30\npress down 60\nwait 30\ndump end\nquit\n'
    menu=(ROOT/'local/menu-status-repro.txt').read_text()
    cases=[('walk-original',args.exe,0,0,True,ROOT/'local/runs/likado-east-a/saves/save0.sav',walk),
           ('walk-enhanced',args.exe,1,1,True,ROOT/'local/runs/likado-east-a/saves/save0.sav',walk),
           ('menu-original',args.exe,0,0,False,ROOT/'local/runs/likado-inside-a/saves/save0.sav',menu),
           ('menu-fixed',args.exe,0,1,False,ROOT/'local/runs/likado-inside-a/saves/save0.sav',menu),
           ('menu-broken',args.broken_exe,0,1,False,ROOT/'local/runs/likado-inside-a/saves/save0.sav',menu)]
    if args.walk_only: cases=cases[:2]
    for name,exe,enhanced,fast,windows,state,script in cases:
        run=base/name;run.mkdir();(run/'dump').mkdir();shutil.copy2(exe,run/'game.exe');shutil.copy2(state,run/'resume.state')
        (run/'input.txt').write_text(script)
        (run/'config.ini').write_text('[Graphics]\nRenderer='+args.renderer+'\nWindowScale=4\nVSync=1\nFullscreen='+str(int(args.fullscreen))+'\n'
            '[Sound]\nEnableAudio='+str(int(windows))+'\nVolume=70\nAudioFreq=32040\nAudioSamples=512\n'
            '[General]\nAutosave=0\nRunAhead=0\nDisableFrameDelay='+str(int(not windows))+'\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_FOUNDATION_FAST_MENUS=str(fast),SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced),
            SNESRECOMP_FOUNDATION_BATTLE_INFO='0',SNESRECOMP_DUMP_DIR=str(run/'dump'),
            SNESRECOMP_FOUNDATION_TRACE=str(run/'foundation.csv'),SNESRECOMP_FRAME_TIMING=str(run/'timing.csv'))
        if not windows:env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_FOUNDATION_VIDEO_RAW=str(run/'video.bgrx'))
        with (run/'host.log').open('w') as log:
            result=subprocess.run([str(run/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                '--resume-state',str(run/'resume.state'),'--script',str(run/'input.txt')],cwd=run,env=env,stdout=log,stderr=log,
                timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode==0
        renderer_lines=[line for line in (run/'host.log').read_text().splitlines() if line.startswith('Renderer:')]
        rows=list(csv.DictReader((run/'timing.csv').open()))[60:]
        times=[float(r['present_seconds']) for r in rows]
        delta=[(b-a)*1000 for a,b in zip(times,times[1:])]
        cpu=[float(r['guest_ms'])+float(r['raster_ms'])+float(r['compose_ms'])+float(r['present_ms']) for r in rows]
        case={'exit':result.returncode,'windows':windows,'renderer_evidence':renderer_lines,'frames_measured':len(rows),
            'processing_ms':{'median':statistics.median(cpu),'p95':sorted(cpu)[int(len(cpu)*.95)],'max':max(cpu)},
            'present_interval_ms':{'median':statistics.median(delta),'p95':sorted(delta)[int(len(delta)*.95)],'max':max(delta)},
            'average_present_fps':(len(times)-1)/(times[-1]-times[0]),'intervals_above_25ms':sum(x>25 for x in delta)}
        trace=list(csv.DictReader((run/'foundation.csv').open()))
        if 'bg1_scroll_x' in trace[0]:
            coords=[(int(r['bg1_scroll_x']),int(r['bg1_scroll_y'])) for r in trace]
            changes=[i for i in range(1,len(coords)) if coords[i]!=coords[i-1]]
            case['camera_changed_frames']=len(changes)
            case['camera_update_gap_counts']={str(gap):sum(b-a==gap for a,b in zip(changes,changes[1:])) for gap in sorted({b-a for a,b in zip(changes,changes[1:])})}
            case['guest_modes']=sorted({int(r['mode']) for r in trace})
        if not windows:
            raw=(run/'video.bgrx').read_bytes();size=256*224*4
            # Static chair/wall area outside the tested status/HP windows.
            crops=[Image.frombytes('RGB',(256,224),raw[i:i+size],'raw','BGRX').crop((184,24,208,56)).tobytes() for i in range(0,len(raw),size)]
            case['static_background_changed_frames']=sum(x!=crops[29] for x in crops[30:])
        report['cases'][name]=case
    report['walk_guest_identical']=all((base/'walk-original/dump'/('end.'+ext)).read_bytes()==(base/'walk-enhanced/dump'/('end.'+ext)).read_bytes()
        for ext in ['wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','fb.bgrx'])
    report['passed']=report['walk_guest_identical'] and all(c['exit']==0 for c in report['cases'].values())
    report['limits']=['Two finite real-Windows walks in one town; not owner hardware latency or campaign profiling',
        'One static background patch during indoor menu transitions; other transient flashes remain possible',
        'Cold-resume first 60 frames excluded; camera cadence is original guest state, not added interpolation']
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
