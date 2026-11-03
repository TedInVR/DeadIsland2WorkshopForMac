"""User-confirmed full-condition references stay private and reject invalid values."""
import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import preset_storage as p
class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(Path(self.temp.name)/'Backups')});self.env.start()
        self.item={'id':'1'*32,'signature':'a'*64,'maximum':126.5}
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_record_reload_and_replacement_preserve_other_weapons(self):
        self.assertEqual(p.durability_references(),{})
        p.record_durability([self.item]);p.record_durability([dict(self.item,id='2'*32)])
        refs=p.durability_references();self.assertEqual(len(refs),2);self.assertEqual(refs['1'*32+':'+'a'*64]['maximum'],126.5)
        if os.name!='nt':self.assertEqual(p.durability_file().stat().st_mode&0o777,0o600)
    def test_invalid_references_leave_existing_file_unchanged(self):
        p.record_durability([self.item]);before=p.durability_file().read_bytes()
        for n in (None,True,-1,0,float('nan'),float('inf'),1_000_000_001):
            with self.assertRaises(ValueError):p.record_durability([dict(self.item,maximum=n)])
            self.assertEqual(p.durability_file().read_bytes(),before)
    def test_corrupt_reference_storage_is_not_overwritten(self):
        p.durability_file().parent.mkdir(parents=True,exist_ok=True);p.durability_file().write_text('{broken')
        with self.assertRaises(ValueError):p.record_durability([self.item])
        self.assertEqual(p.durability_file().read_text(),'{broken')
if __name__=='__main__':unittest.main()
