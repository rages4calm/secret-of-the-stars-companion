"""Verify the isolated preview launcher and copied Windows/GPU presentation."""
from pathlib import Path
import array
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    owner = ROOT / 'local/player-foundation'
    protected = {p.relative_to(owner).as_posix(): sha(p) for p in list(owner.glob('*')) + list((owner/'saves').glob('*')) if p.is_file()}
    rom_hashes = {p: sha(p) for p in [ROOT/'Tecmo Secret of the Stars (USA).sfc', ROOT/'local/inputs/clean-usa.sfc']}
    base = ROOT/'local/runs'/('likado-desktop-'+time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    launch = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'tools/Start-LikadoPreview.ps1'),'-VerifyFrames','150'], cwd=ROOT,
        capture_output=True,text=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    (base/'launcher.log').write_text(launch.stdout+launch.stderr)
    assert launch.returncode == 0, launch.stdout+launch.stderr
    preview = Path(re.search(r'Separate preview saves and diagnostics: (.+)',launch.stdout).group(1).strip())
    assert preview.resolve().is_relative_to((ROOT/'local/preview-likado').resolve())
    logs = '\n'.join(p.read_text(errors='replace') for p in (preview/'logs').glob('*stderr.log'))
    receipt = json.loads((ROOT/'local/evidence/build-receipt.json').read_text())
    checks = {'launcher_exit_zero': launch.returncode == 0,
        'isolated_executable_matches': sha(preview/'SecretOfTheStarsSNESRecomp.exe') == receipt['release_executable_sha256'],
        'isolated_checkpoint_consumed': not (preview/'fixture-resume.state').exists(),
        'native_wide_enabled': 'experimental_field_wide=1' in logs,
        'launcher_gpu_requested_and_initialized': 'renderer request: direct3d11' in logs and 'renderer initialized: sdl' in logs,
        'source_fixture_preserved': sha(preview/'saves/save0.sav') == sha(ROOT/'local/runs/likado-east-a/saves/save0.sav')}
    # Capture actual composed enhanced pixels and SDL callback audio in a copy.
    smoke = base/'gpu-copy'; smoke.mkdir(); (smoke/'dump').mkdir()
    for p in preview.iterdir():
        if p.is_file(): shutil.copy2(p,smoke/p.name)
    shutil.copy2(ROOT/'local/runs/likado-east-a/saves/save0.sav',smoke/'resume.state')
    (smoke/'input.txt').write_text('wait 60\npress left 32\nwait 60\ndump end\nquit\n')
    env = {k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
    env.update(SNESRECOMP_HOST_PROFILE='1', SNESRECOMP_FOUNDATION_FIELD_TRACE=str(smoke/'field.csv'),
        SNESRECOMP_FOUNDATION_PRESENT_CAPTURE=str(smoke/'present.bgrx'),SNESRECOMP_FOUNDATION_CAPTURE_AT='60',
        SNESRECOMP_AUDIO_OUTPUT_RAW=str(smoke/'audio.pcm'),SNESRECOMP_DUMP_DIR=str(smoke/'dump'))
    with (smoke/'host.log').open('w') as stream:
        run=subprocess.run([str(smoke/'SecretOfTheStarsSNESRecomp.exe'),'--no-launcher','--rom',
            str(ROOT/'local/inputs/clean-usa.sfc'),'--resume-state',str(smoke/'resume.state'),
            '--script',str(smoke/'input.txt')],cwd=smoke,env=env,stdout=stream,stderr=stream,
            timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    log=(smoke/'host.log').read_text(errors='replace')
    raw=(smoke/'present.bgrx').read_bytes()
    w,h=map(int,re.search(r'composed capture (\d+)x(\d+)',log).groups())
    Image.frombytes('RGB',(w,h),raw,'raw','BGRX').save(base/'likado-preview.png')
    pcm=array.array('h');pcm.frombytes((smoke/'audio.pcm').read_bytes())
    first=next((i//2/32040 for i,v in enumerate(pcm) if v),None)
    checks.update({'copied_gpu_exit_zero':run.returncode == 0,
        'enhanced_wide_surface_800x448': (w,h)==(800,448) and len(raw)==800*448*4,
        'copied_gpu_vsync_enabled': 'Renderer: direct3d11 (vsync=1 ' in log,
        'cold_audio_nonzero_within_half_second': first is not None and first < .5,
        'owner_files_unchanged': all(sha(owner/n)==v for n,v in protected.items()),
        'rom_inputs_unchanged': all(sha(p)==v for p,v in rom_hashes.items())})
    report={'executable_sha256': receipt['release_executable_sha256'],'preview_profile':preview.relative_to(ROOT).as_posix(),
        'checks':checks,'first_audio_seconds':first,'owner_pre_hashes':protected,
        'limits':['Windows composed surface/SDL callback proof; not monitor scanout, physical pad or listening certification'],
        'passed':all(checks.values())}
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
