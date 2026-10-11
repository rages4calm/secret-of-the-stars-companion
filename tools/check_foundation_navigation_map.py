"""Check the authored read-only navigation core against original ROM/captures.

This is a portable host proof, not native input/audio/campaign certification.
All copied ROM-derived outputs stay under a fresh ignored local/ directory.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import time

from inspect_foundation_maps import OriginalMaps, ROM_SHA256
from check_foundation_map_resolver import expected, make_view

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parent if SOURCE.name == 'github-repo' else SOURCE


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(rom_path, prefixes, output, runtime, compiler):
    output = output.resolve()
    if output.exists() or not output.is_relative_to((ROOT / 'local').resolve()):
        raise ValueError('Choose a fresh private output under local/')
    rom = rom_path.read_bytes()
    maps = OriginalMaps(rom)
    output.mkdir(parents=True)
    authored = SOURCE / 'native/foundation/src'
    library = output / ('navigation.dll' if os.name == 'nt' else 'navigation.so')
    command = [str(compiler), '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared',
               '-DFOUNDATION_FIELD_STANDALONE', '-DFOUNDATION_MAP_STANDALONE',
               '-I' + str(authored), '-I' + str(runtime),
               str(authored / 'foundation_map.c'), str(authored / 'foundation_field.c'),
               str(runtime / 'sha256.c'), '-o', str(library)]
    if os.name != 'nt':
        command.insert(1, '-fPIC')
    built = subprocess.run(command, capture_output=True, text=True)
    (output / 'compile.log').write_text(built.stdout + built.stderr, encoding='utf-8')
    if built.returncode:
        raise ValueError(built.stderr)
    lib = ctypes.CDLL(str(library))
    byte_p, word_p = ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint16)
    lib.FoundationFieldBind.argtypes = [byte_p, ctypes.c_size_t]
    lib.FoundationFieldCheckSceneView.argtypes = [ctypes.c_void_p]
    lib.FoundationMapPosition.argtypes = [byte_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    lib.FoundationMapSample.argtypes = [byte_p, ctypes.c_size_t, word_p, ctypes.c_size_t, word_p, ctypes.c_size_t,
                                       ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint32)]
    rb = (ctypes.c_uint8 * len(rom)).from_buffer_copy(rom)
    checks = {'exact_original_rom': sha(rom) == ROM_SHA256, 'rom_binds': bool(lib.FoundationFieldBind(rb,len(rom)))}
    count = 0
    receipts = []

    def color(ram, vram, palette, px, py):
        indices, tiles = [], []
        for layer in range(2):
            if not ram[0x50c + layer]:
                indices.append(0); tiles.append(0); continue
            lx,ly=px,py
            if layer:
                word=lambda at:int.from_bytes(ram[at:at+2],'little')
                sx=(word(0x2b1)-word(0x2ad)+32768)%65536-32768
                sy=(word(0x2b3)-word(0x2af)+32768)%65536-32768
                lx+=sx;ly+=sy
            tile = expected(maps,ram,layer,lx,ly)
            col, row = lx % 8, ly % 8
            if tile & 0x4000: col = 7-col
            if tile & 0x8000: row = 7-row
            start = (tile & 1023)*32
            pixel = sum(((vram[start + row*2 + (plane%2) + (16 if plane>=2 else 0)] >> (7-col)) & 1) << plane for plane in range(4))
            indices.append(pixel + ((tile >> 10)&7)*16 if pixel else 0); tiles.append(tile)
        index = indices[0] if indices[0] and tiles[0]&0x2000 else indices[1] if indices[1] and tiles[1]&0x2000 else indices[0] or indices[1]
        rgb = int.from_bytes(palette[index*2:index*2+2],'little')
        return 0xff000000 | (rgb&31)*255//31 << 16 | ((rgb>>5)&31)*255//31 << 8 | ((rgb>>10)&31)*255//31

    for i,prefix in enumerate(prefixes):
        parts = {k: Path(str(prefix)+'.'+k) for k in ['wram.bin','regs.json','vram.bin','cgram.bin']}
        raw = {k:p.read_bytes() for k,p in parts.items()}
        ram,vram,pal = raw['wram.bin'],raw['vram.bin'],raw['cgram.bin']
        regs=json.loads(raw['regs.json'])
        buffer,view=make_view(ram,regs)
        lib.FoundationFieldBind(rb,len(rom))
        vb=(ctypes.c_uint16*0x8000).from_buffer_copy(vram)
        pb=(ctypes.c_uint16*256).from_buffer_copy(pal)
        tag=f'capture{i}'
        checks[tag+'_selected_resource'] = bool(lib.FoundationFieldCheckSceneView(ctypes.byref(view)))
        if not checks[tag+'_selected_resource']:
            raise ValueError(f'Ineligible input {prefix}')
        original=(bytes(buffer),bytes(vb),bytes(pb))
        width,height=ram[0x46d]*256,ram[0x46e]*256
        cw,ch=224,height*224//width
        if ch>128: ch=128;cw=width*128//height
        pixels=bytearray()
        result=ctypes.c_uint32(0xdeadbeef)
        mismatches=0
        started=time.perf_counter()
        for y in range(ch):
            for x in range(cw):
                px,py=(2*x+1)*width//(2*cw),(2*y+1)*height//(2*ch)
                accepted=lib.FoundationMapSample(buffer,len(ram),vb,0x8000,pb,256,px,py,ctypes.byref(result))
                mismatches += not accepted or result.value != color(ram,vram,pal,px,py)
                pixels+=result.value.to_bytes(4,'little');count+=1
        checks[tag+'_full_overview_independent_colors']=mismatches==0
        checks[tag+'_read_only_inputs']=original==(bytes(buffer),bytes(vb),bytes(pb))
        (output/f'{tag}-map.argb').write_bytes(pixels)
        px,py=ctypes.c_int(-999),ctypes.c_int(-999)
        accepted=bool(lib.FoundationMapPosition(buffer,len(ram),ctypes.byref(px),ctypes.byref(py)))
        wx=int.from_bytes(ram[0x2ad:0x2af],'little',signed=True)+(ram[0x4001]&0xf0)
        wy=int.from_bytes(ram[0x2af:0x2b1],'little',signed=True)+(ram[0x4002]&0xf0)
        if ram[0x407]:wx%=width;wy%=height
        position_guard=(ram[0x401]&4)!=0 and ram[0x4000]<=3 and not ram[0x4005]&3 and not any(ram[0x471:0x475]) and 0<=wx<width and 0<=wy<height
        checks[tag+'_original_anchor']=accepted==position_guard and (not accepted or (px.value,py.value)==(wx,wy))
        for field,value in [(0x20,5),(0x401,0),(0x4000,255),(0x4005,1),(0x471,1),(0x473,1),(0x46d,0),(0x46e,16)]:
            altered=bytearray(ram);altered[field]=value
            ab=(ctypes.c_uint8*len(ram)).from_buffer_copy(altered)
            px.value=py.value=-999
            checks[tag+f'_marker_refusal_{field:x}']=not lib.FoundationMapPosition(ab,len(ram),ctypes.byref(px),ctypes.byref(py)) and (px.value,py.value)==(-999,-999)
        for slot,bad in [(1,len(ram)-1),(3,0x7fff),(5,255)]:
            args=[buffer,len(ram),vb,0x8000,pb,256,0,0,ctypes.byref(result)]
            args[slot]=bad;result.value=0xdeadbeef
            checks[tag+f'_sample_bounds{slot}']=not lib.FoundationMapSample(*args) and result.value==0xdeadbeef
        lib.FoundationFieldReset()
        result.value=0xdeadbeef
        checks[tag+'_reset_discards_field']=not lib.FoundationMapSample(buffer,len(ram),vb,0x8000,pb,256,0,0,ctypes.byref(result)) and result.value==0xdeadbeef
        receipts.append({'prefix':str(prefix),'inputs':{k:{'path':str(parts[k]),'sha256':sha(v)} for k,v in raw.items()},
                         'scene':int.from_bytes(ram[0x40e:0x410],'little'),'world_size':[width,height], 'overview_size':[cw,ch],
                         'overview_sha256':sha(pixels),'player_available':accepted,'player_original_anchor':[wx,wy],
                         'overview_pixels':cw*ch,'host_check_seconds':time.perf_counter()-started})
    report={'status':'pass' if all(checks.values()) else 'fail','checks':checks,'capture_count':len(receipts),'pixel_comparisons':count,
            'source_sha256':{f:sha((authored/f).read_bytes()) for f in ['foundation_map.c','foundation_map.h','foundation_field.c','foundation_field.h']},
            'rom_sha256':sha(rom),'captures':receipts,
            'limits':['Pure authored core and independent original word/4bpp/palette oracle only','Marker guard faults are synthetic host controls',
                      'No host UI/input/pacing qualification in this check','No natural full campaign, permanent visited history or enemy/item locations; town/objective metadata tested separately',
                      'No owner save/settings/ROM writes; colors are current original loaded graphics snapshots']}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':len(checks),'pixel_comparisons':count,'failed':[k for k,v in checks.items() if not v],'report':str(output/'report.json')}))
    return report['status']=='pass'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,default=ROOT/'local/inputs/clean-usa.sfc')
    p.add_argument('--prefix',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--runtime',type=Path,default=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src')
    configured=Path(r'C:\Users\crono\.local\share\retcomm\toolchains\cmake-clang-v1\latest\bin\clang.exe')
    p.add_argument('--compiler',default=str(configured) if configured.exists() else shutil.which('clang'))
    args=p.parse_args()
    if not args.compiler:p.error('A standalone C compiler is required')
    return 0 if run(args.rom,args.prefix,args.output,args.runtime,args.compiler) else 1


if __name__=='__main__':
    raise SystemExit(main())
