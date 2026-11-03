import math
import save_codec
import character_editor
"""DI2 PS4 Save Wizard export reader; preserves unedited bytes verbatim.
Independent implementation for the uncompressed, sectioned PS4 export format.
"""
import struct, re, hashlib, json, uuid, secrets
from pathlib import Path

CATALOG=json.loads(Path(__file__).with_name("catalog.json").read_text(encoding='utf-8'))
WEAPON_NAMES={r["path"]:r["name"] for r in CATALOG["weapons"]}
PERK_NAMES={r["path"]:r["name"] for r in CATALOG["upgrades"]}
SLAYERS={("Warrior","Male"):"Ryan",("Warrior","Female"):"Carla",("Berserker","Male"):"Jacob",("Berserker","Female"):"Dani",("Rogue","Male"):"Bruno",("Rogue","Female"):"Amy"}
from dataclasses import dataclass

class FormatError(ValueError): pass

def u32(b,p): return struct.unpack_from('<I',b,p)[0]
def put(n): return struct.pack('<I',n)
def fs(s):
    d=s.encode('utf-8')+b'\0'; return put(len(d))+d

def string(b,p):
    if p<0 or p+4>len(b): raise FormatError('Truncated string')
    n=struct.unpack_from('<i',b,p)[0]; p+=4
    if n==0: return '',p
    if abs(n)>2000000: raise FormatError('Invalid string length')
    k=n if n>0 else -2*n
    if p+k>len(b): raise FormatError('String extends past end')
    raw=b[p:p+k]; enc='utf-8' if n>0 else 'utf-16le'
    if not raw.endswith(b'\0' if n>0 else b'\0\0'): raise FormatError('Unterminated string')
    return raw.decode(enc).rstrip('\0'),p+k

@dataclass
class Prop:
    b:bytes
    start:int
    name:str
    typ:str
    sizepos:int
    data:int
    end:int
    extra:str=''
    def raw(self): return self.b[self.start:self.end]
    def payload(self): return self.b[self.data:self.end]
    def replace(self,payload):
        h=bytearray(self.b[self.start:self.data]); h[self.sizepos-self.start:self.sizepos-self.start+4]=put(len(payload))
        return bytes(h)+payload

def prop(b,p):
    start=p; name,p=string(b,p)
    if name=='None': return None,p
    typ,p=string(b,p); sizepos=p
    if p+8>len(b): raise FormatError('Truncated property')
    size=u32(b,p); p+=8; extra=''
    if typ=='StructProperty': extra,p=string(b,p); p+=16
    elif typ in ('EnumProperty','ByteProperty','ArrayProperty','SetProperty'): extra,p=string(b,p)
    elif typ=='MapProperty':
        t,p=string(b,p); v,p=string(b,p); extra=t+'|'+v
    elif typ=='BoolProperty': p+=1
    if p>=len(b): raise FormatError('Truncated property header')
    guid=b[p];p+=1
    if guid==1:p+=16
    elif guid!=0: raise FormatError('Unknown property GUID flag')
    end=p+size
    if end>len(b):raise FormatError('Property exceeds file')
    return Prop(b,start,name,typ,sizepos,p,end,extra),end

def props(b,p,end=None):
    out=[]
    for _ in range(50000):
        item,q=prop(b,p)
        if item is None:return out,q
        out.append(item); p=q
        if end is not None and p>end:raise FormatError('Properties exceed container')
    raise FormatError('Too many properties')

def replace_props(b,start,end,items,changes):
    return b[start:(items[0].start if items else end)]+b''.join(changes.get(x.name,x.raw()) for x in items)+b[(items[-1].end if items else end):end]

def label(path):
    name=path.rsplit('.',1)[-1]
    name=re.sub(r'^DA_(?:MeleeWeaponArchetype_|RangedWeaponArchetype_|ItemUpgradeData_|WeaponUpgradeData_)','',name)
    name=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',name).replace('_',' ')
    return re.sub(r'\s+',' ',name).strip()

