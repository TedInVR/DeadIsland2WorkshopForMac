"""Story diagnostics; reset writes suspended after a live-console regression. Character data is preserved verbatim.

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

RESET_UNAVAILABLE = ('Story reset is temporarily unavailable: clearing campaign data can make an existing character appear as New Game. Restore a pre-reset backup; opening the affected save does not repair it.')

def info(s):
    return dict(available=False,characters=[],reason=RESET_UNAVAILABLE)

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

def apply(s,requests):
    """Fail closed after the live-console regression. Never clear campaigns."""
    if not isinstance(requests,list):raise StoryError('Invalid story reset list')
    if requests:raise StoryError(RESET_UNAVAILABLE)
    return s.b
