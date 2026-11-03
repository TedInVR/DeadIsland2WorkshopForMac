# GarlicSaves integration preview — 0.11.0

Workshop includes an opt-in client for the published [GarlicSaves REST API](https://github.com/earthonion/HTOS-web/blob/main/API.md), implemented independently using Python standard-library HTTPS and ZIP handling. API protocol and authentication were checked against [routes/api_v1.py](https://github.com/earthonion/HTOS-web/blob/main/routes/api_v1.py). The service processes jobs using remote console workers; the desktop app does not perform local console cryptography.

## Credentials and file flow

Users enter their worker key in the app. It is saved in macOS Keychain or Windows Credential Manager and loaded automatically on later launches. No worker key is bundled in source, downloads, settings, logs, or backups. Cross-origin redirects are refused.

Test Connection reads the jobs endpoint without uploading saves. Decrypt submits only a selected PS4 save pair after confirmation and local backups, requesting complete metadata. Generic packages from other games are retained intact; only supported Dead Island 2 data can open in the internal editor. Re-encryption accepts an unchanged complete package, a validated edited Dead Island 2 file, or a complete externally edited ZIP with matching account and game metadata.

Resign submits one selected save or sequential jobs for a source profile on one drive. Source and existing destination saves receive named backups before processing. Completed pairs are staged locally. Explicit USB installation backs up each current destination again before replacement. Live service compatibility and PS4 acceptance depend on the game and provider.

## Verification and limits

Local tests exercise protocol requests, status polling, credential storage, archive boundaries, source preservation, named-backup integrity, destination replacement failures, generic package preservation, and simulated account transfers. Platform CI checks native credential APIs and app packaging. These checks do not establish a live, console-accepted round trip.

The internal game-data editor supports sectioned uncompressed Dead Island 2 saves. Unsupported representations remain intact as generic packages. Metadata and companion files are retained. The online service controls availability, processing queues and remote retention. The console-worker config file is not needed for the desktop connection.

See the [User Guide](USER_GUIDE.md) for setup, account transfers, backup restoration and retained-file handling.

## Verified re-encryption — 0.16.0

A private live round trip showed that the returned SFO account bytes were reversed while the edited gameplay file and other companion files survived exactly. The desktop API adapter now inspects the encrypted result through a fresh decrypt job. It requires the intended account/title, identical gameplay files and keystone before releasing a USB-ready pair. Only the exact reversed-account condition permits one retry using a byte-reversed account wire value; the submitted package metadata and USB account folder keep their original identity. The retry must independently pass verification. Other mismatches or failed verification stop installation. No private sample identifiers are included in source or tests.

The highlighted Finalize and Re-encrypt action backs up and replaces the chosen USB pair only after these checks. This is verification of returned metadata and payload, not a proof of console acceptance or in-game safety.

## Post-game header — 0.18.0

The post-game sample uses a different game-build integer and the newer of two observed save revisions. The initial uint32 is not a fixed magic number. The header validator now accepts variable nonzero build values with the two observed revision fields and the expected marker/compression tag. These header fields remain byte-for-byte unchanged on export; structure and compressed checksum checks remain mandatory.
