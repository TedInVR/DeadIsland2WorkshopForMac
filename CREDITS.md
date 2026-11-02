# Credits & Acknowledgments

Dead Island 2 Workshop is a free experimental hobby project maintained by **TedInVR**, developed with OpenAI ChatGPT/Codex assistance. Credit below distinguishes material actually distributed, external services, technical references and the creators of products we appreciate. Listing an organization does not mean it contributed to, approved or endorsed Workshop.

## Platforms, game creators and trademarks — with appreciation

- **Sony Interactive Entertainment / PlayStation** — the PlayStation platform and PS4 hardware/software ecosystem. https://www.playstation.com/
- **PLAION, Deep Silver and Deep Silver Dambuster Studios** — publisher/developer of Dead Island 2. The official game's notices also credit additional development by **Fishlabs**. https://deadisland.com/LaunchTrailer
- **Apple** — macOS, Swift, AppKit, WebKit, Security/Keychain and the development tools used by the Mac app. https://developer.apple.com/
- **Microsoft** — Windows, .NET/Windows Forms and WebView2 technology used by the Windows app. https://learn.microsoft.com/microsoft-edge/webview2/

Game/platform names, marks and internal asset identifiers belong to their respective rights holders. Workshop does not claim ownership of them. Its icon and weapon-family silhouettes are original schematic artwork, not extracted game images or official logos. These acknowledgments express appreciation; they are not grants of permission or a claim that no harm can occur.

## Save-editing community and technical references

- **Steffen André Langnes (SteffenL)** — prior Dead Island 2 save-editor work, published manuals, format documentation and published game-data tables used as references. https://steffenl.com/projects/dead-island-2-save-editor and https://github.com/SteffenL/file-format-docs
- **Fristet / Hyundo Yoo** — repository hosting the GUI wrapper and game-data tables from which selected catalog facts were obtained. https://github.com/Fristet/Dead-Island-2-Save-Editor-GUI
- **SurgeStri and contributors** — Slayer Command Center, reviewed as prior community work; no executable or implementation code from this project is bundled. https://github.com/SurgeStri/DI2-Slayer-Command-Center
- **Save Wizard team** — the separate export/import workflow supported by Workshop. No Save Wizard executable, license key or proprietary implementation is included. https://www.savewizard.net/

Workshop's Python parser/editor, desktop shells, updater and service client are independently implemented. Referencing a format or consulting a manual is distinguished here from distributing someone else's program. The upstream projects' own licenses remain applicable to their material; this statement is not a legal-clearance opinion.

**Catalog permission remains unresolved:** selected item names, identifiers and factual fields came from the Fristet-hosted tables credited above. A redistribution license covering those tables has not been verified. Attribution alone is not permission, and Workshop does not claim that the tables are licensed merely because they were publicly accessible. Permission/independent replacement and any compilation/database rights should be reviewed before relying on redistribution clearance.

## External processing service — not bundled code

- **GarlicSaves, earthonion and contributors** — optional hosted save-processing service and published HTOS-web API. https://garlicsaves.com/ and https://github.com/earthonion/HTOS-web
- **hzhreal / HTOS contributors** — upstream save-tooling project acknowledged in the service's ecosystem. https://github.com/hzhreal/HTOS

Workshop sends authorized requests through an independently written HTTP client. The hosted server, console workers, firmware and their code/keys are not included in Workshop. Their operation, licensing and retention have not been independently certified by Workshop. Using an external service does not itself resolve legal or platform-policy questions about decryption or resigning.

## Community text and numerical references

**Dead Island Wiki contributors** supplied community descriptions used to write shortened/paraphrased perk-effect summaries and an XP reference table. Wiki text is credited under **Creative Commons Attribution–ShareAlike 3.0 Unported (CC BY-SA 3.0)**, subject to page-specific exceptions. Changes: text was shortened, paraphrased and grouped; summaries are not verbatim game descriptions. Numerical values and identifiers are identified separately from adapted prose.

