# Dead Island 2 Workshop for Mac

A Mac weapon editor for **decrypted Dead Island 2 PS4 saves exported through Save Wizard**.

[Download the latest Mac installer](https://github.com/TedInVR/DeadIsland2WorkshopForMac/blob/main/downloads/Dead-Island-2-Workshop-Mac-Latest.zip?raw=true) · [User guide](USER_GUIDE.md) · [Version history](CHANGELOG.md)

## Install

Quit Workshop, extract the downloaded ZIP, and double-click **Install.command**. It builds and installs **Dead Island 2 Workshop.app** in Applications, then opens it. Updates reuse the same app.

Requires macOS 12+, Python 3.9+, and Apple Command Line Tools. No pip dependencies or Windows emulator. For this private repository, sign into GitHub in your browser before downloading.

## Features

- Actual character names with Regular/New Game Plus labels and active-character marking.
- Shared lockers and Unclaimed Property separated by game mode.
- Weapon level, rarity, mods, and perks; copy/paste perk sets.
- Effect descriptions and hover help, plus Select All followed by individual deselection in editing and creation.
- Create weapons from a searchable base-game/DLC catalog.
- Delete/undo deletion to free slots in the same export.
- Replace an existing weapon with a catalog weapon without using another slot.
- Review changes and export a separate validated copy; original inputs stay unchanged.
- Help menu links to the user guide, update checks, latest download, and automatic-update preference.

## Updates

**Help → Download Updates** opens the latest installer in your signed-in GitHub browser. **Check for Updates** can download and queue newer builds. Automatic updates default on and run every 15 minutes only while the app is closed, leaving it closed afterward.

For private-repository automation, an authenticated GitHub CLI (`gh`) with repository access is required on the Mac. Without it, use the browser download. No credentials are embedded or uploaded. See the [update guide](USER_GUIDE.md#updates).

## Preview status

Version **0.4.0**. Save serialization and interface regression tests passed; the native 0.1.0 installer/window was tested by the user. Newer native builds, the first edited-save import, weapon creation, replacement, and deletion still need testing on the Mac/PS4.

Workshop does **not** decrypt or re-encrypt the PS4 USB save container. Save Wizard is still needed for export/import in the current workflow. See [PS4 encryption](USER_GUIDE.md#ps4-encryption-and-save-wizard).

Personal saves are not included. The app implementation is independent. Game-data name/identifier attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Not affiliated with the game publisher, Save Wizard, or SteffenL.

## Source and verification

Source files are at repository root. Run `python3 test_core.py /path/to/decrypted.sav` locally for the supplied-save regression suite. That suite includes assertions tied to the original development fixture, which is intentionally not published; use an appropriate local fixture when adapting it. `python3 -m unittest test_updater.py` runs isolated updater tests without a save or GitHub login.

To publish a new update, see [DEVELOPMENT.md](DEVELOPMENT.md).
