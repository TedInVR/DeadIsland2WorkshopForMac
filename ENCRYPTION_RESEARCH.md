# External PS4 encryption service research

Workshop does not currently decrypt or re-encrypt PS4 USB save containers. Save Wizard remains the tested extraction/import workflow for this project.

## A documented integration candidate

[GarlicSaves](https://garlicsaves.com/) runs online PS4/PS5 save tools based on [HTOS-web](https://github.com/earthonion/HTOS-web). Its published [API documentation](https://github.com/earthonion/HTOS-web/blob/main/API.md) describes REST jobs for decrypt, encrypt, and resign, with status polling and a result ZIP. Requests require an `X-Worker-Key` obtained through the service's Contribute page. The availability and intended use of that access for an ordinary desktop-app user still needs confirmation with the service; documentation alone does not establish that a key will be granted.

The backend uses participating jailbroken consoles. The person using the hosted service need not be the person supplying a console, but running the same server software on a Mac does not provide the missing console worker.

## Proposed file flow

1. Choose the original encrypted PS4 save and its paired `.bin` file.
2. With API access and the user's approval to send these files to the named service, submit a decrypt job and request the `sce_sys` metadata.
3. Keep the original container, account metadata, and all extracted companion files together locally. Confirm the returned Dead Island 2 game-data format is supported by Workshop; it may differ from the sectioned uncompressed Save Wizard export currently tested.
4. Edit a separate game-data copy, retain the other files and metadata, then submit the complete package for encryption back to the same account.
5. Download the new encrypted pair into a separate PS4 folder and test importing it on the console. Preserve the original backup.

No account has been created, API key obtained, or personal save uploaded during this research. No live encryption integration is included in the current release. A compatible service account/key, confirmation of automation support, and an end-to-end Dead Island 2 round trip are needed before the app can offer this as a working feature. A web frontend or Discord interface alone is not evidence of an unauthenticated automation endpoint.

Primary sources: [HTOS](https://github.com/hzhreal/HTOS), [HTOS-web](https://github.com/earthonion/HTOS-web), [REST API](https://github.com/earthonion/HTOS-web/blob/main/API.md), [GarlicSaves About](https://garlicsaves.com/about).
