"""Local first-use acknowledgment; no registration, identity or network reporting."""
import hashlib,json,os,re,uuid
from datetime import datetime,timezone
from pathlib import Path
import backup_storage
ROOT=Path(__file__).resolve().parent
VERSION=1
class AgreementRequired(ValueError):pass

def file():return backup_storage.folder().parent/'usage-acknowledgment.json'
def document():return (ROOT/'USAGE_TERMS.md').read_text(encoding='utf-8')
def digest():return hashlib.sha256((ROOT/'USAGE_TERMS.md').read_bytes()).hexdigest()
def is_accepted():
    try:
        value=json.loads(file().read_text(encoding='utf-8'))
        # An update is not a new first use; retain the originally acknowledged hash.
        return value.get('accepted')is True and value.get('schema')==1 and type(value.get('agreement_version'))is int and isinstance(value.get('document_sha256'),str) and re.fullmatch('[0-9a-f]{64}',value['document_sha256']) is not None and isinstance(value.get('accepted_at'),str)
    except (OSError,ValueError,AttributeError):return False

def require():
    if not is_accepted():raise AgreementRequired('Read and acknowledge the first-use agreement before using Workshop.')
def status():return {'accepted':bool(is_accepted()),'version':VERSION,'sha256':digest(),'text':document()}
def accept(value):
    if not isinstance(value,dict) or value.get('confirm')is not True or value.get('version')!=VERSION or value.get('sha256')!=digest():raise AgreementRequired('Read the current agreement and check the acknowledgment box before accepting.')
    if is_accepted():return {'accepted':True}
    target=file();target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    record={'schema':1,'accepted':True,'agreement_version':VERSION,'document_sha256':digest(),'accepted_at':datetime.now(timezone.utc).isoformat()}
    try:
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(temp,target)
    except OSError:raise AgreementRequired('The local acknowledgment could not be saved. Check application-support folder access and try again.') from None
    finally:temp.unlink(missing_ok=True)
    return {'accepted':True}