class Runtime:
    def __init__(self,p):
        self.p=p;b=p.b
        self.inner,q=prop(b,p.data)
        if self.inner is None or self.inner.extra!='InventoryPersistentStateEntry':raise FormatError('Unsupported weapon runtime container')
        r=self.inner.data
        if u32(b,r)!=0:raise FormatError('Runtime has removed entries')
        count=u32(b,r+4);r+=8;self.entries=[]
        for _ in range(count):
            start=r;key,r=string(b,r);typ=u32(b,r);size=u32(b,r+4);r+=8
            self.entries.append((key,typ,b[r:r+size],b[start:r+size]));r+=size
        if r!=self.inner.end or q!=p.end:raise FormatError('Runtime length mismatch')
        self.upgrades=[];self.count=None
        for key,t,v,_ in self.entries:
            if key=='NumUpgrades' and t==14 and len(v)==4:self.count=u32(v,0)
            if re.fullmatch('UpgradeEntry[0-9]+',key):
                val,stop=string(v,0)
                if stop>len(v) or t!=24:raise FormatError('Unknown upgrade representation: '+str((key,t,len(v),stop,repr(v[:60]))))
                self.upgrades.append((int(key[12:]),val))
        self.upgrades.sort()
        self.paths=[v for i,v in self.upgrades if self.count is None or i<self.count]
        if self.count is not None and self.count!=len(self.paths):raise FormatError('Upgrade count mismatch')
    def durability(self):
        for key,t,v,_ in self.entries:
            if key=='Durability' and t==10 and len(v)==4:
                value=struct.unpack('<f',v)[0]
                return value if math.isfinite(value) else None
        return None
    def rebuild(self,paths,durability=None):
        if paths==self.paths and durability is None:return self.p.raw()
        if len(paths)>256:raise FormatError('This editor allows up to 256 upgrade entries')
        seen=set()
        for s in paths:
            if not s.startswith('/Game/') or '\0' in s:raise FormatError('Invalid upgrade path')
            if s in seen:raise FormatError('Duplicate upgrades are not supported')
            seen.add(s)
        if durability is not None and (isinstance(durability,bool) or not isinstance(durability,(int,float)) or not math.isfinite(durability) or not 0<=durability<=1_000_000_000):raise FormatError('Durability must be a finite number from 0 to 1,000,000,000')
        new=[];found=False
        for key,t,v,raw in self.entries:
            if paths!=self.paths and (key=='NumUpgrades' or re.fullmatch('UpgradeEntry[0-9]+',key)):continue
            if key=='Durability' and durability is not None:
                if t!=10 or len(v)!=4:raise FormatError('Unknown durability representation')
                raw=fs(key)+put(10)+put(4)+struct.pack('<f',durability);found=True
            new.append(raw)
        if durability is not None and not found:new.append(fs('Durability')+put(10)+put(4)+struct.pack('<f',durability))
        if paths!=self.paths:
            new.append(fs('NumUpgrades')+put(14)+put(4)+put(len(paths)))
            for i,s in enumerate(paths):
                v=fs(s);new.append(fs('UpgradeEntry'+str(i))+put(24)+put(len(v))+v)
        payload=put(0)+put(len(new))+b''.join(new)
        return self.p.replace(self.inner.replace(payload))

