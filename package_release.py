#!/usr/bin/env python3
"""Build versioned/latest installer ZIPs and update.json without personal files."""
import hashlib,json,plistlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FILES=('Install.command','Repair-Updates.command','Workshop.swift','server.py','save_codec.py','requirements-runtime.txt','legal_state.py','USAGE_TERMS.md','CREDITS.md','Credits.html','LICENSING_REVIEW.md','ps4_backups.py','character_editor.py','resource_catalog.json','credential_store.py','garlic_service.py','save_browser.py','backup_storage.py','save_core.py','index.html','Info.plist','Workshop.icns','catalog.json','updater.py','User-Guide.html','USER_GUIDE.md','README.txt','THIRD_PARTY_NOTICES.md')
def main():
    with (ROOT/'Info.plist').open('rb') as f:version=plistlib.load(f)['CFBundleShortVersionString']
    output=ROOT/'downloads';output.mkdir(exist_ok=True)
    name='Dead-Island-2-Workshop-Mac-'+version+'.zip';path=output/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for file in (*FILES,*(p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'third_party_licenses').iterdir()) if p.is_file())):
            if not (ROOT/file).is_file():raise FileNotFoundError(file)
            info=zipfile.ZipInfo('Dead-Island-2-Workshop-Mac-'+version+'/'+file,(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3
            info.external_attr=((0o100755 if file.endswith('.command') else 0o100644)<<16)
            z.writestr(info,(ROOT/file).read_bytes())
    (output/'Dead-Island-2-Workshop-Mac-Latest.zip').write_bytes(path.read_bytes())
    manifest=dict(version=version,path='downloads/'+name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),notes='Fix editing GarlicSaves compressed DI2 saves; preserve compression and checksums; reopen the previous decryption without another upload; clearer save labels.')
    (ROOT/'update.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(file=str(path),size=path.stat().st_size,**manifest)))
if __name__=='__main__':main()
