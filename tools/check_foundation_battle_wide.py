"""All16 original-resource battle clone proof; no saves or owner profile writes.
Synthetic host fixtures reconstruct the original ROM loader resource tables.
They do not execute story progression or certify natural campaign transitions.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
CLEAN="7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600"
RECIPES={0: [[[1, 0, 1], [3, 2, 3], [5, 4, 5], [7, 8, 9], [11, 11, 12], [13, 13, 13], [13, 13, 13], [13, 13, 13]], [[0, 1, 0], [2, 3, 2], [4, 5, 4], [6, 7, 8], [10, 11, 11], [13, 13, 13], [13, 13, 13], [13, 13, 13]]], 1: [[[258, 257, 256], [265, 264, 290], [293, 292, 291], [43, 44, 45], [30, 48, 49], [32, 32, 52], [33, 33, 54], [32, 32, 32]], [[262, 261, 260], [268, 267, 266], [276, 297, 296], [42, 43, 44], [46, 47, 30], [50, 51, 32], [53, 33, 33], [32, 32, 32]]], 2: [[[258, 257, 256], [265, 264, 263], [271, 270, 269], [279, 278, 277], [30, 30, 31], [32, 32, 32], [33, 33, 33], [32, 32, 32]], [[262, 261, 260], [268, 267, 266], [276, 275, 274], [284, 283, 282], [29, 30, 30], [32, 32, 32], [33, 33, 33], [32, 32, 32]]], 3: [[[3, 3, 3], [57, 58, 59], [65, 66, 67], [73, 74, 75], [30, 30, 31], [32, 32, 32], [33, 33, 33], [32, 32, 32]], [[3, 3, 3], [55, 56, 3], [60, 61, 62], [68, 69, 70], [29, 30, 30], [32, 32, 32], [33, 33, 33], [32, 32, 32]]], 4: [[[258, 257, 256], [265, 264, 263], [271, 270, 269], [279, 278, 332], [30, 30, 30], [32, 32, 32], [33, 33, 33], [32, 32, 32]], [[262, 261, 260], [268, 267, 266], [276, 275, 274], [333, 283, 282], [30, 30, 30], [32, 32, 32], [33, 33, 33], [32, 32, 32]]], 5: [[[3, 3, 3], [3, 3, 3], [83, 83, 83], [89, 90, 91], [92, 92, 92], [93, 93, 93], [94, 94, 94], [93, 93, 93]], [[3, 3, 3], [3, 3, 3], [83, 83, 83], [84, 85, 86], [92, 92, 92], [93, 93, 93], [94, 94, 94], [93, 93, 93]]], 6: [[[258, 257, 256], [265, 264, 290], [293, 292, 291], [78, 78, 78], [79, 79, 79], [81, 80, 81], [80, 81, 80], [81, 80, 81]], [[262, 261, 260], [268, 267, 266], [276, 297, 296], [78, 78, 78], [79, 79, 79], [80, 81, 80], [81, 80, 81], [80, 81, 80]]], 7: [[[0, 1, 2], [4, 5, 6], [8, 9, 10], [30, 31, 32], [34, 34, 34], [36, 35, 36], [35, 36, 35], [36, 35, 36]], [[0, 1, 2], [4, 5, 6], [8, 9, 10], [30, 31, 32], [34, 34, 34], [35, 36, 35], [36, 35, 36], [35, 36, 35]]], 8: [[[0, 1, 2], [4, 5, 6], [8, 9, 10], [12, 13, 14], [16, 16, 16], [18, 17, 18], [17, 18, 17], [18, 17, 18]], [[0, 1, 2], [4, 5, 6], [8, 9, 10], [12, 13, 14], [16, 16, 16], [17, 18, 17], [18, 17, 18], [17, 18, 17]]], 9: [[[19, 20, 21], [22, 23, 24], [25, 26, 27], [29, 28, 29], [16, 16, 16], [18, 17, 18], [17, 18, 17], [18, 17, 18]], [[21, 19, 20], [24, 22, 23], [27, 25, 26], [28, 29, 28], [16, 16, 16], [17, 18, 17], [18, 17, 18], [17, 18, 17]]], 10: [[[293, 293, 293], [299, 298, 297], [307, 306, 305], [314, 313, 312], [16, 16, 16], [18, 17, 18], [17, 18, 17], [18, 17, 18]], [[296, 295, 294], [304, 303, 302], [311, 310, 309], [319, 318, 317], [16, 16, 16], [17, 18, 17], [18, 17, 18], [17, 18, 17]]], 11: [[[14, 15, 16], [23, 23, 23], [28, 28, 28], [33, 33, 33], [38, 38, 38], [39, 39, 39], [40, 40, 40], [40, 40, 40]], [[16, 16, 16], [23, 23, 23], [28, 28, 28], [33, 33, 33], [38, 38, 38], [39, 39, 39], [40, 40, 40], [40, 40, 40]]], 12: [[[2, 3, 4], [10, 11, 12], [17, 18, 19], [24, 24, 24], [28, 28, 28], [29, 29, 29], [30, 30, 30], [31, 31, 31]], [[5, 6, 7], [13, 14, 15], [20, 21, 22], [25, 26, 27], [28, 28, 28], [29, 29, 29], [30, 30, 30], [31, 31, 31]]], 13: [[[1, 1, 1], [1, 1, 1], [1, 1, 1], [24, 24, 24], [30, 30, 30], [33, 33, 33], [36, 36, 36], [100, 100, 100]], [[7, 6, 7], [12, 13, 14], [19, 19, 19], [24, 24, 24], [30, 30, 30], [33, 33, 33], [36, 36, 36], [100, 100, 100]]], 14: [[[42, 43, 44], [49, 40, 45], [49, 40, 50], [57, 55, 58], [62, 61, 63], [64, 64, 65], [67, 67, 67], [68, 68, 68]], [[37, 38, 39], [45, 46, 47], [50, 51, 41], [52, 53, 54], [59, 60, 61], [64, 64, 64], [66, 67, 67], [68, 68, 68]]], 15: [[[72, 72, 72], [78, 78, 78], [78, 78, 78], [89, 89, 89], [94, 94, 94], [96, 96, 96], [97, 97, 97], [101, 101, 101]], [[72, 72, 72], [78, 78, 78], [78, 78, 78], [89, 89, 89], [94, 94, 94], [96, 96, 96], [97, 97, 97], [101, 101, 101]]]}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--rom',type=Path,required=True);a.add_argument('--base-dump',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--clang',type=Path,required=True);a.add_argument('--runtime-root',type=Path,default=Path('local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'));args=a.parse_args()
 root=Path(__file__).resolve().parents[1];out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);rom=args.rom.read_bytes();assert len(rom)==1572864 and hashlib.sha256(rom).hexdigest()==CLEAN,'Exact clean ROM required'
 def rb(addr,n):off=(addr>>16)*32768+(addr&32767);assert 0<=off<=len(rom)-n;return rom[off:off+n]
 def rr(addr,n=1):return int.from_bytes(rb(addr,n),'little')
 def word(cells,tiles,cell,x,y):m=rr(cells+cell*4+((y>>4)&1)*2+((x>>4)&1));return rr(tiles+m*8+((y>>3)&1)*4+((x>>3)&1)*2,2)
 base={k:Path(str(args.base_dump)+'.'+k+'.bin').read_bytes() for k in ['wram','vram','cgram']};assert [len(base[k]) for k in base]==[131072,65536,512] and base['wram'][32]==5,'Battle dump contract required'
 runtime=args.runtime_root.resolve();source=root/'native/foundation/src/foundation_battle_wide.c';harness=root/'tools/check_foundation_battle_wide.c';exe=out/'battle-ppu-proof.exe'
 files=[source,runtime/'sha256.c',runtime/'snes/ppu.c',runtime/'snes/ppu_legacy.c',runtime/'snes/ws_shadow.c',harness]
 subprocess.run([str(args.clang),'-std=c11','-O2','-I',str(source.parent),'-I',str(runtime),*[str(p) for p in files],'-o',str(exe)],check=True)
 report={'kind':'host synthetic original-ROM resource PPU proof, not natural campaign/CPU/controller/audio proof','rom_sha256':CLEAN,'source_sha256':{str(p.relative_to(root)):sha(p) for p in files},'harness_sha256':sha(exe),'base_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in base.items()},'cases':{}}
 for selector in range(16):
  kind=rr(0xed800+selector);cells=0xe0000|rr(0xef800+(kind&15)*2,2);tiles=0xe0000|rr(0xedc10+(kind>>4)*2,2);desc=rb(0xf9400+selector*4,4);ids=rb(0xf9200+desc[0]*4,4);w=bytearray(base['wram']);v=bytearray(base['vram']);cg=bytearray(base['cgram']);w[0x529]=selector;w[0x550]=desc[3]^128;w[0x4408:0x440a]=desc[1:3];w[0x4416:0x441a]=ids
  for chunk,g in enumerate(ids):v[0x4000+chunk*4096:0x5000+chunk*4096]=rb(((16+(g>>3))<<16)|(0x8000+((g&7)<<12)),4096)
  words=[word(cells,tiles,rr(0xed810+selector*64+(y//4)*8+x//4),x*8,y*8) for y in range(32) for x in range(32)];v[0xb000:0xb800]=struct.pack('<1024H',*words)
  for pal,idx in zip([6,7],desc[1:3]):cg[pal*32+2:pal*32+32]=rb(0x5ae00+idx*30,30)
  phases=[]
  for phase in range(2):
   prefix=out/f'selector-{selector:02d}-phase-{phase}'
   phasecg=bytearray(cg)
   if phase:
    for pal in [6,7]:colors=bytes(phasecg[pal*32+2:pal*32+32]);phasecg[pal*32+2:pal*32+32]=colors[2:]+colors[:2]
   for key,data in [('wram',w),('vram',v),('cgram',phasecg)]:Path(str(prefix)+'.'+key+'.bin').write_bytes(data)
   raw=Path(str(prefix)+'.bgrx');proc=subprocess.run([str(exe),str(args.rom.resolve()),str(prefix)+'.wram.bin',str(prefix)+'.vram.bin',str(prefix)+'.cgram.bin',str(raw),'1'],capture_output=True,text=True,timeout=15);assert proc.returncode==0,(selector,phase,proc.stderr,proc.stdout);result=json.loads(proc.stdout);shadow=Path(str(raw)+'.shadow').read_bytes();comparisons=0
   assert shadow[0xb000:0xb800]==v[0xb000:0xb800]
   for y in range(29):
    for side in range(2):
     for x in range(9):
      px=x*8+(24 if not side else 0);entry=RECIPES[selector][side][y//4][px//32];lx=px&31;lx=31-lx if entry&256 else lx;expected=word(cells,tiles,entry&255,lx,y*8)^(0x4000 if entry&256 else 0);index=0x5800+1024+y*32+(23 if not side else 0)+x;assert struct.unpack_from('<H',shadow,index*2)[0]==expected,(selector,phase,side,x,y);comparisons+=1
   result['independent_sideword_comparisons']=comparisons;result['pixels_sha256']=sha(raw);phases.append(result)
   try:
    from PIL import Image
    Image.frombytes('RGB',(400,224),raw.read_bytes(),'raw','BGRX').save(raw.with_suffix('.png'))
   except ImportError:pass
  assert phases[0]['pixels_sha256']!=phases[1]['pixels_sha256'],'Actual palette use must affect output'
  report['cases'][str(selector)]={'resource_kind':kind,'graphics_ids':list(ids),'palette_animation_marker':desc[3],'phases':phases,'actual_palette_change_observed':True}
 report['qualified_host_resource_cases']=16;report['center_pixels_compared']=16*2*256*224;report['sidewords_compared']=16*2*522;report['guard_rejections']=sum(p['rejection_checks'] for c in report['cases'].values() for p in c['phases']);report['qualified']=True;(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['qualified','qualified_host_resource_cases','center_pixels_compared','sidewords_compared','guard_rejections']},indent=2))
if __name__=='__main__':main()
