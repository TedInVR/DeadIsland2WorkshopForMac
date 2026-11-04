"""Post-tutorial story reset with private, persistent starting points. Character data is preserved verbatim.

Independent reader of the section/node/script framing documented by
SteffenL/file-format-docs. No personal starting points are distributed; only story state is cached locally.
"""
from dataclasses import dataclass
import struct

class StoryError(ValueError): pass

def integer(b, p):
    if p < 0 or p + 4 > len(b): raise StoryError('Truncated story data')
    return struct.unpack_from('<I', b, p)[0]

def count(b, p, maximum=100000):
    n = integer(b, p)
    if n > maximum: raise StoryError('Unsupported story collection size')
    return n

@dataclass
class Script:
    name: str
    typ: str
    start: int
    end: int
    tail: int
    fields: list

@dataclass
class Node:
    name: str
    start: int
    end: int
    scripts: list
    children: list

def variants(b, p):
    from save_core import string
    records=[]
    n=count(b,p);p+=4
    for _ in range(n):
        start=p;name,p=string(b,p);typ=integer(b,p);size=integer(b,p+4);p+=8
        if p+size>len(b):raise StoryError('Truncated summary value')
        records.append((name,typ,b[p:p+size],b[start:p+size]));p+=size
    if len({r[0] for r in records})!=len(records):raise StoryError('Duplicate summary key')
    return records,p

def _pairs(b,p):
    from save_core import string
    n=count(b,p);p+=4
    for _ in range(n):_,p=string(b,p);p+=4
    return p

def read_script(b,p):
    from save_core import string,props
    start=p;name,p=string(b,p);typ,p=string(b,p)
    if integer(b,p)!=0:raise StoryError('Unsupported story script version')
    fields,p=props(b,p+4)
    if integer(b,p)!=0:raise StoryError('Unsupported story script trailer')
    p+=4;tail=p
    if typ.endswith(('.CharacterProfileSummary','.OptionsHierarchyPersistentState')):
        _,p=variants(b,p)
    elif typ.endswith('.DIInventoryPersistentData'):p=_pairs(b,p)
    elif typ.endswith('.KnowledgeBasePersistentDataCollection'):
        n=count(b,p+4);p+=8
        for _ in range(n):_,p=string(b,p);p+=12
    elif typ.endswith('.GameAchievementsPersistentState'):
        n=count(b,p);p+=4
        for _ in range(n):_,p=string(b,p)
        p=_pairs(b,p)
    elif typ.endswith('.ScopedDialogueKBFactPersistentDataCollection'):
        n=count(b,p);p+=4
        for _ in range(n):
            _,p=string(b,p);_,p=string(b,p);n2=count(b,p+4);p+=8+4*n2
    if p>len(b):raise StoryError('Story script exceeds file')
    return Script(name,typ,start,p,tail,fields),p

def read_node(b,p,name='',depth=0,budget=None):
    from save_core import string
    if budget is None:budget=[100000]
    budget[0]-=1
    if depth>64 or budget[0]<0:raise StoryError('Story tree exceeds supported limits')
    start=p;nc=count(b,p);ns=count(b,p+4,10000);p+=8;scripts=[];children=[]
    for _ in range(ns):
        item,p=read_script(b,p);scripts.append(item)
    for _ in range(nc):
        child_name,p=string(b,p);item,p=read_node(b,p,child_name,depth+1,budget);children.append(item)
    if len({x.name for x in children})!=len(children):raise StoryError('Duplicate story node')
    return Node(name,start,p,scripts,children),p

def tree(s,sec):
    node,end=read_node(s.b,sec['start'],sec['name'])
    if end!=sec['end']:raise StoryError('Unsupported story section framing')
    return node

def named(items,name):
    found=[x for x in items if x.name==name]
    if len(found)!=1:raise StoryError('Missing or ambiguous story component: '+name)
    return found[0]

def raw(b,x):return b[x.start:x.end]

def field(script,name):return named(script.fields,name)

def quest_counts(s,root):
    from save_core import prop
    stats=named(root.scripts,'QuestStats');values=[]
    for name in ('QuestRecords','ObjectiveRecords'):
        f=field(stats,name);inner,end=prop(s.b,f.data)
        if inner is None or inner.extra!='QuestRecord' or end!=f.end:raise StoryError('Unsupported quest statistics')
        values.append(count(s.b,inner.data+4))
    return values

def walk(root):
    yield root
    for ch in root.children:yield from walk(ch)

