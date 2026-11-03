"""Real macOS build/install smoke test, isolated from /Applications and user data."""
import json,os,plistlib,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import updater as u


def main():
    if sys.platform!='darwin':raise SystemExit('Run this integration check on macOS.')
    root=Path(__file__).resolve().parent
    m=json.loads((root/'update.json').read_text());package=(root/m['path']).read_bytes()
    with tempfile.TemporaryDirectory(prefix='di2-install-test-') as temp:
        temp=Path(temp);support=temp/'Support';app=temp/'Applications'/'Dead Island 2 Workshop.app';dev=temp/'Development'
        (app/'Contents').mkdir(parents=True)
        (app/'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleShortVersionString':'0.0.0'}))
        env={'DI2_WORKSHOP_INSTALL_APP':str(app),'DI2_WORKSHOP_DEV_DIR':str(dev),'DI2_WORKSHOP_SKIP_AGENT':'1','DI2_WORKSHOP_RUNTIME_DIR':str(temp/'Runtime'),'DI2_WORKSHOP_RUNTIME_PYTHON':sys.executable}
        with patch.object(u,'SUPPORT',support),patch.object(u,'APP',app),patch.object(u,'app_running',return_value=False),patch.object(u,'github_bytes',side_effect=lambda path:json.dumps(m).encode() if path=='update.json' else package),patch.dict(os.environ,env):
            assert u.startup()['status']=='queued'
            with patch.object(u,'reopen_app') as reopen:
                result=u.after_quit(reopen=True)
                reopen.assert_called_once_with()
            assert result['status']=='installed',result
            assert u.installed_version()==m['version']
            assert (app/'Contents/MacOS/DI2Workshop').is_file()
            for name in ('preset_storage.py','save_codec.py','PythonPath.txt','requirements-runtime.txt','legal_state.py','USAGE_TERMS.md','CREDITS.md','Credits.html','THIRD_PARTY_NOTICES.md','LICENSING_REVIEW.md','third_party_licenses/CC-BY-SA-3.0.txt','updater.py','credential_store.py','garlic_service.py','server.py','ps4_backups.py','character_editor.py','resource_catalog.json','ammo_catalog.json','backup_storage.py','save_browser.py','catalog.json','index.html'):
                assert (app/'Contents/Resources'/name).is_file(),name
            runtime=(app/'Contents/Resources/PythonPath.txt').read_text().strip()
            subprocess.run([runtime,'-B','-c','import zstandard,cityhash; import sys; sys.path.insert(0,sys.argv[1]); import save_codec; assert save_codec.encode(b"example",None)==b"example"',str(app/'Contents/Resources')],check=True)
            assert not (support/'pending-update.json').exists()
            subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(app)],check=True)
            print(json.dumps({'status':'passed','actual_installed_version':u.installed_version(),'native_build_and_install':True,'original_user_app_untouched':True}))
if __name__=='__main__':main()