The wiki-derived description text and Workshop's adaptations of that text are offered under CC BY-SA 3.0. This applies to that text, not a blanket relicensing of game assets, catalog compilations, upstream software or Workshop's independently written code. The usage agreement does not impose additional restrictions on the rights that this license grants in that material. No wiki images are bundled. Attribution by original page URL also links readers to contributor/edit histories; per-entry URLs remain in catalog.json.

- License: https://creativecommons.org/licenses/by-sa/3.0/
- Full legal code: https://creativecommons.org/licenses/by-sa/3.0/legalcode.en
- Local license reference: third_party_licenses/CC-BY-SA-3.0.txt
- Wiki copyright notice: https://deadisland.fandom.com/wiki/Dead_Island_Wiki:Copyrights
- Perk overview: https://deadisland.fandom.com/wiki/Perks
- XP reference: https://deadisland.fandom.com/wiki/Experience_Points

## Runtime, build and development tools

- **Python Software Foundation and Python contributors** — Python runtime/standard library; PSF/Python license and included third-party notices. https://www.python.org/psf/license/
- **Roman Sirokov and pywebview contributors** — Windows desktop webview integration; BSD-3-Clause. https://github.com/r0x0r/pywebview
- **pythonnet contributors**, **clr-loader**, **cffi**, **pycparser**, **proxy_tools**, **bottle**, **typing_extensions** and other installed dependency authors — Python/.NET and Windows integration, under their respective licenses. Package-specific notices are retained in Windows distributions.
- **PyInstaller contributors** — Windows bundling/bootloader, GPL-2.0 with its bundling exception and specified Apache-2.0 files. The exception does not relicense unrelated dependencies. https://pyinstaller.org/en/stable/license.html
- **OpenSSL Project** — Windows Python TLS libraries; Apache-2.0, with the distributed license and attribution. https://github.com/openssl/openssl
- **libffi and other Python-library contributors** — applicable notices accompany the Python/runtime or dependency licenses.
- **Microsoft WebView2** — SDK redistributables under the included Microsoft license; WebView2 Runtime is separately installed. Its license is not the license of sample code or of pywebview.
- **Pillow contributors** — image/icon conversion in the build environment, under Pillow's license. https://python-pillow.org/
- **jsdom contributors** — development-only interface tests, MIT; not a runtime component. https://github.com/jsdom/jsdom

Windows releases contain a THIRD_PARTY_LICENSES folder and a dependency/file inventory. It can include build-environment packages as well as runtime packages; an inventory entry does not mean that every listed package is linked into the app. Mac releases use the user's separately installed Python and OS frameworks and do not redistribute those runtimes.

## Scope of the Sony-code review

A static source/dependency review and archive filename inspection found no bundled Sony SDK/source files, Sony firmware, console executables, console-key database, or third-party save-editor executable. User-selected encrypted save pairs and local worker credentials are inputs, not bundled application material.

This is a limited provenance review, not a forensic certification, legal opinion, third-party-service audit, or warranty of non-infringement. It does not establish that all game-data identifiers/compilations may be redistributed or that public encryption/resigning functionality is lawful or permitted by every applicable agreement. See LICENSING_REVIEW.md and USAGE_TERMS.md.

## Perk summary source pages

- https://deadisland.fandom.com/wiki/Accurate (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Agile (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Balanced (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Bandolier (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Bloodlust_(Perk) (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Boomstick (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Bullseye (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Concussion (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Damaging (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Disarmer (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Donkinator (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Empowering (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Energizing (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Enhanced (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Ferocious (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Guardian (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Hair-Trigger (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Hard_and_Fast (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Headhunter_(Perk) (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Honed (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Infectious (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Cremator_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Electrocutor_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Impactor_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Liquidator_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Mutilator_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Melee_Puncturator_Mod (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Merciless (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Overkill (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Perks (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Primed (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Reaper_(Perk) (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Revolutionary (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Rubber_Bullets (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Savage (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Shockwave (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Sizzler (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Skilled (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Special_Sauce (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Spitting_Fire (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Static_Charge (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Stopping_Power (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Threefer (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Top_Up (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
- https://deadisland.fandom.com/wiki/Vigilant (Dead Island Wiki contributors; shortened/paraphrased; CC BY-SA 3.0, subject to page-specific exceptions)
