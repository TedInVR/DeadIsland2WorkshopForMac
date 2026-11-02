"""Opt-in GarlicSaves API client. Credentials live in memory, never on disk."""
import io,json,os,re,stat,struct,threading,time,uuid,zipfile
from pathlib import Path,PurePosixPath
from urllib import request,error
import backup_storage

BASE='https://garlicsaves.com/api/v1'
LIMIT=128*1024*1024
class ServiceError(ValueError):pass

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ServiceError('GarlicSaves redirected the request. No credentials were forwarded. Please check service availability.')

def validate_pair(save,sealed):
    if not save or len(save)>LIMIT:raise ServiceError('The encrypted save is empty or larger than 128 MB.')
    if len(sealed)!=96 or not sealed.startswith(b'pfsSKKey'):raise ServiceError('Choose the matching 96-byte PS4 .bin key file.')

def unpack(raw):
    if len(raw)>LIMIT:raise ServiceError('Result ZIP exceeds 128 MB.')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if len(z.infolist())>2048:raise ServiceError('Too many files in result ZIP.')
            total=0;result={};seen=set()
            for entry in z.infolist():
                name=entry.filename;p=PurePosixPath(name)
                if not name or '\\' in name or p.is_absolute() or '..' in p.parts or ':' in name or '\x00' in name or any(ord(c)<32 for c in name):raise ServiceError('Unsafe path in result ZIP.')
                if stat.S_ISLNK(entry.external_attr>>16) or entry.flag_bits&1:raise ServiceError('Links or encrypted entries are not supported in result ZIPs.')
                if entry.is_dir():continue
                normalized=p.as_posix();fold=normalized.casefold()
                if fold in seen:raise ServiceError('Duplicate file paths in result ZIP.')
                seen.add(fold);total+=entry.file_size
                if total>LIMIT:raise ServiceError('Expanded result exceeds 128 MB.')
                result[normalized]=z.read(entry)
            if not result:raise ServiceError('The result ZIP contains no files.')
            return result
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as e:raise ServiceError('GarlicSaves returned an unreadable ZIP.') from e

