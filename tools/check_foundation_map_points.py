"""Independent original-exit/name oracle for the read-only map-point module.

The owned clean ROM is read at run time. ROM-derived reports stay in the caller's
private output. This is finite host/parser evidence, not campaign/gameplay proof.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Point(C.Structure):
    _fields_=[('x',C.c_int),('y',C.c_int),('objective',C.c_uint),('label',C.c_char*24)]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True,help='Runtime runner/src with sha256.c/h');p.add_argument('--cc');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rom_path=a.rom.resolve(strict=True);data=rom_path.read_bytes();assert len(data)==1572864 and sha(rom_path)==ROM_SHA
    runtime=a.runtime.resolve(strict=True);source=ROOT/'native/foundation/src';output=a.output.resolve();assert not output.exists();output.mkdir(parents=True)
    inputs=[rom_path,source/'foundation_map_points.c',source/'foundation_map_points.h',source/'foundation_map.h',runtime/'sha256.c',runtime/'sha256.h',Path(__file__).resolve()]
    before={str(x):sha(x)for x in inputs};checks=[];proofs=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    compiler=a.cc or shutil.which('clang');assert compiler
    library=output/'points.dll'
    # Private-only corruption harness reaches bounded parsing independently of
    # the production clean-image SHA admission. No bypass enters native builds.
    wrapper=output/'parser-test-wrapper.c'
    wrapper.write_text('#include "'+(source/'foundation_map_points.c').as_posix()+'"\n'
        'int PointsParserTestBuild(const uint8_t *rom,size_t size,const uint8_t *ram,size_t ram_size,unsigned scene,unsigned width,unsigned height,int destination,FoundationMapPoint *points,size_t capacity,size_t *count){\n'
        'if(!count)return 0;*count=0;if(!rom||size!=ImageSize||!ram||ram_size!=RamSize||!points||capacity>MaxPoints)return 0;Image image={rom,size};return Build(&image,ram,scene,width,height,destination,points,capacity,count);}\n')
    command=[compiler,'-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-DFOUNDATION_MAP_STANDALONE','-DFOUNDATION_MAP_POINTS_STANDALONE','-I'+str(runtime),str(wrapper),str(runtime/'sha256.c'),'-o',str(library)]
    result=subprocess.run(command,capture_output=True,text=True);(output/'compile.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
    lib=C.CDLL(str(library));build=lib.FoundationMapPointsBuild
    build.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_void_p,C.c_size_t,C.c_void_p];build.restype=C.c_int
    parser=lib.PointsParserTestBuild;parser.argtypes=build.argtypes;parser.restype=C.c_int
    image=(C.c_ubyte*len(data)).from_buffer_copy(data)
    def read(address,size=1):
        bank,low=address>>16,address&65535;assert bank<48 and low>=32768 and low+size<=65536
        offset=bank*32768+low-32768;assert offset+size<=len(data)
        return int.from_bytes(data[offset:offset+size],'little')
    def story(r,selector,nibble):
        if selector<120:return r[0x5360+((selector>>3)&1)]&(128>>(selector&7))
        if selector==126:return r[0x5361]&15
        if selector==255:return (r[0x5362+(nibble>>1)]&15)if nibble&1 else r[0x5362+(nibble>>1)]>>4
        return r[0x5362+((selector&127)>>3)]&(128>>(selector&7))
    def selected(r,scene,record=False):
        assert 0<=scene<337;cursor=0x80000|read(0x88000+scene*2,2)
        for _ in range(52):
            kind=read(cursor);assert kind in list(range(8))+[255]
            if kind==255:return cursor if record else 0x80000|read(cursor+1,2)
            x,y,stage=read(cursor+1),read(cursor+2),r[0x5372]
            values=[stage<x or(stage==x and not story(r,y,y)),stage==x and bool(story(r,y,y)),stage<=x,stage==x and story(r,126,0)==y,bool(story(r,x|128,y)),not story(r,x|128,y),story(r,255,x)==y,bool(r[0x4b6]&128)]
            if values[kind]:return cursor if record else 0x80000|read(cursor+3,2)
            cursor+=5
        raise AssertionError('No selected stream')
    def name_index(r,scene):
        stream=selected(r,scene);flags=read(stream,2);cursor=stream+15
        for mask,size in [(0x6000,2),(0x1000,1),(128,2),(64,1),(32,1),(16,2)]:
            if flags&mask:cursor+=size
        if flags&8:cursor+=5 if read(cursor)&128 else 8
        if flags&4:cursor+=2
        return read(cursor)if flags&2 else -1
    def label(r,index):
        if index==0 and r[0x546a]not in(0,255):
            text=[]
            for value in r[0x546a:0x5482]:
                if value==255:return ''.join(text).rstrip()
                assert value==128 or 129<=value<=154
                text.append(' 'if value==128 else chr(value-129+65))
            raise AssertionError('Mutable town name not terminated')
        cursor=0x40000|read(0x4c200+index*2,2);text=[]
        for _ in range(24):
            v=read(cursor);cursor+=1
            if v in(0,255):return ''.join(text).rstrip()
            assert v==128 or 129<=v<=154
            text.append(' 'if v==128 else chr(v-129+65))
        raise AssertionError('Name not terminated')
    def exits(r,scene):
        stream=selected(r,scene);idx=read(stream+10,2);assert idx<384;cursor=0x80000|read(0x8aa00+idx*2,2);records=[]
        for _ in range(512):
            if read(cursor,2)==65535:return records
            records.append((read(cursor),read(cursor+1),read(cursor+2),read(cursor+3,2)&16383));cursor+=8
        raise AssertionError('Exit list not terminated')
    def oracle(r,destination):
        groups={}
        for x,y,flags,dest in exits(r,0):
            if flags:continue
            index=name_index(r,dest);objective=dest==destination
            if not(0<=index<23)and not objective:continue
            key=dest
            if key not in groups:groups[key]=[[],index,objective]
            groups[key][0].append((x,y))
        result=[];objectives=[]
        for dest,(positions,index,objective) in groups.items():
            point=(sum(x for x,y in positions)*16//len(positions)+8,sum(y for x,y in positions)*16//len(positions)+8,0,label(r,index)if 0<=index<23 else'CURRENT OBJECTIVE')
            if 0<=index<23:result.append(point)
            if objective:objectives.append(point)
        if not objectives and destination>=0:
            for dest,(positions,index,_) in groups.items():
                if 0<=index<23 and any(flags==0 and target==destination for x,y,flags,target in exits(r,dest)):
                    objectives.append((sum(x for x,y in positions)*16//len(positions)+8,sum(y for x,y in positions)*16//len(positions)+8,0,label(r,index)))
        if len(objectives)==1:
            point=objectives[0];result.append((point[0],point[1],1,point[3]))
        return result
    def actual(r,destination=-1,scene=0,width=3584,height=3584,capacity=32,trusted_corruption=False):
        ram=(C.c_ubyte*len(r)).from_buffer_copy(r);points=(Point*32)();C.memset(points,0x5a,C.sizeof(points));before_points=bytes(points);count=C.c_size_t(99)
        ok=(parser if trusted_corruption else build)(image,len(data),ram,len(r),scene,width,height,destination,points,capacity,C.byref(count))
        return ok,[(v.x,v.y,v.objective,v.label.decode('ascii'))for v in points[:count.value]],count.value,bytes(points)==before_points
    failure=None
    try:
        r=bytearray(0x20000);records=exits(r,0);check('Original world list contains all113 records',len(records)==113)
        for stage in range(256):
            for pattern in(0,255):
                r[0x5360:0x53e2]=bytes([pattern])*0x82;r[0x5372]=stage;r[0x4b6]=pattern&128
                expected=oracle(r,-1);ok,points,_,_=actual(r)
                check(f'Chapter{stage}/story{pattern} agrees with independent original decoder',ok==1 and points==expected)
                if stage in(0,1,2,3,4,5,255)and pattern==0:proofs.append({'chapter':stage,'story_pattern':pattern,'points':points})
        r=bytearray(0x20000)
        for destination in(5,39,50,58,59,67,85,151):
            expected=oracle(r,destination);ok,points,_,_=actual(r,destination)
            check('Verified destination '+str(destination)+' follows original exits',ok==1 and points==expected)
            proofs.append({'chapter':0,'verified_destination_control':destination,'points':points,'one_hop_original_edges':[(town,destination)for town in{dest for x,y,flags,dest in exits(r,0)if flags==0 and 0<=name_index(r,dest)<23}if any(flags==0 and target==destination for x,y,flags,target in exits(r,town))]})
        r[0x546a:0x5482]=bytes([129,130,128,131,255])+bytes(19)
        ok,points,_,_=actual(r);check('Current mutable town-name0 follows original RAM buffer',ok==1 and points==oracle(r,-1)and any(point[3]=='AB C'for point in points))
        r[0x546a:0x5482]=bytes([129])*24;ok,_,count,intact=actual(r);check('Unterminated mutable town name refuses all-or-nothing',ok==0 and count==0 and intact)
        r[0x546a:0x5482]=bytes([1,255])+bytes(22);ok,_,count,intact=actual(r);check('Unreadable mutable town name refuses all-or-nothing',ok==0 and count==0 and intact)
        r[0x546a:0x5482]=bytes(24)
        for scene,width,height,capacity,dest in[(337,3584,3584,32,-1),(0,3583,3584,32,-1),(0,3584,3840,32,-1),(0,3584,3584,0,-1),(0,3584,3584,33,-1),(0,3584,3584,32,337)]:
            ok,_,count,intact=actual(r,dest,scene,width,height,capacity);check('Invalid arguments refuse all-or-nothing '+str((scene,width,height,capacity,dest)),ok==0 and count==0 and intact)
        ok,points,count,intact=actual(r,-1,5,256,256);check('Local areas carry no guessed town metadata',ok==1 and points==[]and count==0 and intact)
        image[0]^=1;ok,_,count,intact=actual(r);check('Tampered owned image refuses before output writes',ok==0 and count==0 and intact);image[0]^=1
        def offset(address):return(address>>16)*32768+(address&65535)-32768
        stream=selected(r,0);chosen=selected(r,0,True);chosen_value=chosen+(1 if read(chosen)==255 else 3)
        world=0x80000|read(0x8aa00,2);sentinel=world+len(records)*8
        corruptions=[('unsupported world exit flag',[(world+2,1)]),('world coordinate outside dimensions',[(world,255)]),
            ('destination outside scene table',[(world+3,255),(world+4,255)]),('list pointer before exit domain',[(0x8aa00,0),(0x8aa01,170)]),
            ('header index outside pointer table',[(stream+10,255),(stream+11,255)]),('selected stream outside header domain',[(chosen_value,255),(chosen_value+1,255)]),
            ('missing terminator refuses at next-list boundary',[(sentinel,0),(sentinel+1,0)])]
        for label,changes in corruptions:
            for address,value in changes:image[offset(address)]=value
            ok,_,count,intact=actual(r,trusted_corruption=True)
            check('Synthetic parser '+label+' refuses all-or-nothing',ok==0 and count==0 and intact)
            for address,value in changes:image[offset(address)]=data[offset(address)]
    except Exception as error:failure=repr(error)
    after={str(x):sha(x)for x in inputs};report={'passed':failure is None and before==after,'failure':failure,'checks':len(checks),'cases':checks,'original_exit_records':len(records),'private_original_decoder_points':proofs,'protected':before,'protected_unchanged':before==after,'scope':'Pure original-ROM parser/oracle and synthetic chapter/story/argument/tamper/malformed-list controls only. Private corruption wrapper bypasses SHA admission solely to test parser refusal; production admission remains separately checked. No native rendering, campaign, objective-event acquisition or paced performance claim.'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in('cases','private_original_decoder_points','protected')},indent=2));return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
