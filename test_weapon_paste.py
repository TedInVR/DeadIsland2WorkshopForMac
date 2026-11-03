"""Optional local integration against private fixtures; no save data is bundled."""
import os,unittest,zipfile
from pathlib import Path
from save_core import Save,FormatError,props,Weapon

@unittest.skipUnless(os.environ.get('DI2_TEST_SAVE'),'Set a private fixture path locally')
class WeaponPasteTests(unittest.TestCase):
    def variants(self):
        yield Save(Path(os.environ['DI2_TEST_SAVE']).read_bytes())
        if os.environ.get('DI2_TEST_COMPRESSED_ZIP'):
            yield Save(zipfile.ZipFile(os.environ['DI2_TEST_COMPRESSED_ZIP']).read('ue4savegame.ps4.sav'))
    def test_full_state_paste_keeps_destination_ids_and_all_other_records(self):
        for s in self.variants():
            editable=[w for w in s.weapons if w.info()['editable']]
            source=next(w for w in editable if 'MeleeWeaponArchetype' in w.path)
            target=next(w for w in editable if 'RangedWeaponArchetype' in w.path)
            override={'path':source.path,'level':12,'rarity':'Legendary','perks':source.runtime.paths[:3],'durability':9999}
            expected=source.rebuild(override);fields,end=props(expected,0)
            out=Save(s.rebuild({str(target.idx):dict(copy_source=source.idx,**override)}));pasted=out.weapons[target.idx]
            self.assertEqual(len(s.weapons),len(out.weapons))
            self.assertEqual(b''.join(p.raw() for p in fields if p.name not in ('EntryID','UniqueId')),b''.join(p.raw() for p in pasted.ps if p.name not in ('EntryID','UniqueId')))
            for name in ('EntryID','UniqueId'):self.assertEqual(pasted.by[name].payload(),target.by[name].payload())
            for before,after in zip(s.weapons,out.weapons):
                if before.idx!=target.idx:self.assertEqual(before.b[before.start:before.end],after.b[after.start:after.end])
    def test_multiple_destinations_and_invalid_sources(self):
        s=next(self.variants());items=[w for w in s.weapons if w.info()['editable']];source=items[0];targets=items[1:3]
        out=Save(s.rebuild({str(w.idx):{'copy_source':source.idx} for w in targets}))
        for w in targets:self.assertEqual(out.weapons[w.idx].path,source.path);self.assertEqual(out.weapons[w.idx].id,w.id)
        for key in (True,-1,len(s.weapons),1.5):
            with self.assertRaises(FormatError):s.rebuild({str(targets[0].idx):{'copy_source':key}})

if __name__=='__main__':unittest.main()
