const {JSDOM}=require('jsdom');
const fs=require('fs'), cp=require('child_process'),os=require('os'),path=require('path');
const assert=require('assert');
(async()=>{
 const ready=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'di2-ui-')),'ready');
 const usbRoot=path.join(path.dirname(ready),'USB'),account='0000000000000001',game=path.join(usbRoot,'PS4','SAVEDATA',account,'CUSA01014');fs.mkdirSync(game,{recursive:true});
 fs.writeFileSync(path.join(game,'DeadIsland2SaveGame'),'encrypted example');fs.writeFileSync(path.join(game,'DeadIsland2SaveGame.bin'),Buffer.concat([Buffer.from('pfsSKKey'),Buffer.alloc(88)]));
 fs.copyFileSync(process.env.DI2_TEST_SAVE||'../upload/ue4savegame.ps4.sav',path.join(game,'export.sav'));
 const proc=cp.spawn('python',[path.join(__dirname,'server.py'),'--ready',ready],{env:{...process.env,DI2_WORKSHOP_BACKUP_DIR:path.join(path.dirname(ready),'backups'),DI2_WORKSHOP_SCAN_ROOTS:JSON.stringify([usbRoot])}});

 try{
  for(let i=0;i<100&&!fs.existsSync(ready);i++)await new Promise(r=>setTimeout(r,40));
  const base=fs.readFileSync(ready,'utf8');const source=fs.readFileSync(process.env.DI2_TEST_SAVE||'../upload/ue4savegame.ps4.sav');
  const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{url:base,runScripts:'dangerously',beforeParse(w){w.confirm=()=>true;w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};w.fetch=(url,o={})=>fetch(base+url,{...o,body:url==='open'?source:o.body});w.webkit={messageHandlers:{workshop:{postMessage(x){w.exported=x}}}}}});
  const w=dom.window,d=w.document;
  await w.legalBoot;
  assert(d.querySelector('#agreement-dialog').open);
  assert(!d.querySelector('#agreement-check').checked);assert(d.querySelector('#agreement-accept').disabled);
  let locked=await fetch(base+'saves');assert.equal(locked.status,403);
  locked=await fetch(base+'open',{method:'POST',body:'{}'});assert.equal(locked.status,403);
  await w.acceptAgreement();assert(d.querySelector('#agreement-dialog').open);
  d.querySelector('#agreement-check').click();await w.acceptAgreement();assert(!d.querySelector('#agreement-dialog').open);
  await w.showUsageTerms();assert(d.querySelector('#legal-document-text').textContent.includes('TO THE MAXIMUM EXTENT'));d.querySelector('#legal-document-dialog').close();
  const reload=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{url:base,runScripts:'dangerously',beforeParse(x){x.HTMLDialogElement.prototype.showModal=function(){this.open=true};x.fetch=(url,o={})=>fetch(base+url,o)}});
  await reload.window.legalBoot;assert(!reload.window.document.querySelector('#agreement-dialog').open);reload.window.close();
  Object.defineProperty(d.querySelector('#file'),'files',{value:[{name:'test.sav'}]});await d.querySelector('#file').onchange({target:d.querySelector('#file')});
  const backup=w.eval('data.backup');assert.equal(backup.reason,'opened');assert(fs.readFileSync(backup.path).equals(source));
  assert.equal(w.eval('data.profiles.length'),10);assert([...d.querySelectorAll('#group option')].some(x=>x.textContent.includes('Ryan — New Game Plus (active)')));
  const raven=w.eval('data.weapon_catalog.find(w=>w.name.toUpperCase()==="RAVEN")');
  assert.equal(w.weaponVisual(raven).label,'Sporting rifle');
  assert(d.querySelector('#list .weapon svg[role="img"]'));
  assert.equal(w.weaponVisual({path:'/Game/DI2/Weapons/Melee/DA_MeleeWeaponArchetype_Unknown.Unknown',name:'Unknown'}).icon,'unknown');
  assert.equal(w.eval('Object.keys(changes).length'),0);
  const full=w.eval('data.destinations.find(d=>d.name==="Shared storage locker — New Game Plus")');
  const weapon=w.eval('data.weapons.find(w=>w.group==="Shared storage locker — New Game Plus"&&w.editable)');
  w.select(weapon.key);assert.equal(d.querySelector('#deleteweapon').textContent,'Delete Weapon');
  // Descriptions are readable inline and associated with each checkbox.
  assert(w.eval('data.catalog.every(p=>p.description && p.description_basis)'));
  assert(d.querySelector('#perks .perk-description').textContent.length>10);
  assert(d.querySelector('#perks .perk').title.includes(d.querySelector('#perks .perk-description').textContent));
  assert(d.getElementById(d.querySelector('#perks input').getAttribute('aria-describedby')));
  const original=w.eval('currentPerks.slice()');
  await w.refreshPresets();assert.equal(w.eval('perkPresets.length'),0);
  w.openPresetName(false);d.querySelector('#preset-name').value='Favourite build';await w.savePreset();
  assert.equal(w.eval('perkPresets.length'),1);const presetId=w.eval('perkPresets[0].id');
  w.eval('currentPerks=[]');w.stage();w.renderPerks();d.querySelector('#preset').value=presetId;w.applyPreset(false);
  assert.deepEqual(w.eval('currentPerks'),original);assert(!d.querySelector('#preset-apply').disabled);
  const another=w.eval('data.weapons.find(w=>w.editable&&w.key!==selected)');w.select(another.key);
  d.querySelector('#preset').value=presetId;w.applyPreset(false);assert.deepEqual(w.eval('currentPerks'),original);w.resetWeapon();w.select(weapon.key);
  const presetReload=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{url:base,runScripts:'dangerously',beforeParse(x){x.HTMLDialogElement.prototype.showModal=function(){this.open=true};x.fetch=(url,o={})=>fetch(base+url,o)}});
  await presetReload.window.legalBoot;await presetReload.window.refreshPresets();assert.equal(presetReload.window.document.querySelector('#preset option[value="'+presetId+'"]').textContent,'Favourite build ('+original.length+')');presetReload.window.close();
  assert([...d.querySelectorAll('header button')].every(b=>b.title&& !b.textContent.includes('…')));

  d.querySelector('#perksearch').value='Acid Rain';w.renderPerks();
  assert(d.querySelectorAll('#perks input').length<w.eval('data.catalog.length'));
  d.querySelector('#allperks').click();
  assert.equal(w.eval('currentPerks.length'),w.eval('data.catalog.length'));
  assert(d.querySelector('#allperks').checked);assert(!d.querySelector('#allperks').indeterminate);
  d.querySelector('#perks input').click();assert(d.querySelector('#allperks').indeterminate);
  assert.equal(w.eval('currentPerks.length'),w.eval('data.catalog.length-1'));
  d.querySelector('#perksearch').value='';w.resetWeapon();assert.deepEqual(w.eval('currentPerks.slice()'),original);

  w.toggleDelete();assert.equal(d.querySelector('#deleteweapon').textContent,'Undo Delete');assert.equal(w.eval('deletions.length'),1);
  d.querySelector('#group').value=full.name;w.openCreate();assert.equal(Number(d.querySelector('#newdest').value),full.key);assert.equal(w.creationFree(),1);
  const previousChanges=w.eval('JSON.stringify(changes)');
  d.querySelector('#newpreset').value=presetId;w.applyPreset(true);assert.deepEqual(w.eval('newPerks'),original);
  d.querySelector('#newtype').value=raven.path;d.querySelector('#newtype').onchange();
  assert(d.querySelector('#newweaponpreview').textContent.includes('Sporting rifle'));
  assert(d.querySelector('#newweaponpreview svg').getAttribute('aria-label').includes('representative silhouette'));
  assert.equal(w.eval('JSON.stringify(changes)'),previousChanges);
  d.querySelector('#newsearch').value='sporting rifle';w.renderWeaponChoices();
  assert([...d.querySelector('#newtype').options].some(x=>x.value===raven.path));
  assert([...d.querySelector('#newtype').options].every(x=>x.textContent.includes('Sporting rifle')));
  assert(d.querySelector('#newperks .perk-description').textContent.length>10);
  d.querySelector('#newperksearch').value='Acid Rain';w.renderNewPerks();
  d.querySelector('#allnewperks').click();assert.equal(w.eval('newPerks.length'),w.eval('data.catalog.length'));
  d.querySelector('#newperks input').click();assert(d.querySelector('#allnewperks').indeterminate);
  d.querySelector('#allnewperks').click();assert(d.querySelector('#allnewperks').checked);
  d.querySelector('#allnewperks').click();assert.equal(w.eval('newPerks.length'),0);assert(!d.querySelector('#allnewperks').indeterminate);
  d.querySelector('#newperksearch').value='';w.renderNewPerks();
  d.querySelector('#newsearch').value='katana';w.renderWeaponChoices();assert(d.querySelector('#newtype').options.length>0);w.queueWeapon();assert.equal(w.eval('additions.length'),1);assert.equal(w.creationFree(),0);
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('DELETE:'));assert(d.querySelector('#reviewitems').textContent.includes('NEW:'));
  await w.exportSave();assert(w.exported);assert(d.querySelector('#status').textContent.includes('Validating'));
  let out=await fetch(base+'export');assert(out.ok);let bytes=await out.arrayBuffer();assert(bytes.byteLength>0);assert(fs.readdirSync(backup.folder).filter(n=>n.includes('_exported_')).some(n=>fs.readFileSync(path.join(backup.folder,n)).equals(Buffer.from(bytes))));
  // Undo deletion and queued creation, then replace a weapon in a full slot.
  w.toggleDelete();w.eval('additions=[]');w.openReplace();assert.equal(d.querySelector('#queueweapon').textContent,'Done');assert(d.querySelector('#newdestlabel').hidden);assert.equal(w.creationFree(),1);
  d.querySelector('#newsearch').value='Peggy';w.renderWeaponChoices();assert(d.querySelector('#newtype').options.length);w.queueWeapon();assert.equal(w.eval('Object.keys(changes).length'),1);assert(d.querySelector('#name').textContent.includes('PEGGY'));assert(d.querySelector('#weaponpreview').textContent.includes('Hunting rifle'));
  w.review();await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);
  // Clone the complete staged weapon into another container, then batch-edit by family.
  w.eval('changes={};additions=[];deletions=[];ammoChanges={}');
  const melee=w.eval('data.weapons.find(w=>w.editable&&w.path.includes("MeleeWeaponArchetype")&&w.durability!==null)');
  const locker=w.eval('data.destinations.find(d=>d.name==="Shared storage locker — Regular")');
  const beforeLocker=locker.count;w.select(melee.key);d.querySelector('#durability').value=9999;w.stage();
  w.openDuplicate();assert.equal(d.querySelector('#newtitle').textContent,'Duplicate Weapon');assert(d.querySelector('#newtype').disabled);
  d.querySelector('#newdest').value=locker.key;w.updateCreateSpace();w.queueWeapon();
  assert.equal(w.eval('additions[0].clone_source'),melee.key);assert.equal(w.eval('additions[0].durability'),9999);
  assert.deepEqual(w.eval('additions[0].perks'),w.eval('currentPerks'));
  d.querySelector('#group').value=locker.name;w.renderList();assert(d.querySelector('#slots').textContent.includes((beforeLocker+1)+' / 64 slots used'));
  const acid=w.eval('data.catalog.find(p=>p.name.toLowerCase()==="acid rain").path');
  w.openBulkPerk(acid);d.querySelector('#bulkscope').value='firearms';w.previewBulk();
  const unchangedMelee=w.eval('JSON.stringify(state(data.weapons.find(w=>w.key==='+melee.key+')))');
  w.applyBulkPerk(false);w.openBulkPerk(acid);d.querySelector('#bulkscope').value='firearms';w.previewBulk();w.applyBulkPerk(true);
  assert(w.eval('data.weapons.filter(w=>w.editable&&weaponFamily(w)==="firearms").every(w=>state(w).perks.includes(bulkPerk))'));
  assert.equal(w.eval('JSON.stringify(state(data.weapons.find(w=>w.key==='+melee.key+')))'),unchangedMelee);
  assert(w.eval('data.weapons.filter(w=>!w.editable).every(w=>!changes[w.key])'));
  w.openBulkPerk(acid);d.querySelector('#bulkscope').value='melee';w.previewBulk();w.applyBulkPerk(false);
  assert(!w.eval('additions[0].perks.includes(bulkPerk)'));
  // Current-location scoping, deletion exclusion, and no duplicate upgrade entries.
  const gun=w.eval('data.weapons.find(w=>w.editable&&weaponFamily(w)==="firearms")');
  w.select(gun.key);w.toggleDelete();w.openBulkPerk(acid);d.querySelector('#bulkwhere').value='current';w.previewBulk();
  assert(w.bulkTargets().existing.every(x=>x.group===locker.name&&x.key!==gun.key));
  w.applyBulkPerk(true);assert(w.eval('Object.values(changes).every(c=>new Set(c.perks).size===c.perks.length)'));
  w.openAmmo();const input=d.querySelector('#ammolist input');assert(input);input.value=9999;input.onchange();assert.equal(w.ammoDirty(),1);
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('DUPLICATE:'));assert(d.querySelector('#reviewitems').textContent.includes('RESERVE AMMO:'));
  await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);
  // The USB list locates exports and encrypted pairs, and names survive rescans.
  await w.refreshUSB(true);assert.equal(w.eval('usbState.entries.length'),2);
  w.openUSB();w.editProfileName(account);d.querySelector('#profile-name').value='Example_Player';await w.saveProfileName();
  assert([...d.querySelectorAll('#usb-list strong')].every(x=>x.textContent==='Example_Player'));
  const encrypted=w.eval('usbState.entries.find(e=>e.kind==="encrypted")');w.eval('selectedUSB='+JSON.stringify(encrypted.key));w.renderUSB();
  await w.openSelectedUSB();assert(w.eval('selectedEncrypted.account_id')===account);assert(d.querySelector('#status').textContent.includes('for GarlicSaves decryption'));
  // It is deliberately impossible to open an encrypted container as a decrypted export.
  const refused=await fetch(base+'open-found',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:encrypted.key})});assert.equal(refused.status,400);
  const plain=w.eval('usbState.entries.find(e=>e.kind==="decrypted")');w.eval('selectedUSB='+JSON.stringify(plain.key));await w.openSelectedUSB();
  assert.equal(w.eval('fileName'),'export.sav');assert.equal(w.eval('data.source_path'),plain.path);assert(fs.readFileSync(w.eval('data.backup.path')).equals(source));
  // Named backups round-trip through the real backend with destination protection.
  assert([...d.querySelectorAll('#usb-list button')].some(b=>b.textContent==='Back Up This Save'));
  w.nameBackup(encrypted.key);d.querySelector('#backup-name').value='Before cheats 2 Nov';await w.saveNamedBackup();
  await w.openNamedBackups();assert(d.querySelector('#named-backups-list').textContent.includes('Before cheats 2 Nov'));
  let saved=await (await fetch(base+'named-backups')).json();const named=saved.backups.find(b=>b.name==='Before cheats 2 Nov');assert(named);
  fs.writeFileSync(path.join(game,'DeadIsland2SaveGame'),'changed-after-backup');await w.restoreNamedBackup(named);assert.equal(fs.readFileSync(path.join(game,'DeadIsland2SaveGame'),'utf8'),'encrypted example');
  saved=await (await fetch(base+'named-backups')).json();assert(saved.backups.length>=2);d.querySelector('#named-backups-dialog').close();
  // Character level, capped cash and full resource stacks use the real save parser.
  w.openCharacter();assert(d.querySelector('#character-items input'));d.querySelector('#character-level').value=20;w.stageCharacterLevel();w.stageMoney(2000000);w.fillResources(false);assert(w.extraDirty()>2);
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('level 40 → 20'));assert(d.querySelector('#reviewitems').textContent.includes('Cash'));
  await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);d.querySelector('#character-dialog').close();
  fs.unlinkSync(path.join(game,'DeadIsland2SaveGame'));fs.unlinkSync(path.join(game,'DeadIsland2SaveGame.bin'));fs.unlinkSync(path.join(game,'export.sav'));await w.refreshUSB(true);assert.equal(w.eval('usbState.entries.length'),0);
  // Exercise the Windows bridge through the same shared page.
  let winName=null;const originalData=w.eval('data');w.pywebview={api:{open_save:async()=>({name:'windows.sav',data:originalData}),export_save:async name=>{winName=name;return {message:'Windows native export completed.'}}}};
  // Consent and session binding are enforced on the backend, before submission.
  const denied=await fetch(base+'service-decrypt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:encrypted.key})});assert.equal(denied.status,400);
  const unbound=await fetch(base+'service-encrypt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consent:true})});assert.equal(unbound.status,400);
  // Exercise the visible connection dialog without contacting the real service.
  const oldFetch=w.fetch;const secret='test_worker_key_00000000000000000000';let serviceCalls=[];
  w.fetch=async (url,o={})=>{if(!url.startsWith('service-'))return oldFetch(url,o);serviceCalls.push({url,body:o.body});const v=url==='service-test'?{status:'working',has_key:true,message:'Checking…'}:{status:'done',has_key:true,has_session:false,has_folder:false,message:'Connected. No save files were sent.'};return {ok:true,json:async()=>v}};
  await w.openService();assert(d.querySelector('#service-dialog').open);assert.equal(d.querySelector('#service-key').type,'password');d.querySelector('#service-key').value=secret;await w.serviceConnect();assert.equal(d.querySelector('#service-key').value,'');assert(!d.querySelector('#service-status').textContent.includes(secret));assert(serviceCalls.some(c=>c.url==='service-test'));assert(!w.eval('busy'));assert(d.querySelector('#service-encrypt').disabled);w.fetch=oldFetch;d.querySelector('#service-dialog').close();
  w.dispatchEvent(new w.Event('pywebviewready'));assert(d.querySelector('#platformbadge').textContent.includes('Windows'));
  await w.openSave();assert.equal(w.eval('fileName'),'windows.sav');assert.equal(w.ammoDirty(),0);
  w.review();await w.exportSave();assert.equal(winName,'windows_Edited.sav');assert.equal(d.querySelector('#status').textContent,'Windows native export completed.');
  // Reopen a local decryption without a new upload, then enter the editor automatically.
  const resumeFetch=w.fetch;
  w.fetch=async (url,o={})=>{
   if(url==='service-status'||url==='service-resume')return {ok:true,json:async()=>({operation:'decrypt',status:'done',editable:true,has_session:true,has_key:true,message:'Previous decryption reopened. No upload.'})};
   if(url==='service-open')return {ok:true,json:async()=>({name:'downloaded.sav',data:originalData})};
   return resumeFetch(url,o);
  };
  assert.equal(d.querySelector('#service-decrypt').textContent,'Decrypt Selected Save…');
  await w.openService();await w.serviceResume();assert(!d.querySelector('#service-dialog').open);
  assert(w.eval('serviceOpened'));assert.equal(w.eval('fileName'),'downloaded.sav');assert(!d.querySelector('#service-encrypt').disabled);w.fetch=resumeFetch;
  await w.refreshPresets();d.querySelector('#preset').value=presetId;const beforePresetDelete=w.eval('JSON.stringify(currentPerks)');await w.deletePreset(false);assert.equal(w.eval('perkPresets.length'),0);assert.equal(w.eval('JSON.stringify(currentPerks)'),beforePresetDelete);
  console.log('PASS: named presets save/reload/apply to another weapon/create/delete; Done replacement label and header tooltips; USB discovery, profile rename, encrypted-pair selection, direct decrypted open and drive removal; automatic open/export backups; Windows open/export bridge; complete duplication; slot counters; batch family/location/deletion scopes; durability and reserve ammo; weapon silhouettes; Raven type and searchable labels; live creation/replacement previews; unverified fallback; inline and hover descriptions; accessible help; filtered Select All; individual deselection; partial state; clear all; import; named profiles; staged deletion/undo; freed-slot creation; review; validated export; in-place replacement');
  dom.window.close();
 }finally{proc.kill()}
})().catch(e=>{console.error(e);process.exit(1)});
