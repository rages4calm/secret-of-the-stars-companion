"""Finite actual-modal input/parity and separately paced audio checks."""
from pathlib import Path
import argparse, array, csv, hashlib, json, os, re, shutil, subprocess, time

EXT = ('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--mode', choices=('forensic','paced'), required=True)
    ap.add_argument('--exe', type=Path, required=True)
    ap.add_argument('--rom', type=Path, required=True)
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--profile', type=Path, required=True)
    args = ap.parse_args()
    exe, state, rom, profile = (p.resolve() for p in (args.exe,args.state,args.rom,args.profile))
    for source in (exe,state,rom,*(profile/n for n in ('config.ini','foundation.ini','keybinds.ini'))):
        if not source.is_file(): ap.error(f'Missing explicit input: {source}')
    if rom.stat().st_size != 1572864 or sha(rom) != '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600':
        ap.error('Expected the clean, unheadered USA ROM; no input has been changed.')
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    report = {'mode':args.mode, 'exe_sha256':sha(exe), 'state_sha256':sha(state),
              'rom_sha256':sha(rom), 'cases':{}, 'checks':{},
              'limits':'Actual SDL virtual-device modal pumps; finite fixture only. No physical-controller, listening, restore-commit or campaign claim.'}
    for name, exit_mode in [('control',None),('pad-cancel','pad'),('escape','escape'),('toggle','toggle')]:
        d=out/name; d.mkdir(); (d/'dump').mkdir()
        shutil.copy2(exe,d/'game.exe'); shutil.copy2(state,d/'resume.state')
        for n in ('config.ini','foundation.ini','keybinds.ini'): shutil.copy2(profile/n,d/n)
        config=(d/'config.ini').read_text()
        config=re.sub(r'(?m)^Fullscreen\s*=.*$', 'Fullscreen=0',config)
        # These self-test shortcuts are private controls, not player bindings.
        config=re.sub(r'(?m)^SaveStateMenu=.*$', 'SaveStateMenu=F7',config)
        config=re.sub(r'(?m)^Rewind=.*$', 'Rewind=F8',config)
        if args.mode=='forensic':
            config=re.sub(r'(?m)^Renderer=.*$', 'Renderer=software',config)
            config=re.sub(r'(?m)^VSync=.*$', 'VSync=0',config)
            config=re.sub(r'(?m)^EnableAudio\s*=.*$', 'EnableAudio=0',config)
            config=re.sub(r'(?m)^DisableFrameDelay=.*$', 'DisableFrameDelay=1',config)
        else:
            config=re.sub(r'(?m)^Renderer=.*$', 'Renderer=direct3d11',config)
            config=re.sub(r'(?m)^VSync=.*$', 'VSync=1',config)
            config=re.sub(r'(?m)^EnableAudio\s*=.*$', 'EnableAudio=1',config)
        (d/'config.ini').write_text(config)
        script='wait 175\ndump before\nwait 140\ndump after\nwait 285\ndump end\nquit\n'
        if args.mode=='paced': script='wait 600\nquit\n'
        (d/'input.txt').write_text(script)
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',SNESRECOMP_FOUNDATION_WIDE='1',
                   SNESRECOMP_FOUNDATION_WIDE_ACTORS='1',SNESRECOMP_FOUNDATION_MAP='0',
                   SNESRECOMP_FOUNDATION_JOURNAL='0')
        if exit_mode:
            env['SNESRECOMP_OVERLAY_SELFTEST_PAD']='180'
            env['SNESRECOMP_OVERLAY_SELFTEST_EXIT']=exit_mode
        if args.mode=='forensic':
            env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',
                       SNESRECOMP_DUMP_DIR=str(d/'dump'),SNESRECOMP_FOUNDATION_CPU_TRACE=str(d/'cpu.csv'))
        else:
            env.update(SNESRECOMP_HOST_PROFILE='1',SNESRECOMP_HOST_PROFILE_START_FRAME='20',
                       SNESRECOMP_AUDIO_STATS=str(d/'audio.stats'),SNESRECOMP_AUDIO_OUTPUT_RAW=str(d/'output.pcm'))
        with (d/'host.log').open('w') as log:
            started=time.perf_counter()
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(rom),
                '--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],
                cwd=d,env=env,stdout=log,stderr=log,timeout=35,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(d/'host.log').read_text(errors='replace')
        checks={'exit_zero':result.returncode==0,'explicit_resume':'resume state loaded:' in log}
        if exit_mode:
            checks.update(actual_virtual_pad='virtual gamepad attached' in log,
                browser_and_rewind_open_closed='ok: browser and rewind both opened and closed from the pad' in log,
                no_modal_timeout='[overlay_selftest_pad] FAIL' not in log)
        case={'seconds':time.perf_counter()-started,'checks':checks}
        if args.mode=='paced':
            lines=(d/'audio.stats').read_text().splitlines();keys=lines[0].lstrip('# ').split()
            rows=[dict(zip(keys,map(int,l.split()))) for l in lines[1:] if not l.startswith('#')]
            steady=rows[2:]
            deltas={k:steady[-1][k]-steady[0][k] for k in ('underflows','missing_frames','dropped_audible')} if len(steady)>=3 else {}
            pcm=array.array('h');pcm.frombytes((d/'output.pcm').read_bytes())
            first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
            checks.update(actual_gpu_vsync='Renderer: direct3d11 (vsync=1 ' in log,
                steady_samples=len(steady)>=3,callback_audio=first is not None and first<.5,
                no_steady_underflows=deltas.get('underflows')==0,
                no_steady_missing=deltas.get('missing_frames')==0,
                no_steady_audible_drops=deltas.get('dropped_audible')==0)
            case.update(audio_stats=rows,steady_audio_deltas=deltas,first_audio_seconds=first)
        case['passed']=all(checks.values());report['cases'][name]=case
    if args.mode=='forensic':
        for name in ('pad-cancel','escape','toggle'):
            pairs={f'{tag}.{ext}':(out/'control/dump'/f'{tag}.{ext}').read_bytes()==(out/name/'dump'/f'{tag}.{ext}').read_bytes()
                   for tag in ('before','after','end') for ext in EXT}
            report['cases'][name]['guest_comparisons']=pairs
            report['checks'][name+'_guest_equal']=all(pairs.values())
            report['checks'][name+'_cpu_trace_equal']=(out/'control/cpu.csv').read_bytes()==(out/name/'cpu.csv').read_bytes()
    report['passed']=all(report['checks'].values()) and all(c['passed'] for c in report['cases'].values())
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':report['checks'],'cases':{n:c['checks'] for n,c in report['cases'].items()}},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
