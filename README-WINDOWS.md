# Dead Island 2 Workshop — Windows preview

## First use, credits and risks

On first launch, read the Experimental Use Agreement, check the acknowledgment box and choose **I Agree & Continue**, or quit. Workshop stores only an acceptance flag, agreement version/hash and time locally; there is no registration or central user list. Ordinary updates remember acceptance. **Help → Usage Agreement & Risks** reopens the notice; **Help → Credits & Licenses** opens named credits, reference links and license boundaries.

Workshop is a free, independent experimental hobby project maintained by TedInVR with OpenAI ChatGPT/Codex assistance. Modified gameplay must remain offline. Users must follow applicable laws and platform, game and service terms. The notice explains save corruption, account/console bans, penalties and legal-action risks and limits warranties/liability only to the extent permitted by law. It cannot bind Sony or publishers, remove non-waivable rights, authorize prohibited activity or guarantee legal protection. Free/offline use is not itself legal clearance.

With appreciation to Sony/PlayStation, PLAION/Deep Silver/Dambuster/Fishlabs, the community and dependency authors. Workshop is not affiliated with or endorsed by them. See [the agreement](USAGE_TERMS.md), [credits](CREDITS.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [licensing review](LICENSING_REVIEW.md). The technical review identified no bundled Sony SDK, firmware or console keys; this is a limited review, not certification. Redistribution permission for the referenced catalog tables remains unverified. Attribution alone is not permission.

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

## Optional GarlicSaves connection preview

Click **PS4 Decrypt / Encrypt** to enter and securely save a worker key on this computer and test the connection. Decrypt a selected USB pair only after confirming upload to GarlicSaves. The app backs up the originals, preserves returned metadata, and can submit validated edits for encryption back to the source account. Results go into a separate PS4 folder. Live service output compatibility and PS4 import still need testing. See the shared User Guide for setup and limitations.

0.13.0 adds named PS4 backups/restore, all-game CUSA discovery, profile-to-profile and batch resigning, and DI2 Character & Resources. See USER_GUIDE.md for limits and destination backup behavior.
