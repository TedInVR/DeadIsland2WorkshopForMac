"""Experimental generated story reset. Character data is preserved verbatim.

Independent reader of the section/node/script framing documented by
SteffenL/file-format-docs. No personal save templates or reference characters are used.
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

def info(s):
    if hasattr(s,'_story_info'):return s._story_info
    try:result=dict(available=True,characters=inspect(s))
    except (ValueError,struct.error,IndexError,KeyError) as e:result=dict(available=False,characters=[],reason=str(e))
    s._story_info=result;return result

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

def initial_state(s,root):
    """Generate an uninitialized campaign from typed fields, never a donor save.

    Empty campaign/world collections and an unset saved location match the
    observed fresh NG+ slot. The game chooses its mode-specific opening on load.
    No identity, XP, inventory, skill or stat fields are reset.
    """
    from save_core import prop,put
    changes=[]
    stats=named(root.scripts,'QuestStats')
    if {f.name for f in stats.fields}!={'QuestRecords','ObjectiveRecords'}:raise StoryError('Unsupported quest statistics fields')
    stats_edits=[]
    for f in stats.fields:
        inner,end=prop(s.b,f.data)
        if inner is None or inner.extra!='QuestRecord' or end!=f.end:raise StoryError('Unsupported quest statistics schema')
        stats_edits.append((f.start,f.end,f.replace(inner.replace(put(0)+put(0)))))
    changes.append((stats.start,stats.end,splice(s.b,stats.start,stats.end,stats_edits)))
    campaign=named(root.children,'Campaign')
    if set(c.name for c in campaign.children)-set(CAMPAIGN_STORY):raise StoryError('Unknown campaign state; reset is unsupported for this save')
    changes.append((campaign.start,campaign.end,put(0)+put(len(campaign.scripts))+b''.join(raw(s.b,x) for x in campaign.scripts)))
    discovery=named(root.children,'Discovery')
    if discovery.children or len(discovery.scripts)!=1:raise StoryError('Unsupported discovery state')
    ds=discovery.scripts[0];df=field(ds,'DiscoveredObjects')
    if len(ds.fields)!=1 or df.typ!='ArrayProperty' or df.extra!='StrProperty':raise StoryError('Unsupported map discovery schema')
    changes.append((df.start,df.end,df.replace(put(0))))
    game=named(root.children,'GameProgression')
    if game.children or len(game.scripts)!=1:raise StoryError('Unsupported saved location')
    gp=game.scripts[0]
    if {f.name for f in gp.fields}!={'MapPath','PlayerLocation','bSavedPlayerLocation'}:raise StoryError('Unsupported saved location fields')
    for f in gp.fields:
        if f.name=='MapPath':
            if f.typ!='StrProperty':raise StoryError('Unsupported location path')
            value=f.replace(put(0))
        elif f.name=='PlayerLocation':
            if f.typ!='StructProperty' or f.extra!='Vector' or len(f.payload())!=12:raise StoryError('Unsupported location vector')
            value=f.replace(bytes(12))
        else:
            if f.typ!='BoolProperty' or len(f.payload()) or f.raw()[-1:]!=b'\0':raise StoryError('Unsupported saved-location flag')
            value=bytearray(f.raw());value[-2]=0;value=bytes(value)
        changes.append((f.start,f.end,value))
    for name in ('Dialogue','Sectors'):
        nd=named(root.children,name);changes.append((nd.start,nd.end,put(0)+put(0)))
    return changes


def apply(s,requests):
    """Clear selected stories; use the game's mode-specific initialization."""
    from save_core import put
    if not isinstance(requests,list) or len(requests)>12:raise StoryError('Invalid story reset list')
    if not requests:return s.b
    known={sec['name']:sec for sec in s.sections if 'profile' in sec};targets=set()
    for request in requests:
        if not isinstance(request,dict) or set(request)!={'target'} or not isinstance(request['target'],str):raise StoryError('Choose a character to reset')
        pid=request['target']
        if pid not in known or pid in targets:raise StoryError('Invalid or duplicate story reset character')
        targets.add(pid)
    edits={}
    for pid in targets:
        sec=known[pid];root=tree(s,sec);edits[s.sections.index(sec)]=initial_state(s,root)
        summary,nd,sc,records=summary_node(s,pid)
        kept=[x[3] for x in records if x[0] not in SUMMARY_STORY]
        edits.setdefault(s.sections.index(summary),[]).append((sc.tail,sc.end,put(len(kept))+b''.join(kept)))
    output=[];last=0
    for si,sec in enumerate(s.sections):
        if si not in edits:continue
        data=splice(s.b,sec['start'],sec['end'],edits[si]);output.extend((s.b[last:sec['sizepos']],put(len(data)),data));last=sec['end']
    output.append(s.b[last:]);result=b''.join(output)
    from save_core import Save
    check=Save(result)
    for si,sec in enumerate(s.sections):
        new=check.sections[si];wanted=splice(s.b,sec['start'],sec['end'],edits.get(si,[]))
        if check.b[new['start']:new['end']]!=wanted:raise StoryError('Story reset preservation check failed')
        if sec['name'] not in targets:continue
        before=tree(s,sec);after=tree(check,new)
        for sc in before.scripts:
            if sc.name!='QuestStats' and raw(s.b,sc)!=raw(check.b,named(after.scripts,sc.name)):raise StoryError('Story reset changed character data')
        for child in before.children:
            if child.name not in ROOT_STORY+('Campaign',) and raw(s.b,child)!=raw(check.b,named(after.children,child.name)):raise StoryError('Story reset changed inventory or character state')
        bc=named(before.children,'Campaign');ac=named(after.children,'Campaign')
        if ac.children:raise StoryError('Campaign reset validation failed')
        if [raw(s.b,x) for x in bc.scripts]!=[raw(check.b,x) for x in ac.scripts]:raise StoryError('Story reset changed fury state')
        if quest_counts(check,after)!=[0,0]:raise StoryError('Quest reset validation failed')
    return result
