import io,json,hashlib,plistlib,tempfile,unittest,zipfile,subprocess
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
        with patch.object(u,'app_running',return_value=False),patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',side_effect=['0.3.0','0.4.0']),patch.object(u,'github_bytes',return_value=b),patch.object(u.subprocess,'run') as run:
            run.return_value.returncode=0;run.return_value.stdout='installed';run.return_value.stderr=''
            self.assertEqual(u.run()['status'],'installed')
            self.assertIn('--unattended',run.call_args.args[0])
        self.assertFalse((self.root/'pending-update.zip').exists())
    def test_cached_zip_restores_missing_pending_manifest(self):
        b=self.package();m=self.manifest(b);(self.root/'pending-update.zip').write_bytes(b)
        with patch.object(u,'github_bytes') as network:u.download(m);network.assert_not_called()
        self.assertEqual(json.loads((self.root/'pending-update.json').read_text()),m)
    def test_after_quit_waits_then_installs_only_the_pending_update(self):
        u.atomic_json(self.root/'pending-update.json',{'version':'0.4.0'});u.atomic_json(self.root/'install-intent.json',{'pid':1})
        with patch.object(u,'app_running',side_effect=[True,True,False]),patch.object(u.time,'sleep') as sleep,patch.object(u,'run',return_value={'status':'installed'}) as run:
            self.assertEqual(u.after_quit()['status'],'installed');self.assertEqual(sleep.call_count,2);run.assert_called_once_with(pending_only=True)
        self.assertFalse((self.root/'install-intent.json').exists())
    def test_pending_only_never_fetches_when_nothing_is_queued(self):
        with patch.object(u,'app_running',return_value=False),patch.object(u,'manifest') as network:
            self.assertEqual(u.run(pending_only=True)['status'],'nothing_queued');network.assert_not_called()
    def test_successful_exit_with_wrong_installed_version_is_reported(self):
        b=self.package();m=self.manifest(b)
        with patch.object(u,'app_running',return_value=False),patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',return_value='0.3.0'),patch.object(u,'github_bytes',return_value=b),patch.object(u.subprocess,'run') as run:
            run.return_value.returncode=0;run.return_value.stdout='';run.return_value.stderr=''
            with self.assertRaisesRegex(u.UpdateError,'still contains version'):u.run()
        self.assertTrue((self.root/'pending-update.json').exists())
    def test_installer_stdout_and_stderr_are_retained(self):
        b=self.package();m=self.manifest(b)
        with patch.object(u,'app_running',return_value=False),patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',return_value='0.3.0'),patch.object(u,'github_bytes',return_value=b),patch.object(u.subprocess,'run') as run:
            run.return_value.returncode=1;run.return_value.stdout='stdout failure';run.return_value.stderr='stderr detail'
            with self.assertRaisesRegex(u.UpdateError,'stdout failure'):u.run()
        log=(self.root/'install.log').read_text();self.assertIn('stdout failure',log);self.assertIn('stderr detail',log)
    def test_newer_version_check(self):
        with patch.object(u,'manifest',return_value={'version':'0.4.0'}),patch.object(u,'installed_version',return_value='0.3.0'):self.assertEqual(u.check()['status'],'available')
    def test_startup_respects_disabled_preference_without_network(self):
        u.atomic_json(self.root/'settings.json',{'automatic_updates':False})
        with patch.object(u,'queue') as queue:
            self.assertEqual(u.startup()['status'],'disabled');queue.assert_not_called()
    def test_background_check_queues_verified_update_without_installing(self):
        b=self.package();m=self.manifest(b)
        with patch.object(u,'manifest',return_value=m),patch.object(u,'installed_version',return_value='0.3.0'),patch.object(u,'github_bytes',return_value=b):
            with patch.object(u,'run') as install:
                self.assertEqual(u.startup()['status'],'queued');install.assert_not_called()
        self.assertEqual((self.root/'pending-update.zip').read_bytes(),b)
    def test_startup_handoff_reopens_only_after_install_and_clears_intent(self):
        u.atomic_json(self.root/'pending-update.json',{'version':'0.4.0'});u.atomic_json(self.root/'install-intent.json',{'pid':1})
        def reopen():self.assertFalse((self.root/'install-intent.json').exists())
        with patch.object(u,'app_running',return_value=False),patch.object(u,'run',return_value={'status':'installed'}),patch.object(u,'reopen_app',side_effect=reopen) as launch:
            self.assertEqual(u.after_quit(reopen=True)['status'],'installed');launch.assert_called_once_with()
    def test_startup_install_failure_reopens_old_app_with_failure_flag(self):
        u.atomic_json(self.root/'pending-update.json',{'version':'0.4.0'});u.atomic_json(self.root/'install-intent.json',{'pid':1})
        with patch.object(u,'app_running',return_value=False),patch.object(u,'run',side_effect=u.UpdateError('Build failed')),patch.object(u,'reopen_app') as launch:
            with self.assertRaisesRegex(u.UpdateError,'Build failed'):u.after_quit(reopen=True)
            launch.assert_called_once_with(failed=True)
        self.assertFalse((self.root/'install-intent.json').exists());self.assertEqual(u.read_json('update-status.json')['status'],'error')
    def test_normal_quit_install_does_not_reopen(self):
        u.atomic_json(self.root/'pending-update.json',{'version':'0.4.0'})
        with patch.object(u,'app_running',return_value=False),patch.object(u,'run',return_value={'status':'installed'}),patch.object(u,'reopen_app') as launch:
            u.after_quit();launch.assert_not_called()
    def test_reopen_skips_second_startup_check(self):
        with patch.object(u.subprocess,'run') as launch:
            u.reopen_app();self.assertIn('--skip-startup-update',launch.call_args.args[0])

    def test_reopen_checks_macos_launch_and_uses_new_instance(self):
        with patch.object(u.subprocess,'run') as launch:
            u.reopen_app()
            self.assertEqual(launch.call_args.args[0][:2],['/usr/bin/open','-n'])
            self.assertTrue(launch.call_args.kwargs['check'])
            self.assertEqual(launch.call_args.kwargs['timeout'],30)
    def test_reopen_reports_launch_failure(self):
        with patch.object(u.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['open'])):
            with self.assertRaisesRegex(u.UpdateError,'could not reopen'):u.reopen_app()

if __name__=='__main__':unittest.main()
