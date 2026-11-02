import AppKit
import WebKit
import Darwin

final class Workshop: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKUIDelegate, NSWindowDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var worker: Process?
    var ready: URL?
    var base: URL?
    var logHandle: FileHandle?
    var exporting = false
    var autoUpdateItem: NSMenuItem?
    var applicationLock: Int32 = -1
    var sourcePaths = Set<String>()
    let version = "0.6.0"
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let support = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Dead Island 2 Workshop", isDirectory: true)
        try? FileManager.default.createDirectory(at: support, withIntermediateDirectories: true)
        applicationLock = Darwin.open(support.appendingPathComponent("app-install.lock").path, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        if applicationLock < 0 || flock(applicationLock, LOCK_SH | LOCK_NB) != 0 {
            alert("An update is installing", "Workshop will remain closed until installation finishes. Please open it again in a moment.")
            NSApp.terminate(nil); return
        }
        makeMenus()
        let content = WKUserContentController()
        content.add(self, name: "workshop")
        let config = WKWebViewConfiguration(); config.userContentController = content
        web = WKWebView(frame: .zero, configuration: config); web.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0,y: 0,width: 1220,height: 850), styleMask: [.titled,.closable,.miniaturizable,.resizable], backing: .buffered, defer: false)
        window.title = "Dead Island 2 Workshop"
        window.minSize = NSSize(width: 860,height: 650)
        window.contentView = web; window.delegate = self
        window.center();window.makeKeyAndOrderFront(nil);NSApp.activate(ignoringOtherApps: true)
        startServer()
    }
    func makeMenus() {
        let bar = NSMenu(); NSApp.mainMenu = bar
        let appItem = NSMenuItem();bar.addItem(appItem);let app=NSMenu();appItem.submenu=app
        app.addItem(withTitle:"About Dead Island 2 Workshop", action:#selector(about), keyEquivalent:"").target=self
        app.addItem(NSMenuItem.separator())
        app.addItem(withTitle:"Quit Dead Island 2 Workshop", action:#selector(quitApp), keyEquivalent:"q").target=self
        let fileItem=NSMenuItem();bar.addItem(fileItem);let file=NSMenu(title:"File");fileItem.submenu=file
        file.addItem(withTitle:"Open Decrypted Save…", action:#selector(openFile), keyEquivalent:"o").target=self
        file.addItem(withTitle:"Review & Export Copy…", action:#selector(exportFile), keyEquivalent:"s").target=self
        file.addItem(withTitle:"Create Weapon…", action:#selector(createWeapon), keyEquivalent:"n").target=self
        file.addItem(NSMenuItem.separator())
        file.addItem(withTitle:"Close", action:#selector(closeWindow), keyEquivalent:"w").target=self
        let editItem=NSMenuItem();bar.addItem(editItem);let edit=NSMenu(title:"Edit");editItem.submenu=edit
        edit.addItem(withTitle:"Undo", action:Selector(("undo:")), keyEquivalent:"z")
        edit.addItem(withTitle:"Cut", action:#selector(NSText.cut(_:)), keyEquivalent:"x")
        edit.addItem(withTitle:"Copy", action:#selector(NSText.copy(_:)), keyEquivalent:"c")
        edit.addItem(withTitle:"Paste", action:#selector(NSText.paste(_:)), keyEquivalent:"v")
        edit.addItem(withTitle:"Select All", action:#selector(NSText.selectAll(_:)), keyEquivalent:"a")
        let helpItem=NSMenuItem();bar.addItem(helpItem);let help=NSMenu(title:"Help");helpItem.submenu=help
        help.addItem(withTitle:"User Guide", action:#selector(userGuide), keyEquivalent:"").target=self
        help.addItem(withTitle:"Using Workshop", action:#selector(helpText), keyEquivalent:"").target=self
        help.addItem(withTitle:"Keyboard Shortcuts", action:#selector(shortcuts), keyEquivalent:"").target=self
        help.addItem(withTitle:"Check for Updates…", action:#selector(updates), keyEquivalent:"").target=self
        help.addItem(withTitle:"Download Updates…", action:#selector(downloadUpdates), keyEquivalent:"").target=self
        let auto=help.addItem(withTitle:"Automatic Updates", action:#selector(toggleAutomaticUpdates), keyEquivalent:"");auto.target=self;auto.state=automaticUpdatesEnabled() ? .on : .off;autoUpdateItem=auto
        help.addItem(withTitle:"Save Encryption", action:#selector(encryptionInfo), keyEquivalent:"").target=self
    }
    @objc func about(){alert("Dead Island 2 Workshop \(version)","Independent Mac preview for decrypted PS4 Save Wizard exports. No affiliation with the game developer, Save Wizard, or SteffenL. Save format checks passed against your supplied file; PS4 in-game validation is still required.")}
    @objc func helpText(){alert("Using Workshop", "1. Open a copy of your decrypted PS4 export.\n2. Select a locker or carried inventory and a weapon.\n3. Adjust level, rarity, or perks. Copy/Paste Perk Set transfers upgrades between weapons.\n4. Review & Export creates a separate edited file.\n5. Import that file in Save Wizard on your PC, apply it, then test on PS4.\n\nKeep your original backup. Create Weapon adds a new catalog weapon to the selected character or shared locker. Replace Weapon switches an existing weapon to a catalog model in the same slot. Delete Weapon marks it for removal; Undo Delete restores it before export. Duplicate Weapon copies complete saved weapon state with fresh IDs. Slots after export shows capacity by location. Apply / Remove beside a perk opens scoped batch editing. Reserve Ammo edits existing reserve stacks, not loaded magazines. Melee durability is experimental. Separate combat-class overrides are not included. Profiles show actual slayer names and Regular/New Game Plus. The weapon and perk catalog combines published game identifiers with your opened save.")}
    @objc func shortcuts(){alert("Keyboard Shortcuts", "Command–O: Open save\nCommand–N: Create weapon\nCommand–S: Review and export\nCommand–W: Close window and quit\nCommand–Q: Quit\nCommand–C / V / X / A: Text editing\n\nKeyboard shortcuts are fixed in this preview.")}
    func automaticUpdatesEnabled() -> Bool {
        let path=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Dead Island 2 Workshop/settings.json")
        if let bytes=try? Data(contentsOf:path),let obj=(try? JSONSerialization.jsonObject(with:bytes)) as? [String:Any],let enabled=obj["automatic_updates"] as? Bool{return enabled}
        return true
    }
    @objc func userGuide(){
        if let path=Bundle.main.url(forResource:"User-Guide",withExtension:"html"){NSWorkspace.shared.open(path)}
        else{NSWorkspace.shared.open(URL(string:"https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/USER_GUIDE.md")!)}
    }
    @objc func encryptionInfo(){alert("PS4 Save Encryption", "Workshop edits the decrypted game-data file. It currently cannot decrypt or re-encrypt the PS4 USB save container. Continue using Save Wizard to export and import that file. No Save Wizard password or license key is stored in Workshop. Console-side homebrew alternatives require a separate compatible PS4 setup.")}
    @objc func downloadUpdates(){NSWorkspace.shared.open(URL(string:"https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true")!)}
    @objc func toggleAutomaticUpdates(){
        let enabled = !automaticUpdatesEnabled()
        runUpdater(enabled ? "--enable":"--disable"){obj in
            if let actual=obj["automatic_updates"] as? Bool{self.autoUpdateItem?.state=actual ? .on:.off}
            else{self.alert("Update preference",obj["message"] as? String ?? "The preference could not be saved.")}
        }
    }
    func runUpdater(_ argument:String,completion:@escaping ([String:Any])->Void){
        guard let resource=Bundle.main.resourceURL,let python=["/opt/homebrew/bin/python3","/usr/local/bin/python3","/usr/bin/python3"].first(where:{FileManager.default.isExecutableFile(atPath:$0)}) else{completion(["status":"error","message":"Python 3 was not found."]);return}
        DispatchQueue.global().async {
            let proc=Process(),pipe=Pipe();proc.executableURL=URL(fileURLWithPath:python);proc.arguments=[resource.appendingPathComponent("updater.py").path,argument];proc.standardOutput=pipe;proc.standardError=FileHandle.nullDevice
            var result:[String:Any]=["status":"error","message":"The update check could not finish."]
            do{try proc.run();let data=pipe.fileHandleForReading.readDataToEndOfFile();proc.waitUntilExit();if let obj=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any]{result=obj}}
            catch{result["message"]=error.localizedDescription}
            let final=result;DispatchQueue.main.async{completion(final)}
        }
    }
    @objc func updates(){
        runUpdater("--check"){obj in
            switch obj["status"] as? String {
            case "current":self.alert("You’re up to date", "Dead Island 2 Workshop "+self.version+" is the latest published version.")
            case "available":
                let a=NSAlert();a.messageText="An update is available";a.informativeText="Version "+(obj["version"] as? String ?? "")+"\n\nDownload now and install after Workshop closes? Installation will leave the app closed.";a.addButton(withTitle:"Download & Queue");a.addButton(withTitle:"Later")
                if a.runModal() == .alertFirstButtonReturn{self.runUpdater("--queue"){r in self.alert("Workshop Update",r["message"] as? String ?? "The update request has finished.")}}
            case "busy":self.alert("Update check in progress", "Another check is already running. Please try again shortly.")
            default:
                let a=NSAlert();a.messageText="Check for Updates";a.informativeText=(obj["message"] as? String ?? "Could not reach GitHub.")+"\n\nYou can download the latest installer using your signed-in GitHub browser.";a.addButton(withTitle:"Download in Browser");a.addButton(withTitle:"Close");if a.runModal() == .alertFirstButtonReturn{self.downloadUpdates()}
            }
        }
    }
    @objc func openFile(){web.evaluateJavaScript("window.openSave()",completionHandler:nil)}
    @objc func createWeapon(){web.evaluateJavaScript("window.createWeapon()",completionHandler:nil)}
    @objc func exportFile(){web.evaluateJavaScript("window.reviewSave()",completionHandler:nil)}
    @objc func closeWindow(){window.performClose(nil)}
    @objc func quitApp(){
        if exporting {alert("Export in progress", "Please wait until saving has finished before quitting.");return}
        web.evaluateJavaScript("Object.keys(changes).length+additions.length+deletions.length+ammoDirty()") { value, _ in
            if let count=value as? Int, count>0 {
                let a=NSAlert();a.messageText="Quit Workshop?";a.informativeText="Edits are kept in memory. If you have not exported them, they will be discarded.";a.addButton(withTitle:"Keep Editing");a.addButton(withTitle:"Quit")
                if a.runModal() != .alertSecondButtonReturn{return}
            }
            NSApp.terminate(nil)
        }
    }
    func windowShouldClose(_ sender: NSWindow)->Bool{quitApp();return false}
    func applicationWillTerminate(_ notification: Notification){worker?.terminate();if applicationLock >= 0 {flock(applicationLock, LOCK_UN);Darwin.close(applicationLock)};if let r=ready{try? FileManager.default.removeItem(at:r)};try? logHandle?.close()}
    func alert(_ title:String,_ message:String){let a=NSAlert();a.messageText=title;a.informativeText=message;a.addButton(withTitle:"OK");a.runModal()}
    func startServer(){
        guard let resources=Bundle.main.resourceURL else {alert("Unable to start","App resources are missing.");return}
        let candidates=["/opt/homebrew/bin/python3","/usr/local/bin/python3","/usr/bin/python3"]
        guard let python=candidates.first(where:{FileManager.default.isExecutableFile(atPath:$0)}) else {alert("Python 3 is needed", "Install Python 3 for macOS, then reopen Workshop. No Python packages are required.");return}
        let dir=FileManager.default.temporaryDirectory.appendingPathComponent("DI2Workshop-"+UUID().uuidString,isDirectory:true)
        do {
            try FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true)
            ready=dir.appendingPathComponent("ready.txt")
            let support=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Dead Island 2 Workshop",isDirectory:true)
            try FileManager.default.createDirectory(at:support,withIntermediateDirectories:true)
            let log=support.appendingPathComponent("startup.log")
            FileManager.default.createFile(atPath:log.path,contents:nil)
            logHandle=try FileHandle(forWritingTo:log)
            let p=Process();p.executableURL=URL(fileURLWithPath:python);p.arguments=[resources.appendingPathComponent("server.py").path,"--ready",ready!.path];p.standardOutput=logHandle;p.standardError=logHandle
            p.environment=ProcessInfo.processInfo.environment.merging(["PYTHONDONTWRITEBYTECODE":"1","PYTHONUNBUFFERED":"1"]){_,new in new}
            try p.run();worker=p
            let readyFile=ready!
            DispatchQueue.global().async {
                var address:String?=nil
                for _ in 0..<200 {
                    if let s=try? String(contentsOf:readyFile,encoding:.utf8),!s.isEmpty{address=s;break}
                    if !p.isRunning{break};Thread.sleep(forTimeInterval:0.05)
                }
                let result=address
                DispatchQueue.main.async {
                    if let s=result,let url=URL(string:s){self.base=url;self.web.load(URLRequest(url:url))}
                    else{self.alert("Workshop could not start", "Please send the startup log from:\n"+log.path+"\n\nThe original save has not been changed.")}
                }
            }
        }catch{alert("Workshop could not start",error.localizedDescription)}
    }
    func webView(_ webView:WKWebView,runOpenPanelWith parameters:WKOpenPanelParameters,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping ([URL]?)->Void){
        let p=NSOpenPanel();p.canChooseDirectories=false;p.canChooseFiles=true;p.allowsMultipleSelection=false;p.message="Choose your decrypted PS4 save exported from Save Wizard."
        p.beginSheetModal(for:window){r in if r == .OK, let url=p.url {self.sourcePaths.insert(url.resolvingSymlinksInPath().standardizedFileURL.path)};completionHandler(r == .OK ? p.urls:nil)}
    }
    func webView(_ webView:WKWebView,runJavaScriptConfirmPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping (Bool)->Void){let a=NSAlert();a.messageText=message;a.addButton(withTitle:"Continue");a.addButton(withTitle:"Cancel");completionHandler(a.runModal() == .alertFirstButtonReturn)}
    func userContentController(_ userContentController:WKUserContentController,didReceive message:WKScriptMessage){
        guard let body=message.body as? [String:Any], body["action"] as? String == "export",let base=base,!exporting else{return}
        let panel=NSSavePanel();panel.nameFieldStringValue=body["name"] as? String ?? "ue4savegame.ps4_Edited.sav";panel.message="Save a separate edited copy. Keep your original save backup.";panel.canCreateDirectories=true
        panel.beginSheetModal(for:window){r in
            guard r == .OK,let target=panel.url else{self.finish("Export canceled. Edits are still staged.");return}
            if self.sourcePaths.contains(target.resolvingSymlinksInPath().standardizedFileURL.path) {self.finish("Choose a different filename; the original save cannot be overwritten.",true);return}
            self.exporting=true
            URLSession.shared.dataTask(with:base.appendingPathComponent("export")){d,response,e in
                DispatchQueue.main.async{
                    defer{self.exporting=false}
                    guard e==nil,let bytes=d,(response as? HTTPURLResponse)?.statusCode==200 else{self.finish("Unable to export: "+(e?.localizedDescription ?? "No validated output"),true);return}
                    do{try bytes.write(to:target,options:.atomic);self.finish("Saved "+target.lastPathComponent+". Import this edited copy through Save Wizard on your PC.")}
                    catch{self.finish("Could not save: "+error.localizedDescription,true)}
                }
            }.resume()
        }
    }
    func finish(_ text:String,_ error:Bool=false){let arr:[Any]=[text,error];if let data=try? JSONSerialization.data(withJSONObject:arr),let json=String(data:data,encoding:.utf8){web.evaluateJavaScript("window.exportFinished.apply(null,"+json+")",completionHandler:nil)}}
}
let app=NSApplication.shared
let delegate=Workshop()
app.delegate=delegate
app.run()
