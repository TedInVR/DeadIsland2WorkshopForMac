# Version history

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
