"""Qualify targeted renderer migration without advancing owner progress."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = ROOT/'local/runs'/('vsync-migration-'+time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    report = {'checks': {}}
    old = ROOT/'local/owner-backups/menu-glitch-20261009-101153/SecretOfTheStarsSNESRecomp.exe'
    for renderer in ['software', 'opengl']:
        profile = base/renderer
        (profile/'saves').mkdir(parents=True)
        shutil.copy2(old, profile/'SecretOfTheStarsSNESRecomp.exe')
        config = ('[Graphics]\r\nRenderer='+renderer+'\r\nOutputMethod=SDL-Software\r\nVSync=0\r\nFullscreen=1\r\n'
                  '[Sound]\r\nVolume=49\r\n[KeyMap]\r\nFullscreen=Alt+Return,F11\r\n'
                  '[Controller]\r\nSourceP1=2\r\n[General]\r\nAutosave=0\r\n')
        (profile/'config.ini').write_bytes(config.encode())
        (profile/'controls-v2.done').write_text('Existing custom controls')
        (profile/'foundation.ini').write_text('[Enhancements]\nBattleInfo=0\nEnhancedPixels=0\nFastMenus=0\nJournal=0\nExperimentalFieldWide=0\n')
        (profile/'first-start.done').write_text('Existing profile')
        shutil.copy2(ROOT/'local/player-foundation/saves/save.srm', profile/'saves/save.srm')
        saved = {str(p.relative_to(profile)):p.read_bytes() for p in [profile/'saves/save.srm',profile/'foundation.ini',profile/'controls-v2.done']}
        args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/Start-Foundation.ps1'),'-PrepareOnly','-ProfileDirectory',str(profile)]
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        (profile/'prepare.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0, result.stdout+result.stderr
        after=(profile/'config.ini').read_text()
        expected=config if renderer=='opengl' else config.replace('Renderer=software','Renderer=direct3d11').replace('OutputMethod=SDL-Software','OutputMethod=SDL').replace('VSync=0','VSync=1')
        report['checks'][renderer+'_only_intended_settings_changed']=after==expected.replace('\r\n','\n')
        report['checks'][renderer+'_protected_files_unchanged']=all((profile/name).read_bytes()==data for name,data in saved.items())
        report['checks'][renderer+'_original_config_backed_up']=any(p.read_bytes()==config.encode() for p in (profile/'backups').glob('*/config.ini'))
        before=(profile/'config.ini').read_bytes()
        again=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        report['checks'][renderer+'_second_launch_idempotent']=again.returncode==0 and (profile/'config.ini').read_bytes()==before
    missing=profile/'foundation.ini'
    prior=missing.read_bytes().replace(b'Journal=0\r\n',b'').replace(b'Journal=0\n',b'')
    missing.write_bytes(prior)
    prepared=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
    updated=missing.read_bytes()
    report['checks']['missing_journal_added_without_other_preferences_change']=prepared.returncode==0 and updated.startswith(prior) and b'Journal=1' in updated[len(prior):]
    report['checks']['missing_journal_original_backed_up']=any(p.read_bytes()==prior for p in (profile/'backups').glob('*/foundation.ini'))
    again=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
    report['checks']['journal_addition_idempotent']=again.returncode==0 and missing.read_bytes()==updated
    report['passed']=all(report['checks'].values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base)
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
