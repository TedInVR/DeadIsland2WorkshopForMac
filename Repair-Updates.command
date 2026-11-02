#!/bin/bash
set -euo pipefail
echo "Workshop update repair — quit Workshop before continuing."
WORKSHOP_PYTHON=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; assert sys.version_info >= (3,9)' 2>/dev/null; then WORKSHOP_PYTHON="$candidate"; break; fi
done
if [[ -z "$WORKSHOP_PYTHON" ]]; then echo "Python 3.9 or newer was not found.";exit 1;fi
if ! "$WORKSHOP_PYTHON" - <<'PY'
import fcntl,importlib.util,plistlib,time
from pathlib import Path
support=Path.home()/'Library/Application Support/Dead Island 2 Workshop'
file=support/'updater.py'
if not file.is_file():raise SystemExit('The installed update helper is missing. Use the latest Mac installer.')
spec=importlib.util.spec_from_file_location('workshop_repair',file)
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
with (support/'updater-worker.lock').open('a') as lock:
    print('Waiting for any existing update check...',flush=True)
    fcntl.flock(lock,fcntl.LOCK_EX)
    if u.app_running():raise SystemExit('Quit Workshop with Command-Q, then run this repair again.')
    print('Downloading and verifying the latest update...',flush=True)
    m=u.manifest();u.download(m);u.atomic_json(support/'pending-update.json',m)
    print('Installing now. Please keep Workshop closed...',flush=True)
    result=u.run()
    with (u.APP/'Contents/Info.plist').open('rb') as f:actual=plistlib.load(f)['CFBundleShortVersionString']
    if actual!=m['version']:raise SystemExit('Installation did not reach version '+m['version']+'. Result: '+str(result))
    u.atomic_json(support/'update-status.json',{'status':'installed','version':actual,'message':'Update repair installed version '+actual+' in Applications.','time':time.time()})
    print('Installed version '+actual+'. You can now open Workshop from Applications.',flush=True)
PY
then
    echo "Repair did not finish. Keep this Terminal output so we can see the error."
    read -r -p "Press Return to close…" _reply
    exit 1
fi
read -r -p "Press Return to close…" _reply