def inspect(s):
    from save_core import string
    result=[]
    for sec in s.sections:
        if 'profile' not in sec:continue
        pf=sec['profile'];root=tree(s,sec);campaign=named(root.children,'Campaign')
        gp=named(named(root.children,'GameProgression').scripts,'GameProgressionState')
        location=string(s.b,field(gp,'MapPath').data)[0];states={};started=[]
        for nd in walk(campaign):
            for sc in nd.scripts:
                if sc.typ!='/Script/DeadIsland.DIQuestInstancePersistentDataCollection':continue
                state=string(s.b,field(sc,'State').data)[0].split('::')[-1]
                states[state]=states.get(state,0)+1
                if state=='Started':started.append(sc.name)
        quests,objectives=quest_counts(s,root)
        result.append(dict(id=pf['id'],name=pf['name'],ng=pf['ng'],level=pf.get('level'),location=location,completed=states.get('Complete',0),started=started))
    return result

# Keep character statistics, skills, challenges, collectibles, cosmetics,
# entitlements, rewards, shortcuts and all inventory outside this allowlist.
ROOT_STORY=('Discovery','GameProgression','Dialogue','Sectors')
CAMPAIGN_STORY=('MissionSystem','LightingScenario','TrackedWaypoint','WorldActorState')
SUMMARY_STORY=frozenset(('KeyLocation','KeyActiveQuest','QSTLN_DI2','QSTLN_DI2_EXP1','QSTLN_DI2_EXP02'))

def splice(b,start,end,edits):
    parts=[];pos=start
    for lo,hi,value in sorted(edits):
        if lo<pos or hi<lo or hi>end:raise StoryError('Overlapping story edits')
        parts.extend((b[pos:lo],value));pos=hi
    return b''.join(parts)+b[pos:end]

def summary_node(s,pid):
    sec=next((x for x in s.sections if x['name']=='CharacterProfileAccount'),None)
    if sec is None:raise StoryError('Missing character summaries')
    root=tree(s,sec);nd=named(named(root.children,'ProfileSummaries').children,pid)
    if len(nd.scripts)!=1 or nd.children or not nd.scripts[0].typ.endswith('.CharacterProfileSummary'):raise StoryError('Unsupported character summary')
    sc=nd.scripts[0];records,end=variants(s.b,sc.tail)
    if end!=sc.end:raise StoryError('Unsupported character summary tail')
    return sec,nd,sc,records

# Mission counters drive the menu bars. Totals are denominators and stay intact.
import base64,re
import story_points
COUNTER=re.compile(r'^(Main|Side|Tertiary)MissionsCompleted(?:_|$)')
OPENING_MAP='/Game/DI2/Maps/BeverlyHills/Mansions/Bev_Mansions_P_Main'
PIECES=('QuestStats',)+ROOT_STORY+tuple('Campaign/'+n for n in CAMPAIGN_STORY)


def mission_counters(s,root):
    from save_core import string
    sc=named(named(root.children,'StatGathering').scripts,'Stats')
    f=field(sc,'StoredStats')
    if f.typ!='MapProperty' or f.extra!='NameProperty|IntProperty' or integer(s.b,f.data)!=0:raise StoryError('Unsupported mission counters')
    p=f.data+8;records=[]
    for _ in range(count(s.b,f.data+4)):
        name,p=string(s.b,p);value=integer(s.b,p);records.append((name,p,value));p+=4
    if p!=f.end or len({x[0]for x in records})!=len(records):raise StoryError('Invalid mission counter map')
    return records


def completed_set(s,sc):
    from save_core import string
    f=field(sc,'CompletedObjectives')
    if f.typ!='SetProperty' or f.extra!='StrProperty' or integer(s.b,f.data)!=0:raise StoryError('Unsupported mission checkpoint')
    p=f.data+8;values=[]
    for _ in range(count(s.b,f.data+4)):
        value,p=string(s.b,p);values.append(value)
    if p!=f.end:raise StoryError('Invalid mission checkpoint')
    return set(values)


def at_dumpster(s,sec,root):
    from save_core import string
    import struct
    campaign=named(root.children,'Campaign');ms=named(campaign.children,'MissionSystem')
    gp=named(named(root.children,'GameProgression').scripts,'GameProgressionState')
    if string(s.b,field(gp,'MapPath').data)[0]!=OPENING_MAP:return False
    location=field(gp,'PlayerLocation').payload()
    if len(location)!=12:return False
    xyz=struct.unpack('<fff',location)
    import math
    if not all(math.isfinite(v)for v in xyz):return False
    if sum((v-c)**2 for v,c in zip(xyz,(-31000,-500,4700)))>2500**2:return False
    missions=[]
    for n in walk(ms):
        for sc in n.scripts:
            if sc.typ=='/Script/DeadIsland.DIQuestInstancePersistentDataCollection':
                missions.append((sc.name.lower(),string(s.b,field(sc,'State').data)[0],sc))
    if not 90<=len(missions)<=200:return False
    complete=[n for n,state,_ in missions if state=='EMissionState::Complete']
    active=[n for n,state,_ in missions if state=='EMissionState::Started']
    if complete!=['mis_main01'] or active!=['mis_main02']:return False
    main=next(sc for n,_,sc in missions if n=='mis_main02')
    if integer(s.b,field(main,'ObjectiveDisplayIndex').data)!=4:return False
    hard=None
    for n in walk(ms):
        for sc in n.scripts:
            if sc.name.lower()=='mis_main02_hard_checkpoint':hard=sc
    if hard is None or completed_set(s,hard)!={'OBJ_Main01_08a_Cutscene_TheThanksIGet'}:return False
    q,o=quest_counts(s,root)
    return q==1 and o<=64


