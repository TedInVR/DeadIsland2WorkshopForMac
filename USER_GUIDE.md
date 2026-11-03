# Dead Island 2 Workshop for Mac — User Guide

## Named mod and perk presets

Select the mods/perks you want, click **Save as Preset**, give the set a name and save it. In the weapon editor or Create/Replace/Duplicate dialog, choose a saved set from **Saved mod & perk presets**, then click **Apply Preset**. Applying a preset replaces that weapon's selected mod/perk set; other weapon settings remain unchanged. Presets are stored locally between launches, independently of opened saves and app updates. A duplicate name requires confirmation before replacement. **Delete Preset** removes the saved set without changing weapons already using it. If a preset includes upgrades unavailable in the current save's catalog, no changes are applied.

The replacement dialog uses **Done** to apply your selection in the editor. It does not write to the USB save: use **Review & Export** or **Encrypt Edited Copy** to save the edited copy. Top toolbar labels are shown in full without trailing dots; complete buttons wrap to additional rows and include descriptive hover help.

## First use, credits and risks

On first launch, read the Experimental Use Agreement, check the acknowledgment box and choose **I Agree & Continue**, or quit. Workshop stores only an acceptance flag, agreement version/hash and time locally; there is no registration or central user list. Ordinary updates remember acceptance. **Help → Usage Agreement & Risks** reopens the notice; **Help → Credits & Licenses** opens named credits, reference links and license boundaries.

Workshop is a free, independent experimental hobby project maintained by TedInVR with OpenAI ChatGPT/Codex assistance. Modified gameplay must remain offline. Users must follow applicable laws and platform, game and service terms. The notice explains save corruption, account/console bans, penalties and legal-action risks and limits warranties/liability only to the extent permitted by law. It cannot bind Sony or publishers, remove non-waivable rights, authorize prohibited activity or guarantee legal protection. Free/offline use is not itself legal clearance.

