#!/usr/bin/env python3
"""GitHub updater. No embedded credentials; optional existing gh login for private repos."""
import argparse,fcntl,hashlib,json,os,plistlib,re,shutil,subprocess,sys,tempfile,urllib.request,urllib.error,zipfile
from pathlib import Path
REPO='TedInVR/DeadIsland2WorkshopForMac'
BRANCH='main'
SUPPORT=Path.home()/'Library/Application Support/Dead Island 2 Workshop'
APP=Path('/Applications/Dead Island 2 Workshop.app')
BROWSER='https://github.com/'+REPO+'/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true'
MAX=32*1024*1024
class UpdateError(Exception):pass

def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.new');temp.write_text(json.dumps(value,indent=2));temp.replace(path)

def settings():
    try:return json.loads((SUPPORT/'settings.json').read_text())
    except (OSError,ValueError):return {'automatic_updates':True}

def version_tuple(v):
    if not isinstance(v,str) or not re.fullmatch(r'\d+\.\d+\.\d+',v):raise UpdateError('Invalid update version')
    return tuple(map(int,v.split('.')))

def installed_version():
    try:
        with (APP/'Contents/Info.plist').open('rb') as f:return plistlib.load(f)['CFBundleShortVersionString']
    except (OSError,KeyError):
        with Path(__file__).with_name('Info.plist').open('rb') as f:return plistlib.load(f)['CFBundleShortVersionString']

def github_bytes(path):
    # gh performs its own authentication. Never read, store, or log its token.
    gh=next((p for p in ['/opt/homebrew/bin/gh','/usr/local/bin/gh',shutil.which('gh')] if p and os.access(p,os.X_OK)),None)
    if gh:
        r=subprocess.run([gh,'api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json','repos/'+REPO+'/contents/'+path+'?ref='+BRANCH],capture_output=True,timeout=90)
        if r.returncode==0 and len(r.stdout)<=MAX:return r.stdout
    url='https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+'/'+path
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'DeadIsland2Workshop-Updater'}),timeout=30) as r:
            b=r.read(MAX+1)
            if len(b)>MAX:raise UpdateError('Update exceeds size limit')
            return b
    except urllib.error.HTTPError as e:
        if e.code in (401,403,404):raise UpdateError('GitHub authentication is required for this private repository. Use Download Updates in your signed-in browser, or authenticate GitHub CLI (gh) for automatic updates.')
        raise UpdateError('GitHub could not supply the update (HTTP '+str(e.code)+').')
    except urllib.error.URLError:raise UpdateError('Could not connect to GitHub. Try again when online.')

def manifest():
    m=json.loads(github_bytes('update.json'))
    version_tuple(m.get('version'))
    if not re.fullmatch(r'[0-9a-f]{64}',m.get('sha256','')):raise UpdateError('Invalid update checksum')
    if not re.fullmatch(r'downloads/Dead-Island-2-Workshop-Mac-[0-9.]+\.zip',m.get('path','')):raise UpdateError('Invalid update download path')
    return m

def app_running():
    p=subprocess.run(['/usr/bin/pgrep','-f',r'/Dead Island 2 Workshop\.app/Contents/MacOS/DI2Workshop'],capture_output=True)
    if p.returncode not in (0,1):raise UpdateError('Could not verify whether Workshop is closed')
    return p.returncode==0

def check():
    m=manifest();current=installed_version();available=version_tuple(m['version'])>version_tuple(current)
    return dict(status='available' if available else 'current',installed=current,version=m['version'],notes=m.get('notes',''),browser_url=BROWSER,automatic_updates=settings().get('automatic_updates',True))

def download(m):
    SUPPORT.mkdir(parents=True,exist_ok=True)
    target=SUPPORT/'pending-update.zip'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==m['sha256']:return target
    b=github_bytes(m['path'])
    if hashlib.sha256(b).hexdigest()!=m['sha256']:raise UpdateError('Update checksum did not match; nothing was installed')
    tmp=target.with_suffix('.tmp');tmp.write_bytes(b);tmp.replace(target)
    atomic_json(SUPPORT/'pending-update.json',m)
    return target

