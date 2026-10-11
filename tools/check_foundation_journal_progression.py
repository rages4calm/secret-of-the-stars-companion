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

def JournalGroups(ram):return sum(1<<pack for pack in range(2) if 0x40 in ram[0x5373+32*pack:0x5393+32*pack])

def font_oracle(runtime):
    source=(runtime/'runner/src/snes_overlay_draw.c').read_text()
    body=re.search(r'FONT8\[59\]\[8\]\s*=\s*\{(.*?)\n\};',source,re.S)
    if not body:raise ValueError('Unsupported font oracle source')
    values=[int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)',body.group(1))]
    if len(values)!=59*8:raise ValueError('Unsupported font table length')
    return [values[i:i+8] for i in range(0,len(values),8)]

def expected_card(background,font,lead,groups,ram=None,width=256,height=224):
    data=bytearray(background);left=(width-240)//2;top=(height-196)//2
    if len(data)!=width*height*4:raise ValueError('Unexpected host canvas dimensions')
    def pixel(x,y,color):
        if not (left<=x<left+240 and top<=y<top+196):raise AssertionError('Journal pixel escaped its panel')
        struct.pack_into('<I',data,(y*width+x)*4,color)
    def rectangle(x,y,w,h,color,stroke=False):
        for dy in range(h):
            for dx in range(w):
                if not stroke or dx in (0,w-1) or dy in (0,h-1):pixel(left+x+dx,top+y+dy,color)
    rectangle(0,0,240,196,0xff080e1c)
    rectangle(0,0,240,196,0xff809bc8,True)
    rectangle(2,2,236,192,0xff293a57,True)
    for row in (22,72,122):rectangle(8,row,224,1,0xff293a57)
    town_route=0
    if ram is not None and (ram[0x5372]==2 or ram[0x5372]==1 and ram[0x5360]&32):
        dog_groups=sum(1<<pack for pack in range(2) if 0x6d in ram[0x5373+32*pack:0x5393+32*pack])
        town_route=2 if dog_groups&(1<<bool(ram[0x4b6])) else 3 if dog_groups else 1
    if town_route:
        objective=("Stop Badbad's dog spell.",'Recover the Dog Pill.')
        route=('Badbad-House is in','the south part of town.')
        progress="Town's current plea"
        if town_route>=2:
            objective=('Return with the Dog Pill.' if town_route==2 else 'Switch to the Dog Pill pack.','Help the townspeople.')
            route=('Speak to the person who','asked you to stop Badbad.')
            progress='DOG PILL: CURRENT PACK' if town_route==2 else 'DOG PILL: OTHER PARTY PACK'
    elif lead==7:
        objective=("Seek Dynamite's help.",'Find a way to defeat Golan.')
        route=("Dynamite's laboratory is",'in the town Morgan entered.')
        progress='Current Dynamite route'
        # Original07BB FA01 precedes the6E award. FA03 precedes escort movement.
        # Flags and current item evidence are independent; this is not history.
        if ram is not None:
            weapon=sum(1<<pack for pack in range(2) if 0x6e in ram[0x5373+32*pack:0x5393+32*pack])
            flags=ram[0x5360]
            if (flags&0xc0)==0xc0 and (weapon or flags&0x10):
                if flags&0x10:
                    objective=('Find a way to defeat Golan.','Use Graviton against Golan.' if weapon else 'Graviton is not held now.')
                    route=("Dynamite's weapon advice:",'use Graviton against Golan.')
                else:
                    objective=('Take Dynamite to your town.','He asks for a laboratory.')
                    route=('Dynamite asks you to','take him to the new town.')
                active=bool(ram[0x4b6]&0x80)
                progress='GRAVITON: BOTH PACKS' if weapon==3 else 'GRAVITON: NOT HELD NOW' if not weapon else 'GRAVITON: CURRENT PACK' if weapon&(1<<active) else 'GRAVITON: OTHER PACK'
    elif lead==6:
        objective=('Find builders and farmers.','Help build the new town.')
        route=('Talk to Uncle Save at home.','Ask people about town help.')
        progress='Current town-building lead'
        if ram is not None and ram[0x5360]&1:
            route=('Find architects to build','and farmers to grow crops.')
            progress="Uncle Save's current advice"
        if ram is not None and ram[0x5360]&32:
            objective=('Find a way to defeat Golan.','Ask Dynamite for help.')
            route=('Morgan offers town access.','Bring 100 gold for entry.')
            progress="Morgan's current advice"
    elif lead==4:
        objective=('Rescue the kidnapped kids.','Face the Ringo Brothers.')
        route=("Speak to the town's mayor.",'Ask about the Ringo Bros.')
        progress="Town's current chapter"
        if ram is not None and ram[0x5360]&128:
            route=("Ringo Bros' hide-out lies",'south of the mayor.')
            progress="Mayor's current advice"
    elif lead==3:
        objective=("Defeat Homncruse's follower",'in Jeep Volcano.')
        route=('Enter the nearby mountain.','Kustera can fight for you.')
        progress='Aris advice: Pennon'
    elif lead==2:
        objective=('Find Aqutallion allies.','Find Kustera; build a town.')
        route=('Bosen asks you to find','allies for the new town.')
        progress="Bosen's current advice"
        if ram is not None and ram[0x5372]==1 and ram[0x5360]&0x10:
            route=('Uncle Save: Likado is empty.','Gather allies for the town.')
    elif lead==1:
        objective=('Seek the Crest of Stars.',"Follow David's lead.")
        route=('David: somewhere in','the mountain.')
        progress="David's current advice"
    else:
        objective=('No current lead recorded.','Talk to people for clues.')
        route=('No route recorded for','the current chapter.')
        progress='Current party packs'
    used=[sum(b!=255 for b in ram[0x5373+pack*32:0x5393+pack*32]) for pack in range(2)] if ram is not None else [int(bool(groups&1)),int(bool(groups&2))]
    crest='STARCREST: BOTH PACKS' if groups==3 else 'STARCREST: ONE PACK' if groups else 'STARCREST: NOT HELD NOW'
    lines=[(8,'QUEST JOURNAL',0xffffdf78),(28,'CURRENT OBJECTIVE',0xffffdf78),
        (42,objective[0],0xfff0f3fa),(54,objective[1],0xfff0f3fa),(78,'ROUTE AND ADVICE',0xffffdf78),
        (92,route[0],0xfff0f3fa),(104,route[1],0xfff0f3fa),(128,'CURRENT PROGRESS',0xffffdf78),
        (142,progress,0xfff0f3fa),(154,f'PACKS: {used[0]}/32 AND {used[1]}/32',0xffa7b9d8),
        (166,crest,0xffa7b9d8),(184,'GAME RUNNING',0xffffdf78)]
    for y,text,color in lines:
        if len(text)>28 or y+8>192:raise AssertionError('Journal text exceeds layout bounds')
        for i,c in enumerate(text.upper()):
            glyph=font[ord(c)-32 if 32<=ord(c)<=90 else ord('?')-32]
            for dy,row in enumerate(glyph):
                for dx in range(8):
                    if row & (1<<dx):pixel(left+8+i*8+dx,top+y+dy,color)
    return bytes(data)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('exe','rom','before-state','after-state','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cc',type=Path,default=Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
    p.add_argument('--runtime',type=Path,help='Exact candidate runtime tree, for font oracle and pure-header compilation')
    p.add_argument('--pennon-before-state',type=Path,help='Optional original pre-award stage-zero checkpoint')
    p.add_argument('--pennon-after-state',type=Path,help='Optional original post-award stage-zero checkpoint')
    p.add_argument('--likado-state',type=Path,help='Optional original stage-one Uncle Save clue checkpoint')
    for name in ('badbad-state','dog-pill-state','returned-state','mayor-state','town-clue-state','morgan-state','dynamite-route-state'):
        p.add_argument('--'+name,type=Path,help='Optional explicitly staged original-event fixture; see its private source receipts')
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
    likado_inputs=[]
    if a.likado_state:
        a.likado_state=a.likado_state.resolve(strict=True);likado_inputs=[a.likado_state]
        data=a.likado_state.read_bytes();lr=data[wram_offset(data):wram_offset(data)+0x20000]
        if lr[0x20]!=1 or lr[0x5372]!=1 or not lr[0x5360]&0x10 or ar[0x5360]&0x10:
            raise ValueError('Expected original before/after stage-one clue bit10 evidence')
    town_inputs=[];town_rams={}
    for field in ('badbad_state','dog_pill_state','returned_state','mayor_state','town_clue_state','morgan_state','dynamite_route_state'):
        state=getattr(a,field)
        if state:
            state=state.resolve(strict=True);setattr(a,field,state);town_inputs.append(state)
            data=state.read_bytes();ram=data[wram_offset(data):wram_offset(data)+0x20000];town_rams[field]=ram
            if ram[0x20]!=1:raise ValueError('Town fixtures require original field mode')
            if field=='badbad_state' and not(ram[0x5372]==1 and ram[0x5360]&32):raise ValueError('Expected original stage1 advice bit20')
            if field=='dog_pill_state' and not(ram[0x5372]==2 and ram[0x5373]==0x6d and ram[0x4b6]==0):raise ValueError('Expected declared stage2 first-pack Dog Pill prerequisite')
            if field=='returned_state' and not(ram[0x5372]==3 and ram[0x5360]==0 and 0x6d not in ram[0x5373:0x53b3]):raise ValueError('Expected original2-to3 return outcome')
            if field=='mayor_state' and not(ram[0x5372]==3 and ram[0x5360]&128):raise ValueError('Expected stage3 original Mayor bit80 clue')
            if field=='town_clue_state' and not(ram[0x5372]==4 and ram[0x5360]&1):raise ValueError('Expected original chapter4 Uncle Save bit01 clue')
            if field=='morgan_state' and not(ram[0x5372]==4 and ram[0x5360]&32):raise ValueError('Expected original chapter4 Morgan bit20 clue')
            if field=='dynamite_route_state' and not(ram[0x5372]==5 and ram[0x5360]==0):raise ValueError('Expected original Morgan paid-entry chapter5 outcome')
    protected={path:sha(path) for path in (a.exe,a.rom,a.before_state,a.after_state,*pennon_inputs,*likado_inputs,*town_inputs,ROOT/'native/foundation/src/foundation_journal.h',ROOT/'native/foundation/src/foundation_journal.c',a.runtime/'runner/src/snes_overlay_draw.c')}
    out.mkdir(parents=True);(out/'runs').mkdir();(out/'staged').mkdir()
    checks={};cases={};receipts={}
    def check(name,value):
        checks[name]=bool(value)
        if not value:
            (out/'failure.json').write_text(json.dumps({'passed':False,'failed_check':name,'checks':checks,'cases':cases},indent=2)+'\n')
            raise AssertionError(name)
    unit=out/'stage-unit.c'
    unit.write_text('#include "foundation_journal.h"\n#include <stdio.h>\nint main(void){unsigned n=0;'
        'for(unsigned s=0;s<256;s++)for(unsigned f=0;f<256;f++){unsigned e=s==1?2:(s==2?5:(s==3?4:(s==4?6:(s==5?7:(s==0?(f&2?3:(f&0x40?1:0)):0)))));'
        'if(FoundationJournalLead(s,f)!=e||FoundationJournalHasLead(s,f)!=(e!=0)||FoundationJournalHasLikadoClue(s,f)!=(s==1&&(f&16)!=0)||FoundationJournalHasTownClue(s,f)!=(s==4&&(f&1)!=0)||FoundationJournalHasMorganClue(s,f)!=(s==4&&(f&32)!=0))return 1;n+=5;for(unsigned g=0;g<4;g++)for(unsigned p=0;p<2;p++){unsigned r=(s==2||(s==1&&(f&32)))?(g&(1u<<p)?2:(g?3:1)):0;unsigned d=r?(r>=2?58:67):s==3&&!(f&128)?59:s==5&&(f&0x50)?65535:(s==4&&(f&32))||s==5?85:65535;unsigned dy=s==5&&(f&0xc0)==0xc0?((f&16)?(g?2:3):(g?1:0)):0;if(FoundationJournalBadbadRoute(s,f,g,p)!=r||FoundationJournalDestination(s,f,g,p)!=d||FoundationJournalDynamiteRoute(s,f,g)!=dy)return 2;n+=3;}}'
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
    later=manufactured('other-stage',a.after_state,['5372=01:06'])
    stage0_first=manufactured('stage0-first-pack',a.before_state,['5373=ff:40','04ba=00:01'])
    stage0_both=manufactured('stage0-both-packs',stage0_first,['5393=ff:40','04bb=20:21'])
    later_first=manufactured('other-stage-first-pack',first,['5372=01:06'])
    config=('[Graphics]\nRenderer=software\nVSync=0\nNewRenderer=1\nWidescreen=0\n[Sound]\nEnableAudio=0\n'
        '[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
        '[KeyMap]\nJournal=J\nTurbo=None\nMovementBoost=None\nBattleInfo=None\nReset=Ctrl+R\n'
        '[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\nJournal=L3\n'
        'Controls=DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1\n'
        '[Controller]\nSourceP1=2\nSourceP2=0\n')
    def run(name,state,enabled=1,method='keyboard',capture=60,load=None,original=False,wide=False):
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
            SNESRECOMP_FOUNDATION_WIDE=str(int(wide)),SNESRECOMP_FOUNDATION_WIDE_ACTORS='0',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='0',
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
            'source':'manufactured control' if state.is_relative_to(out/'staged') else 'explicit staged item prerequisite; acquisition unqualified' if state==a.dog_pill_state else 'original event from documented staged prerequisites' if state in town_inputs else 'explicit supplied original-event checkpoint',
            'method':method,'enabled':enabled,'original_view_override':original,'wide':wide}
        return d,rows
    def parity(l,r):return all((l/'dump'/f'{prefix}.{ext}').read_bytes()==(r/'dump'/f'{prefix}.{ext}').read_bytes() for prefix in ('shown','hidden') for ext in GUEST)
    def surface(d):return (d/'present.bgrx').read_bytes()
    def oracle(d,lead,groups,load=False,wide=False):
        sample='hidden' if load else 'shown'
        ram=(d/'dump'/f'{sample}.wram.bin').read_bytes()
        return expected_card(surface(d),font,lead,groups,ram,width=400 if wide else 256)
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
        plater=manufactured('pennon-later-stage',a.pennon_after_state,['5372=00:06'])
        fixtures.update({'pennon-before':(a.pennon_before_state,1 if before_p[0x5360]&64 else 0,0),
                         'pennon':(a.pennon_after_state,3,0),'pennon-david':(with_david,3,0),
                         'pennon-possession':(ppack,3,1),'pennon-later':(plater,0,0)})
    if likado_inputs:
        fixtures['likado-clue']=(a.likado_state,2,JournalGroups(lr))
        wrong0=manufactured('stage0-clue-bit',a.before_state,[f'5360={br[0x5360]:02x}:{br[0x5360]|16:02x}'])
        wrong2=manufactured('stage6-clue-bit',later,['5360=00:10'])
        fixtures['stage0-clue-refused']=(wrong0,before_lead,0)
        fixtures['stage6-clue-refused']=(wrong2,0,0)
    if a.badbad_state:
        fixtures['badbad-advice']=(a.badbad_state,2,JournalGroups(town_rams['badbad_state']))
        wrong=manufactured('stage6-badbad-refused',a.badbad_state,['5372=01:06'])
        fixtures['stage6-badbad-refused']=(wrong,0,JournalGroups(town_rams['badbad_state']))
    if a.dog_pill_state:
        dog=a.dog_pill_state;ram=town_rams['dog_pill_state']
        removed=manufactured('dog-pill-removed',dog,['5373=6d:ff','04ba=01:00'])
        other=manufactured('dog-pill-other-pack',removed,['5393=ff:6d','04bb=20:21'])
        both_dog=manufactured('dog-pill-both-packs',dog,['5393=ff:6d','04bb=20:21'])
        wrong=manufactured('dog-pill-stage6-refused',dog,['5372=02:06'])
        fixtures.update({'dog-pill-current':(dog,5,JournalGroups(ram)),'dog-pill-removed':(removed,5,JournalGroups(ram)),
            'dog-pill-other':(other,5,JournalGroups(ram)),'dog-pill-both':(both_dog,5,JournalGroups(ram)),
            'dog-pill-stage6-refused':(wrong,0,JournalGroups(ram))})
    if a.returned_state:fixtures['town-returned']=(a.returned_state,4,JournalGroups(town_rams['returned_state']))
    if a.mayor_state:fixtures['mayor-clue']=(a.mayor_state,4,JournalGroups(town_rams['mayor_state']))
    for field,name,lead in (('town_clue_state','town-building-clue',6),('morgan_state','morgan-clue',6),('dynamite_route_state','dynamite-route',7)):
        state=getattr(a,field)
        if state:fixtures[name]=(state,lead,JournalGroups(town_rams[field]))
    if a.town_clue_state:
        ram=town_rams['town_clue_state']
        default=manufactured('chapter4-before-town-clue',a.town_clue_state,[f'5360={ram[0x5360]:02x}:00'])
        wrong=manufactured('chapter6-town-clue-refused',a.town_clue_state,['5372=04:06'])
        fixtures.update({'town-building-default':(default,6,JournalGroups(ram)),'chapter6-town-clue-refused':(wrong,0,JournalGroups(ram))})
    if a.morgan_state:
        ram=town_rams['morgan_state']
        both=manufactured('chapter4-both-clues',a.morgan_state,[f'5360={ram[0x5360]:02x}:{ram[0x5360]|1:02x}'])
        wrong=manufactured('chapter3-morgan-bit-refused',a.morgan_state,['5372=04:03'])
        fixtures.update({'morgan-priority':(both,6,JournalGroups(ram)),'chapter3-morgan-bit-refused':(wrong,4,JournalGroups(ram))})

    for name,(state,lead,groups) in fixtures.items():
        off,_=run(name+'-off',state,0);on,rows=run(name+'-on',state)
        check(name+'_all_guest_register_capture_parity',parity(off,on))
        check(name+'_derived_lead_first_frame',int(rows[0]['lead_kind'])==lead and cases[name+'-on']['lead_values']==[lead])
        check(name+'_keyboard_once_per_press',cases[name+'-on']['shown']==cases[name+'-on']['hidden']==1)
        check(name+'_exact_font_oracle_copy',surface(on)==oracle(off,lead,groups))
        check(name+'_card_contained',all(surface(off)[i:i+4]==surface(on)[i:i+4] for y in range(224) for x in range(256) if not (8<=x<248 and 14<=y<210) for i in [(y*256+x)*4]))
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
    check('rollback_card_has_no_stale_bosen_copy',surface(rollback)==oracle(rollback_off,before_lead,0,load=True))
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
        check('pennon_rollback_card_exact',surface(pr)==oracle(proff,fixtures['pennon-before'][1],0,load=True))
        pv,rows=run('pennon-original-view',a.pennon_after_state,original=True)
        check('pennon_original_view_exact',all(int(row['enabled'])==int(row['visible'])==0 for row in rows) and parity(pv,out/'runs/pennon-off') and surface(pv)==surface(out/'runs/pennon-off'))
        next_off,_=run('pennon-to-bosen-off',a.pennon_after_state,0,capture=100,load=a.after_state)
        next_on,rows=run('pennon-to-bosen-on',a.pennon_after_state,capture=100,load=a.after_state)
        check('chapter_restore_replaces_pennon_with_bosen',int(rows[0]['lead_kind'])==3 and all(int(row['lead_kind'])==2 for row in rows if int(row['frame'])>=81) and parity(next_off,next_on) and surface(next_on)==oracle(next_off,2,0,load=True))
    wide_names=['stage1','pennon' if pennon_inputs else 'david']
    if likado_inputs:wide_names.append('likado-clue')
    wide_names.extend(name for name in ('badbad-advice','dog-pill-current','dog-pill-other','town-returned','mayor-clue','town-building-clue','town-building-default','morgan-clue','morgan-priority','dynamite-route') if name in fixtures)
    for name in wide_names:
        state,lead,groups=fixtures[name]
        wide_off,_=run(name+'-wide-off',state,0,wide=True)
        wide_on,rows=run(name+'-wide-on',state,wide=True)
        check(name+'_wide400_actual_canvas',len(surface(wide_on))==400*224*4)
        check(name+'_wide400_guest_parity',parity(wide_off,wide_on))
        check(name+'_wide400_independent_font_layout',surface(wide_on)==oracle(wide_off,lead,groups,wide=True))
        check(name+'_wide400_contained',all(surface(wide_off)[i:i+4]==surface(wide_on)[i:i+4] for y in range(224) for x in range(400) if not (80<=x<320 and 14<=y<210) for i in [(y*400+x)*4]))
    if likado_inputs:
        lcold,rows=run('likado-cold',a.likado_state)
        check('likado_cold_original_current_state',int(rows[0]['stage'])==1 and int(rows[0]['flags'])&16 and parity(lcold,results['likado-clue']) and surface(lcold)==surface(results['likado-clue']))
        loff,_=run('likado-pad-off',a.likado_state,0,'pad');lpad,rows=run('likado-pad-on',a.likado_state,method='pad')
        check('likado_real_pad_toggle',cases['likado-pad-on']['virtual_pad_attached'] and cases['likado-pad-on']['shown']==cases['likado-pad-on']['hidden']==1)
        check('likado_real_pad_guest_surface',parity(loff,lpad) and parity(lpad,results['likado-clue']) and surface(lpad)==surface(results['likado-clue']))
        lroff,_=run('likado-rollback-off',a.likado_state,0,capture=100,load=a.after_state)
        lrback,rows=run('likado-rollback-on',a.likado_state,capture=100,load=a.after_state)
        check('likado_original_rollback_removes_clue',int(rows[0]['flags'])&16 and all(int(row['stage'])==1 and not int(row['flags'])&16 for row in rows if int(row['frame'])>=81) and '[overlay_selftest] load issued' in (lrback/'host.log').read_text())
        check('likado_rollback_guest_and_font_exact',parity(lroff,lrback) and surface(lrback)==oracle(lroff,2,0,load=True))
        lv,rows=run('likado-original-view',a.likado_state,original=True)
        check('likado_original_view_exact',all(int(row['enabled'])==int(row['visible'])==0 for row in rows) and parity(lv,out/'runs/likado-clue-off') and surface(lv)==surface(out/'runs/likado-clue-off'))
    for name in ('badbad-advice','dog-pill-current','town-returned','mayor-clue','town-building-clue','morgan-clue','dynamite-route'):
        if name not in fixtures:continue
        state,lead,groups=fixtures[name]
        cold,rows=run(name+'-cold',state)
        check(name+'_cold_current_font',parity(cold,results[name]) and surface(cold)==surface(results[name]))
        poff,_=run(name+'-pad-off',state,0,'pad');pon,rows=run(name+'-pad-on',state,method='pad')
        check(name+'_pad_toggle_guest_font',cases[name+'-pad-on']['virtual_pad_attached'] and cases[name+'-pad-on']['shown']==cases[name+'-pad-on']['hidden']==1 and parity(poff,pon) and parity(pon,results[name]) and surface(pon)==surface(results[name]))
        original,rows=run(name+'-original-view',state,original=True)
        check(name+'_original_view_exact',all(int(row['enabled'])==int(row['visible'])==0 for row in rows) and parity(original,out/'runs'/(name+'-off')) and surface(original)==surface(out/'runs'/(name+'-off')))
    if a.dog_pill_state and a.returned_state:
        off,_=run('town-return-rollback-off',a.returned_state,0,capture=100,load=a.dog_pill_state)
        on,rows=run('town-return-rollback-on',a.returned_state,capture=100,load=a.dog_pill_state)
        check('town_return_actual_rollback_replaces_lead',int(rows[0]['lead_kind'])==4 and all(int(row['lead_kind'])==5 for row in rows if int(row['frame'])>=81) and '[overlay_selftest] load issued' in (on/'host.log').read_text())
        check('town_return_rollback_guest_and_font',parity(off,on) and surface(on)==oracle(off,5,JournalGroups(town_rams['dog_pill_state']),load=True))
        check('town_return_rollback_closes_and_reopens',cases['town-return-rollback-on']['shown']==2 and any(81<=int(row['frame'])<=89 and int(row['visible'])==0 for row in rows))
    for initial,target,label in ((a.dynamite_route_state,a.morgan_state,'paid-entry-rollback'),(a.morgan_state,a.town_clue_state,'morgan-clue-rollback'),(a.town_clue_state,a.mayor_state,'town-chapter-rollback')):
        if not(initial and target):continue
        tr=target.read_bytes();tr=tr[wram_offset(tr):wram_offset(tr)+0x20000]
        lead=6 if tr[0x5372]==4 else 4
        off,_=run(label+'-off',initial,0,capture=100,load=target)
        on,rows=run(label+'-on',initial,capture=100,load=target)
        check(label+'_actual_restore_current_lead',all(int(row['lead_kind'])==lead and int(row['stage'])==tr[0x5372] for row in rows if int(row['frame'])>=81) and '[overlay_selftest] load issued' in (on/'host.log').read_text())
        check(label+'_guest_and_font_exact',parity(off,on) and surface(on)==oracle(off,lead,JournalGroups(tr),load=True))
        check(label+'_closes_and_reopens',cases[label+'-on']['shown']==2 and any(81<=int(row['frame'])<=89 and int(row['visible'])==0 for row in rows))
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
            'Chapter-scoped current advice and active-pack possession only; no Crest completion, permanent quest history or campaign certification. Original Dog Pill acquisition and Ringo victory/Crest advancement remain separately unqualified. Dynamite weapon acquisition needs independent original-producer evidence; staged inventory cases cannot prove it. Chapter4/5 event tests use explicitly staged prerequisites.',
            'Real SDL keyboard/indexed virtual-controller events; physical controller and paced GPU/audio remain separate.',
            'Original View checks its launcher-equivalent Journal=0 override, not a new launcher route certification.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(checks),'native_runs':len(cases),'pure_checks':pure['checks'],'output':str(out)},indent=2))

if __name__=='__main__':main()
