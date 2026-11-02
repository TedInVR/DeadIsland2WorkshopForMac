# Dead Island 2 Workshop — Windows preview

Windows 10/11 x64. Uses the same save reader, editor, catalog, duplication, batch-perk tools, durability/reserve-ammo controls, and silhouette UI as the Mac app. Works with **decrypted PS4 game-data saves**; this is not a PC-game-save converter.

## Download and install

1. Download **Dead-Island-2-Workshop-Windows-Latest.zip** from [GitHub Releases](https://github.com/TedInVR/DeadIsland2WorkshopForMac/releases/latest).
2. Right-click the ZIP and choose **Extract All**.
3. In the extracted folder, double-click **Install-Windows.cmd**. It installs under your own LocalAppData Programs folder and creates Desktop and Start menu shortcuts. No administrator access or separate Python installation is needed for the packaged app.

Alternatively, run **Dead Island 2 Workshop.exe** inside the extracted **Dead Island 2 Workshop** folder for portable use. Keep that folder's `_internal` files beside the executable.

The app uses Microsoft Edge WebView2 Runtime. Windows normally already has it; if startup reports that it is missing, install the [Microsoft Evergreen WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). This preview is not code-signed, so Windows may display an unknown-publisher warning.

## Use

**USB Saves…** finds PS4 Dead Island 2 saves on connected removable/fixed drive roots. Edit profile names in that list or import your private JSON mappings; names stay on this computer and the PS4 folders stay unchanged. Encrypted pairs are listed but still need a separate decryption workflow.

Open the decrypted save exported by Save Wizard, make edits, then Review & Export Copy. Every successful open and every validated export creates a dated full-file backup under `%LOCALAPPDATA%\Dead Island 2 Workshop\Backups`; Help → Open Backup Folder opens it. Backups accumulate without automatic deletion or overwrite. Windows uses native Open/Save dialogs and prevents overwriting a save opened during this session. Exported files still need to be imported into a valid PS4 save container through Save Wizard or another compatible external workflow. The shared [user guide](USER_GUIDE.md) explains editing features.

**Help → Check for Updates** opens the latest GitHub release. Download, extract, quit the app, and run the new Windows installer to update the same shortcuts. Windows background automatic installation is not included in this first preview; the existing Mac updater remains available.

The Windows build is made on a Windows GitHub Actions runner. Bundled-executable and file-operation checks do not replace a real interactive test on a Windows PC or in-game testing on PS4.

## Run or build from source

Install Python 3.11 x64, then run:

```powershell
python -m pip install -r requirements-windows.txt
python windows_app.py
```

To build the self-contained distribution on Windows:

```powershell
python build_windows.py
```

The `Build Windows app` GitHub Actions workflow performs the build, smoke-tests the executable, and publishes versioned/latest ZIPs plus SHA-256 checksums as release assets. No personal saves are included.
