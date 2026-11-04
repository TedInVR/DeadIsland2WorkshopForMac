#!/usr/bin/env python3
import argparse,json,secrets,threading,time,sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from save_core import Save,FormatError
from urllib.parse import unquote
import backup_storage
import save_browser
import legal_state
import preset_storage
import garlic_service
import ps4_backups
usb_busy=False
service=garlic_service.Manager()
ROOT=Path(__file__).resolve().parent
MAX=128*1024*1024
DESKTOP_EVAL=False
class App:
    def __init__(self): self.save=None;self.name='ue4savegame.ps4.sav';self.output=None;self.source_paths=set();self.selected_usb=None;self.service_session=None
    def open_save(self,raw,name='ue4savegame.ps4.sav',source_path=None):
        save=Save(raw)
        if save.rebuild({})!=raw:raise FormatError('No-edit validation failed')
        info=save.info();info['backup']=backup_storage.snapshot(raw,'opened',name)
        if source_path is not None:
            info['source_path']=str(Path(source_path).resolve());self.source_paths.add(str(Path(source_path).resolve()).casefold())
        self.save=save;self.output=None;self.name=name;self.service_session=None
        return info
app=App(); token=secrets.token_urlsafe(32)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,data,ctype='application/json'):
        if isinstance(data,(dict,list)):data=json.dumps(data).encode()
        if isinstance(data,str):data=data.encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'"+(" 'unsafe-eval'" if DESKTOP_EVAL else "")+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(data)
    def endpoint(self):
        if not self.path.startswith('/'+token+'/'):return None
        return self.path[len(token)+2:].split('?',1)[0]
    def do_GET(self):
        p=self.endpoint()
        if p=='':self.reply(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        elif p=='legal-status':self.reply(200,legal_state.status())
        elif p=='credits':self.reply(200,{'text':(ROOT/'CREDITS.md').read_text(encoding='utf-8')+'\n\n'+(ROOT/'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')})
        elif not legal_state.is_accepted():self.reply(403,{'error':'Read and acknowledge the first-use agreement first.'})
        elif p=='saves':
            try:self.reply(200,save_browser.scan())
            except Exception as e:self.reply(400,{'error':str(e)})
        elif p=='presets':
            try:self.reply(200,{'presets':preset_storage.list_presets(),'bindings':preset_storage.bindings()})
            except ValueError as e:self.reply(400,{'error':str(e)})
        elif p=='durability-references':
            try:self.reply(200,{'references':preset_storage.durability_references()})
            except ValueError as e:self.reply(400,{'error':str(e)})
        elif p=='named-backups':self.reply(200,{'backups':ps4_backups.list_backups()})
        elif p=='backup-folder':
            ps4_backups.root().mkdir(parents=True,exist_ok=True);self.reply(200,{'path':str(ps4_backups.root())})
        elif p=='finalize-info':
            try:
                if app.service_session is None or app.service_session is not service.session:raise ValueError('Open the decrypted USB result in this editor before finalizing.')
                self.reply(200,service.finalize_info())
            except ValueError as e:self.reply(400,{'error':str(e)})
        elif p=='service-status':self.reply(200,service.view())
        elif p=='service-folder':self.reply(200,{'path':str(service.folder) if service.folder else None})
        elif p=='export' and app.output is not None:self.reply(200,app.output,'application/octet-stream')
        else:self.reply(404,{'error':'Not found'})
    def do_POST(self):
        global usb_busy
        if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid host'})
        origin=self.headers.get('Origin')
        if origin and origin!='http://127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid origin'})
        p=self.endpoint()
        if p!='legal-accept' and not legal_state.is_accepted():return self.reply(403,{'error':'Read and acknowledge the first-use agreement first.'})
        if p not in ('legal-accept','durability-record','presets-save','presets-delete','presets-bind','open','prepare','profile-name','import-profiles','open-found','select-found','service-resume','service-key','service-test','service-decrypt','service-open','service-encrypt','service-finalize','service-encrypt-original','service-import-zip','service-resign','service-install','named-backup','restore-backup','open-backup'):return self.reply(404,{'error':'Not found'})
        try:
            n=int(self.headers.get('Content-Length',0))
            if not 0<n<=MAX:raise ValueError('File is empty or larger than 128 MB')
            raw=self.rfile.read(n)
            if len(raw)!=n:raise ValueError('Upload was interrupted')
            if p=='legal-accept':self.reply(200,legal_state.accept(json.loads(raw)))
            elif p=='durability-record':
                value=json.loads(raw);keys=value.get('keys')
                if app.save is None or value.get('confirm') is not True or not isinstance(keys,list) or not keys or len(keys)>10000 or any(type(k)!=int or not 0<=k<len(app.save.weapons) for k in keys):raise ValueError('Confirm that the selected weapons were fully repaired in-game before recording their current saved values.')
                items=[]
                for key in keys:
                    w=app.save.weapons[key];info=w.info()
                    if not info['editable'] or 'MeleeWeaponArchetype' not in w.path:raise ValueError('Only editable melee weapons have durability references.')
                    items.append({'id':w.id,'signature':info['durability_signature'],'maximum':info['durability']})
                self.reply(200,{'references':preset_storage.record_durability(items)})
            elif p=='presets-bind':self.reply(200,preset_storage.bind(json.loads(raw)))
            elif p=='presets-save':self.reply(200,preset_storage.save(json.loads(raw)))
            elif p=='presets-delete':self.reply(200,preset_storage.delete(json.loads(raw)))
            elif p in ('named-backup','restore-backup','open-backup'):
                value=json.loads(raw)
                if p=='named-backup':self.reply(200,ps4_backups.capture(save_browser.find_save(value.get('key')),value.get('name')))
                else:
                    meta,files=ps4_backups.retrieve(value.get('id'))
                    if p=='open-backup':
                        if meta['kind']!='decrypted':raise ValueError('Restore this encrypted backup to USB, then decrypt it through PS4 tools.')
                        self.reply(200,{'name':meta['filename'],'data':app.open_save(files[meta['filename']],meta['filename'])})
                    else:
                        if value.get('consent')is not True:raise ValueError('Confirm restoring this backup and replacing the USB destination.')
                        usb_busy=True
                        try:self.reply(200,ps4_backups.install(save_browser.find_drive(value.get('drive_key')),meta['account_id'],meta['title_id'],meta['filename'],files,'Automatic backup before restoring '+meta['name']))
                        finally:usb_busy=False
            elif p=='service-import-zip':
                if self.headers.get('X-Workshop-Consent')!='yes':raise ValueError('Confirm uploading this complete decrypted ZIP to GarlicSaves.')
                self.reply(200,service.encrypt(package=raw))
            elif p.startswith('service-'):
                value=json.loads(raw)
                if not isinstance(value,dict):raise ValueError('Invalid service request.')
                if p=='service-resume':self.reply(200,service.resume())
                elif p=='service-key':
                    if len(raw)>2048:raise ValueError('Worker key is too long.')
                    if not isinstance(value.get('key'),str):raise ValueError('Enter a worker key, or explicitly remove the saved key.')
                    self.reply(200,service.set_key(value.get('key')))
                elif p=='service-test':self.reply(200,service.test())
                elif p=='service-install':
                    if value.get('consent')is not True:raise ValueError('Confirm replacing the destination saves on USB.')
                    usb_busy=True
                    try:self.reply(200,service.install_results())
                    finally:usb_busy=False
                elif p=='service-resign':
                    if value.get('consent')is not True:raise ValueError('Confirm sending the selected saves to GarlicSaves for resigning.')
                    entry=save_browser.find_save(value.get('key'));entries=[entry]
                    if value.get('all')is True:entries=[e for e in save_browser.scan()['entries'] if e['account_id']==entry['account_id'] and e['drive_key']==entry['drive_key'] and e['kind']=='encrypted']
                    target=value.get('account_id')
                    known=set(save_browser.profile_names())|{e['account_id'] for e in save_browser.scan()['entries']}
                    if target not in known:raise ValueError('Choose an existing or named destination profile.')
                    self.reply(200,service.resign(entries,target))
                elif p=='service-encrypt-original':
                    if value.get('consent')is not True:raise ValueError('Confirm sending the complete decrypted package to GarlicSaves.')
                    self.reply(200,service.encrypt())
                elif p=='service-decrypt':
                    if value.get('consent') is not True:raise ValueError('Confirm sending this encrypted pair to GarlicSaves.')
                    entry=save_browser.find_save(value.get('key'))
                    if entry['kind']!='encrypted':raise ValueError('Choose a complete encrypted pair.')
                    for source in (entry['path'],entry['bin_path']):app.source_paths.add(str(Path(source).resolve()).casefold())
                    self.reply(200,service.decrypt(entry))
                elif p=='service-open':
                    if service.running or service.session is None:raise ValueError('Wait for a successful decryption first.')
                    session=service.session;name=session['name']
                    if not name:raise ValueError('This game-data format is not editable here. Use the generic PS4 package tools.')
                    info=app.open_save(session['files'][name],Path(name).name)
                    app.service_session=session
                    self.reply(200,{'data':info,'name':Path(name).name})
                else:
                    if value.get('consent') is not True:raise ValueError('Confirm sending this edited package to GarlicSaves.')
                    if app.service_session is None or app.service_session is not service.session:raise ValueError('Open the decrypted GarlicSaves result in this editor before encrypting it.')
                    if app.output is None:raise ValueError('Review and validate your edited save first.')
                    if p=='service-finalize' and not value.get('drive_key'):raise ValueError('Choose a destination USB drive before finalizing.')
                    self.reply(200,service.encrypt(app.output,finalize_drive_key=value.get('drive_key')) if p=='service-finalize' and value.get('drive_key') else service.encrypt(app.output))
            elif p in ('profile-name','import-profiles'):
                if len(raw)>65536:raise ValueError('Profile-name imports must be smaller than 64 KB.')
                value=json.loads(raw)
                if p=='profile-name':
                    if not isinstance(value,dict) or set(value)!={'account_id','name'}:raise ValueError('Choose a profile and name.')
                    value={value['account_id']:value['name']}
                self.reply(200,{'profiles':save_browser.import_names(value)})
            elif p in ('open-found','select-found'):
                request=json.loads(raw);entry=save_browser.find_save(request.get('key'))
                if p=='select-found':
                    if entry['kind']!='encrypted':raise ValueError('Choose a complete encrypted PS4 save pair.')
                    app.selected_usb=entry
                    for source in (entry['path'],entry['bin_path']):app.source_paths.add(str(Path(source).resolve()).casefold())
                    self.reply(200,{'selected':entry})
                else:
                    if entry['kind']!='decrypted':raise ValueError('This is an encrypted PS4 save pair. Decrypt it through a compatible external workflow first.')
                    path=Path(entry['path'])
                    if path.stat().st_size>MAX:raise ValueError('Save exceeds 128 MB.')
                    with path.open('rb') as f:raw=f.read(MAX+1)
                    if len(raw)>MAX:raise ValueError('Save exceeds 128 MB.')
                    info=app.open_save(raw,path.name,path);self.reply(200,{'name':path.name,'data':info})
            elif p=='open':
                self.reply(200,app.open_save(raw,unquote(self.headers.get('X-Workshop-Filename','ue4savegame.ps4.sav'))))
            else:
                if app.save is None:raise ValueError('Open a save first')
                request=json.loads(raw)
                if "changes" in request:
                    changes=request["changes"];additions=request.get("additions",[]);deletions=request.get("deletions",[]);ammo_changes=request.get('ammo_changes',{});resource_changes=request.get('resource_changes',[]);character_levels=request.get('character_levels',{});ammo_refills=request.get('ammo_refills',[]);story_resets=request.get('story_resets',[])
                else:changes=request;additions=[];deletions=[];ammo_changes={};resource_changes=[];character_levels={};ammo_refills=[];story_resets=[]
                catalog={x['path'] for x in app.save.info()['catalog']}
                for key,c in changes.items():
                    if not isinstance(c,dict) or set(c)-{'level','rarity','perks','path','durability','copy_source'}:raise ValueError('Unknown edit field')
                    if 'perks' in c and (not isinstance(c['perks'],list) or any(x not in catalog for x in c['perks'])):raise ValueError('Choose upgrades from this save’s catalog')
                app.output=None
                output=app.save.rebuild(changes,additions,deletions,ammo_changes,resource_changes,character_levels,ammo_refills,story_resets)
                backup=backup_storage.snapshot(output,'exported',app.name)
                app.output=output
                self.reply(200,{'bytes':len(app.output),'edited':len(changes),'created':len(additions),'deleted':len(deletions),'backup':backup})
        except Exception as e:
            self.reply(400,{'error':str(e) or type(e).__name__})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ready',required=True);args=parser.parse_args()
    server=HTTPServer(('127.0.0.1',0),Handler)
    Path(args.ready).write_text('http://127.0.0.1:'+str(server.server_port)+'/'+token+'/')
    server.serve_forever()
if __name__=='__main__': main()
