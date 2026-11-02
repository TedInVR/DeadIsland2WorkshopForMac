#!/usr/bin/env python3
import argparse,json,secrets,threading,time,sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from save_core import Save,FormatError
from urllib.parse import unquote
import backup_storage
import save_browser
ROOT=Path(__file__).resolve().parent
MAX=128*1024*1024
DESKTOP_EVAL=False
class App:
    def __init__(self): self.save=None;self.name='ue4savegame.ps4.sav';self.output=None;self.source_paths=set();self.selected_usb=None
    def open_save(self,raw,name='ue4savegame.ps4.sav',source_path=None):
        save=Save(raw)
        if save.rebuild({})!=raw:raise FormatError('No-edit validation failed')
        info=save.info();info['backup']=backup_storage.snapshot(raw,'opened',name)
        if source_path is not None:
            info['source_path']=str(Path(source_path).resolve());self.source_paths.add(str(Path(source_path).resolve()).casefold())
        self.save=save;self.output=None;self.name=name
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
        elif p=='saves':
            try:self.reply(200,save_browser.scan())
            except Exception as e:self.reply(400,{'error':str(e)})
        elif p=='export' and app.output is not None:self.reply(200,app.output,'application/octet-stream')
        else:self.reply(404,{'error':'Not found'})
    def do_POST(self):
        if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid host'})
        origin=self.headers.get('Origin')
        if origin and origin!='http://127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid origin'})
        p=self.endpoint()
        if p not in ('open','prepare','profile-name','import-profiles','open-found','select-found'):return self.reply(404,{'error':'Not found'})
        try:
            n=int(self.headers.get('Content-Length',0))
            if not 0<n<=MAX:raise ValueError('File is empty or larger than 128 MB')
            raw=self.rfile.read(n)
            if len(raw)!=n:raise ValueError('Upload was interrupted')
            if p in ('profile-name','import-profiles'):
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
                    changes=request["changes"];additions=request.get("additions",[]);deletions=request.get("deletions",[]);ammo_changes=request.get('ammo_changes',{})
                else:changes=request;additions=[];deletions=[];ammo_changes={}
                catalog={x['path'] for x in app.save.info()['catalog']}
                for key,c in changes.items():
                    if not isinstance(c,dict) or set(c)-{'level','rarity','perks','path','durability'}:raise ValueError('Unknown edit field')
                    if 'perks' in c and (not isinstance(c['perks'],list) or any(x not in catalog for x in c['perks'])):raise ValueError('Choose upgrades from this save’s catalog')
                app.output=None
                output=app.save.rebuild(changes,additions,deletions,ammo_changes)
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
