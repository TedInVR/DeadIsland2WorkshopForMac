"""Read-only PS4 USB save discovery and local profile display names."""
import hashlib,json,os,re,stat,sys,uuid
from pathlib import Path
import backup_storage

TITLE_IDS=('CUSA01014','CUSA27043','CUSA35681')
ACCOUNT=re.compile(r'[0-9a-fA-F]{16}')
class BrowserError(Exception):pass

def names_file():return backup_storage.folder().parent/'profile-names.json'

def validate_names(value):
    if isinstance(value,dict) and 'profiles' in value:value=value['profiles']
    if not isinstance(value,dict) or len(value)>256:raise BrowserError('Choose a profile-name JSON object with at most 256 profiles.')
    result={}
    for account,name in value.items():
        if not isinstance(account,str) or not ACCOUNT.fullmatch(account):raise BrowserError('Profile account IDs must contain 16 hexadecimal characters.')
        if not isinstance(name,str) or len(name.strip())>64 or any(ord(c)<32 for c in name):raise BrowserError('Profile names must be text of at most 64 characters.')
        result[account.lower()]=name.strip()
    return result

def profile_names():
    file=names_file()
    if not file.exists():return {}
    try:return validate_names(json.loads(file.read_text(encoding='utf-8')))
    except (OSError,ValueError) as e:raise BrowserError('Profile names could not be read: '+str(e)) from e

def import_names(value):
    updates=validate_names(value);names=profile_names()
    for account,name in updates.items():
        if name:names[account]=name
        else:names.pop(account,None)
    file=names_file();file.parent.mkdir(parents=True,exist_ok=True);temp=file.with_name(file.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('x',encoding='utf-8') as f:json.dump({'profiles':names},f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.replace(temp,file)
    finally:temp.unlink(missing_ok=True)
    return names

def mounted_roots():
    configured=os.environ.get('DI2_WORKSHOP_SCAN_ROOTS')
    if configured:
        paths=json.loads(configured)
        if not isinstance(paths,list) or len(paths)>64 or any(not isinstance(p,str) for p in paths):raise BrowserError('Invalid configured scan roots.')
        return [Path(p) for p in paths]
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.GetLogicalDrives.restype=wintypes.DWORD
        api.GetDriveTypeW.argtypes=[wintypes.LPCWSTR];api.GetDriveTypeW.restype=wintypes.UINT
        mask=api.GetLogicalDrives()
        return [Path(chr(65+i)+':\\') for i in range(26) if mask&(1<<i) and api.GetDriveTypeW(chr(65+i)+':\\') in (2,3)]
    if sys.platform=='darwin':
        try:return [p for p in Path('/Volumes').iterdir() if not p.is_symlink()]
        except OSError:return []
    # Development fallback. Production desktop releases target macOS and Windows.
    result=[]
    for base in (Path('/media'),Path('/run/media'),Path('/mnt')):
        if not base.is_dir():continue
        try:
            for p in base.iterdir():
                if p.is_symlink():continue
                result.append(p)
                if base.name!='mnt' and p.is_dir():result.extend(q for q in p.iterdir() if not q.is_symlink())
        except OSError:continue
    return result

def _key(path):return hashlib.sha256(str(path.resolve()).encode('utf-8')).hexdigest()[:32]

def scan(roots=None):
    names=profile_names();entries=[];errors=[];seen=set()
    roots=mounted_roots() if roots is None else roots
    for root in roots:
        root=Path(root);savedata=root/'PS4'/'SAVEDATA'
        try:
            if (root/'PS4').is_symlink() or savedata.is_symlink():continue
            try:info=savedata.stat()
            except FileNotFoundError:continue
            if not stat.S_ISDIR(info.st_mode):continue
            for account in sorted(savedata.iterdir(),key=lambda p:p.name.lower())[:512]:
                if not ACCOUNT.fullmatch(account.name) or account.is_symlink() or not account.is_dir():continue
                aid=account.name.lower()
                for game in sorted(account.iterdir(),key=lambda p:p.name):
                    title=game.name
                    if not re.fullmatch(r"CUSA[0-9]{5}",title):continue
                    if game.is_symlink() or not game.is_dir():continue
                    try:files={p.name.lower():p for p in list(game.iterdir())[:512] if not p.is_symlink() and p.is_file()}
                    except OSError as e:errors.append(str(game)+': '+str(e));continue
                    for low,path in files.items():
                        if low.startswith('.') or (low.endswith('.bin') and low+'.bin' not in files):continue
                        if not re.fullmatch(r'[A-Za-z0-9_. -]{1,64}',path.name):continue
                        try:
                            with path.open('rb') as f:head=f.read(21)
                            fileinfo=path.stat()
                        except OSError as e:errors.append(str(path)+': '+str(e));continue
                        plain=head[:4]==bytes.fromhex('3dca1200') and head[16:21]==b'Zstd\0'
                        binfile=files.get(low+'.bin')
                        if not plain and not binfile and low!='deadisland2savegame':continue
                        kind='decrypted' if plain else ('encrypted' if binfile else 'incomplete')
                        key=_key(path)
                        if key in seen:continue
                        seen.add(key)
                        entries.append(dict(drive_key=_key(root),drive_root=str(root),game_name='Dead Island 2' if low=='deadisland2savegame' else title,is_di2=low=='deadisland2savegame' or plain,key=key,path=str(path),folder=str(game),drive=root.name or str(root),account_id=aid,profile_name=names.get(aid,aid),title_id=title,filename=path.name,kind=kind,bin_path=str(binfile) if binfile else None,bytes=fileinfo.st_size,modified=fileinfo.st_mtime))
        except OSError as e:errors.append(str(root)+': '+str(e))
    entries.sort(key=lambda e:(e['profile_name'].lower(),e['drive'].lower(),e['title_id'],e['filename'].lower()))
    return dict(entries=entries,profiles=names,errors=errors,drives=[dict(key=_key(p),name=Path(p).name,root=str(p)) for p in roots if Path(p).is_dir() and not Path(p).is_symlink()])

def find_save(key,roots=None):
    if not isinstance(key,str) or not re.fullmatch('[0-9a-f]{32}',key):raise BrowserError('Choose a save from the USB list.')
    entry=next((e for e in scan(roots)['entries'] if e['key']==key),None)
    if not entry:raise BrowserError('That drive or save is no longer available. Refresh the USB list.')
    return entry


def find_drive(key):
    for p in mounted_roots():
        if Path(p).is_dir() and not Path(p).is_symlink() and _key(p)==key:return Path(p)
    raise BrowserError('That USB drive is no longer available.')
