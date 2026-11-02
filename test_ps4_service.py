import json,os,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import garlic_service as g,save_browser as browser,ps4_backups as backups
from test_garlic_service import MemoryStore,KEY,sfo
A='0000000000000001';B='0000000000000002';SEALED=b'pfsSKKey'+b'\0'*88
class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.drive=self.root/'USB';self.drive.mkdir()
        self.env=patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(self.root/'Backups'),'DI2_WORKSHOP_SCAN_ROOTS':json.dumps([str(self.drive)])});self.env.start()
        self.manager=g.Manager(store=MemoryStore());self.manager.set_key(KEY)
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def pair(self,account,title,name,data):
        folder=self.drive/'PS4/SAVEDATA'/account/title;folder.mkdir(parents=True,exist_ok=True);(folder/name).write_bytes(data);(folder/(name+'.bin')).write_bytes(SEALED);return folder
    def wait(self):
        end=time.monotonic()+10
        while self.manager.running and time.monotonic()<end:time.sleep(.01)
        self.assertFalse(self.manager.running);self.assertEqual(self.manager.view()['status'],'done',self.manager.view())
    def test_all_game_profile_resign_stages_and_backs_up_before_replacement(self):
        source=self.pair(A,'CUSA99999','SaveA',b'source-a');self.pair(A,'CUSA99998','SaveB',b'source-b');destination=self.pair(B,'CUSA99999','SaveA',b'old-destination')
        entries=[e for e in browser.scan()['entries'] if e['account_id']==A]
        result=[g.make_zip({'PS4/SAVEDATA/'+B+'/'+e['title_id']+'/'+e['filename']:b'resigned-'+e['filename'].encode(),'PS4/SAVEDATA/'+B+'/'+e['title_id']+'/'+e['filename']+'.bin':SEALED}) for e in entries]
        with patch.object(g.Client,'submit',return_value='resign-job') as submit,patch.object(g.Client,'result',side_effect=result):
            self.manager.resign(entries,B);self.wait()
            self.assertEqual(submit.call_count,2);self.assertTrue(all(c.args[0]=='resign' and c.args[2]==B for c in submit.call_args_list))
        self.assertEqual((destination/'SaveA').read_bytes(),b'old-destination');self.assertEqual(self.manager.view()['result_count'],2);self.assertEqual(len(backups.list_backups()),3)
        (destination/'SaveA').write_bytes(b'changed-while-waiting')
        self.manager.install_results();self.assertEqual((source/'SaveA').read_bytes(),b'source-a');self.assertEqual((destination/'SaveA').read_bytes(),b'resigned-SaveA')
        old=[backups.retrieve(m['id'])[1] for m in backups.list_backups()]
        self.assertTrue(any(x.get('SaveA')==b'changed-while-waiting' for x in old))
    def test_other_game_decrypt_reencrypt_preserves_complete_metadata(self):
        self.pair(A,'CUSA99999','SaveA',b'encrypted-original');entry=browser.scan()['entries'][0]
        files={'save/sce_sys/param.sfo':sfo(A,'CUSA99999'),'save/data.bin':b'other-game-data','save/companion.dat':b'keep'}
        encrypted=g.make_zip({'SaveA':b'encrypted-new','SaveA.bin':SEALED})
        with patch.object(g.Client,'submit',return_value='job') as submit,patch.object(g.Client,'result',side_effect=[g.make_zip(files),encrypted]):
            self.manager.decrypt(entry);self.wait();self.assertFalse(self.manager.view()['editable']);self.assertTrue(self.manager.view()['has_session'])
            self.manager.encrypt();self.wait();upload=submit.call_args.args[1][0][1]
            self.assertEqual(g.unpack(upload),{n.removeprefix('save/'):v for n,v in files.items()})
        self.assertTrue((self.manager.folder/'PS4/SAVEDATA'/A/'CUSA99999/SaveA').exists())
if __name__=='__main__':unittest.main()
