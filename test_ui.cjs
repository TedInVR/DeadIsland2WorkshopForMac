const {JSDOM}=require('jsdom');
const fs=require('fs'), cp=require('child_process'),os=require('os'),path=require('path');
const assert=require('assert');
(async()=>{
 const ready=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'di2-ui-')),'ready');
 const usbRoot=path.join(path.dirname(ready),'USB'),account='0000000000000001',game=path.join(usbRoot,'PS4','SAVEDATA',account,'CUSA01014');fs.mkdirSync(game,{recursive:true});
 fs.writeFileSync(path.join(game,'DeadIsland2SaveGame'),'encrypted example');fs.writeFileSync(path.join(game,'DeadIsland2SaveGame.bin'),'bin example');
 fs.copyFileSync(process.env.DI2_TEST_SAVE||'../upload/ue4savegame.ps4.sav',path.join(game,'export.sav'));
 const proc=cp.spawn('python',[path.join(__dirname,'server.py'),'--ready',ready],{env:{...process.env,DI2_WORKSHOP_BACKUP_DIR:path.join(path.dirname(ready),'backups'),DI2_WORKSHOP_SCAN_ROOTS:JSON.stringify([usbRoot])}});

 try{
  for(let i=0;i<100&&!fs.existsSync(ready);i++)await new Promise(r=>setTimeout(r,40));
  const base=fs.readFileSync(ready,'utf8');const source=fs.readFileSync(process.env.DI2_TEST_SAVE||'../upload/ue4savegame.ps4.sav');
  const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{url:base,runScripts:'dangerously',beforeParse(w){w.confirm=()=>true;w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};w.fetch=(url,o={})=>fetch(base+url,{...o,body:url==='open'?source:o.body});w.webkit={messageHandlers:{workshop:{postMessage(x){w.exported=x}}}}}});
  const w=dom.window,d=w.document;
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
  w.toggleDelete();w.eval('additions=[]');w.openReplace();assert(d.querySelector('#newdestlabel').hidden);assert.equal(w.creationFree(),1);
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
  console.log('PASS: USB discovery, profile rename, encrypted-pair selection, direct decrypted open and drive removal; automatic open/export backups; Windows open/export bridge; complete duplication; slot counters; batch family/location/deletion scopes; durability and reserve ammo; weapon silhouettes; Raven type and searchable labels; live creation/replacement previews; unverified fallback; inline and hover descriptions; accessible help; filtered Select All; individual deselection; partial state; clear all; import; named profiles; staged deletion/undo; freed-slot creation; review; validated export; in-place replacement');
  dom.window.close();
 }finally{proc.kill()}
})().catch(e=>{console.error(e);process.exit(1)});
