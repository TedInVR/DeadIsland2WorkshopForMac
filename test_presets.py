import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import preset_storage as store
A='/Game/DI2/Upgrades/Example.Example';B='/Game/DI2/Upgrades/Other.Other'
class PresetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.target=patch.object(store,'file',return_value=self.root/'PerkPresets.json');self.target.start()
    def tearDown(self):self.target.stop();self.temp.cleanup()
    def test_save_reload_replace_and_delete_preserve_named_sets(self):
        first=store.save({'name':'Acid favourite','perks':[A,B]});identity=first['saved_id']
        self.assertEqual(store.list_presets()[0]['perks'],[A,B])
        with self.assertRaises(store.PresetError):store.save({'name':'ACID FAVOURITE','perks':[B]})
        store.save({'name':'Acid favourite','perks':[B],'replace':True})
        self.assertEqual(store.list_presets(),[{'id':identity,'name':'Acid favourite','perks':[B]}])
        store.save({'name':'No upgrades','perks':[]})
        store.delete({'id':identity});self.assertEqual(store.list_presets()[0]['perks'],[])
    def test_write_failure_preserves_existing_file(self):
        store.save({'name':'Keep','perks':[A]});original=store.file().read_bytes()
        with patch.object(store.os,'replace',side_effect=PermissionError):
            with self.assertRaises(store.PresetError):store.save({'name':'New','perks':[B]})
        self.assertEqual(store.file().read_bytes(),original);self.assertFalse(list(self.root.glob('*.tmp')))
    def test_invalid_input_and_corrupt_storage_are_not_overwritten(self):
        for value in ({'name':'','perks':[]},{'name':'Bad','perks':[A,A]},{'name':'Bad','perks':['invalid']},{'name':'Bad','perks':None}):
            with self.assertRaises(store.PresetError):store.save(value)
        store.file().write_text('not JSON')
        with self.assertRaises(store.PresetError):store.save({'name':'New','perks':[A]})
        self.assertEqual(store.file().read_text(),'not JSON')
    def test_many_presets_and_special_text_names(self):
        for name in ['<script>not markup</script>','Melee','Firearms']:
            store.save({'name':name,'perks':[A]})
        self.assertEqual(len(store.list_presets()),3)
        with self.assertRaises(store.PresetError):store.delete({'id':'not-an-id'})
if __name__=='__main__':unittest.main()
