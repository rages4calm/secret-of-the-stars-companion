"""Check isolated HD menu preview launch and protected owner files."""
from pathlib import Path
import hashlib,json,re,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    owner=ROOT/'local/player-foundation'
    protected={p.relative_to(owner).as_posix():sha(p) for p in list(owner.glob('*'))+list((owner/'saves').glob('*')) if p.is_file()}
    base=ROOT/'local/runs'/('hd-preview-'+time.strftime('%Y%m%d-%H%M%S'));base.mkdir()
    r=json.loads((ROOT/'local/evidence/build-receipt.json').read_text())
    result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'tools/Start-HdMenuPreview.ps1'),'-VerifyFrames','150'],cwd=ROOT,
        capture_output=True,text=True,timeout=35,creationflags=subprocess.CREATE_NO_WINDOW)
    (base/'launcher.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    preview=Path(re.search(r'Separate preview saves and diagnostics: (.+)',result.stdout).group(1).strip())
    logs='\n'.join(p.read_text(errors='replace') for p in (preview/'logs').glob('*stderr.log'))
    checks={'exit_zero':result.returncode==0,'isolated_fresh_profile':preview.resolve().is_relative_to((ROOT/'local/preview-hd-menu').resolve()),
        'qualified_executable':sha(preview/'SecretOfTheStarsSNESRecomp.exe')==r['release_executable_sha256'],
        'configuration_selected_hd':'hd_menu_frames=1 ' in logs,
        'original_loading_and_width':'native_clear_original_cost=0' in logs and
            'native_column_lookup=0 fast_fetch=0' in logs and 'experimental_field_wide=0' in logs,
        'actual_gpu_requested':'renderer request: direct3d11' in logs and 'renderer initialized: sdl' in logs,
        'audio_device_opened':'audio device opened:' in logs,
        'fixture_resumed':'resume state loaded:' in logs and not(preview/'fixture-resume.state').exists(),
        'fixture_slot_retained':sha(preview/'saves/save0.sav')==r['hd_menu_fixture_sha256'],
        'owner_files_unchanged':all(sha(owner/n)==v for n,v in protected.items())}
    report={'executable_sha256':r['release_executable_sha256'],'preview_profile':preview.relative_to(ROOT).as_posix(),
        'checks':checks,'passed':all(checks.values()),
        'limits':['Launcher and copied fixture startup; active menu art/audio PCM have separate GPU proof. No owner progress or physical-controller certification.']}
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
