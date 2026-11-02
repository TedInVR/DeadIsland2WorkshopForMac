# GarlicSaves integration preview — 0.10.1

Workshop now includes an opt-in client for the published [GarlicSaves REST API](https://github.com/earthonion/HTOS-web/blob/main/API.md), implemented independently using Python standard-library HTTPS and ZIP handling. API protocol and authentication were checked against [routes/api_v1.py](https://github.com/earthonion/HTOS-web/blob/main/routes/api_v1.py). The server processes jobs using remote console workers; the desktop app does not perform local console cryptography.

Users enter their private worker key locally. Test Connection reads /jobs without uploading a save. Decrypt submits only the selected original PS4 pair after confirmation and local backups, requesting include_sce_sys=true. Encrypt submits the validated edited file together with every original companion file and sce_sys metadata, using the original account ID. Results are retained in unique private local session folders. The key is saved privately by macOS Keychain or Windows Credential Manager and automatically loaded on later launches. It is not stored in app settings, sent in URLs, logged, included in result archives, or bundled in GitHub source/downloads. Cross-origin redirects are refused so credentials cannot be forwarded to another host.

## Verification and limitations

- The user supplied an original encrypted pair for private local inspection. Its 96-byte .bin has the expected pfsSKKey header. That does not establish that the pair cryptographically matches.
- Local tests cover the API wire format, status polling, credential handling, malicious ZIP boundaries, metadata account/title matching, source preservation, and a simulated service round trip using the existing decrypted fixture.
- No worker key is available in this development session. No user saves have been uploaded to GarlicSaves by the developer. Live service authentication, actual decrypted output compatibility, and a console-accepted encryption round trip remain untested.
- The game-data reader supports sectioned uncompressed PS4 exports. If GarlicSaves returns another representation, the app retains its full ZIP and reports unsupported format. A real decrypted result is needed to add and verify any conversion.
- The provided console-worker config is unnecessary for this desktop API integration.

See [User Guide](USER_GUIDE.md#ps4-encryption-and-save-wizard) for the step-by-step workflow and retained-file handling. The third-party service controls availability, remote processing, and retention.
