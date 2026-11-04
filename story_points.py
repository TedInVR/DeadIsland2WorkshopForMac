"""Private, per-game-build story starting points. Never bundled in releases."""
import hashlib,json,os,sys,tempfile
from pathlib import Path
MAX=12*1024*1024
class PointError(ValueError):pass

def folder():
    override=os.environ.get('DI2_WORKSHOP_STORY_DIR')
    if override:return Path(override).expanduser().resolve()
    if sys.platform=='darwin':base=Path.home()/'Library/Application Support'
    elif sys.platform=='win32':base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))
    else:base=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
    return base/'Dead Island 2 Workshop'/'StoryStartingPoints'

def path(header,ng):
    if not isinstance(header,bytes) or len(header)!=21 or type(ng)!=bool:raise PointError('Invalid story starting-point identity')
    return folder()/(hashlib.sha256(header).hexdigest()+'-'+('ngplus' if ng else 'regular')+'.json')

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def load(header,ng):
    p=path(header,ng)
    if not p.exists():return None
    if p.stat().st_size>MAX:raise PointError('Stored story starting point exceeds size limit')
    try:
        raw=json.loads(p.read_text());value=raw['checkpoint']
        if hashlib.sha256(canonical(value)).hexdigest()!=raw['sha256']:raise PointError('Stored story starting-point checksum failed')
        if value['version']!=1 or value['header']!=header.hex() or value['ng'] is not ng:raise PointError('Stored story starting-point identity mismatch')
        return value
    except (OSError,KeyError,TypeError,json.JSONDecodeError) as e:raise PointError('Stored story starting point is unreadable') from e

def save_once(header,ng,value):
    p=path(header,ng)
    if p.exists():return load(header,ng)
    data=canonical(dict(checkpoint=value,sha256=hashlib.sha256(canonical(value)).hexdigest()))
    if len(data)>MAX:raise PointError('Story starting point exceeds size limit')
    p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temp=tempfile.mkstemp(dir=p.parent,prefix='.starting-point-')
    try:
        with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
        # Link is an atomic exclusive create; never replace a stored point silently.
        try:os.link(temp,p)
        except FileExistsError:pass
    finally:Path(temp).unlink(missing_ok=True)
    return load(header,ng)
