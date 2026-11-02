"""Named, append-only PS4 backups and guarded USB pair installation."""
import hashlib,json,os,re,shutil,uuid
from datetime import datetime,timezone
from pathlib import Path
import backup_storage
LIMIT=128*1024*1024
class BackupError(ValueError):pass
ACCOUNT=re.compile('[0-9a-f]{16}');TITLE=re.compile('CUSA[0-9]{5}')
NAME=re.compile(r'[A-Za-z0-9_. -]{1,64}')
def identity(account,title,name):
    if not ACCOUNT.fullmatch(account) or not TITLE.fullmatch(title) or not NAME.fullmatch(name) or name in ('.','..') or name.endswith(('.', ' ')):raise BackupError('Invalid PS4 save identity.')
def root():return backup_storage.folder().parent/'NamedBackups'
def read_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>LIMIT:raise BackupError('The save is unavailable, is a link, or exceeds 128 MB.')
    with p.open('rb') as f:data=f.read(LIMIT+1)
    if len(data)>LIMIT:raise BackupError('The save exceeds 128 MB.')
    return data

def capture(entry,label,files=None):
    if not isinstance(label,str) or not label.strip() or len(label.strip())>160 or any(ord(x)<32 for x in label):raise BackupError('Give the backup a name of 1–160 characters.')
    label=label.strip();account=entry['account_id'];title=entry['title_id'];name=entry['filename'];identity(account,title,name)
    if files is None:
        if entry.get('drive_root') and target_folder(entry['drive_root'],account,title,name).resolve()!=Path(entry['path']).parent.resolve():raise BackupError('The source folder has changed. Refresh the USB list.')
        files={name:read_file(entry['path'])}
        if entry.get('bin_path'):files[name+'.bin']=read_file(entry['bin_path'])
    if not files or set(files)-{name,name+'.bin'}:raise BackupError('Invalid backup file set.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S');slug=re.sub(r'[^\w .-]','-',label)[:48].strip(' .') or 'Save'
    key=uuid.uuid4().hex;folder=root()/(stamp+' '+slug+' '+key[:8]);folder.mkdir(parents=True,exist_ok=False)
    relative='PS4/SAVEDATA/'+account+'/'+title+'/';records=[]
    try:
        for filename,data in files.items():
            path=folder/relative/filename;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            digest=hashlib.sha256(data).hexdigest()
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise BackupError('Backup checksum verification failed.')
            records.append({'file':relative+filename,'sha256':digest,'bytes':len(data)})
        value={'id':key,'name':label,'created':datetime.now(timezone.utc).isoformat(),'account_id':account,'title_id':title,'filename':name,'kind':entry.get('kind','encrypted'),'files':records}
        with (folder/'backup.json').open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        return dict(value,folder=str(folder))
    except Exception:
        shutil.rmtree(folder);raise

def list_backups():
    result=[]
    if not root().is_dir():return result
    for folder in root().iterdir():
        if folder.is_symlink() or not folder.is_dir():continue
        try:
            meta=json.loads((folder/'backup.json').read_text());identity(meta['account_id'],meta['title_id'],meta['filename'])
            if not re.fullmatch('[0-9a-f]{32}',meta['id']):continue
            result.append(dict(meta,folder=str(folder)))
        except (OSError,ValueError,KeyError,TypeError):continue
    return sorted(result,key=lambda x:x['created'],reverse=True)

def retrieve(key):
    if not isinstance(key,str) or not re.fullmatch('[0-9a-f]{32}',key):raise BackupError('Choose a named backup.')
    meta=next((x for x in list_backups() if x['id']==key),None)
    if not meta:raise BackupError('That backup is no longer available.')
    files={};base=Path(meta['folder']);prefix='PS4/SAVEDATA/'+meta['account_id']+'/'+meta['title_id']+'/'
    for record in meta['files']:
        name=record['file']
        if name not in (prefix+meta['filename'],prefix+meta['filename']+'.bin'):raise BackupError('Invalid backup manifest path.')
        path=base/name
        for parent in (path,*path.parents):
            if parent==base.parent:break
            if parent.is_symlink():raise BackupError('Backup links cannot be restored.')
        data=read_file(path)
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:raise BackupError('This backup failed its integrity check; it was not restored.')
        files[Path(name).name]=data
    return meta,files

def target_folder(drive,account,title,name):
    identity(account,title,name);drive=Path(drive)
    if not drive.is_dir():raise BackupError('The destination drive is unavailable.')
    target=drive/'PS4'/'SAVEDATA'/account/title
    for path in (drive,drive/'PS4',drive/'PS4'/'SAVEDATA',target.parent,target):
        if path.is_symlink():raise BackupError('Destination folders must not be symbolic links.')
    if drive.resolve() not in target.resolve().parents:raise BackupError('Invalid destination folder.')
    return target

def destination_backup(drive,account,title,name,label):
    target=target_folder(drive,account,title,name);files={}
    for filename in (name,name+'.bin'):
        p=target/filename
        if p.exists() or p.is_symlink():files[filename]=read_file(p)
    if not files:return None
    return capture(dict(account_id=account,title_id=title,filename=name,kind='encrypted' if len(files)==2 else 'incomplete'),label[:160],files)

def install(drive,account,title,name,files,label='Automatic backup before replacing USB save'):
    target=target_folder(drive,account,title,name)
    if set(files)!={name,name+'.bin'}:raise BackupError('A complete encrypted pair is required for USB installation.')
    if not files[name] or len(files[name])>LIMIT or len(files[name+'.bin'])!=96 or not files[name+'.bin'].startswith(b'pfsSKKey'):raise BackupError('The result does not have a valid PS4 pair structure.')
    # Back up the current destination immediately before writing, even if it was
    # already backed up when the remote resign job started.
    previous=destination_backup(drive,account,title,name,label)
    old={n:read_file(target/n) for n in files if (target/n).exists()}
    target.mkdir(parents=True,exist_ok=True);temps={};replaced=[]
    try:
        for n,data in files.items():
            temp=target/('.workshop-'+uuid.uuid4().hex+'.tmp');temps[n]=temp
            with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            if hashlib.sha256(temp.read_bytes()).digest()!=hashlib.sha256(data).digest():raise BackupError('USB write verification failed.')
        for n,temp in temps.items():os.replace(temp,target/n);replaced.append(n)
    except Exception as error:
        try:
            for n in replaced:
                if n in old:
                    temp=target/('.workshop-rollback-'+uuid.uuid4().hex);temp.write_bytes(old[n]);os.replace(temp,target/n)
                else:(target/n).unlink(missing_ok=True)
        except OSError:raise BackupError('USB installation stopped and rollback could not finish. Restore the automatic named backup before using this save.') from error
        raise BackupError('USB installation stopped. The previous pair was restored; its named backup is also retained.') from error
    finally:
        for temp in temps.values():temp.unlink(missing_ok=True)
    return {'message':'Installed the new pair on USB. Any previous destination pair was backed up first.','backup':previous}
