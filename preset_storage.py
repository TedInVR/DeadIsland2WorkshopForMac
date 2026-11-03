"""Named perk sets stored only in the user's application-support folder."""
import json,os,uuid,math,re
from pathlib import Path
import backup_storage
class PresetError(ValueError):pass

def durability_file():return backup_storage.folder().parent/'DurabilityReferences.json'
def durability_references():
    target=durability_file()
    if not target.exists():return {}
    try:
        if target.stat().st_size>4*1024*1024:raise ValueError()
        value=json.loads(target.read_text())
        if not isinstance(value,dict) or len(value)>10000:raise ValueError()
        for identity,entry in value.items():
            if not re.fullmatch('[0-9a-fA-F]{32}:[0-9a-f]{64}',identity) or not isinstance(entry,dict) or set(entry)!={'signature','maximum'}:raise ValueError()
            maximum=entry['maximum']
            if not isinstance(entry['signature'],str) or not re.fullmatch('[0-9a-f]{64}',entry['signature']) or type(maximum) not in (int,float) or not math.isfinite(maximum) or not 0<maximum<=1_000_000_000:raise ValueError()
        return value
    except (OSError,ValueError,TypeError):raise PresetError('Saved full-durability references could not be read; existing references were not changed.') from None
def record_durability(items):
    values=durability_references()
    for item in items:
        identity=item['id'];maximum=item['maximum'];signature=item['signature']
        if not re.fullmatch('[0-9a-fA-F]{32}',identity) or not re.fullmatch('[0-9a-f]{64}',signature) or type(maximum) not in (int,float) or not math.isfinite(maximum) or not 0<maximum<=1_000_000_000:raise PresetError('Choose melee weapons with a positive saved condition.')
        values[identity+':'+signature]={'signature':signature,'maximum':maximum}
    raw=json.dumps(values)
    if len(values)>10000 or len(raw.encode())>4*1024*1024:raise PresetError('Full-durability reference storage is full.')
    target=durability_file();target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temporary,target)
    finally:temporary.unlink(missing_ok=True)
    return values

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
    identity=value.get('id')
    existing=next((p for p in presets if p['id']==identity),None) if identity else next((p for p in presets if p['name'].casefold()==name.strip().casefold()),None)
    if identity and not existing:raise PresetError('The preset to update was not found.')
    if any(p['name'].casefold()==name.strip().casefold() and (not existing or p['id']!=existing['id']) for p in presets):raise PresetError('That preset name already exists.')
    if existing and value.get('replace')is not True:raise PresetError('That preset name already exists. Choose another name or confirm replacing it.')
    record={'id':existing['id'] if existing else uuid.uuid4().hex,'name':name,'perks':perks}
    validate([record]);presets=[p for p in presets if p['id']!=record['id']]+[record]
    return {'presets':write(presets),'saved_id':record['id']}

def delete(value):
    if not isinstance(value,dict) or not isinstance(value.get('id'),str):raise PresetError('Choose a preset to delete.')
    presets=list_presets()
    if not any(p['id']==value['id'] for p in presets):raise PresetError('That preset was not found. Refresh the preset list.')
    return {'presets':write([p for p in presets if p['id']!=value['id']])}

# Bindings are local display annotations, never written into game saves.
def bindings_file():return file().with_name('PerkPresetBindings.json')
def bindings():
    target=bindings_file()
    if not target.exists():return {}
    try:
        if target.stat().st_size>16*1024*1024:raise PresetError('Preset annotations are too large.')
        value=json.loads(target.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or len(value)>10000:raise PresetError('Invalid preset annotations.')
        for key,entry in value.items():
            if not isinstance(key,str) or len(key)!=32 or any(c not in '0123456789abcdef' for c in key) or not isinstance(entry,dict):raise PresetError('Invalid weapon preset annotation.')
            validate([{'id':entry.get('preset_id'),'name':'annotation','perks':entry.get('perks')}])
        return value
    except (OSError,json.JSONDecodeError) as e:raise PresetError('Preset annotations could not be read.') from e

def bind(value):
    if not isinstance(value,dict):raise PresetError('Invalid preset annotation.')
    key=value.get('weapon_id');identity=value.get('preset_id');perks=value.get('perks')
    if not isinstance(key,str) or len(key)!=32 or any(c not in '0123456789abcdef' for c in key):raise PresetError('Invalid weapon identity.')
    if identity is not None:
        if not any(p['id']==identity for p in list_presets()):raise PresetError('That preset no longer exists.')
        validate([{'id':identity,'name':'annotation','perks':perks}])
    data=bindings()
    if identity is None:data.pop(key,None)
    else:data[key]={'preset_id':identity,'perks':perks}
    if len(data)>10000:raise PresetError('Preset annotations are full.')
    target=bindings_file();temp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        target.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(data,ensure_ascii=False)
        if len(raw.encode('utf-8'))>16*1024*1024:raise PresetError('Preset annotations are full.')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as out:out.write(raw);out.flush();os.fsync(out.fileno())
        os.replace(temp,target)
    except OSError as e:raise PresetError('The applied-preset label could not be saved.') from e
    finally:temp.unlink(missing_ok=True)
    return {'saved':True}
