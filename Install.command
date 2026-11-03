#!/bin/bash
set -euo pipefail
UNATTENDED=0
[[ "${1:-}" == "--unattended" ]] && UNATTENDED=1
SOURCE="$(cd "$(dirname "$0")" && pwd)"
APP="${DI2_WORKSHOP_INSTALL_APP:-/Applications/Dead Island 2 Workshop.app}"
DEV="${DI2_WORKSHOP_DEV_DIR:-/Applications/Dead Island 2 Workshop Development}"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/DI2Workshop-build.XXXXXX")"
trap 'rm -rf "$BUILD"' EXIT
fail() { echo; echo "$1"; echo; if [[ "$UNATTENDED" == "0" ]]; then read -r -p "Press Return to close…" _reply; fi; exit 1; }
echo "Dead Island 2 Workshop 0.14.0 — Mac preview"
echo "Building your Mac app. Compression support is installed automatically in Workshop’s private runtime."
[[ "$(uname -s)" == "Darwin" ]] || fail "Run this installer on your Mac."
if pgrep -f '/Dead Island 2 Workshop.app/Contents/MacOS/' >/dev/null 2>&1; then
    fail "Please quit Dead Island 2 Workshop, then run this installer again."
fi
SWIFTC="$(/usr/bin/xcrun --find swiftc 2>/dev/null)" || fail "Apple Command Line Tools are required. Open Terminal and run: xcode-select --install"
SDK="$(/usr/bin/xcrun --sdk macosx --show-sdk-path)" || fail "Unable to locate the macOS SDK."
PYTHON=""
for candidate in "${DI2_WORKSHOP_RUNTIME_PYTHON:-/opt/homebrew/bin/python3}" /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /usr/local/bin/python3 /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; assert (3,9) <= sys.version_info < (3,14)' 2>/dev/null; then PYTHON="$candidate"; break; fi
done
[[ -n "$PYTHON" ]] || fail "Python 3.9–3.13 is required for the compression runtime. Install a supported Python version, then retry."
RUNTIME="${DI2_WORKSHOP_RUNTIME_DIR:-$HOME/Library/Application Support/Dead Island 2 Workshop/Runtime}"
if [[ ! -x "$RUNTIME/bin/python3" ]] || ! "$RUNTIME/bin/python3" -c 'import zstandard,cityhash; assert zstandard.__version__ == "0.25.0"' 2>/dev/null; then
    echo "Preparing Workshop compression support…"
    "$PYTHON" -m venv "$RUNTIME" || fail "Could not prepare Workshop’s private Python runtime."
    "$RUNTIME/bin/python3" -m pip install --disable-pip-version-check --only-binary=:all: -r "$SOURCE/requirements-runtime.txt" || fail "Compression support could not be installed. Check your internet connection and retry. Your existing app is unchanged."
fi
"$RUNTIME/bin/python3" -c 'import zstandard,cityhash' || fail "Workshop’s compression support is incomplete."
"$PYTHON" -c 'import py_compile,sys; [py_compile.compile(x,doraise=True,cfile="/tmp/di2-workshop-check.pyc") for x in sys.argv[1:]]' "$SOURCE/preset_storage.py" "$SOURCE/save_codec.py" "$SOURCE/legal_state.py" "$SOURCE/ps4_backups.py" "$SOURCE/character_editor.py" "$SOURCE/credential_store.py" "$SOURCE/garlic_service.py" "$SOURCE/server.py" "$SOURCE/save_browser.py" "$SOURCE/backup_storage.py" "$SOURCE/save_core.py" "$SOURCE/updater.py"
mkdir -p "$BUILD/Dead Island 2 Workshop.app/Contents/MacOS" "$BUILD/Dead Island 2 Workshop.app/Contents/Resources"
if ! "$SWIFTC" -sdk "$SDK" -O -framework AppKit -framework WebKit "$SOURCE/Workshop.swift" -o "$BUILD/Dead Island 2 Workshop.app/Contents/MacOS/DI2Workshop"; then
    fail "The Mac build did not finish. Send the compiler message above to ChatGPT. Your existing app and saves have not been changed."
fi
cp "$SOURCE/Info.plist" "$BUILD/Dead Island 2 Workshop.app/Contents/Info.plist"
for name in server.py preset_storage.py save_codec.py requirements-runtime.txt legal_state.py ps4_backups.py character_editor.py resource_catalog.json credential_store.py garlic_service.py save_browser.py backup_storage.py save_core.py index.html Workshop.icns catalog.json updater.py User-Guide.html USER_GUIDE.md README.txt USAGE_TERMS.md CREDITS.md Credits.html THIRD_PARTY_NOTICES.md LICENSING_REVIEW.md; do cp "$SOURCE/$name" "$BUILD/Dead Island 2 Workshop.app/Contents/Resources/$name"; done
printf '%s\n' "$RUNTIME/bin/python3" > "$BUILD/Dead Island 2 Workshop.app/Contents/Resources/PythonPath.txt"
cp -R "$SOURCE/third_party_licenses" "$BUILD/Dead Island 2 Workshop.app/Contents/Resources/third_party_licenses"
/usr/bin/codesign --force --sign - "$BUILD/Dead Island 2 Workshop.app"
mkdir -p "$DEV"
if [[ "$SOURCE" != "$DEV" ]]; then
    for name in Install.command Workshop.swift server.py preset_storage.py save_codec.py requirements-runtime.txt legal_state.py ps4_backups.py character_editor.py resource_catalog.json credential_store.py garlic_service.py save_browser.py backup_storage.py save_core.py index.html Info.plist Workshop.icns catalog.json updater.py User-Guide.html USER_GUIDE.md README.txt USAGE_TERMS.md CREDITS.md Credits.html THIRD_PARTY_NOTICES.md LICENSING_REVIEW.md; do cp "$SOURCE/$name" "$DEV/$name"; done
fi
if [[ "$SOURCE" != "$DEV" ]]; then cp -R "$SOURCE/third_party_licenses" "$DEV/"; fi
chmod +x "$DEV/Install.command"
if pgrep -f "/Dead Island 2 Workshop.app/Contents/MacOS/DI2Workshop" >/dev/null 2>&1; then fail "Please quit Workshop before installing this update."; fi
if [[ -d "$APP" ]]; then
    mv "$APP" "$BUILD/Previous.app"
fi
if ! /usr/bin/ditto "$BUILD/Dead Island 2 Workshop.app" "$APP"; then
    [[ -d "$BUILD/Previous.app" ]] && /usr/bin/ditto "$BUILD/Previous.app" "$APP"
    fail "Installation did not complete. Please send this Terminal output to ChatGPT."
fi
/usr/bin/touch "$APP"
echo "Installed: $APP"
# The persistent helper uses the installed app version and an existing gh login
# when private-repository authentication is required. No credentials are copied.
if [[ "${DI2_WORKSHOP_SKIP_AGENT:-0}" != "1" ]]; then
    mkdir -p "$HOME/Library/Application Support/Dead Island 2 Workshop"
    cp "$SOURCE/updater.py" "$HOME/Library/Application Support/Dead Island 2 Workshop/updater.py"
    if ! DI2_WORKSHOP_UPDATE_PYTHON="$PYTHON" "$PYTHON" "$SOURCE/updater.py" --install-agent; then
        echo "App installed; the background updater could not be configured. See Help > Update Status."
    fi
fi
if [[ "$UNATTENDED" == "0" ]]; then
    echo "Opening Workshop…"
    /usr/bin/open "$APP"
else
    echo "Updated successfully. Workshop remains closed."
fi
