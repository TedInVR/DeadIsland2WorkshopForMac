# Version 0.20.0 — 4 November 2026

- Add scoped exact-model copy counts, existing-weapon checkboxes and Select All / Edit Selected for batch perk, preset, level and rarity edits. Include queued copies in counts and exclude deletions.
- Split main and creation editors into compact sections; paginate perks and move secondary service text/tools into expandable sections. Keep keyboard/focus explanations and small-window scrolling as fallback.
- Add prominent reduced-motion-aware processing emphasis, elapsed queue wait and fresh server-status confirmation. Do not invent queue positions, percentages or finish estimates.
- Add a three-stage Guide Me flow, with separate GarlicSaves and external Save Wizard finishing instructions; claim verified USB completion only after successful finalization.
- Record standing interface preferences and test selection scoping, counts, walkthrough branching and status emphasis.

# Version 0.19.1 — 3 November 2026

- Open the Mac editor immediately; perform the automatic update check/download in the background after five seconds.
- Replace the blocking startup screen and ineffective skip button with a dismissible native update bar shown only when a verified update is queued.
- Never auto-close an editing session to install a background update. Retain Quit & Install and unsaved-edit checks; install only after closing.
- Leave current/offline/failed background checks silent, with manual checks and status available in Help.

# Version 0.19.0 — 3 November 2026

- On Mac, check for updates before opening the editor, download and verify an available update, close for installation and automatically reopen afterward.
- Respect Automatic Updates; offer Open Workshop Now to skip waiting and open the existing editor if the check is unavailable.
- Reopen the existing version with a notice if installation fails; prevent duplicate handoffs and recursive startup checks.
- Preserve closed-app installation locks and ordinary/background update behavior, which leaves Workshop closed.
- Add startup preference, verified queue, restart, failure recovery and no-restart-on-normal-quit tests.
- Keep ammunition numeric fields editable after normal restoration; allow individual custom overrides, missing ammo types and validated consolidated stacks.
- Add a separate Weapon Durability dialog with individual, selected-location and global custom values. Restore normal condition only from matching user-recorded fully repaired references; identify and skip missing or invalidated references.
- Persist references privately with exact weapon/owner/generation/perk signatures, and validate condition exports and custom ammo overrides.

# Version 0.18.0 — 3 November 2026

- Recognize the newer observed post-game save revision and variable game-build field instead of matching one fixed build number.
- Use the same supported header check in the editor, USB browser and decrypted-package detection.
- Preserve the complete original header and no-edit bytes; retain revision, compression checksum and structural validation.
- Validate normal-ammo restoration against the private post-game sample while preserving all weapon record bytes. The sample still stores oversized distinct ammo types despite the game's mirrored icons; in-game normalization remains to be tested.

# Version 0.17.0 — 3 November 2026

- Replace ambiguous ammo Revert actions with Restore Normal Maximum for the selected character or all characters, and a separate Undo Pending Ammo Changes action.
- Fill seven supported ammunition types to published normal amounts, add missing records, consolidate duplicates and verify one correctly sized record per type. Exclude shared lockers and preserve unrelated items and weapon state.
- Remove 9,999 ammo fill buttons and experimental durability input fields after live testing did not produce the intended behavior. Do not treat the mirrored counts seen in-game as capacity limits.
- The user confirmed console acceptance after the ownership correction. The new refill behavior still needs live gameplay validation; post-game ammo diagnosis awaits a decrypted package.

# Version 0.16.0 — 3 November 2026

- Make Finalize and Re-encrypt the highlighted final header action; retain Review & Export as an optional action.
- Back up the selected USB destination before processing and immediately before replacement; write and verify both encrypted files in their correct PS4 folder, with rollback on failure.
- Decrypt returned encrypted pairs to verify the actual PSN account/title, exact edited game data and keystone. Retry one observed account byte-order reversal with a corrected wire value and verify again; never release a USB-ready result after a failed check.
- Recover previously submitted edited packages when reopening a service session, and skip later failed diagnostic decryptions with mismatched accounts.
- Add synthetic ownership/USB failure tests and private local save checks. Native packaging and live console acceptance are separate validation steps.

# Version 0.15.0 — 3 November 2026

- Fill materials and zombie parts to 50 for the selected character while filling med-kits/fuses to their normal maximum, without changing cash or level.
- Show character levels in inventory choices and below the selector, including staged level changes.
- Right-click Copy Weapon / Paste Weapon snapshots full saved state and staged settings, preserving destination IDs and slot count; validate pasted records on export.
- Add selected-character/location Set All to 9,999 and Revert All ammo actions, plus a separate global ammo reset.
- Track per-weapon applied preset labels locally, show modified sets, and update an existing preset by selecting it in the save dialog.
- Local file/serialization checks passed; in-game effects and live PS4 import still require console testing.

# Version 0.14.0 — 3 November 2026

- Save named mod/perk presets locally between launches, apply them to existing/new/replacement/duplicate weapons, replace a saved set with confirmation and delete presets without altering weapons already edited.
- Reject unavailable preset upgrades without partial application; validate and atomically write local preset storage.
- Rename Stage Replacement to Done, with clear guidance that export/encryption saves the file.
- Remove toolbar ellipses, keep complete button labels, wrap buttons across rows and add descriptive hover help. Editor height follows the resized header.

# Version 0.13.0 — 3 November 2026

- Read and edit compressed GarlicSaves Dead Island 2 results as well as uncompressed Save Wizard exports. Recompute and verify compression framing and CityHash64 checksums on edited exports; keep no-edit exports identical.
- Automatically open validated DI2 decryption results. Reopen Last Decryption restores the latest local package without another service upload.
- Rename Decrypt Selected Pair to Decrypt Selected Save and show parser diagnostics when a package is unsupported.
- Install private Mac compression dependencies automatically; bundle them in Windows. Companion metadata and original packages remain preserved.
- Local round-trip checks do not replace live service re-encryption and PS4 import testing.

# Version 0.12.0 — 2 November 2026

- First-use agreement with unchecked acknowledgment and explicit accept/quit choices; local acceptance survives ordinary updates without registration.
- Editing and service requests remain locked until acknowledgment; Help reopens the agreement and credits.
- Expanded named credits, per-page wiki attribution/license boundaries, gratitude/non-affiliation notices, guide and README coverage.
- Mac packages retain notice files; Windows packages include available dependency licenses and distribution inventories.
- Limited provenance review records no identified bundled Sony SDK/firmware/console keys and the unresolved catalog-table redistribution permission. No legal clearance or ban protection is asserted.

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
