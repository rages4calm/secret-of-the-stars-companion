"""Windows guard-page and undefined-behavior checks for the original map resolver.

Uses synthetic host views of inventoried original primary resources. Does not
launch the game or change guest timing, owner files, ROM or qualified sources.
Run with --inventory pointing to the primary inventory report.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from inspect_foundation_maps import OriginalMaps, ROOT, ROM_SHA256
from check_foundation_map_resolver import make_view, expected, View


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def worker(inventory_path, output):
    # Each input ends immediately before PAGE_NOACCESS. A C over-read crashes
    # this private child, allowing the parent to retain an explicit failure.
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.SetErrorMode.argtypes = [C.c_uint32]
    kernel.SetErrorMode.restype = C.c_uint32
    kernel.SetErrorMode(0x0001 | 0x0002)  # Retain child failures without an error dialog.
    kernel.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    kernel.VirtualAlloc.restype = C.c_void_p
    kernel.VirtualProtect.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.POINTER(C.c_uint32)]
    kernel.VirtualProtect.restype = C.c_int
    kernel.VirtualFree.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32]
    kernel.VirtualFree.restype = C.c_int
    allocations = []
    def guarded(size):
        assert size % 4096 == 0
        base = kernel.VirtualAlloc(None, size + 8192, 0x3000, 0x04)
        assert base, C.get_last_error()
        old = C.c_uint32()
        assert kernel.VirtualProtect(base, 4096, 0x01, C.byref(old))
        assert kernel.VirtualProtect(base+4096+size, 4096, 0x01, C.byref(old))
        allocations.append(base)
        return (C.c_uint8 * size).from_address(base+4096)
    rom_path = ROOT/'local/inputs/clean-usa.sfc'
    assert sha(rom_path) == ROM_SHA256
    maps = OriginalMaps(rom_path.read_bytes())
    inventory = json.loads(inventory_path.read_text())
    assert inventory['passed'] and inventory['rom_sha256'] == ROM_SHA256
    dll = C.CDLL(str(output/'map-memory.dll'))
    dll.FoundationFieldBind.argtypes = [C.POINTER(C.c_uint8), C.c_size_t]
    dll.FoundationFieldBind.restype = C.c_int
    for n in ('FoundationFieldCheckView','FoundationFieldCheckSceneView'):
        getattr(dll,n).argtypes = [C.POINTER(View)]
        getattr(dll,n).restype = C.c_int
    dll.FoundationFieldResolve.argtypes = [C.c_int,C.c_int,C.c_int,C.POINTER(C.c_uint16)]
    dll.FoundationFieldResolve.restype = C.c_int
    dll.FoundationFieldReset.argtypes = []
    dll.FoundationFieldReset.restype = None
    rom, ram = guarded(len(maps.rom)), guarded(0x20000)
    C.memmove(rom,maps.rom,len(maps.rom))
    assert dll.FoundationFieldBind(rom,len(maps.rom))
    regs = dict(inidisp=15,bgmode=9,mosaic=0,setini=0,bgsc=[0x49,0x59,0x51,0],
                tm=0x17,ts=0,bg_tile_adr=0x0400,hscroll=[0,0],vscroll=[0,0])
    counts = dict(resource_views=0,extreme_coordinate_pairs=0,malformed_resources=0,
                  invalid_arguments=0,cache_recoveries=0)
    coordinates = [-2147483648,-2147483647,-65537,-4097,-1,0,4097,65537,2147483647]
    def resolve(x,y,layer=0):
        out = C.c_uint16(0x5aa5)
        accepted = dll.FoundationFieldResolve(layer,x,y,C.byref(out))
        return bool(accepted),out.value
    def reject(view):
        assert not dll.FoundationFieldCheckSceneView(C.byref(view))
        assert resolve(0,0)==(False,0x5aa5)
    for r in inventory['primary_resources']:
        data = bytearray(0x20000)
        def put(at,value,size): data[at:at+size]=int(value).to_bytes(size,'little')
        put(0x20,1,1);put(0x50c,1,1);put(0x40e,r['scene_indices'][0],2)
        put(0x407,r['wrap'],1)
        for at,key in [(0x513,'grid'),(0x506,'cells'),(0x500,'tiles'),(0x537,'attributes')]:
            put(at,int(r[key],16),3)
        put(0x46d,r['dimensions_segments'][0],1);put(0x46e,r['dimensions_segments'][1],1)
        put(0x453,0x08f661,3);put(0x456,0x08f661,3)
        _,view=make_view(data,regs)
        view.ram=C.cast(ram,C.POINTER(C.c_uint8))
        C.memmove(ram,bytes(data),len(data))
        assert dll.FoundationFieldCheckView(C.byref(view))
        counts['resource_views']+=1
        for x in coordinates:
            for y in coordinates:
                ok,value=resolve(x,y)
                assert ok and value==expected(maps,data,0,x,y),(r,x,y,value)
                counts['extreme_coordinate_pairs']+=1
        for layer in (-2147483648,-1,1,2,2147483647):
            assert resolve(-2147483648,2147483647,layer)==(False,0x5aa5)
            counts['invalid_arguments']+=1
        assert not dll.FoundationFieldResolve(0,0,0,None)
        counts['invalid_arguments']+=1
        # These alter validated primary identity/extent, not speculative flags.
        bad = [(0x40e,337,2),(0x40e,65535,2),(0x50c,0,1)]
        bad += [(at,v,1) for at in (0x46d,0x46e) for v in (0,16,255)]
        bad += [(at,v,3) for at in (0x513,0x506,0x500,0x537)
                for v in (0,0x087fff,0x30ffff,0xffffff)]
        for at,value,size in bad:
            C.memmove(ram,bytes(data),len(data))
            for i in range(size): ram[at+i]=(value>>(i*8))&255
            reject(view);counts['malformed_resources']+=1
            C.memmove(ram,bytes(data),len(data))
            assert dll.FoundationFieldCheckView(C.byref(view))
            counts['cache_recoveries']+=1
        # Invalid sizes/pointers must be refused before touching guarded memory.
        original_size=view.ram_size
        for size in (0,1,0x1ffff,0x20001):
            view.ram_size=size;reject(view);counts['invalid_arguments']+=1
        view.ram_size=original_size
        view.ram=None;reject(view);counts['invalid_arguments']+=1
    dll.FoundationFieldReset()
    assert resolve(0,0)==(False,0x5aa5)
    assert not dll.FoundationFieldCheckView(None)
    # Wrong ROM sizes must not be hashed, even when the pointer is protected.
    protected=C.cast(allocations[0],C.POINTER(C.c_uint8))
    for size in (0,1,len(maps.rom)-1,len(maps.rom)+1):
        assert not dll.FoundationFieldBind(protected,size)
        counts['invalid_arguments']+=1
    assert not dll.FoundationFieldBind(None,len(maps.rom))
    for base in allocations: assert kernel.VirtualFree(base,0,0x8000)
    assert sha(rom_path)==ROM_SHA256
    (output/'worker-report.json').write_text(json.dumps(dict(passed=True,counts=counts),indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        worker(args.inventory,args.out);return 0
    out=(args.out or ROOT/'local/evidence'/('map-memory-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if out.exists() or not out.is_relative_to((ROOT/'local').resolve()):
        parser.error('Choose a fresh directory under project local/')
    out.mkdir(parents=True)
    source=ROOT/'native/foundation/src'
    runtime=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    sources=[source/'foundation_field.c',source/'foundation_field.h',runtime/'sha256.c']
    before={str(p.relative_to(ROOT)):sha(p) for p in sources}
    compiler=Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe'
    command=[str(compiler),'-std=c11','-O1','-Wall','-Wextra','-Werror','-shared',
             '-fsanitize=undefined','-fsanitize-trap=all','-DFOUNDATION_FIELD_STANDALONE',
             '-I'+str(source),'-I'+str(runtime),str(sources[0]),str(sources[2]),
             '-o',str(out/'map-memory.dll')]
    built=subprocess.run(command,capture_output=True,text=True,timeout=30)
    (out/'compile.log').write_text(built.stdout+built.stderr)
    assert built.returncode==0,built.stderr
    child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',
                          '--inventory',str(args.inventory.resolve()),'--out',str(out)],
                         capture_output=True,text=True,timeout=180)
    (out/'worker.log').write_text(child.stdout+child.stderr)
    result=json.loads((out/'worker-report.json').read_text()) if (out/'worker-report.json').exists() else {}
    result.update(child_exit_code=child.returncode,guard_pages='Both ends of exact ROM and WRAM buffers',
                  undefined_behavior_traps=True,source_hashes=before,
                  sources_unchanged=all(sha(ROOT/p)==d for p,d in before.items()),
                  checker_sha256=sha(Path(__file__)),inventory_sha256=sha(args.inventory),
                  limits='Host primary resource/cache tests; no campaign, cutscene, actor, GPU or audio certification')
    result['passed']=bool(result.get('passed') and child.returncode==0 and result['sources_unchanged'])
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
