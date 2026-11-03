"""API wire protocol, archive boundaries and an optional real-save local round trip.
All network activity is mocked. No key or personal save is shipped with the tests.
"""
import io,json,os,stat,struct,tempfile,time,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import garlic_service as g

KEY='test_worker_key_00000000000000000000'
def sfo(account='0000000000000001',title='CUSA01014'):
    keys=b'TITLE_ID\0ACCOUNT_ID\0';data=title.encode()+b'\0'+int(account,16).to_bytes(8,'little')
    header=struct.pack('<4sIIII',b'\0PSF',0x101,52,52+len(keys),2)
    entries=struct.pack('<HHIII',0,0x204,len(title)+1,len(title)+1,0)+struct.pack('<HHIII',9,4,8,8,len(title)+1)
    return header+entries+keys+data
class MemoryStore:
    def __init__(self):self.value=None
    def load(self):return self.value
    def save(self,value):self.value=value
    def delete(self):self.value=None
class Response(io.BytesIO):pass
class WireTests(unittest.TestCase):
    def test_connection_is_read_only_and_credential_not_in_url_or_body(self):
        c=g.Client(KEY)
        with patch.object(c.opener,'open',return_value=Response(b'[]')) as send:
            self.assertIn('No save files',c.test()['message'])
            req=send.call_args.args[0]
            self.assertEqual(req.full_url,g.BASE+'/jobs');self.assertIsNone(req.data)
            self.assertEqual(req.get_header('X-worker-key'),KEY)
            self.assertNotIn(KEY,req.full_url)
    def test_decrypt_multipart_requests_metadata_and_matching_filenames(self):
        c=g.Client(KEY)
        with patch.object(c.opener,'open',return_value=Response(b'{"job_id":"test-job_1"}')) as send:
            self.assertEqual(c.submit('decrypt',[('DeadIsland2SaveGame',b'one'),('DeadIsland2SaveGame.bin',b'two')]),'test-job_1')
            body=send.call_args.args[0].data
            self.assertIn(b'name="include_sce_sys"\r\n\r\ntrue',body)
            self.assertIn(b'filename="DeadIsland2SaveGame.bin"',body);self.assertNotIn(KEY.encode(),body)
    def test_encrypt_sends_same_account_and_complete_package(self):
        c=g.Client(KEY)
        with patch.object(c,'call',return_value={'job_id':'job'}) as send:
            c.submit('encrypt',[('decrypted_save.zip',b'zip')],'0000000000000001')
            body=send.call_args.args[1]
            self.assertIn(b'name="account_id"\r\n\r\n0000000000000001',body)
            self.assertIn(b'filename="decrypted_save.zip"',body)
    def test_rejects_endpoint_injection_and_redirects(self):
        with self.assertRaises(g.ServiceError):g.Client(KEY).call('/jobs/../../evil')
        with self.assertRaises(g.ServiceError):g.NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_error_response_cannot_echo_key(self):
        from urllib.error import HTTPError
        c=g.Client(KEY)
        with patch.object(c.opener,'open',side_effect=HTTPError(g.BASE+'/jobs',500,'oops',{},Response(KEY.encode()))):
            with self.assertRaises(g.ServiceError) as error:c.test()
            self.assertNotIn(KEY,str(error.exception))
    def test_job_polling_and_download_do_not_resubmit(self):
        c=g.Client(KEY);progress=[]
        with patch.object(c,'call',side_effect=[{'status':'queued'},{'status':'running'},{'status':'done'},b'zip']) as call,patch.object(g.time,'sleep'):
            self.assertEqual(c.result('job',progress.append),b'zip')
            self.assertEqual(len(progress),2);self.assertEqual(call.call_args.args[0],'/jobs/job/result')
    def test_busy_and_missing_key_prevent_operations(self):
        m=g.Manager(store=MemoryStore())
        with self.assertRaises(g.ServiceError):m.test()
        m.set_key(KEY);m.running=True
        with self.assertRaises(g.ServiceError):m.test()
        with self.assertRaises(g.ServiceError):m.set_key('')

