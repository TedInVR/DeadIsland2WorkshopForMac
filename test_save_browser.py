import json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import save_browser as b

A='0000000000000001';B='0000000000000002'
class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.drive=self.root/'USB';self.game=self.drive/'PS4'/'SAVEDATA'/A/'CUSA01014';self.game.mkdir(parents=True)
        self.p=patch.object(b,'names_file',return_value=self.root/'settings'/'profile-names.json');self.p.start()
    def tearDown(self):self.p.stop();self.temp.cleanup()
    def pair(self):
        (self.game/'DeadIsland2SaveGame').write_bytes(b'encrypted bytes');(self.game/'DeadIsland2SaveGame.bin').write_bytes(b'key bytes')
    def test_profiles_and_pairs_are_found_without_any_drive_writes(self):
        self.pair();before={p.relative_to(self.drive):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()}
        b.import_names({'profiles':{A:'Example_Player'}});found=b.scan([self.drive])['entries'];self.assertEqual(len(found),1);e=found[0]
        self.assertEqual(e['profile_name'],'Example_Player');self.assertEqual(e['account_id'],A);self.assertEqual(e['kind'],'encrypted');self.assertTrue(e['bin_path'].endswith('.bin'))
        self.assertEqual(b.find_save(e['key'],[self.drive]),e)
        self.assertEqual(before,{p.relative_to(self.drive):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()})
    def test_multiple_accounts_and_other_games(self):
        self.pair();other=self.drive/'PS4'/'SAVEDATA'/B/'CUSA01014';other.mkdir(parents=True);(other/'DeadIsland2SaveGame').write_bytes(b'pair missing key')
        wrong=self.drive/'PS4'/'SAVEDATA'/A/'CUSA99999';wrong.mkdir();(wrong/'DeadIsland2SaveGame').write_bytes(b'other game')
        found=b.scan([self.drive])['entries'];self.assertEqual(len(found),2);self.assertEqual({e['kind'] for e in found},{'encrypted','incomplete'})
    def test_decrypted_header_detection_and_unplugged_drive(self):
        file=self.game/'ue4savegame.ps4.sav';file.write_bytes(bytes.fromhex('3dca1200')+bytes(12)+b'Zstd\0'+b'example header only')
        (self.game/'random.sav').write_bytes(b'unrelated')
        e=b.scan([self.drive])['entries'][0];self.assertEqual(e['kind'],'decrypted')
        shutil.rmtree(self.drive)
        with self.assertRaises(b.BrowserError):b.find_save(e['key'],[self.drive])
    def test_names_merge_rename_clear_and_persist(self):
        b.import_names({A:'Alpha'});b.import_names({B:'Beta'});b.import_names({A:'Changed'})
        self.assertEqual(b.profile_names(),{A:'Changed',B:'Beta'});b.import_names({A:''});self.assertEqual(b.profile_names(),{B:'Beta'})
        self.assertEqual(json.loads(b.names_file().read_text())['profiles'],{B:'Beta'})
    def test_invalid_import_is_atomic_and_never_changes_existing_names(self):
        b.import_names({A:'Keep'})
        for value in ({'../bad':'Oops'},{A:'Good',B:'x'*65},['bad'],{A:22}):
            with self.assertRaises(b.BrowserError):b.import_names(value)
            self.assertEqual(b.profile_names(),{A:'Keep'})
    def test_links_and_invalid_ids_are_ignored(self):
        self.pair();bad=self.drive/'PS4'/'SAVEDATA'/'not-an-account';bad.mkdir();(bad/'CUSA01014').mkdir()
        outside=self.root/'elsewhere.sav';outside.write_bytes(bytes.fromhex('3dca1200')+bytes(12)+b'Zstd\0')
        try:(self.game/'linked.sav').symlink_to(outside)
        except OSError:pass
        self.assertEqual(len(b.scan([self.drive])['entries']),1)
        with self.assertRaises(b.BrowserError):b.find_save('../file',[self.drive])

if __name__=='__main__':unittest.main()
