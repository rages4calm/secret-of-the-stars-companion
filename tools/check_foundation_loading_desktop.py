"""Check copied natural loading and v3 continuation with Windows video/audio."""
from pathlib import Path
import argparse
import array
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from check_foundation_loading import EXTENSIONS, SCRIPT

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--loading-report',type=Path,required=True)
    args=parser.parse_args()
    proof=json.loads(args.loading_report.read_text())
    assert proof['passed'] and proof['executable_sha256']==sha(args.exe)
    owner=ROOT/'local/player-foundation'
    protected={p.relative_to(owner).as_posix():sha(p) for p in list(owner.glob('*'))+list((owner/'saves').glob('*')) if p.is_file()}
    inputs={p:sha(p) for p in [ROOT/'Tecmo Secret of the Stars (USA).sfc',ROOT/'local/inputs/clean-usa.sfc']}
    base=ROOT/'local/runs'/('loading-desktop-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir()
    report={'executable_sha256':sha(args.exe),'checks':{},'cases':{},'limits':[
        'Copied Windows/GPU and actual SDL callback PCM; no physical controller, listening or monitor scanout claim',
        'Original-cost native clear: no guest CPU acceleration or scrolling slowdown fix']}
    def run(name,state,native,script,capture):
        d=base/name;d.mkdir();(d/'dump').mkdir()
        shutil.copy2(args.exe,d/'game.exe');shutil.copy2(state,d/'resume.state')
        for name in ['config.ini','keybinds.ini','foundation.ini']:shutil.copy2(owner/name,d/name)
        (d/'input.txt').write_text(script)
        env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SNESRECOMP_HOST_PROFILE='1',SNESRECOMP_FOUNDATION_NATIVE_CLEAR='original' if native else '0',
            SNESRECOMP_FOUNDATION_WIDE='0',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='1',
            SNESRECOMP_AUDIO_OUTPUT_RAW=str(d/'audio.pcm'),SNESRECOMP_DUMP_DIR=str(d/'dump'),
            SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(d/'present.bgrx'),SNESRECOMP_FOUNDATION_CAPTURE_AT=str(capture))
        with (d/'host.log').open('w') as stream:
            result=subprocess.run([str(d/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc'),
                '--resume-state',str(d/'resume.state'),'--script',str(d/'input.txt')],cwd=d,env=env,
                stdout=stream,stderr=stream,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(d/'host.log').read_text(errors='replace')
        pcm=array.array('h');pcm.frombytes((d/'audio.pcm').read_bytes())
        first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
        match=re.search(r'\[foundation_clear\] native_instructions=(\d+)',log)
        count=int(match.group(1)) if match else 0
        checks={'exit_zero':result.returncode==0,'resumed':'resume state loaded:' in log,
            'actual_gpu_vsync':'Renderer: direct3d11 (vsync=1 ' in log,
            'audio_nonzero_early':first is not None and first<.5,
            'capture_enhanced_original_width':len((d/'present.bgrx').read_bytes())==512*448*4,
            'native_route_expected':count>0 if native else count==0}
        report['cases'][d.name]={'checks':checks,'first_audio_seconds':first,'native_instructions':count,'passed':all(checks.values())}
        return d
    for name,state,script,capture in [
        ('natural',ROOT/'local/runs/likado-inside-a/saves/save0.sav',SCRIPT,220),
        ('mid-clear',args.loading_report.parent/'mid-save/saves/save0.sav','wait 102\ndump after\nquit\n',90)]:
        off=run(name+'-original',state,False,script,capture);on=run(name+'-native',state,True,script,capture)
        tags=[p.name[:-len('.wram.bin')] for p in (off/'dump').glob('*.wram.bin')]
        report['checks'][name+'_guest_snapshots_identical']=bool(tags) and all((off/'dump'/(tag+'.'+ext)).read_bytes()==(on/'dump'/(tag+'.'+ext)).read_bytes() for tag in tags for ext in EXTENSIONS)
        report['checks'][name+'_composed_pixels_identical']=(off/'present.bgrx').read_bytes()==(on/'present.bgrx').read_bytes()
    report['checks']['owner_files_unchanged']=all(sha(owner/n)==v for n,v in protected.items())
    report['checks']['rom_inputs_unchanged']=all(sha(p)==v for p,v in inputs.items())
    report['passed']=all(report['checks'].values()) and all(c['passed'] for c in report['cases'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