def extract_package(archive,directory):
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist())>MAX:raise UpdateError('Expanded update is too large')
        roots=set()
        for item in z.infolist():
            p=Path(item.filename)
            if p.is_absolute() or '..' in p.parts or not p.parts:raise UpdateError('Invalid archive path')
            if (item.external_attr>>16)&0o170000==0o120000:raise UpdateError('Update cannot contain symbolic links')
            roots.add(p.parts[0])
        if len(roots)!=1:raise UpdateError('Invalid update package layout')
        root=directory/next(iter(roots))
        z.extractall(directory)
        required=('Install.command','Info.plist','Workshop.swift','save_core.py','server.py','index.html','catalog.json','updater.py')
        if any(not (root/name).is_file() for name in required):raise UpdateError('Update is missing required files')
        return root

def queue():
    m=manifest()
    if version_tuple(m['version'])<=version_tuple(installed_version()):return {'status':'current','version':m['version']}
    download(m)
    return {'status':'queued','version':m['version'],'message':'Downloaded and verified. It will install after Workshop is closed, without reopening it.'}

def run():
    if not settings().get('automatic_updates',True) and not (SUPPORT/'pending-update.json').exists():return {'status':'disabled'}
    # Never check, download, build, or install automatically while the app is open.
    if app_running():return {'status':'app_open'}
    try:m=json.loads((SUPPORT/'pending-update.json').read_text())
    except (OSError,ValueError):m=manifest()
    if version_tuple(m['version'])<=version_tuple(installed_version()):
        for name in ('pending-update.zip','pending-update.json'):(SUPPORT/name).unlink(missing_ok=True)
        return {'status':'current'}
    package=download(m)
    with (SUPPORT/'app-install.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'app_open'}
        if app_running():return {'status':'app_open'}
        with tempfile.TemporaryDirectory(prefix='di2-update-',dir=SUPPORT) as temp:
            root=extract_package(package,Path(temp))
            with (root/'Info.plist').open('rb') as f:actual=plistlib.load(f)['CFBundleShortVersionString']
            if actual!=m['version']:raise UpdateError('Package version does not match update manifest')
            result=subprocess.run(['/bin/bash',str(root/'Install.command'),'--unattended'],capture_output=True,text=True,timeout=240)
            if result.returncode:raise UpdateError('Installation did not finish. The previous app is retained; run the downloaded installer manually. Details: '+result.stderr[-1200:])
        for name in ('pending-update.zip','pending-update.json'):(SUPPORT/name).unlink(missing_ok=True)
    return {'status':'installed','version':m['version']}

def install_agent(python):
    SUPPORT.mkdir(parents=True,exist_ok=True)
    cfg=SUPPORT/'settings.json'
    if not cfg.exists():atomic_json(cfg,{'automatic_updates':True})
    here=Path(__file__).resolve()
    if here!=SUPPORT/'updater.py':shutil.copyfile(here,SUPPORT/'updater.py')
    agents=Path.home()/'Library/LaunchAgents';agents.mkdir(parents=True,exist_ok=True)
    path=agents/'local.ted.di2workshop.updater.plist'
    value=dict(Label='local.ted.di2workshop.updater',ProgramArguments=[python,str(SUPPORT/'updater.py'),'--run'],StartInterval=900,RunAtLoad=True,StandardOutPath=str(SUPPORT/'updater.log'),StandardErrorPath=str(SUPPORT/'updater-error.log'),ProcessType='Background')
    path.write_bytes(plistlib.dumps(value))
    # During a scheduled install this job is already loaded; it will use the new
    # helper on its next invocation without terminating itself with bootout.
    if not subprocess.run(['/bin/launchctl','print','gui/'+str(os.getuid())+'/local.ted.di2workshop.updater'],capture_output=True).returncode==0:
        r=subprocess.run(['/bin/launchctl','bootstrap','gui/'+str(os.getuid()),str(path)],capture_output=True)
        if r.returncode:raise UpdateError('The app was installed, but its update agent could not be loaded')
    return {'status':'agent_installed'}

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for flag in ('check','queue','run','enable','disable','status','install-agent'):g.add_argument('--'+flag,action='store_true')
    args=p.parse_args();SUPPORT.mkdir(parents=True,exist_ok=True)
    with (SUPPORT/'updater-worker.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:print(json.dumps({'status':'busy','message':'An update check is already running.'}));return
        try:
            if args.check:result=check()
            elif args.queue:result=queue()
            elif args.run:result=run()
            elif args.install_agent:result=install_agent(sys.executable)
            elif args.status:result=settings()
            else:
                cfg=settings();cfg['automatic_updates']=args.enable;atomic_json(SUPPORT/'settings.json',cfg);result=cfg
            print(json.dumps(result))
        except Exception as e:print(json.dumps({'status':'error','message':str(e),'browser_url':BROWSER}));sys.exit(1)
if __name__=='__main__':main()
