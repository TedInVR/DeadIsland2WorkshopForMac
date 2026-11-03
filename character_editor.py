"""Fixed XP/cache edits and schema-validated DI2 resource stack editing."""
import json,re,struct,uuid
from pathlib import Path
# Compiled XP thresholds, cross-checked against the supplied Regular/NG+ saves.
# Numerical reference: https://deadisland.fandom.com/wiki/Experience_Points#Dead_Island_2
XP=(0,1500,4100,6800,9400,13300,17700,22500,27800,33500,39800,46700,54200,62300,71000,80300,90200,100900,112300,124500,137400,151200,165900,181500,198000,215700,234600,254700,276000,298500,322200,347100,373200,400500,429000,458700,489600,521700,555000,589500)
CATALOG=json.loads(Path(__file__).with_name('resource_catalog.json').read_text())
AMMO=json.loads(Path(__file__).with_name('ammo_catalog.json').read_text())
def attach(s):
    from save_core import fs,prop,props,u32,string,FormatError
    s.resource_arrays=[];s.character_fields={}
    for si,sec in enumerate(s.sections):
        if 'profile'in sec:
            pf=sec['profile'];marker=fs('Progression')+fs('/Script/DeadIsland.PlayerProgressionState')+struct.pack('<I',0)
            starts=[m.end()+sec['start'] for m in re.finditer(re.escape(marker),s.b[sec['start']:sec['end']])]
            if len(starts)==1:
                fields,end=props(s.b,starts[0]);field=next((x for x in fields if x.name=='XPValue' and x.typ=='IntProperty' and len(x.payload())==4),None)
                if field:
                    xp=u32(s.b,field.data);cap=40 if pf['ng'] else 30;level=min(cap,sum(v<=xp for v in XP))
                    pf.update(level=level,xp=xp,level_cap=cap);s.character_fields[pf['id']]=(si,field)
        for m in re.finditer(re.escape(fs('ArchetypeItems')+fs('ArrayProperty')),s.b[sec['start']:sec['end']]):
            outer,_=prop(s.b,sec['start']+m.start());inner,end=prop(s.b,outer.data+4)
            ar=next((a for a in s.arrays if a['section']==si and a['outer'].end==outer.start),None)
            if not ar or inner is None or inner.end!=outer.end:continue
            records=[];p=inner.data
            for _ in range(u32(s.b,outer.data)):
                start=p;fields,p=props(s.b,p,inner.end);d={x.name:x for x in fields}
                if 'Archetype'not in d or 'Count'not in d:raise FormatError('Unsupported resource record')
                if d['Count'].typ!='IntProperty' or len(d['Count'].payload())!=4:raise FormatError('Unsupported resource count')
                records.append(dict(start=start,end=p,fields=fields,by=d,path=string(s.b,d['Archetype'].data)[0],count=u32(s.b,d['Count'].data)))
            if p!=inner.end:raise FormatError('Invalid resource array length')
            s.resource_arrays.append(dict(key=ar['key'],section=si,outer=outer,inner=inner,records=records,group=ar['group'],kind=ar['kind'],profile_id=sec.get('profile',{}).get('id')))

def info(s):
    result=[]
    for a in s.resource_arrays:
        if a['kind']!='DIInventory' or not a['profile_id']:continue
        totals={}
        for r in a['records']:totals[r['path']]=totals.get(r['path'],0)+r['count']
        result.append(dict(key=a['key'],name=a['group'].replace('Carried weapons','Inventory'),profile_id=a['profile_id'],items=[dict(c,count=totals.get(c['path'],0)) for c in CATALOG]))
    return result