def component(root,name):
    if name=='QuestStats':return named(root.scripts,name)
    if name.startswith('Campaign/'):return named(named(root.children,'Campaign').children,name.split('/',1)[1])
    return named(root.children,name)


def validate_point(s,value,ng):
    from save_core import string
    if not isinstance(value,dict) or value.get('version')!=1 or value.get('header')!=s.b[:21].hex() or value.get('ng') is not ng:raise StoryError('Story starting point does not match this game build and mode')
    if not isinstance(value.get('pieces'),dict)or set(value['pieces'])!=set(PIECES):raise StoryError('Incomplete story starting point')
    pieces={}
    for name,encoded in value['pieces'].items():
        if not isinstance(encoded,str) or len(encoded)>8*1024*1024:raise StoryError('Invalid story component size')
        try:raw_piece=base64.b64decode(encoded,validate=True)
        except Exception as e:raise StoryError('Invalid story component encoding') from e
        if name=='QuestStats':parsed,end=read_script(raw_piece,0)
        else:parsed,end=read_node(raw_piece,0,name.split('/')[-1])
        if end!=len(raw_piece) or parsed.name!=name.split('/')[-1]:raise StoryError('Invalid story component framing')
        pieces[name]=raw_piece
    # Reassemble a small inspection tree around the cached story fragments so
    # the same checkpoint gate can be reapplied without any character template.
    from save_core import put,fs
    camp=put(4)+put(0)+b''.join(fs(n)+pieces['Campaign/'+n]for n in CAMPAIGN_STORY)
    children=[('Campaign',camp)]+[(n,pieces[n])for n in ROOT_STORY]
    body=put(len(children))+put(1)+pieces['QuestStats']+b''.join(fs(n)+v for n,v in children)
    from types import SimpleNamespace
    fake=SimpleNamespace(b=body);root,end=read_node(body,0)
    if end!=len(body) or not at_dumpster(fake,None,root):raise StoryError('Stored starting point is not the post-tutorial checkpoint')
    counts=value.get('counters',{})
    if not isinstance(counts,dict) or not {'MainMissionsCompleted','SideMissionsCompleted','TertiaryMissionsCompleted'}<=set(counts):raise StoryError('Starting point has no mission counters')
    if any(not isinstance(k,str) or not COUNTER.match(k) or k.endswith('_Total') or type(v)!=int or not 0<=v<=5000 for k,v in counts.items()):raise StoryError('Invalid starting-point mission counter')
    if [counts[k]for k in ('MainMissionsCompleted','SideMissionsCompleted','TertiaryMissionsCompleted')]!=[1,0,0]:raise StoryError('Starting-point mission counts are not at the opening')
    summary=value.get('summary',[])
    if not isinstance(summary,list) or len(summary)>len(SUMMARY_STORY):raise StoryError('Invalid starting-point summary')
    summary_bytes=b''.join(base64.b64decode(x,validate=True)for x in summary)
    records,end=variants(put(len(summary))+summary_bytes,0)
    if end!=4+len(summary_bytes) or not {'KeyLocation','KeyActiveQuest','QSTLN_DI2'}<={r[0]for r in records}:raise StoryError('Incomplete starting-point summary')
    for name,typ,payload,_ in records:
        if name not in SUMMARY_STORY or typ!=24:raise StoryError('Unexpected starting-point summary field')
        text,p=string(payload,0)
        if not text.startswith('/Game/DI2/') or p!=len(payload):raise StoryError('Invalid starting-point path')
        if name=='KeyLocation' and text!=OPENING_MAP:raise StoryError('Starting-point summary location mismatch')
        if name in ('KeyActiveQuest','QSTLN_DI2')and not text.lower().endswith('.mis_main02'):raise StoryError('Starting-point summary mission mismatch')
    return pieces,counts,summary_bytes,len(summary)


