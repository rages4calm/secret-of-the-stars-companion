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
    ap.add_argument('--restore-state', type=Path, help='Optional copied partial-loader checkpoint for actual browser load')
    args = ap.parse_args()
    exe, state, rom, profile = (p.resolve() for p in (args.exe,args.state,args.rom,args.profile))
    for source in (exe,state,rom,*(profile/n for n in ('config.ini','foundation.ini','keybinds.ini'))):
        if not source.is_file(): ap.error(f'Missing explicit input: {source}')
    if rom.stat().st_size != 1572864 or sha(rom) != '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600':
        ap.error('Expected the clean, unheadered USA ROM; no input has been changed.')
    restore = args.restore_state.resolve() if args.restore_state else None
    if restore and (not restore.is_file() or restore.is_symlink()): ap.error('Invalid restore checkpoint')
    guarded = (exe,state,rom,*(profile/n for n in ('config.ini','foundation.ini','keybinds.ini')),
               *((restore,) if restore else ()))
    if any(p.is_symlink() for p in guarded): ap.error('Linked input refused')
    protected = {str(p):sha(p) for p in guarded}
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    report = {'mode':args.mode, 'exe_sha256':sha(exe), 'state_sha256':sha(state),
              'rom_sha256':sha(rom), 'cases':{}, 'checks':{},
              'limits':'Actual SDL virtual-device modal pumps; finite fixture only. No physical-controller, listening, rewind-commit or campaign claim; optional restore is an actual original browser load of an explicitly copied partial-loader fixture.'}
    cases=[('control',None,None),('pad-cancel','pad','pad'),('escape','escape','pad'),('toggle','toggle','pad'),
           ('key-cancel','pad','keyboard'),('key-escape','escape','keyboard'),('key-toggle','toggle','keyboard')]
    if restore:
        cases.extend([('restore-control','restore','keyboard'),('key-restore','restore','keyboard')])
        report['restore_state_sha256']=sha(restore)
    for name, exit_mode, opener in cases:
        d=out/name; d.mkdir(); (d/'dump').mkdir()
        shutil.copy2(exe,d/'game.exe'); shutil.copy2(state,d/'resume.state')
        if exit_mode=='restore':
            (d/'saves').mkdir(); shutil.copy2(restore,d/'saves/save0.sav')
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
                   SNESRECOMP_FOUNDATION_JOURNAL='0',SNESRECOMP_AUDIO_RESUME_TRACE='1',
                   SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',SNESRECOMP_FOUNDATION_GENERATED_CLEAR='1',
                   SNESRECOMP_FOUNDATION_GENERATED_ROUTINE='1')
        if exit_mode:
            env['SNESRECOMP_OVERLAY_SELFTEST_PAD']='180'
            env['SNESRECOMP_OVERLAY_SELFTEST_EXIT']=exit_mode
            if opener=='keyboard': env['SNESRECOMP_OVERLAY_SELFTEST_OPEN']='keyboard'
            if name=='restore-control': env['SNESRECOMP_OVERLAY_SELFTEST_BROWSER_ONLY']='1'
        if args.mode=='forensic':
            env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',
                       SNESRECOMP_DUMP_DIR=str(d/'dump'),SNESRECOMP_FOUNDATION_CPU_TRACE=str(d/'cpu.csv'),
                       SNESRECOMP_FOUNDATION_ROUTINE_TRACE=str(d/'routine.csv'))
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
                browser_and_rewind_open_closed=('ok: browser opened and closed from the pad' if name=='restore-control'
                    else 'ok: browser and rewind both opened and closed from the pad') in log,
                no_modal_timeout='[overlay_selftest_pad] FAIL' not in log)
            browser_open=len(re.findall(r'save-state browser OPEN -',log))
            browser_close=len(re.findall(r'save-state browser CLOSED after',log))
            rewind_open=len(re.findall(r'rewind filmstrip OPEN -',log))
            rewind_close=len(re.findall(r'rewind filmstrip CLOSED after',log))
            checks.update(browser_open_once=browser_open==1,browser_close_once=browser_close==1,
                          rewind_open_once=rewind_open==(0 if name=='restore-control' else 1),
                          rewind_close_once=rewind_close==(0 if name=='restore-control' else 1))
            if opener=='keyboard':
                checks['queued_keyboard_browser']='[overlay_selftest_keyboard] queued browser opener and repeat' in log
                if name!='restore-control':
                    checks['queued_keyboard_rewind']='[overlay_selftest_keyboard] queued rewind opener and repeat' in log
                checks['repeat_did_not_close_rewind']=name=='restore-control' or bool(re.search(
                    r'rewind filmstrip CLOSED after (?:1[5-9]|[2-9][0-9]) pumps',log))
            if exit_mode=='restore':
                checks['actual_browser_load_requested']='[overlay_selftest_restore] original browser load requested' in log
                checks['copied_slot_not_rewritten']=sha(d/'saves/save0.sav')==sha(restore)
        ready=[(source,int(available),int(prefill)) for source,available,prefill in re.findall(
            r'\[host_audio_resume\] ready source=(producer|frame) available=(\d+) prefill=(\d+)',log)]
        checks['resume_requires_real_prefill']=all(available>=prefill==2136 for _,available,prefill in ready)
        if args.mode=='paced':
            deferred=len(re.findall(r'\[host_audio_resume\] deferred available=',log))
            checks['deferred_resume_reached_prefill']=len(ready)>=deferred
            if exit_mode=='restore':
                post_browser=log.split('save-state browser CLOSED after',1)[-1].split('rewind filmstrip OPEN -',1)[0]
                post_ready=[(source,int(available),int(prefill)) for source,available,prefill in re.findall(
                    r'\[host_audio_resume\] ready source=(producer|frame) available=(\d+) prefill=(\d+)',post_browser)]
                checks['long_loader_resumes_from_producer_after_browser_close']=any(
                    source=='producer' and available>=prefill==2136 for source,available,prefill in post_ready)
        summary=re.search(r'\[foundation_generated_routine\] generated_instructions=(\d+)([^\n]*)',log)
        generated=int(summary[1]) if summary else None
        pcs={pc:int(count) for pc,count in re.findall(r'pc([0-9a-f]{6})=(\d+)',summary[2])} if summary else {}
        hand=re.search(r'\[foundation_clear\] native_instructions=(\d+)',log)
        checks['actual_generated_summary']=summary is not None
        checks['zero_handwritten_steps']=hand is not None and int(hand[1])==0
        if exit_mode=='restore':
            # An ordinary standing fixture never executes this island. The
            # copied partial checkpoint must actually reach the guarded clear
            # body and its generated original RTS, not merely request a load.
            checks['actual_partial_loader_executed']=generated is not None and generated>0
            checks['generated_original_rts_once']=pcs.get('01cb34')==1
            checks['partial_checkpoint_not_full_fresh_call']=pcs.get('01c45e')==0
            if args.mode=='forensic':
                instructions=list(csv.DictReader((d/'routine.csv').open()))
                rts=[row for row in instructions if int(row['pc'])==0x01cb34 and int(row['context'])==1]
                returns=[row for row in instructions if int(row['pc'])==0x01c461]
                checks['original_rts_guest_stack_and_return']=len(rts)==1 and len(returns)==1 and (
                    int(rts[0]['y'])==0 and int(rts[0]['vram'])==0x6000 and
                    int(rts[0]['stack_lo']) | int(rts[0]['stack_hi'])<<8)==0xc460 and (
                    int(returns[0]['s'])==int(rts[0]['s'])+2 and int(returns[0]['pb'])==1)
        else:
            checks['ordinary_fixture_has_no_generated_clear']=generated==0
        case={'seconds':time.perf_counter()-started,'checks':checks,'resume_ready':ready,
              'generated_instructions':generated,'generated_pc_counts':pcs}
        if args.mode=='paced' and exit_mode=='restore':case['post_browser_resume_ready']=post_ready


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
        for name in ('pad-cancel','escape','toggle','key-cancel','key-escape','key-toggle'):
            pairs={f'{tag}.{ext}':(out/'control/dump'/f'{tag}.{ext}').read_bytes()==(out/name/'dump'/f'{tag}.{ext}').read_bytes()
                   for tag in ('before','after','end') for ext in EXT}
            report['cases'][name]['guest_comparisons']=pairs
            report['checks'][name+'_guest_equal']=all(pairs.values())
            report['checks'][name+'_cpu_trace_equal']=(out/'control/cpu.csv').read_bytes()==(out/name/'cpu.csv').read_bytes()
        if restore:
            pairs={f'{tag}.{ext}':(out/'restore-control/dump'/f'{tag}.{ext}').read_bytes()==(out/'key-restore/dump'/f'{tag}.{ext}').read_bytes()
                   for tag in ('before','after','end') for ext in EXT}
            report['cases']['key-restore']['guest_comparisons']=pairs
            report['checks']['restored_guest_equal']=all(pairs.values())
            report['checks']['restored_cpu_trace_equal']=(out/'restore-control/cpu.csv').read_bytes()==(out/'key-restore/cpu.csv').read_bytes()
    report['checks']['inputs_byte_preserved']=all(p.is_file() and sha(p)==protected[str(p)] for p in guarded)
    report['passed']=all(report['checks'].values()) and all(c['passed'] for c in report['cases'].values())
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':report['checks'],'cases':{n:c['checks'] for n,c in report['cases'].items()}},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