class ArchiveTests(unittest.TestCase):
    def test_matching_pair_and_wrong_keys(self):
        pair=Path(__file__).parent.parent/'upload'/'DeadIsland2SaveGame.bin'
        g.validate_pair(b'encrypted',b'pfsSKKey'+b'\0'*88)
        for key in (b'',b'pfsSKKey',b'wrongkey'+b'\0'*88):
            with self.assertRaises(g.ServiceError):g.validate_pair(b'enc',key)
        if pair.exists():g.validate_pair(pair.with_suffix('').read_bytes(),pair.read_bytes())
    def test_traversal_duplicate_symlink_and_size_rejected(self):
        for name in ('../escape','/absolute','C:/bad','folder\\escape'):
            raw=g.make_zip({name.replace('\\','/'):b'bad'})
            if '\\' in name:raw=raw.replace(name.replace('\\','/').encode(),name.encode())
            with self.assertRaises(g.ServiceError):g.unpack(raw)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            e=zipfile.ZipInfo('link');e.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(e,'/tmp/bad')
        with self.assertRaises(g.ServiceError):g.unpack(out.getvalue())
        with self.assertRaises(g.ServiceError):g.unpack(g.make_zip({'A':b'1','a':b'2'}))
        with patch.object(g,'LIMIT',10):
            with self.assertRaises(g.ServiceError):g.unpack(g.make_zip({'too-big':b'x'*100}))
    def test_decrypted_folder_metadata_and_companion_files_retained(self):
        files={'wrapper/sce_sys/param.sfo':sfo(),'wrapper/ue4savegame.ps4.sav':bytes.fromhex('3dca1200')+b'payload','wrapper/companion.dat':b'keep'}
        result,name=g.decrypted_files(g.unpack(g.make_zip(files)))
        self.assertEqual(name,'ue4savegame.ps4.sav');self.assertEqual(result['companion.dat'],b'keep');self.assertIn('sce_sys/param.sfo',result)
        with self.assertRaises(g.ServiceError):g.decrypted_files({'ue4savegame.ps4.sav':b'abc'})
    def test_account_and_game_metadata_mismatch_is_rejected(self):
        files={'sce_sys/param.sfo':sfo()}
        g.validate_identity(files,'0000000000000001','CUSA01014')
        for account,title in [('0000000000000002','CUSA01014'),('0000000000000001','CUSA27043')]:
            with self.assertRaises(g.ServiceError):g.validate_identity(files,account,title)
        with self.assertRaises(g.ServiceError):g.validate_identity({'sce_sys/param.sfo':b'\0PSFbad'},'0000000000000001','CUSA01014')
    def test_encrypted_output_is_separate_ps4_pair_for_expected_account(self):
        files={'DeadIsland2SaveGame':b'encrypted','DeadIsland2SaveGame.bin':b'pfsSKKey'+b'\0'*88}
        out=g.encrypted_files(files,'0000000000000001','CUSA01014')
        self.assertEqual(len(out),2);self.assertTrue(all(n.startswith('PS4/SAVEDATA/0000000000000001/CUSA01014/') for n in out))
        wrong={'PS4/SAVEDATA/0000000000000002/CUSA01014/'+n:v for n,v in files.items()}
        with self.assertRaises(g.ServiceError):g.encrypted_files(wrong,'0000000000000001','CUSA01014')