def capture(s,sec,root):
    from save_core import fs
    pf=sec['profile'];pieces={name:raw(s.b,component(root,name))for name in PIECES}
    guid=b''.join(bytes.fromhex(pf['id'])[i:i+4][::-1]for i in range(0,16,4))
    if any(fs(pf['id'])in v or guid in v for v in pieces.values()):raise StoryError('Starting-point story includes character-bound data')
    _,_,_,records=summary_node(s,pf['id'])
    value=dict(version=1,header=s.b[:21].hex(),ng=pf['ng'],pieces={k:base64.b64encode(v).decode()for k,v in pieces.items()},counters={k:v for k,_,v in mission_counters(s,root)if COUNTER.match(k)and not k.endswith('_Total')},summary=[base64.b64encode(v).decode()for k,_,_,v in records if k in SUMMARY_STORY])
    validate_point(s,value,pf['ng']);return value


def ensure_points(s):
    available={};errors={}
    for ng in (False,True):
        try:
            value=story_points.load(s.b[:21],ng)
            if value is not None:validate_point(s,value,ng);available[ng]=value;continue
            for sec in s.sections:
                if sec.get('profile',{}).get('ng')is not ng:continue
                root=tree(s,sec)
                if at_dumpster(s,sec,root):
                    value=capture(s,sec,root);value=story_points.save_once(s.b[:21],ng,value);validate_point(s,value,ng);available[ng]=value;break
        except (ValueError,OSError,KeyError,IndexError,TypeError,struct.error)as e:errors[ng]=str(e)
    return available,errors


def info(s):
    if hasattr(s,'_story_info'):return s._story_info
    points,errors=ensure_points(s)
    value=dict(available=bool(points),checkpoints=[dict(ng=ng,available=ng in points,reason=errors.get(ng,''))for ng in (False,True)],reason=''if points else 'Open a save with a character saved beside the dumpster after the prologue once. Workshop privately remembers that starting point for later resets.')
    s._story_info=value;return value


def apply(s,requests):
    from save_core import Save,put
    if not isinstance(requests,list) or len(requests)>12:raise StoryError('Invalid story reset list')
    if not requests:return s.b
    targets=set();known={x['name']:x for x in s.sections if 'profile'in x}
    for request in requests:
        if not isinstance(request,dict)or set(request)!={'target'}or not isinstance(request['target'],str)or request['target']not in known or request['target']in targets:raise StoryError('Choose each character to reset once')
        targets.add(request['target'])
    points,errors=ensure_points(s);edits={}
    for pid in targets:
        sec=known[pid];ng=sec['profile']['ng']
        if ng not in points:raise StoryError(errors.get(ng)or 'No saved post-tutorial starting point for '+('NG+'if ng else 'Regular')+'. Open your checkpoint save once first.')
        pieces,counts,summary_bytes,summary_count=validate_point(s,points[ng],ng);root=tree(s,sec);changes=[]
        for name,new in pieces.items():
            old=component(root,name);changes.append((old.start,old.end,new))
        for name,p,value in mission_counters(s,root):
            if COUNTER.match(name)and not name.endswith('_Total'):
                if name not in counts:raise StoryError('Starting point has no matching regional mission counter')
                changes.append((p,p+4,put(counts[name])))
        edits[s.sections.index(sec)]=changes
        account,_,sc,records=summary_node(s,pid);kept=[r[3]for r in records if r[0]not in SUMMARY_STORY]
        edits.setdefault(s.sections.index(account),[]).append((sc.tail,sc.end,put(len(kept)+summary_count)+b''.join(kept)+summary_bytes))
    parts=[];last=0
    for si,sec in enumerate(s.sections):
        if si not in edits:continue
        value=splice(s.b,sec['start'],sec['end'],edits[si]);parts.extend((s.b[last:sec['sizepos']],put(len(value)),value));last=sec['end']
    parts.append(s.b[last:]);result=b''.join(parts);check=Save(result)
    if check.profiles!=s.profiles:raise StoryError('Story reset changed a character level or identity')
    for i,(old,new)in enumerate(zip(s.sections,check.sections)):
        expected=splice(s.b,old['start'],old['end'],edits.get(i,[]))
        if check.b[new['start']:new['end']]!=expected:raise StoryError('Story reset changed data outside its approved fields')
        if old['name']in targets:
            before=tree(s,old);after=tree(check,new)
            if not at_dumpster(check,new,after):raise StoryError('Story reset did not retain a playable post-tutorial checkpoint')
            for sc in before.scripts:
                if sc.name!='QuestStats'and raw(s.b,sc)!=raw(check.b,named(after.scripts,sc.name)):raise StoryError('Story reset changed character properties')
            for child in before.children:
                if child.name not in ROOT_STORY+('Campaign','StatGathering')and raw(s.b,child)!=raw(check.b,named(after.children,child.name)):raise StoryError('Story reset changed inventory, skills or character state')
            ca=named(before.children,'Campaign');cb=named(after.children,'Campaign')
            if [raw(s.b,x)for x in ca.scripts]!=[raw(check.b,x)for x in cb.scripts]:raise StoryError('Story reset changed fury state')
    return result
