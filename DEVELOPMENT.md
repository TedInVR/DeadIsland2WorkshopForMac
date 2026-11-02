# Development and updates

The native shell is AppKit + WKWebView. A local Python server owns an independent save parser and serializer. Save data stays local. There is no Save Wizard decryption backend.

## Files

| File | Purpose |
| --- | --- |
| `Workshop.swift` | Native window, menus, file panels, update controls, app lock |
| `server.py` | Loopback HTTP service and edit/export API |
| `save_core.py` | Sectioned PS4 export reader, edits, creation/deletion/replacement |
| `catalog.json` | Game-data names/identifiers and provenance |
| `index.html` | Editor interface |
| `Install.command` | Local Mac build/install; `--unattended` leaves the app closed |
| `updater.py` | Manifest/checksum checks, private `gh` access, queued/background installs |
| `USER_GUIDE.md` / `User-Guide.html` | Repository and bundled local guide |
| `package_release.py` | Explicit-allowlist ZIP packaging and manifest generation |
| `update.json` | Latest version, versioned ZIP path, SHA-256 |
| `downloads/` | Versioned and latest installer ZIPs |

## Verify

- `python3 -m unittest test_updater.py` — isolated updater regression tests.
- `python3 test_core.py /path/to/decrypted.sav` — local save regression suite, including original fixture-specific profile expectations. The personal fixture is not committed.
- `bash -n Install.command` and Python compilation checks.
- Build/install on macOS to test the AppKit shell and launchd agent.
- Test the exported save through Save Wizard and PS4 separately; a structural round trip cannot prove in-game compatibility.

The development UI integration test (`test_ui.cjs`) uses jsdom and a local decrypted save. Run `npm install`, then `DI2_TEST_SAVE=/path/to/decrypted.sav node test_ui.cjs` from the repository. This dependency is development-only and not part of the app. Like the save regression suite, this test expects the original development fixture; the fixture is not committed.

## Publish an update

1. Update the version in `Info.plist`, `Workshop.swift`, `index.html`, `README.md`, and `README.txt`; increment `CFBundleVersion` in the plist.
2. Update `CHANGELOG.md` and both forms of the guide. Keep installer resource lists and the packaging allowlist in sync.
3. Run the relevant tests and build on a Mac.
4. Run `python3 package_release.py`. Update manifest release notes if needed.
5. Commit the source, versioned ZIP, latest ZIP, and `update.json` together. Do not change a versioned ZIP after publishing it; bump the version instead.

Private repository downloads require authentication. The updater first tries an existing `gh api` login, then HTTPS raw download (which works only if visibility permits it). The browser menu uses GitHub's normal authenticated download page. No token is embedded in source or packages.

Automatic updates run from a per-user LaunchAgent every 900 seconds. An app-open check prevents automatic network/download/build work while running. A shared/exclusive file lock and a second installer process check guard replacement. Manual checks may download and queue updates while the app is open. The automatic install never reopens the app.

## Privacy

Never commit actual saves, PSN credentials, Save Wizard credentials/license keys, GitHub tokens, startup logs, or screenshots containing personal information. The packaging script uses an explicit list and `.gitignore` excludes save files. The updater does not send save data to GitHub.

The scanner tests use synthetic account IDs and temporary drive trees. `DI2_WORKSHOP_SCAN_ROOTS` may contain a JSON list of explicit development roots; `DI2_WORKSHOP_BACKUP_DIR` isolates backups/settings during tests. Do not commit private profile mappings or actual save containers.
