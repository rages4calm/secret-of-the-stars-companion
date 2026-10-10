"""Copied-state enemy HUD qualification: original guest parity and wide center.

Needs an owned ROM and actual battle checkpoint. No private fixture is bundled.
Host captures are separate from paced playback; this checker is silent/unpaced.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,struct,subprocess

ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
GUEST=('wram.bin','vram.bin','sram.bin','oam.bin','cgram.bin','regs.json','fb.bgrx')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--battle-state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 exe=a.exe.resolve(strict=True);rom=a.rom.resolve(strict=True);state=a.battle_state.resolve(strict=True);out=a.output.resolve();assert sha(rom)==ROM_SHA;out.mkdir(parents=True,exist_ok=False)
 protected={str(f):sha(f)for f in (exe,rom,state)};cases={};checks={}
 for wide in (0,1):
  for enhanced in (0,1):
   pair=[]
   for enabled in (0,1):
    name=f'wide{wide}-pixels{enhanced}-hud{enabled}';d=out/name;d.mkdir();(d/'dump').mkdir();(d/'captures').mkdir()
    shutil.copy2(exe,d/'game.exe');shutil.copy2(state,d/'resume.state')
    (d/'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
    (d/'input.txt').write_text('wait 60\ndump current\nwait 30\ndump end\nquit\n')
    env={k:v for k,v in os.environ.items()if not k.startswith('SNESRECOMP_')};env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_FOUNDATION_BATTLE_INFO=str(enabled),SNESRECOMP_FOUNDATION_JOURNAL='0',SNESRECOMP_FOUNDATION_HD_MENU_FRAMES='0',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced),SNESRECOMP_FOUNDATION_WIDE=str(wide),SNESRECOMP_FOUNDATION_WIDE_ACTORS=str(wide),SNESRECOMP_DUMP_DIR=str(d/'dump'),SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE='60,90',SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(d/'captures'))
    with(d/'runtime.log').open('w')as log:r=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(rom),'--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,stdout=log,stderr=log,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log=(d/'runtime.log').read_text(errors='replace');q={'exit_zero':r.returncode==0,'explicit_private_anchor':str(d)in log and 'resume state loaded:'in log,'copied_binary_exact':sha(d/'game.exe')==sha(exe)};checks.update({name+'_'+k:v for k,v in q.items()});cases[name]={'checks':q};pair.append(d)
   off,on=pair;factor=2 if enhanced else 1;w=(400 if wide else 256)*factor;h=224*factor
   for stem,frame in (('current',60),('end',90)):
    tag=f'wide{wide}-pixels{enhanced}-{stem}'
    for ext in GUEST:checks[tag+'_guest_'+ext]=sha(off/'dump'/(stem+'.'+ext))==sha(on/'dump'/(stem+'.'+ext))
    ram=(on/'dump'/(stem+'.wram.bin')).read_bytes();checks[tag+'_actual_battle']=ram[0x20]==5
    records=[(i,ram[0x6100+i*28],struct.unpack_from('<HH',ram,0x6101+i*28))for i in range(4)if not ram[0x6100+i*28]&128]
    checks[tag+'_actual_enemies_present']=bool(records)
    old=(off/'captures'/f'frame-{frame}-{w}x{h}.bgrx').read_bytes();new=(on/'captures'/f'frame-{frame}-{w}x{h}.bgrx').read_bytes();assert len(old)==len(new)==w*h*4
    differences=[]
    for y in range(h):
     for x in range(w):
      at=(y*w+x)*4
      if old[at:at+4]!=new[at:at+4]:differences.append((x,y))
    checks[tag+'_hud_draws']=bool(differences)
    left=4 if wide else 8;right=68 if wide else 248;bottom=6+(28+len(records)*42 if wide else 24+len(records)*18)
    # Scale2x can modify one adjacent source-pixel decision at a panel edge.
    checks[tag+'_all_changes_in_panel_bounds']=all((left-1)*factor<=x<(right+1)*factor and 5*factor<=y<(bottom+1)*factor for x,y in differences)
    if wide:
     checks[tag+'_authentic_center_unobscured']=all(old[(y*w+72*factor)*4:(y*w+328*factor)*4]==new[(y*w+72*factor)*4:(y*w+328*factor)*4]for y in range(h))
     checks[tag+'_right_side_unchanged']=all(old[(y*w+328*factor)*4:(y+1)*w*4]==new[(y*w+328*factor)*4:(y+1)*w*4]for y in range(h))
    if not enhanced:
     for row,(slot,ident,(hp,maximum))in enumerate(records):
      bw=52 if wide else 66;barx=left+(6 if wide else 166);bary=6+(26+row*42+31 if wide else 22+row*18+1)
      value=min(hp,maximum);filled=value*(bw-2)//maximum if maximum else 0;color=0xffff7a78 if value*4<=maximum else 0xffffdf78 if value*2<=maximum else 0xff62d9c1
      expected=[color if x<filled else 0xff101b2c for x in range(bw-2)]
      actual=[struct.unpack_from('<I',new,((bary+1)*w+barx+1+x)*4)[0]for x in range(bw-2)]
      checks[tag+f'_enemy{slot}_bar_matches_original_hp']=actual==expected
   from PIL import Image
   if not enhanced:Image.frombytes('RGBA',(w,h),(on/'captures'/f'frame-60-{w}x{h}.bgrx').read_bytes(),'raw','BGRA').convert('RGB').resize((w*3,h*3),Image.Resampling.NEAREST).save(out/(f'hud-wide{wide}.png'))
 checks['immutable_exe_rom_checkpoint']=all(sha(Path(f))==v for f,v in protected.items())
 report={'passed':all(checks.values()),'checks':checks,'check_count':len(checks),'native_runs':8,'executable_sha256':sha(exe),'source_checkpoint_sha256':sha(state),'protected':protected,'scope':'One actual battle copied checkpoint, two times, 256/400 canvases with original/enhanced pixels; original guest bytes and wide composed center. No campaign, physical-controller or paced-audio certification.'}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ('checks','protected')},indent=2));return 0 if report['passed']else 1

if __name__=='__main__':raise SystemExit(main())
