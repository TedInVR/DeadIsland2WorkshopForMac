import os,unittest
from pathlib import Path
from save_core import Save,FormatError,u32,fs,prop
from character_editor import XP
@unittest.skipUnless(os.environ.get('DI2_TEST_SAVE'),'Requires private DI2 fixture via DI2_TEST_SAVE')
class CharacterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s=Save(Path(os.environ['DI2_TEST_SAVE']).read_bytes())
    def test_all_regular_and_ngplus_levels_up_and_down(self):
        s=self.s
        for levels in ({p['id']:p['level_cap'] for p in s.profiles},{p['id']:1 for p in s.profiles},{p['id']:14 for p in s.profiles}):
            raw=s.rebuild({},character_levels=levels);t=Save(raw)
            for p in t.profiles:self.assertEqual(p['level'],levels[p['id']]);self.assertEqual(p['xp'],XP[levels[p['id']]-1])
            for old,new in zip(s.weapons,t.weapons):self.assertEqual(old.b[old.start:old.end],new.b[new.start:new.end])
            self.assertEqual(len(raw),len(s.b))
            summary=next(sec for sec in t.sections if sec['name']=='CharacterProfileAccount')
            for pid,level in levels.items():
                start=raw.index(fs(pid),summary['start'],summary['end']);q=raw.index(fs('KeyProgression'),start,summary['end'])+len(fs('KeyProgression'))
                self.assertEqual(u32(raw,q+8),level)
            import re
            for match in re.finditer(re.escape(fs('PlayerLevels')+fs('MapProperty')),raw):
                outer,_=prop(raw,match.start());inner,_=prop(raw,outer.data)
                for offset in range(inner.data+8,inner.end,20):
                    pid=''.join(raw[k:k+4][::-1].hex() for k in range(offset,offset+16,4)).upper()
                    if pid in levels:self.assertEqual(u32(raw,offset+16),levels[pid])

    def test_invalid_levels_and_cash_are_rejected(self):
        p=next(p for p in self.s.profiles if not p['ng']);g=self.s.info()['resource_groups'][0];cash=next(i for i in g['items'] if i['category']=='Money')
        for v in (0,31,True,2.5):
            with self.assertRaises(FormatError):self.s.rebuild({},character_levels={p['id']:v})
        for v in (-1,2000001,True):
            with self.assertRaises(FormatError):self.s.rebuild({},resource_changes=[dict(group=g['key'],path=cash['path'],count=v)])
    def test_fill_all_characters_preserves_weapons_recipes_and_other_bytes(self):
        s=self.s;requests=[dict(group=g['key'],path=i['path'],count=i['maximum']) for g in s.info()['resource_groups'] for i in g['items']]
        out=Save(s.rebuild({},resource_changes=requests))
        for g in out.info()['resource_groups']:
            for item in g['items']:self.assertEqual(item['count'],item['maximum'])
        for a,b in zip(s.weapons,out.weapons):self.assertEqual(a.b[a.start:a.end],b.b[b.start:b.end])
        for a,b in zip(s.resource_arrays,out.resource_arrays):
            known={i['path'] for i in s.info()['resource_groups'][0]['items']}
            old=[r for r in a['records'] if r['path']not in known];new=[r for r in b['records'] if r['path']not in known]
            self.assertEqual([s.b[r['start']:r['end']] for r in old],[out.b[r['start']:r['end']] for r in new])
    def test_missing_resource_is_added_without_duplicate_ids(self):
        from save_core import put
        s=self.s;group=s.info()['resource_groups'][0];item=next(i for i in group['items'] if i['category']=='Crafting materials')
        ar=next(a for a in s.resource_arrays if a['key']==group['key']);record=next(r for r in ar['records'] if r['path']==item['path'])
        payload=b''.join(s.b[r['start']:r['end']] for r in ar['records'] if r is not record)
        new=ar['outer'].replace(put(len(ar['records'])-1)+ar['inner'].replace(payload));sec=s.sections[ar['section']]
        body=s.b[sec['start']:ar['outer'].start]+new+s.b[ar['outer'].end:sec['end']]
        raw=s.b[:sec['sizepos']]+put(len(body))+body+s.b[sec['end']:];missing=Save(raw)
        out=Save(missing.rebuild({},resource_changes=[dict(group=group['key'],path=item['path'],count=99)]))
        newgroup=next(g for g in out.info()['resource_groups'] if g['key']==group['key']);self.assertEqual(next(i for i in newgroup['items'] if i['path']==item['path'])['count'],99)
        records=next(a for a in out.resource_arrays if a['key']==group['key'])['records'];ids=[r['by']['EntryID'].payload() for r in records];self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__':unittest.main()
