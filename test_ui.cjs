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
  w.eval('changes={};additions=[];deletions=[];ammoChanges={};ammoRefills={};ammoTargets={}');
  const melee=w.eval('data.weapons.find(w=>w.editable&&w.path.includes("MeleeWeaponArchetype")&&w.durability!==null)');
  const locker=w.eval('data.destinations.find(d=>d.name==="Shared storage locker — Regular")');
  const beforeLocker=locker.count;w.select(melee.key);assert.equal(d.querySelector('#durability'),null);assert.equal(d.querySelector('#newdurability'),null);w.stage();
  w.openDuplicate();assert.equal(d.querySelector('#newtitle').textContent,'Duplicate Weapon');assert(d.querySelector('#newtype').disabled);
  d.querySelector('#newdest').value=locker.key;w.updateCreateSpace();w.queueWeapon();
  assert.equal(w.eval('additions[0].clone_source'),melee.key);assert.equal(w.eval('additions[0].durability'),undefined);
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

  // Half-fill preserves pickup space and cash; character levels identify inventory groups.
  w.openCharacter();const halfGroup=w.chosenCharacter().group,halfProfile=w.chosenCharacter().profile;
  w.stageMoney(123456);d.querySelector('#fill-half').click();
  for(const item of halfGroup.items){const changed=w.eval('resourceChanges['+JSON.stringify(halfGroup.key+'|'+item.path)+']');const count=changed?.count??item.count;assert.equal(count,item.category==='Money'?123456:item.category==='Consumables'?item.maximum:50)}
  assert(w.eval('Object.values(resourceChanges)').every(x=>x.group===halfGroup.key));
  const levelGroup=w.eval('data.containers.find(c=>c.profile_id==='+JSON.stringify(halfProfile.id)+').name');d.querySelector('#group').value=levelGroup;w.renderList();assert(d.querySelector('#group-level').textContent.includes('Character level '+halfProfile.level));
  d.querySelector('#character-level').value=18;w.stageCharacterLevel();assert(d.querySelector('#group-level').textContent.includes('Character level 18'));assert([...d.querySelector('#group').options].some(o=>o.value===levelGroup&&o.textContent.includes('Character level 18')));d.querySelector('#character-dialog').close();
  // Reserve-ammo fill/reset is scoped to the dropdown; the global reset is separate.
  w.openAmmo();const ammoGroups=w.eval('data.ammo_groups.map(g=>g.name)');assert(ammoGroups.length>1);
  d.querySelector('#ammogroup').value=ammoGroups[0];w.revertCharacterAmmo();const groupA=w.eval('data.ammo_groups[0].key');assert(w.eval('ammoRefills['+groupA+']'));assert.equal(d.querySelectorAll('#ammolist input').length,7);assert([...d.querySelectorAll('#ammolist input')].every(i=>!i.disabled));
  d.querySelector('#ammogroup').value=ammoGroups[1];w.revertCharacterAmmo();const groupB=w.eval('data.ammo_groups[1].key');assert(w.eval('ammoRefills['+groupB+']'));
  d.querySelector('#ammogroup').value=ammoGroups[0];w.undoCharacterAmmo();assert(!w.eval('ammoRefills['+groupA+']'));assert(w.eval('ammoRefills['+groupB+']'));
  w.revertEveryAmmoEdit();assert.equal(w.eval('Object.keys(ammoRefills).length'),ammoGroups.length);assert.equal(d.querySelector('#ammo-fill-all'),null);const experimental=d.querySelector('[aria-label="Shotgun shells reserve count"]');experimental.value=211;experimental.onchange();assert.equal(w.eval('Object.values(ammoTargets)[0].count'),211);assert(w.eval('ammoRefills['+groupA+']'));
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('CUSTOM RESERVE AMMO: Shotgun shells → 211'));assert(d.querySelector('#reviewitems').textContent.includes('RESTORE NORMAL AMMO'));await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);
  // Durability custom values are scoped; normal maximums require explicit repaired references.
  w.eval('changes={};ammoChanges={};ammoRefills={};ammoTargets={};resourceChanges={};characterLevels={};additions=[];deletions=[]');
  await w.openDurability();assert.equal(d.querySelector('#durability-restore-group').disabled,true);
  const durabilityGroup=d.querySelector('#durability-group').value,meleeTargets=w.durabilityTargets(),originalOther=w.eval('JSON.stringify(data.weapons.filter(w=>w.group!=='+JSON.stringify(durabilityGroup)+').map(w=>[w.key,state(w).durability]))');
  assert(meleeTargets.length);await w.recordFullDurability(false);assert(!d.querySelector('#durability-restore-group').disabled);const referenceWeapon=meleeTargets[0];w.eval('changes['+referenceWeapon.key+']={level:'+((referenceWeapon.level||1)+1)+'}');assert.equal(w.fullDurability(referenceWeapon),null);w.eval('delete changes['+referenceWeapon.key+']');
  d.querySelector('#durability-value').value=9999;w.setBulkDurability(false);assert(meleeTargets.every(x=>w.eval('changes['+x.key+'].durability')===9999||x.durability===9999));
  assert.equal(w.eval('JSON.stringify(data.weapons.filter(w=>w.group!=='+JSON.stringify(durabilityGroup)+').map(w=>[w.key,state(w).durability]))'),originalOther);
  w.restoreDurability(false);assert(meleeTargets.every(x=>w.eval('state(data.weapons.find(w=>w.key==='+x.key+')).durability')===x.durability));
  d.querySelector('#durability-value').value=500;w.setBulkDurability(true);assert(w.durabilityTargets(true).every(x=>w.eval('state(data.weapons.find(w=>w.key==='+x.key+')).durability')===500));
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('Durability'));await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);d.querySelector('#durability-dialog').close();
  w.eval('changes={};ammoChanges={};ammoRefills={};ammoTargets={};resourceChanges={};characterLevels={};additions=[];deletions=[]');
  // Clipboard snapshots do not follow later source edits and replace without consuming a slot.
  const copySource=w.eval('data.weapons.find(w=>w.editable&&w.path.includes("MeleeWeaponArchetype"))'),pasteTarget=w.eval('data.weapons.find(w=>w.editable&&w.path.includes("RangedWeaponArchetype"))');
  w.select(copySource.key);d.querySelector('#level').value=14;w.stage();w.showWeaponMenu(new w.MouseEvent('contextmenu',{clientX:60,clientY:80}),copySource.key);assert(!d.querySelector('#weapon-context').hidden);d.querySelector('#weapon-copy').click();assert(d.querySelector('#weapon-context').hidden);
  d.querySelector('#level').value=16;w.stage();const pendingAdditions=w.eval('additions.length');w.showWeaponMenu(new w.MouseEvent('contextmenu'),pasteTarget.key);assert(!d.querySelector('#weapon-paste').disabled);d.querySelector('#weapon-paste').click();assert.equal(w.eval('state(data.weapons.find(w=>w.key==='+pasteTarget.key+')).level'),14);assert.equal(w.eval('additions.length'),pendingAdditions);
  w.review();await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);
  // Explicit preset association follows each weapon; untouched weapons show Choose a preset.
  d.querySelector('#preset').value=presetId;w.applyPreset(false);await w.rememberPresetBinding(pasteTarget.key,presetId,w.eval('currentPerks'));
  w.select(copySource.key);w.select(pasteTarget.key);assert.equal(d.querySelector('#preset').value,presetId);
  const noPreset=w.eval('data.weapons.find(w=>w.editable&&!presetBindings[w.id]&&w.key!==selected)');w.select(noPreset.key);assert.equal(d.querySelector('#preset').value,'');
  w.select(pasteTarget.key);w.openPresetName(false);d.querySelector('#preset-save-mode').value='update';w.presetSaveMode();assert.equal(d.querySelector('#preset-existing').value,presetId);assert(d.querySelector('#preset-name').readOnly);const originalPresetName=w.eval('perkPresets.find(p=>p.id==='+JSON.stringify(presetId)+').name');
  w.eval('currentPerks=currentPerks.slice(0,1)');await w.savePreset();assert.equal(w.eval('perkPresets[0].id'),presetId);assert.equal(w.eval('perkPresets[0].name'),originalPresetName);assert.equal(w.eval('perkPresets[0].perks.length'),1);
  await w.refreshPresets();d.querySelector('#preset').value=presetId;const beforePresetDelete=w.eval('JSON.stringify(currentPerks)');await w.deletePreset(false);assert.equal(w.eval('perkPresets.length'),0);assert.equal(w.eval('JSON.stringify(currentPerks)'),beforePresetDelete);
  // The last highlighted action prepares, encrypts and installs; export remains secondary.
  assert(!d.querySelector('#export').classList.contains('primary'));assert.equal(d.querySelector('header .primary').id,'finalize');assert.equal([...d.querySelectorAll('header button')].at(-1).id,'finalize');
  const finalizeFetch=w.fetch,finalizeCalls=[];let finalizeInstalled=false;
  w.fetch=async (url,o={})=>{
   if(url==='finalize-info')return {ok:true,json:async()=>({account_id:account,profile_name:'Example_Player',title_id:'CUSA01014',filename:'DeadIsland2SaveGame',drives:[{key:'example-drive',name:'Test USB',root:'/USB'}],preferred_drive:'example-drive',relative_path:'PS4/SAVEDATA/'+account+'/CUSA01014/DeadIsland2SaveGame'})};
   if(url==='service-finalize'){finalizeCalls.push(JSON.parse(o.body));return {ok:true,json:async()=>({status:'done',operation:'finalize',installed:finalizeInstalled,message:finalizeInstalled?'Saved to USB and verified.':'USB write failed; result retained.',destination:'/USB/PS4/SAVEDATA/example',has_folder:true,has_key:true,editable:true})}}
   if(url==='service-open')return {ok:true,json:async()=>({name:'finalized.sav',data:originalData})};
   return finalizeFetch(url,o);
  };
  await w.openFinalize();assert(d.querySelector('#finalize-dialog').open);assert.equal(d.querySelector('#finalize-drive').value,'example-drive');assert(d.querySelector('#finalize-target').textContent.startsWith('/USB/PS4/SAVEDATA/'));
  w.eval('guideRoute="garlic";guideStep="finish";guideFinalized=false');
  const beforeFailedFinalize=w.eval('JSON.stringify(changes)');await w.finalizeSave();assert(d.querySelector('#finalize-status').textContent.includes('failed'));assert.equal(w.eval('JSON.stringify(changes)'),beforeFailedFinalize);assert(!d.querySelector('#finalize-confirm').hidden);
  assert.equal(w.eval('guideStep'),'finish');assert(!w.eval('guideFinalized'));finalizeInstalled=true;await w.finalizeSave();assert.equal(w.eval('guideStep'),'complete');assert(w.eval('guideFinalized'));w.endGuide();assert(d.querySelector('#finalize-status').textContent.includes('Saved to USB and verified'));assert.equal(w.eval('Object.keys(changes).length+ammoDirty()+extraDirty()+additions.length+deletions.length'),0);assert.equal(d.querySelector('#finalize-close').textContent,'Done');assert(d.querySelector('#finalize-confirm').hidden);assert(finalizeCalls.every(c=>c.drive_key==='example-drive'&&c.consent===true));w.fetch=finalizeFetch;d.querySelector('#finalize-dialog').close();

  // Counts are scoped to the inventory, independent of search, and track staged copies/deletions.
  const backpack=w.eval('data.containers.find(c=>c.profile_id&&data.weapons.some(w=>w.group===c.name&&w.editable))');
  d.querySelector('#group').value=backpack.name;w.changeWeaponGroup();
  const target=w.eval('data.weapons.find(w=>w.group==='+JSON.stringify(backpack.name)+'&&w.editable)');
  const countBefore=w.weaponModelCounts(backpack.name).get(target.path);
  w.eval('additions.push({path:'+JSON.stringify(target.path)+',destination:'+backpack.key+',level:30,rarity:"Legendary",perks:[]})');
  assert.equal(w.weaponModelCounts(backpack.name).get(target.path),countBefore+1);
  w.eval('deletions.push('+target.key+')');assert.equal(w.weaponModelCounts(backpack.name).get(target.path),countBefore);
  w.eval('deletions=[];additions=[]');d.querySelector('#search').value='no matching weapon';w.renderList();w.selectAllWeapons();
  const checked=w.selectionTargets();assert(checked.length>0);assert(checked.every(x=>x.group===backpack.name&&x.editable));
  assert.equal(checked.length,w.eval('data.weapons.filter(w=>w.group==='+JSON.stringify(backpack.name)+'&&w.editable).length'));
  const othersBefore=w.eval('JSON.stringify(data.weapons.filter(w=>w.group!=='+JSON.stringify(backpack.name)+').map(w=>state(w)))');
  await w.openSelectionEdit();d.querySelector('#selection-action').value='level';w.selectionEditControls();d.querySelector('#selection-level').value=22;w.applySelectionEdit();
  assert(checked.every(x=>w.eval('state(data.weapons.find(w=>w.key==='+x.key+')).level')===22));
  d.querySelector('#selection-action').value='add';w.selectionEditControls();const batchPerk=d.querySelector('#selection-value').value;w.applySelectionEdit();
  assert(checked.every(x=>w.eval('state(data.weapons.find(w=>w.key==='+x.key+')).perks').includes(batchPerk)));
  assert.equal(w.eval('JSON.stringify(data.weapons.filter(w=>w.group!=='+JSON.stringify(backpack.name)+').map(w=>state(w)))'),othersBefore);
  d.querySelector('#search').value='';w.renderList();assert(d.querySelector('.weapon-count').textContent.match(/^\(\d+\)$/));
  d.querySelector('#group').value=full.name;w.changeWeaponGroup();assert.equal(w.selectionTargets().length,0);
  w.editorTab('settings');assert.equal(d.querySelector('#detail').dataset.tab,'settings');w.editorTab('perks');
  w.createTab('perks');assert(d.querySelector('#new-weapon-pane').hidden);assert(!d.querySelector('#new-perks-pane').hidden);w.createTab('weapon');
  w.select(target.key);assert(d.querySelectorAll('#perks .perk').length<=6);const firstPerk=d.querySelector('#perks .perk-name').textContent;w.changePerkPage(1);assert.notEqual(d.querySelector('#perks .perk-name').textContent,firstPerk);
  // Guidance follows real opening/finalization state and does not perform uploads or writes itself.
  w.endGuide();w.openGuide();assert(d.querySelector('#guide-choices').textContent.includes('Save Wizard'));
  w.chooseGuideRoute('wizard');assert(!d.querySelector('#guidebar').hidden);w.acceptSave(originalData,'guide.sav');
  assert.equal(w.eval('guideStep'),'edit');w.openGuide();const finishGuide=[...d.querySelectorAll('#guide-choices button')].find(b=>b.textContent.includes('My edits are ready'));finishGuide.click();
  assert.equal(w.eval('guideStep'),'finish');assert(d.querySelector('#guide-text').textContent.includes('cannot verify'));
  w.endGuide();w.chooseGuideRoute('garlic');assert.equal(w.eval('guideStep'),'source');assert(!d.querySelector('#guide-text').textContent.includes('verified'));
  w.eval('guideStep="finish"');w.openGuide();assert(d.querySelector('#guide-choices').textContent.includes('Finalize and Re-encrypt'));w.endGuide();
  w.eval('serviceActive=true');w.serviceRender({has_key:true,message:'Waiting in GarlicSaves queue'});assert(d.querySelector('#service-status').classList.contains('processing'));assert(d.querySelector('#status').classList.contains('processing'));
  w.eval('serviceActive=false');w.serviceRender();w.status('Ready');assert(!d.querySelector('#service-status').classList.contains('processing'));assert(!d.querySelector('#status').classList.contains('processing'));
  // No checkpoint means no write; saved points require only a target, never a donor picker.
  w.acceptSave(originalData,'story.sav');w.eval('data.story={available:false,checkpoints:[],reason:"Open checkpoint save once"}');w.openStoryReset();assert(d.querySelector('#story-stage').disabled);
  w.stageStoryReset();assert.equal(w.editPayload().story_resets.length,0);assert(d.querySelector('#story-description').textContent.includes('once'));
  w.eval('data.story={available:true,checkpoints:[{ng:false,available:true},{ng:true,available:true}]}');w.renderStoryReset();assert(!d.querySelector('#story-stage').disabled);assert(!d.querySelector('#story-reference'));
  const storyTarget=d.querySelector('#story-target').value;w.stageStoryReset();assert.equal(w.editPayload().story_resets[0].target,storyTarget);assert.equal(Object.keys(w.editPayload().story_resets[0]).length,1);assert.equal(w.extraDirty(),1);
  w.review();assert(d.querySelector('#reviewitems').textContent.includes('dumpster after prologue'));d.querySelector('#review').close();w.undoStoryReset();assert.equal(w.editPayload().story_resets.length,0);
  w.eval('data.story.checkpoints=[{ng:false,available:false,reason:"Regular missing"},{ng:true,available:true}]');d.querySelector('#story-target').value=w.eval('data.profiles.find(p=>!p.ng).id');w.renderStoryReset();assert(d.querySelector('#story-stage').disabled);assert(d.querySelector('#story-description').textContent.includes('Regular missing'));
  w.acceptSave(originalData,'next.sav');assert.equal(w.editPayload().story_resets.length,0);
  console.log('PASS: post-prologue reset mode-specific availability, no donor picker, level independence, review/payload and undo');
  console.log('PASS: scoped exact-model counts; search-independent backpack selection; bulk levels/perks preserve other characters; selection resets across locations; compact tabs and perk paging; separate GarlicSaves/Save Wizard guide paths; active processing emphasis');
  console.log('PASS: highlighted last-step finalize flow, failed-write handling and refreshed baseline; half resource fill and character levels; scoped/global ammo actions; clipboard snapshot paste; per-weapon preset labels and update-existing mode; named presets save/reload/apply to another weapon/create/delete; Done replacement label and header tooltips; USB discovery, profile rename, encrypted-pair selection, direct decrypted open and drive removal; automatic open/export backups; Windows open/export bridge; complete duplication; slot counters; batch family/location/deletion scopes; custom/scoped durability and recorded normal references; editable ammo overrides and normal refills; weapon silhouettes; Raven type and searchable labels; live creation/replacement previews; unverified fallback; inline and hover descriptions; accessible help; filtered Select All; individual deselection; partial state; clear all; import; named profiles; staged deletion/undo; freed-slot creation; review; validated export; in-place replacement');
  dom.window.close();
 }finally{proc.kill()}
})().catch(e=>{console.error(e);process.exit(1)});
