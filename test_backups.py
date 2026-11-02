import hashlib,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import backup_storage as b
import server

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'Backups';self.p=patch.object(b,'folder',return_value=self.root);self.p.start()
    def tearDown(self):self.p.stop();self.temp.cleanup()
    def test_repeated_names_accumulate_complete_copies(self):
        paths=[]
        for raw in (b'first original',b'next original',b'edited copy'):
            info=b.snapshot(raw,'opened','../save.sav');p=Path(info['path']);paths.append(p)
            self.assertEqual(p.parent,self.root);self.assertEqual(p.read_bytes(),raw);self.assertEqual(info['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(set(paths)),3);self.assertEqual(paths[0].read_bytes(),b'first original')
    def test_collision_never_overwrites_existing_backup(self):
        with patch.object(b.uuid,'uuid4',return_value=SimpleNamespace(hex='same')),patch.object(b,'datetime') as clock:
            clock.now.return_value.strftime.return_value='fixed-time'
            info=b.snapshot(b'keep forever','opened','same.sav')
            with self.assertRaises(b.BackupError):b.snapshot(b'overwrite attempt','opened','same.sav')
        self.assertEqual(Path(info['path']).read_bytes(),b'keep forever');self.assertEqual(len(list(self.root.iterdir())),1)
    def test_concurrent_snapshots_remain_distinct(self):
        with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda i:b.snapshot(bytes([i])*100,'exported','same.sav'),range(16)))
        self.assertEqual(len({r['path'] for r in results}),16)
        for i,r in enumerate(results):self.assertEqual(Path(r['path']).read_bytes(),bytes([i])*100)
    def test_write_failure_cleans_only_its_new_file(self):
        old=b.snapshot(b'keep','opened')
        with patch.object(b.os,'fsync',side_effect=OSError('disk full')):
            with self.assertRaises(b.BackupError):b.snapshot(b'failed export','exported')
        self.assertEqual([p.name for p in self.root.iterdir()],[Path(old['path']).name]);self.assertEqual(Path(old['path']).read_bytes(),b'keep')
    def test_backups_are_protected_from_manual_export(self):
        self.assertTrue(b.protects(self.root/'any.sav'));self.assertTrue(b.protects(self.root));self.assertFalse(b.protects(self.root.parent/'edited.sav'))
    def test_open_failure_preserves_previous_session(self):
        app=server.App();previous=object();app.save=previous;app.output=b'previous validated output'
        save=SimpleNamespace(rebuild=lambda _:b'raw',info=lambda:{})
        with patch.object(server,'Save',return_value=save),patch.object(b,'snapshot',side_effect=b.BackupError('full')):
            with self.assertRaises(b.BackupError):app.open_save(b'raw','test.sav')
        self.assertIs(app.save,previous);self.assertEqual(app.output,b'previous validated output')
    def test_shared_open_handler_backs_up_before_accepting(self):
        app=server.App();save=SimpleNamespace(rebuild=lambda _:b'raw',info=lambda:{'weapons':[]})
        with patch.object(server,'Save',return_value=save):info=app.open_save(b'raw','test.sav')
        self.assertEqual(Path(info['backup']['path']).read_bytes(),b'raw');self.assertIs(app.save,save)

if __name__=='__main__':unittest.main()
