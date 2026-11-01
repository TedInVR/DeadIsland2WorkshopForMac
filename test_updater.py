import io,json,hashlib,plistlib,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import updater as u

class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.p=patch.object(u,'SUPPORT',self.root);self.p.start()
    def tearDown(self):self.p.stop();self.temp.cleanup()
    def package(self,version='0.4.0'):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            for name in ('Install.command','Workshop.swift','save_core.py','server.py','index.html','catalog.json','updater.py'):z.writestr('Package/'+name,'test')
            z.writestr('Package/Info.plist',plistlib.dumps({'CFBundleShortVersionString':version}))
        return b.getvalue()
    def manifest(self,b):return dict(version='0.4.0',sha256=hashlib.sha256(b).hexdigest(),path='downloads/Dead-Island-2-Workshop-Mac-0.4.0.zip')
    def test_versions(self):
        self.assertGreater(u.version_tuple('0.10.0'),u.version_tuple('0.9.9'))
        for v in ('dev','1.0','1;rm',''):
            with self.assertRaises(u.UpdateError):u.version_tuple(v)
    def test_no_network_while_open(self):
        with patch.object(u,'app_running',return_value=True),patch.object(u,'manifest') as m:
            self.assertEqual(u.run()['status'],'app_open');m.assert_not_called()
    def test_disabled(self):
        u.atomic_json(self.root/'settings.json',{'automatic_updates':False})
        with patch.object(u,'manifest') as m:self.assertEqual(u.run()['status'],'disabled');m.assert_not_called()
    def test_bad_checksum_no_install(self):
        m=self.manifest(b'expected')
        with patch.object(u,'github_bytes',return_value=b'wrong'):
            with self.assertRaises(u.UpdateError):u.download(m)
        self.assertFalse((self.root/'pending-update.zip').exists())
    def test_verified_queue(self):
        b=self.package();m=self.manifest(b)
        with patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',return_value='0.3.0'),patch.object(u,'github_bytes',return_value=b):self.assertEqual(u.queue()['status'],'queued')
        self.assertEqual((self.root/'pending-update.zip').read_bytes(),b)
    def test_private_archive_traversal_rejected(self):
        p=self.root/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('../escape','bad')
        with self.assertRaises(u.UpdateError):u.extract_package(p,self.root/'expanded')
        self.assertFalse((self.root.parent/'escape').exists())
    def test_archive_symlink_rejected(self):
        p=self.root/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:
            i=zipfile.ZipInfo('Package/link');i.external_attr=(0o120777<<16);z.writestr(i,'/tmp/elsewhere')
        with self.assertRaises(u.UpdateError):u.extract_package(p,self.root/'expanded')
    def test_closed_install_unattended_and_cleanup(self):
        b=self.package();m=self.manifest(b)
        with patch.object(u,'app_running',return_value=False),patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',return_value='0.3.0'),patch.object(u,'github_bytes',return_value=b),patch.object(u.subprocess,'run') as run:
            run.return_value.returncode=0
            self.assertEqual(u.run()['status'],'installed')
            self.assertIn('--unattended',run.call_args.args[0])
        self.assertFalse((self.root/'pending-update.zip').exists())
    def test_newer_version_check(self):
        with patch.object(u,'manifest',return_value={'version':'0.4.0'}),patch.object(u,'installed_version',return_value='0.3.0'):self.assertEqual(u.check()['status'],'available')

if __name__=='__main__':unittest.main()
