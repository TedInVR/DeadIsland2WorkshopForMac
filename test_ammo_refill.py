"""Normal ammo restoration: one stack per type, missing types, scope and preservation."""
import os,unittest
from pathlib import Path
from types import SimpleNamespace
import character_editor as c
from save_core import Save,FormatError,fs,put,prop,props,string

def property_bytes(name,typ,payload,extra=''):
    return fs(name)+fs(typ)+put(len(payload))+put(0)+(fs(extra)+bytes(16) if typ=='StructProperty' else fs(extra) if typ=='ArrayProperty' else b'')+b'\0'+payload
def record(path,count,number):
    return b''.join([property_bytes('EntryID','StructProperty',number.to_bytes(16,'little'),'Guid'),property_bytes('Archetype','ObjectProperty',fs(path)+put(0)),property_bytes('Count','IntProperty',put(count)),property_bytes('UniqueId','StructProperty',bytes(16),'Guid'),fs('None')])
def array(records):
    inner=property_bytes('ArchetypeItems','StructProperty',b''.join(records),'InventoryItemArchetype')
    return property_bytes('ArchetypeItems','ArrayProperty',put(len(records))+inner,'StructProperty')
def read_array(raw,offset,key):
    outer,_=prop(raw,offset);inner,_=prop(raw,outer.data+4);p=inner.data;records=[]
    while p<inner.end:
        start=p;fields,p=props(raw,p,inner.end);by={x.name:x for x in fields}
        records.append(dict(start=start,end=p,fields=fields,by=by,path=string(raw,by['Archetype'].data)[0],count=int.from_bytes(by['Count'].payload(),'little')))
    return dict(key=key,section=0,outer=outer,inner=inner,records=records,kind='DIInventory',profile_id='synthetic-'+str(key))

class AmmoRefillTests(unittest.TestCase):
    def setUp(self):
        nails=next(a['path'] for a in c.AMMO if a['name']=='Nails')
        self.keep=record('/Game/Test/Unrelated',17,90)
        first=array([record(nails,9999,n+1) for n in range(7)]+[self.keep])
        second=array([record(c.AMMO[0]['path'],3,100)])
        raw=first+second
        self.s=SimpleNamespace(b=raw,resource_arrays=[read_array(raw,0,1),read_array(raw,len(first),2)],ammo=[],character_fields={})
    def test_refill_consolidates_duplicates_adds_missing_types_and_preserves_other_character(self):
        edits=c.plan(self.s,[],{}, {},[1]);self.assertEqual(len(edits[0]),1)
        start,end,raw=edits[0][0];a=read_array(raw,0,1)
        for item in c.AMMO:
            matching=[r for r in a['records'] if r['path']==item['path']]
            self.assertEqual(len(matching),1);self.assertEqual(matching[0]['count'],item['maximum'])
        unrelated=next(r for r in a['records'] if r['path']=='/Game/Test/Unrelated')
        self.assertEqual(raw[unrelated['start']:unrelated['end']],self.keep)
        ids=[r['by']['EntryID'].payload() for r in a['records']];self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(r['by']['UniqueId'].payload()==bytes(16) for r in a['records']))
        self.assertEqual(end,self.s.resource_arrays[0]['outer'].end)
    def test_rejects_unknown_duplicate_and_boolean_groups(self):
        for groups in ([9],[1,1],[True]):
            with self.assertRaises(FormatError):c.plan(self.s,[],{},{},groups)
    def test_all_characters_are_explicitly_scoped(self):
        edits=c.plan(self.s,[],{},{},[1,2]);self.assertEqual(len(edits[0]),2)
    def test_custom_above_normal_overrides_refill_and_keeps_one_stack(self):
        item=next(a for a in c.AMMO if a['name']=='Shotgun shells')
        request=dict(group=1,path=item['path'],count=211)
        edits=c.plan(self.s,[request],{},{},[1]);raw=edits[0][0][2];a=read_array(raw,0,1)
        match=[r for r in a['records'] if r['path']==item['path']]
        self.assertEqual(len(match),1);self.assertEqual(match[0]['count'],211)
        for other in c.AMMO:
            if other is not item:self.assertEqual(next(r for r in a['records'] if r['path']==other['path'])['count'],other['maximum'])
    def test_custom_ammo_accepts_zero_and_rejects_invalid_values(self):
        path=c.AMMO[0]['path']
        for n in (-1,True,1.5,10_000_000):
            with self.assertRaises(FormatError):c.plan(self.s,[dict(group=1,path=path,count=n)],{},{},[])
        edits=c.plan(self.s,[dict(group=1,path=path,count=0)],{},{},[])
        raw=edits[0][0][2];a=read_array(raw,0,1)
        self.assertEqual(next(r for r in a['records'] if r['path']==path)['count'],0)

@unittest.skipUnless(os.environ.get('DI2_TEST_SAVE'),'Requires private save fixture')
class PrivateAmmoTests(unittest.TestCase):
    def test_refill_roundtrip_preserves_weapons_and_other_characters(self):
        s=Save(Path(os.environ['DI2_TEST_SAVE']).read_bytes());groups=s.info()['ammo_groups']
        selected=groups[0]['key'];other=groups[-1]['key']
        other_array=next(a for a in s.resource_arrays if a['key']==other)
        target=next((a for a in s.ammo if any(r['by']['Count'].data==a['field'].data for r in other_array['records'])),None)
        edits={str(target['key']):11} if target else {}
        t=Save(s.rebuild({},ammo_changes=edits,ammo_refills=[selected]))
        c.verify(s,t,[],{},[selected])
        for before,after in zip(s.weapons,t.weapons):self.assertEqual(s.b[before.start:before.end],t.b[after.start:after.end])
        for a,b in zip(s.resource_arrays,t.resource_arrays):
            if a['key'] not in (selected,other):self.assertEqual(s.b[a['outer'].start:a['outer'].end],t.b[b['outer'].start:b['outer'].end])
        t=Save(s.rebuild({},ammo_refills=[g['key'] for g in groups]));c.verify(s,t,[],{},[g['key'] for g in groups])
        request=dict(group=selected,path=c.AMMO[0]['path'],count=211)
        t=Save(s.rebuild({},resource_changes=[request],ammo_refills=[selected]));c.verify(s,t,[request],{},[selected])

if __name__=='__main__':unittest.main()
