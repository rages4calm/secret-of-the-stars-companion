"""Copied Likado actor side-pass proof; never launch or edit owner progress."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import time
import numpy as np
from PIL import Image
from inspect_foundation_actors import SCRIPT, inspect, rom_slice, oam_piece

ROOT=Path(__file__).resolve().parents[1]
GUEST=('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx')
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def read_surface(path):
    frame,width,height=map(int,re.search(r'frame-(\d+)-(\d+)x(\d+)',path.name).groups())
    raw=path.read_bytes()
    if len(raw)!=width*height*4: raise ValueError('Incomplete composed surface '+str(path))
    return frame,np.frombuffer(raw,dtype=np.uint8).reshape(height,width,4)


def guest_prefixes(directory):
    return sorted(p.name[:-len('.wram.bin')] for p in (directory/'dump').glob('*.wram.bin'))


def actor_trace(directory):
    path=directory/'actors.csv'
    if not path.exists():raise ValueError('Actor trace not emitted: '+str(path))
    rows=list(csv.DictReader(path.open()))
    return [{key:(value if key=='event' else int(value,0)) for key,value in row.items()} for row in rows]


def qualify_trace(rows):
    """Link active poses to observed source metadata and actual completed DMA."""
    completed={};captured={};invalid_frames=0;valid_frames=0;linked=[];source_exact=[]
    target_key=lambda row:tuple(row[k] for k in ('target_record','target_flags','target_phase','target_descriptor','target_x','target_y'))
    target_captures=[row for row in rows if row['event']=='capture' and row['target_record']==0x414b]
    for row in rows:
        key=(row['generation'],row['epoch'])
        if row['event']=='capture' and row['target_record']==0x414b:
            captured[(row['generation'],row['producer_frame'])]=target_key(row)
        if row['event']=='dma_complete' and row['packet_valid']:
            completed[key]=row
        if row['event']=='frame':
            if not row['packet_valid']:invalid_frames+=1;continue
            valid_frames+=1
            packet=completed.get(key)
            linked.append(packet is not None and packet['packet_match']==1 and packet['producer_frame']==row['producer_frame'])
            if row['target_record']==0x414b:
                source_exact.append(captured.get((row['generation'],row['producer_frame']))==target_key(row))
    reset_rows=[row for row in rows if row['event']=='reset']
    return {'active_frames':valid_frames,'invalid_frames':invalid_frames,'target_captures':len(target_captures),
        'resets':len(reset_rows),'generations':sorted({row['generation'] for row in rows}),
        'checks':{'actual_packet_epoch_lineage':bool(linked) and all(linked),
            'target_pose_matches_observed_producer_metadata':bool(source_exact) and all(source_exact),
            'target_capture_cpu_context_verified':bool(target_captures) and all(
                (r['cpu_d'],r['cpu_db'],r['cpu_m'],r['cpu_x'])==(0x0e00,1,0,1) for r in target_captures),
            'reset_events_clear_packet_cache':bool(reset_rows) and all(r['packet_valid']==0 and r['cached_actors']==0 for r in reset_rows)}}


def original_target_art(prefix,rom,descriptor_override=None,anchor_override=None):
    """Decode original 4bpp pixels using actual packet pose and current palette."""
    ram=Path(str(prefix)+'.wram.bin').read_bytes();vram=Path(str(prefix)+'.vram.bin').read_bytes()
    cgram=Path(str(prefix)+'.cgram.bin').read_bytes()
    record=ram[0x414b:0x4164];camera=struct.unpack_from('<hh',ram,0x2ad)
    world=struct.unpack_from('<HH',record,1)
    phase=ram[0x475]>>7;base=int.from_bytes(record[5:7],'little')
    descriptor=descriptor_override or (0x0e9800+((base+((record[0]*2)&255)+phase)&65535)*8)
    anchor=anchor_override or (world[0]-camera[0],world[1]-camera[1])
    data=rom_slice(rom,descriptor,8);mask=0xefff if ram[0x400] else 0xffff
    expected=[]
    for part,(dx,dy) in enumerate(((0,0),(8,0),(0,8),(8,8))):
        tileword=int.from_bytes(data[part*2:part*2+2],'little')&mask
        at=(0xe000 if tileword&256 else 0xc000)+(tileword&255)*32
        palette=128+((tileword>>9)&7)*16
        for v in range(8):
            for u in range(8):
                tx=7-u if tileword&0x4000 else u;ty=7-v if tileword&0x8000 else v
                pixel=sum(((vram[at+ty*2+plane//2*16+plane%2]>>(7-tx))&1)<<plane for plane in range(4))
                if not pixel:continue
                color=int.from_bytes(cgram[(palette+pixel)*2:(palette+pixel+1)*2],'little')
                rgb=tuple((((color>>shift)&31)<<3)|(((color>>shift)&31)>>2) for shift in (0,5,10))
                expected.append((anchor[0]+dx+u,anchor[1]-1+dy+v,rgb))
    return {'record':'7E:414B','flags':record[0],'phase':phase,'descriptor_rom':f'{descriptor:06X}',
            'camera':list(camera),'world':list(world),'screen_anchor':list(anchor),'pixels':expected}


def compare_pair(base,name,report):
    off,on=base/(name+'-off'),base/(name+'-on');checks=report['checks']
    tags=guest_prefixes(off)
    checks[name+'_snapshot_tags_match']=bool(tags) and tags==guest_prefixes(on)
    checks[name+'_all_guest_snapshots_identical']=bool(tags) and all((off/'dump'/f'{tag}.{ext}').read_bytes()==
        (on/'dump'/f'{tag}.{ext}').read_bytes() for tag in tags for ext in GUEST)
    for trace in ('cpu','state','field'):
        checks[name+'_'+trace+'_identical']=(off/(trace+'.csv')).read_bytes()==(on/(trace+'.csv')).read_bytes()
    surfaces={};center_exact=[];only_margins=[]
    for p in sorted((on/'captures').glob('*.bgrx')):
        frame,b=read_surface(p);matches=list((off/'captures').glob(f'frame-{frame}-*.bgrx'))
        if len(matches)!=1:raise ValueError('Missing paired actor capture '+str(frame))
        _,a=read_surface(matches[0]);scale=b.shape[0]//224
        if a.shape!=b.shape:raise ValueError('Actor toggle changed output dimensions')
        left=(b.shape[1]-256*scale)//2;right=left+256*scale
        diff=np.any(a!=b,axis=2);center=np.array_equal(a[:,left:right],b[:,left:right]);center_exact.append(center)
        only_margins.append(not bool(diff[:,left:right].any()))
        surfaces[str(frame)]={'width':b.shape[1],'height':b.shape[0],'changed_pixels':int(diff.sum()),
            'left_margin_changed_pixels':int(diff[:,:left].sum()),'right_margin_changed_pixels':int(diff[:,right:].sum()),
            'original256_center_identical':center}
        if diff.any():
            Image.fromarray(b[:,:,:3][:,:,::-1]).save(p.with_suffix('.png'))
    checks[name+'_composed_center256_byte_identical']=bool(center_exact) and all(center_exact)
    checks[name+'_changes_confined_to_margins']=bool(only_margins) and all(only_margins)
    report['surfaces'][name]=surfaces
    return off,on


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--fixture',type=Path,default=ROOT/'local/runs/likado-east-a/saves/save0.sav')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();args.exe=args.exe.resolve(strict=True);args.fixture=args.fixture.resolve(strict=True)
    base=(args.out or ROOT/'local/runs'/('actor-wide-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if not base.is_relative_to((ROOT/'local').resolve()) or base.exists():raise ValueError('Use a fresh private directory under local/')
    base.mkdir(parents=True);frozen=base/'candidate.exe';shutil.copy2(args.exe,frozen)
    rom_path=ROOT/'local/inputs/clean-usa.sfc';rom=rom_path.read_bytes()
    if sha(rom_path)!=ROM_SHA:raise ValueError('Exact clean USA ROM required')
    source_hashes={str(p):sha(p) for p in (args.fixture,rom_path,args.exe)}
    report={'executable_sha256':sha(frozen),'script_sha256':hashlib.sha256(SCRIPT.encode()).hexdigest(),
            'source_inputs':source_hashes,'checks':{},'cases':{},'surfaces':{},'actor_snapshots':{}}
    sequence=list(range(1,115))+[120,130,140,160,180,200,220,240]

    def run(name,state,script,enabled,enhanced=0,save=None,load=None,wide=1):
        d=base/name;d.mkdir();(d/'dump').mkdir();(d/'captures').mkdir()
        shutil.copy2(frozen,d/'game.exe');shutil.copy2(state,d/'resume.state');(d/'input.txt').write_text(script)
        (d/'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n[Controller]\nSourceP1=1\nSourceP2=0\n')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(d/'dump'),
            SNESRECOMP_FOUNDATION_WIDE=str(wide),SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(enabled),
            SNESRECOMP_STATE_TRACE=str(d/'state.csv'),
            SNESRECOMP_FOUNDATION_CPU_TRACE=str(d/'cpu.csv'),SNESRECOMP_FOUNDATION_TRACE=str(d/'field.csv'),
            SNESRECOMP_FOUNDATION_FIELD_TRACE=str(d/'terrain.csv'),SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced),
            SNESRECOMP_FOUNDATION_BATTLE_INFO='0',SNESRECOMP_FOUNDATION_JOURNAL='0',SNESRECOMP_FOUNDATION_FAST_MENUS='0',
            SNESRECOMP_FOUNDATION_HD_MENU_FRAMES='0',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',SNESRECOMP_FOUNDATION_NATIVE_COLUMNS='0',
            SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE=','.join(map(str,sequence)),SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(d/'captures'))
        if enabled:env['SNESRECOMP_FOUNDATION_ACTORS_TRACE']=str(d/'actors.csv')
        if save is not None:env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save),SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load is not None:env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load),SNESRECOMP_RUN_FRAMES=str(load+50))
        with (d/'host.log').open('w') as log:
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(rom_path),'--resume-state',str(d/'resume.state'),
                '--script',str(d/'input.txt')],cwd=d,env=env,stdout=log,stderr=log,timeout=50,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        text=(d/'host.log').read_text(errors='replace')
        report['cases'][name]={'exit':result.returncode,'resumed':'resume state loaded:' in text,
            'gamepads_disabled':'enable_gamepad=[0,0]' in text,'source_checkpoint_sha256':sha(state)}
        if not enabled:report['cases'][name]['actor_observer_disabled']='experimental_field_actors=0 observer=0' in text
        return d

    def pair(name,state,script,**options):
        run(name+'-off',state,script,0,**options);run(name+'-on',state,script,1,**options)
        return compare_pair(base,name,report)

    off,on=pair('sweep',args.fixture,SCRIPT)
    snapshots=[inspect(off/'dump'/tag,rom) for tag in guest_prefixes(off)]
    report['actor_snapshots']['sweep']=snapshots
    report['checks']['original_actor414B_moves_from_margin_into_center']=any(not s['actors'][3]['original_draw_gate'] and
        s['actors'][3]['within400_margin'] for s in snapshots) and any(s['actors'][3]['original_draw_gate'] for s in snapshots)
    adjacent=[]
    by_tag={Path(s['prefix']).name:s for s in snapshots}
    for tag in ('start','edge','entered','further','return'):
        source=by_tag[tag];following=(off/'dump'/(tag+'_next.oam.bin')).read_bytes()
        for actor in source['actors']:
            for piece in actor.get('pieces',[]):
                if 'slot' in piece:
                    actual=oam_piece(following,piece['slot'])
                    adjacent.append(all(actual[key]==piece[key] for key in ('x9','y8','tile','attr','large')))
    report['packet_snapshot_oracle']={'adjacent_original_piece_comparisons':len(adjacent),'all_exact':bool(adjacent) and all(adjacent)}
    report['checks']['source_staging_matches_next_actual_oam']=bool(adjacent) and all(adjacent)
    # Displayed OAM lineage may precede current WRAM. Decode the matched packet pose.
    start_packet=[r for r in actor_trace(on) if r['event']=='frame'][1]
    oracle=original_target_art(off/'dump/start',rom,start_packet['target_descriptor'],
        (start_packet['target_x'],start_packet['target_y']))
    report['target_start_art']={k:v for k,v in oracle.items() if k not in ('pixels','flags','phase')}
    report['target_start_art'].update(displayed_flags=start_packet['target_flags'],displayed_phase=start_packet['target_phase'],
        producer_frame=start_packet['producer_frame'],packet_epoch=start_packet['epoch'])
    p=next((on/'captures').glob('frame-2-*.bgrx'));q=next((off/'captures').glob('frame-2-*.bgrx'))
    _,a=read_surface(q);_,b=read_surface(p);matches=0
    expected={(x+72,y):rgb for x,y,rgb in oracle['pixels']}
    for x,y,rgb in oracle['pixels']:
        if not (256<=x<328 or -72<=x<0) or not 0<=y<224:continue
        at=x+72
        if not np.array_equal(a[y,at],b[y,at]) and tuple(b[y,at,:3][::-1])==rgb:matches+=1
    report['target_start_art']['changed_pixels_matching_original_palette']=matches
    changed=np.argwhere(np.any(a!=b,axis=2))
    report['target_start_art']['all_margin_changed_pixels']=len(changed)
    report['checks']['actor414B_original_art_really_drawn_in_right_margin']=matches==len(oracle['pixels']) and matches>0
    report['checks']['displayed_packet_descriptor_explains_every_start_margin_pixel']=bool(len(changed)) and all(
        expected.get((int(x),int(y)))==tuple(b[y,x,:3][::-1]) for y,x in changed)
    pair('enhanced-sweep',args.fixture,SCRIPT,enhanced=1)
    pair('menu',args.fixture,'wait 30\npress b 1\nwait 60\ndump menu\npress b 1\nwait 90\ndump closed\nquit\n')
    saved=run('save-source',args.fixture,SCRIPT,1,save=32)
    pair('cold',saved/'saves/save0.sav','wait 92\ndump restored\nquit\n')
    pair('rollback',args.fixture,SCRIPT,save=32,load=96)
    report['checks']['actual_rollback_load_issued']='[overlay_selftest] load issued' in (base/'rollback-on/host.log').read_text(errors='replace')
    pair('original-width',args.fixture,SCRIPT,wide=0)
    report['checks']['actor_setting_without_wide_keeps_exact_surface']=all(m['changed_pixels']==0 and m['width']==256
        for m in report['surfaces']['original-width'].values())
    report['checks']['all_processes_exit_resume_and_disable_gamepads']=all(c['exit']==0 and c['resumed'] and c['gamepads_disabled'] for c in report['cases'].values())
    report['checks']['actor_off_uses_disabled_observer']=all(c['actor_observer_disabled'] for name,c in report['cases'].items() if name.endswith('-off'))
    report['checks']['source_inputs_preserved']=all(sha(Path(path))==value for path,value in source_hashes.items())
    report['actor_trace_qualification']={}
    for name in ('sweep','enhanced-sweep','menu','cold','rollback'):
        rows=actor_trace(base/(name+'-on'));qualified=qualify_trace(rows);report['actor_trace_qualification'][name]=qualified
        for key,value in qualified['checks'].items():report['checks'][name+'_'+key]=value
        if name=='sweep':
            target_frames=[r for r in rows if r['event']=='frame' and r['packet_valid'] and r['target_record']==0x414b]
            report['checks']['actual_target_native_margin_counts_positive']=any(r['side_pieces']>0 and r['side_pixels']>0 and
                r['target_x']>=256 for r in target_frames)
            report['checks']['exact254_crossing_observed_with_margin_pixels']=any(r['target_x']==254 and r['side_pixels']>0 for r in target_frames)
            report['checks']['original_target_pose_change_observed']=len({r['target_flags'] for r in target_frames})>1
        if name=='cold':
            resets=[r for r in rows if r['event']=='reset']
            report['checks']['cold_restore_clears_cache_before_new_packet']=bool(resets) and resets[0]['packet_valid']==0 and qualified['checks']['actual_packet_epoch_lineage']
        if name=='rollback':
            report['checks']['rollback_has_restore_generation_change']=len(qualified['generations'])>2
            resets=[r for r in rows if r['event']=='reset']
            report['checks']['rollback_reset_has_no_valid_packet']=len(resets)>1 and all(r['packet_valid']==0 for r in resets)
            report['checks']['actual_restore_rolls_guest_frame_back_and_clears_cache']=any(
                row['event']=='reset' and row['frame']<previous['frame'] and not row['packet_valid'] and not row['cached_actors']
                for previous,row in zip(rows,rows[1:]))
    report['limits']=['Only checked nonwrapping Likado regular actor records; no new spawning, collision, tasks, party/composite/effect actor coverage',
        'Composed side pixels are original owner-provided ROM-derived artwork; all extracts/captures stay local',
        'Headless exact parity is separate from paced GPU/audio; root runs the existing frame/audio gate on this same binary',
        'Interactive rewind timeline and physical-controller behavior are not newly certified']
    report['passed']=all(report['checks'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps({'passed':report['passed'],'checks':report['checks']},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
