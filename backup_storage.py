"""Local, append-only save snapshots. No pruning, overwriting, or network access."""
import hashlib,os,re,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

class BackupError(Exception):pass

def folder():
    override=os.environ.get('DI2_WORKSHOP_BACKUP_DIR')
    if override:return Path(override).expanduser().resolve()
    if sys.platform=='darwin':base=Path.home()/'Library/Application Support'
    elif sys.platform=='win32':base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))
    else:base=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
    return base/'Dead Island 2 Workshop'/'Backups'

def protects(path):
    # Refuse manual exports anywhere inside the dedicated backup directory.
    root=folder().resolve();target=Path(path).resolve()
    return any(target==p or p in target.parents for p in (root,root.parent/'NamedBackups'))

def snapshot(data,reason,name='ue4savegame.ps4.sav'):
    if reason not in ('opened','exported'):raise ValueError('Unknown backup reason')
    name=Path(str(name).replace('\\','/')).name
    stem=re.sub(r'[^A-Za-z0-9._-]+','_',Path(name).stem)[:72].strip('._') or 'save'
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S-%fZ')
    root=folder();target=None;created=False
    try:
        root.mkdir(parents=True,exist_ok=True)
        # Exclusive create is the guarantee: even a repeated timestamp/UUID cannot replace a file.
        for _ in range(10):
            target=root/(stamp+'_'+reason+'_'+stem+'_'+uuid.uuid4().hex+'.sav')
            try:f=target.open('xb');created=True;break
            except FileExistsError:continue
        else:raise OSError('Could not allocate a unique backup filename')
        digest=hashlib.sha256(data).hexdigest()
        with f:
            f.write(data);f.flush();os.fsync(f.fileno())
        if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise OSError('Backup verification failed')
        return dict(path=str(target),folder=str(root),reason=reason,sha256=digest,bytes=len(data))
    except OSError as e:
        if created and target is not None:
            try:target.unlink()
            except OSError:pass
        raise BackupError('Automatic backup could not be saved. The operation was stopped; check free disk space and backup-folder access. '+str(e)) from e
