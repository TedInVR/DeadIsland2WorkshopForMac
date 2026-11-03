"""Opt-in GarlicSaves API client. Credentials are stored privately in the operating system credential store."""
import hashlib,io,json,os,re,stat,struct,threading,time,uuid,zipfile
from pathlib import Path,PurePosixPath
from urllib import request,error
import backup_storage
import credential_store
import ps4_backups

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
                name=entry.orig_filename;p=PurePosixPath(name)
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

def editable_file(files):
    candidates=[n for n in files if not n.lower().startswith('sce_sys/') and (PurePosixPath(n).name.lower()=='ue4savegame.ps4.sav' or files[n][:4]==bytes.fromhex('3dca1200'))]
    if len(candidates)!=1:return None,'Workshop could not identify one Dead Island 2 data file.'
    name=candidates[0]
    from save_core import Save,FormatError
    try:
        if Save(files[name]).rebuild({})!=files[name]:return None,'The no-edit validation did not match the downloaded data.'
        return name,None
    except (FormatError,ValueError,IndexError,UnicodeError) as e:return None,str(e)


def package_files(files):
    names=[n for n,v in files.items() if n.endswith('sce_sys/param.sfo') and v.startswith(b'\0PSF')]
    if len(names)!=1:raise ServiceError('Choose a ZIP containing exactly one complete decrypted save with sce_sys/param.sfo.')
    prefix=names[0][:-len('sce_sys/param.sfo')]
    if any(not n.startswith(prefix) for n in files):raise ServiceError('The ZIP contains files outside the selected save folder.')
    return {n[len(prefix):]:v for n,v in files.items()}

def package_identity(files):
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
    return actual_account,actual_title

def validate_identity(files,account,title):
    if package_identity(files)!=(account,title):raise ServiceError('The decrypted metadata identifies a different PSN account or game. The result ZIP is retained; Workshop did not open or re-encrypt it.')

def verified_encrypt(client,files,account,title,savename,folder,message):
    """Inspect the actual encrypted result through a fresh decrypt job before release.

    Some service workers reverse the account bytes. Retry only that exact,
    observed mismatch with the wire value reversed; never trust a folder name
    as proof of ownership. Both attempts must preserve the submitted game data.
    """
    package=make_zip(files)
    wire_account=account
    expected={n:v for n,v in files.items() if not n.lower().startswith('sce_sys/')}
    for attempt in (1,2):
        message('Uploading the validated save for re-encryption…' if attempt==1 else 'Correcting the service account byte order and re-encrypting…')
        job=client.submit('encrypt',[('decrypted_save.zip',package)],wire_account)
        write_new(folder/('encrypt-job.json' if attempt==1 else 'encrypt-retry-job.json'),json.dumps({'job_id':job,'account_id':account,'wire_account_id':wire_account,'title_id':title}).encode())
        result=client.result(job,message)
        write_new(folder/('Encrypted-Attempt-'+str(attempt)+'.zip'),result)
        pair=encrypted_files(unpack(result),account,title,savename)
        message('Verifying the encrypted result: checking the PSN account and saved edits…')
        check_job=client.submit('decrypt',[(PurePosixPath(n).name,v) for n,v in pair.items()])
        write_new(folder/('verification-job-'+str(attempt)+'.json'),json.dumps({'job_id':check_job,'encrypt_job_id':job}).encode())
        check=client.result(check_job,message)
        write_new(folder/('Verification-Decrypted-'+str(attempt)+'.zip'),check)
        checked=package_files(unpack(check))
        actual_account,actual_title=package_identity(checked)
        actual={n:v for n,v in checked.items() if not n.lower().startswith('sce_sys/')}
        if actual!=expected or checked.get('sce_sys/keystone')!=files.get('sce_sys/keystone'):
            raise ServiceError('The encrypted result did not preserve the submitted game data or keystone. Diagnostic results were retained; no USB-ready save was released.')
        if actual_title!=title:raise ServiceError('The encrypted result identifies a different game. Diagnostic results were retained; no USB-ready save was released.')
        if actual_account==account:
            write_new(folder/'Encrypted-Result.zip',result)
            write_new(folder/'Ownership-Verified.json',json.dumps({'account_id':account,'title_id':title,'encrypt_job_id':job,'verification_job_id':check_job,'package_sha256':hashlib.sha256(package).hexdigest(),'account_byte_order_corrected':attempt==2}).encode())
            return pair,job
        reversed_account=bytes.fromhex(account)[::-1].hex()
        if attempt==1 and actual_account==reversed_account:
            wire_account=reversed_account
            continue
        raise ServiceError('The encrypted result belongs to a different PSN account. Diagnostic results were retained; no USB-ready save was released.')

