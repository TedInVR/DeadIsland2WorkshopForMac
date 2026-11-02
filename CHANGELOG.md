# Version history

## 0.11.0

- Add named, append-only PS4 save backups, persistent browsing, checksum validation and guarded restore.
- Discover encrypted pairs for all CUSA games. Add single-save or source-profile batch resigning with source/destination backups and explicit installation of staged results.
- Add generic complete-package decryption/re-encryption and externally edited ZIP import for other PS4 games; service compatibility and console import remain untested live.
- Add DI2 character level/XP/cache editing within Regular 1–30 and NG+ 1–40; per-character cash capped at $2,000,000.
- Fill crafting materials/zombie parts to 99, med-kits to 5, fuses to 3, adding missing stacks. Preserve unrelated records and retain normal capacity limits.

## 0.10.1

- Remember each user's GarlicSaves worker key privately in macOS Keychain or Windows Credential Manager and load it automatically on later launches.
- Add Save Key, saved-key status, replacement and removal; never include credentials in settings, backups, logs, source, or app downloads.
- Report secure-store access errors and retain the previous key if a replacement cannot be saved.

## 0.10.0

- Add an opt-in GarlicSaves API connection preview with session-only worker key and a read-only connection test.
- Decrypt a selected USB pair after confirmation and verified local backup; preserve complete returned metadata and companions.
- Validate original account/title and supported game-data structure before opening; retain unsupported result ZIPs for inspection.
- Re-encrypt validated staged edits into a separate result folder for the original account. Keep original USB files untouched.
- Live GarlicSaves output compatibility and PS4 console round-trip validation remain pending.

## 0.9.1

- Fix queued Mac updates that previously depended on the 15-minute background timer. Quit & Install starts a detached helper immediately; Keep Editing installs when the user later quits.
- Keep the app closed during the handoff/build and respect in-progress operations and unexported-edit prompts.
- Restore queue metadata when reusing an already downloaded ZIP, verify the installed Applications version before reporting success, and retain installer stdout/stderr and status.
- Add Help → Update Status, running-copy diagnostics, a one-time repair command for older installs, and stable Python paths for future agent registration. Agent registration no longer contends with its parent install worker lock.
- Add macOS CI that actually compiles, signs, and installs an update into a temporary app location, then verifies the new installed version. User apps and data are not touched by that test.

## 0.9.0

- Add automatic, read-only discovery of PS4 Dead Island 2 saves on mounted Mac volumes and Windows removable/fixed drive roots. Check only PS4/SAVEDATA/account-ID/known-title-ID folders, and refresh every 10 seconds while the app is visible.
- Add USB Saves browser with account labels/IDs, drive, title, filename, size, modified date, and encrypted/decrypted/incomplete status. Rescan on demand and reveal the selected file in Finder/Explorer.
- Open supported decrypted exports directly from the list with automatic backups and source-file overwrite protection. Encrypted pairs can be selected and identified but still require a separate decryption workflow; missing .bin files are marked incomplete.
- Add local profile-name editing and JSON import. Labels persist across updates without renaming PS4 folders or publishing personal mappings in the repository.
- Add USB discovery, persistence, no-write, unplug, symlink, invalid-import, and shared UI integration checks.

## 0.8.0

- Automatically create a full-file backup after successful validation on every save open and before making each validated export available. Both desktop shells use the shared open/backup logic.
- Give snapshots UTC timestamps, opened/exported labels, and unique IDs. Exclusive file creation prevents overwrites, including on filename collisions. Verify the saved bytes by SHA-256; stop the operation if backup writing fails.
- Add Help → Open Backup Folder on Mac and Windows. Backups are retained without automatic pruning; updates retain the folder. Manual exports cannot target the automatic-backup directory.
- Add collision, concurrent-write, disk-failure, open-session preservation, protected-export, and full editor/export backup checks.

## 0.7.0

- Add a Windows desktop shell with WebView2, native save dialogs, source-file overwrite protection, and unsaved-edit close confirmation. Shared save/editing logic and interface remain the same on Mac and Windows.
- Add Windows packaging, per-user installation with shortcuts, dependency notices, file-operation tests, and a GitHub Actions executable/release build.
- Make catalog text decoding explicitly UTF-8 for Windows.
- Record the researched GarlicSaves/HTOS REST integration candidate and the remaining access/compatibility requirements. No online save uploads or encryption integration are included yet.

## 0.6.0

- Duplicate complete weapons, preserving generation seed, runtime state, and unknown fields while assigning fresh item and persistent IDs. Copies snapshot staged level/rarity/perk/durability edits and can be placed in another inventory or locker.
- Show used/total/free weapon slots by location, updating for queued additions and deletions. Unclaimed Property has an explicit unverified limit.
- Add Apply / Remove actions beside each perk, with whole-save or selected-location scope and all/melee/firearm targets. Includes queued creations and duplicates; skips read-only attacks and deleted weapons. Shows affected counts before applying.
- Edit saved melee durability experimentally, including 9,999; preserve unrelated runtime fields.
- Edit existing reserve-ammo stacks experimentally, including 9,999. No verified magazine-count field was found; magazine editing is not claimed.
- Make the installed version visible beneath the app title at all window sizes. Retain the weapon silhouettes introduced in 0.5.0.
- Replacements retain the source seed so copies of a staged replacement match its generated stats.

## 0.5.0

- Add original weapon-family silhouettes beside inventory entries and a larger selected-weapon preview.
- Add plain-language type labels (for example, Raven → Sporting rifle), inferred from game model identifiers. Unknown types remain explicitly unverified.
- Add live silhouette previews and type labels in Create Weapon and Replace Weapon.
- Search both inventory and creation catalog by weapon type as well as name. Illustrations are representative silhouettes, not exact game renders; no external images or network requests are needed.

## 0.4.0

- Add short effect descriptions beneath every mod and perk, with hover details and clear labels for inferred or unverified effects.
- Search descriptions as well as names.
- Add Select All checkboxes in weapon editing, creation, and replacement. Includes the entire catalog regardless of filters, supports individual deselection, and shows a partial-selection state.
- Keep unrecognized save upgrades visible with an explicit unverified-effect description.

## 0.3.0

- GitHub-hosted versioned/latest installer packages and update manifest.
- Help menu: User Guide, Check for Updates, Download Updates, Automatic Updates, and Save Encryption explanation.
- Optional authenticated private-repository checks through an existing GitHub CLI login.
- Per-user 15-minute background updater; only installs with the app closed and leaves it closed.
- SHA-256 verification, archive checks, staged installation, and app/update locking.
- Full user guide covering editing, creation, deletion, replacement, updates, and Save Wizard workflow.

## 0.2.0

- Actual slayer names and Regular/New Game Plus labels.
- Shared locker and Unclaimed Property labels by game mode.
- Create Weapon with catalog, destination, level, rarity, and perk selection.
- Delete/Undo Delete and in-place replacement.
- Shortcut cleanup for deleted carried weapons.
- Named weapon/perk data supplemented by the opened save.

## 0.1.0

- Initial native Mac window and decrypted PS4 save reader.
- Level, rarity, and perk edits; copy/paste perk sets.
- Original-file protection, staged edits, reviewed export, and structural round-trip checks.