With appreciation to Sony/PlayStation, PLAION/Deep Silver/Dambuster/Fishlabs, the community and dependency authors. Workshop is not affiliated with or endorsed by them. See [the agreement](USAGE_TERMS.md), [credits](CREDITS.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [licensing review](LICENSING_REVIEW.md). The technical review identified no bundled Sony SDK, firmware or console keys; this is a limited review, not certification. Redistribution permission for the referenced catalog tables remains unverified. Attribution alone is not permission.

Workshop edits weapons inside a **decrypted PS4 Dead Island 2 save**, including compressed GarlicSaves results and uncompressed Save Wizard exports. Version 0.14.0 is a preview. Structural checks have passed; PS4 in-game testing remains necessary.

## Install or update

1. Download [the latest installer](https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true). For a private repository, sign into GitHub in your browser first.
2. Quit Workshop, then extract the ZIP.
3. Double-click **Install.command**.
4. The installer builds and opens **Dead Island 2 Workshop** in Applications. It updates the same app and retains source in **Applications / Dead Island 2 Workshop Development**.

macOS 12 or newer, Python 3.9–3.13, and Apple's Command Line Tools are required. Homebrew Python is used when available. The installer installs Zstandard and CityHash libraries into a private application runtime. No manual pip commands, Windows emulator, or third-party editor executable are required. A locally built app is ad-hoc signed, not notarized by Apple.

## Open your save

Keep an original PS4 backup. In Save Wizard's Advanced Mode, export the internal game-data file (typically `ue4savegame.ps4.sav`). Open that exported file with **Open Save** or **Command-O**. Workshop checks the save structure and verifies that saving without edits would reproduce the input exactly.

Workshop does not modify the file you open. Edits stay in memory until you export a separate copy. Closing without exporting discards them.

## Understand the location menu

| Location | Meaning |
| --- | --- |
| Shared storage locker — Regular | Weapons stored in the shared locker for regular play |
| Shared Unclaimed Property — Regular | The regular game's Unclaimed Property collection; not the Lost & Found quest list |
| Shared storage locker — New Game Plus | Separate shared locker for NG+ |
| Shared Unclaimed Property — New Game Plus | Separate Unclaimed Property collection for NG+ |
| Ryan, Carla, Jacob, Dani, Amy, or Bruno — Regular | That saved character's carried inventory in regular play |
| Character name — New Game Plus | That character's NG+ save and carried inventory |
| (active) | The character marked active in the opened save |

The first preview's Warrior/Berserker/Rogue labels were internal class metadata. Current versions show the actual slayer names and read NG+ status from the saved profile privileges. Empty legacy character-specific stash entries are not shown as shared lockers. Only character saves actually present in the file are listed.

## Windows edition

The Windows edition uses the same editing controls described here. Download the Windows ZIP from GitHub Releases, extract it, and run **Install-Windows.cmd**. Native file dialogs handle Open Save and exporting a separate copy. **Help → Check for Updates** opens release downloads; Windows does not yet have the Mac background installer. See [the Windows guide](https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/README-WINDOWS.md).

## Find saves on a USB drive

Choose **USB Saves…** in the toolbar or **File → Browse USB Saves…**. The home screen also shows connected-save counts. Workshop checks mounted drive roots for `PS4/SAVEDATA/<16-character account ID>/<game title ID>` without recursively searching the drive. Known Dead Island 2 title IDs checked are CUSA01014, CUSA27043, and CUSA35681. The list refreshes every 10 seconds while the app is visible, or immediately with **Refresh drives**.

Each row shows the profile label, account ID, drive, game ID, filename, size, modified date, and save type. Use **Show folder** to reveal it in Finder or File Explorer.

- **Decrypted save:** select it and choose **Open selected save**. Workshop validates it, makes an automatic backup, and opens it directly without a file-navigation dialog.
- **Encrypted PS4 pair:** a game save and its matching `.bin` are listed together. **Select encrypted pair** remembers the chosen source and protects both paths from manual exports. This identifies the pair and opens **PS4 Decrypt / Encrypt**, where an optional GarlicSaves job can be started with confirmation.
- **Incomplete pair:** the `.bin` is missing, so selection is disabled. Copy the complete pair from the PS4.

If a drive is removed, the next refresh removes its entries; opening a stale selection produces a clear refresh message. If macOS reports access denied, allow Workshop access to removable volumes in System Settings. Discovery reads metadata and short file headers. It does not edit, rename, upload or back up files until you choose a backup or service action.

## Name your PSN profiles

Choose **Edit profile name…** beside an account in the USB list, enter its PSN screen name or any recognizable label, and save. A blank name restores the displayed account ID. Workshop keeps labels under the local application-support folder in `profile-names.json`, separately from automatic save backups. Updates preserve them. PS4 directory names must remain account IDs and are never renamed by this feature.

For several accounts, choose **Import profile names…** in the USB browser and select a private JSON file with this shape:

```json
{"profiles":{"0000000000000001":"Example_Player"}}
```

Imports merge with existing names; blank values remove individual labels. IDs must be 16 hexadecimal characters and labels at most 64 characters. Invalid imports leave the existing names unchanged. A personal import file is not bundled in the public app or repository; import it once on each computer you use. A profile name in GarlicSaves is stored separately and does not automatically synchronize with Workshop.

## Identify weapons by picture and type

Each weapon in the list has a small silhouette and a plain-language type label. Selecting a weapon shows a larger silhouette. For example, **Raven** is labeled **Sporting rifle**. The creation and replacement windows show the same preview, which updates when you choose a different weapon.

These are original, representative illustrations of the weapon family, not exact pictures of each named variant, finish, or attachment. Labels are inferred from the game's model identifiers. If the identifier does not establish a more specific type, Workshop shows **type unverified** with a question-mark image instead of guessing. Silhouettes are bundled in the app and work offline.

Use **Find a weapon** or the creation search to look for a type such as **shotgun**, **sporting rifle**, or **katana**, as well as a weapon name.

## Automatic backups

Backups are on automatically. Every successfully validated save you open gets a full-file **opened** backup before the app accepts it. Every validated export gets a full-file **exported** backup before the Save dialog/export is made available. Export backups are retained even if you then cancel the Save dialog. Merely ticking a perk or typing a value does not create another full-file backup; unexported edits remain in memory.

Each backup has a UTC date/time, its opened/exported label, the source name, and a unique ID. Opening the same file repeatedly creates separate backups. Files are created exclusively and checked by SHA-256. Workshop never automatically overwrites, rotates, or deletes them, and app updates retain the folder. If a backup fails, the open/export stops with an error instead of continuing without protection.

Choose **Help → Open Backup Folder** to see them:

- Mac: `~/Library/Application Support/Dead Island 2 Workshop/Backups`
- Windows: `%LOCALAPPDATA%\Dead Island 2 Workshop\Backups`

To restore, open a chosen `.sav` backup in Workshop and export a separate copy outside the backup folder, then use your normal PS4 container import workflow. Workshop blocks manual exports into its backup folder. These snapshots contain decrypted game-data bytes; restoring them to a PS4 still requires re-encryption into a valid PS4 save container. Keep your original encrypted PS4 save pair as well.

Full copies accumulate, so disk usage grows with the number and size of your saves. You can manage them yourself in Finder or File Explorer; the app does not remove old backups.

## Edit a weapon

1. Select a location, then select a weapon. Use **Find a weapon** to narrow the list.
2. Change **Required weapon level** or **Weapon rarity**.
3. Tick or untick entries under **Mods & perks**. Each entry has a short effect description; hover over it for more detail. Entries inferred from internal names are labeled as unverified. Search also finds words in descriptions, or use **Installed only** to shorten the list.
4. **Select all mods & perks** selects the entire catalog, including entries hidden by search or Installed only. Then untick anything you do not want. Clicking the fully checked box clears the selection. The same control and descriptions appear in Create Weapon and Replace Weapon. Different damage types and tiers are included; selecting an upgrade does not guarantee it will work with that weapon in-game.
5. **Copy perk set** copies the selected weapon's upgrade list. Select another weapon and choose **Paste perk set** to apply it there.
6. **Revert this weapon** cancels that weapon's staged edits, replacement, or deletion.

The catalog combines named game data with special entries already in your save. Hover over a perk to see its internal identifier. A stored upgrade is not a guarantee of an active game effect. Duplicate upgrades cannot be added. Rarity changes do not offer a separate control for combat classes such as Bulldozer or Headhunter.

Levels 0–1000 and up to 256 upgrades are accepted as experimental values. Values beyond normal game rules may be ignored, changed, or rejected by the game. Special built-in Bare Hands and Fury Fists records are read-only and do not consume normal weapon-capacity calculations.

## Duplicate an entire weapon

Select an existing weapon and choose **Duplicate Weapon…**. The dialog copies its model, generation seed, complete saved runtime state, level, rarity, perks, and durability. Any staged edits are included. The duplicate receives fresh IDs so it is a separate item. Choose a destination and press **Queue Duplicate**. The source stays in place. If its current location is full, choose another location or stage a deletion first.

The copy is a snapshot: later edits to the source do not automatically change the queued copy. Batch perk actions can affect queued copies. Use Create Weapon to inspect or remove queued copies before export. Custom values are preserved in the file; structural checks do not establish that every copied state has an in-game effect.

## Weapon slot counters

The **Slots after export** panel above the weapon list shows used / total slots and free space. Choose a location to see its counter, or use All inventories & lockers for a breakdown. Creation and duplication destination choices also show these counts. Queued creations/duplicates use slots and staged deletions release them immediately in the counters; replacement uses the same slot.

Workshop uses limits of **16 carried weapons** and **64 shared locker weapons**, with regular and NG+ lockers counted separately. Special Bare Hands/Fury Fists records do not consume these counters. Unclaimed Property shows a weapon count with **limit unverified** and is not a creation destination. The app does not increase the game's capacity.

## Apply or remove one perk across many weapons

Choose **Apply / Remove…** beside a perk in an existing weapon's perk list. Select **All weapons**, **Melee weapons only**, or **Firearms only**, then choose **Entire save** or **Selected location only**. The dialog shows the target count and how many weapons Apply and Remove would change before you click either button.

A batch adds or removes only that one perk. Other perks, levels, rarity, and durability are retained. It includes queued new weapons and duplicates, skips read-only attacks and staged deletions, and does not add duplicate perk entries. Weapon/perk search filters do not limit the batch. Changes remain staged for Review & Export; revert an individual weapon to cancel its edits. A perk stored on an incompatible weapon may have no effect in-game.

## Experimental durability and ammunition

For a melee weapon, edit **Melee durability · experimental** under Weapon settings. Try **9999** to test a high finite value. Creation, replacement, and duplication also have this field. Blank on creation uses 1000; blank on duplication preserves the source's saved state. Values from 0 to 1,000,000,000 are allowed; 0 represents broken durability. The game may cap, reset, or otherwise reinterpret high values. This is not a guarantee of infinite durability.

Choose **Reserve Ammo…** in the top toolbar, select a character or location, and change an existing stack's count or click **Set 9,999**. These are reserve counts, not a gun's loaded magazine. Review & Export lists each ammo change. **Revert ammo edits** cancels all staged reserve-ammo changes. Ammo-only edits also trigger the quit-with-unsaved-edits prompt.

No verified per-gun magazine count was found in the development save. Workshop does not invent an ammo field or claim to change magazine capacity. Reserve counts accept whole numbers from 0 to 9,999,999, but the game may enforce a much lower limit or reset them. Start with one weapon/stack and check it in-game before changing everything.

## Create a weapon

1. Choose **Create Weapon** or press **Command-N**.
2. Choose a **Destination**. Its free-slot count includes staged deletions and creations.
3. Search the catalog and select the weapon.
4. Set its level, rarity, and perks. **Use copied perk set** applies a previously copied list.
5. Choose **Add to Export**.

The new weapon is queued, not immediately written. Reopen Create Weapon to inspect the queue or **Remove** a queued creation. Review & Export writes queued weapons to the edited copy.

The catalog contains base-game and DLC weapon variants and additional types found in the opened save. It is not guaranteed to cover every later game update. DLC entries require the relevant content. New weapons receive fresh IDs, and melee weapons start with durability 1000. Named weapons, DLC content, and unusual upgrade combinations still need in-game testing.

## Delete a weapon to make room

Select a weapon and choose **Delete Weapon** near the top of its details. The list marks it for deletion and the button becomes **Undo Delete**. Undo restores it before export. Marking a weapon for deletion discards its other staged edits.

Deleting a weapon immediately frees its slot for a creation in the same export. Existing overfilled inventories are preserved, but enough deletions are needed to bring the final total within the configured limits: 16 carried weapons or 64 locker weapons. Creation in Unclaimed Property is unavailable.

When a carried weapon is deleted, its character's matching shortcut assignment is removed if no surviving weapon uses the same persistent ID. Other characters' copies remain untouched.

## Replace a weapon without an extra slot

1. Select the existing weapon.
2. Choose **Replace Weapon** near the top of its details.
3. Select a different weapon from the catalog. Level and rarity are prefilled; choose the replacement's perks (the old perk set is cleared initially).
4. Choose **Stage Replacement**.

Replacement uses the same inventory slot and keeps the existing IDs for shortcut references. It does not require free space. **Revert this weapon** cancels it before export.

## Export and return to PS4

1. Choose **Review & Export** or press **Command-S**.
2. Review all edits, replacements, deletions, and new weapons.
3. Choose **Validate & Save Copy** and save the resulting `_Edited.sav` file.
4. Move it to the PC running Save Wizard.
5. Open the original PS4 save in Save Wizard Advanced Mode, select the same internal file originally exported, import the edited file, then apply the changes.
6. Copy the resulting PS4 save back to your console using your normal USB workflow.

Workshop refuses to export over a file opened as an input during the session. Its output is reparsed and compared with requested changes before saving. This checks file structure, not game compatibility. Start with one change and keep the original PS4 backup.

## Named PS4 save backups and restoration

In **USB Saves**, every save has **Back Up This Save**. Enter a descriptive name such as “Saved game before doing cheats on 2 Nov” and save it. Workshop creates a new dated folder with that label, a unique ID, the original filenames and `PS4/SAVEDATA/account-ID/CUSA…` tree. A manifest records account, game, timestamp, sizes and SHA-256 checksums. Labels never rename your PS4 source folders. Repeated names create separate backups.

Click **Named Backups…** in that screen to browse saved backups after restarting the app. **Open Backup Folder** opens their local **NamedBackups** folder next to automatic Backups. Encrypted backups can be restored to their original account/game on a chosen connected USB drive; decrypted Dead Island 2 backups open in the editor. Restoring encrypted pairs requires confirmation and automatically backs up any existing destination pair before writing. Backups with missing files, links or changed checksums are refused. A backup originally captured as incomplete remains available for inspection but cannot be installed as a complete pair.

Named backups never expire or overwrite one another. Manual exports into the named or automatic backup folders are blocked. Workshop restores the old pair if a normal two-file installation fails after the first file was replaced. As with any removable-drive write, a power failure or disconnect may require manual restoration from the retained backup; do not remove the drive during installation.

## Dead Island 2 character levels, cash and resources

Open **Character & Resources…** after loading a supported decrypted Dead Island 2 save. Select the actual slayer and Regular/NG+ profile. Character level can be raised or lowered to **1–30 Regular** or **1–40 NG+**. Enter the level and click **Stage Level**. Export synchronizes the character’s XP to the start of that level and updates existing profile-summary and account level caches. It leaves missions, earned skills and weapon requirements unchanged; lowering character level does not lower weapon levels.

Cash uses whole dollars, from **$0 to $2,000,000**. Click **Stage Cash** or **Set $2,000,000**. If the original save has several cash stacks, Workshop sets their combined amount to your requested total rather than granting that amount to every duplicate stack. An existing amount above this limit is preserved unless you stage a cash edit.

Crafting materials and zombie parts can be filled to **99 each**, med-kits to **5**, and fuses to **3**. Edit individual saved quantities or click **Fill this character** / **Fill all characters…**. Missing known stack types are added with fresh identities. Recipes, curveballs, ammo and weapon records are preserved by these fill actions. Ammo has its separate editor. These controls fill inventory quantities; they do not increase hard-coded stack capacity or enable crafting-material storage in a weapon-only locker.

All these edits are staged in memory alongside weapon edits. **Review & Export** lists and validates them in a separate copy with an automatic backup. **Encrypt Edited Copy** includes them in the active GarlicSaves session. Opening another save or quitting asks about unexported edits. The parser and XP/cache changes have local round-trip tests; in-game effects still require a PS4 test.

## Other PS4 games and profile-to-profile resigning

USB discovery now lists matching encrypted pairs across **all CUSA game folders**, including filenames other than DeadIsland2SaveGame. Game labels use title IDs when Workshop has no local game name. This expands container management; the internal editor still understands only supported Dead Island 2 data.

Select an encrypted save and open **PS4 Decrypt / Encrypt**. After decryption, **Re-encrypt Complete Package…** sends the complete unchanged package back for encryption; **Encrypt Edited ZIP…** accepts a complete externally edited ZIP, including `sce_sys/param.sfo` and all companion files. Account/title metadata must still match the original context. An unsupported Dead Island 2 representation is also retained as a generic package instead of being mistaken for editable data. File downloads and console processing depend on GarlicSaves support and availability; “all game folders” is not a guarantee that every game/firmware/protection scheme will process successfully.

For account transfers, choose a **Destination PSN profile**, then **Resign selected save…** or **Resign all source-profile saves…**. The latter selects all complete encrypted pairs belonging to that source account on the same selected drive, across all listed games. Workshop sends one job per save, sequentially. The source pair and any existing destination pair receive named backups before processing. Original USB saves remain unchanged while results are staged locally.

After processing, review the result count and click **Install Resigned Copies…**. Confirm USB replacement. Each destination is backed up again immediately before installation, including changes made while a remote job was running. A backup failure prevents that destination write. Batch processing may stop after partial results; completed pairs are retained. A later installation failure can leave earlier pairs installed, each with its own destination backup. Check the result message rather than assuming the entire batch completed.

PSN targets come from your local profile names and accounts found on drives. Register/use accounts you control. Re-signing is performed by GarlicSaves, not by renaming an account folder locally. Its acceptance on the PS4 still requires testing. Keep Workshop open through a transfer; if you quit, raw result files remain in ServiceSessions, but this preview’s staged installation list is not restored automatically.

## PS4 encryption and Save Wizard

Workshop 0.14.0 includes a **GarlicSaves connection preview**. The cryptographic processing takes place on GarlicSaves’ remote console workers. It is not offline decryption on the Mac or PC, and does not need Save Wizard for the proposed online workflow. Compressed Dead Island 2 package parsing, edit/recompression and companion-file preservation are tested locally; PS4 import still needs testing; the existing Save Wizard workflow remains available.

### Connect and decrypt

1. Click **PS4 Decrypt / Encrypt…** in the header (or Help menu).
2. Paste your GarlicSaves **worker key** and click **Test Connection**. This sends a read-only API request; no save files are uploaded. The key is saved in **macOS Keychain** or **Windows Credential Manager**, and loads automatically after quitting and reopening. Click **Save Key** to save without testing; **Test Connection** also saves a newly entered key. The field stays masked and shows **Saved key ready** when a key exists. Paste another key to replace it, or click **Remove Saved Key** to delete it. On Mac, allow Keychain access if prompted; choosing **Always Allow** avoids repeated access prompts for that Python executable. Never include it in screenshots, GitHub, or shared files. The console-worker config file is not needed.
3. Choose an encrypted save in **USB Saves**. The matching `DeadIsland2SaveGame.bin` must be present in the same game folder. The profile/account and title are displayed for checking.
4. Click **Decrypt Selected Save…** and confirm sending those two files to **garlicsaves.com**. Workshop saves an original-pair ZIP and automatic snapshots locally before submission. Keep Workshop open while the job is queued/running. The app does not automatically upload any saves just because a drive is connected.
5. When the decrypted Dead Island 2 data passes validation, Workshop opens it in the editor automatically. Existing staged edits require a discard confirmation before replacement. **Open Decrypted Save** also opens the current validated result.

To continue after updating or restarting, choose **PS4 Decrypt / Encrypt → Reopen Last Decryption**. Workshop validates and opens the latest locally saved decryption without another upload. This does not restore unexported edits from a previous session. Compressed inputs stay compressed on export, with validated chunk sizes and a recalculated CityHash64 checksum; no-edit exports remain byte-for-byte identical. Companion files and metadata are preserved unchanged.

The downloaded package must include `sce_sys/param.sfo`. Workshop checks its account and title against the selected source, preserves companion files, and requires the exact supported game-data format with a byte-for-byte no-edit validation. If the returned game data is compressed or otherwise unsupported, Workshop retains **Decrypted-Result.zip** as a generic package for inspection or re-encryption; it does not claim successful internal editing or silently convert the data.

### Re-encrypt an edited copy

1. Edit the decrypted result normally. Open **PS4 Decrypt / Encrypt…** again.
2. Click **Encrypt Edited Copy…**. Confirm the edit count, destination account, and upload to GarlicSaves. This validates the currently staged edits and submits the full package, retaining metadata and companion files. A standalone Save Wizard file opened separately is not bound to this session and cannot accidentally be encrypted into the wrong container.
3. When complete, click **Open Result Folder**. The folder contains the raw result ZIP, the edited decrypted package, and a separate **PS4/SAVEDATA/account-ID/CUSA…** tree with the matching encrypted pair, plus **Ready-For-USB.zip**. Original USB files are never overwritten by this operation.
4. Copy that new PS4 folder to a spare USB drive and test importing it on the PS4 before replacing your working save. In-game validation is required; syntax checks do not prove the console will accept a remote service result.

The active link between an opened decrypted result and its original container lasts for the current app session. Keep Workshop open through decryption, editing, and re-encryption. If you quit, the archives remain on disk, but this preview requires decryption again to establish a new editable service session.

### Retained files and failures

Service sessions accumulate under **ServiceSessions** next to **Backups** in Workshop’s application-support folder. Each session and encryption attempt has a unique directory. These files contain private save data; they are not published to GitHub. A missing/invalid key, network outage, unavailable workers, service failure, unsafe ZIP, wrong account/title, or unsupported game-data format stops the operation with a status message. Downloaded ZIPs and submitted job IDs are retained where available. The remote service controls its queues and data retention.

Workshop does not automatically retry a failed submission, which avoids creating duplicate jobs after uncertain network failures. If you quit or force-close during a job, check its status/results on GarlicSaves before resubmitting. Normal quit is blocked while the operation is in progress. Polling stops after 30 minutes; the remote job may still finish. Closing the settings dialog alone does not cancel the job.

## Updates

- **Help → Download Updates** opens the latest ZIP download in your default browser. The public repository needs no GitHub login. Quit Workshop and run the downloaded installer.
- **Help → Check for Updates** reads `update.json`. If a newer version is available, you can download it and choose **Quit & Install**. Installation starts immediately after the app finishes quitting. **Keep Editing** leaves the update queued for your next quit. Unsaved-edit and busy-operation guards still apply. If authentication is unavailable, it offers the browser download instead.
- **Help → Update Status** shows the running app path/version, installed Applications version, queued version, and last installation result. **Open Update Folder** reveals `install.log` and `update-handoff.log` when troubleshooting. A successful installer exit is followed by checking the actual installed version.
- **Help → Automatic Updates** is enabled by default and can be turned off. A per-user LaunchAgent checks every 15 minutes while the Mac is awake and you are signed in. Automatic checks/downloads/installation run only while Workshop is closed. Updates leave it closed.
- If the repository is made private later, automation requires an already authenticated **GitHub CLI (`gh`)** on this Mac with access to this repository. Workshop uses `gh api`; it does not copy the login token. A browser GitHub login alone does not authenticate the background updater. Without CLI authentication, use Download Updates; automatic attempts will report authentication required in the update log.
- Downloaded updates are SHA-256 checked, extracted into a temporary folder, built locally, and installed over the same Applications app. An application lock prevents installation while the updated app is open. Failed downloads or builds retain the previous app. Old version updates also check the running app before replacement.

The background agent and settings are under your user account. Settings and logs live in `~/Library/Application Support/Dead Island 2 Workshop/`. The agent is `~/Library/LaunchAgents/local.ted.di2workshop.updater.plist`.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| Command-O | Open decrypted save |
| Command-N | Create weapon |
| Command-S | Review and export |
| Command-W | Close window and quit |
| Command-Q | Quit |
| Command-C / V / X / A | Standard text editing |

Shortcuts are fixed in this preview. Mouse-wheel input does not change number fields or dropdown selections.

## Troubleshooting

- **Encrypted/unsupported input:** export the internal game-data file through Save Wizard first. Other PS4 layouts and PC-format saves are not supported by this preview.
- **No free slots:** stage deletions, choose another character/locker, or use Replace Weapon.
- **Startup failure:** inspect `startup.log` in the Application Support folder above.
- **Private GitHub download fails:** sign into GitHub in the browser and confirm repository access. For automated checks, the Mac's `gh` login needs that same access.
- **Install build error:** copy the compiler output. The installer builds before replacing the app.

Saves are handled locally by a service listening only on 127.0.0.1 at a random session address. The service stops when the app quits. Updates contact GitHub; save contents are not sent to GitHub. Personal save files are excluded from this repository.

## Repair older Mac update queues

Versions through 0.9.0 queued downloads for the 15-minute background agent and did not launch installation on quit. Reopening could postpone installation repeatedly. Quit the app and run **Repair-Updates.command** from a newly downloaded Mac package to install the latest version immediately. Keep the app closed until the repair prints the installed version, then open the copy in Applications. If it fails, retain the Terminal output. The repair does not modify saves, backups, or profile names.
