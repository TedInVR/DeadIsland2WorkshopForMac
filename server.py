#!/usr/bin/env python3
import argparse,json,secrets,threading,time,sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from save_core import Save,FormatError
ROOT=Path(__file__).resolve().parent
MAX=128*1024*1024
DESKTOP_EVAL=False
class App:
    def __init__(self): self.save=None;self.name='ue4savegame.ps4.sav';self.output=None
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
        elif p=='export' and app.output is not None:self.reply(200,app.output,'application/octet-stream')
        else:self.reply(404,{'error':'Not found'})
    def do_POST(self):
        if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid host'})
        origin=self.headers.get('Origin')
        if origin and origin!='http://127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Invalid origin'})
        p=self.endpoint()
        if p not in ('open','prepare'):return self.reply(404,{'error':'Not found'})
        try:
            n=int(self.headers.get('Content-Length',0))
            if not 0<n<=MAX:raise ValueError('File is empty or larger than 128 MB')
            raw=self.rfile.read(n)
            if len(raw)!=n:raise ValueError('Upload was interrupted')
            if p=='open':
                save=Save(raw)
                # Complete a no-edit serialization check before accepting a file.
                if save.rebuild({})!=raw:raise FormatError('No-edit validation failed')
                app.save=save;app.output=None
                self.reply(200,save.info())
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
                app.output=app.save.rebuild(changes,additions,deletions,ammo_changes)
                self.reply(200,{'bytes':len(app.output),'edited':len(changes),'created':len(additions),'deleted':len(deletions)})
        except Exception as e:
            self.reply(400,{'error':str(e) or type(e).__name__})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ready',required=True);args=parser.parse_args()
    server=HTTPServer(('127.0.0.1',0),Handler)
    Path(args.ready).write_text('http://127.0.0.1:'+str(server.server_port)+'/'+token+'/')
    server.serve_forever()
if __name__=='__main__': main()
