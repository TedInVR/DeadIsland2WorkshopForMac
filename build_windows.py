"""Run on Windows to produce the self-contained, versioned distribution ZIP."""
import hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
from windows_app import version
ROOT=Path(__file__).resolve().parent

def main():
    if sys.platform!='win32':raise SystemExit('Build the Windows executable on Windows, using the GitHub Actions workflow.')
    os.chdir(ROOT);v=version();output=ROOT/'windows-dist';output.mkdir(exist_ok=True)
    resources=['index.html','catalog.json','Info.plist','User-Guide.html','USER_GUIDE.md','README-WINDOWS.md','THIRD_PARTY_NOTICES.md']
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--name','Dead Island 2 Workshop','--icon','Workshop.icns','--copy-metadata','pywebview','--copy-metadata','pythonnet','--exclude-module','tkinter']
    for name in resources:command+=['--add-data',name+':.']
    command+=['windows_app.py'];subprocess.run(command,check=True)
    folder=ROOT/'dist'/'Dead Island 2 Workshop'
    # Include dependency license metadata and the Python runtime license.
    for name in ('LICENSE.txt','LICENSE'):
        license=Path(sys.base_prefix)/name
        if license.is_file():shutil.copyfile(license,folder/'PYTHON-LICENSE.txt');break
    shutil.copyfile(ROOT/'THIRD_PARTY_NOTICES.md',folder/'THIRD_PARTY_NOTICES.md')
    shutil.copyfile(ROOT/'README-WINDOWS.md',folder/'README-WINDOWS.md')
    name='Dead-Island-2-Workshop-Windows-'+v;archive=output/(name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file():z.write(p,name+'/Dead Island 2 Workshop/'+p.relative_to(folder).as_posix())
        for n in ('Install-Windows.cmd','Install-Windows.ps1','README-WINDOWS.md'):z.write(ROOT/n,name+'/'+n)
    latest=output/'Dead-Island-2-Workshop-Windows-Latest.zip';shutil.copyfile(archive,latest)
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in (archive,latest))
    (output/'WINDOWS-SHA256SUMS.txt').write_text(sums)
    print(json.dumps({'version':v,'archive':str(archive),'bytes':archive.stat().st_size}))
if __name__=='__main__':main()
