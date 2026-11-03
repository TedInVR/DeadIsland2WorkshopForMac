"""Named perk sets stored only in the user's application-support folder."""
import json,os,uuid
from pathlib import Path
import backup_storage
class PresetError(ValueError):pass

def file():return backup_storage.folder().parent/'PerkPresets.json'
def validate(value):
    if not isinstance(value,list) or len(value)>256:raise PresetError('Preset storage is invalid or contains more than 256 presets.')
    seen=set();names=set();result=[]
    for item in value:
        if not isinstance(item,dict):raise PresetError('Invalid preset record.')
        identity=item.get('id');name=item.get('name');perks=item.get('perks')
        if not isinstance(identity,str) or len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity) or identity in seen:raise PresetError('Invalid preset identity.')
        if not isinstance(name,str) or not 1<=len(name.strip())<=80 or any(ord(c)<32 for c in name) or name.strip().casefold() in names:raise PresetError('Use a unique preset name of 1–80 characters.')
        if not isinstance(perks,list) or len(perks)>512 or any(not isinstance(p,str) or not p.startswith('/Game/') or len(p)>2048 or any(ord(c)<32 for c in p) for p in perks) or len(set(perks))!=len(perks):raise PresetError('Invalid mod/perk list.')
        seen.add(identity);names.add(name.strip().casefold());result.append({'id':identity,'name':name.strip(),'perks':list(perks)})
    return result

def list_presets():
    target=file()
    if not target.exists():return []
    try:
        if target.stat().st_size>2*1024*1024:raise PresetError('Preset storage is too large.')
        value=json.loads(target.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or value.get('schema')!=1:raise PresetError('Unsupported preset storage format.')
        return sorted(validate(value.get('presets')),key=lambda p:p['name'].casefold())
    except (OSError,json.JSONDecodeError) as e:raise PresetError('Saved presets could not be read. Existing presets were not changed.') from e

def write(presets):
    presets=validate(presets);target=file();temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        target.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps({'schema':1,'presets':presets},ensure_ascii=False,indent=2)
        if len(raw.encode('utf-8'))>2*1024*1024:raise PresetError('Preset storage is full.')
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as out:out.write(raw);out.flush();os.fsync(out.fileno())
        os.replace(temporary,target)
    except OSError as e:raise PresetError('The preset could not be saved. Existing presets were not changed.') from e
    finally:temporary.unlink(missing_ok=True)
    return list_presets()

def save(value):
    if not isinstance(value,dict):raise PresetError('Invalid preset request.')
    name=value.get('name');perks=value.get('perks');presets=list_presets()
    if not isinstance(name,str):raise PresetError('Enter a preset name.')
    existing=next((p for p in presets if p['name'].casefold()==name.strip().casefold()),None)
    if existing and value.get('replace')is not True:raise PresetError('That preset name already exists. Choose another name or confirm replacing it.')
    record={'id':existing['id'] if existing else uuid.uuid4().hex,'name':name,'perks':perks}
    validate([record]);presets=[p for p in presets if p['id']!=record['id']]+[record]
    return {'presets':write(presets),'saved_id':record['id']}

def delete(value):
    if not isinstance(value,dict) or not isinstance(value.get('id'),str):raise PresetError('Choose a preset to delete.')
    presets=list_presets()
    if not any(p['id']==value['id'] for p in presets):raise PresetError('That preset was not found. Refresh the preset list.')
    return {'presets':write([p for p in presets if p['id']!=value['id']])}
