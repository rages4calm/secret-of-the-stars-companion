"""Read-only inventory of possible B0 records in existing local gameplay dumps.

Raw records alone do not establish constructor execution or natural actor art.
No original bytes are exported outside the ignored local evidence directory.
"""
from pathlib import Path
import argparse,hashlib,json,time

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runs',type=Path,default=ROOT/'local/runs')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    output=args.out.resolve()
    assert output.is_relative_to((ROOT/'local').resolve()),'Derived game records must stay local.'
    assert not output.exists(),'Use a fresh output file.'
    seen=set();hits=[];scanned=0;invalid=[];started=time.time()
    for p in sorted(args.runs.rglob('*.wram.bin')):
        data=p.read_bytes();scanned+=1
        if len(data)!=131072:
            invalid.append({'path':str(p),'size':len(data)});continue
        digest=hashlib.sha256(data).hexdigest()
        if digest in seen:continue
        seen.add(digest);records=[]
        for family,base,stride,count,offset in [('party',0x4000,18,5,3),('regular',0x4100,25,19,5)]:
            for i in range(count):
                at=base+i*stride
                if data[at]!=255 and int.from_bytes(data[at+offset:at+offset+2],'little')==0xb0:
                    records.append({'family':family,'index':i,'pose':data[at],'record_hex':data[at:at+stride].hex()})
        if records:
            hits.append({'path':str(p),'sha256':digest,'mode':data[0x20],
                         'scene':int.from_bytes(data[0x43b:0x43d],'little'),'records':records})
    report={'files_scanned':scanned,'unique_full_wram':len(seen),'invalid_sizes':invalid,
            'candidate_captures':hits,'elapsed_seconds':time.time()-started,
            'limits':'Raw active-looking B0 records may be stale. Existing run dumps only; no constructor, packet, natural-art or campaign qualification.',
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(output),'files_scanned':scanned,'unique_full_wram':len(seen),'candidate_captures':len(hits)},indent=2))

if __name__=='__main__':main()
