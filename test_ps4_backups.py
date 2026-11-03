import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import ps4_backups as b
import save_browser as browser
A='0000000000000001';B='0000000000000002';TITLE='CUSA99999';NAME='OtherGameSave';SEALED=b'pfsSKKey'+b'\0'*88
class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.drive=self.root/'USB';self.game=self.drive/'PS4/SAVEDATA'/A/TITLE;self.game.mkdir(parents=True)
        self.env=patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(self.root/'Backups'),'DI2_WORKSHOP_SCAN_ROOTS':json.dumps([str(self.drive)])});self.env.start()
        (self.game/NAME).write_bytes(b'original');(self.game/(NAME+'.bin')).write_bytes(SEALED)
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def entry(self):return browser.scan()['entries'][0]
    def test_named_backup_keeps_structure_label_checksums_and_never_overwrites(self):
        e=self.entry();a=b.capture(e,'Before cheats 2 Nov');c=b.capture(e,'Before cheats 2 Nov');self.assertNotEqual(a['folder'],c['folder'])
        meta,files=b.retrieve(a['id']);self.assertEqual(files,{NAME:b'original',NAME+'.bin':SEALED});self.assertIn('Before cheats',a['folder']);self.assertEqual(meta['account_id'],A)
        self.assertEqual((self.game/NAME).read_bytes(),b'original')
        (Path(a['folder'])/a['files'][0]['file']).write_bytes(b'tampered')
        with self.assertRaises(b.BackupError):b.retrieve(a['id'])
    def test_replacement_backs_up_destination_and_restore_also_backs_up(self):
        files={NAME:b'new',NAME+'.bin':SEALED};result=b.install(self.drive,A,TITLE,NAME,files)
        self.assertIsNotNone(result['backup']);meta,old=b.retrieve(result['backup']['id']);self.assertEqual(old[NAME],b'original')
        b.install(self.drive,A,TITLE,NAME,old);self.assertEqual((self.game/NAME).read_bytes(),b'original');self.assertEqual(len(b.list_backups()),2)
    def test_backup_failure_prevents_any_destination_write(self):
        with patch.object(b,'capture',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):b.install(self.drive,A,TITLE,NAME,{NAME:b'new',NAME+'.bin':SEALED})
        self.assertEqual((self.game/NAME).read_bytes(),b'original')
    def test_second_write_failure_rolls_back_first_and_retains_backup(self):
        real=os.replace;counter=0
        def replace(source,target):
            nonlocal counter
            counter+=1
            if counter==2:raise OSError('USB write failed')
            return real(source,target)
        with patch.object(b.os,'replace',side_effect=replace):
            with self.assertRaises(b.BackupError):b.install(self.drive,A,TITLE,NAME,{NAME:b'new',NAME+'.bin':SEALED})
        self.assertEqual((self.game/NAME).read_bytes(),b'original');self.assertEqual((self.game/(NAME+'.bin')).read_bytes(),SEALED);self.assertEqual(len(b.list_backups()),1)
    def test_bad_identity_and_incomplete_pairs_refused(self):
        with self.assertRaises(b.BackupError):b.install(self.drive,'../bad',TITLE,NAME,{NAME:b'new',NAME+'.bin':SEALED})
        with self.assertRaises(b.BackupError):b.install(self.drive,A,TITLE,NAME,{NAME:b'new'})
    def test_other_game_and_bin_suffix_pair_are_discovered(self):
        self.assertEqual(self.entry()['title_id'],TITLE);self.assertFalse(self.entry()['is_di2'])
        (self.game/'slot.bin').write_bytes(b'container');(self.game/'slot.bin.bin').write_bytes(SEALED)
        self.assertEqual(len(browser.scan()['entries']),2)
    def test_installed_file_verification_failure_rolls_back(self):
        real=b.read_file
        def read(path):
            value=real(path)
            return b'bad readback' if Path(path)==self.game/NAME and value==b'new' else value
        with patch.object(b,'read_file',side_effect=read):
            with self.assertRaises(b.BackupError):b.install(self.drive,A,TITLE,NAME,{NAME:b'new',NAME+'.bin':SEALED})
        self.assertEqual((self.game/NAME).read_bytes(),b'original')
        self.assertEqual((self.game/(NAME+'.bin')).read_bytes(),SEALED)

if __name__=='__main__':unittest.main()
