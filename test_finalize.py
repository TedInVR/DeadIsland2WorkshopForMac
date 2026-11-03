"""USB finalization workflow tests. Service and save validation are isolated with fakes;
private-fixture integration is exercised separately. No network requests are made.
"""
import json,os,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import garlic_service as g,save_browser as browser,ps4_backups as backups
from test_garlic_service import MemoryStore,KEY,sfo
A='0000000000000001';TITLE='CUSA01014';NAME='DeadIsland2SaveGame';SEALED=b'pfsSKKey'+bytes(88)
class ValidatedSave:
    def __init__(self,raw):self.raw=raw
    def rebuild(self,changes):return self.raw

class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.drive=self.root/'USB';self.game=self.drive/'PS4/SAVEDATA'/A/TITLE;self.game.mkdir(parents=True)
        self.env=patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(self.root/'Backups'),'DI2_WORKSHOP_SCAN_ROOTS':json.dumps([str(self.drive)])});self.env.start()
        (self.game/NAME).write_bytes(b'original encrypted');(self.game/(NAME+'.bin')).write_bytes(SEALED)
        self.session_root=self.root/'ServiceSessions'/'20990101-example';self.session_root.mkdir(parents=True)
        self.files={'sce_sys/param.sfo':sfo(A,TITLE),'ue4savegame.ps4.sav':b'original game data','companion.dat':b'keep exactly'}
        (self.session_root/'Decrypted-Result.zip').write_bytes(g.make_zip(self.files))
        (self.session_root/'Original-Encrypted-Pair.zip').write_bytes(g.make_zip({'PS4/SAVEDATA/'+A+'/'+TITLE+'/'+NAME:b'original encrypted','PS4/SAVEDATA/'+A+'/'+TITLE+'/'+NAME+'.bin':SEALED}))
        (self.session_root/'decrypt-job.json').write_text(json.dumps({'account_id':A,'title_id':TITLE}))
        self.manager=g.Manager(store=MemoryStore());self.manager.set_key(KEY);self.manager.session={'files':dict(self.files),'name':'ue4savegame.ps4.sav','root':self.session_root};self.manager.context=browser.scan()['entries'][0]
        self.key=self.manager.context['drive_key'];self.output=g.make_zip({NAME:b'new encrypted',NAME+'.bin':SEALED})
        self.parser=patch('save_core.Save',ValidatedSave);self.parser.start()
        # Network verification has its own protocol tests. These tests isolate
        # USB backup/install behavior, including failures after the result arrives.
        self.verifier=patch.object(g,'verified_encrypt',side_effect=self.encrypt_result);self.verifier.start()
    def encrypt_result(self,client,files,account,title,name,folder,message):
        job=client.submit('encrypt',[('decrypted_save.zip',g.make_zip(files))],account)
        raw=client.result(job,message);g.write_new(folder/'Encrypted-Result.zip',raw)
        return g.encrypted_files(g.unpack(raw),account,title,name),job
    def tearDown(self):self.verifier.stop();self.parser.stop();self.env.stop();self.temp.cleanup()
    def wait(self):
        until=time.monotonic()+10
        while self.manager.running and time.monotonic()<until:time.sleep(.01)
        self.assertFalse(self.manager.running);return self.manager.view()
    def test_complete_finalization_backs_up_latest_destination_preserves_companions_and_resumes(self):
        self.assertEqual(self.manager.finalize_info()['preferred_drive'],self.key)
        def result(*args):
            (self.game/NAME).write_bytes(b'changed while job ran');return self.output
        with patch.object(g.Client,'submit',return_value='job') as submit,patch.object(g.Client,'result',side_effect=result):
            self.manager.encrypt(b'edited game data',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'done',state);self.assertTrue(state['installed']);self.assertEqual(state['operation'],'finalize')
        self.assertEqual((self.game/NAME).read_bytes(),b'new encrypted');self.assertEqual((self.game/(NAME+'.bin')).read_bytes(),SEALED)
        archived=[backups.retrieve(meta['id'])[1][NAME] for meta in backups.list_backups()]
        self.assertIn(b'original encrypted',archived);self.assertIn(b'changed while job ran',archived)
        uploaded=g.unpack(submit.call_args.args[1][0][1]);self.assertEqual(uploaded['companion.dat'],self.files['companion.dat']);self.assertEqual(uploaded['sce_sys/param.sfo'],self.files['sce_sys/param.sfo']);self.assertEqual(uploaded['ue4savegame.ps4.sav'],b'edited game data')
        self.assertEqual(g.unpack((self.session_root/'Decrypted-Result.zip').read_bytes()),self.files)
        resumed=g.Manager(store=MemoryStore());self.assertTrue(resumed.resume()['editable']);self.assertEqual(resumed.session['files']['ue4savegame.ps4.sav'],b'edited game data');self.assertEqual(resumed.finalize_info()['preferred_drive'],self.key)
    def test_missing_drive_rejects_before_submission(self):
        with patch.object(g.Client,'submit') as submit:
            with self.assertRaises(g.ServiceError):self.manager.encrypt(b'edited',finalize_drive_key='f'*32)
            submit.assert_not_called()
    def test_wrong_account_verification_blocks_usb_installation(self):
        self.verifier.stop()
        checked=dict(self.files);checked['ue4savegame.ps4.sav']=b'edited';checked['sce_sys/param.sfo']=sfo('1111111111111111',TITLE)
        with patch.object(g.Client,'submit',side_effect=['enc','dec']),patch.object(g.Client,'result',side_effect=[self.output,g.make_zip(checked)]):
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'error');self.assertNotIn('installed',state)
        self.assertEqual((self.game/NAME).read_bytes(),b'original encrypted')
        self.assertFalse((self.manager.folder/'Ready-For-USB.zip').exists())
    def test_resume_recovers_saved_edits_and_skips_later_wrong_account_diagnostic(self):
        edited=dict(self.files);edited['ue4savegame.ps4.sav']=b'previously edited'
        target=self.session_root/'Encrypted-old';target.mkdir();(target/'Edited-Decrypted-Package.zip').write_bytes(g.make_zip(edited))
        bad=self.session_root.parent/'20990102-diagnostic';bad.mkdir()
        (bad/'decrypt-job.json').write_text(json.dumps({'account_id':A,'title_id':TITLE}))
        wrong=dict(self.files);wrong['sce_sys/param.sfo']=sfo('1111111111111111',TITLE)
        (bad/'Decrypted-Result.zip').write_bytes(g.make_zip(wrong));(bad/'Original-Encrypted-Pair.zip').write_bytes(b'invalid')
        resumed=g.Manager(store=MemoryStore());state=resumed.resume()
        self.assertEqual(resumed.session['files']['ue4savegame.ps4.sav'],b'previously edited')
        self.assertIn('recovered',state['message'])
    def test_backup_failure_stops_before_upload(self):
        with patch.object(backups,'destination_backup',side_effect=backups.BackupError('Backup disk full')),patch.object(g.Client,'submit') as submit:
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait();submit.assert_not_called()
        self.assertEqual(state['status'],'error');self.assertEqual((self.game/NAME).read_bytes(),b'original encrypted')
    def test_failure_of_immediate_backup_retains_result_without_overwriting(self):
        real=backups.destination_backup;calls=0
        def backup(*args):
            nonlocal calls
            calls+=1
            if calls==2:raise backups.BackupError('Immediate backup failed')
            return real(*args)
        with patch.object(backups,'destination_backup',side_effect=backup),patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',return_value=self.output):
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'error');self.assertNotIn('installed',state);self.assertEqual((self.game/NAME).read_bytes(),b'original encrypted');self.assertTrue((self.manager.folder/'Ready-For-USB.zip').exists())
    def test_disconnected_usb_retains_reencrypted_result_and_originals(self):
        gone=self.root/'Disconnected'
        def result(*args):self.drive.rename(gone);return self.output
        with patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',side_effect=result):
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'error');self.assertNotIn('installed',state);self.assertEqual((gone/'PS4/SAVEDATA'/A/TITLE/NAME).read_bytes(),b'original encrypted');self.assertTrue((self.manager.folder/'Encrypted-Result.zip').exists())
    def test_second_write_failure_rolls_back_and_never_reports_completion(self):
        real=os.replace;calls=0
        def replace(source,target):
            nonlocal calls
            if Path(target).parent==self.game:
                calls+=1
                if calls==2:raise OSError('USB interrupted')
            return real(source,target)
        with patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',return_value=self.output),patch.object(backups.os,'replace',side_effect=replace):
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'error');self.assertNotIn('installed',state);self.assertEqual((self.game/NAME).read_bytes(),b'original encrypted');self.assertEqual((self.game/(NAME+'.bin')).read_bytes(),SEALED);self.assertEqual(self.manager.session['files'],self.files)
    def test_wrong_account_output_never_replaces_usb(self):
        wrong=g.make_zip({'PS4/SAVEDATA/0000000000000002/'+TITLE+'/'+NAME:b'wrong','PS4/SAVEDATA/0000000000000002/'+TITLE+'/'+NAME+'.bin':SEALED})
        with patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',return_value=wrong):
            self.manager.encrypt(b'edited',finalize_drive_key=self.key);state=self.wait()
        self.assertEqual(state['status'],'error');self.assertEqual((self.game/NAME).read_bytes(),b'original encrypted')

if __name__=='__main__':unittest.main()
