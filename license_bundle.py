"""Include license/notice material and a reviewable build/distribution inventory."""
import hashlib,importlib.metadata as metadata,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def collect(folder):
    target=folder/'THIRD_PARTY_LICENSES';target.mkdir(exist_ok=True);packages=[]
    for dist in sorted(metadata.distributions(),key=lambda d:d.metadata.get('Name','').lower()):
        name=dist.metadata.get('Name','unknown');safe=re.sub(r'[^A-Za-z0-9._-]','_',name+'-'+dist.version);out=target/safe;out.mkdir(exist_ok=True)
        # Preserve the installed metadata verbatim; serializing email headers can fail
        # on valid package descriptions containing unindented multiline prose.
        raw=dist.read_text('METADATA') or dist.read_text('PKG-INFO')
        if raw is None:raw=json.dumps(list(dist.metadata.items()),ensure_ascii=False,indent=2)
        (out/'METADATA.txt').write_text(raw,encoding='utf-8');copied=[]
        for file in dist.files or []:
            basename=Path(str(file)).name
            if not re.match(r'(?i)^(licen[cs]e|copying|copyright|notice|authors)([._-]|$)',basename):continue
            source=Path(dist.locate_file(file))
            if not source.is_file():continue
            destination=out/(str(len(copied)+1)+'-'+basename)
            shutil.copyfile(source,destination);copied.append(destination.name)
        packages.append({'name':name,'version':dist.version,'license':dist.metadata.get('License-Expression') or dist.metadata.get('License'),'project_urls':dist.metadata.get_all('Project-URL',[]),'license_files':copied,'inventory_scope':'installed build environment; not every package is bundled'})
    # pywebview's Microsoft SDK terms are outside its dist-info directory.
    import webview
    microsoft=Path(webview.__file__).parent/'lib'/'Microsoft.Web.WebView2.LICENSE.md'
    # Some pywebview wheels omit this notice although their source includes it.
    # Retain the checked-in upstream notice for that pinned dependency.
    if not microsoft.is_file():microsoft=ROOT/'third_party_licenses'/'Microsoft-WebView2-LICENSE.md'
    if not microsoft.is_file():raise RuntimeError('Microsoft WebView2 license notice is missing.')
    shutil.copyfile(microsoft,target/'Microsoft-WebView2-LICENSE.md')
    for source in (ROOT/'third_party_licenses').iterdir():
        if source.is_file() and not (target/source.name).exists():shutil.copyfile(source,target/source.name)
    (target/'OpenSSL-ATTRIBUTION.txt').write_text('OpenSSL Project; Copyright (c) 1998-2024 The OpenSSL Project. Copyright (c) 1995-1998 Eric A. Young, Tim J. Hudson.\nPython 3.11 Windows TLS libraries use OpenSSL 3.x, under Apache-2.0; see OpenSSL-3.0.13-LICENSE.txt and https://github.com/openssl/openssl.\n',encoding='utf-8')
    (target/'README.txt').write_text('Package licenses/notices are copied from the installed build distributions. METADATA and the inventory include build-only packages as well as runtime packages; that is not a claim that every package is linked. Microsoft WebView2 terms and applicable runtime notices are retained separately. See CREDITS.md and THIRD_PARTY_NOTICES.md. No licenses for unrelated materials are inferred from dependency licenses.\n',encoding='utf-8')
    return packages

def audit_files(folder):
    files=[]
    for file in folder.rglob('*'):
        if not file.is_file():continue
        relative=file.relative_to(folder).as_posix();low=relative.lower()
        if file.suffix.lower() in ('.prx','.sprx','.self','.elf','.pkg','.pup','.sav','.sfo','.bin') or re.search(r'(^|/)(libsce|sony-sdk|ps4sdk|sce_sdk)',low):raise RuntimeError('Unexpected console/save artifact in distribution: '+relative)
        files.append({'path':relative,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    return files

def finish(folder,packages):
    inventory={'scope':'Installed build-package metadata and final distribution-file hashes; not legal clearance or proof of binary provenance.','packages':packages,'files':audit_files(folder)}
    (folder/'DISTRIBUTION-INVENTORY.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
