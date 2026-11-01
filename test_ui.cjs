const {JSDOM}=require('jsdom');
const fs=require('fs'), cp=require('child_process'),os=require('os'),path=require('path');
const assert=require('assert');
(async()=>{
 const ready=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'di2-ui-')),'ready');
 const proc=cp.spawn('python',[path.join(__dirname,'server.py'),'--ready',ready]);
 try{
  for(let i=0;i<100&&!fs.existsSync(ready);i++)await new Promise(r=>setTimeout(r,40));
  const base=fs.readFileSync(ready,'utf8');const source=fs.readFileSync(process.env.DI2_TEST_SAVE||'../upload/ue4savegame.ps4.sav');
  const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'),{url:base,runScripts:'dangerously',beforeParse(w){w.confirm=()=>true;w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};w.fetch=(url,o={})=>fetch(base+url,{...o,body:url==='open'?source:o.body});w.webkit={messageHandlers:{workshop:{postMessage(x){w.exported=x}}}}}});
  const w=dom.window,d=w.document;
  Object.defineProperty(d.querySelector('#file'),'files',{value:[{name:'test.sav'}]});await d.querySelector('#file').onchange({target:d.querySelector('#file')});
  assert.equal(w.eval('data.profiles.length'),10);assert([...d.querySelectorAll('#group option')].some(x=>x.textContent.includes('Ryan — New Game Plus (active)')));
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
  let out=await fetch(base+'export');assert(out.ok);let bytes=await out.arrayBuffer();assert(bytes.byteLength>0);
  // Undo deletion and queued creation, then replace a weapon in a full slot.
  w.toggleDelete();w.eval('additions=[]');w.openReplace();assert(d.querySelector('#newdestlabel').hidden);assert.equal(w.creationFree(),1);
  d.querySelector('#newsearch').value='Peggy';w.renderWeaponChoices();assert(d.querySelector('#newtype').options.length);w.queueWeapon();assert.equal(w.eval('Object.keys(changes).length'),1);assert(d.querySelector('#name').textContent.includes('PEGGY'));
  w.review();await w.exportSave();assert(!d.querySelector('#status').classList.contains('error'),d.querySelector('#status').textContent);
  console.log('PASS: inline and hover descriptions; accessible help; filtered Select All; individual deselection; partial state; clear all; import; named profiles; staged deletion/undo; freed-slot creation; review; validated export; in-place replacement');
  dom.window.close();
 }finally{proc.kill()}
})().catch(e=>{console.error(e);process.exit(1)});
