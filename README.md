# Dead Island 2 Workshop — Mac and Windows

A weapon editor for **decrypted Dead Island 2 PS4 saves exported through Save Wizard**.

[Windows download](https://github.com/TedInVR/DeadIsland2WorkshopForMac/releases/latest/download/Dead-Island-2-Workshop-Windows-Latest.zip) · [Windows guide](README-WINDOWS.md) · [Download the latest Mac installer](https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true) · [User guide](USER_GUIDE.md) · [Version history](CHANGELOG.md)

## Install on Mac

Quit Workshop, extract the downloaded ZIP, and double-click **Install.command**. It builds and installs **Dead Island 2 Workshop.app** in Applications, then opens it. Updates reuse the same app.

Requires macOS 12+, Python 3.9+, and Apple Command Line Tools. No pip dependencies or Windows emulator. Public downloads and updates require no GitHub login.

## Install on Windows

Download the Windows ZIP above, choose **Extract All**, and run **Install-Windows.cmd**. It installs a self-contained app with Desktop and Start menu shortcuts. See the [Windows guide](README-WINDOWS.md) for requirements, portable use, updates, and building from source.

## Features

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
- Review changes and export a separate validated copy; original inputs stay unchanged.
- Help menu links to the user guide, update checks, latest download, and automatic-update preference.

## Updates

**Help → Download Updates** opens the latest installer in your signed-in GitHub browser. **Check for Updates** can download and queue newer builds. Automatic updates default on and run every 15 minutes only while the app is closed, leaving it closed afterward.

The public repository supports direct downloads without authentication. If you make the repository private later, automated downloads require an authenticated GitHub CLI (`gh`) on the Mac; browser downloads use your browser login. No credentials are embedded or uploaded. See the [update guide](USER_GUIDE.md#updates).

## Preview status

Version **0.7.0**. Save serialization and interface regression tests passed; the native 0.1.0 installer/window was tested by the user. The user has reported opening/exporting from the Mac app and completing a Save Wizard import. New controls and their in-game effects still need testing on the Mac/PS4.

Workshop does **not** decrypt or re-encrypt the PS4 USB save container. Save Wizard is still needed for export/import in the current workflow. See [PS4 encryption](USER_GUIDE.md#ps4-encryption-and-save-wizard).

Personal saves are not included. The app implementation is independent. Game-data name/identifier attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Not affiliated with the game publisher, Save Wizard, or SteffenL.

## Source and verification

Source files are at repository root. Run `python3 test_core.py /path/to/decrypted.sav` locally for the supplied-save regression suite. That suite includes assertions tied to the original development fixture, which is intentionally not published; use an appropriate local fixture when adapting it. `python3 -m unittest test_updater.py` runs isolated updater tests without a save or GitHub login.

To publish a new update, see [DEVELOPMENT.md](DEVELOPMENT.md).

External encryption services are being investigated; see [current findings and requirements](ENCRYPTION_RESEARCH.md). An online decryption connection is not included yet.
