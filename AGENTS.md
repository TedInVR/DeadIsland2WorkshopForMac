# Workshop development and releases

## Standing publication authorization

On 3 November 2026, the repository owner explicitly authorized publishing version 0.14.0 and gave permanent permission to publish future changes, updates and fixes for this app to its configured public GitHub update source, TedInVR/DeadIsland2WorkshopForMac. Treat requested app changes as including implementation, appropriate tests, packaging, publication and verification of the Mac update source and Windows release. Do not routinely ask for publication permission again.

Keep the existing application identity, user settings, presets, backups and credential storage through updates. Never include personal save files, worker keys, private profile imports or other user-specific data in public source, tests, documentation or release archives. Use synthetic public fixtures; private integration fixtures remain local. Report the actual validation performed and any outstanding platform or live-console limitations. This standing authorization does not override tool approval requirements or platform safety rules.

## User interface preferences — 4 November 2026

Show an exact-model copy count beside weapon names, scoped to the chosen character/location and including staged changes. Provide an obvious Select All / Edit Selected workflow for one backpack; exclude other characters, lockers, deletions and read-only attacks unless explicitly selected. Prefer compact panels, tabs and collapsible secondary information over scrolling the main editor or dialogs. Keep labels readable; show detailed explanations on hover/focus and in Help. Give active service jobs a prominent, gently pulsing status with reduced-motion support, elapsed wait and fresh status confirmation; animation is not a completion estimate. Provide a simple Guide Me entry point that walks through opening/decryption, editing, re-encryption and console transfer, distinguishing GarlicSaves from the external Save Wizard workflow. Do not claim USB readiness before actual verified finalization or the user's explicit external-workflow acknowledgment.

## Story reset invariant

Story reset must preserve the selected character’s current XP/level regardless of any previous manual level edits. Preserve inventory, weapons, resources, skills and character identity; generate the initial campaign state in the existing Regular/NG+ mode. Never require another character to be kept at an early story point. Never publish personal save templates. Clearly distinguish byte-preservation checks from unverified in-game behavior.

## Story reset regression — 4 November 2026

A live-console test of 0.22.0 showed completed progress bars and New Game instead of Continue after clearing campaign/location state. Treat generated empty campaign reset as disproven. Version 0.22.1 blocks reset writes and disables the control. Do not re-enable this method or call byte preservation evidence of a working mission replay. Recovery requires a pre-reset backup; an app update does not repair affected saves. A future implementation needs initialized mission, objective, world, location and menu-summary state, while preserving character data and requiring no permanent donor.
