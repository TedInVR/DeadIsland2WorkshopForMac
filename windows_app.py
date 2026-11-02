"""Windows desktop shell for the shared Workshop editor (WebView2 / pywebview)."""
import json,os,sys,threading,uuid,webbrowser
from pathlib import Path
import server
from save_core import Save
import backup_storage
import save_browser
import subprocess

ROOT=Path(__file__).resolve().parent
RELEASES='https://github.com/TedInVR/DeadIsland2WorkshopForMac/releases/latest'

def version():
    import plistlib
    with (ROOT/'Info.plist').open('rb') as f:return plistlib.load(f)['CFBundleShortVersionString']

class DesktopAPI:
    def __init__(self,webview):
        self._webview=webview;self._window=None;self._sources=set();self._exporting=False
    def _bind(self,window):self._window=window
    def open_save(self):
        try:
            paths=self._window.create_file_dialog(self._webview.FileDialog.OPEN,allow_multiple=False,file_types=('Save files (*.sav;*.dat)','All files (*.*)'))
            if not paths:return None
            path=Path(paths[0] if isinstance(paths,(list,tuple)) else paths)
            if path.stat().st_size>server.MAX:raise ValueError('Save exceeds 128 MB')
            raw=path.read_bytes();info=server.app.open_save(raw,path.name,path)
            self._sources.add(str(path.resolve()).casefold())
            return {'name':path.name,'data':info}
        except Exception as e:return {'error':str(e)}
    def export_save(self,name):
        if self._exporting:return {'error':'An export is already in progress.'}
        self._exporting=True
        try:
            if server.app.output is None:raise ValueError('Validate the edited save before exporting.')
            # The page supplies a suggested basename only; all paths come from the native dialog.
            name=Path(str(name).replace('\\','/')).name
            chosen=self._window.create_file_dialog(self._webview.FileDialog.SAVE,save_filename=name,file_types=('Save files (*.sav)','All files (*.*)'))
            if not chosen:return {'message':'Export canceled. Edits are still staged.'}
            path=Path(chosen[0] if isinstance(chosen,(tuple,list)) else chosen)
            if backup_storage.protects(path):raise ValueError('Choose another folder. Automatic backups cannot be overwritten.')
            if str(path.resolve()).casefold() in self._sources|server.app.source_paths:raise ValueError('Choose another filename. The original save cannot be overwritten.')
            temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
            try:temporary.write_bytes(server.app.output);os.replace(temporary,path)
            finally:temporary.unlink(missing_ok=True)
            return {'message':'Saved '+path.name+'. Import this edited copy through Save Wizard or a compatible PS4 container workflow.'}
        except Exception as e:return {'error':str(e)}
        finally:self._exporting=False
    def reveal_save(self,key):
        try:
            entry=save_browser.find_save(key);subprocess.Popen(['explorer.exe','/select,'+entry['path']]);return {'message':'Save folder opened.'}
        except (OSError,save_browser.BrowserError) as e:return {'error':str(e)}
    def open_backups(self):
        try:
            directory=backup_storage.folder();directory.mkdir(parents=True,exist_ok=True);os.startfile(directory)
            return {'message':'Backup folder opened.'}
        except OSError as e:return {'error':str(e)}
    def _closing(self):
        if self._exporting:return False
        try:
            dirty=self._window.evaluate_js('typeof ammoDirty==="function" && (Object.keys(changes).length+additions.length+deletions.length+ammoDirty())')
            if dirty:return self._window.create_confirmation_dialog('Quit Workshop?','Unexported edits are kept only in memory. Quit and discard them?')
        except Exception:
            pass # Permit closing if the local page never finished starting.
        return True

def self_test():
    assert len(server.ROOT.joinpath('catalog.json').read_bytes())>1000
    assert '<html' in server.ROOT.joinpath('index.html').read_text(encoding='utf-8')
    assert version()
    result=json.dumps({'status':'ok','version':version(),'catalog_weapons':len(__import__('save_core').CATALOG['weapons'])})
    if '--self-test' in sys.argv and len(sys.argv)>sys.argv.index('--self-test')+1:Path(sys.argv[sys.argv.index('--self-test')+1]).write_text(result)
    elif sys.stdout is not None:print(result)


def main():
    if '--self-test' in sys.argv:self_test();return
    if sys.platform!='win32':raise SystemExit('This launcher is for Windows. Use Install.command on macOS.')
    import webview
    from webview.menu import Menu,MenuAction,MenuSeparator
    server.DESKTOP_EVAL=True
    http=server.HTTPServer(('127.0.0.1',0),server.Handler)
    threading.Thread(target=http.serve_forever,daemon=True).start()
    api=DesktopAPI(webview)
    def js(code):api._window.evaluate_js(code)
    def guide():webbrowser.open((ROOT/'User-Guide.html').as_uri())
    def updates():webbrowser.open(RELEASES)
    def about():api._window.create_confirmation_dialog('Dead Island 2 Workshop '+version(),'Windows preview. Edits decrypted PS4 saves. In-game effects of experimental edits still require testing.')
    menus=[Menu('File',[MenuAction('Browse USB Saves…',lambda:js('openUSB()')),MenuAction('Open Decrypted Save…',lambda:js('openSave()')),MenuAction('Create Weapon…',lambda:js('openCreate()')),MenuAction('Duplicate Selected Weapon…',lambda:js('openDuplicate()')),MenuAction('Reserve Ammo…',lambda:js('openAmmo()')),MenuAction('Review & Export Copy…',lambda:js('review()')),MenuSeparator(),MenuAction('Quit',lambda:api._window.destroy())]),Menu('Help',[MenuAction('Open Backup Folder',api.open_backups),MenuAction('User Guide',guide),MenuAction('Check for Updates…',updates),MenuAction('About Workshop',about)])]
    window=webview.create_window('Dead Island 2 Workshop',url='http://127.0.0.1:'+str(http.server_port)+'/'+server.token+'/',js_api=api,width=1220,height=850,min_size=(900,650),background_color='#101618',menu=menus)
    api._bind(window);window.events.closing+=api._closing
    profile=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Dead Island 2 Workshop'/'WebView2'
    try:webview.start(gui='edgechromium',storage_path=str(profile),private_mode=False)
    finally:http.shutdown();http.server_close()

if __name__=='__main__':
    try:main()
    except Exception as e:
        if sys.platform=='win32' and '--self-test' not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(e)+'\n\nWindows requires Microsoft Edge WebView2 Runtime.','Workshop could not start',0x10)
        raise