def make_zip(files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in files.items():z.writestr(name,value)
    return out.getvalue()

def write_new(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def decrypted_files(files):
    sfos=[n for n in files if n.lower().endswith('sce_sys/param.sfo') and files[n].startswith(b'\0PSF')]
    if len(sfos)!=1:raise ServiceError('The decrypted package must include exactly one sce_sys/param.sfo. The downloaded ZIP has been kept for inspection.')
    prefix=sfos[0][:-len('sce_sys/param.sfo')]
    if any(not n.startswith(prefix) for n in files):raise ServiceError('The decrypted ZIP contains files outside its save folder.')
    result={n[len(prefix):]:v for n,v in files.items()}
    candidates=[n for n,v in result.items() if not n.lower().startswith('sce_sys/') and (v[:4]==bytes.fromhex('3dca1200') or PurePosixPath(n).name.lower()=='ue4savegame.ps4.sav')]
    if len(candidates)!=1:raise ServiceError('Could not identify a single Dead Island 2 game-data file. The downloaded ZIP has been kept for inspection.')
    return result,candidates[0]

def validate_identity(files,account,title):
    raw=files['sce_sys/param.sfo']
    try:
        magic,version,keys,data,count=struct.unpack_from('<4sIIII',raw)
        if magic!=b'\0PSF' or not 0<count<=256 or not 20+16*count<=keys<=data<=len(raw):raise ValueError()
        fields={}
        for i in range(count):
            k,fmt,length,maximum,offset=struct.unpack_from('<HHIII',raw,20+16*i)
            start=keys+k;end=raw.index(b'\0',start,data)
            if start<keys or length>maximum or data+offset+length>len(raw):raise ValueError()
            name=raw[start:end].decode('ascii');fields[name]=raw[data+offset:data+offset+length]
        actual_title=fields['TITLE_ID'].rstrip(b'\0').decode('ascii')
        aid=fields['ACCOUNT_ID']
        if len(aid)!=8:raise ValueError()
        actual_account=f'{int.from_bytes(aid,"little"):016x}'
    except (ValueError,KeyError,struct.error,UnicodeError):raise ServiceError('The decrypted param.sfo account/game metadata could not be validated. The result ZIP is retained for inspection.') from None
    if actual_title!=title or actual_account!=account:raise ServiceError('The decrypted metadata identifies a different PSN account or game. The result ZIP is retained; Workshop did not open or re-encrypt it.')

def encrypted_files(files,account,title):
    found=[n for n in files if PurePosixPath(n).name=='DeadIsland2SaveGame']
    if len(found)!=1 or found[0]+'.bin' not in files:raise ServiceError('The encrypted result did not contain one matching DeadIsland2SaveGame pair. The ZIP has been kept for inspection.')
    name=found[0];parts=PurePosixPath(name).parts
    if 'SAVEDATA' in parts:
        i=parts.index('SAVEDATA')
        if len(parts)<=i+2 or parts[i+1].lower()!=account or parts[i+2]!=title:raise ServiceError('The result folder identifies a different account or game. Workshop did not prepare it for USB copying.')
    validate_pair(files[name],files[name+'.bin'])
    base='PS4/SAVEDATA/'+account+'/'+title+'/'
    return {base+'DeadIsland2SaveGame':files[name],base+'DeadIsland2SaveGame.bin':files[name+'.bin']}

class Client:
    def __init__(self,key):
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,256}',key.strip()):raise ServiceError('Enter the worker key issued by GarlicSaves.')
        self.key=key.strip();self.opener=request.build_opener(NoRedirect())
    def call(self,path,data=None,ctype=None,binary=False):
        if not re.fullmatch(r'/jobs(?:/[A-Za-z0-9_-]{1,100}(?:/result)?)?',path):raise ServiceError('Invalid service endpoint.')
        headers={'X-Worker-Key':self.key,'Accept':'application/zip' if binary else 'application/json','User-Agent':'DeadIsland2Workshop'}
        if ctype:headers['Content-Type']=ctype
        req=request.Request(BASE+path,data=data,headers=headers)
        try:
            with self.opener.open(req,timeout=60) as response:
                raw=response.read((LIMIT if binary else 1024*1024)+1)
                if len(raw)>(LIMIT if binary else 1024*1024):raise ServiceError('Service response exceeds the size limit.')
                return raw if binary else json.loads(raw)
        except error.HTTPError as e:
            if e.code in (401,403):raise ServiceError('GarlicSaves rejected this worker key. Check the key and that it is active.') from None
            if e.code==429:raise ServiceError('GarlicSaves is busy or rate-limiting requests. Please try later.') from None
            raise ServiceError('GarlicSaves returned HTTP '+str(e.code)+'. Check the job on the GarlicSaves website.') from None
        except (error.URLError,TimeoutError,OSError):raise ServiceError('Could not reach GarlicSaves. Check your internet connection and service availability.') from None
        except (ValueError,UnicodeError):raise ServiceError('GarlicSaves returned an unexpected response.') from None
    def test(self):
        value=self.call('/jobs')
        if not isinstance(value,list):raise ServiceError('Unexpected connection-test response.')
        return {'message':'Connected to GarlicSaves. The worker key was accepted. No save files were sent.'}
    def submit(self,operation,files,account=None):
        boundary='Workshop'+uuid.uuid4().hex;chunks=[]
        fields={'operation':operation}
        if operation=='decrypt':fields['include_sce_sys']='true'
        elif operation=='encrypt':fields['account_id']=account
        else:raise ServiceError('Unsupported operation.')
        for name,value in fields.items():chunks.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+name+'"\r\n\r\n'+str(value)+'\r\n').encode())
        for name,raw in files:
            if not re.fullmatch(r'[A-Za-z0-9._-]+',name):raise ServiceError('Invalid upload filename.')
            chunks.extend([('--'+boundary+'\r\nContent-Disposition: form-data; name="files"; filename="'+name+'"\r\nContent-Type: application/octet-stream\r\n\r\n').encode(),raw,b'\r\n'])
        chunks.append(('--'+boundary+'--\r\n').encode());data=b''.join(chunks)
        if len(data)>LIMIT+1048576:raise ServiceError('Upload exceeds the size limit.')
        result=self.call('/jobs',data,'multipart/form-data; boundary='+boundary)
        job=result.get('job_id') if isinstance(result,dict) else None
        if not isinstance(job,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',job):raise ServiceError('GarlicSaves did not return a valid job ID. Check the website before retrying.')
        return job
    def result(self,job,progress):
        deadline=time.monotonic()+1800
        while True:
            value=self.call('/jobs/'+job);state=value.get('status') if isinstance(value,dict) else None
            if state=='done':return self.call('/jobs/'+job+'/result',binary=True)
            if state=='failed':raise ServiceError('GarlicSaves reported that the job failed. View its details on the GarlicSaves website. Job: '+job)
            if state not in ('queued','running'):raise ServiceError('Unexpected job status. Check GarlicSaves. Job: '+job)
            progress('GarlicSaves job '+state+'. Keep Workshop open. Job: '+job)
            if time.monotonic()>=deadline:raise ServiceError('Stopped waiting after 30 minutes. The remote job may still finish; check GarlicSaves before retrying. Job: '+job)
            time.sleep(5)

class Manager:
    def __init__(self):
        self.client=None;self.state={'status':'idle','message':'Enter your worker key and test the connection.'};self.lock=threading.Lock();self.session=None;self.folder=None;self.context=None;self.running=False
    def view(self):
        with self.lock:return dict(self.state,has_key=self.client is not None,has_session=self.session is not None,has_folder=self.folder is not None,account_id=(self.context or {}).get('account_id'),title_id=(self.context or {}).get('title_id'))
    def message(self,text):
        with self.lock:self.state['message']=text
    def set_key(self,key):
        if self.running:raise ServiceError('Wait for the current service operation to finish.')
        self.client=Client(key) if key else None
        return self.view()
    def start(self,operation,task):
        with self.lock:
            if self.running:raise ServiceError('A service operation is already running.')
            if self.client is None:raise ServiceError('Enter your GarlicSaves worker key first.')
            self.running=True;self.state={'status':'working','operation':operation,'message':'Connecting to GarlicSaves…'};client=self.client
        def worker():
            try:
                result=task(client)
                with self.lock:self.state={'status':'done','operation':operation,**result}
            except Exception as e:
                # Never expose unexpected exception text: it could contain credentials.
                message=str(e) if isinstance(e,(ServiceError,backup_storage.BackupError)) else 'The operation could not finish. Your original files are unchanged. Downloaded results, if any, are retained in the service folder.'
                with self.lock:self.state={'status':'error','operation':operation,'message':message.replace(client.key,'[redacted]')}
            finally:
                with self.lock:self.running=False
        threading.Thread(target=worker,daemon=True).start();return self.view()
    def test(self):return self.start('test',lambda c:c.test())
    def decrypt(self,entry):
        # Read and back up originals before any network submission. Do not modify USB.
        def task(c):
            a=Path(entry['path']);b=Path(entry['bin_path'])
            if a.is_symlink() or b.is_symlink() or a.stat().st_size>LIMIT or b.stat().st_size!=96:raise ServiceError('The selected PS4 pair changed or is invalid. Refresh the USB list.')
            raw=a.read_bytes();sealed=b.read_bytes();validate_pair(raw,sealed)
            root=backup_storage.folder().parent/'ServiceSessions'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex)
            root.mkdir(parents=True,mode=0o700)
            originals={'PS4/SAVEDATA/'+entry['account_id']+'/'+entry['title_id']+'/DeadIsland2SaveGame':raw,'PS4/SAVEDATA/'+entry['account_id']+'/'+entry['title_id']+'/DeadIsland2SaveGame.bin':sealed}
            write_new(root/'Original-Encrypted-Pair.zip',make_zip(originals));self.folder=root
            for data,name in ((raw,a.name),(sealed,b.name)):backup_storage.snapshot(data,'opened',name)
            job=c.submit('decrypt',[('DeadIsland2SaveGame',raw),('DeadIsland2SaveGame.bin',sealed)])
            write_new(root/'decrypt-job.json',json.dumps({'job_id':job,'account_id':entry['account_id'],'title_id':entry['title_id']}).encode())
            result=c.result(job,self.message);write_new(root/'Decrypted-Result.zip',result)
            files,name=decrypted_files(unpack(result));validate_identity(files,entry['account_id'],entry['title_id'])
            from save_core import Save,FormatError
            try:
                save=Save(files[name])
                if save.rebuild({})!=files[name]:raise FormatError('Round-trip mismatch')
            except (FormatError,ValueError,IndexError,UnicodeError):raise ServiceError('Decryption finished, but this game-data format is not supported yet. The complete result ZIP is saved in the service folder. It has not been converted or modified.') from None
            # Opening is a separate explicit action so existing staged edits are retained.
            self.session={'files':files,'name':name,'root':root};self.context=dict(entry)
            return {'message':'Decrypted and validated. Click Open Decrypted Save to begin editing.','job_id':job}
        if not re.fullmatch('[0-9a-f]{16}',entry.get('account_id','')) or entry.get('title_id') not in ('CUSA01014','CUSA27043','CUSA35681'):raise ServiceError('Choose a known Dead Island 2 PS4 save from USB.')
        return self.start('decrypt',task)
    def encrypt(self,raw):
        session=self.session;context=self.context
        if session is None or not context:raise ServiceError('Decrypt and open a save through GarlicSaves first.')
        validate_identity(session['files'],context['account_id'],context['title_id'])
        from save_core import Save
        save=Save(raw)
        if save.rebuild({})!=raw:raise ServiceError('Edited game data did not pass validation.')
        def task(c):
            folder=session['root']/('Encrypted-'+uuid.uuid4().hex);folder.mkdir();self.folder=folder
            files=dict(session['files']);files[session['name']]=raw
            package=make_zip(files);write_new(folder/'Edited-Decrypted-Package.zip',package)
            backup_storage.snapshot(raw,'exported',PurePosixPath(session['name']).name)
            job=c.submit('encrypt',[('decrypted_save.zip',package)],context['account_id'])
            write_new(folder/'encrypt-job.json',json.dumps({'job_id':job,'account_id':context['account_id'],'title_id':context['title_id']}).encode())
            result=c.result(job,self.message);write_new(folder/'Encrypted-Result.zip',result)
            pair=encrypted_files(unpack(result),context['account_id'],context['title_id'])
            for name,data in pair.items():write_new(folder/name,data)
            write_new(folder/'Ready-For-USB.zip',make_zip(pair))
            return {'message':'Encrypted pair downloaded into a separate PS4 folder. Open the result folder and copy its PS4 folder to a spare USB drive for a console test. Original saves were preserved.','job_id':job}
        return self.start('encrypt',task)
