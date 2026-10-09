"""Replay external packet fixtures through a selected ordinary-party/reserved actor observer.

No guest execution or original assets are embedded. Actor source must expose the
party/reserved observer contract; field source is linked independently.
"""
from pathlib import Path
import hashlib,json,subprocess,argparse,time,os
ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CLEAN='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--clang',type=Path,default=Path('C:/Users/crono/.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe'))
    a.add_argument('--actor-source-dir',type=Path,required=True,help='Directory containing foundation_wide_actors.c/h to compile')
    a.add_argument('--field-source-dir',type=Path,required=True,help='Directory containing foundation_field.c/h to link')
    a.add_argument('--fixtures',type=Path,default=ROOT/'local/runs/actor-wide-20261009-133859/sweep-on/dump',help='External copied dump namespace containing five adjacent packet pairs')
    a.add_argument('--rom',type=Path,default=ROOT/'local/inputs/clean-usa.sfc',help='Exact clean local ROM, read only')
    a.add_argument('--out',type=Path,help='Fresh output directory beneath project local/')
    args=a.parse_args()
    actor=args.actor_source_dir.resolve();field=args.field_source_dir.resolve()
    for directory,names in [(actor,['foundation_wide_actors.c','foundation_wide_actors.h']),(field,['foundation_field.c','foundation_field.h'])]:
        if not all((directory/name).is_file() for name in names):a.error('Required C/header pair missing from '+str(directory))
    out=(args.out or ROOT/'local/evidence'/('reserved-actors-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    if out.exists() or not out.is_relative_to(ROOT/'local'):a.error('Use a fresh output directory beneath project local/')
    out.mkdir(parents=True)
    runtime=ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
    authored=ROOT/'native/foundation/src'
    files=[HERE/'foundation_reserved_actor_canary.c',field/'foundation_field.c',runtime/'sha256.c',runtime/'snes/ppu.c',runtime/'snes/ppu_legacy.c',runtime/'snes/ws_shadow.c']
    source=[actor/'foundation_wide_actors.c',actor/'foundation_wide_actors.h',HERE/'check_foundation_reserved_actors.py',field/'foundation_field.h',*files]
    frozen=[authored/'foundation_wide_actors.c',authored/'foundation_wide_actors.h',ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/src/foundation_wide_actors.c',ROOT/'local/native-proof/SecretOfTheStarsSNESRecomp/src/foundation_wide_actors.h']
    rom=args.rom.resolve()
    if not rom.is_file() or sha(rom)!=CLEAN:a.error('ROM must match exact clean SHA-256 '+CLEAN)
    fixtures=args.fixtures.resolve()
    tags=['start','edge','entered','further','return']
    inputs=[rom,*[fixtures/(tag+ext) for tag in tags for ext in ['.wram.bin','.vram.bin','.cgram.bin','_next.oam.bin']]]
    # Protect older private proofs when present, without requiring a historical
    # prototype for future runs against qualified authored source.
    frozen += [p for p in [ROOT/'local/evidence/party-actor-prototype-20261009/src/foundation_wide_actors.c',ROOT/'local/evidence/party-actor-prototype-20261009/src/foundation_wide_actors.h'] if p.is_file()]
    missing=[str(p) for p in [*inputs,*source,*frozen] if not p.is_file()]
    if missing:a.error('Required read-only input missing: '+', '.join(missing))
    before={str(p):sha(p) for p in [*inputs,*source,*frozen]}
    exe=out/'reserved-actor-canary.exe'
    compiled=subprocess.run([str(args.clang),'-std=c11','-O2','-I',str(actor),'-I',str(field),'-I',str(runtime),*[str(p) for p in files],'-o',str(exe)],capture_output=True,text=True)
    (out/'compile.txt').write_text(compiled.stdout+compiled.stderr)
    report={'scope':'Selected integrated party/ordinary-reserved observer; registered observer CPU seams and registered DMA notifications are replayed by the host harness. No guest constructor or DMA engine executes.',
            'baseline_authored_actor_sha256':before[str(frozen[0])],
            'selected_actor_source_sha256':before[str(source[0])],
            'selected_field_source_sha256':before[str(field/'foundation_field.c')],
            'actor_source_dir':str(actor),'field_source_dir':str(field),'fixture_dir':str(fixtures),
            'protected_inputs_before':before,'compile_exit':compiled.returncode,'cases':{},'checks':{},
            'limits':['No integrated guest-opcode observer coverage or candidate EXE',
                      'Natural sample contains one ordinary party member; no natural offscreen party or enabled multiple-member fixture',
                      'Synthetic record movement, second member and phase do not certify campaign activation/movement',
                      'Ordinary17/18 have host-synthetic positives only; B0, party A8 special emitter, variable/composite/wrap/nonzero-offset eligibility remains refused; regular A8 artwork uses the ordinary emitter',
                      'Headless metadata/OAM proof is separate from audible/GPU/controller and per-pixel composition proof']}
    if not compiled.returncode:
        report['harness_executable_sha256']=sha(exe)
        scenarios={0:'natural-data',1:'synthetic-two-members-right300-left505',2:'reject-partyB0',3:'reject-derivedA8',4:'reject-high-pose',5:'reject-variable-route',6:'reject-wrap',7:'reject-nonzero-offset',8:'synthetic-reserved17-culled',9:'synthetic-per-record-phase',10:'reject-visible-party-staging-word',11:'reject-cpu-data-bank',12:'reject-party-record-pointer',13:'reject-party-end-cursor',14:'reject-regular-begin-cursor',15:'reject-party-cpu-width',16:'reject-resource-transition',17:'reject-field-route-placeholder',18:'reject-ppu-layout',19:'reject-party-mask',20:'reject-derivedA9-from-baseA7',21:'synthetic-ordinary-regular-A8',
          30:'synthetic-both-reserved-visible',31:'synthetic-only18-visible',32:'synthetic17-culled18-visible',33:'synthetic-both-reserved-culled',34:'synthetic17-visible18-culled',35:'synthetic-only17-visible',36:'synthetic-reserved-center-anchors',
          40:'reject-reserved17-B0',41:'reject-reserved18-B0',42:'synthetic-reserved17-A8',43:'synthetic-reserved18-A8',44:'reject-reserved-pose',45:'reject-reserved-staging-x',46:'reject-reserved-staging-word',47:'reject-reserved-size-bit',48:'reject-reserved-DP34',49:'reject-reserved-DP38',50:'reject-reserved-advanced-append-cursor',51:'reject-reserved-parked-coordinate',52:'reject-reserved-duplicate-capture',53:'reject-reserved-pointer',54:'reject-reserved-late-B0',55:'reject-reserved-late-A8-stale-staging',56:'reject-reserved-mask',57:'reject-reserved-missing-capture',58:'synthetic-reserved17-late-A8-matching-staging',59:'reject-reserved-descriptor-limit',60:'reject-reserved-late-descriptor-limit'}
        #17 is redundant with independently checked packet/restore guards; do not invent it.
        del scenarios[17]
        for scenario,label in scenarios.items():
            for tag in (tags if not scenario else ['start']):
                name=label+'-'+tag
                command=[str(exe),str(rom),str(fixtures/(tag+'.wram.bin')),str(fixtures/(tag+'.vram.bin')),str(fixtures/(tag+'.cgram.bin')),str(fixtures/(tag+'_next.oam.bin')),str(out),str(scenario)]
                env=os.environ.copy();env['SNESRECOMP_FOUNDATION_WIDE_ACTORS']='1';env.pop('SNESRECOMP_FOUNDATION_ACTORS_TRACE',None)
                p=subprocess.run(command,capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW,env=env)
                (out/(name+'.txt')).write_text(p.stdout+p.stderr)
                result={'exit':p.returncode,'scenario':scenario,'fixture':tag,'input_kind':'genuine-adjacent-data' if not scenario else 'synthetic-mutated-host-records'}
                if not p.returncode:
                    result.update(json.loads(p.stdout))
                report['cases'][name]=result
        report['checks']['all_host_replays_exit_normally']=all(c['exit']==0 for c in report['cases'].values())
        natural=[c for c in report['cases'].values() if c['scenario']==0]
        report['checks']['all_five_natural_packets_accept_one_member_and_preserve_regular_cache']=len(natural)==5 and all(c.get('accepted') and c.get('party_count')==1 and c.get('regular_count',0)>0 and c.get('natural_stage_matches_actual_scanout') for c in natural)
        report['checks']['natural_party_margin_coverage_explicitly_absent']=all(c.get('max_party_side_pieces_per_line')==0 for c in natural)
        two=report['cases']['synthetic-two-members-right300-left505-start']
        report['checks']['synthetic_two_members_produce_margin_metadata']=two.get('party_count')==2 and two.get('max_party_side_pieces_per_line',0)>0
        positives={0,1,8,9,21,42,43,58,*range(30,37)}
        report['checks']['all_requested_refusal_cases_reject']=all(c.get('negative_guard_passed') for c in report['cases'].values() if c['scenario'] not in positives)
        reserved=[c for c in report['cases'].values() if c['scenario'] in range(30,37)]
        report['checks']['all_seven_reserved_patterns_accept']=len(reserved)==7 and all(c.get('accepted') for c in reserved)
        report['checks']['natural_active_reserved_coverage_remains_zero']=all(c.get('reserved_count')==0 for c in natural)
        report['checks']['synthetic_only18_compacts_to_slots4through7']=report['cases']['synthetic-only18-visible-start'].get('reserved_end_slot')==8
        report['checks']['synthetic_culled17_compacts18_to_slots4through7']=report['cases']['synthetic17-culled18-visible-start'].get('reserved_end_slot')==8
        report['checks']['synthetic_reserved_output_does_not_advance_046B']=all(c.get('append_end_slot')==12 for c in reserved)
        report['checks']['synthetic_offscreen_reserved_margin_pieces_present']=all(c.get('max_reserved_side_pieces_per_line',0)>0 for c in reserved if c['scenario']!=36)
        report['checks']['regular_A8_artwork_uses_ordinary_original_emitters']=all(c.get('accepted') and c.get('regular_A8_descriptor_checked') for c in report['cases'].values() if c['scenario'] in {21,42,43,58})
        report['checks']['synthetic_priority_reserved17_before18_before_party_via_actual_PPU_composer']=report['cases']['synthetic-both-reserved-visible-start'].get('synthetic_priority_control_checked') is True
    after={str(p):sha(p) for p in [*inputs,*source,*frozen]}
    report['protected_inputs_after']=after
    report['checks']['all_inputs_and_frozen_authored_live_sources_preserved']=before==after
    report['passed']=compiled.returncode==0 and all(report['checks'].values())
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(out);print(json.dumps({'passed':report['passed'],'checks':report['checks'],'cases':len(report['cases'])},indent=2))
    raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
