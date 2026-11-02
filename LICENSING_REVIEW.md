# Licensing and provenance review — 2 November 2026

This is a technical provenance/risk record, not legal advice or legal clearance.

## Reviewed scope and findings

- Reviewed Workshop's source imports, build/installer configuration, current dependencies, Mac installer archive contents and the published Windows 0.11.0 archive filenames/notices.
- No Sony SDK/source/firmware, console executable, console-key database or third-party editor executable was identified in those distributions. Windows DLLs identified by names/build dependencies belong to the Python/.NET/Microsoft stack, not a bundled Sony SDK. Binary filenames and metadata are not a forensic proof of origin.
- Mac resources are distributed from an explicit source-file list. The Mac runtime/frameworks are supplied by the user's OS/Python installation.
- The independent GarlicSaves client uses the documented API. The service/server/console-worker code, firmware, legality and retention are outside this review. No claim is made that moving processing to a service removes circumvention or contractual risk.
- Catalog facts reference SteffenL's data as hosted by Fristet. A license granting redistribution of those tables was not verified. This is an unresolved permission/compilation-rights question; obtain appropriate permission or an independently cleared replacement before asserting clearance. Attribution alone does not solve it.
- Wiki-derived effect prose now has explicit contributor/source attribution, a modifications statement and CC BY-SA 3.0 terms. No wiki/game images are bundled. Page-specific exceptions and underlying third-party rights still matter.
- Windows packaging now collects package license/notice files and runtime-specific notices into THIRD_PARTY_LICENSES and records a distribution/file inventory. Dependency-license compliance remains a release-maintenance task, not a one-time warranty.

## First-use notice and privacy

USAGE_TERMS.md explains noncommercial experimental intent, offline-only modified gameplay, compliance obligations, save/account/device/service risks, warranty/liability limits to the extent lawful, and non-waivable rights. It explicitly says third parties are not bound, offline/free use is not clearance, and no ban protection or immunity is promised. The acknowledgment is local only: version, document hash, acceptance flag and time, without a central registry, identity, PSN ID or agreement telemetry. A click is not described as a verified signature or proof that a court must enforce the notice.

## Issues that a disclaimer cannot resolve

Sony's terms address modification, reverse engineering, security/circumvention and automation as well as cheating; a rule against online use does not itself establish permitted offline use. PLAION's published EULA also contains modification and information-extraction restrictions. U.S. Copyright Office guidance explains that section 1201 can address circumvention and provision of certain circumvention products/services. Exemptions and their application require specific legal analysis. Noncommercial purpose is one consideration in copyright analysis, not universal permission. Do not present free distribution, gratitude or “no harm intended” as legal defenses that guarantee protection.

For actual publication/distribution risk decisions, have an attorney familiar with software, game-platform contracts and anti-circumvention law review the shipped functionality and data, including the public decryption/resigning integration. The first-use notice does not make Sony, a publisher or a service operator waive its rights. The project owner has not been promised immunity from claims, suspension, penalties or enforcement.

## Primary policy/license references

- https://www.playstation.com/en-us/legal/terms-of-service/
- https://www.playstation.com/en-us/support/account/suspensions/
- https://plaion.com/tos
- https://copyright.gov/dmca/
- https://www.copyright.gov/fair-use/more-info.html
- https://community.fandom.com/wiki/Help:Licensing
- https://deadisland.fandom.com/wiki/Dead_Island_Wiki:Copyrights
- https://creativecommons.org/licenses/by-sa/3.0/legalcode
- https://pyinstaller.org/en/stable/license.html
- https://github.com/earthonion/HTOS-web/blob/main/API.md
- https://github.com/Fristet/Dead-Island-2-Save-Editor-GUI
