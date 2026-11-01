import unittest,sys,hashlib
from pathlib import Path
from save_core import Save,FormatError

class SaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s=Save(Path(sys.argv[1]).read_bytes())
    def test_unchanged(self):self.assertEqual(self.s.rebuild({}),self.s.b)
    def test_all_levels(self):
        edits={str(w.idx):{'level': 1+(w.idx%50)} for w in self.s.weapons if w.info()['editable']}
        out=Save(self.s.rebuild(edits))
        # Fixed-width changes must affect only the actual level integers.
        allowed=set()
        for w in self.s.weapons:
            if str(w.idx) in edits:
                p=next(p for p in w.pgprops if p.name=='RequiredLevel');allowed.update(range(p.data,p.end))
        diffs={i for i,(a,b) in enumerate(zip(self.s.b,out.b)) if a!=b}
        self.assertTrue(diffs<=allowed);self.assertEqual(len(out.b),len(self.s.b))
    def test_rarity_and_perks(self):
        targets=[w for w in self.s.weapons if w.info()['editable']][:6]
        edits={str(w.idx):{'rarity':r,'perks':w.runtime.paths[:3], 'level':7} for w,r in zip(targets,['Common','Uncommon','Rare','Superior','Legendary','Common'])}
        out=Save(self.s.rebuild(edits))
        # Every unedited weapon stays byte-for-byte identical after variable-size edits.
        for old,new in zip(self.s.weapons,out.weapons):
            if str(old.idx) not in edits:self.assertEqual(old.b[old.start:old.end],new.b[new.start:new.end])
        # Every untouched top-level section stays identical.
        changed_sections={a['section'] for a in self.s.arrays if any(str(w.idx) in edits for w in a['weapons'])}
        for i,(a,b) in enumerate(zip(self.s.sections,out.sections)):
            if i not in changed_sections:self.assertEqual(self.s.b[a['start']:a['end']],out.b[b['start']:b['end']])
    def test_add_remove_perks(self):
        w=next(w for w in self.s.weapons if w.info()['editable']);catalog=[v['path'] for v in self.s.info()['catalog']]
        for paths in ([],catalog[:1],catalog[:60],catalog):
            out=self.s.rebuild({str(w.idx):{'perks':paths}});self.assertEqual(Save(out).weapons[w.idx].runtime.paths,paths)
    def test_reject_invalid(self):
        w=next(w for w in self.s.weapons if w.info()['editable'])
        for c in ({'level':-1},{'level':True},{'rarity':'Fake'},{'perks':['bad']},{'perks':[w.runtime.paths[0]]*2}):
            with self.assertRaises((FormatError,ValueError)):self.s.rebuild({str(w.idx):c})
    def test_truncated(self):
        for b in (self.s.b[:100],self.s.b[:-1],b'not a save'):
            with self.assertRaises((FormatError,ValueError)):Save(b)

    def test_names_and_modes(self):
        self.assertEqual([(p['name'],p['ng']) for p in self.s.profiles],[('Ryan',False),('Ryan',True),('Jacob',False),('Carla',False),('Dani',False),('Amy',False),('Bruno',False),('Jacob',True),('Carla',True),('Bruno',True)])
        self.assertEqual([p['name'] for p in self.s.profiles if p['active']],['Ryan'])
    def test_catalog_creation(self):
        from save_core import props,Weapon
        ids=set();unique_ids=set()
        for item in self.s.info()['weapon_catalog']:
            request=dict(path=item['path'],level=30,rarity='Legendary',perks=[])
            raw=self.s.create_record(request);ps,end=props(raw,0);w=Weapon(raw,0,end,ps,'test',0)
            self.assertEqual(w.path,item['path']);self.assertEqual(w.level,30);self.assertEqual(w.rarity,'Legendary');self.assertEqual(w.runtime.paths,[])
            self.assertNotIn(w.id,ids);ids.add(w.id)
            uid=w.by['UniqueId'].payload();self.assertNotIn(uid,unique_ids);unique_ids.add(uid)
    def test_delete_and_create_in_full_locker(self):
        ar=next(a for a in self.s.arrays if a['kind']=='StashNewGamePlus')
        original=ar['weapons'][0];path=self.s.info()['weapon_catalog'][0]['path']
        request=dict(destination=ar['key'],path=path,level=35,rarity='Rare',perks=[])
        with self.assertRaises(FormatError):self.s.rebuild({},[request])
        out=Save(self.s.rebuild({},[request],[original.idx]))
        target=out.arrays[ar['key']];self.assertEqual(len(target['weapons']),len(ar['weapons']))
        self.assertEqual(target['weapons'][-1].path,path)
        self.assertNotIn(original.id,[w.id for w in target['weapons']])
        for old,new in zip(ar['weapons'][1:],target['weapons'][:-1]):self.assertEqual(old.b[old.start:old.end],new.b[new.start:new.end])
    def test_replace_in_place(self):
        for ar in [next(a for a in self.s.arrays if a['kind']=='StashNewGamePlus'),next(a for a in self.s.arrays if a['kind']=='DIInventory')]:
            w=next(w for w in ar['weapons'] if w.info()['editable'])
            item=next(c for c in self.s.info()['weapon_catalog'] if ('MeleeWeaponArchetype' in c['path'])!=('MeleeWeaponArchetype' in w.path))
            change=dict(path=item['path'],level=27,rarity='Superior',perks=[])
            out=Save(self.s.rebuild({str(w.idx):change}));new=out.weapons[w.idx]
            self.assertEqual(len(out.weapons),len(self.s.weapons));self.assertEqual(new.id,w.id);self.assertEqual(new.by['UniqueId'].payload(),w.by['UniqueId'].payload());self.assertEqual(new.path,item['path'])
            for old,n in zip(self.s.weapons,out.weapons):
                if old.idx!=w.idx:self.assertEqual(old.b[old.start:old.end],n.b[n.start:n.end])
    def test_delete_carried_shortcut(self):
        from save_core import fs,prop,props,u32
        import re
        ar=next(a for a in self.s.arrays if a['kind']=='DIInventory')
        w=next(w for w in ar['weapons'] if w.info()['editable']);uid=w.by['UniqueId'].payload()
        out=Save(self.s.rebuild({},[],[w.idx]));sec=out.sections[ar['section']]
        for m in re.finditer(re.escape(fs('AssignedItems')+fs('ArrayProperty')),out.b[sec['start']:sec['end']]):
            outer,_=prop(out.b,sec['start']+m.start());inner,_=prop(out.b,outer.data+4)
            if not inner or inner.extra!='AssignedItem':continue
            pos=inner.data
            for _ in range(u32(out.b,outer.data)):
                fields,pos=props(out.b,pos,inner.end);pd={p.name:p for p in fields}
                self.assertNotEqual(pd['PersistentId'].payload(),uid)
        # His NG+ counterpart (with shared historical IDs) stays unchanged.
        si=next(i for i,s in enumerate(self.s.sections) if s.get('profile',{}).get('ng') and s['profile']['name']=='Ryan')
        a=self.s.sections[si];b=out.sections[si];self.assertEqual(self.s.b[a['start']:a['end']],out.b[b['start']:b['end']])

if __name__=='__main__':
    arg=sys.argv[1];suite=unittest.defaultTestLoader.loadTestsFromTestCase(SaveTests);r=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not r.wasSuccessful())
