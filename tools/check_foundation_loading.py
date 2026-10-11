"""Finite real-native proof of the private generated whole clear call/routine."""
from pathlib import Path
import argparse,collections,csv,hashlib,json,os,re,shutil,struct,subprocess,time,zlib

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
EXT=('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx')
SCRIPT='wait 10\ndump before\npress down 96\ndump door\nwait 17\ndump loading\nwait 2\ndump clear\nwait 102\ndump after\nquit\n'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open(newline='')as stream:return list(csv.DictReader(stream))
def write(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')

def main():
    global ROOT
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-exe',type=Path,required=True)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--legacy-state',type=Path,required=True)
    p.add_argument('--native-proof',action='store_true',help='Retained compatibility flag; this focused checker qualifies generated and diagnostic routes')
    p.add_argument('--workspace-root',type=Path,help='Explicit root for private output/protected-input checks; never affects ROM or EXE choice')
    p.add_argument('--compilation-receipt',type=Path,help='Real immutable public or private source compilation receipt')
    args=p.parse_args()
    if args.workspace_root:ROOT=args.workspace_root.resolve(strict=True)
    output=args.output.resolve();candidate=args.exe.resolve();baseline=args.reference_exe.resolve();BASE_SHA=sha(baseline)
    if not output.is_relative_to(ROOT/'local')or output.exists():raise ValueError('Fresh private output required')
    fixture=args.fixture.resolve(strict=True)
    legacy=args.legacy_state.resolve(strict=True)
    rom=args.rom.resolve(strict=True);assert sha(rom)==ROM_SHA
    receipt=args.compilation_receipt
    if receipt is None:
        receipt=candidate.parent.parent/'source-build-receipt.json'
        if not receipt.is_file():receipt=candidate.parent.parent/'experimental-build-receipt.json'
    receipt=receipt.resolve(strict=True);compiled=json.loads(receipt.read_text())
    assert compiled['status']in('compiled_unqualified','compiled_unqualified_experimental') and compiled['executable_sha256']==sha(candidate)
    assert compiled['public_build']is(compiled['status']=='compiled_unqualified'), 'Compilation receipt kind must remain truthful'
    protected={str(path):sha(path)for path in [candidate,baseline,receipt,fixture,legacy,rom,Path(__file__)]}
    for directory in [ROOT/'local/player-foundation',ROOT/'local/companion',ROOT/'native/foundation',ROOT/'github-repo/native/foundation']:
        for path in directory.rglob('*'):
            if path.is_file():protected[str(path)]=sha(path)
    for path in [ROOT/'local/evidence/build-receipt.json',ROOT/'local/evidence/companion-receipt.json']:
        if path.exists():protected[str(path)]=sha(path)
    output.mkdir();write(output/'protected-before.json',protected)
    report={'passed':False,'checks':{},'cases':{},'candidate_sha256':sha(candidate),'baseline_sha256':BASE_SHA,
        'compilation_receipt_sha256':sha(receipt),'fixture_sha256':sha(fixture),'legacy_v2_fixture_sha256':sha(legacy),
        'limits':['Private complete guarded CB19-CB34 routine plus observed C45E call; not full loading chain or campaign coverage',
                  'Original timing and CPU budget; no performance/headroom claim',
                  'Dummy audio/software headless; no paced/listening/controller certification',
                  'Historical816B generated WRAM divergence remains unresolved']}
    def check(name,value):report['checks'][name]=bool(value)
    def run(name,route='interpreted',state=fixture,script=SCRIPT,trace=True,save=False,load_at=None,exe=candidate):
        directory=output/name;directory.mkdir();(directory/'dump').mkdir()
        copy=directory/'game.exe';shutil.copy2(exe,copy);shutil.copy2(state,directory/'resume.state')
        assert sha(copy)==sha(exe)
        (directory/'input.txt').write_text(script)
        (directory/'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
          '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        (directory/'foundation.ini').write_text('NativeColumns=0\nNavigationMap=0\nJournal=0\n')
        env={k:v for k,v in os.environ.items()if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(directory/'dump'),
          SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory/'cpu.csv'),SNESRECOMP_FOUNDATION_TRACE=str(directory/'field.csv'),
          SNESRECOMP_FOUNDATION_FAST_MENUS='0',SNESRECOMP_FOUNDATION_BATTLE_INFO='0',SNESRECOMP_FOUNDATION_JOURNAL='0',
          SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',SNESRECOMP_FOUNDATION_WIDE='0',SNESRECOMP_FOUNDATION_NAVIGATION_MAP='0',
          SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='original'if route=='handwritten'else'0',
          SNESRECOMP_FOUNDATION_GENERATED_CLEAR='0',SNESRECOMP_FOUNDATION_ROUTINE_TRACE=str(directory/'routine.csv'))
        if route in ('generated','legacy-generated','native-diagnostic','native-ini','handwritten-switch','family-disabled','unknown-routine','conflict-native'):
            env.pop('SNESRECOMP_FOUNDATION_GENERATED_CLEAR')
        if route in ('generated','native-ini'):env.pop('SNESRECOMP_FOUNDATION_NATIVE_CLEAR')
        if route=='native-ini':
            with(directory/'foundation.ini').open('a')as stream:stream.write('NativeClear=1\n')
        if route=='legacy-generated':env['SNESRECOMP_FOUNDATION_GENERATED_ROUTINE']='0'
        if route=='unknown-routine':env['SNESRECOMP_FOUNDATION_GENERATED_ROUTINE']='unknown'
        if route=='native-diagnostic':env['SNESRECOMP_FOUNDATION_NATIVE_CLEAR']='original'
        if route=='handwritten-switch':env.update(SNESRECOMP_FOUNDATION_GENERATED_CLEAR='handwritten-original',SNESRECOMP_FOUNDATION_GENERATED_ROUTINE='1')
        if route=='family-disabled':env.update(SNESRECOMP_FOUNDATION_GENERATED_CLEAR='0',SNESRECOMP_FOUNDATION_GENERATED_ROUTINE='1')
        if route=='conflict-native':env.update(SNESRECOMP_FOUNDATION_GENERATED_CLEAR='1',SNESRECOMP_FOUNDATION_GENERATED_ROUTINE='1',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='original')
        if trace:env['SNESRECOMP_FOUNDATION_LOADING_TRACE']=str(directory/'loading.csv')
        if save:env.update(SNESRECOMP_OVERLAY_SELFTEST='126',SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load_at is not None:env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load_at),SNESRECOMP_RUN_FRAMES='280')
        start=time.perf_counter()
        with(directory/'host.log').open('w')as log:
            result=subprocess.run([str(copy),'--no-launcher','--rom',str(rom),'--resume-state',str(directory/'resume.state'),'--script',str(directory/'input.txt')],cwd=directory,env=env,stdout=log,stderr=log,timeout=50,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(directory/'host.log').read_text(errors='replace')
        handmade=re.search(r'\[foundation_clear\] native_instructions=(\d+)',log)
        generated=re.search(r'\[foundation_generated_routine\] generated_instructions=(\d+)([^\n]*)',log)
        pc_counts={int(pc,16):int(value)for pc,value in re.findall(r'pc([0-9a-f]{6})=(\d+)',generated[2]if generated else'')}
        old_gen=re.search(r'\[foundation_generated_clear\] generated_instructions=(\d+)',log)
        loading=rows(directory/'loading.csv')if trace else[]
        report['cases'][name]={'route':route,'exit':result.returncode,'seconds':time.perf_counter()-start,
          'resumed':'resume state loaded:'in log,'copied_exe_sha256':sha(copy),
          'handwritten_steps':int(handmade[1])if handmade else 0,'generated_steps':int(generated[1])if generated else 0,
          'generated_pc_counts':pc_counts,'legacy_generated_steps':int(old_gen[1])if old_gen else 0,
          'loading_rows':len(loading),'event_counts':dict(collections.Counter(r['event']for r in loading))}
        check(name+'_finite_resume',result.returncode==0 and report['cases'][name]['resumed'])
        if route=='generated':check(name+'_no_handwritten_execution',report['cases'][name]['handwritten_steps']==0)
        else:check(name+'_no_generated_execution',report['cases'][name]['generated_steps']==0)
        write(output/'report.json',report)
        return directory,loading
    def equal(name,left,right,native=True):
        tags=sorted(path.name[:-len('.wram.bin')]for path in(left/'dump').glob('*.wram.bin'))
        right_tags=sorted(path.name[:-len('.wram.bin')]for path in(right/'dump').glob('*.wram.bin'))
        check(name+'_dump_tags',bool(tags)and tags==right_tags)
        check(name+'_all_guest_dumps',bool(tags)and all((left/'dump'/f'{tag}.{ext}').read_bytes()==(right/'dump'/f'{tag}.{ext}').read_bytes()for tag in tags for ext in EXT))
        check(name+'_field_trace',(left/'field.csv').read_bytes()==(right/'field.csv').read_bytes())
        a=rows(left/'cpu.csv');b=rows(right/'cpu.csv');keys=set(a[0])-({'interp_insns','interp_cpu_cycles'}if native else set())
        check(name+'_cpu_timing_scheduler',len(a)==len(b)and all(all(x[k]==y[k]for k in keys)for x,y in zip(a,b)))
        if native:
            removed=sum(int(x['interp_insns'])-int(y['interp_insns'])for x,y in zip(a,b))
            report.setdefault('interpreter_step_deltas',{})[name]=removed
            report['cases'][right.name].setdefault('interpreted_instructions_removed',removed)
        if(left/'loading.csv').exists()and(right/'loading.csv').exists():check(name+'_all_bus_ppu_seam_rows',rows(left/'loading.csv')==rows(right/'loading.csv'))
        if(left/'routine.csv').exists()and(right/'routine.csv').exists():
            check(name+'_full_routine_every_instruction_state_bus_stack',rows(left/'routine.csv')==rows(right/'routine.csv'))
    old,_=run('base',exe=baseline,trace=False);off,_=run('off',trace=False)
    equal('candidate_disabled_baseline',old,off,native=False)
    observed,original_rows=run('original');equal('observer_read_only',off,observed,native=False)
    hand,hand_rows=run('hand','handwritten');gen,gen_rows=run('gen','generated')
    equal('handwritten_original',observed,hand);equal('generated_original',observed,gen);equal('generated_handwritten',hand,gen)
    check('full_generated_call_routine_18442_steps',report['cases']['gen']['generated_steps']==18442)
    pc_counts=report['cases']['gen']['generated_pc_counts']
    check('full_generated_each_loop_pc_6144',all(pc_counts.get(pc)==6144 for pc in(0x01cb2e,0x01cb31,0x01cb32)))
    other=(0x01c45e,0x01cb19,0x01cb1b,0x01cb1d,0x01cb20,0x01cb22,0x01cb25,0x01cb28,0x01cb2b,0x01cb34)
    check('full_generated_every_call_setup_return_once',all(pc_counts.get(pc)==1 for pc in other))
    all_steps=rows(gen/'routine.csv')
    returns=[r for r in all_steps if int(r['pc'])==0x01cb34]
    continuations=[r for r in all_steps if int(r['pc'])==0x01c461]
    calls=[r for r in all_steps if int(r['pc'])==0x01c45e]
    check('real_generated_call_rts_continuation',len(calls)==len(returns)==len(continuations)==1 and int(returns[0]['s'])+2==int(continuations[0]['s'])==int(calls[0]['s']) and int(returns[0]['stack_lo'])==0x60 and int(returns[0]['stack_hi'])==0xc4)
    check('caller_mode_transition_preserved',bool(calls)and int(calls[0]['m'])==int(calls[0]['xflag'])==1 and int(continuations[0]['m'])==int(continuations[0]['xflag'])==0)
    expected_cost={0x01c45e:6,0x01cb19:3,0x01cb1b:2,0x01cb1d:4,0x01cb20:3,0x01cb22:3,0x01cb25:3,0x01cb28:5,0x01cb2b:3,0x01cb2e:5,0x01cb31:2,0x01cb32:3,0x01cb34:6}
    expected_master={0x01c45e:46,0x01cb19:22,0x01cb1b:16,0x01cb1d:30,0x01cb20:22,0x01cb22:24,0x01cb25:24,0x01cb28:36,0x01cb2b:24,0x01cb2e:36,0x01cb31:14,0x01cb32:22,0x01cb34:42}
    exact=True
    for a,b in zip(all_steps,all_steps[1:]):
        pc=int(a['pc']);cost=expected_cost[pc];master=expected_master[pc]
        if pc==0x01cb32 and int(a['z']):cost=2;master=16
        exact &= int(b['cycles'])-int(a['cycles'])==cost and int(b['master'])-int(a['master'])in(master,master+40)
    check('whole_routine_instruction_costs_and_refresh',exact and len(all_steps)==18443)
    check('full_original_handwritten_18432_steps',report['cases']['hand']['handwritten_steps']==18432)
    check('full_whole_routine_removed_interpreter_steps_exact',report['cases']['gen']['interpreted_instructions_removed']==18442)
    stores=[r for r in gen_rows if r['event']=='store'];phases=[r for r in gen_rows if r['event']in('store','after_store','after_dey','exit')]
    check('all6144_word_destinations_original',[int(r['store_word_address'])for r in stores]==list(range(0x4800,0x6000)))
    check('all6144_original_bus_write_values',all(int(r['store_bytes_valid'])==1 and int(r['context_ok'])==int(r['sequence_ok'])==1 and int(r['store_low'])==int(r['store_high'])==0 for r in stores))
    costs={'store':(5,36),'after_store':(2,14),'after_dey':(3,22)};deltas=collections.defaultdict(collections.Counter);valid=True
    for a,b in zip(phases,phases[1:]):
        if a['event']not in costs:continue
        cyc,master=costs[a['event']]
        if a['event']=='after_dey'and int(a['y'])==0:cyc,master=2,16
        dc=int(b['cpu_cycles'])-int(a['cpu_cycles']);dm=int(b['master_cycles'])-int(a['master_cycles'])
        valid &= dc==cyc and dm in(master,master+40);deltas[a['event']][f'{dc}/{dm}']+=1
    check('all_original_loop_instruction_bus_internal_refresh_costs',valid and len(phases)==18433)
    report['instruction_deltas']={key:dict(value)for key,value in deltas.items()}
    legacy_gen,_=run('legacy-gen','legacy-generated');equal('legacy_generated_island',observed,legacy_gen)
    check('legacy_island_exact18432',report['cases']['legacy-gen']['legacy_generated_steps']==18432)
    check('legacy_island_no_full_or_handwritten',report['cases']['legacy-gen']['generated_steps']==report['cases']['legacy-gen']['handwritten_steps']==0)
    check('legacy_island_removed_steps_exact',report['cases']['legacy-gen']['interpreted_instructions_removed']==18432)
    for name,route,hand_expected,oldgen_expected in [('native-default','native-diagnostic',18432,0),('native-ini','native-ini',18432,0),('hand-switch','handwritten-switch',18432,0),('family-off','family-disabled',0,0),('unknown-routine','unknown-routine',0,18432),('conflict-native','conflict-native',18432,0)]:
        selected,_=run(name,route);equal(name+'_selection',observed,selected,native=bool(hand_expected or oldgen_expected))
        case=report['cases'][name]
        check(name+'_exact_route_counts',case['handwritten_steps']==hand_expected and case['legacy_generated_steps']==oldgen_expected and case['generated_steps']==0)
    saved,_=run('save',save=True);mid=saved/'saves/save0.sav';check('v3_mid_checkpoint_exists',mid.exists())
    cold_script='wait 102\ndump after\nquit\n';cold_off,cold_rows=run('cold-off',state=mid,script=cold_script)
    cold_gen,_=run('cold-gen','generated',state=mid,script=cold_script);equal('cold_generated',cold_off,cold_gen)
    cold_pc=report['cases']['cold-gen']['generated_pc_counts']
    check('cold_generated_real_return_without_fabricated_call',cold_pc.get(0x01cb34)==1 and cold_pc.get(0x01c45e)==0 and cold_pc.get(0x01cb19)==0)
    partial=[r for r in cold_rows if r['event']=='entry']
    check('cold_is_actual_partial_clear',bool(partial)and 0<int(partial[0]['entry_remaining'])<6144 and int(partial[0]['prologue_observed'])==0)
    check('cold_vram_cursor_preserved',bool(partial)and int(partial[0]['vram_pointer'])==0x6000-int(partial[0]['y']))
    check('cold_positive_generated',report['cases']['cold-gen']['generated_steps']>0)
    check('cold_removed_steps_exact',report['cases']['cold-gen']['interpreted_instructions_removed']==report['cases']['cold-gen']['generated_steps'])
    check('cold_uninterrupted_end_guest',all((observed/'dump'/f'after.{ext}').read_bytes()==(cold_gen/'dump'/f'after.{ext}').read_bytes()for ext in EXT))
    rollback_off,_=run('roll-off',save=True,load_at=170);rollback_gen,rollback_rows=run('roll-gen','generated',save=True,load_at=170)
    equal('rollback_generated',rollback_off,rollback_gen)
    check('rollback_positive_generated_again',report['cases']['roll-gen']['generated_steps']>18432)
    check('rollback_removed_steps_exact',report['cases']['roll-gen']['interpreted_instructions_removed']==report['cases']['roll-gen']['generated_steps'])
    check('rollback_actual_load_issued','[overlay_selftest] load issued'in(rollback_gen/'host.log').read_text())
    entries=[r for r in rollback_rows if r['event']=='entry']
    check('rollback_original_partial_epochs',len(entries)==3 and all(int(r['prologue_observed'])==0 and 0<int(r['entry_remaining'])<6144 and int(r['vram_pointer'])==0x6000-int(r['y'])for r in entries[1:]))
    target=json.loads((rollback_gen/'dump/after.regs.json').read_text())['frame'];elapsed=target-int(partial[0]['frame']);assert elapsed>0
    uninterrupted,_=run('roll-cold','generated',state=mid,script=f'wait {elapsed}\ndump after\nquit\n')
    check('rollback_same_uninterrupted_continuation',all((uninterrupted/'dump'/f'after.{ext}').read_bytes()==(rollback_gen/'dump'/f'after.{ext}').read_bytes()for ext in EXT))
    check('legacy_v2_fixture_actual_schema',legacy.read_bytes().find(struct.pack('<II',0x53544f53,2))>=48)
    v2_off,_=run('v2-off',state=legacy,script=cold_script);v2_gen,_=run('v2-gen','generated',state=legacy,script=cold_script)
    equal('v2_cursor_fallback',v2_off,v2_gen,native=False);check('v2_zero_generated',report['cases']['v2-gen']['generated_steps']==0)
    raw=mid.read_bytes();header=raw.find(struct.pack('<II',0x53544f53,3));assert header>=48
    for name,flags in [('inc32',0x200001),('remap1',0x010101)]:
        changed=bytearray(raw);struct.pack_into('<I',changed,len(changed)-16,flags);struct.pack_into('<I',changed,len(changed)-4,zlib.crc32(changed[:-4]))
        state=output/(name+'.state');state.write_bytes(changed)
        left,left_rows=run(name+'-off',state=state,script=cold_script);right,_=run(name+'-gen','generated',state=state,script=cold_script)
        equal(name+'_unsupported_fallback',left,right,native=False)
        check(name+'_original_execution',bool(left_rows)and report['cases'][right.name]['generated_steps']==0)
    changed={path:digest for path,digest in protected.items()if not Path(path).is_file()or sha(Path(path))!=digest}
    report['protected_count']=len(protected);report['changed_inputs']=changed;check('protected_inputs_unchanged',not changed)
    report['passed']=all(report['checks'].values());report['check_count']=len(report['checks']);report['real_native_runs']=len(report['cases'])
    write(output/'report.json',report)
    print(json.dumps({'passed':report['passed'],'checks':report['check_count'],'real_native_runs':report['real_native_runs'],'failed':[key for key,value in report['checks'].items()if not value],'report':str(output/'report.json'),'report_sha256':sha(output/'report.json')},indent=2))
    return 0 if report['passed']else 1

if __name__=='__main__':raise SystemExit(main())