class Weapon:
    def __init__(self,b,start,end,ps,group,idx):
        self.b=b;self.start=start;self.end=end;self.ps=ps;self.by={p.name:p for p in ps}; self.group=group;self.idx=idx
        a=self.by.get('Archetype');self.path=string(b,a.data)[0] if a else ''
        self.id=b[self.by['EntryID'].data:self.by['EntryID'].end].hex()
        self.pg=self.by.get('ProceduralGenerationContext');self.pgprops=[];self.level=None;self.rarity=None;self.runtime=None
        if self.pg:
            self.pgprops,stop=props(b,self.pg.data,self.pg.end)
            if stop!=self.pg.end:raise FormatError('Weapon generation block length mismatch')
            pd={p.name:p for p in self.pgprops}
            if 'RequiredLevel' in pd:self.level=u32(b,pd['RequiredLevel'].data)
            if 'RequiredRarity' in pd:self.rarity=string(b,pd['RequiredRarity'].data)[0].split('::')[-1]
        if 'RuntimeState' in self.by:self.runtime=Runtime(self.by['RuntimeState'])
    def info(self):
        return dict(key=self.idx,id=self.id,name=WEAPON_NAMES.get(self.path,label(self.path)),path=self.path,group=self.group,level=self.level,rarity=self.rarity,perks=self.runtime.paths if self.runtime else [],durability=self.runtime.durability() if self.runtime and 'MeleeWeaponArchetype' in self.path else None,editable=bool(self.pg and self.runtime and '/Weapons/' in self.path and 'BareHands' not in self.path and 'FuryFists' not in self.path))
    def rebuild(self,change):
        changes={}
        if 'level' in change or 'rarity' in change:
            pd={p.name:p for p in self.pgprops};pgchanges={}
            if 'level' in change:
                level=change['level']
                if isinstance(level,bool) or not isinstance(level,int) or not 0<=level<=1000:raise FormatError('Weapon level must be a whole number from 0 to 1000')
                if 'RequiredLevel' not in pd:raise FormatError('Weapon has no level field')
                if level!=self.level:pgchanges['RequiredLevel']=pd['RequiredLevel'].replace(put(level))
            if 'rarity' in change:
                r=change['rarity']
                if r not in ('Common','Uncommon','Rare','Superior','Legendary'):raise FormatError('Unknown rarity')
                if 'RequiredRarity' not in pd:raise FormatError('Weapon has no rarity field')
                if r!=self.rarity:pgchanges['RequiredRarity']=pd['RequiredRarity'].replace(fs('EItemRarity::'+r))
            if pgchanges:changes['ProceduralGenerationContext']=self.pg.replace(replace_props(self.b,self.pg.data,self.pg.end,self.pgprops,pgchanges))
        if 'perks' in change or 'durability' in change:
            if 'durability' in change and ('MeleeWeaponArchetype' not in self.path or change['durability'] is None):raise FormatError('Durability is only supported on melee weapons')
            if self.runtime is None:raise FormatError('Weapon has no upgrade block')
            changes['RuntimeState']=self.runtime.rebuild(change.get('perks',self.runtime.paths),change.get('durability'))
        return replace_props(self.b,self.start,self.end,self.ps,changes)

