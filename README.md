# Dead Island 2 Workshop — Mac and Windows

## Named mod and perk presets

Select the mods/perks you want, click **Save as Preset**, give the set a name and save it. In the weapon editor or Create/Replace/Duplicate dialog, choose a saved set from **Saved mod & perk presets**, then click **Apply Preset**. Applying a preset replaces that weapon's selected mod/perk set; other weapon settings remain unchanged. Presets are stored locally between launches, independently of opened saves and app updates. A duplicate name requires confirmation before replacement. **Delete Preset** removes the saved set without changing weapons already using it. If a preset includes upgrades unavailable in the current save's catalog, no changes are applied.

The replacement dialog uses **Done** to apply your selection in the editor. It does not write to the USB save: use **Review & Export** or **Encrypt Edited Copy** to save the edited copy. Top toolbar labels are shown in full without trailing dots; complete buttons wrap to additional rows and include descriptive hover help.

## First use, credits and risks

On first launch, read the Experimental Use Agreement, check the acknowledgment box and choose **I Agree & Continue**, or quit. Workshop stores only an acceptance flag, agreement version/hash and time locally; there is no registration or central user list. Ordinary updates remember acceptance. **Help → Usage Agreement & Risks** reopens the notice; **Help → Credits & Licenses** opens named credits, reference links and license boundaries.

Workshop is a free, independent experimental hobby project maintained by TedInVR with OpenAI ChatGPT/Codex assistance. Modified gameplay must remain offline. Users must follow applicable laws and platform, game and service terms. The notice explains save corruption, account/console bans, penalties and legal-action risks and limits warranties/liability only to the extent permitted by law. It cannot bind Sony or publishers, remove non-waivable rights, authorize prohibited activity or guarantee legal protection. Free/offline use is not itself legal clearance.

