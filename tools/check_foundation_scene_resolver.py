"""Check all inventoried primary resources through the actual native resolver.

These are synthetic host views of original ROM resources, not campaign visits.
Story tables point to an original no-match sentinel; live replacements have a
separate checker. The inactive secondary layer is deliberately not invented.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import subprocess
import time

from check_foundation_map_resolver import make_view, expected, View
from inspect_foundation_maps import OriginalMaps, ROM_SHA256, ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    output = (args.out or ROOT/'local/evidence'/('scene-native-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if output.exists() or not output.is_relative_to((ROOT/'local').resolve()):
        parser.error('Choose a fresh private directory under project local/')
    output.mkdir(parents=True)
    rom_path = ROOT/'local/inputs/clean-usa.sfc'
    assert sha(rom_path) == ROM_SHA256
    inventory = json.loads(args.inventory.read_text())
    assert inventory['passed'] and inventory['rom_sha256'] == ROM_SHA256
    maps = OriginalMaps(rom_path.read_bytes())
    source = ROOT/'native/foundation/src'
    runtime = ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    compiler = Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe'
    library = output/'scene-resolver.dll'
    command = [str(compiler), '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared',
               '-DFOUNDATION_FIELD_STANDALONE', '-I'+str(source), '-I'+str(runtime),
               str(source/'foundation_field.c'), str(runtime/'sha256.c'), '-o', str(library)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (output/'compile.log').write_text(compiled.stdout+compiled.stderr)
    assert compiled.returncode == 0
    dll = ctypes.CDLL(str(library))
    dll.FoundationFieldBind.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    dll.FoundationFieldBind.restype = ctypes.c_int
    dll.FoundationFieldCheckView.argtypes = [ctypes.POINTER(View)]
    dll.FoundationFieldCheckView.restype = ctypes.c_int
    dll.FoundationFieldResolve.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint16)]
    dll.FoundationFieldResolve.restype = ctypes.c_int
    rom = (ctypes.c_uint8*len(maps.rom)).from_buffer_copy(maps.rom)
    assert dll.FoundationFieldBind(rom, len(maps.rom))
    # This genuine original F-list terminator is also a valid empty E list.
    # No record/key/flag is fabricated inside the original ROM.
    sentinel = 0x08f661
    assert maps.read(sentinel, 2) == 65535
    regs = {'inidisp':15, 'bgmode':9, 'mosaic':0, 'setini':0,
            'bgsc':[0x49,0x59,0x51,0], 'tm':0x17, 'ts':0,
            'bg_tile_adr':0x0400, 'hscroll':[0,0], 'vscroll':[0,0]}
    word = ctypes.c_uint16()
    records = []
    total = boundaries = 0
    for resource in inventory['primary_resources']:
        assert resource['resource_valid']
        ram = bytearray(0x20000)
        def put(at, value, size): ram[at:at+size] = int(value).to_bytes(size, 'little')
        put(0x20,1,1); put(0x050c,1,1)
        put(0x040e, resource['scene_indices'][0], 2)
        put(0x0407,resource['wrap'],1)
        for at,key in [(0x0513,'grid'),(0x0506,'cells'),(0x0500,'tiles'),(0x0537,'attributes')]:
            put(at,int(resource[key],16),3)
        width,height = resource['dimensions_segments']
        put(0x046d,width,1); put(0x046e,height,1)
        put(0x0453,sentinel,3); put(0x0456,sentinel,3)
        buffer,view = make_view(ram,regs)
        accepted = bool(dll.FoundationFieldCheckView(ctypes.byref(view)))
        failures=[]; count=0; edge_count=0
        def compare(x,y):
            ok=dll.FoundationFieldResolve(0,x,y,ctypes.byref(word))
            original=expected(maps,ram,0,x,y)
            if (not ok or word.value != original) and len(failures)<10:
                failures.append({'x':x,'y':y,'accepted':bool(ok),'native':word.value,'original':original})
        if accepted:
            for y in range(0,height*256,8):
                for x in range(0,width*256,8):
                    compare(x,y); count+=1
            for x in [-width*256-9,-72,-1,0,width*256-1,width*256,width*512+7]:
                for y in [-height*256-9,-1,0,height*256-1,height*256,height*512+7]:
                    compare(x,y);edge_count+=1
        records.append({'scene_references':resource['scene_indices'],
                        'resource_tuple':[resource['map_index'],resource['cell_index'],resource['tile_attribute_index'],width,height,resource['wrap']],
                        'native_cache_accepted':accepted,'full_grid_words':count,'boundary_words':edge_count,
                        'sample_failures':failures,'passed':accepted and not failures})
        total+=count;boundaries+=edge_count
    report={'passed':all(r['passed'] for r in records) and sha(rom_path)==ROM_SHA256,
            'rom_sha256':ROM_SHA256,'checker_sha256':sha(Path(__file__)),
            'inventory_sha256':sha(args.inventory),
            'native_sources':{n:sha(source/n) for n in ['foundation_field.c','foundation_field.h']},
            'primary_resource_tuples':len(records),'full_grid_words':total,'boundary_words':boundaries,
            'resources':records,
            'limits':['Synthetic host-only primary resource views, not naturally visited scenes or full campaign testing',
                      'Uses original no-match story-list sentinel; live E/F replacements and story selection are checked separately',
                      'No secondary stream, actor, pixel composition, GPU or audio certification']}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='resources'},indent=2))
    print(output)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
