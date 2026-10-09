"""Observe and qualify the bounded clear seam using copied natural transitions."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = ('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx')
SCRIPT = 'wait 10\ndump before\npress down 96\ndump door\nwait 17\ndump loading\nwait 2\ndump clear\nwait 102\ndump after\nquit\n'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--reference-exe',type=Path,required=True)
    parser.add_argument('--native-proof',action='store_true')
    args=parser.parse_args()
    base=ROOT/'local/runs'/('loading-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir(exist_ok=False)
    fixture=ROOT/'local/runs/likado-inside-a/saves/save0.sav'
    report={'executable_sha256':sha(args.exe),'reference_sha256':sha(args.reference_exe),
        'source_state_sha256':sha(fixture),'checks':{},'cases':{},'limits':[
            'Bounded natural house exit and copied mid-clear state; not a campaign or scrolling slowdown proof',
            'Original-cost native execution retains SNES CPU budget; lower interpreted work does not mean fewer loading fields',
            'Headless telemetry is not physical controller/audio listening or display scanout certification']}

    def run(name,exe,state=fixture,trace=False,native=False,script=SCRIPT,save=False,load_at=None):
        directory=base/name;directory.mkdir();(directory/'dump').mkdir()
        shutil.copy2(exe,directory/'game.exe');shutil.copy2(state,directory/'resume.state')
        (directory/'input.txt').write_text(script)
        (directory/'config.ini').write_text('[Graphics]\nRenderer=software\nVSync=0\n[Sound]\nEnableAudio=0\n'
            '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(directory/'dump'),
            SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory/'cpu.csv'),SNESRECOMP_FOUNDATION_TRACE=str(directory/'field.csv'),
            SNESRECOMP_FOUNDATION_FAST_MENUS='0',SNESRECOMP_FOUNDATION_BATTLE_INFO='0',SNESRECOMP_FOUNDATION_JOURNAL='0',
            SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',SNESRECOMP_FOUNDATION_WIDE='0',
            SNESRECOMP_FOUNDATION_NATIVE_CLEAR='original' if native else '0')
        if trace:env['SNESRECOMP_FOUNDATION_LOADING_TRACE']=str(directory/'loading.csv')
        if save:env.update(SNESRECOMP_OVERLAY_SELFTEST='126',SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load_at is not None:env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load_at),SNESRECOMP_RUN_FRAMES='280')
        with (directory/'host.log').open('w') as log:
            start=time.perf_counter()
            result=subprocess.run([str(directory/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                '--resume-state',str(directory/'resume.state'),'--script',str(directory/'input.txt')],cwd=directory,env=env,
                stdout=log,stderr=log,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
        rows=list(csv.DictReader((directory/'loading.csv').open())) if (directory/'loading.csv').exists() else []
        report['cases'][name]={'exit':result.returncode,'seconds':time.perf_counter()-start,
            'resumed':'resume state loaded:' in (directory/'host.log').read_text(errors='replace'),
            'event_counts':dict(collections.Counter(r['event'] for r in rows)),'loading_rows':len(rows)}
        count=re.search(r'\[foundation_clear\] native_instructions=(\d+)',(directory/'host.log').read_text(errors='replace'))
        report['cases'][name]['native_instructions']=int(count.group(1)) if count else 0
        return directory,rows

    def compare(name,left,right,native=False):
        tags=[p.name[:-len('.wram.bin')] for p in (left/'dump').glob('*.wram.bin')]
        report['checks'][name+'_all_guest_snapshots_identical']=bool(tags) and all(
            (left/'dump'/(tag+'.'+ext)).read_bytes()==(right/'dump'/(tag+'.'+ext)).read_bytes() for tag in tags for ext in EXTENSIONS)
        report['checks'][name+'_field_trace_identical']=(left/'field.csv').read_bytes()==(right/'field.csv').read_bytes()
        if native:
            a=list(csv.DictReader((left/'cpu.csv').open()));b=list(csv.DictReader((right/'cpu.csv').open()))
            keys=set(a[0])-{'interp_insns','interp_cpu_cycles'}
            report['checks'][name+'_cpu_timing_and_scheduler_identical']=len(a)==len(b) and all(all(x[k]==y[k] for k in keys) for x,y in zip(a,b))
            report['cases'][right.name]['interpreted_instructions_removed']=sum(int(x['interp_insns'])-int(y['interp_insns']) for x,y in zip(a,b))
        else:report['checks'][name+'_cpu_trace_identical']=(left/'cpu.csv').read_bytes()==(right/'cpu.csv').read_bytes()
        report['checks'][name+'_same_dump_tags']=tags==[p.name[:-len('.wram.bin')] for p in (right/'dump').glob('*.wram.bin')]

    original,_=run('reference',args.reference_exe)
    off,_=run('observer-off',args.exe)
    observed,rows=run('observer-on',args.exe,trace=True)
    compare('shared_charge_original_path',original,off)
    compare('read_only_observer',off,observed)
    stores=[r for r in rows if r['event']=='store'];exits=[r for r in rows if r['event']=='exit']
    report['checks']['one_full_original_clear_observed']=len(stores)==6144 and len(exits)==1 and int(exits[0]['completed'])==int(exits[0]['full_range'])==1
    report['checks']['all_original_word_writes_valid']=all(int(r['store_bytes_valid'])==1 and int(r['context_ok'])==int(r['sequence_ok'])==1 and int(r['store_low'])==int(r['store_high'])==0 for r in stores)
    report['checks']['original_word_destinations_exact']=list(map(lambda r:int(r['store_word_address']),stores))==list(range(0x4800,0x6000))
    # Neighbour phase rows measure each completed original instruction.
    expected={'store':(5,36),'after_store':(2,14),'after_dey':(3,22)}
    deltas=collections.defaultdict(collections.Counter)
    valid_costs=True
    phases=[r for r in rows if r['event'] in ['store','after_store','after_dey','exit']]
    for a,b in zip(phases,phases[1:]):
        if a['event'] not in expected:continue
        dc=int(b['cpu_cycles'])-int(a['cpu_cycles']);dm=int(b['master_cycles'])-int(a['master_cycles'])
        cyc,master=expected[a['event']]
        if a['event']=='after_dey' and int(a['y'])==0:cyc,master=2,16
        # DRAM refresh adds 40 clocks at its existing instruction boundary.
        valid_costs &= dc==cyc and dm in (master,master+40)
        deltas[a['event']][f'{dc}/{dm}']+=1
    report['instruction_deltas']={k:dict(v) for k,v in deltas.items()}
    report['checks']['original_instruction_costs_match']=valid_costs and len(phases)==6144*3+1
    report['clear_exit']=exits[0] if exits else None
    report['constructor_context']=[r for r in rows if r['event'].startswith('constructor_')]
    if args.native_proof:
        native,nrows=run('native-original',args.exe,trace=True,native=True)
        compare('native_original',observed,native,native=True)
        report['checks']['native_original_every_seam_row_identical']=rows==nrows
        report['checks']['full_clear_really_native']=report['cases']['native-original']['native_instructions']==18432
        # A saved copy whose resumed PC lies within the clear, not an owner save.
        saved,_=run('mid-save',args.exe,save=True)
        state=saved/'saves/save0.sav'
        cold_script='wait 102\ndump after\nquit\n'
        cold_off,cold_rows=run('cold-original',args.exe,state,trace=True,script=cold_script)
        cold_on,cold_native=run('cold-native',args.exe,state,trace=True,native=True,script=cold_script)
        compare('cold_mid_clear',cold_off,cold_on,native=True)
        report['checks']['cold_mid_clear_seams_identical']=cold_rows==cold_native
        partial=[r for r in cold_rows if r['event']=='entry']
        report['checks']['copied_state_is_partial_clear']=bool(partial) and 0<int(partial[0]['entry_remaining'])<6144 and int(partial[0]['prologue_observed'])==0
        report['checks']['cold_restore_retains_coherent_vram_cursor']=bool(partial) and int(partial[0]['vram_pointer'])==0x6000-int(partial[0]['y'])
        report['checks']['cold_partial_really_native']=report['cases']['cold-native']['native_instructions']>0
        report['checks']['cold_matches_uninterrupted_after']=all((observed/'dump'/('after.'+ext)).read_bytes()==(cold_on/'dump'/('after.'+ext)).read_bytes() for ext in EXTENSIONS)
        rollback_off,rollback_rows=run('rollback-original',args.exe,trace=True,save=True,load_at=170)
        rollback_on,rollback_native=run('rollback-native',args.exe,trace=True,native=True,save=True,load_at=170)
        compare('rollback_mid_clear',rollback_off,rollback_on,native=True)
        report['checks']['rollback_every_seam_row_identical']=rollback_rows==rollback_native
        entries=[r for r in rollback_native if r['event']=='entry']
        # Saving also closes/reset-notifies the overlay, starting an observer
        # epoch during the first pass; the later load is the third entry.
        report['checks']['rollback_reenters_partial_clear']=len(entries)==3 and all(int(r['prologue_observed'])==0 and 0<int(r['entry_remaining'])<6144 and int(r['vram_pointer'])==0x6000-int(r['y']) for r in entries[1:])
        report['checks']['rollback_really_native_again']=report['cases']['rollback-native']['native_instructions']>18432
        report['checks']['rollback_load_issued']='[overlay_selftest] load issued' in (rollback_on/'host.log').read_text(errors='replace')
        target=json.loads((rollback_on/'dump/after.regs.json').read_text())['frame']
        elapsed=target-int(partial[0]['frame']);assert elapsed>0
        uninterrupted,_=run('rollback-uninterrupted-cold',args.exe,state,native=True,script=f'wait {elapsed}\ndump after\nquit\n')
        report['checks']['rollback_matches_uninterrupted_continuation']=all((uninterrupted/'dump'/('after.'+ext)).read_bytes()==(rollback_on/'dump'/('after.'+ext)).read_bytes() for ext in EXTENSIONS)
        legacy_saved,_=run('v2-mid-save',args.reference_exe,save=True)
        legacy_state=legacy_saved/'saves/save0.sav'
        assert legacy_state.read_bytes().find(struct.pack('<II',0x53544f53,2))>=48, \
            'Legacy missing-cursor proof requires a reference that produces schema v2, not a current v3 build.'
        legacy_off,_=run('v2-old-reference',args.reference_exe,legacy_state,script=cold_script)
        legacy_on,_=run('v2-native-fallback',args.exe,legacy_state,trace=True,native=True,script=cold_script)
        compare('v2_missing_cursor_compatibility',legacy_off,legacy_on)
        report['checks']['v2_missing_cursor_retains_original']=report['cases']['v2-native-fallback']['native_instructions']==0
        # Change only a copied v3 hardware latch to another valid SNES setting.
        # Unsupported port state must execute the original instructions exactly.
        raw=state.read_bytes();header=raw.find(struct.pack('<II',0x53544f53,3))
        assert header>=48 and raw.find(struct.pack('<II',0x53544f53,3),header+1)==-1
        port_offset=len(raw)-20
        for name,flags in [('increment-32',0x200001),('remap-1',0x010101)]:
            changed=bytearray(raw);struct.pack_into('<I',changed,port_offset+4,flags)
            struct.pack_into('<I',changed,len(changed)-4,zlib.crc32(changed[:-4]))
            changed_state=base/(name+'.state');changed_state.write_bytes(changed)
            fallback_off,fallback_rows=run(name+'-original',args.exe,changed_state,trace=True,script=cold_script)
            fallback_on,fallback_native=run(name+'-native',args.exe,changed_state,trace=True,native=True,script=cold_script)
            compare(name+'_fallback',fallback_off,fallback_on,native=True)
            report['checks'][name+'_fallback_seams_identical']=fallback_rows==fallback_native
            report['checks'][name+'_guard_retains_original']=report['cases'][name+'-native']['native_instructions']==0 and bool(fallback_rows)
    report['checks']['source_state_preserved']=sha(fixture)==report['source_state_sha256']
    report['checks']['all_processes_exit_and_resume']=all(c['exit']==0 and c['resumed'] for c in report['cases'].values())
    report['passed']=all(report['checks'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
