"""Reproduce slow composition and qualify paced GPU service/audio after startup."""
from pathlib import Path
import argparse,array,hashlib,json,os,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True);p.add_argument('--reference-exe',type=Path,required=True)
    p.add_argument('--wide-actors',action='store_true',help='Qualify regular actor margin composition in the paced wide case')
    p.add_argument('--candidate-only',action='store_true',help='Test only current playback without reopening the known choppy reference')
    p.add_argument('--expanded-scenes',action='store_true',help='Also qualify paced interior, overworld, forest battle and prepared title scenery')
    p.add_argument('--title-state',type=Path,help='Explicit copied, verified visible-title checkpoint for expanded scene coverage')
    args=p.parse_args()
    owner=ROOT/'local/player-foundation'
    protected={f.relative_to(owner).as_posix():sha(f) for f in list(owner.glob('*'))+list((owner/'saves').rglob('*')) if f.is_file()}
    base=ROOT/'local/runs'/('frame-audio-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir()
    report={'executable_sha256':sha(args.exe),'reference_sha256':sha(args.reference_exe),
        'synchronous_forensic_dumps_enabled':not args.candidate_only,'checks':{},'cases':{}}
    frozen={}
    for name,exe in [('candidate',args.exe),('reference',args.reference_exe)]:
        frozen[name]=base/(name+'.exe');shutil.copy2(exe,frozen[name])
    fixture=ROOT/'local/runs/likado-inside-a/saves/save0.sav'
    town=ROOT/'local/runs/likado-east-a/saves/save0.sav'
    script='wait 30\npress b 1\nwait 100\ndump menu\npress b 1\nwait 300\ndump end\nquit\n'
    cases=[('slow-reference','reference',fixture,1,0,script),
        ('cached-menu','candidate',fixture,1,0,script),
        ('cached-standard','candidate',fixture,0,0,script),
        ('cached-wide','candidate',town,0,1,'wait 30\npress left 90\nwait 60\npress right 90\nwait 160\ndump end\nquit\n')]
    if args.candidate_only:cases=cases[1:]
    if args.expanded_scenes:
        if not args.title_state or not args.title_state.is_file():p.error('--expanded-scenes requires --title-state pointing to a verified visible-title checkpoint')
        extra=[('cached-room-wide',fixture,1),
            ('cached-world-wide',ROOT/'local/runs/likado-loop-exit-a/saves/save0.sav',1),
            ('cached-battle-wide',ROOT/'local/runs/world-cave-a/saves/save0.sav',3),
            ('cached-title-wide',args.title_state.resolve(),2)]
        cases += [(name,'candidate',state,0,1,'wait 540\ndump end\nquit\n') for name,state,kind in extra]
    expected_kinds={name:kind for name,state,kind in extra} if args.expanded_scenes else {}
    for name,kind,state,hd,wide,commands in cases:
        # Full dumps synchronously write multiple guest/PPU files on the game
        # thread. They can exhaust queued audio while no frames are simulated.
        # Pixel/state parity has its own headless checker; paced candidate-only
        # qualification measures playback with those capture stalls removed.
        if args.candidate_only:commands='\n'.join(line for line in commands.splitlines() if not line.startswith('dump '))+'\n'
        d=base/name;d.mkdir();(d/'dump').mkdir()
        shutil.copy2(frozen[kind],d/'game.exe');shutil.copy2(state,d/'resume.state')
        for config in ('config.ini','keybinds.ini','foundation.ini'):shutil.copy2(owner/config,d/config)
        text=(d/'config.ini').read_text();text=re.sub(r'(?m)^Fullscreen=.*$', 'Fullscreen=0',text)
        if wide:text=re.sub(r'(?m)^NewRenderer=.*$', 'NewRenderer=1',text)
        (d/'config.ini').write_text(text)
        (d/'input.txt').write_text(commands)
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_HOST_PROFILE='1',SNESRECOMP_HOST_PROFILE_START_FRAME='20',
            SNESRECOMP_FOUNDATION_HD_MENU_FRAMES=str(hd),SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',
            SNESRECOMP_FOUNDATION_WIDE=str(wide),SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',
            SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(int(args.wide_actors and bool(wide))),
            SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',SNESRECOMP_AUDIO_STATS=str(d/'audio.stats'),
            SNESRECOMP_AUDIO_OUTPUT_RAW=str(d/'output.pcm'))
        if not args.candidate_only:env['SNESRECOMP_DUMP_DIR']=str(d/'dump')
        if name in expected_kinds:env['SNESRECOMP_FOUNDATION_FIELD_TRACE']=str(d/'wide.csv')
        with (d/'host.log').open('w') as log:
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                '--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,
                stdout=log,stderr=log,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(d/'host.log').read_text(errors='replace')
        timings={m.group(1):{'mean_ms':float(m.group(2)),'max_ms':float(m.group(3))} for m in
            re.finditer(r'video profile: stage=(\S+).*?mean_ms=([\d.]+) max_ms=([\d.]+)',log)}
        window=re.search(r'video profile window:.*?seconds=([\d.]+) presentations=(\d+)',log)
        fps=int(window.group(2))/float(window.group(1))
        lines=(d/'audio.stats').read_text().splitlines();keys=lines[0].lstrip('# ').split()
        rows=[dict(zip(keys,map(int,line.split()))) for line in lines[1:] if not line.startswith('#')]
        # Per-second cumulative counters: discard the first two sampled seconds
        # for boot/prefill and require a real later observation window.
        steady=rows[2:]
        deltas={key:steady[-1][key]-steady[0][key] for key in ('underflows','missing_frames','dropped_audible')} if len(steady)>=3 else {}
        pcm=array.array('h');pcm.frombytes((d/'output.pcm').read_bytes())
        first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
        checks={'exit_zero':result.returncode==0,'real_gpu_vsync':'Renderer: direct3d11 (vsync=1 ' in log,
            'explicit_checkpoint_loaded':'resume state loaded:' in log,
            'callback_pcm_nonzero':first is not None and first<.5,'steady_window_present':len(steady)>=3}
        if kind=='candidate':checks.update(steady_presentation_rate=fps>=58.5,
            compose_under_frame_budget=timings['compose']['mean_ms']<10,
            no_steady_audio_underflows=deltas.get('underflows')==0,
            no_steady_missing_frames=deltas.get('missing_frames')==0,
            no_steady_audible_overflow=deltas.get('dropped_audible')==0)
        if name=='cached-wide' and args.wide_actors:
            actor_stats=re.search(r'\[foundation_wide_actors\] captured=(\d+) packets=(\d+) side_pieces=(\d+) side_pixels=(\d+)',log)
            checks['regular_actors_really_presented']=bool(actor_stats) and all(int(v)>0 for v in actor_stats.groups())
        if name in expected_kinds:
            import csv
            wide_rows=list(csv.DictReader((d/'wide.csv').open()))
            checks['expanded_scene_really_drawn']=sum(int(r['accepted_lines']) for r in wide_rows if int(r['kind'])==expected_kinds[name])>224*100
            checks['original_center_has_no_pixel_or_tile_mismatches']=all(int(r['pixel_mismatches'])==int(r['tile_mismatches'])==0 for r in wide_rows)
            if name=='cached-world-wide':checks['actual_world_scene']=any(int(r['scene'])==0 and int(r['kind'])==1 for r in wide_rows)
        report['cases'][name]={'checks':checks,'steady_profile_fps':fps,'timings':timings,
            'audio_stats':rows,'steady_audio_counter_deltas':deltas,'first_audio_seconds':first,
            'passed':all(checks.values())}
    if not args.candidate_only:
        slow,fast=[report['cases'][n] for n in ('slow-reference','cached-menu')]
        report['checks']['reproduces_reference_chop']=slow['steady_profile_fps']<55 and slow['steady_audio_counter_deltas'].get('underflows',0)>0
        report['checks']['cached_composition_improves']=fast['timings']['compose']['mean_ms']<slow['timings']['compose']['mean_ms']/2
        report['checks']['same_menu_and_end_guest_picture']=all((base/'slow-reference/dump'/(tag+'.'+ext)).read_bytes()==
            (base/'cached-menu/dump'/(tag+'.'+ext)).read_bytes() for tag in ('menu','end') for ext in
            ('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx'))
    report['checks']['owner_files_unchanged']=all(sha(owner/n)==v for n,v in protected.items())
    report['limits']=['Actual Windows GPU pacing and SDL output counters after startup on finite copied routes; not a listening or universal system-load guarantee',
        'Cached host memory composition changes no guest CPU budget or logic rate; independent image/guest parity has a separate checker',
        'Candidate-only playback excludes synchronous full forensic dumps; those captures can interrupt the game thread and belong to headless parity tests']
    report['passed']=all(report['checks'].values()) and all(c['passed'] for c in report['cases'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
