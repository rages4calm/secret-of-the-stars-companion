"""Private B0 synthetic host metadata/artwork proof; never executes a guest."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
CLEAN='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
u16=lambda b,o:int.from_bytes(b[o:o+2],'little')
signed=lambda v:(v&65535)-65536 if v&32768 else v&65535
def put(b,o,v):b[o:o+2]=(v&65535).to_bytes(2,'little')

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',type=Path,required=True)
    a.add_argument('--rom',type=Path,required=True);a.add_argument('--base-dump',type=Path,required=True)
    a.add_argument('--clang',type=Path,required=True)
    a.add_argument('--runtime-root',type=Path,default=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src');args=a.parse_args()
    out=args.out.resolve();assert not out.exists() and out.is_relative_to(ROOT/'local');out.mkdir(parents=True)
    runtime=args.runtime_root.resolve()
    rompath=args.rom.resolve(strict=True);rom=rompath.read_bytes();assert len(rom)==1572864 and sha(rompath)==CLEAN
    base=args.base_dump.resolve()
    inputs=[rompath,*[Path(str(base)+ext)for ext in('.wram.bin','.vram.bin','.cgram.bin')]]
    sources=[HERE/'foundation_large_actor_canary.c',HERE/'foundation_large_actor_canary.h',HERE/'check_foundation_large_actors.c',Path(__file__),runtime/'sha256.c']
    before={str(p):sha(p)for p in[*inputs,*sources]}
    files=[HERE/'check_foundation_large_actors.c',HERE/'foundation_large_actor_canary.c',runtime/'sha256.c'];exe=out/'large-proof.exe'
    build=subprocess.run([str(args.clang),'-std=c11','-O2','-Wall','-Wextra','-I',str(HERE),'-I',str(runtime),*[str(p)for p in files],'-o',str(exe)],capture_output=True,text=True)
    (out/'compile.txt').write_text(build.stdout+build.stderr);assert build.returncode==0,build.stderr
    template=bytearray(Path(str(base)+'.wram.bin').read_bytes());vram=Path(str(base)+'.vram.bin').read_bytes();cg=Path(str(base)+'.cgram.bin').read_bytes()
    assert len(template)==131072 and len(vram)==65536 and len(cg)==512
    initial=bytearray(544)
    for slot in range(128):initial[slot*4:slot*4+2]=bytes((128,240))
    initial[512:]=bytes([0x55])*32
    vpath=out/'fixture.vram.bin';cpath=out/'fixture.cgram.bin';ipath=out/'initial.packet.bin'
    vpath.write_bytes(vram);cpath.write_bytes(cg);ipath.write_bytes(initial)
    report={'scope':'ROM-free authored helper and synthetic host records/CPU seams/packets. Original ROM supplies descriptor words; an existing natural dump supplies current tile/palette input only. No natural B0 actor, guest opcode execution, full PPU/GPU/controller/audio or campaign qualification.',
            'source_inputs_before':before,'helper_executable_sha256':sha(exe),'metadata_cases':{},'decode_cases':{},'checks':{}}
    def rw(address):return int.from_bytes(rom[(address>>16)*32768+(address&32767):(address>>16)*32768+(address&32767)+2],'little')
    def record(w,family,index,x,y,pose=0):
        at=(0x4100 if family else 0x4000)+index*(25 if family else 18)
        w[at]=pose;put(w,at+(5 if family else 3),0xb0)
        if family:put(w,at+1,x+signed(u16(w,0x2ad)));put(w,at+3,y+1+signed(u16(w,0x2af)))
        else:w[at+1]=x&255;w[at+2]=(y+1)&255;w[at+5]=((x>>8)&1)|((((y+1)>>8)&1)<<1)
        return at
    def expected(w,sequence):
        packet=bytearray(initial);actors=[]
        for family,index in sequence:
            at=(0x4100 if family else 0x4000)+index*(25 if family else 18)
            if family:x=signed(u16(w,at+1)-u16(w,0x2ad));y=signed(u16(w,at+3)-u16(w,0x2af)-1)
            else:x=w[at+1]+((w[at+5]&1)<<8);y=signed(w[at+2]+((w[at+5]&2)<<7)-1)
            desc=0xe9800+0xb0*8+w[at]*4;pieces=[];high=0
            for p in range(2):
                xx=signed(x+16*p);yy=signed(y);word=rw(desc+2*p)&(0xefff if w[0x400] else 65535)
                threshold=0xfff1 if family else 0x1f9
                emit=((xx&65535)>=threshold or(xx&65535)<255)and((yy&65535)>=threshold or(yy&65535)<239)
                if emit:packet[p*4:p*4+4]=bytes((xx&255,yy&255,word&255,word>>8));high|=(2|((xx>>8)&1))<<(p*2)
                pieces.append(dict(x=xx,y=yy,word=word,emitted=int(emit),slot=p))
            packet[512]=high;actors.append(dict(family=family,index=index,descriptor=desc,pieces=pieces))
        return packet,actors
    def case(name,sequence,positions,guard=0,accept=True,mask=False):
        w=bytearray(template);w[0x20]=1;w[0x401]=12;w[0x407]=0;put(w,0x471,0);put(w,0x473,0)
        if mask:w[0x400]=0
        for(f,i),(x,y,pose)in zip(sequence,positions):record(w,f,i,x,y,pose)
        # Deliberately different phase bytes must not affect B0's direct pose descriptor.
        w[0x475]=128
        for f,i in sequence:
            if not f:w[0x4000+i*18+10]=128
        packet,actors=expected(w,sequence);wp=out/(name+'.wram.bin');fp=out/(name+'.packet.bin');wp.write_bytes(w);fp.write_bytes(packet)
        f,i=sequence[0];second,index=sequence[1]if len(sequence)>1 else(2,0)
        command=[str(exe),'case',str(rompath),str(wp),str(vpath),str(cpath),str(ipath),str(fp),str(out),str(f),str(i),str(second),str(index),str(guard),'unused']
        p=subprocess.run(command,capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0,(name,p.returncode,p.stdout,p.stderr)
        got=json.loads(p.stdout);got['expected_accepted']=accept;got['acceptance_matches']=got['accepted']==accept
        if accept:got['independent_metadata_exact']=got['pieces']==actors[-1]['pieces']and got['descriptor']==actors[-1]['descriptor']and got['last_family']==actors[-1]['family']and got['last_index']==actors[-1]['index']
        report['metadata_cases'][name]=got
    # Both source coordinate families, signed/packed boundaries, per-component culling.
    positions=[-16,-15,-8,-1,0,238,239,250,254,255,256,300,327,328,383,505,511]
    for family in(0,1):
        for x in positions:
            if not family and x<0:x&=511
            case(f'family{family}-x{x}',[(family,0)],[(x,79,0)])
        for y in(-1,0,238,239,240,504,505,510):
            case(f'family{family}-y{y}',[(family,0)],[(300,y,3)])
    for pose in(0,1,2,3,7,127,128,254):case(f'pose{pose}',[(1,18)],[(300,79,pose)])
    case('maskFFFF-and-no-global-phase',[(0,0)],[(505,79,3)],mask=True)
    case('party-to-regular-complete-lastwriter',[(0,0),(1,0)],[(505,79,0),(-8,79,3)])
    case('party-to-regular-partial-failsclosed',[(0,0),(1,0)],[(505,79,0),(250,79,3)],accept=False)
    case('party-to-party-complete-lastwriter',[(0,0),(0,1)],[(505,79,0),(505,79,3)])
    case('regular-to-party-order-refused',[(1,0),(0,0)],[(-8,79,0),(505,79,3)],accept=False)
    case('duplicate-fixedwriter-refused',[(1,0),(1,0)],[(-8,79,0),(-8,79,0)],accept=False)
    # Every requested negative must actually be reached by the proper source family.
    for guard in range(1,75):
        family=1 if guard in(13,14,15) else 0
        x=-8 if family else 505
        case(f'refusal-{guard:02}',[(family,0)],[(x,79,0)],guard=guard,accept=False)
    report['checks']['metadata_and_all_requested_refusals_exact']=all(c['acceptance_matches']and c.get('independent_metadata_exact',True)and c['source_inputs_unchanged']for c in report['metadata_cases'].values())
    report['checks']['same_slot_collision_uses_only_complete_lastwriter']=all(report['metadata_cases'][k]['writers']==2 and report['metadata_cases'][k]['collision']and report['metadata_cases'][k]['margin_parts_at_line80']<=2 for k in('party-to-regular-complete-lastwriter','party-to-party-complete-lastwriter'))
    # Independent byte-plane decoding, covering tile-column wrap/row carry,
    # both banks, all palettes and both full16x16 flips. Inputs stay private.
    words=np.array([tile|bank*256|palette*512|flip*16384 for tile in range(256)for bank in range(2)for palette in range(8)for flip in range(4)],dtype='<u2')
    wordpath=out/'decode.words.bin';wordpath.write_bytes(words.tobytes());decoderam=out/'decode.wram.bin';decoderam.write_bytes(template)
    def pixel_oracle(word,colors):
        result=[];baseword=0x7000 if word&256 else 0x6000;palette=128+((word>>9)&7)*16
        for row in range(16):
            y=15-row if word&0x8000 else row
            for col in range(16):
                x=15-col if word&0x4000 else col
                tile=(((word&255)//16+y//8)*16)|(((word&15)+x//8)%16)
                at=(baseword+tile*16+y%8)&32767;bit=7-x%8;idx=0
                for plane in range(4):
                    byte=((at+(8 if plane>=2 else 0))&32767)*2+(plane%2)
                    idx|=((vram[byte]>>bit)&1)<<plane
                result.append(0x8000|(u16(colors,(palette+idx)*2)&32767) if idx else 0)
        return result
    for phase in range(2):
        colors=bytearray(cg)
        if phase:
            for pal in range(8):
                start=(128+pal*16+1)*2;row=bytes(colors[start:start+30]);colors[start:start+30]=row[2:]+row[:2]
        cp=out/f'decode-phase{phase}.cgram.bin';cp.write_bytes(colors);pixels=out/f'decode-phase{phase}.pixels.bin'
        p=subprocess.run([str(exe),'decode',str(rompath),str(decoderam),str(vpath),str(cp),str(wordpath),str(ipath),str(pixels),'0','0','2','0','0','unused'],capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0,p.stderr
        actual=np.frombuffer(pixels.read_bytes(),dtype='<u2').reshape(-1,256);mismatch=0
        for n,word in enumerate(words):mismatch+=int(np.any(actual[n]!=pixel_oracle(int(word),colors)))
        report['decode_cases'][str(phase)]={**json.loads(p.stdout),'independent_byteplane_word_mismatches':mismatch,'pixels_sha256':sha(pixels),'cgram_sha256':sha(cp)}
    report['checks']['all16x16_art_pixels_match_independent_byteplane_oracle']=all(not c['independent_byteplane_word_mismatches']for c in report['decode_cases'].values())
    report['checks']['current_palette_phase_changes_pixels']=report['decode_cases']['0']['pixels_sha256']!=report['decode_cases']['1']['pixels_sha256']
    after={str(p):sha(p)for p in[*inputs,*sources]};report['source_inputs_after']=after
    report['checks']['original_inputs_and_canary_sources_unchanged']=before==after
    report['metadata_case_count']=len(report['metadata_cases']);report['pixel_comparisons']=sum(c['pixels']for c in report['decode_cases'].values())
    report['passed']=all(report['checks'].values());(out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k]for k in('passed','checks','metadata_case_count','pixel_comparisons')},indent=2));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
