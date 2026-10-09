"""Verify optional menu-frame configuration on copied Windows GPU/audio runs."""
from pathlib import Path
import argparse,array,hashlib,json,os,re,shutil,subprocess,time
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    args=parser.parse_args()
    owner=ROOT/'local/player-foundation'
    protected={p.relative_to(owner).as_posix():sha(p) for p in list(owner.glob('*'))+list((owner/'saves').glob('*')) if p.is_file()}
    state=ROOT/'local/runs/likado-inside-a/saves/save0.sav';before=sha(state)
    rom=ROOT/'local/inputs/clean-usa.sfc';rom_before=sha(rom)
    base=ROOT/'local/runs'/('hd-desktop-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir()
    report={'executable_sha256':sha(args.exe),'checks':{},'cases':{}}
    for hd in (0,1):
        d=base/f'gpu-{hd}';d.mkdir();(d/'dump').mkdir()
        shutil.copy2(args.exe,d/'game.exe');shutil.copy2(state,d/'resume.state')
        for name in ('config.ini','keybinds.ini','foundation.ini'):shutil.copy2(owner/name,d/name)
        text=(d/'foundation.ini').read_text()
        text=re.sub(r'(?m)^\s*HdMenuFrames\s*=.*$', '',text)
        (d/'foundation.ini').write_text(text+f'\nHdMenuFrames={hd}\n')
        (d/'input.txt').write_text('wait 30\npress b 1\nwait 100\ndump menu\nquit\n')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_HOST_PROFILE='1',SNESRECOMP_FOUNDATION_WIDE='0',
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',
            SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',SNESRECOMP_AUDIO_OUTPUT_RAW=str(d/'audio.pcm'),
            SNESRECOMP_DUMP_DIR=str(d/'dump'),SNESRECOMP_FOUNDATION_HD_UI_TRACE=str(d/'hd.csv'),
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(d/'present.bgrx'),SNESRECOMP_FOUNDATION_CAPTURE_AT='120')
        with (d/'host.log').open('w') as log:
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(rom),
                '--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,
                stdout=log,stderr=log,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(d/'host.log').read_text(errors='replace')
        w,h=map(int,re.search(r'composed capture (\d+)x(\d+)',log).groups())
        raw=(d/'present.bgrx').read_bytes()
        assert len(raw)==w*h*4
        Image.frombytes('RGB',(w,h),raw,'raw','BGRX').save(d/'present.png')
        pcm=array.array('h');pcm.frombytes((d/'audio.pcm').read_bytes())
        first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
        rows=(d/'hd.csv').read_text().splitlines() if (d/'hd.csv').exists() else []
        count=max((int(row.split(',')[1]) for row in rows),default=0)
        checks={'exit_zero':result.returncode==0,'resume_consumed':not(d/'resume.state').exists(),
            'real_gpu_vsync':'Renderer: direct3d11 (vsync=1 ' in log,
            'configuration_route':f'hd_menu_frames={hd} ' in log,
            'expected_surface':(w,h)==((1024,896) if hd else (512,448)),
            'expected_binding':count>0 if hd else count==0,
            'audio_nonzero_early':first is not None and first<.5}
        report['cases'][f'gpu-{hd}']={'checks':checks,'first_audio_seconds':first,
            'max_bound_base_pixels':count,'passed':all(checks.values())}
    report['checks']['all_guest_menu_dumps_identical']=all((base/'gpu-0/dump'/('menu.'+ext)).read_bytes()==
        (base/'gpu-1/dump'/('menu.'+ext)).read_bytes() for ext in ('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx'))
    off=Image.open(base/'gpu-0/present.png').resize((1024,896),Image.Resampling.NEAREST)
    on=Image.open(base/'gpu-1/present.png')
    report['checks']['authored_art_changes_gpu_surface']=not np.array_equal(np.asarray(off),np.asarray(on))
    report['checks']['owner_files_unchanged']=all(sha(owner/n)==v for n,v in protected.items())
    report['checks']['input_state_and_rom_unchanged']=sha(state)==before and sha(rom)==rom_before
    report['limits']=['Copied house main menu on owner display/input preferences and configuration-selected art; no owner progress advanced',
        'Actual GPU surface and SDL callback PCM, not listening/physical-controller/monitor scanout or campaign certification']
    report['passed']=all(report['checks'].values()) and all(c['passed'] for c in report['cases'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
