"""Synthetic service round trips: account byte order, data retention and fail-closed output."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
import garlic_service as g
from test_garlic_service import sfo

A='0123456789abcdef';TITLE='CUSA01014';NAME='DeadIsland2SaveGame'
class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        self.files={'sce_sys/param.sfo':sfo(A,TITLE),'sce_sys/keystone':b'original keystone','ue4savegame.ps4.sav':b'edited game','companion':b'keep'}
        self.pair=g.make_zip({NAME:b'encrypted',NAME+'.bin':b'pfsSKKey'+bytes(88)})
        self.client=Mock();self.client.submit.side_effect=['encrypt-1','verify-1','encrypt-2','verify-2']
    def tearDown(self):self.tmp.cleanup()
    def check(self,account=A,**changes):
        return g.make_zip(dict(self.files,**{'sce_sys/param.sfo':sfo(account,TITLE)},**changes))
    def run_encrypt(self):return g.verified_encrypt(self.client,self.files,A,TITLE,NAME,self.folder,lambda _:None)
    def test_correct_worker_is_verified_without_retry(self):
        self.client.result.side_effect=[self.pair,self.check()]
        pair,job=self.run_encrypt()
        self.assertEqual(job,'encrypt-1');self.assertEqual(self.client.submit.call_count,2)
        self.assertEqual(self.client.submit.call_args_list[1].args[0],'decrypt')
        self.assertTrue((self.folder/'Ownership-Verified.json').exists())
        self.assertEqual((self.folder/'Encrypted-Result.zip').read_bytes(),self.pair)
    def test_reversed_account_is_detected_corrected_and_verified_again(self):
        rev=bytes.fromhex(A)[::-1].hex()
        self.client.result.side_effect=[self.pair,self.check(rev),self.pair,self.check()]
        _,job=self.run_encrypt()
        self.assertEqual(job,'encrypt-2')
        self.assertEqual(self.client.submit.call_args_list[0].args[2],A)
        self.assertEqual(self.client.submit.call_args_list[2].args[2],rev)
        self.assertEqual(g.package_identity(g.unpack(self.client.submit.call_args_list[2].args[1][0][1])),(A,TITLE))
        self.assertTrue((self.folder/'Encrypted-Attempt-1.zip').exists())
    def test_other_account_is_never_released(self):
        self.client.result.side_effect=[self.pair,self.check('1111111111111111')]
        with self.assertRaisesRegex(g.ServiceError,'different PSN account'):self.run_encrypt()
        self.assertFalse((self.folder/'Encrypted-Result.zip').exists())
        self.assertFalse((self.folder/'Ownership-Verified.json').exists())
        self.assertEqual(self.client.submit.call_count,2)
    def test_unsuccessful_correction_is_never_released(self):
        rev=bytes.fromhex(A)[::-1].hex()
        self.client.result.side_effect=[self.pair,self.check(rev),self.pair,self.check(rev)]
        with self.assertRaisesRegex(g.ServiceError,'different PSN account'):self.run_encrypt()
        self.assertFalse((self.folder/'Encrypted-Result.zip').exists())
    def test_wrong_data_and_keystone_are_never_released(self):
        for field in ('ue4savegame.ps4.sav','companion','sce_sys/keystone'):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    self.folder=Path(tmp);self.client.submit.side_effect=['enc','dec']
                    bad=dict(self.files);bad[field]=b'changed by service'
                    self.client.result.side_effect=[self.pair,g.make_zip(bad)]
                    with self.assertRaisesRegex(g.ServiceError,'did not preserve'):self.run_encrypt()
                    self.assertFalse((self.folder/'Encrypted-Result.zip').exists())
    def test_verification_failure_retains_diagnostics_without_releasing_result(self):
        self.client.result.side_effect=[self.pair,g.ServiceError('verification unavailable')]
        with self.assertRaisesRegex(g.ServiceError,'verification unavailable'):self.run_encrypt()
        self.assertTrue((self.folder/'Encrypted-Attempt-1.zip').exists())
        self.assertFalse((self.folder/'Encrypted-Result.zip').exists())

if __name__=='__main__':unittest.main()
