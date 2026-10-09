"""Verify ordinary party observer lineage in an existing private gameplay replay.

Requires a passing actor guest/center parity report and the same frozen EXE.
This checks natural producer/capture/completed-DMA observations; it does not
claim natural multi-member or offscreen party gameplay from synthetic tests.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,required=True)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    replay=args.replay.resolve()
    report_path=replay/'report.json'
    source=json.loads(report_path.read_text())
    report_hash,exe_hash=sha(report_path),sha(args.exe)
    assert source['passed'] and source['executable_sha256']==exe_hash
    out=(args.out or ROOT/'local/evidence'/('party-lineage-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    assert not out.exists() and out.is_relative_to((ROOT/'local').resolve())
    out.mkdir(parents=True)
    checks={};cases={};traces={}
    for name in ('sweep','enhanced-sweep','menu','cold','rollback'):
        path=replay/(name+'-on')/'actors.csv'
        traces[str(path.relative_to(ROOT))]=sha(path)
        with path.open() as f:
            rows=[{k:v if k=='event' else int(v,0) for k,v in row.items()}
                  for row in csv.DictReader(f)]
        started={};captures={};ended={};staged={};completed={}
        capture_count=frames=packet_count=0;failures=[]
        identity=lambda r:tuple(r[k] for k in ('party_seen','party_end_slot',
                                              'party0_descriptor','party0_x','party0_y','party0_phase'))
        def require(ok,label,r):
            if not ok and len(failures)<12:failures.append(dict(check=label,frame=r['frame'],epoch=r['epoch']))
        for r in rows:
            key=(r['generation'],r['epoch'])
            event=r['event']
            if event=='party_begin' and r['packet_match']:
                started[key]=r
            elif event=='party_capture' and r['packet_match']:
                require(key in started,'capture_has_begin',r)
                require((r['cpu_d'],r['cpu_db'],r['cpu_m'],r['cpu_x'])==(0x0e00,1,0,1),'capture_cpu_context',r)
                require(r['party_count']>=1 and r['party_seen']&1 and
                        0x0e9800<=r['party0_descriptor']<=0x0ed7f8 and
                        r['party0_phase'] in (0,1),'positive_original_party_metadata',r)
                captures[key]=r;capture_count+=1
            elif event=='party_end' and r['packet_match']:
                require(key in captures,'end_has_capture',r)
                require(key in captures and identity(r)[2:]==identity(captures[key])[2:],
                        'end_retains_captured_party_pose',r)
                require(r['party_seen'].bit_count()==r['party_count'] and
                        r['party_end_slot']==12+4*r['party_count'],'ordinary_visible_party_cursor',r)
                ended[key]=r
            elif event=='begin' and r['packet_match']:
                require(key in ended and r['start_slot']==r['party_end_slot'],'regular_retains_party_cursor',r)
            elif event=='staging_ready' and r['packet_valid']:
                require(key in ended and identity(r)==identity(ended[key]),'staging_has_party_identity',r)
                staged[key]=r
            elif event=='dma_complete' and r['packet_valid']:
                require(key in staged and r['packet_match'] and identity(r)==identity(staged[key]),'completed_packet_has_party_identity',r)
                completed[key]=r;packet_count+=1
            elif event=='frame' and r['packet_valid']:
                require(key in completed and identity(r)==identity(completed[key]),'displayed_party_matches_completed_packet',r)
                frames+=1
            elif event=='reset':
                require(not r['packet_valid'] and not r['party_count'] and not r['party_seen'],'reset_clears_party_metadata',r)
        checks[name+'_actual_party_capture']=capture_count>0
        checks[name+'_completed_party_packets']=packet_count>0
        checks[name+'_displayed_party_frames']=frames>0
        checks[name+'_party_lineage_and_context']=not failures
        cases[name]=dict(party_captures=capture_count,completed_packets=packet_count,
                         displayed_frames=frames,failures=failures)
    checks['all_inputs_unchanged']=sha(report_path)==report_hash and sha(args.exe)==exe_hash and all(sha(ROOT/p)==d for p,d in traces.items())
    report=dict(passed=all(checks.values()),checks=checks,cases=cases,
                executable_sha256=sha(args.exe),guest_center_parity_report=str(report_path.relative_to(ROOT)),
                guest_center_parity_report_sha256=sha(report_path),trace_sha256=traces,
                checker_sha256=sha(Path(__file__)),
                limits='Natural single visible party member and regular list; no natural multi-member or party-margin positivity; synthetic party coordinates tested separately')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