class Save:
    def __init__(self,b):
        self.original=b
        try:b,self.compression=save_codec.decode(b)
        except save_codec.CodecError as e:raise FormatError(str(e)) from e
        self.b=b;self.sha=hashlib.sha256(self.original).hexdigest();self.sections=[];self.arrays=[];self.weapons=[];self.profiles=[]
        if b[:4]!=bytes.fromhex('3dca1200') or b[16:21]!=b'Zstd\0':raise FormatError('Choose a supported decrypted Dead Island 2 save or use PS4 Decrypt / Encrypt first.')
        n=u32(b,21);p=25
        if not 1<=n<=100:raise FormatError('Unknown section count')
        for _ in range(n):
            name,p=string(b,p);sizepos=p;size=u32(b,p);p+=4;end=p+size
            if end>len(b):raise FormatError('Truncated save section')
            self.sections.append(dict(name=name,sizepos=sizepos,start=p,end=end));p=end
        if p!=len(b):raise FormatError('Unexpected trailing data')
        self.active=''
        ap=b.find(fs('ActiveCharacter')+fs('StructProperty'))
        if ap>=0:
            ac,_=prop(b,ap)
            if ac.end-ac.data==16:self.active=''.join(b[k:k+4][::-1].hex() for k in range(ac.data,ac.end,4)).upper()
        for sec in self.sections:
            if len(sec['name'])!=32:continue
            # CharacterProfile is the first named object in each character section.
            p=sec['start']+8;obj,p=string(b,p);typ,p=string(b,p)
            if obj!='CharacterData' or typ!='/Script/DeadIsland.CharacterProfile':raise FormatError('Unknown character profile structure')
            ps,_=props(b,p+4);pd={x.name:x for x in ps}
            cp,_=props(b,pd['CharacterArchetype'].data);cd={x.name:x for x in cp}
            cls=string(b,cd['CharacterType'].data)[0].rsplit('_',1)[-1]
            gender=string(b,cd['CharacterGender'].data)[0].split('::')[-1]
            name=SLAYERS.get((cls,gender),'Unknown character')
            # Exact enum string: CreateNewGamePlus is eligibility, not NG+ status.
            ng=fs('EProfilePrivilege::NewGamePlus') in pd['ProfilePrivileges'].payload()
            profile=dict(id=sec['name'],name=name,ng=ng,active=sec['name']==self.active,internal_class=cls,gender=gender)
            self.profiles.append(profile);sec['profile']=profile
        pat=fs('InstancedItems')+fs('ArrayProperty')
        for secnum,sec in enumerate(self.sections):
            for m in re.finditer(re.escape(pat),b[sec['start']:sec['end']]):
                start=sec['start']+m.start();outer,_=prop(b,start)
                if outer.end>sec['end']:raise FormatError('Inventory crosses section boundary')
                count=u32(b,outer.data); inner,q=prop(b,outer.data+4)
                if inner is None or inner.extra!='InventoryItemInstanced' or inner.end!=outer.end:raise FormatError('Unknown inventory structure')
                # Container name immediately before the inventory object header.
                before=b[max(sec['start'],start-170):start]
                group='Inventory'
                for g in ('LostAndFoundNewGamePlus','StashNewGamePlus','LostAndFound','Stash','DIInventory'):
                    if fs(g) in before:group=g;break
                kind=group
                if sec['name']=='Account':
                    group={'Stash':'Shared storage locker — Regular','StashNewGamePlus':'Shared storage locker — New Game Plus','LostAndFound':'Shared Unclaimed Property — Regular','LostAndFoundNewGamePlus':'Shared Unclaimed Property — New Game Plus'}.get(kind,'Shared '+kind)
                elif 'profile' in sec:
                    pf=sec['profile'];group=pf['name']+' — '+('New Game Plus' if pf['ng'] else 'Regular')+(' (active)' if pf['active'] else '')+' / Carried weapons'
                else:group=sec['name']+' / '+kind
                wp=[];p=inner.data
                for _ in range(count):
                    ps,end=props(b,p,inner.end)
                    w=Weapon(b,p,end,ps,group,len(self.weapons));self.weapons.append(w);wp.append(w);p=end
                if p!=inner.end:raise FormatError('Inventory item count/length mismatch')
                self.arrays.append(dict(outer=outer,inner=inner,weapons=wp,section=secnum,group=group,kind=kind,key=len(self.arrays)))
        if not self.arrays:raise FormatError('No supported inventory arrays found')
        self.ammo=[]
        pattern=fs('ArchetypeItems')+fs('ArrayProperty')
        for si,sec in enumerate(self.sections):
            for m in re.finditer(re.escape(pattern),b[sec['start']:sec['end']]):
                outer,_=prop(b,sec['start']+m.start())
                if outer.extra!='StructProperty' or outer.end>sec['end']:raise FormatError('Unknown archetype inventory')
                inner,_=prop(b,outer.data+4)
                if inner is None or inner.extra!='InventoryItemArchetype' or inner.end!=outer.end:raise FormatError('Unknown archetype item representation')
                previous=[a for a in self.arrays if a['section']==si and a['outer'].end<=outer.start]
                group=max(previous,key=lambda a:a['outer'].start)['group'] if previous else sec['name']+' / Ammo'
                pos=inner.data
                for _ in range(u32(b,outer.data)):
                    fields,pos=props(b,pos,inner.end);pd={f.name:f for f in fields}
                    if 'Archetype' not in pd or 'Count' not in pd:continue
                    path=string(b,pd['Archetype'].data)[0];count=pd['Count']
                    if 'DA_AmmoArchetype_' not in path:continue
                    if count.typ!='IntProperty' or count.end-count.data!=4:raise FormatError('Unknown ammo count representation')
                    names={'ShotgunAmmo':'Shotgun shells','HeavyRoundsAmmo':'Heavy rounds','PistolAmmo':'Pistol rounds','CarbineAmmo':'Rifle rounds','NailgunNailsAmmo':'Nails','CrossbowBoltsAmmo':'Crossbow bolts','SawbladeDiskAmmo':'Sawblade disks'}
                    token=path.rsplit('DA_AmmoArchetype_',1)[-1]
                    self.ammo.append(dict(key=len(self.ammo),name=names.get(token,label(path)),group=group,count=u32(b,count.data),field=count,section=si))
                if pos!=inner.end:raise FormatError('Archetype item count mismatch')

        character_editor.attach(self)

    def catalogs(self):
        weapons={r['path']:dict(r) for r in CATALOG['weapons']}
        for w in self.weapons:
            if w.info()['editable'] and w.path not in weapons:
                weapons[w.path]=dict(path=w.path,name=label(w.path),type='Melee' if 'MeleeWeaponArchetype' in w.path else 'Ranged',dlc=False,from_save=True)
        perks={r['path']:dict(r) for r in CATALOG['upgrades']}
        for w in self.weapons:
            if w.runtime:
                for path in w.runtime.paths:
                    if path not in perks:perks[path]=dict(path=path,name=label(path),type='unknown',kind='special',rarity='unknown',description='Internal upgrade: '+label(path)+'. Its exact gameplay effect has not been verified.',description_basis='unverified',description_source='')
        return sorted(weapons.values(),key=lambda x:(x['name'].lower(),x['path'])),sorted(perks.values(),key=lambda x:(x['name'].lower(),x['path']))
    def info(self):
        wc,pc=self.catalogs();dest=[]
        for ar in self.arrays:
            if ar['kind'] not in ('Stash','StashNewGamePlus','DIInventory'):continue
            if ar['kind']!='DIInventory' and self.sections[ar['section']]['name']!='Account':continue
            count=sum(w.info()['editable'] for w in ar['weapons'])
            cap=16 if ar['kind']=='DIInventory' else 64
            dest.append(dict(key=ar['key'],name=ar['group'],count=count,capacity=cap,free=max(0,cap-count)))
        containers=[dict(key=a['key'],name=a['group'],count=sum(w.info()['editable'] for w in a['weapons']),capacity=next((d['capacity'] for d in dest if d['key']==a['key']),None)) for a in self.arrays if a['weapons'] or any(d['key']==a['key'] for d in dest)]
        return dict(resource_groups=character_editor.info(self),ammo=[{k:v for k,v in a.items() if k not in ('field','section')} for a in self.ammo],containers=containers,sha=self.sha,bytes=len(self.b),weapons=[w.info() for w in self.weapons if '/Weapons/' in w.path],catalog=pc,weapon_catalog=wc,destinations=dest,profiles=self.profiles)
    def duplicate_record(self,request):
        key=request.get('clone_source')
        if type(key)!=int or not 0<=key<len(self.weapons):raise FormatError('Invalid duplicate source')
        source=self.weapons[key]
        if not source.info()['editable']:raise FormatError('This item cannot be duplicated')
        change={k:request[k] for k in ('path','level','rarity','perks','durability') if k in request}
        raw=self.replacement_record(source,change) if change.get('path',source.path)!=source.path else source.rebuild(change)
        ps,end=props(raw,0);pd={p.name:p for p in ps}
        # Preserve the complete state and generation seed, changing only identities.
        return replace_props(raw,0,end,ps,{name:pd[name].replace(uuid.uuid4().bytes) for name in ('EntryID','UniqueId')})

    def create_record(self,request):
        if 'clone_source' in request:return self.duplicate_record(request)
        path=request.get('path');wc,pc=self.catalogs();paths={r['path'] for r in wc}
        if path not in paths:raise FormatError('Choose a weapon from the catalog')
        level=request.get('level');rarity=request.get('rarity');perks=request.get('perks',[])
        if not isinstance(perks,list) or any(v not in {r['path'] for r in pc} for v in perks):raise FormatError('Unknown upgrade')
        melee='MeleeWeaponArchetype' in path
        # Reuse only the serialization headers of a known weapon, not its identity/state.
        candidates=[w for w in self.weapons if w.info()['editable'] and ('MeleeWeaponArchetype' in w.path)==melee]
        if not candidates:raise FormatError('No compatible weapon serialization template exists in this save')
        template=next((w for w in candidates if w.path==path),candidates[0])
        pd={p.name:p for p in template.pgprops}
        pg=template.pg.replace(replace_props(self.b,template.pg.data,template.pg.end,template.pgprops,{'Seed':pd['Seed'].replace(put(secrets.randbelow(65536)))}))
        runtime=template.runtime
        entries=[fs('NumUpgrades')+put(14)+put(4)+put(0)]
        if melee:entries.append(fs('Durability')+put(10)+put(4)+struct.pack('<f',1000.0))
        rt=runtime.p.replace(runtime.inner.replace(put(0)+put(len(entries))+b''.join(entries)))
        # Fresh random IDs prevent collisions with any existing inventory item.
        raw=b''.join([template.by['EntryID'].replace(uuid.uuid4().bytes),template.by['Archetype'].replace(fs(path)+put(0)),pg,template.by['UniqueId'].replace(uuid.uuid4().bytes),rt,fs('None')])
        ps,end=props(raw,0);weapon=Weapon(raw,0,end,ps,'New weapon',-1)
        change=dict(level=level,rarity=rarity,perks=perks)
        if 'durability' in request:change['durability']=request['durability']
        return weapon.rebuild(change)
    def replacement_record(self,weapon,change):
        raw=self.create_record(dict(path=change['path'],level=change.get('level',weapon.level),rarity=change.get('rarity',weapon.rarity),perks=change.get('perks',[]),**({'durability':change['durability']} if 'durability' in change else {})))
        ps,end=props(raw,0);pd={p.name:p for p in ps}
        # Keep both identities so weapon-wheel assignments continue referring to this slot.
        pg=pd['ProceduralGenerationContext'];pgprops,_=props(raw,pg.data,pg.end);newseed=next(p for p in pgprops if p.name=='Seed');oldseed=next(p for p in weapon.pgprops if p.name=='Seed')
        changes={name:pd[name].replace(weapon.by[name].payload()) for name in ('EntryID','UniqueId')}
        changes['ProceduralGenerationContext']=pg.replace(replace_props(raw,pg.data,pg.end,pgprops,{'Seed':newseed.replace(oldseed.payload())}))
        return replace_props(raw,0,end,ps,changes)
    def rebuild(self,changes,additions=None,deletions=None,ammo_changes=None,resource_changes=None,character_levels=None):
        resource_changes=resource_changes or [];character_levels=character_levels or {}
        deletions=deletions or []
        if not isinstance(deletions,list) or any(type(k)!=int for k in deletions):raise FormatError('Invalid deletion list')
        deleted=set(deletions)
        if len(deleted)!=len(deletions):raise FormatError('Duplicate deletion request')
        for key in deleted:
            if key<0 or key>=len(self.weapons) or not self.weapons[key].info()['editable']:raise FormatError('This item cannot be deleted')
        if not isinstance(changes,dict):raise FormatError('Invalid edits')
        if {str(k) for k in deleted}&set(changes):raise FormatError('An item cannot be both edited and deleted')
        additions=additions or []
        if not isinstance(additions,list) or len(additions)>256:raise FormatError("Invalid new-weapon list")
        created={}
        destinations={d["key"]:d for d in self.info()["destinations"]}
        for ar in self.arrays:
            if ar['key'] in destinations:
                d=destinations[ar['key']];removed=sum(w.idx in deleted for w in ar['weapons']);d['free']=max(0,d['capacity']-d['count']+removed)
        for request in additions:
            if not isinstance(request,dict) or set(request)-{'destination','path','level','rarity','perks','clone_source','durability'}:raise FormatError("Invalid weapon request")
            dest=request.get("destination")
            if dest not in destinations:raise FormatError("Invalid weapon destination")
            bucket=created.setdefault(dest,[])
            if len(bucket)>=destinations[dest]["free"]:raise FormatError("No free weapon slots in "+destinations[dest]["name"])
            bucket.append(self.create_record(request))
        if not isinstance(changes,dict):raise FormatError('Invalid edit set')
        known={str(w.idx) for w in self.weapons}
        if set(changes)-known:raise FormatError('Unknown weapon')
        for key in changes:
            if not self.weapons[int(key)].info()['editable']:raise FormatError('This item cannot be edited')
        section_edits={}
        ammo_changes=ammo_changes or {}
        if not isinstance(ammo_changes,dict) or set(ammo_changes)-{str(a['key']) for a in self.ammo}:raise FormatError('Unknown ammunition stack')
        for key,value in ammo_changes.items():
            if type(value)!=int or not 0<=value<=9_999_999:raise FormatError('Ammo count must be a whole number from 0 to 9,999,999')
        section_edits=character_editor.plan(self,resource_changes,character_levels,ammo_changes)
        for ar in self.arrays:
            new_items=created.get(ar['key'],[])
            payload=b''.join((self.replacement_record(w,changes[str(w.idx)]) if changes[str(w.idx)].get('path',w.path)!=w.path else w.rebuild(changes[str(w.idx)])) if str(w.idx) in changes else self.b[w.start:w.end] for w in ar['weapons'] if w.idx not in deleted)+b''.join(new_items)
            inner=ar['inner'];outer=ar['outer']
            if payload==inner.payload():continue
            new=outer.replace(put(len(ar['weapons'])-sum(w.idx in deleted for w in ar['weapons'])+len(new_items))+inner.replace(payload))
            section_edits.setdefault(ar['section'],[]).append((outer.start,outer.end,new))
        # Remove shortcut assignments for deleted carried weapons, only in their own
        # character section and only if no surviving weapon uses that persistent ID.
        for si,sec in enumerate(self.sections):
            arrs=[a for a in self.arrays if a['section']==si and a['kind']=='DIInventory']
            removed={w.by['UniqueId'].payload() for a in arrs for w in a['weapons'] if w.idx in deleted}
            surviving={w.by['UniqueId'].payload() for a in arrs for w in a['weapons'] if w.idx not in deleted}
            gone=removed-surviving
            if not gone:continue
            pattern=fs('AssignedItems')+fs('ArrayProperty')
            for m in re.finditer(re.escape(pattern),self.b[sec['start']:sec['end']]):
                outer,_=prop(self.b,sec['start']+m.start())
                if outer.extra!='StructProperty':continue
                inner,_=prop(self.b,outer.data+4)
                if inner is None or inner.extra!='AssignedItem':continue
                count=u32(self.b,outer.data);pos=inner.data;kept=[]
                for _ in range(count):
                    fields,end=props(self.b,pos,inner.end);pd={p.name:p for p in fields}
                    if 'PersistentId' not in pd or pd['PersistentId'].payload() not in gone:kept.append(self.b[pos:end])
                    pos=end
                if pos!=inner.end or inner.end!=outer.end:raise FormatError('Invalid shortcut array')
                if len(kept)!=count:
                    replacement=outer.replace(put(len(kept))+inner.replace(b''.join(kept)))
                    section_edits.setdefault(si,[]).append((outer.start,outer.end,replacement))
        out=[];last=0
        for si,sec in enumerate(self.sections):
            es=section_edits.get(si,[])
            if not es:continue
            payload=[];pos=sec['start']
            for start,end,new in sorted(es):payload.extend([self.b[pos:start],new]);pos=end
            payload.append(self.b[pos:sec['end']]);data=b''.join(payload)
            out.extend([self.b[last:sec['sizepos']],put(len(data)),data]);last=sec['end']
        out.append(self.b[last:]);result=b''.join(out)
        # Re-parse entire output and verify every requested value, before returning bytes.
        check=Save(result)
        if len(check.weapons)!=len(self.weapons)-len(deleted)+len(additions):raise FormatError('Validation changed inventory count')
        by_index={}
        for old_ar,new_ar in zip(self.arrays,check.arrays):
            for old_w,new_w in zip([w for w in old_ar['weapons'] if w.idx not in deleted],new_ar['weapons']):
                if old_w.id!=new_w.id:raise FormatError('Existing weapon identity changed')
                by_index[old_w.idx]=new_w
        seen_ids={w.id for w in self.weapons}
        seen_unique={w.by['UniqueId'].payload() for w in self.weapons}
        for key,c in changes.items():
            old=self.weapons[int(key)];new=by_index[old.idx]
            for field in ('level','rarity'):
                if field in c and getattr(new,field)!=c[field]:raise FormatError('Validation failed for '+field)
            if 'perks' in c and new.runtime.paths!=c['perks']:raise FormatError('Validation failed for upgrades')
            if 'durability' in c and new.runtime.durability()!=struct.unpack('<f',struct.pack('<f',c['durability']))[0]:raise FormatError('Durability validation failed')
            if 'path' in c and new.path!=c['path']:raise FormatError('Validation failed for replacement')
        for ar in self.arrays:
            target=next(a for a in check.arrays if a['key']==ar['key'])
            n=len(created.get(ar['key'],[]))
            if len(target['weapons'])!=len(ar['weapons'])-sum(w.idx in deleted for w in ar['weapons'])+n:raise FormatError('Destination inventory count mismatch')
            if n:
                for w,raw in zip(target['weapons'][-n:],created[ar['key']]):
                    if w.b[w.start:w.end]!=raw:raise FormatError('New weapon validation failed')
                    if w.id in seen_ids:raise FormatError('New weapon identity collision')
                    seen_ids.add(w.id)
                    uid=w.by['UniqueId'].payload()
                    if uid in seen_unique:raise FormatError('New persistent identity collision')
                    seen_unique.add(uid)
        for key,value in ammo_changes.items():
            if check.ammo[int(key)]['count']!=value:raise FormatError('Ammo validation failed')
        character_editor.verify(self,check,resource_changes,character_levels)
        return save_codec.encode(result,self.compression)
