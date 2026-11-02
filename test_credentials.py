"""Credential persistence, failed-write handling, and isolated native vault checks."""
import ctypes as C,sys,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
import credential_store as vault
from garlic_service import Manager,Client
from test_garlic_service import MemoryStore,KEY

class PersistenceTests(unittest.TestCase):
    def test_saved_key_loads_in_new_manager_without_returning_secret(self):
        store=MemoryStore();a=Manager(store=store);a.set_key(KEY)
        b=Manager(store=store);state=b.view()
        self.assertTrue(state['has_key']);self.assertTrue(state['key_saved']);self.assertEqual(b.client.key,KEY)
        self.assertNotIn(KEY,str(state))
    def test_replace_and_delete_survive_reopening(self):
        store=MemoryStore();a=Manager(store=store);a.set_key(KEY)
        replacement='replacement_worker_key_0000000000000000';a.set_key(replacement)
        b=Manager(store=store);b.view();self.assertEqual(b.client.key,replacement)
        b.set_key('');self.assertFalse(Manager(store=store).view()['has_key'])
    def test_denied_write_keeps_previous_credential(self):
        store=MemoryStore();a=Manager(store=store);a.set_key(KEY)
        with patch.object(store,'save',side_effect=vault.CredentialError('Access denied')):
            with self.assertRaises(vault.CredentialError):a.set_key('replacement_worker_key_0000000000000000')
        self.assertEqual(a.client.key,KEY);self.assertEqual(store.value,KEY)
    def test_denied_read_is_visible_and_can_retry(self):
        store=MemoryStore();store.value=KEY;a=Manager(store=store)
        with patch.object(store,'load',side_effect=vault.CredentialError('Access denied')):
            state=a.view();self.assertIsNotNone(state['key_error']);self.assertFalse(state['has_key']);self.assertNotIn(KEY,str(state))
        self.assertTrue(a.view()['has_key'])
    def test_invalid_replacement_does_not_change_saved_key(self):
        store=MemoryStore();a=Manager(store=store);a.set_key(KEY)
        with self.assertRaises(ValueError):a.set_key('not a key')
        self.assertEqual(store.value,KEY)

@unittest.skipUnless(sys.platform=='darwin','Native macOS test')
class MacNativeTests(unittest.TestCase):
    def test_two_instances_share_private_temporary_keychain(self):
        with tempfile.TemporaryDirectory() as temp:
            api=vault.MacStore().sec;ref=C.c_void_p();password=b'disposable-test-password'
            api.SecKeychainCreate.argtypes=[C.c_char_p,C.c_uint32,C.c_void_p,C.c_ubyte,C.c_void_p,C.POINTER(C.c_void_p)];api.SecKeychainCreate.restype=C.c_int32
            api.SecKeychainDelete.argtypes=[C.c_void_p];api.SecKeychainDelete.restype=C.c_int32
            status=api.SecKeychainCreate(str(Path(temp)/'test.keychain').encode(),len(password),password,0,None,C.byref(ref))
            self.assertEqual(status,0)
            a=vault.MacStore(ref);b=vault.MacStore(ref)
            try:
                self.assertIsNone(a.load());a.save(KEY);self.assertEqual(b.load(),KEY)
                b.save(KEY+'updated');self.assertEqual(a.load(),KEY+'updated')
                a.delete();self.assertIsNone(b.load());b.delete()
            finally:api.SecKeychainDelete(ref);a.cf.CFRelease(ref)

@unittest.skipUnless(sys.platform=='win32','Native Windows test')
class WindowsNativeTests(unittest.TestCase):
    def test_two_instances_share_disposable_credential(self):
        a=vault.WindowsStore();b=vault.WindowsStore();a.target=b.target='Workshop-test-'+uuid.uuid4().hex
        try:
            self.assertIsNone(a.load());a.save(KEY);self.assertEqual(b.load(),KEY)
            b.save(KEY+'updated');self.assertEqual(a.load(),KEY+'updated');a.delete();self.assertIsNone(b.load());b.delete()
        finally:a.delete()

if __name__=='__main__':unittest.main()