With appreciation to Sony/PlayStation, PLAION/Deep Silver/Dambuster/Fishlabs, the community and dependency authors. Workshop is not affiliated with or endorsed by them. See [the agreement](USAGE_TERMS.md), [credits](CREDITS.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [licensing review](LICENSING_REVIEW.md). The technical review identified no bundled Sony SDK, firmware or console keys; this is a limited review, not certification. Redistribution permission for the referenced catalog tables remains unverified. Attribution alone is not permission.

A **Dead Island 2 save editor** for characters, cash, materials, consumables and weapons, plus named backups and optional GarlicSaves tools for PS4 save containers from other games.

[Windows download](https://github.com/TedInVR/DeadIsland2WorkshopForMac/releases/latest/download/Dead-Island-2-Workshop-Windows-Latest.zip) · [Windows guide](README-WINDOWS.md) · [Download the latest Mac installer](https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true) · [User guide](USER_GUIDE.md) · [Version history](CHANGELOG.md)

## Install on Mac

Quit Workshop, extract the downloaded ZIP, and double-click **Install.command**. It builds and installs **Dead Island 2 Workshop.app** in Applications, then opens it. Updates reuse the same app.

Requires macOS 12+, Python 3.9–3.13, and Apple Command Line Tools. The installer automatically prepares a private runtime with Zstandard and CityHash support. No Windows emulator. Public downloads and updates require no GitHub login.

## Install on Windows

Download the Windows ZIP above, choose **Extract All**, and run **Install-Windows.cmd**. It installs a self-contained app with Desktop and Start menu shortcuts. See the [Windows guide](README-WINDOWS.md) for requirements, portable use, updates, and building from source.

## Features

- Name a complete PS4 save backup beside each USB save; browse and restore named backups with checksum validation and automatic destination backups.
- Discover encrypted pairs across all CUSA game folders. Resign one save or all encrypted saves on a source profile/drive to another local PSN profile; stage remote results before explicitly installing them, backing up every replaced destination.
- Generic GarlicSaves decrypt/re-encrypt/resign workflows for other PS4 games, preserving complete packages and metadata. Actual service/game compatibility and console import require live testing; internal editing of other games is not included.
- Dead Island 2 character levels 1–30 Regular / 1–40 NG+, with synchronized XP and level-display caches; cash from $0 to $2,000,000 per character.
- Fill saved crafting materials and zombie parts to 99, med-kits to 5, and fuses to 3, including missing stack types. Fill one or all characters. These are quantity edits, not increases to the game’s capacity limits.

- Automatically discover PS4 save pairs on connected drives; show editable local PSN profile labels without renaming folders. Import private profile names once per computer.

- Actual character names with Regular/New Game Plus labels and active-character marking.
- Shared lockers and Unclaimed Property separated by game mode.
- Weapon level, rarity, mods, and perks; copy/paste perk sets.
- Effect descriptions and hover help, plus Select All followed by individual deselection in editing and creation.
- Representative weapon silhouettes and plain-language type labels in the list, selected weapon, and creation/replacement preview. Search by weapon type as well as name.
- Create weapons from a searchable base-game/DLC catalog.
- Duplicate complete weapons with fresh IDs; see used/total/free slots by location.
- Apply/remove a perk across all weapons, melee weapons, or firearms, across the whole save or selected location.
- Experimental melee durability and existing reserve-ammo count editing; game-imposed caps still apply. No magazine-count editing.
- Delete/undo deletion to free slots in the same export.
- Replace an existing weapon with a catalog weapon without using another slot.
- Automatic dated backups on every valid save open and validated export; each is a separate file, with no automatic overwrite or deletion. Help → Open Backup Folder opens the local collection.
- Review changes and export a separate validated copy; original inputs stay unchanged.
- Help menu links to the user guide, update checks, latest download, and automatic-update preference.

## Updates

**Help → Download Updates** opens the latest installer in your signed-in GitHub browser. **Check for Updates** downloads newer builds and offers **Quit & Install**. Installation starts immediately after quitting. **Keep Editing** leaves it queued until the next quit. **Update Status** shows the last result and log location. Automatic discovery defaults on and checks every 15 minutes only while the app is closed, leaving it closed afterward. Manually queued installation starts on quit without waiting for that timer.

The public repository supports direct downloads without authentication. If you make the repository private later, automated downloads require an authenticated GitHub CLI (`gh`) on the Mac; browser downloads use your browser login. No credentials are embedded or uploaded. See the [update guide](USER_GUIDE.md#updates).

## Preview status

Version **0.14.0**. Save serialization and interface regression tests passed; the native 0.1.0 installer/window was tested by the user. The user has reported opening/exporting from the Mac app and completing a Save Wizard import. New controls and their in-game effects still need testing on the Mac/PS4.

Workshop offers an opt-in **GarlicSaves connection preview** for online PS4 decryption/re-encryption, alongside the existing Save Wizard workflow. Enter a worker key locally; selected saves are sent only after confirmation. Actual GarlicSaves output compatibility and a PS4 console round trip still need live testing. See [PS4 encryption](USER_GUIDE.md#ps4-encryption-and-save-wizard).

Personal saves are not included. The app implementation is independent. Game-data name/identifier attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Not affiliated with the game publisher, Save Wizard, or SteffenL.

## Source and verification

Source files are at repository root. Run `python3 test_core.py /path/to/decrypted.sav` locally for the supplied-save regression suite. That suite includes assertions tied to the original development fixture, which is intentionally not published; use an appropriate local fixture when adapting it. `python3 -m unittest test_updater.py` runs isolated updater tests without a save or GitHub login.

To publish a new update, see [DEVELOPMENT.md](DEVELOPMENT.md).

See [GarlicSaves setup, privacy, and test limits](ENCRYPTION_RESEARCH.md). Worker keys are remembered privately in macOS Keychain or Windows Credential Manager; they are never bundled or stored in settings.

If an older version repeatedly queues an update but never installs it, quit Workshop and run `Repair-Updates.command` from the latest Mac package. It uses the existing helper to verify/download/install the latest version immediately and checks the resulting Applications version.
