"""Finite copied-EXE navigation-map SDL input, movement and restore proof.

Silent forensic tests are separate from paced audio qualification. No old native
artifact without map source is accepted; source receipts retain their status.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess

SOURCE=Path(__file__).resolve().parents[1]
ROOT=SOURCE.parent if SOURCE.name=='github-repo' else SOURCE
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
EXTENSIONS=('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','fb.bgrx','regs.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original_objective(rom,ram,destination):
    """Independent original selected scene/exit/name stream oracle, not host C."""
    def read(address,n=1):
        bank,low=address>>16,address&65535
        if not 0<=bank<48 or low<32768 or low+n>65536:raise ValueError('original address')
        offset=bank*32768+low-32768
        return int.from_bytes(rom[offset:offset+n],'little')
    def story(selector,nibble):
        if selector<120:return ram[0x5360+((selector>>3)&1)]&(128>>(selector&7))
        if selector==126:return ram[0x5361]&15
        if selector==255:
            value=ram[0x5362+(nibble>>1)]
            return value&15 if nibble&1 else value>>4
        return ram[0x5362+((selector&127)>>3)]&(128>>(selector&7))
    def selected(scene):
        cursor=0x080000|read(0x088000+scene*2,2)
        for _ in range(52):
            kind=read(cursor)
            if kind==255:return 0x080000|read(cursor+1,2)
            a,b=read(cursor+1),read(cursor+2);stage=ram[0x5372]
            conditions=(stage<a or(stage==a and not story(b,b)),stage==a and story(b,b),stage<=a,
                stage==a and story(126,0)==b,bool(story(a|128,b)),not story(a|128,b),
                story(255,a)==b,bool(ram[0x4b6]&128))
            if kind>7:raise ValueError('original scene selector')
            if conditions[kind]:return 0x080000|read(cursor+3,2)
            cursor+=5
        raise ValueError('original scene selection unterminated')
    stream=selected(0)
    index=read(stream+10,2)
    cursor=0x080000|read(0x08aa00+index*2,2)
    records=[]
    for _ in range(512):
        if read(cursor,2)==65535:break
        if read(cursor+3,2)&16383==destination:
            if read(cursor+2):raise ValueError('conditional objective entrance')
            records.append((read(cursor),read(cursor+1)))
        cursor+=8
    else:raise ValueError('original exit list unterminated')
    if not records or len(records)>4:raise ValueError('objective world entrance ambiguous')
    if max(x for x,y in records)-min(x for x,y in records)>1 or max(y for x,y in records)-min(y for x,y in records)>1:
        raise ValueError('objective entrance group ambiguous')
    named=selected(destination);flags=read(named,2);cursor=named+15
    for mask,size in [(0x6000,2),(0x1000,1),(0x80,2),(0x40,1),(0x20,1),(0x10,2)]:
        if flags&mask:cursor+=size
    if flags&8:cursor+=5 if read(cursor)&128 else 8
    if flags&4:cursor+=2
    if not flags&2:raise ValueError('objective town unnamed')
    name_index=read(cursor)
    if name_index>=23:raise ValueError('objective name is not original town name')
    cursor=0x040000|read(0x04c200+name_index*2,2)
    name=[]
    for _ in range(24):
        value=read(cursor);cursor+=1
        if value in (0,255):break
        if value!=128 and not 129<=value<=154:raise ValueError('original town text unreadable')
        name.append(' ' if value==128 else chr(65+value-129))
    dims=read(stream+5)
    return {'destination':destination,'label':''.join(name).strip(),'original_stream':hex(stream),
            'world_x':sum(x for x,y in records)*16//len(records)+8,
            'world_y':sum(y for x,y in records)*16//len(records)+8,
            'world_width':(dims>>4)*256,'world_height':(dims&15)*256,'original_entrance_records':records}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('exe','receipt','rom','field-state','world-state','output'):
        p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args()
    source={k:getattr(args,k.replace('-','_')).resolve(strict=True) for k in ('exe','receipt','rom','field-state','world-state')}
    original={k:sha(v) for k,v in source.items()}
    receipt=json.loads(source['receipt'].read_text())
    if receipt.get('executable_sha256')!=original['exe'] or receipt.get('status')!='compiled_unqualified' or not receipt.get('public_build'):
        p.error('Require the matching real compiled_unqualified public source receipt')
    if 'src/foundation_map.c' not in receipt.get('authored_inputs',{}):
        p.error('Executable receipt has no authored navigation map input')
    if original['rom']!=ROM_SHA:p.error('Exact original clean USA ROM required')
    out=args.output.resolve()
    if out.exists() or not out.is_relative_to((ROOT/'local').resolve()):p.error('Use a fresh private directory under local/')
    out.mkdir(parents=True)
    report={'executable_sha256':original['exe'],'source_receipt_sha256':original['receipt'],
            'receipt_status_unchanged':'compiled_unqualified','checks':{},'runs':{},'comparisons':[]}
    checks=report['checks']
    capture_frames=(59,60,76,106,120,131,150,151,180,210)
    simple='wait 60\ndump open\nwait 120\ndump closed\nquit\n'
    move='wait 60\ndump open\npress right 16\ndump walk\nwait 104\ndump closed\nquit\n'
    restore='wait 60\ndump open\npress right 16\ndump walk\nwait 30\ndump before\npress left 16\nwait 58\ndump restored\nquit\n'
    warm='wait 60\ndump open\nwait 60\ndump closed\nwait 11\ndump reopened\nwait 79\ndump stable\nquit\n'

    def run(name,state,enabled,method,width=256,script=simple,rollback=False,original_view=False,objective=True):
        folder=out/name
        folder.mkdir();(folder/'dump').mkdir();(folder/'capture').mkdir()
        local_exe=folder/'game.exe'
        shutil.copy2(source['exe'],local_exe)
        for dll in source['exe'].parent.glob('*.dll'):shutil.copy2(dll,folder/dll.name)
        shutil.copy2(state,folder/'seed.state')
        shutil.copy2(state,folder/'resume.state')
        resume_initial=sha(folder/'resume.state')
        (folder/'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[Controller]\nSourceP1=2\nSourceP2=0\n'
            '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\n'
            'Controls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
            'Map=Back+L3\nJournal=L3\nTurbo=None\nMovementBoost=None\n'
            '[KeyMap]\nMap=M\nJournal=J\nTurbo=None\nMovementBoost=None\n',encoding='utf-8')
        (folder/'foundation.ini').write_text(f'NavigationMap={enabled}\nNavigationMapObjective={int(objective)}\nJournal=1\n'
            f'ExperimentalFieldWide={int(width==400)}\nEnhancedPixels=0\nFastMenus=0\nBattleInfo=0\n',encoding='utf-8')
        (folder/'input.txt').write_text(script,encoding='utf-8')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',
            SNESRECOMP_FOUNDATION_MAP_INPUT_TEST=method,SNESRECOMP_FOUNDATION_MAP_TRACE=str(folder/'map.csv'),
            SNESRECOMP_FOUNDATION_JOURNAL_TRACE=str(folder/'journal.csv'),SNESRECOMP_HOTKEY_TRACE='1',
            SNESRECOMP_STATE_TRACE=str(folder/'state.csv'),SNESRECOMP_FOUNDATION_TRACE=str(folder/'guest-input.csv'),
            SNESRECOMP_DUMP_DIR=str(folder/'dump'),SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE=','.join(map(str,capture_frames)),
            SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(folder/'capture'),SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FOUNDATION_FAST_MENUS='0',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
            SNESRECOMP_FOUNDATION_WIDE=str(int(width==400)),SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(int(width==400)))
        if original_view:env['SNESRECOMP_FOUNDATION_NAVIGATION_MAP']='0'
        if rollback:
            env.update(SNESRECOMP_OVERLAY_SELFTEST='80',SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1',
                       SNESRECOMP_OVERLAY_SELFTEST_LOADAT='150',SNESRECOMP_RUN_FRAMES='200')
        command=[str(local_exe),'--no-launcher','--rom',str(source['rom']),'--resume-state',str(folder/'resume.state'),
                 '--script',str(folder/'input.txt')]
        with (folder/'host.log').open('wb') as log:
            result=subprocess.run(command,cwd=folder,env=env,stdout=log,stderr=log,timeout=50,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log=(folder/'host.log').read_text(encoding='utf-8',errors='replace')
        rows=list(csv.DictReader((folder/'map.csv').open()))
        journal=list(csv.DictReader((folder/'journal.csv').open()))
        anchor=re.search(r"Config/saves anchored to '([^\r\n']+)'",log)
        runchecks={'exit_zero':result.returncode==0,'copied_exe_exact':sha(local_exe)==original['exe'],
                   'copied_checkpoint_exact':resume_initial==sha(state) and sha(folder/'seed.state')==sha(state),
                   'checkpoint_loaded':'resume state loaded:' in log,
                   'isolated_profile_anchor':bool(anchor and Path(anchor[1]).resolve()==folder),
                   'map_trace_exists':bool(rows),'legacy_l3_journal_remains_hidden':bool(journal) and all(int(r['visible'])==0 for r in journal)}
        if method.startswith('pad'):
            runchecks['actual_virtual_controller']='virtual pad attached' in log
            input_rows=list(csv.DictReader((folder/'guest-input.csv').open()))
            # Runtime runner input word bit2 is Select (not the keyboard-local
            # button layout); compare the actual SNES current input state.
            runchecks['map_modifier_never_forwards_guest_select']=bool(input_rows) and all(not int(r['input'])&4 for r in input_rows)
        for key,value in runchecks.items():checks[name+'_'+key]=value
        report['runs'][name]={'profile':str(folder),'exit':result.returncode,'checkpoint_sha256':sha(state),
                              'method':method,'width':width,'map_enabled':enabled,'objective_enabled':objective,'original_view_override':original_view,
                              'private_resume_consumed':not (folder/'resume.state').exists(),
                              'frame_count':len(rows),'ready_frames':sum(int(r['ready']) for r in rows),
                              'max_samples_per_frame':max((int(b['samples'])-int(a['samples']) for a,b in zip(rows,rows[1:])),default=0),
                              'max_generations':max((int(r['generations']) for r in rows),default=0)}
        return folder,rows

    def captured(folder,frame,width):
        return (folder/'capture'/f'frame-{frame}-{width}x224.bgrx').read_bytes()

    def compare(label,off,on,width,tags,open_expected=True):
        left,right=off[0],on[0]
        count=0
        for tag in tags:
            for ext in EXTENSIONS:
                lp,rp=left/'dump'/f'{tag}.{ext}',right/'dump'/f'{tag}.{ext}'
                value=lp.exists() and rp.exists() and lp.read_bytes()==rp.read_bytes()
                checks[label+'_'+tag+'_'+ext+'_guest_parity']=value;count+=1
        opened=captured(right,60,width);original=captured(left,60,width)
        checks[label+'_open_surface_changes']=opened!=original if open_expected else opened==original
        checks[label+'_closed_surface_restored']=captured(left,180,width)==captured(right,180,width)
        checks[label+'_actual_cpu_register_and_wram_trace_parity']=(left/'state.csv').read_bytes()==(right/'state.csv').read_bytes()
        if open_expected:
            panel_left=(width-240)//2
            checks[label+'_panel_bounds_exact']=all(original[(y*width+x)*4:(y*width+x+1)*4]==opened[(y*width+x)*4:(y*width+x+1)*4]
                for y in range(224) for x in range(width) if not(panel_left<=x<panel_left+240 and 14<=y<210))
            checks[label+'_map_ready_on_open']=any(int(r['visible']) and int(r['ready']) and int(r['frame'])<=60 for r in on[1])
        checks[label+'_per_frame_sampling_bounded']=report['runs'][right.name]['max_samples_per_frame']<=1024
        report['comparisons'].append({'name':label,'guest_components':count,'width':width,'tags':tags})

    for label,state,method,width,script in [
        ('field-keyboard',source['field-state'],'keyboard',256,simple),
        ('world-pad',source['world-state'],'pad',400,simple),
        ('world-moving-keyboard',source['world-state'],'keyboard',400,move)]:
        off=run(label+'-off',state,0,method,width,script)
        on=run(label+'-on',state,1,method,width,script)
        tags=['open','closed']+(['walk'] if script==move else [])
        compare(label,off,on,width,tags)
        rows=on[1]; transitions=[];last=0
        for r in rows:
            val=int(r['visible'])
            if val!=last:transitions.append(val);last=val
        checks[label+'_once_per_press']=transitions==[1,0]
        for tag in tags:
            if tag=='closed':continue
            ram=(on[0]/'dump'/f'{tag}.wram.bin').read_bytes()
            width_pixels,height_pixels=ram[0x46d]*256,ram[0x46e]*256
            px=int.from_bytes(ram[0x2ad:0x2af],'little',signed=True)+(ram[0x4001]&0xf0)
            py=int.from_bytes(ram[0x2af:0x2b1],'little',signed=True)+(ram[0x4002]&0xf0)
            if ram[0x407]:px%=width_pixels;py%=height_pixels
            initial_info=json.loads((on[0]/'dump/open.info.json').read_text())
            tag_info=json.loads((on[0]/'dump'/f'{tag}.info.json').read_text())
            frame=60+int(tag_info['frame'])-int(initial_info['frame'])
            row=next((r for r in rows if int(r['frame'])==frame),None)
            checks[label+'_'+tag+'_original_player_anchor']=bool(row and int(row['player_valid']) and (int(row['player_x']),int(row['player_y']))==(px,py))
        if script==move:
            checks[label+'_live_player_marker_moves']=any(int(r['player_x'])!=int(rows[59]['player_x']) for r in rows if 61<=int(r['frame'])<=76 and int(r['player_valid']))
    override=run('original-view-map-override',source['field-state'],1,'keyboard',256,original_view=True)
    field_off=out/'field-keyboard-off'
    checks['original_view_override_hides_map']=all(int(r['enabled'])==0 and int(r['visible'])==0 for r in override[1])
    checks['original_view_surface_original']=captured(override[0],60,256)==captured(field_off,60,256)

    world_folder=out/'world-pad-on'
    world_ram=(world_folder/'dump/open.wram.bin').read_bytes()
    # Verified chapter5 journal route is destination85. Derive its point from
    # the actual original selected world exits; no copied host marker table.
    checks['objective_fixture_original_stage5_scene0']=world_ram[0x5372]==5 and int.from_bytes(world_ram[0x40e:0x410],'little')==0
    point=original_objective(source['rom'].read_bytes(),world_ram,85)
    cw,ch=224,point['world_height']*224//point['world_width']
    if ch>128:ch=128;cw=point['world_width']*128//point['world_height']
    left=80+8+(224-cw)//2;top=14+38+(128-ch)//2
    mx=max(left+2,min(left+cw-3,left+point['world_x']*cw//point['world_width']))
    my=max(top+2,min(top+ch-3,top+point['world_y']*ch//point['world_height']))
    pin=[(mx+dx,my+dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]
    def ink(frame,color,folder=world_folder):
        pixels=captured(folder,frame,400)
        return all(pixels[(y*400+x)*4:(y*400+x)*4+3]==color for x,y in pin)
    checks['native_original_town_cyan_at_verified_entrance']=ink(59,bytes.fromhex('efe667'))
    checks['native_current_objective_pink_at_verified_entrance']=ink(60,bytes.fromhex('e986ff'))
    checks['native_objective_same_phase_at76']=ink(76,bytes.fromhex('e986ff'))
    point.update(capture_pixel=[mx,my],blink_hidden_frame=59,blink_visible_frame=60)
    report['original_objective_pixel_oracle']=point
    objective_off=run('world-objective-off',source['world-state'],1,'pad',400,objective=False)
    checks['optional_objective_hidden_keeps_verified_town_cyan']=ink(60,bytes.fromhex('efe667'),objective_off[0])
    checks['optional_objective_hidden_guest_cpu_parity']=(world_folder/'state.csv').read_bytes()==(objective_off[0]/'state.csv').read_bytes()
    checks['optional_objective_hidden_preserves_player_anchor']=any(int(r['ready']) and int(r['player_valid']) for r in objective_off[1])

    warm_off=run('warm-reopen-off',source['field-state'],0,'keyboard-reopen',256,warm)
    warm_on=run('warm-reopen-on',source['field-state'],1,'keyboard-reopen',256,warm)
    for tag in ['open','closed','reopened','stable']:
        for ext in EXTENSIONS:
            checks['warm_'+tag+'_'+ext+'_guest_parity']=(warm_off[0]/'dump'/f'{tag}.{ext}').read_bytes()==(warm_on[0]/'dump'/f'{tag}.{ext}').read_bytes()
    checks['warm_actual_cpu_trace_parity']=(warm_off[0]/'state.csv').read_bytes()==(warm_on[0]/'state.csv').read_bytes()
    warm_rows={int(r['frame']):r for r in warm_on[1]}
    checks['warm_closed_capture_original']=captured(warm_off[0],120,256)==captured(warm_on[0],120,256)
    checks['warm_native_reopen_immediately_ready']=all(int(warm_rows[131][v]) for v in ['visible','eligible','ready'])
    checks['warm_native_reopen_zero_terrain_samples']=warm_rows[130]['samples']==warm_rows[131]['samples']
    checks['warm_native_reopen_same_terrain_generation']=warm_rows[130]['generations']==warm_rows[131]['generations']
    checks['warm_native_reopen_surface_visible']=captured(warm_off[0],131,256)!=captured(warm_on[0],131,256)
    checks['warm_native_graphics_refresh_preserves_ready_front']=all(int(r['ready']) for f,r in warm_rows.items() if 131<=f<=210)
    checks['warm_native_terrain_sampling_bounded']=report['runs']['warm-reopen-on']['max_samples_per_frame']<=1024
    changes=[];previous=0
    for row in warm_on[1]:
        current=int(row['visible'])
        if current!=previous:changes.append(current);previous=current
    checks['warm_native_three_explicit_toggles']=changes==[1,0,1]

    rollback_off=run('restore-off',source['field-state'],0,'keyboard-open',256,restore,rollback=True)
    rollback_on=run('restore-on',source['field-state'],1,'keyboard-open',256,restore,rollback=True)
    compare('restore',rollback_off,rollback_on,256,['open','walk','before','restored'])
    checks['actual_save_and_load_issued']=all('[overlay_selftest] load issued' in (r[0]/'host.log').read_text(errors='replace') for r in [rollback_off,rollback_on])
    checks['restore_keeps_derived_map_hidden']=all(int(r['visible'])==0 for r in rollback_on[1] if int(r['frame'])>=151)
    saved=rollback_on[0]/'saves/save0.sav'
    checks['copied_save_exists']=saved.exists()
    if saved.exists():
        saved_off=rollback_off[0]/'saves/save0.sav'
        checks['complete_checkpoint_guest_parity']=saved_off.exists() and saved_off.read_bytes()==saved.read_bytes()
        cold=run('cold-checkpoint',saved,1,'keyboard',256)
        checks['cold_map_starts_hidden']=int(cold[1][0]['visible'])==0
        checks['cold_map_derives_fresh_ready']=any(int(r['ready']) and int(r['player_valid']) for r in cold[1] if 45<=int(r['frame'])<=60)
    checks['all_source_inputs_unchanged']=all(sha(path)==original[k] for k,path in source.items())
    report.update(status='pass' if all(checks.values()) else 'fail',source_inputs={k:{'path':str(v),'sha256':original[k]} for k,v in source.items()},
                  checker_sha256=sha(Path(__file__)),
                  limits=['Actual SDL keyboard and indexed virtual controller; no physical-controller certification',
                          'Finite copied fixtures; staged original world producer separate from natural acquisition/campaign',
                          'Silent forensic guest/map/input/restore proof; audio and paced native benefit are separate',
                          'Current-area terrain, original anchor and only separately verified town/objective metadata; no visited history'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':len(checks),'runs':len(report['runs']),'failed':[k for k,v in checks.items() if not v],'report':str(out/'report.json')}))
    return 0 if report['status']=='pass' else 1


if __name__=='__main__':
    raise SystemExit(main())
