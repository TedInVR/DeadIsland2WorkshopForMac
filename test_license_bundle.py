"""License metadata is retained verbatim, including multiline package descriptions."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import license_bundle as bundle

class Metadata(dict):
    def __str__(self):raise AssertionError('Do not reserialize metadata as email headers')
    def get_all(self,key,default):return default
class Distribution:
    metadata=Metadata(Name='example',License='MIT');version='1.0';files=[]
    def read_text(self,name):return 'Name: example\nVersion: 1.0\n\nDescription\nProject links\n-------------\n' if name=='METADATA' else None

class LicenseTests(unittest.TestCase):
    def test_preserves_raw_metadata_and_required_notices(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);view=root/'webview';(view/'lib').mkdir(parents=True)
            (view/'lib/Microsoft.Web.WebView2.LICENSE.md').write_text('Microsoft notice')
            out=root/'dist';out.mkdir()
            with patch.object(bundle.metadata,'distributions',return_value=[Distribution()]),patch.dict(sys.modules,{'webview':types.SimpleNamespace(__file__=str(view/'__init__.py'))}):
                packages=bundle.collect(out);bundle.finish(out,packages)
            self.assertEqual((out/'THIRD_PARTY_LICENSES/example-1.0/METADATA.txt').read_text(),Distribution().read_text('METADATA'))
            self.assertEqual((out/'THIRD_PARTY_LICENSES/Microsoft-WebView2-LICENSE.md').read_text(),(bundle.ROOT/'third_party_licenses/Microsoft-WebView2-LICENSE.md').read_text())
            inventory=json.loads((out/'DISTRIBUTION-INVENTORY.json').read_text())
            self.assertEqual(inventory['packages'][0]['name'],'example')
            self.assertTrue(inventory['files'])

if __name__=='__main__':unittest.main()
