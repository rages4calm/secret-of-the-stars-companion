"""Private registered-callback/actual-PPU B0 proof, synthetic host contexts only."""
from pathlib import Path
import argparse,hashlib,json,subprocess,struct,shutil
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'local/evidence/large-actor-integration-20261009';S=H/'src'
DRIVER=Path(__file__).with_suffix('.c')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
u16=lambda b,o:int.from_bytes(b[o:o+2],'little')
signed=lambda v:(v&65535)-65536 if v&32768 else v&65535
def put(b,o,v):b[o:o+2]=(v&65535).to_bytes(2,'little')
def main():
 global H,S
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',type=Path,required=True);a.add_argument('--prototype-root',type=Path,default=H);args=a.parse_args()
 H=args.prototype_root.resolve();S=H/'src';assert H.is_relative_to(R/'local')
 O=args.out.resolve();assert not O.exists() and O.is_relative_to(H);O.mkdir()
 runtime=R/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src';rompath=R/'local/inputs/clean-usa.sfc';rom=rompath.read_bytes()
 assert sha(rompath)=='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
 base=R/'local/runs/actor-wide-20261009-133859/sweep-on/dump/start'
 tags=('start','edge','entered','further','return')
 inputs=[rompath,*[base.parent/(tag+ext) for tag in tags for ext in('.wram.bin','.vram.bin','.cgram.bin','_next.oam.bin')]]
 files=[DRIVER,S/'foundation_wide_actors.c',S/'foundation_field.c',S/'foundation_large_actor_canary.c',runtime/'sha256.c',runtime/'snes/ppu.c',runtime/'snes/ppu_legacy.c',runtime/'snes/ws_shadow.c']
 protected=[*inputs,*files,*S.glob('*.h'),Path(__file__),H/'source-copy-manifest.json',*[R/'native/foundation/src'/n for n in('foundation_wide_actors.c','foundation_wide_actors.h','foundation_field.c','foundation_field.h')],*[R/'local/native-proof/SecretOfTheStarsSNESRecomp/src'/n for n in('foundation_wide_actors.c','foundation_field.c')],*[p for p in(R/'local/player-foundation').glob('*')if p.is_file()],*[p for p in(R/'local/player-foundation/saves').rglob('*')if p.is_file()]]
 protected.extend(runtime/n for n in ('common_rtl.h','cpu_state.h','sha256.h','snes/ppu.h','snes/ppu_legacy.h','snes/ws_shadow.h','snes/dma.h','snes/interp_bridge.h','snes/cart.h','snes/snes.h'))
 protected=[p for p in protected if p.exists()]
 manifest=json.loads((H/'source-copy-manifest.json').read_text())['base_inputs']
 for name in ('foundation_wide_actors.c','foundation_field.c'):
  original=R/'native/foundation/src'/name
  assert sha(original)==manifest[str(original.relative_to(R))], 'Baseline source changed; supply a newly reviewed isolated prototype'
 before={str(p.relative_to(R)):sha(p)for p in protected}
 exe=O/'integration-proof.exe';clang=Path('C:/Users/crono/.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
 build=subprocess.run([str(clang),'-std=c11','-O2','-Wall','-Wextra','-Wno-unused-parameter','-I',str(S),'-I',str(runtime),*[str(p)for p in files],'-o',str(exe)],capture_output=True,text=True)
 (O/'compile.txt').write_text(build.stdout+build.stderr);assert build.returncode==0,build.stderr
 baseline=S/'baseline';baseline.mkdir(exist_ok=True);shutil.copyfile(R/'native/foundation/src/foundation_wide_actors.c',baseline/'foundation_wide_actors.c')
 baselineexe=O/'baseline-ordinary-proof.exe';baselinefiles=[baseline/'foundation_wide_actors.c' if p==S/'foundation_wide_actors.c'else p for p in files]
 buildbase=subprocess.run([str(clang),'-std=c11','-O2','-I',str(S),'-I',str(runtime),*[str(p)for p in baselinefiles],'-o',str(baselineexe)],capture_output=True,text=True)
 (O/'baseline-compile.txt').write_text(buildbase.stdout+buildbase.stderr);assert buildbase.returncode==0,buildbase.stderr
 template=Path(str(base)+'.wram.bin').read_bytes();vram=Path(str(base)+'.vram.bin').read_bytes();cg=Path(str(base)+'.cgram.bin').read_bytes();vp=O/'vram.bin';vp.write_bytes(vram)
 report={'scope':'Synthetic host records, original-byte packets and CPU contexts dispatched through the actual registered private callbacks and public PPU scanout. Original ROM and captured VRAM/CGRAM inputs are read only. No guest actor spawned, guest opcode executed, natural B0, controller/audio/GPU or campaign claim. Center parity is the explicit original-center stitch used by the real presentation contract; margin oracle isolates OBJ over captured backdrop.',
         'source_inputs_before':before,'base_source_manifest':json.loads((H/'source-copy-manifest.json').read_text()),'executable_sha256':sha(exe),'cases':{},'checks':{}}
 def rw(address):return u16(rom,(address>>16)*32768+(address&32767))
 def record(w,f,i,x,y,pose=0,base=0xb0):
  at=(0x4100 if f else 0x4000)+i*(25 if f else 18);w[at]=pose;put(w,at+(5 if f else 3),base)
  if f:put(w,at+1,x+signed(u16(w,0x2ad)));put(w,at+3,y+1+signed(u16(w,0x2af)))
  else:w[at+1]=x&255;w[at+2]=(y+1)&255;w[at+5]=((x>>8)&1)|((((y+1)>>8)&1)<<1)
  return at
 def initial():
  p=bytearray(544)
  for slot in range(128):p[slot*4:slot*4+2]=bytes((128,240))
  p[512:]=bytes([85])*32;return p
 def stage(w,seq,ordinary):
  p=initial();art=[];mask=0xefff if w[0x400] else 65535
  for f,i,x,y,pose in seq:
   rawx=x&511 if not f else signed(x);rawy=signed(y);descriptor=0xe9800+0xb0*8+pose*4;high=0;art=[]
   for part in range(2):
    xx=signed(rawx+16*part);word=rw(descriptor+2*part)&mask;threshold=0xfff1 if f else 0x1f9
    emit=((xx&65535)>=threshold or(xx&65535)<255)and((rawy&65535)>=threshold or(rawy&65535)<239)
    if emit:p[part*4:part*4+4]=bytes((xx&255,rawy&255,word&255,word>>8));high|=(2|((xx>>8)&1))<<(part*2)
    dx=xx if f else((xx-128+256)&511)+128-256;dy=rawy if f else((rawy-112+256)&511)+112-256
    art.append((part,dx,dy,word,16))
   p[512]=high
  slot=12
  for f,i,x,y,pose,base in ordinary:
   at=(0x4100 if f else 0x4000)+i*(25 if f else 18);phase=w[0x475 if f else at+10]>>7;desc=0xe9800+(base+pose*2+phase)*8
   for part in range(4):
    xx=x+(part&1)*8;yy=y+(part>>1)*8;word=rw(desc+part*2)&mask
    threshold=0xfff1 if f else 0x1f9
    visible=((x&65535)>=threshold or(x&65535)<255)and(((y+1 if f else y)&65535)>=threshold or((y+1 if f else y)&65535)<239)
    if visible:
     p[slot*4:slot*4+4]=bytes((xx&255,yy&255,word&255,word>>8));shift=(slot%4)*2;p[512+slot//4]=(p[512+slot//4]&~(3<<shift))|(((xx>>8)&1)<<shift);slot+=1
    dx=xx if f else((xx-128+256)&511)+128-256;dy=yy if f else((yy-112+256)&511)+112-256
    virtual=12+(i if not f else 5+i)*4+part;art.append((virtual,dx,dy,word,8))
  return p,art
 def pixel(word,width,row,col,colors):
  sy=width-1-row if word&0x8000 else row;sx=width-1-col if word&0x4000 else col;baseword=0x7000 if word&256 else 0x6000
  tile=(((word&255)//16+sy//8)*16)|(((word&15)+sx//8)%16);at=(baseword+tile*16+sy%8)&32767;idx=0
  for plane in range(4):byte=((at+(8 if plane>=2 else 0))&32767)*2+plane%2;idx|=((vram[byte]>>(7-sx%8))&1)<<plane
  return u16(colors,(128+16*((word>>9)&7)+idx)*2)&32767 if idx else None
 def rgb(color,style,math=False):
  components=[color&31,(color>>5)&31,(color>>10)&31];brightness=7 if style==1 else 15
  if math and style in(2,3):components=[min(31,c+4)if style==2 else max(0,c-4)for c in components]
  return sum((((c<<3)|(c>>2))*brightness//15)<<shift for c,shift in zip(components,(16,8,0)))
 def oracle(art,colors,style,expect,dx=0,dy=0):
  image=np.full((224,400),rgb(u16(colors,0),style),dtype=np.uint32);ranks=np.full((224,400),999,dtype=np.int32)
  if expect and style not in(4,5):
   for slot,x,y,word,width in sorted(art):
    x-=dx;y-=dy
    for row in range(width):
     yy=y+row
     if yy<0 or yy>=224:continue
     for col in range(width):
      xx=x+col
      if not(-72<=xx<0 or 256<=xx<328):continue
      color=pixel(word,width,row,col,colors)
      if color is not None and slot<ranks[yy,xx+72]:image[yy,xx+72]=rgb(color,style,bool(word&0x800));ranks[yy,xx+72]=slot
  return image
 def case(name,seq,guard=0,expect=True,style=0,ordinary=(),phase=0):
  w=bytearray(template);w[0x20]=1;w[0x401]=12;w[0x407]=0;put(w,0x471,0);put(w,0x473,0)
  for i in range(5):w[0x4000+18*i]=255
  for i in range(19):w[0x4100+25*i]=255
  for f,i,x,y,pose in seq:record(w,f,i,x,y,pose)
  for f,i,x,y,pose,base in ordinary:record(w,f,i,x,y,pose,base)
  packet,art=stage(w,seq,ordinary);w[0x2200:0x2420]=initial()
  colors=bytearray(cg)
  if phase:
   for pal in range(8):start=(128+pal*16+1)*2;row=bytes(colors[start:start+30]);colors[start:start+30]=row[2:]+row[:2]
  wp=O/(name+'.wram.bin');fp=O/(name+'.packet.bin');cp=O/(name+'.cgram.bin');op=O/(name+'.bgrx');wp.write_bytes(w);fp.write_bytes(packet);cp.write_bytes(colors)
  p=subprocess.run([str(exe),str(rompath),str(wp),str(vp),str(cp),str(fp),str(op),str(guard),str(int(expect)),str(style)],capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
  (O/(name+'.txt')).write_text(p.stdout+p.stderr);got={'exit':p.returncode,'synthetic_host_context':True,'guard':guard,'expected_metadata':expect}
  if not p.returncode:
   got.update(json.loads(p.stdout));actual=np.frombuffer(op.read_bytes(),dtype='<u4').reshape(224,400)&0xffffff;expected=oracle(art,colors,style,expect,8 if style==6 else 0,3 if style==7 else 0)
   mask=np.ones((224,400),bool);mask[:,72:328]=False;got['margin_pixel_comparisons']=int(mask.sum());got['independent_margin_pixel_mismatches']=int(np.count_nonzero(actual[mask]!=expected[mask]));got['pixels_sha256']=sha(op)
  report['cases'][name]=got
 for f in(0,1):
  for x in(-32,-8,250,300):case(f'family{f}-x{x}',[(f,0,x&511 if not f else x,79,0)])
 for style in range(8):case(f'ppu-style{style}',[(0,0,505,79,3)],style=style)
 for style in(0,2,3):case(f'ppu-positive-math-style{style}',[(0,0,505,79,32)],style=style)
 case('current-palette-base',[(1,0,300,79,3)])
 case('current-palette',[(1,0,300,79,3)],phase=1)
 case('party-to-regular-last-complete',[(0,0,505,79,0),(1,0,-8,79,3)])
 case('party-to-regular-partial-refusal',[(0,0,505,79,0),(1,0,250,79,3)],expect=False)
 case('regular-index18-fixed-family',[(1,18,300,79,3)])
 case('ordinary-regular-coexists',[(0,0,505,79,0)],ordinary=[(1,0,300,120,0,0)])
 case('reset-reproduce-positive',[(0,0,505,79,0)],guard=32)
 for guard in range(1,31):case(f'refusal{guard:02}',[(1 if guard==5 else 0,0,-8 if guard==5 else 505,79,0)],guard=guard,expect=False)
 natural={}
 for tag in tags:
  fixture=base.parent/tag;outputs=[];runs=[]
  for label,binary in(('private',exe),('baseline',baselineexe)):
   op=O/f'natural-ordinary-{tag}-{label}.bgrx'
   command=[str(binary),str(rompath),str(fixture)+'.wram.bin',str(fixture)+'.vram.bin',str(fixture)+'.cgram.bin',str(fixture)+'_next.oam.bin',str(op),'31','1','0']
   p=subprocess.run(command,capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);(O/f'natural-ordinary-{tag}-{label}.txt').write_text(p.stdout+p.stderr)
   runs.append({'label':label,'exit':p.returncode,'result':json.loads(p.stdout)if not p.returncode else None});outputs.append(op)
  natural[tag]={'scope':'Natural ordinary data only; synthetic replay of registered callbacks, no natural B0.','runs':runs,'exact_private_vs_qualified_ordinary_pixels':all(p.exists()for p in outputs)and outputs[0].read_bytes()==outputs[1].read_bytes()}
 report['natural_ordinary_regression']=natural
 after={str(p.relative_to(R)):sha(p)for p in protected};report['source_inputs_after']=after
 report['checks']['all_registered_callback_and_ppu_cases_exit_normally']=all(c['exit']==0 for c in report['cases'].values())
 report['checks']['actual_registered_hooks_and_readonly_callbacks']=all(c.get('registered_hooks')==9 and c.get('readonly_callbacks',0)>5 for c in report['cases'].values())
 report['checks']['no_metadata_before_complete_transfer']=all(c.get('before_complete_parts')==0 for c in report['cases'].values())
 report['checks']['independent_full_margin_pixels_exact']=all(c.get('independent_margin_pixel_mismatches')==0 for c in report['cases'].values())
 report['checks']['original_center_stitch_exact']=all(c.get('center_stitch_line_mismatches')==0 for c in report['cases'].values())
 report['checks']['positive_both_coordinate_families']=all(report['cases'][f'family{f}-x300'].get('max_side_parts',0)>0 for f in(0,1))
 report['checks']['reset_then_reproduction_recovers_checked_metadata']=report['cases']['reset-reproduce-positive'].get('max_side_parts',0)>0
 report['checks']['five_genuine_ordinary_packets_match_qualified_baseline']=all(c['exact_private_vs_qualified_ordinary_pixels']and all(not r['exit']for r in c['runs'])for c in natural.values())
 report['checks']['brightness_window_and_fixed_math_have_positive_pixel_effect']=all(report['cases']['ppu-style0']['pixels_sha256']!=report['cases'][f'ppu-style{i}']['pixels_sha256']for i in(1,4,5,6,7))and all(report['cases']['ppu-positive-math-style0']['pixels_sha256']!=report['cases'][f'ppu-positive-math-style{i}']['pixels_sha256']for i in(2,3))
 report['checks']['current_palette_updates_public_ppu_pixels']=report['cases']['current-palette']['pixels_sha256']!=report['cases']['current-palette-base']['pixels_sha256']
 report['checks']['all_original_inputs_owner_profile_sources_preserved']=before==after
 report['case_count']=len(report['cases']);report['margin_pixel_comparisons']=sum(c.get('margin_pixel_comparisons',0)for c in report['cases'].values());report['passed']=all(report['checks'].values())
 (O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k]for k in('passed','checks','case_count','margin_pixel_comparisons')},indent=2));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
