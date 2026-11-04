"""Synthetic story fixtures only; no user save data or templates."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import story_editor as story
from save_core import fs,put,prop

GUIDS=['11111111222222223333333344444444','55555555666666667777777788888888','99999999AAAAAAAABBBBBBBBCCCCCCCC']
def tagged(name,typ,payload,extra=''):
    header=fs(name)+fs(typ)+put(len(payload))+put(0)
    if typ=='StructProperty':header+=fs(extra)+bytes(16)
    elif typ in ('EnumProperty','ArrayProperty'):header+=fs(extra)
    elif typ=='MapProperty':header+=b''.join(fs(x) for x in extra.split('|'))
    return header+b'\0'+payload

def script(name,typ,fields=(),tail=b''):
    return fs(name)+fs('/Script/DeadIsland.'+typ)+put(0)+b''.join(fields)+fs('None')+put(0)+tail

def node(scripts=(),children=()):return put(len(children))+put(len(scripts))+b''.join(scripts)+b''.join(fs(n)+b for n,b in children)
def scalar_node(name,value):return node([script(name,'TestState',[tagged('Value','StrProperty',fs(value))])])
def statistics(name,n):
    inner=tagged(name,'StructProperty',put(0)+put(n),extra='QuestRecord')
    return tagged(name,'MapProperty',inner,extra='IntProperty|StructProperty')
def character(pid,early,mode=False):
    missions=[]
    for i in range(96):
        state='Started' if early and i==0 else 'Waiting' if early else 'Complete'
        missions.append((('mis_main01' if i==0 else 'mission_'+str(i)),node([script('mis_main01' if i==0 else 'mission_'+str(i),'DIQuestInstancePersistentDataCollection',[tagged('State','EnumProperty',fs('EMissionState::'+state),'EMissionState')])])))
    campaign=node([script('FuryValues','FuryValuesState',[tagged('CurrentFury','FloatProperty',put(123))])],[(n,node(children=missions) if n=='MissionSystem' else scalar_node(n,'early' if early else 'late')) for n in story.CAMPAIGN_STORY])
    return node([script('CharacterData','CharacterProfile',[tagged('Owner','StrProperty',fs(pid))]),script('Progression','PlayerProgressionState',[tagged('XPValue','IntProperty',put(6800 if early else 589500))]),script('QuestStats','QuestStatsTrackerRuntimeState',[statistics('QuestRecords',0 if early else 90),statistics('ObjectiveRecords',2 if early else 1000)])],[(n,scalar_node(n,'early' if early else 'late')) for n in ('Discovery','Dialogue','Sectors')]+[('Campaign',campaign),('GameProgression',node([script('GameProgressionState','GameProgressionPersistentData',[tagged('MapPath','StrProperty',fs('/test/start' if early else '/test/end'))])])),('DIInventory',scalar_node('Items','private equipment '+pid)),('SkillSlots',scalar_node('ActiveSkills','skills '+pid)),('CharacterStats',scalar_node('Stats','stats '+pid)),('Stash',scalar_node('Items','locker '+pid))])
def variant(name,typ,value):return fs(name)+put(typ)+put(len(value))+value

def make_save(raw=None):
    if raw is None:
        summaries=[]
        for i,pid in enumerate(GUIDS):
            vals=[variant('KeyProgression',14,put(40 if i==0 else 4)),variant('KeyArchetype',24,fs('class '+pid)),variant('KeyCosplay',19,fs('costume '+pid))]+[variant(k,24,fs(('start' if i else 'end')+k)) for k in story.SUMMARY_STORY if i==0 or k in ('KeyLocation','KeyActiveQuest','QSTLN_DI2')]
            summaries.append((pid,node([script(pid,'CharacterProfileSummary',tail=put(len(vals))+b''.join(vals))])))
        bodies=[('CharacterProfileAccount',node(children=[('ProfileSummaries',node(children=summaries))]))]+[(pid,character(pid,i>0)) for i,pid in enumerate(GUIDS)]
        raw=put(len(bodies))+b''.join(fs(n)+put(len(b))+b for n,b in bodies)
    sections=[];p=4
    for _ in range(int.from_bytes(raw[:4],'little')):
        from save_core import string
        n,p=string(raw,p);sizepos=p;size=int.from_bytes(raw[p:p+4],'little');p+=4;sec=dict(name=n,start=p,end=p+size,sizepos=sizepos)
        if n in GUIDS:sec['profile']=dict(id=n,name='Test Slayer',ng=n==GUIDS[2],level=40 if n==GUIDS[0] else 4)
        sections.append(sec);p+=size
    if p!=len(raw):raise ValueError('Invalid synthetic framing')
    return SimpleNamespace(b=raw,sections=sections)

class StoryTests(unittest.TestCase):
    def setUp(self):self.s=make_save()
    def apply(self,requests):
        with patch('save_core.Save',side_effect=make_save):return make_save(story.apply(self.s,requests))
    def test_reset_preserves_level_inventory_skills_identity_other_characters(self):
        request=dict(target=GUIDS[0],reference=GUIDS[1]);out=self.apply([request])
        old=story.tree(self.s,self.s.sections[1]);new=story.tree(out,out.sections[1]);donor=story.tree(self.s,self.s.sections[2])
        for name in ('DIInventory','SkillSlots','CharacterStats','Stash'):
            self.assertEqual(story.raw(self.s.b,story.named(old.children,name)),story.raw(out.b,story.named(new.children,name)))
        for name in ('CharacterData','Progression'):
            self.assertEqual(story.raw(self.s.b,story.named(old.scripts,name)),story.raw(out.b,story.named(new.scripts,name)))
        for name in story.ROOT_STORY:self.assertEqual(story.raw(out.b,story.named(new.children,name)),story.raw(self.s.b,story.named(donor.children,name)))
        for i in (2,3):self.assertEqual(self.s.b[self.s.sections[i]['start']:self.s.sections[i]['end']],out.b[out.sections[i]['start']:out.sections[i]['end']])
        a=story.summary_node(self.s,GUIDS[0])[3];b=story.summary_node(out,GUIDS[0])[3]
        self.assertEqual([x[3] for x in a if x[0] not in story.SUMMARY_STORY],[x[3] for x in b if x[0] not in story.SUMMARY_STORY])
        self.assertEqual(next(x for x in story.inspect(out) if x['id']==GUIDS[0])['completed'],0)
    def test_reject_mismatched_modes_self_progressed_reference_duplicates(self):
        for rs in ([dict(target=GUIDS[0],reference=GUIDS[2])],[dict(target=GUIDS[0],reference=GUIDS[0])],[dict(target=GUIDS[1],reference=GUIDS[0])],[dict(target=GUIDS[0],reference=GUIDS[1])]*2,[dict(target=GUIDS[0],reference=GUIDS[1]),dict(target=GUIDS[1],reference=GUIDS[0])]):
            with self.assertRaises(story.StoryError):self.apply(rs)
    def test_noop_and_truncated_or_unsupported_input(self):
        self.assertEqual(story.apply(self.s,[]),self.s.b)
        for b in (b'',put(100001)+put(0),put(0)+put(1)+fs('x')+fs('/test')+put(9)):
            with self.assertRaises(ValueError):story.read_node(b,0)
    def test_reference_detection_does_not_use_level(self):
        refs=story.inspect(self.s)
        self.assertFalse(refs[0]['reference']);self.assertTrue(refs[1]['reference'])
        self.s.sections[2]['profile']['level']=40
        self.assertTrue(story.inspect(self.s)[1]['reference'])
if __name__=='__main__':unittest.main()
