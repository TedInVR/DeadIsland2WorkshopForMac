#!/bin/bash
set -euo pipefail
UNATTENDED=0
[[ "${1:-}" == "--unattended" ]] && UNATTENDED=1
SOURCE="$(cd "$(dirname "$0")" && pwd)"
APP="/Applications/Dead Island 2 Workshop.app"
DEV="/Applications/Dead Island 2 Workshop Development"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/DI2Workshop-build.XXXXXX")"
trap 'rm -rf "$BUILD"' EXIT
fail() { echo; echo "$1"; echo; if [[ "$UNATTENDED" == "0" ]]; then read -r -p "Press Return to close…" _reply; fi; exit 1; }
echo "Dead Island 2 Workshop 0.9.0 — Mac preview"
echo "Building your Mac app. No additional Python packages are needed."
[[ "$(uname -s)" == "Darwin" ]] || fail "Run this installer on your Mac."
if pgrep -f '/Dead Island 2 Workshop.app/Contents/MacOS/' >/dev/null 2>&1; then
    fail "Please quit Dead Island 2 Workshop, then run this installer again."
fi
SWIFTC="$(/usr/bin/xcrun --find swiftc 2>/dev/null)" || fail "Apple Command Line Tools are required. Open Terminal and run: xcode-select --install"
SDK="$(/usr/bin/xcrun --sdk macosx --show-sdk-path)" || fail "Unable to locate the macOS SDK."
PYTHON=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; assert sys.version_info >= (3,9)' 2>/dev/null; then PYTHON="$candidate"; break; fi
done
[[ -n "$PYTHON" ]] || fail "Python 3.9 or newer is required. Install Python 3, then rerun this installer."
"$PYTHON" -c 'import py_compile,sys; [py_compile.compile(x,doraise=True,cfile="/tmp/di2-workshop-check.pyc") for x in sys.argv[1:]]' "$SOURCE/server.py" "$SOURCE/save_browser.py" "$SOURCE/backup_storage.py" "$SOURCE/save_core.py" "$SOURCE/updater.py"
mkdir -p "$BUILD/Dead Island 2 Workshop.app/Contents/MacOS" "$BUILD/Dead Island 2 Workshop.app/Contents/Resources"
if ! "$SWIFTC" -sdk "$SDK" -O -framework AppKit -framework WebKit "$SOURCE/Workshop.swift" -o "$BUILD/Dead Island 2 Workshop.app/Contents/MacOS/DI2Workshop"; then
    fail "The Mac build did not finish. Send the compiler message above to ChatGPT. Your existing app and saves have not been changed."
fi
cp "$SOURCE/Info.plist" "$BUILD/Dead Island 2 Workshop.app/Contents/Info.plist"
for name in server.py save_browser.py backup_storage.py save_core.py index.html Workshop.icns catalog.json updater.py User-Guide.html USER_GUIDE.md README.txt; do cp "$SOURCE/$name" "$BUILD/Dead Island 2 Workshop.app/Contents/Resources/$name"; done
/usr/bin/codesign --force --sign - "$BUILD/Dead Island 2 Workshop.app"
mkdir -p "$DEV"
if [[ "$SOURCE" != "$DEV" ]]; then
    for name in Install.command Workshop.swift server.py save_browser.py backup_storage.py save_core.py index.html Info.plist Workshop.icns catalog.json updater.py User-Guide.html USER_GUIDE.md README.txt; do cp "$SOURCE/$name" "$DEV/$name"; done
fi
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
mkdir -p "$HOME/Library/Application Support/Dead Island 2 Workshop"
cp "$SOURCE/updater.py" "$HOME/Library/Application Support/Dead Island 2 Workshop/updater.py"
if ! "$PYTHON" "$SOURCE/updater.py" --install-agent; then
    echo "App installed; the background updater could not be configured. Use Help > Download Updates."
fi
if [[ "$UNATTENDED" == "0" ]]; then
    echo "Opening Workshop…"
    /usr/bin/open "$APP"
else
    echo "Updated successfully. Workshop remains closed."
fi
