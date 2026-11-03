"""Public synthetic framing tests; optional private-package integration via environment only."""
import os,struct,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import save_codec as codec
import zstandard,cityhash
HEADER=bytes.fromhex('3dca12000a000a0001d90e51050000005a73746400')
def packed(body):
    chunks=[]
    for p in range(0,len(body),65536):
        raw=body[p:p+65536];frame=zstandard.ZstdCompressor().compress(raw)
        chunks.append(struct.pack('<II',len(frame),len(raw))+frame)
    return HEADER+b''.join(chunks)+codec.END+struct.pack('<Q',cityhash.CityHash64(body))
class FramingTests(unittest.TestCase):
    def test_multichunk_edit_rehash_and_noedit_identity(self):
        body=b'example data'*19000;raw=packed(body);plain,state=codec.decode(raw)
        self.assertEqual(plain,HEADER+body);self.assertEqual(codec.encode(plain,state),raw)
        edited=plain[:-12]+b'different!!!';out=codec.encode(edited,state)
        self.assertEqual(codec.decode(out)[0],edited)
        self.assertEqual(out[21:21+len(state['chunks'][0][1])],state['chunks'][0][1])
    def test_damage_truncation_limits_and_footer_are_rejected(self):
        raw=packed(b'example'*20000)
        variants=[raw[:-1],raw[:-8]+bytes(8),raw+b'extra',raw[:25]+struct.pack('<I',65537)+raw[29:]]
        for value in variants:
            with self.subTest(size=len(value)),self.assertRaises(codec.CodecError):codec.decode(value)
        with patch.object(codec,'LIMIT',100):
            with self.assertRaises(codec.CodecError):codec.decode(raw)
    def test_uncompressed_data_passes_through(self):
        raw=HEADER+struct.pack('<I',1)+b'example'
        self.assertEqual(codec.decode(raw),(raw,None));self.assertEqual(codec.encode(raw,None),raw)

@unittest.skipUnless(os.environ.get('DI2_TEST_COMPRESSED_ZIP'),'Private package is never included in repository')
class CompressedSaveTests(unittest.TestCase):
    def test_complete_edit_and_service_resume_roundtrip(self):
        from save_core import Save
        import garlic_service as g
        from test_garlic_service import MemoryStore
        archive=Path(os.environ['DI2_TEST_COMPRESSED_ZIP']).read_bytes();files=g.package_files(g.unpack(archive));name='ue4savegame.ps4.sav';raw=files[name];s=Save(raw)
        self.assertEqual(s.rebuild({}),raw)
        weapon=next(w for w in s.weapons if w.info()['editable']);level=8 if weapon.level!=8 else 9
        edited=s.rebuild({str(weapon.idx):{'level':level}});t=Save(edited)
        self.assertEqual(t.weapons[weapon.idx].level,level)
        for a,b in zip(s.weapons,t.weapons):
            if a.idx!=weapon.idx:self.assertEqual(a.b[a.start:a.end],b.b[b.start:b.end])
        # Read identity locally; private sample values never appear in public tests/output.
        sf=files['sce_sys/param.sfo'];_,_,keys,data,count=struct.unpack_from('<4sIIII',sf);fields={}
        for i in range(count):
            k,fmt,n,maximum,offset=struct.unpack_from('<HHIII',sf,20+16*i);key=sf[keys+k:sf.index(b'\0',keys+k,data)].decode();fields[key]=sf[data+offset:data+offset+n]
        account=f"{int.from_bytes(fields['ACCOUNT_ID'],'little'):016x}";title=fields['TITLE_ID'].rstrip(b'\0').decode()
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'DI2_WORKSHOP_BACKUP_DIR':str(Path(temp)/'Backups')}):
            root=Path(temp)/'ServiceSessions'/'20990101-test';root.mkdir(parents=True)
            import json
            (root/'decrypt-job.json').write_text(json.dumps({'account_id':account,'title_id':title}))
            (root/'Decrypted-Result.zip').write_bytes(archive)
            (root/'Original-Encrypted-Pair.zip').write_bytes(g.make_zip({'DeadIsland2SaveGame':b'original','DeadIsland2SaveGame.bin':b'pfsSKKey'+bytes(88)}))
            m=g.Manager(store=MemoryStore());state=m.resume();self.assertTrue(state['editable']);self.assertEqual(m.session['files'],files)
            m.client=g.Client('test_worker_key_00000000000000000000');m.key_loaded=True
            returned=g.make_zip({'DeadIsland2SaveGame':b'encrypted','DeadIsland2SaveGame.bin':b'pfsSKKey'+bytes(88)})
            with patch.object(g.Client,'submit',return_value='job') as submit,patch.object(g.Client,'result',return_value=returned):
                m.encrypt(edited)
                import time
                deadline=time.monotonic()+30
                while m.running and time.monotonic()<deadline:time.sleep(.01)
                self.assertEqual(m.view()['status'],'done');uploaded=g.unpack(submit.call_args.args[1][0][1])
                self.assertEqual(uploaded[name],edited)
                for n,v in files.items():
                    if n!=name:self.assertEqual(uploaded[n],v)
            self.assertEqual((root/'Decrypted-Result.zip').read_bytes(),archive)

if __name__=='__main__':unittest.main()
