import tempfile,unittest
from pathlib import Path
import windows_app as w

class FakeView:
    class FileDialog:OPEN=1;SAVE=2
class FakeWindow:
    def __init__(self,path):self.path=path
    def create_file_dialog(self,*args,**kwargs):return (str(self.path),) if self.path else None

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.api=w.DesktopAPI(FakeView);w.server.app.output=b'validated edited bytes'
    def tearDown(self):self.temp.cleanup();w.server.app.output=None
    def test_original_cannot_be_overwritten(self):
        p=self.root/'original.sav';p.write_bytes(b'original');self.api._sources.add(str(p.resolve()).casefold());self.api._bind(FakeWindow(p))
        self.assertIn('error',self.api.export_save('edited.sav'));self.assertEqual(p.read_bytes(),b'original')
    def test_separate_export_is_complete_and_atomic(self):
        p=self.root/'edited.sav';self.api._bind(FakeWindow(p));self.assertIn('message',self.api.export_save('../edited.sav'))
        self.assertEqual(p.read_bytes(),b'validated edited bytes');self.assertEqual(list(self.root.glob('*.tmp')),[])
    def test_cancel_does_not_write(self):
        self.api._bind(FakeWindow(None));self.assertIn('canceled',self.api.export_save('edited.sav')['message']);self.assertEqual(list(self.root.iterdir()),[])
    def test_invalid_save_does_not_replace_current_save(self):
        p=self.root/'bad.sav';p.write_bytes(b'not a save');self.api._bind(FakeWindow(p));old=w.server.app.save
        self.assertIn('error',self.api.open_save());self.assertIs(w.server.app.save,old)
    def test_package_resources(self):w.self_test()
if __name__=='__main__':unittest.main()