def encrypted_files(files,account,title,savename='DeadIsland2SaveGame'):
    found=[n for n in files if PurePosixPath(n).name==savename]
    if len(found)!=1 or found[0]+'.bin' not in files:raise ServiceError('The encrypted result did not contain one matching PS4 save pair. The ZIP has been kept for inspection.')
    name=found[0];parts=PurePosixPath(name).parts
    if 'SAVEDATA' in parts:
        i=parts.index('SAVEDATA')
        if len(parts)<=i+2 or parts[i+1].lower()!=account or parts[i+2]!=title:raise ServiceError('The result folder identifies a different account or game. Workshop did not prepare it for USB copying.')
    validate_pair(files[name],files[name+'.bin'])
    base='PS4/SAVEDATA/'+account+'/'+title+'/'
    return {base+savename:files[name],base+savename+'.bin':files[name+'.bin']}

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
        elif operation in ('encrypt','resign'):fields['account_id']=account
        else:raise ServiceError('Unsupported operation.')
        for name,value in fields.items():chunks.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+name+'"\r\n\r\n'+str(value)+'\r\n').encode())
        for name,raw in files:
            if not re.fullmatch(r'[A-Za-z0-9._ -]+',name):raise ServiceError('Invalid upload filename.')
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
    def __init__(self,store=None):
        self.store=store if store is not None else credential_store.default_store();self.key_loaded=False;self.key_saved=False;self.key_error=None
        self.client=None;self.state={'status':'idle','message':'Enter your worker key and test the connection.'};self.lock=threading.Lock();self.session=None;self.folder=None;self.context=None;self.running=False;self.results=[]
    def load_key(self):
        if self.key_loaded:return
        try:
            value=self.store.load()
            if value:self.client=Client(value);self.key_saved=True;self.state['message']='Saved worker key loaded. You can decrypt a USB save or test the connection.'
            self.key_loaded=True;self.key_error=None
        except (credential_store.CredentialError,ServiceError):
            self.key_error='The saved worker key could not be read. Allow secure credential-store access if prompted, then reopen this screen.'
    def view(self):
        if not self.running:self.load_key()
        with self.lock:return dict(self.state,key_saved=self.key_saved,key_error=self.key_error,has_key=self.client is not None,has_session=self.session is not None,has_folder=self.folder is not None,editable=bool(self.session and self.session.get('name')),result_count=len(self.results),account_id=(self.context or {}).get('account_id'),title_id=(self.context or {}).get('title_id'))
    def message(self,text):
        with self.lock:self.state['message']=text
    def set_key(self,key):
        if self.running:raise ServiceError('Wait for the current service operation to finish.')
        client=Client(key) if key else None
        # Save/delete first; a denied OS operation must not replace a working key.
        if client:self.store.save(client.key)
        else:self.store.delete()
        self.client=client;self.key_loaded=True;self.key_saved=client is not None;self.key_error=None
        self.state={'status':'idle','message':'Worker key saved securely on this computer. It will load automatically next time.' if client else 'Saved worker key removed from this computer.'}
        return self.view()
    def start(self,operation,task):
        if not self.running:self.load_key()
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
                message=str(e) if isinstance(e,(ServiceError,backup_storage.BackupError,ps4_backups.BackupError)) else 'The operation could not finish. Your original files are unchanged. Downloaded results, if any, are retained in the service folder.'
                with self.lock:self.state={'status':'error','operation':operation,'message':message.replace(client.key,'[redacted]')}
            finally:
                with self.lock:self.running=False
        threading.Thread(target=worker,daemon=True).start();return self.view()
    def test(self):return self.start('test',lambda c:c.test())
    def decrypt(self,entry):
        entry=dict(entry);entry.setdefault('filename',Path(entry['path']).name)
        # Read and back up originals before any network submission. Do not modify USB.
        def task(c):
            a=Path(entry['path']);b=Path(entry['bin_path'])
            if a.is_symlink() or b.is_symlink() or a.stat().st_size>LIMIT or b.stat().st_size!=96:raise ServiceError('The selected PS4 pair changed or is invalid. Refresh the USB list.')
            raw=a.read_bytes();sealed=b.read_bytes();validate_pair(raw,sealed)
            root=backup_storage.folder().parent/'ServiceSessions'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex)
            root.mkdir(parents=True,mode=0o700)
            originals={'PS4/SAVEDATA/'+entry['account_id']+'/'+entry['title_id']+'/'+entry['filename']:raw,'PS4/SAVEDATA/'+entry['account_id']+'/'+entry['title_id']+'/'+entry['filename']+'.bin':sealed}
            write_new(root/'Original-Encrypted-Pair.zip',make_zip(originals));self.folder=root
            for data,name in ((raw,a.name),(sealed,b.name)):backup_storage.snapshot(data,'opened',name)
            job=c.submit('decrypt',[(entry['filename'],raw),(entry['filename']+'.bin',sealed)])
            write_new(root/'decrypt-job.json',json.dumps({'job_id':job,'account_id':entry['account_id'],'title_id':entry['title_id'],'filename':entry['filename'],'drive_key':entry.get('drive_key'),'drive_root':entry.get('drive_root')}).encode())
            result=c.result(job,self.message);write_new(root/'Decrypted-Result.zip',result)
            files=package_files(unpack(result));validate_identity(files,entry['account_id'],entry['title_id']);name=None
            name,issue=editable_file(files)
            self.session={'files':files,'name':name,'root':root};self.context=dict(entry)
            return {'message':'Decrypted and validated. Click Open Decrypted Save to edit Dead Island 2.' if name else 'Decryption finished, but this save could not be opened for editing. '+issue+' The downloaded package is safe in Open Result Folder.','job_id':job}
        ps4_backups.identity(entry['account_id'],entry['title_id'],entry['filename'])
        return self.start('decrypt',task)
    def resume(self):
        if self.running:raise ServiceError('Wait for the current operation to finish.')
        root=backup_storage.folder().parent/'ServiceSessions'
        sessions=sorted((p for p in root.glob('*') if p.is_dir() and not p.is_symlink() and (p/'decrypt-job.json').is_file() and (p/'Decrypted-Result.zip').is_file()),key=lambda p:p.name,reverse=True)
        if not sessions:raise ServiceError('No previous decryption was found on this computer. Choose a USB save and decrypt it first.')
        for folder in sessions:
            try:return self._resume_folder(folder)
            except (ServiceError,OSError,ValueError,KeyError):continue
        raise ServiceError('No complete, editable decryption with matching account metadata was found. Your saved packages remain in the service folders.')
    def _resume_folder(self,folder):
        paths=[folder/n for n in ('decrypt-job.json','Decrypted-Result.zip','Original-Encrypted-Pair.zip')]
        if any(p.is_symlink() or not p.is_file() or p.stat().st_size>LIMIT for p in paths):raise ServiceError('The saved decryption is incomplete or too large.')
        meta=json.loads(paths[0].read_text());account=meta.get('account_id');title=meta.get('title_id')
        files=package_files(unpack(paths[1].read_bytes()));validate_identity(files,account,title)
        originals=unpack(paths[2].read_bytes());names=[n for n in originals if not n.endswith('.bin')]
        if len(names)!=1:raise ServiceError('The original save backup is not a single complete save.')
        filename=PurePosixPath(names[0]).name
        encrypted_files(originals,account,title,filename)
        finalized=[]
        for receipt in folder.glob('Encrypted-*/Finalized-USB.json'):
            try:finalized.append((receipt.stat().st_mtime_ns,receipt))
            except OSError:continue
        latest=None
        for stamp,receipt in sorted(finalized,reverse=True):
            if receipt.is_symlink() or receipt.parent.is_symlink():continue
            try:
                if receipt.stat().st_size>8192:continue
                record=json.loads(receipt.read_text());package=receipt.parent/'Edited-Decrypted-Package.zip'
                if package.is_symlink() or not package.is_file() or package.stat().st_size>LIMIT:continue
                package_raw=package.read_bytes()
                if record.get('package_sha256')!=hashlib.sha256(package_raw).hexdigest():continue
                candidate=package_files(unpack(package_raw));validate_identity(candidate,account,title)
                latest=(stamp,candidate,record);break
            except (OSError,ValueError,KeyError):continue
        if latest:
            files=latest[1];meta.update({k:latest[2].get(k) for k in ('drive_key','drive_root')})
        recovered=False
        # A previously submitted edited package is also recoverable when its
        # remote encryption failed. It is editor data, never proof of USB success.
        candidates=[]
        for package in folder.glob('Encrypted-*/Edited-Decrypted-Package.zip'):
            try:candidates.append((package.stat().st_mtime_ns,package))
            except OSError:continue
        for stamp,package in sorted(candidates,reverse=True):
            if package.is_symlink() or package.parent.is_symlink():continue
            try:
                if package.stat().st_size>LIMIT:continue
                candidate=package_files(unpack(package.read_bytes()));validate_identity(candidate,account,title)
                if candidate.get('sce_sys/keystone')!=files.get('sce_sys/keystone'):continue
                if not editable_file(candidate)[0]:continue
                recovered=candidate!=files;files=candidate;break
            except (OSError,ValueError,KeyError):continue
        name,issue=editable_file(files)
        if not name:raise ServiceError('The previous decryption could not be opened: '+issue)
        self.session={'files':files,'name':name,'root':folder};self.context={'account_id':account,'title_id':title,'filename':filename,'drive_key':meta.get('drive_key'),'drive_root':meta.get('drive_root')};self.folder=folder;self.results=[]
        self.state={'status':'done','operation':'decrypt','message':('Previously submitted edited package recovered and validated. Use Finalize and Re-encrypt to prepare it for USB.' if recovered else 'Previous decryption reopened and validated. No files were uploaded.')}
        return self.view()
    def finalize_info(self):
        import save_browser
        if self.running:raise ServiceError('Wait for the current operation to finish.')
        if self.session is None or not self.session.get('name') or not self.context:raise ServiceError('Open a complete decrypted USB save through PS4 Decrypt / Encrypt before finalizing. A standalone export cannot be re-encrypted by itself.')
        context=self.context;scan=save_browser.scan();account=context['account_id'];title=context['title_id'];name=context.get('filename','DeadIsland2SaveGame')
        ps4_backups.identity(account,title,name)
        matches={e['drive_key'] for e in scan['entries'] if e['account_id']==account and e['title_id']==title and e['filename']==name}
        keys={d['key'] for d in scan['drives']};preferred=context.get('drive_key')
        if preferred not in keys:preferred=next(iter(matches)) if len(matches)==1 else None
        return {'account_id':account,'profile_name':scan['profiles'].get(account,account),'title_id':title,'filename':name,'drives':scan['drives'],'preferred_drive':preferred,'relative_path':'PS4/SAVEDATA/'+account+'/'+title+'/'+name}

    def encrypt(self,raw=None,package=None,finalize_drive_key=None):
        session=self.session;context=self.context
        if session is None or not context:raise ServiceError('Decrypt and open a save through GarlicSaves first.')
        validate_identity(session['files'],context['account_id'],context['title_id'])
        files=dict(session['files']);drive=None;drive_identity=None
        if finalize_drive_key is not None:
            import save_browser
            if raw is None or package is not None:raise ServiceError('Finalize requires validated edits from the open save.')
            info=self.finalize_info()
            if finalize_drive_key not in {d['key'] for d in info['drives']}:raise ServiceError('Choose an available destination USB drive.')
            drive=save_browser.find_drive(finalize_drive_key);st=drive.stat();drive_identity=(str(drive.resolve()),st.st_dev,st.st_ino)
            ps4_backups.target_folder(drive,context['account_id'],context['title_id'],context.get('filename','DeadIsland2SaveGame'))
        if package is not None:
            files=package_files(unpack(package));validate_identity(files,context['account_id'],context['title_id'])
        elif raw is not None:
            if not session['name']:raise ServiceError('This decrypted game-data format cannot be edited here.')
            from save_core import Save
            save=Save(raw)
            if save.rebuild({})!=raw:raise ServiceError('Edited game data did not pass validation.')
            files[session['name']]=raw
        def task(c):
            if drive is not None:
                self.message('Backing up the current USB save before finalizing…')
                ps4_backups.destination_backup(drive,context['account_id'],context['title_id'],context.get('filename','DeadIsland2SaveGame'),'Before finalizing and re-encrypting '+context['title_id'])
            folder=session['root']/('Encrypted-'+uuid.uuid4().hex);folder.mkdir();self.folder=folder
            package=make_zip(files);write_new(folder/'Edited-Decrypted-Package.zip',package)
            if raw is not None:backup_storage.snapshot(raw,'exported',PurePosixPath(session['name']).name)
            pair,job=verified_encrypt(c,files,context['account_id'],context['title_id'],context.get('filename','DeadIsland2SaveGame'),folder,self.message)
            for name,data in pair.items():write_new(folder/name,data)
            write_new(folder/'Ready-For-USB.zip',make_zip(pair))
            if drive is not None:
                import save_browser
                self.message('Re-encryption finished. Backing up, writing and verifying the USB save…')
                try:
                    current=save_browser.find_drive(finalize_drive_key);st=current.stat()
                    if (str(current.resolve()),st.st_dev,st.st_ino)!=drive_identity:raise ServiceError('The destination USB drive was disconnected or changed. The re-encrypted result is retained in Open Result Folder; nothing was copied to a different drive.')
                    result=ps4_backups.install(current,context['account_id'],context['title_id'],context.get('filename','DeadIsland2SaveGame'),{Path(n).name:data for n,data in pair.items()},'Immediately before finalizing USB save '+context['title_id'])
                except (OSError,ValueError) as e:raise ServiceError(str(e)+' The re-encrypted result is retained in Open Result Folder.') from e
                # Adopt exactly the edited data that was installed, without removing originals.
                session['files']=files;self.context=dict(context,drive_key=finalize_drive_key,drive_root=str(current))
                receipt={'drive_key':finalize_drive_key,'drive_root':str(current),'account_id':context['account_id'],'title_id':context['title_id'],'filename':context.get('filename','DeadIsland2SaveGame'),'package_sha256':hashlib.sha256(package).hexdigest()}
                warning=''
                try:write_new(folder/'Finalized-USB.json',json.dumps(receipt).encode())
                except OSError:warning=' The local resume record could not be saved; the edited package remains in the result folder.'
                return {'message':'Saved to USB and verified. Safely eject the drive, then copy this save from USB to PS4 system storage before playing.'+warning,'installed':True,'destination':str(current/info['relative_path']),'backup':result['backup'],'job_id':job}
            return {'message':'Encrypted pair downloaded into a separate PS4 folder. Open the result folder and copy its PS4 folder to a spare USB drive for a console test. Original saves were preserved.','job_id':job}
        return self.start('finalize' if drive is not None else 'encrypt',task)

    def resign(self,entries,account):
        import save_browser
        if not ps4_backups.ACCOUNT.fullmatch(account):raise ServiceError('Choose a destination PSN profile.')
        if not entries or len(entries)>512:raise ServiceError('Choose between 1 and 512 saves.')
        if any(e['account_id']==account or e['kind']!='encrypted' for e in entries):raise ServiceError('Choose encrypted saves belonging to a different source account.')
        def task(c):
            self.results=[];root=backup_storage.folder().parent/'ServiceSessions'/('Resign-'+uuid.uuid4().hex);root.mkdir(parents=True);self.folder=root
            for index,e in enumerate(entries):
                self.message('Resigning save '+str(index+1)+' of '+str(len(entries))+': '+e['title_id']+' / '+e['filename'])
                drive=save_browser.find_drive(e['drive_key']);ps4_backups.capture(e,'Source before resigning to '+account)
                ps4_backups.destination_backup(drive,account,e['title_id'],e['filename'],'Destination before resigning '+e['title_id']+' / '+e['filename'])
                raw=ps4_backups.read_file(e['path']);sealed=ps4_backups.read_file(e['bin_path']);validate_pair(raw,sealed)
                job=c.submit('resign',[(e['filename'],raw),(e['filename']+'.bin',sealed)],account)
                folder=root/(str(index+1)+'-'+e['title_id']);folder.mkdir()
                write_new(folder/'resign-job.json',json.dumps({'job_id':job,'destination_account':account,'title_id':e['title_id'],'filename':e['filename']}).encode())
                result=c.result(job,self.message);write_new(folder/'Resigned-Result.zip',result)
                pair=encrypted_files(unpack(result),account,e['title_id'],e['filename'])
                for n,data in pair.items():write_new(folder/n,data)
                self.results.append(dict(drive_key=e['drive_key'],account_id=account,title_id=e['title_id'],filename=e['filename'],files={Path(n).name:data for n,data in pair.items()}))
            return {'message':str(len(self.results))+' resigned pairs are ready. Destination backups were saved. Click Install Resigned Copies to write them to the selected USB drive.'}
        return self.start('resign',task)
    def install_results(self):
        import save_browser
        if self.running or not self.results:raise ServiceError('Wait for a completed resign job first.')
        count=0
        for result in self.results:
            drive=save_browser.find_drive(result['drive_key']);ps4_backups.install(drive,result['account_id'],result['title_id'],result['filename'],result['files']);count+=1
        self.results=[]
        return {'message':str(count)+' resigned saves installed. Existing destination saves were backed up immediately before replacement.'}
