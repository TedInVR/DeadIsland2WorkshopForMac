"""Private per-user credentials in macOS Keychain or Windows Credential Manager.
No credential values are written to app settings, command arguments or log files.
"""
import ctypes as C
import sys
SERVICE=b'local.ted.di2workshop.garlicsaves'
ACCOUNT=b'worker-key'
class CredentialError(ValueError):pass

def failure():return CredentialError('Workshop could not access its secure credential store. Allow Keychain access if prompted, then try again. Your saved key has not been copied to settings or logs.')

class MacStore:
    def __init__(self,keychain=None):
        self.keychain=keychain
        self.sec=C.CDLL('/System/Library/Frameworks/Security.framework/Security')
        self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.cf.CFRelease.argtypes=[C.c_void_p];self.cf.CFRelease.restype=None
        self.sec.SecKeychainFindGenericPassword.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,C.POINTER(C.c_uint32),C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)]
        self.sec.SecKeychainFindGenericPassword.restype=C.c_int32
        self.sec.SecKeychainAddGenericPassword.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_void_p,C.c_void_p]
        self.sec.SecKeychainAddGenericPassword.restype=C.c_int32
        self.sec.SecKeychainItemModifyAttributesAndData.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p];self.sec.SecKeychainItemModifyAttributesAndData.restype=C.c_int32
        self.sec.SecKeychainItemDelete.argtypes=[C.c_void_p];self.sec.SecKeychainItemDelete.restype=C.c_int32
        self.sec.SecKeychainItemFreeContent.argtypes=[C.c_void_p,C.c_void_p];self.sec.SecKeychainItemFreeContent.restype=C.c_int32
    def find(self):
        length=C.c_uint32();data=C.c_void_p();item=C.c_void_p()
        status=self.sec.SecKeychainFindGenericPassword(self.keychain,len(SERVICE),SERVICE,len(ACCOUNT),ACCOUNT,C.byref(length),C.byref(data),C.byref(item))
        if status==-25300:return None,None
        if status:raise failure()
        try:return C.string_at(data,length.value).decode('utf-8'),item
        finally:
            if data.value:self.sec.SecKeychainItemFreeContent(None,data)
    def load(self):
        value,item=self.find()
        if item:self.cf.CFRelease(item)
        return value
    def save(self,value):
        old,item=self.find();raw=value.encode('utf-8')
        try:
            if item:status=self.sec.SecKeychainItemModifyAttributesAndData(item,None,len(raw),raw)
            else:status=self.sec.SecKeychainAddGenericPassword(self.keychain,len(SERVICE),SERVICE,len(ACCOUNT),ACCOUNT,len(raw),raw,None)
            if status:raise failure()
        finally:
            if item:self.cf.CFRelease(item)
    def delete(self):
        old,item=self.find()
        if item:
            try:
                if self.sec.SecKeychainItemDelete(item):raise failure()
            finally:self.cf.CFRelease(item)

class WindowsStore:
    def __init__(self):
        from ctypes import wintypes as W
        class Credential(C.Structure):
            _fields_=[('Flags',W.DWORD),('Type',W.DWORD),('TargetName',W.LPWSTR),('Comment',W.LPWSTR),('LastWritten',W.FILETIME),('CredentialBlobSize',W.DWORD),('CredentialBlob',C.POINTER(C.c_ubyte)),('Persist',W.DWORD),('AttributeCount',W.DWORD),('Attributes',C.c_void_p),('TargetAlias',W.LPWSTR),('UserName',W.LPWSTR)]
        self.Credential=Credential;self.api=C.WinDLL('advapi32',use_last_error=True);self.target=SERVICE.decode()
        self.api.CredReadW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.POINTER(C.POINTER(Credential))];self.api.CredReadW.restype=W.BOOL
        self.api.CredWriteW.argtypes=[C.POINTER(Credential),W.DWORD];self.api.CredWriteW.restype=W.BOOL
        self.api.CredDeleteW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD];self.api.CredDeleteW.restype=W.BOOL
        self.api.CredFree.argtypes=[C.c_void_p];self.api.CredFree.restype=None
    def load(self):
        ptr=C.POINTER(self.Credential)()
        if not self.api.CredReadW(self.target,1,0,C.byref(ptr)):
            if C.get_last_error()==1168:return None
            raise failure()
        try:return C.string_at(ptr.contents.CredentialBlob,ptr.contents.CredentialBlobSize).decode('utf-8')
        finally:self.api.CredFree(ptr)
    def save(self,value):
        raw=value.encode('utf-8');buf=(C.c_ubyte*len(raw)).from_buffer_copy(raw)
        cred=self.Credential();cred.Type=1;cred.TargetName=self.target;cred.UserName=ACCOUNT.decode();cred.CredentialBlobSize=len(raw);cred.CredentialBlob=buf;cred.Persist=2
        if not self.api.CredWriteW(C.byref(cred),0):raise failure()
    def delete(self):
        if not self.api.CredDeleteW(self.target,1,0) and C.get_last_error()!=1168:raise failure()

class UnavailableStore:
    def load(self):return None
    def save(self,value):raise CredentialError('Secure credential storage requires the Mac or Windows desktop app.')
    def delete(self):pass

def default_store():
    if sys.platform=='darwin':return MacStore()
    if sys.platform=='win32':return WindowsStore()
    return UnavailableStore()