def plan(s,resource_changes,levels,ammo_changes,ammo_refills=()):
    from save_core import fs,prop,props,u32,put,replace_props,FormatError
    edits={};requests={};catalog={x['path']:x for x in CATALOG};groups={a['key']:a for a in s.resource_arrays if a['kind']=='DIInventory' and a['profile_id']}
    if not isinstance(ammo_refills,(list,tuple)) or any(type(k)!=int or k not in groups for k in ammo_refills) or len(set(ammo_refills))!=len(ammo_refills):raise FormatError('Choose known character inventories for normal ammo refills')
    ammo_catalog={x['path']:x for x in AMMO}
    if not isinstance(resource_changes,list) or len(resource_changes)>4096:raise FormatError('Invalid resource edits')
    for value in resource_changes:
        if not isinstance(value,dict) or set(value)!={'group','path','count'} or type(value['group'])!=int or value['group']not in groups or value['path']not in catalog:raise FormatError('Choose a known resource and character inventory')
        path=value['path'];count=value['count'];maximum=catalog[path]['maximum'];key=(value['group'],path)
        if key in requests:raise FormatError('Duplicate resource edit')
        if type(count)!=int or not 0<=count<=maximum:raise FormatError('Resource count must be a whole number from 0 to '+str(maximum))
        requests[key]=count
    ammo_by_pos={s.ammo[int(k)]['field'].data:v for k,v in ammo_changes.items()}
    template=next((r for a in s.resource_arrays for r in a['records'] if set(r['by'])=={'EntryID','Archetype','Count','UniqueId'}),None)
    for a in s.resource_arrays:
        pending={path:n for (group,path),n in requests.items() if group==a['key']};parts=[];changed=False;seen=set()
        refill=a['key'] in ammo_refills
        if refill:
            if any(r['by']['Count'].data in ammo_by_pos for r in a['records']):raise FormatError('Undo individual ammo edits before restoring this character to normal maximum')
            pending.update({path:item['maximum'] for path,item in ammo_catalog.items()})
        for r in a['records']:
            replacements={};path=r['path'];countfield=r['by']['Count']
            if refill and path in ammo_catalog and path in seen:
                changed=True;continue
            if path in pending:
                count=pending[path] if path not in seen else 0;seen.add(path)
                if count!=r['count']:replacements['Count']=countfield.replace(put(count))
            elif countfield.data in ammo_by_pos:replacements['Count']=countfield.replace(put(ammo_by_pos[countfield.data]))
            raw=replace_props(s.b,r['start'],r['end'],r['fields'],replacements) if replacements else s.b[r['start']:r['end']]
            parts.append(raw);changed=changed or bool(replacements)
        for path,n in pending.items():
            if path in seen or n==0:continue
            if template is None:raise FormatError('This save has no compatible resource serialization template')
            d=template['by'];new={name:d[name].replace(uuid.uuid4().bytes) for name in ('EntryID','UniqueId')}
            if refill and path in ammo_catalog:new['UniqueId']=d['UniqueId'].replace(bytes(16))
            new['Archetype']=d['Archetype'].replace(fs(path)+put(0));new['Count']=d['Count'].replace(put(n))
            parts.append(replace_props(s.b,template['start'],template['end'],template['fields'],new));changed=True
        if changed:
            o=a['outer'];i=a['inner'];replacement=o.replace(put(len(parts))+i.replace(b''.join(parts)))
            edits.setdefault(a['section'],[]).append((o.start,o.end,replacement))
    if not isinstance(levels,dict) or set(levels)-set(s.character_fields):raise FormatError('Unknown editable character')
    for pid,level in levels.items():
        pf=next(p for p in s.profiles if p['id']==pid);cap=pf['level_cap']
        if type(level)!=int or not 1<=level<=cap:raise FormatError('Character level must be from 1 to '+str(cap))
        si,field=s.character_fields[pid];edits.setdefault(si,[]).append((field.data,field.end,put(XP[level-1])))
        # Profile-menu summary cache, a typed integer in the account summary.
        sec=next((x for x in s.sections if x['name']=='CharacterProfileAccount'),None)
        if sec:
            marker=fs(pid);start=s.b.find(marker,sec['start'],sec['end'])
            if start>=0:
                next_profile=min([s.b.find(fs(p['id']),start+len(marker),sec['end']) for p in s.profiles if s.b.find(fs(p['id']),start+len(marker),sec['end'])>=0] or [sec['end']])
                pos=s.b.find(fs('KeyProgression'),start,next_profile)
                if pos>=0:
                    q=pos+len(fs('KeyProgression'))
                    if u32(s.b,q)!=14 or u32(s.b,q+4)!=4:raise FormatError('Unsupported level summary representation')
                    edits.setdefault(s.sections.index(sec),[]).append((q+8,q+12,put(level)))
        # Account-level cached GUID->level map. Absent entries are left absent.
        for si2,sec2 in enumerate(s.sections):
            for m in re.finditer(re.escape(fs('PlayerLevels')+fs('MapProperty')),s.b[sec2['start']:sec2['end']]):
                outer,_=prop(s.b,sec2['start']+m.start());inner,_=prop(s.b,outer.data)
                if inner is None or inner.extra!='GUID' or inner.end!=outer.end:raise FormatError('Unsupported level cache')
                q=inner.data
                if u32(s.b,q)!=0 or inner.end-q!=8+20*u32(s.b,q+4):raise FormatError('Unsupported level map entries')
                for offset in range(q+8,inner.end,20):
                    guid=''.join(s.b[k:k+4][::-1].hex() for k in range(offset,offset+16,4)).upper()
                    if guid==pid:edits.setdefault(si2,[]).append((offset+16,offset+20,put(level)))
    return edits

def verify(before,after,resources,levels,ammo_refills=()):
    from save_core import FormatError
    groups={a['key']:a for a in info(after)}
    for request in resources:
        item=next(i for i in groups[request['group']]['items'] if i['path']==request['path'])
        if item['count']!=request['count']:raise FormatError('Resource validation failed')
    for pid,level in levels.items():
        pf=next(p for p in after.profiles if p['id']==pid)
        if pf['level']!=level or pf['xp']!=XP[level-1]:raise FormatError('Character progression validation failed')
    arrays={a['key']:a for a in after.resource_arrays}
    for key in ammo_refills:
        for item in AMMO:
            records=[r for r in arrays[key]['records'] if r['path']==item['path']]
            if len(records)!=1 or records[0]['count']!=item['maximum']:raise FormatError('Normal ammunition refill validation failed')