class FailureRetentionTests(unittest.TestCase):
    def test_unsupported_game_data_preserves_result_zip_and_originals(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(Path(tmp)/'Backups')}):
            root=Path(tmp);a=root/'DeadIsland2SaveGame';b=root/'DeadIsland2SaveGame.bin'
            a.write_bytes(b'original');b.write_bytes(b'pfsSKKey'+b'\0'*88)
            returned=g.make_zip({'sce_sys/param.sfo':sfo(),'ue4savegame.ps4.sav':b'unsupported-compressed-data'})
            m=g.Manager(store=MemoryStore());m.set_key(KEY)
            with patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',return_value=returned):
                m.decrypt(dict(path=str(a),bin_path=str(b),account_id='0000000000000001',title_id='CUSA01014'))
                deadline=time.monotonic()+5
                while m.running and time.monotonic()<deadline:time.sleep(.01)
            self.assertFalse(m.running);self.assertEqual(m.view()['status'],'done');self.assertIn('could not be opened for editing',m.view()['message'])
            self.assertIsNotNone(m.session);self.assertFalse(m.view()['editable']);self.assertEqual((m.folder/'Decrypted-Result.zip').read_bytes(),returned)
            self.assertTrue((m.folder/'Original-Encrypted-Pair.zip').is_file());self.assertEqual(a.read_bytes(),b'original')


@unittest.skipUnless(os.environ.get('DI2_TEST_SAVE'),'Set DI2_TEST_SAVE for the private local fixture integration test.')
class RealSaveTests(unittest.TestCase):
    def wait(self,m):
        deadline=time.monotonic()+30
        while m.running and time.monotonic()<deadline:time.sleep(.01)
        self.assertFalse(m.running);self.assertEqual(m.view()['status'],'done',m.view())
    def test_complete_local_roundtrip_keeps_metadata_and_originals(self):
        from save_core import Save
        raw=Path(os.environ['DI2_TEST_SAVE']).read_bytes();sealed=b'pfsSKKey'+b'\0'*88
        files={'save/sce_sys/param.sfo':sfo(),'save/ue4savegame.ps4.sav':raw,'save/companion.dat':b'untouched'}
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(Path(tmp)/'Backups')}):
            root=Path(tmp);a=root/'DeadIsland2SaveGame';b=root/'DeadIsland2SaveGame.bin';a.write_bytes(b'encrypted-original');b.write_bytes(sealed)
            entry=dict(path=str(a),bin_path=str(b),account_id='0000000000000001',title_id='CUSA01014')
            m=g.Manager(store=MemoryStore());m.set_key(KEY)
            encrypted=g.make_zip({'DeadIsland2SaveGame':b'encrypted-edited','DeadIsland2SaveGame.bin':sealed})
            with patch.object(g.Client,'submit',return_value='job'),patch.object(g.Client,'result',side_effect=[g.make_zip(files),encrypted,encrypted]) as result:
                m.decrypt(entry);self.wait(m);self.assertEqual(m.session['files']['companion.dat'],b'untouched')
                save=Save(raw);w=next(w for w in save.weapons if w.info()['editable']);edited=save.rebuild({str(w.idx):{'level':7}})
                original_submit=g.Client.submit
                with patch.object(g.Client,'submit',return_value='encrypt-job') as submit:
                    m.encrypt(edited);self.wait(m)
                    package=submit.call_args.args[1][0][1];parts=g.unpack(package)
                    self.assertEqual(parts['ue4savegame.ps4.sav'],edited);self.assertEqual(parts['sce_sys/param.sfo'],sfo());self.assertEqual(parts['companion.dat'],b'untouched')
                first=m.folder;self.assertTrue((first/'PS4/SAVEDATA/0000000000000001/CUSA01014/DeadIsland2SaveGame').is_file())
                m.encrypt(edited);self.wait(m);self.assertNotEqual(first,m.folder);self.assertTrue(first.is_dir())
            self.assertEqual(a.read_bytes(),b'encrypted-original');self.assertEqual(b.read_bytes(),sealed)
            self.assertTrue(list((root/'Backups').iterdir()))
            for p in root.rglob('*'):
                if p.is_file():self.assertNotIn(KEY.encode(),p.read_bytes())

if __name__=='__main__':unittest.main()
