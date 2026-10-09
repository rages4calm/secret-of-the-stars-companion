"""Finite copied-profile OpenGL playback with actual renderer breadcrumbs.

Counter-based Windows qualification; no synchronous forensic capture or owner
save writes. Requested VSync and actual OpenGL initialization are checked,
but driver swap-interval implementation is not inferred from frame rate.
"""
from pathlib import Path
import argparse,array,hashlib,json,os,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def owner_files():
    base=ROOT/'local/player-foundation'
    return {p.relative_to(base).as_posix():sha(p) for p in list(base.iterdir())+list((base/'saves').rglob('*')) if p.is_file()}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--out',type=Path)
    args=parser.parse_args();before=owner_files();exe=args.exe.resolve();initial=sha(exe)
    base=(args.out or ROOT/'local/runs'/('opengl-audio-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    assert base.is_relative_to((ROOT/'local').resolve()) and not base.exists();base.mkdir()
    frozen=base/'candidate.exe';shutil.copy2(exe,frozen);owner=ROOT/'local/player-foundation'
    cases={}
    for name,fixture,hd,wide,commands in [
        ('standard-menu','likado-inside-a',0,0,'wait 30\npress b 1\nwait 180\npress b 1\nwait 220\nquit\n'),
        ('enhanced-wide','likado-east-a',0,1,'wait 30\npress left 90\nwait 90\npress right 90\nwait 130\nquit\n'),
        ('optional-frames','likado-inside-a',1,0,'wait 30\npress b 1\nwait 400\nquit\n')]:
        d=base/name;d.mkdir();state=ROOT/'local/runs'/fixture/'saves/save0.sav';state_hash=sha(state)
        shutil.copy2(state,d/'resume.state');shutil.copy2(frozen,d/'game.exe')
        for n in ('config.ini','foundation.ini','keybinds.ini'):shutil.copy2(owner/n,d/n)
        config=(d/'config.ini').read_text()
        for key,value in [('Renderer','opengl'),('VSync','1'),('NewRenderer',str(wide)),('Fullscreen','0'),('Autosave','0')]:
            if key=='Fullscreen':pattern=r'(?m)^\s*Fullscreen\s*=\s*[012]\s*$'
            else:pattern=r'(?m)^\s*'+key+r'\s*=.*$'
            config,count=re.subn(pattern,key+'='+value,config);assert count==1,(key,count)
        (d/'config.ini').write_text(config);(d/'input.txt').write_text(commands)
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_HOST_PROFILE='1',SNESRECOMP_HOST_PROFILE_START_FRAME='20',
          SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',SNESRECOMP_FOUNDATION_HD_MENU_FRAMES=str(hd),
          SNESRECOMP_FOUNDATION_WIDE=str(wide),SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(wide),
          SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',
          SNESRECOMP_AUDIO_STATS=str(d/'audio.stats'),SNESRECOMP_AUDIO_OUTPUT_RAW=str(d/'output.pcm'))
        with (d/'host.log').open('w') as log:r=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),'--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,stdout=log,stderr=log,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        text=(d/'host.log').read_text(errors='replace');boot=json.loads((d/'last_run_report.json').read_text())
        messages=[e['msg'] for e in boot['breadcrumbs']['events']]
        window=re.search(r'video profile window:.*?seconds=([\d.]+) presentations=(\d+)',text)
        fps=int(window[2])/float(window[1]) if window else 0
        lines=(d/'audio.stats').read_text().splitlines();keys=lines[0].lstrip('# ').split();rows=[dict(zip(keys,map(int,line.split()))) for line in lines[1:] if not line.startswith('#')];steady=rows[2:]
        deltas={k:steady[-1][k]-steady[0][k] for k in ('underflows','missing_frames','dropped_audible')} if len(steady)>=3 else {}
        pcm=array.array('h');pcm.frombytes((d/'output.pcm').read_bytes());first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
        checks={'exit_zero':r.returncode==0,'actual_opengl_initialized':'renderer initialized: opengl' in messages,
            'opengl_requested':bool(re.search(r'(?m)^Renderer=opengl$',config)),
            'vsync_requested':bool(re.search(r'(?m)^VSync=1$',config)),
            'callback_pcm_nonzero':first is not None and first<.5,'steady_window':len(steady)>=3,
            'steady_rate':fps>=58.5,'steady_audio':deltas=={'underflows':0,'missing_frames':0,'dropped_audible':0},
            'fixture_preserved':sha(state)==state_hash,'candidate_preserved':sha(exe)==initial}
        if wide:
            actor=re.search(r'\[foundation_wide_actors\] captured=(\d+) packets=(\d+) side_pieces=(\d+) side_pixels=(\d+)',text)
            checks['actual_actor_margins']=bool(actor) and all(int(v)>0 for v in actor.groups())
        cases[name]={'passed':all(checks.values()),'checks':checks,'steady_fps':fps,'steady_audio_counter_deltas':deltas,'first_audio_seconds':first,'renderer_breadcrumbs':[m for m in messages if 'renderer' in m],'fixture_sha256':state_hash}
    report={'passed':all(r['passed'] for r in cases.values()) and before==owner_files(),'executable_sha256':initial,'checker_sha256':sha(Path(__file__)),'cases':cases,'owner_files_unchanged':before==owner_files(),'synchronous_forensic_dumps_enabled':False,'limits':'Three real OpenGL copied routes with requested VSync, renderer initialization and SDL playback counters; no driver swap-interval query, listening, physical-controller or campaign guarantee'}
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(str(base));print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
