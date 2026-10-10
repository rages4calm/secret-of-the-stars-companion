"""Finite explicit-fixture journal lead/input/composition/rollback qualification.

Owned ROM and checkpoints remain private and byte-identical. Optional manufactured
state controls are explicitly recorded, not original campaign or award evidence.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,re,shutil,struct,subprocess
from stage_foundation_checkpoint import stage,wram_offset

ROOT=Path(__file__).resolve().parents[1]
GUEST=('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','fb.bgrx','regs.json')
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def font_oracle(runtime):
    source=(runtime/'runner/src/snes_overlay_draw.c').read_text()
    body=re.search(r'FONT8\[59\]\[8\]\s*=\s*\{(.*?)\n\};',source,re.S)
    if not body:raise ValueError('Unsupported font oracle source')
    values=[int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)',body.group(1))]
    if len(values)!=59*8:raise ValueError('Unsupported font table length')
    return [values[i:i+8] for i in range(0,len(values),8)]

def expected_card(background,font,lead,groups):
    data=bytearray(background)
    def pixel(x,y,color):struct.pack_into('<I',data,(y*256+x)*4,color)
    for y in range(6,81):
        for x in range(8,248):pixel(x,y,0xff080e1c)
    for x in range(8,248):pixel(x,6,0xff809bc8);pixel(x,80,0xff809bc8)
    for y in range(6,81):pixel(8,y,0xff809bc8);pixel(247,y,0xff809bc8)
    lines=[(11,'JOURNAL - HOTKEY: CLOSE',0xffffdf78)]
    if lead==3:lines += [(29,'Aris: Jeep Volcano',0xfff0f3fa),(45,"Defeat Homncruse's follower",0xfff0f3fa),(57,'STARCREST: HELD NOW' if groups else 'Nearby mountain entrance',0xfff0f3fa)]
    elif lead==2:lines += [(29,'Bosen: gather allies',0xfff0f3fa),(45,'to build a town',0xfff0f3fa),(57,'STARCREST: HELD NOW' if groups else 'Find your fellow allies',0xfff0f3fa)]
    elif groups:lines += [(29,'STARCREST: HELD NOW',0xfff0f3fa),(45,'In both party packs' if groups==3 else 'In one party pack',0xfff0f3fa),(57,'In your pack now',0xfff0f3fa)]
    elif lead==1:lines += [(29,'Seek the Crest of Stars',0xfff0f3fa),(45,'David: somewhere in',0xfff0f3fa),(57,'the mountain',0xfff0f3fa)]
    else:lines += [(29,'No lead recorded for',0xfff0f3fa),(45,'this chapter.',0xfff0f3fa)]
    for y,text,color in lines:
        for i,c in enumerate(text.upper()):
            glyph=font[ord(c)-32 if 32<=ord(c)<=90 else ord('?')-32]
            for dy,row in enumerate(glyph):
                for dx in range(8):
                    if row & (1<<dx):pixel(14+i*8+dx,y+dy,color)
    return bytes(data)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('exe','rom','before-state','after-state','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cc',type=Path,default=Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
    p.add_argument('--runtime',type=Path,help='Exact candidate runtime tree, for font oracle and pure-header compilation')
    p.add_argument('--pennon-before-state',type=Path,help='Optional original pre-award stage-zero checkpoint')
    p.add_argument('--pennon-after-state',type=Path,help='Optional original post-award stage-zero checkpoint')
    a=p.parse_args()
    a.exe=a.exe.resolve(strict=True);a.rom=a.rom.resolve(strict=True)
    a.before_state=a.before_state.resolve(strict=True);a.after_state=a.after_state.resolve(strict=True)
    if bool(a.pennon_before_state)!=bool(a.pennon_after_state):
        raise ValueError('Supply both Pennon checkpoints together')
    pennon_inputs=[]
    if a.pennon_before_state:
        a.pennon_before_state=a.pennon_before_state.resolve(strict=True)
        a.pennon_after_state=a.pennon_after_state.resolve(strict=True)
        pennon_inputs=[a.pennon_before_state,a.pennon_after_state]
    out=a.output.resolve()
    if out.exists() or any(out==path or out in path.parents for path in (a.exe,a.rom,a.before_state,a.after_state)):
        raise ValueError('Output must be fresh and separate from input files')
    if sha(a.rom)!=ROM_SHA:raise ValueError('Unsupported original ROM')
    if a.runtime:a.runtime=a.runtime.resolve(strict=True)
    else:
        options=[parent/'snesrecomp' for parent in a.exe.parents]+[ROOT/'local/upstream/snesrecomp']
        a.runtime=next((r for r in options if (r/'runner/src/snes_overlay_draw.c').is_file()),None)
        if a.runtime is None:raise ValueError('Pass --runtime with the exact candidate runtime tree')
    before=a.before_state.read_bytes();after=a.after_state.read_bytes()
    br=before[wram_offset(before):wram_offset(before)+0x20000]
    ar=after[wram_offset(after):wram_offset(after)+0x20000]
    if br[0x20]!=1 or ar[0x20]!=1 or br[0x5372]!=0 or ar[0x5372]!=1:
        raise ValueError('Expected explicit field-mode stage-zero and stage-one checkpoints')
    if ar[0x5373:0x53b3]!=b'\xff'*64 or ar[0x4ba:0x4bc]!=bytes((0,32)):
        raise ValueError('After-state must have both original inventories empty')
    font=font_oracle(a.runtime)
    if pennon_inputs:
        original_pennon=[]
        for state in pennon_inputs:
            data=state.read_bytes();ram=data[wram_offset(data):wram_offset(data)+0x20000]
            if ram[0x20]!=1 or ram[0x5372]!=0:
                raise ValueError('Pennon checkpoints must be original field-mode stage zero')
            original_pennon.append(ram)
        if original_pennon[0][0x5360]&2 or not original_pennon[1][0x5360]&2:
            raise ValueError('Expected Pennon bit02 absent before and present after')
    protected={path:sha(path) for path in (a.exe,a.rom,a.before_state,a.after_state,*pennon_inputs,ROOT/'native/foundation/src/foundation_journal.h',ROOT/'native/foundation/src/foundation_journal.c',a.runtime/'runner/src/snes_overlay_draw.c')}
    out.mkdir(parents=True);(out/'runs').mkdir();(out/'staged').mkdir()
    checks={};cases={};receipts={}
    def check(name,value):
        checks[name]=bool(value)
        if not value:
            (out/'failure.json').write_text(json.dumps({'passed':False,'failed_check':name,'checks':checks,'cases':cases},indent=2)+'\n')
            raise AssertionError(name)
    unit=out/'stage-unit.c'
    unit.write_text('#include "foundation_journal.h"\n#include <stdio.h>\nint main(void){unsigned n=0;'
        'for(unsigned s=0;s<256;s++)for(unsigned f=0;f<256;f++){unsigned e=s==1?2:(s==0?(f&2?3:(f&0x40?1:0)):0);'
        'if(FoundationJournalLead(s,f)!=e||FoundationJournalHasLead(s,f)!=(e!=0))return 1;n+=2;}'
        'printf("{\\"passed\\":true,\\"checks\\":%u}\\n",n);return 0;}\n')
    compiled=subprocess.run([str(a.cc),str(unit),'-I',str(ROOT/'native/foundation/src'),'-I',str(a.runtime/'runner/src/desktop'),'-o',str(out/'stage-unit.exe')],capture_output=True,text=True)
    (out/'stage-unit.log').write_text(compiled.stdout+compiled.stderr)
    check('pure_predicate_compiles',compiled.returncode==0)
    tested=subprocess.run([str(out/'stage-unit.exe')],capture_output=True,text=True)
    check('all256stages_all256flags_lead_and_boolean',tested.returncode==0)
    pure=json.loads(tested.stdout)
    def manufactured(name,source,edits):
        receipt=stage(source,out/'staged'/name,edits,'Manufactured host-card/predicate control; not original campaign progression or item award.',out)
        receipts[name]=receipt;return Path(receipt['checkpoint'])
    first=manufactured('stage1-first-pack',a.after_state,['5373=ff:40','04ba=00:01'])
    both=manufactured('stage1-both-packs',first,['5393=ff:40','04bb=20:21'])
    david=manufactured('stage0-david-bit',a.before_state,[f'5360={br[0x5360]:02x}:{br[0x5360]|64:02x}'])
    later=manufactured('other-stage',a.after_state,['5372=01:02'])
    stage0_first=manufactured('stage0-first-pack',a.before_state,['5373=ff:40','04ba=00:01'])
    stage0_both=manufactured('stage0-both-packs',stage0_first,['5393=ff:40','04bb=20:21'])
    later_first=manufactured('other-stage-first-pack',first,['5372=01:02'])
    config=('[Graphics]\nRenderer=software\nVSync=0\nNewRenderer=1\nWidescreen=0\n[Sound]\nEnableAudio=0\n'
        '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
        '[KeyMap]\nJournal=J\nTurbo=None\nMovementBoost=None\nBattleInfo=None\nReset=Ctrl+R\n'
        '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nJournal=L3\n'
        'Controls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
        '[Controller]\nSourceP1=2\nSourceP2=0\n')
    def run(name,state,enabled=1,method='keyboard',capture=60,load=None,original=False):
        d=out/'runs'/name;d.mkdir();(d/'dump').mkdir()
        shutil.copy2(a.exe,d/'game.exe');shutil.copy2(state,d/'resume.state')
        (d/'config.ini').write_text(config.replace('Journal=J\n','Journal=I\n') if method=='pad' else config)
        (d/'foundation.ini').write_text('Journal=1\nEnhancedPixels=0\nBattleInfo=0\nFastMenus=0\n')
        (d/'input.txt').write_text('wait 60\ndump shown\nwait 90\ndump hidden\nquit\n')
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',
            SNESRECOMP_RUN_FRAMES='300',SNESRECOMP_DUMP_DIR=str(d/'dump'),SNESRECOMP_FOUNDATION_JOURNAL=str(0 if original else enabled),
            SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST=method,SNESRECOMP_FOUNDATION_JOURNAL_TRACE=str(d/'journal.csv'),
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(d/'present.bgrx'),SNESRECOMP_FOUNDATION_CAPTURE_AT=str(capture),
            SNESRECOMP_FOUNDATION_WIDE='0',SNESRECOMP_FOUNDATION_WIDE_ACTORS='0',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',
            SNESRECOMP_FOUNDATION_FAST_MENUS='0',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FOUNDATION_HD_UI='0',SNESRECOMP_FOUNDATION_XP_PERCENT='100',SNESRECOMP_FOUNDATION_GOLD_PERCENT='100',SNESRECOMP_FOUNDATION_MOVEMENT_PERCENT='100')
        if method=='pad':env.update(SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST='none',SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST='pad',SNESRECOMP_FOUNDATION_HOTKEY_OVERLAY_TEST='journal')
        if load:
            (d/'saves').mkdir();shutil.copy2(load,d/'saves/save0.sav');env['SNESRECOMP_OVERLAY_SELFTEST_LOADAT']='80'
        with (d/'host.log').open('w') as log:
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(a.rom),'--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,stdout=log,stderr=log,timeout=35,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        log=(d/'host.log').read_text(errors='replace');rows=list(csv.DictReader((d/'journal.csv').open()))
        check(name+'_finite_native_resume',result.returncode==0 and 'resume state loaded:' in log and not (d/'resume.state').exists())
        check(name+'_actual_private_anchor',"Config/saves anchored to '"+str(d)+"\\'" in log)
        check(name+'_copied_exe_exact',sha(d/'game.exe')==protected[a.exe])
        cases[name]={'source_checkpoint_sha256':sha(state),'shown':log.count('journal shown'),'hidden':log.count('journal hidden'),
            'virtual_pad_attached':'virtual pad attached' in log,'lead_values':sorted({int(r['lead_kind']) for r in rows}),
            'source':'manufactured control' if state.is_relative_to(out/'staged') else 'explicit supplied original-event checkpoint',
            'method':method,'enabled':enabled,'original_view_override':original}
        return d,rows
    def parity(l,r):return all((l/'dump'/f'{prefix}.{ext}').read_bytes()==(r/'dump'/f'{prefix}.{ext}').read_bytes() for prefix in ('shown','hidden') for ext in GUEST)
    def surface(d):return (d/'present.bgrx').read_bytes()
    results={}
    before_lead=3 if br[0x5360]&2 else 1 if br[0x5360]&64 else 0
    fixtures={'before':(a.before_state,before_lead,0),'stage1':(a.after_state,2,0),'david':(david,3 if br[0x5360]&2 else 1,0),
        'stage1-first':(first,2,1),'stage1-both':(both,2,3),'later':(later,0,0),
        'stage0-first':(stage0_first,before_lead,1),
        'stage0-both':(stage0_both,before_lead,3),'later-first':(later_first,0,1)}
    if pennon_inputs:
        before_p,after_p=original_pennon
        pflags=after_p[0x5360]
        with_david=manufactured('pennon-with-david',a.pennon_after_state,[f'5360={pflags:02x}:{pflags|64:02x}'])
        cursor=after_p[0x4ba]
        if cursor>=32 or after_p[0x5373+cursor]!=0xff:
            raise ValueError('Pennon after-state needs a free first-party slot for possession control')
        ppack=manufactured('pennon-possession',a.pennon_after_state,[f'{0x5373+cursor:04x}=ff:40',f'04ba={cursor:02x}:{cursor+1:02x}'])
        plater=manufactured('pennon-later-stage',a.pennon_after_state,['5372=00:02'])
        fixtures.update({'pennon-before':(a.pennon_before_state,1 if before_p[0x5360]&64 else 0,0),
                         'pennon':(a.pennon_after_state,3,0),'pennon-david':(with_david,3,0),
                         'pennon-possession':(ppack,3,1),'pennon-later':(plater,0,0)})
    for name,(state,lead,groups) in fixtures.items():
        off,_=run(name+'-off',state,0);on,rows=run(name+'-on',state)
        check(name+'_all_guest_register_capture_parity',parity(off,on))
        check(name+'_derived_lead_first_frame',int(rows[0]['lead_kind'])==lead and cases[name+'-on']['lead_values']==[lead])
        check(name+'_keyboard_once_per_press',cases[name+'-on']['shown']==cases[name+'-on']['hidden']==1)
        check(name+'_exact_font_oracle_copy',surface(on)==expected_card(surface(off),font,lead,groups))
        check(name+'_card_contained',all(surface(off)[i:i+4]==surface(on)[i:i+4] for y in range(224) for x in range(256) if not (8<=x<248 and 6<=y<81) for i in [(y*256+x)*4]))
        results[name]=on
    pad_off,_=run('stage1-pad-off',a.after_state,0,'pad');pad,rows=run('stage1-pad-on',a.after_state,method='pad')
    check('indexed_virtual_pad_real_toggle',cases['stage1-pad-on']['virtual_pad_attached'] and cases['stage1-pad-on']['shown']==cases['stage1-pad-on']['hidden']==1)
    check('pad_guest_register_parity',parity(pad_off,pad))
    check('keyboard_pad_same_card_and_guest',parity(results['stage1'],pad) and surface(results['stage1'])==surface(pad))
    closed_off,_=run('closed-off',a.after_state,0,capture=150);closed,_=run('closed-on',a.after_state,capture=150)
    check('closed_card_restores_exact_host_surface',surface(closed_off)==surface(closed) and parity(closed_off,closed))
    cold,rows=run('cold-stage1',a.after_state)
    check('cold_stage1_first_frame_and_surface',int(rows[0]['lead_kind'])==2 and parity(cold,results['stage1']) and surface(cold)==surface(results['stage1']))
    rollback_off,_=run('rollback-off',a.after_state,0,capture=100,load=a.before_state)
    rollback,rows=run('rollback-on',a.after_state,capture=100,load=a.before_state)
    check('actual_rollback_removes_bosen_lead',int(rows[0]['lead_kind'])==2 and all(int(r['lead_kind'])!=2 for r in rows if int(r['frame'])>=81))
    check('actual_checkpoint_load_issued','[overlay_selftest] load issued' in (rollback/'host.log').read_text())
    check('rollback_guest_register_parity',parity(rollback_off,rollback))
    check('rollback_closes_and_next_press_reopens',cases['rollback-on']['shown']==2 and cases['rollback-on']['hidden']==0 and any(81<=int(r['frame'])<=89 and int(r['visible'])==0 for r in rows))
    check('rollback_card_has_no_stale_bosen_copy',surface(rollback)==expected_card(surface(rollback_off),font,before_lead,0))
    original,rows=run('original-view-disabled',a.after_state,original=True)
    check('original_view_override_disables_card',all(int(r['enabled'])==int(r['visible'])==0 for r in rows) and surface(original)==surface(out/'runs/stage1-off') and parity(original,out/'runs/stage1-off'))
    if pennon_inputs:
        poff,_=run('pennon-pad-off',a.pennon_after_state,0,'pad')
        ppad,rows=run('pennon-pad-on',a.pennon_after_state,method='pad')
        check('pennon_pad_real_toggle',cases['pennon-pad-on']['virtual_pad_attached'] and cases['pennon-pad-on']['shown']==cases['pennon-pad-on']['hidden']==1)
        check('pennon_pad_guest_and_keyboard_card',parity(poff,ppad) and parity(results['pennon'],ppad) and surface(results['pennon'])==surface(ppad))
        pcold,rows=run('pennon-cold',a.pennon_after_state)
        check('pennon_cold_current_state',int(rows[0]['lead_kind'])==3 and parity(pcold,results['pennon']) and surface(pcold)==surface(results['pennon']))
        proff,_=run('pennon-rollback-off',a.pennon_after_state,0,capture=100,load=a.pennon_before_state)
        pr,rows=run('pennon-rollback-on',a.pennon_after_state,capture=100,load=a.pennon_before_state)
        check('pennon_actual_rollback_removes_lead',int(rows[0]['lead_kind'])==3 and all(int(row['lead_kind'])!=3 for row in rows if int(row['frame'])>=81) and '[overlay_selftest] load issued' in (pr/'host.log').read_text())
        check('pennon_rollback_guest_exact',parity(proff,pr))
        check('pennon_rollback_clears_and_reopens',cases['pennon-rollback-on']['shown']==2 and any(81<=int(row['frame'])<=89 and int(row['visible'])==0 for row in rows))
        check('pennon_rollback_card_exact',surface(pr)==expected_card(surface(proff),font,fixtures['pennon-before'][1],0))
        pv,rows=run('pennon-original-view',a.pennon_after_state,original=True)
        check('pennon_original_view_exact',all(int(row['enabled'])==int(row['visible'])==0 for row in rows) and parity(pv,out/'runs/pennon-off') and surface(pv)==surface(out/'runs/pennon-off'))
        next_off,_=run('pennon-to-bosen-off',a.pennon_after_state,0,capture=100,load=a.after_state)
        next_on,rows=run('pennon-to-bosen-on',a.pennon_after_state,capture=100,load=a.after_state)
        check('chapter_restore_replaces_pennon_with_bosen',int(rows[0]['lead_kind'])==3 and all(int(row['lead_kind'])==2 for row in rows if int(row['frame'])>=81) and parity(next_off,next_on) and surface(next_on)==expected_card(surface(next_off),font,2,0))
    check('all_input_binary_rom_checkpoint_and_source_hashes_unchanged',all(sha(path)==digest for path,digest in protected.items()))
    from PIL import Image,ImageDraw
    contact=Image.new('RGB',(256*3,244*((len(fixtures)+2)//3)),'#080e1c');draw=ImageDraw.Draw(contact)
    for i,name in enumerate(fixtures):
        image=Image.frombytes('RGB',(256,224),surface(results[name]),'raw','BGRX');image.save(results[name]/'present.png')
        x,y=(i%3)*256,(i//3)*244;contact.paste(image,(x,y+20));draw.text((x+4,y+4),name,fill='white')
    contact.save(out/'journal-progression-cards.png')
    report={'passed':all(checks.values()),'executable_sha256':sha(a.exe),'rom_sha256':sha(a.rom),'checks':checks,'cases':cases,
        'protected_inputs':{str(k):v for k,v in protected.items()},'staging':receipts,'pure_predicate':pure,
        'limits':['Supplied private original-event checkpoints; natural route and event provenance must be documented separately.',
            'Manufactured inventory and later-stage controls are host/predicate tests, not original awards or campaign counts.',
            'Stage-zero Pennon and stage-one Bosen cards are current advice; no Crest completion, persistent history or exhaustive stage-entry claim.',
            'Real SDL keyboard/indexed virtual-controller events; physical controller and paced GPU/audio remain separate.',
            'Original View checks its launcher-equivalent Journal=0 override, not a new launcher route certification.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(checks),'native_runs':len(cases),'pure_checks':pure['checks'],'output':str(out)},indent=2))

if __name__=='__main__':main()
