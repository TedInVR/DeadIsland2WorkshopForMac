"""First-use persistence, failure handling and backend enforcement without registration."""
import json,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
import legal_state as legal
import server
import windows_app

class AgreementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.target=Path(self.temp.name)/'usage-acknowledgment.json'
        self.location=patch.object(legal,'file',return_value=self.target);self.location.start()
    def tearDown(self):self.location.stop();self.temp.cleanup()
    def consent(self):return {'confirm':True,'version':legal.VERSION,'sha256':legal.digest()}
    def test_acceptance_is_local_minimal_and_survives_updates(self):
        self.assertFalse(legal.is_accepted())
        with patch('urllib.request.urlopen',side_effect=AssertionError('No agreement network request')):
            legal.accept(self.consent())
        record=json.loads(self.target.read_text())
        self.assertEqual(set(record),{'schema','accepted','agreement_version','document_sha256','accepted_at'})
        with patch.object(legal,'VERSION',99),patch.object(legal,'digest',return_value='f'*64):
            self.assertTrue(legal.is_accepted());legal.require()
        self.assertEqual(json.loads(self.target.read_text()),record)
    def test_incomplete_or_stale_acknowledgments_do_not_unlock(self):
        for value in ({},dict(self.consent(),confirm=False),dict(self.consent(),sha256='0'*64),dict(self.consent(),version=0)):
            with self.assertRaises(legal.AgreementRequired):legal.accept(value)
        self.assertFalse(self.target.exists())
    def test_corrupt_records_are_first_use(self):
        for text in ('not JSON','[]','null','{}','{"accepted":true}'):
            self.target.write_text(text);self.assertFalse(legal.is_accepted())
    def test_write_failure_keeps_app_locked(self):
        with patch.object(legal.os,'replace',side_effect=PermissionError):
            with self.assertRaises(legal.AgreementRequired):legal.accept(self.consent())
        self.assertFalse(legal.is_accepted());self.assertFalse(list(self.target.parent.glob('*.tmp')))
    def test_windows_native_open_and_export_are_locked(self):
        api=windows_app.DesktopAPI(None)
        self.assertIn('first-use',api.open_save()['error'])
        self.assertIn('first-use',api.export_save('edited.sav')['error'])
    def test_http_blocks_edits_and_processing_until_acknowledged(self):
        http=server.HTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(http.server_port)+'/'+server.token+'/'
        try:
            for name in ('saves','service-status','export'):
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+name)
                self.assertEqual(e.exception.code,403)
            for name in ('open','prepare','service-decrypt','service-resign'):
                req=urllib.request.Request(base+name,data=b'{}')
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
                self.assertEqual(e.exception.code,403)
            for name in ('legal-status','credits'):
                with urllib.request.urlopen(base+name) as response:self.assertEqual(response.status,200)
            req=urllib.request.Request(base+'legal-accept',data=json.dumps(self.consent()).encode())
            with urllib.request.urlopen(req) as response:self.assertTrue(json.load(response)['accepted'])
            with urllib.request.urlopen(base+'service-status') as response:self.assertEqual(response.status,200)
        finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main()
