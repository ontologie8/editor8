// SPDX-License-Identifier: AGPL-3.0-or-later
import {test, expect} from '@playwright/test';
import fs from 'node:fs';
const course = JSON.parse(fs.readFileSync(new URL('../training/course.json', import.meta.url), 'utf8'));
test.beforeEach(async ({context,request})=>{
  await context.addCookies([{name:'nac_session',value:'browser-session',url:'http://127.0.0.1:18767'}]);
  const status=await context.request.get('/api/status');expect(status.status()).toBe(200);
  const session=await status.json();
  if(session.branch!=='main'){
    const left=await context.request.post('/api/drafts/leave',{headers:{Origin:'http://127.0.0.1:18767','X-Editor-Token':session.token},data:{}});expect(left.status()).toBe(200);
  }
  const sources=await (await context.request.get('/api/repositories')).json();
  if(sources.selected!=='notariat8/ontology'){
    const selected=await context.request.post('/api/repositories/select',{headers:{Origin:'http://127.0.0.1:18767','X-Editor-Token':session.token},data:{repository:'notariat8/ontology'}});expect(selected.status()).toBe(200);
  }
});

test('all training slides, learning questions and handbook chapters are usable at the scaled desktop size', async ({page}) => {
  await page.setViewportSize({width:1536, height:760}); const errors=[]; page.on('pageerror', error=>errors.push(error.message));
  await page.goto('/learning/'); await expect(page.locator('#sections button')).toHaveCount(6);
  const slides = course.lessons.flatMap(lesson=>lesson.slides);
  for (const [index, slide] of slides.entries()) {
    await expect(page.locator('main h1')).toHaveText(slide.title);
    await page.locator('.choices button').nth(slide.answer).click(); await expect(page.locator('.feedback')).toContainText('Richtig.');
    await expect(page.locator('header')).toBeInViewport(); await expect(page.locator('footer')).toBeInViewport();
    expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight)).toBe(true);
    if (index < slides.length-1) await page.locator('#next').click();
  }
  await expect(page.locator('#next')).toBeDisabled();
  await page.evaluate(()=>window.print=()=>{}); await page.locator('#print').click(); await expect(page.locator('#print-content article')).toHaveCount(18);
  await page.locator('#handbook-mode').click(); await expect(page.locator('#sections button')).toHaveCount(8);
  for (let index=0;index<8;index++) { await page.locator('#sections button').nth(index).click(); await expect(page.locator('main h1')).toBeVisible(); await expect(page.locator('main table')).toBeVisible(); }
  await page.locator('#print').click(); await expect(page.locator('#print-content article')).toHaveCount(8); expect(errors).toEqual([]);
});

test('training save needs preview confirmation and never writes to the data API', async ({page}) => {
  await page.goto('/'); await page.locator('[data-menu=help]').click(); await page.locator('[data-help-topic=training]').click();
  const frame=page.frameLocator('#learning-frame'); await expect(frame.locator('#position')).toContainText('Folie 1');
  await expect(frame.locator('header')).toBeHidden(); await expect(frame.locator('aside')).toBeHidden(); await expect(page.locator('#task-navigation button')).toHaveCount(6);
  await page.locator('#task-navigation button').nth(2).click(); await expect(frame.locator('#position')).toHaveText('Folie 7 von 18');
  const writes=[]; page.on('request',request=>{if(request.method()!=='GET')writes.push(request.url());});
  await frame.getByRole('button',{name:'Bezeichnung üben',exact:true}).click(); await frame.locator('#practice-label').fill('Künstliche Übungsfrage');
  await frame.locator('#practice-preview').click(); await expect(frame.locator('#practice-before')).toContainText('Benötigte Schutzausrüstung'); await expect(frame.locator('#practice-after')).toContainText('Künstliche Übungsfrage');
  await expect(frame.locator('.model')).not.toContainText('Künstliche Übungsfrage'); await frame.locator('#practice-confirm').click(); await expect(frame.locator('#practice-result')).toContainText('Nur das künstliche Beispiel');
  await frame.getByRole('button',{name:'Schließen',exact:true}).click(); await expect(frame.locator('.model')).toContainText('Künstliche Übungsfrage'); expect(writes).toEqual([]);
  await page.reload(); await page.locator('[data-menu=help]').click(); await page.locator('[data-help-topic=training]').click(); await expect(frame.locator('.model')).toContainText('Benötigte Schutzausrüstung');
});
test('failed sign-in explains recovery and provides a safe diagnostic identifier', async ({page}) => {
  await page.setViewportSize({width:1536,height:760});
  const response=await page.goto('/callback?code=synthetic-browser-code');
  expect(response.status()).toBe(401);
  await expect(page.getByRole('heading',{name:'Anmeldung nicht abgeschlossen'})).toBeVisible();
  await expect(page.locator('main')).toContainText('diesem Browser');
  await expect(page.locator('.auth-diagnostic code')).toHaveText(/^[a-f0-9]{12}$/);
  await expect(page.getByRole('link',{name:'Erneut anmelden'})).toHaveAttribute('href','http://127.0.0.1:18767/login');
  await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Erneut anmelden'})).toBeFocused();
  expect(await page.locator('body').innerText()).not.toContain('synthetic-browser-code');
  expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight)).toBe(true);
  expect((await page.request.get('/api/status')).status()).toBe(200);
});

test('software opens a two-case external dataset and renders its graph',async ({page})=>{
  const errors=[]; page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#case-list .case-item')).toHaveCount(2);
  await expect(page.locator('#case-count')).toHaveText('2');
  for (const slug of ['demo-eins','demo-zwei']) {
    await page.locator('#case-list').getByRole('button',{name:'Künstlicher Fall '+slug,exact:true}).click();
    await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall '+slug);
    await expect(page.locator('#graph .graph-node').first()).toBeAttached();
  }
  expect(errors).toEqual([]);
});

test('context hints support hover, keyboard focus, disabled commands and Escape',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');
  await page.locator('.tree-node').first().click();await expect(page.locator('#graph-inspector')).toBeVisible();
  await page.locator('#selection-help').hover();const tip=page.getByRole('tooltip');await expect(tip).toContainText('fachlichen Kontext');
  await expect(page.locator('#selection-help')).toHaveAttribute('aria-describedby','app-tooltip');
  await tip.hover();await expect(tip).toBeVisible();await page.keyboard.press('Escape');await expect(tip).toBeHidden();await expect(page.locator('#graph-inspector')).toBeVisible();
  await page.locator('[data-menu=file]').click();await page.locator('#save').hover();await expect(tip).toContainText('keine ungespeicherten Änderungen');await expect(page.locator('#save')).toBeDisabled();
  await page.locator('#app-search').click();await page.keyboard.press('Tab');await expect(tip).toBeVisible();
  const bounds=await tip.boundingBox();const size=page.viewportSize();expect(bounds.x).toBeGreaterThanOrEqual(0);expect(bounds.x+bounds.width).toBeLessThanOrEqual(size.width);expect(bounds.y+bounds.height).toBeLessThanOrEqual(size.height);
  await page.keyboard.press('Escape');await expect(tip).toBeHidden();await expect(page.locator('#graph-inspector')).toBeVisible();
});

test('right-click targets the clicked node without writes; keyboard menu returns focus and opens its help',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');
  const writes=[];page.on('request',request=>{if(request.method()!=='GET')writes.push(request.url());});
  await page.locator('.tree-node[data-context-node=demo0]').click();
  const target=page.locator('.tree-node[data-context-node=demo1]');await target.click({button:'right'});
  const menu=page.getByRole('menu',{name:'Befehle für Beispiel Dokumenttyp'});await expect(menu).toBeVisible();await expect(page.locator('#inspector-title')).toHaveText('Beispiel Angabenfrage');
  await expect(menu.getByRole('menuitem',{name:'Entfernen',exact:true})).toHaveCount(0);await expect(page.locator('#branch')).toHaveText('Lesemodus');expect(writes).toEqual([]);
  await page.keyboard.press('Escape');await expect(menu).toBeHidden();await expect(target).toBeFocused();await expect(page.locator('#graph-inspector')).toBeVisible();
  await page.keyboard.press('Shift+F10');await expect(menu).toBeVisible();await expect(menu.getByRole('menuitem',{name:'Öffnen',exact:true})).toBeFocused();
  await page.keyboard.press('ArrowDown');await expect(menu.getByRole('menuitem',{name:'Bearbeiten',exact:true})).toBeFocused();
  await page.keyboard.press('End');await expect(menu.getByRole('menuitem',{name:'Hilfe zur Auswahl',exact:true})).toBeFocused();await page.keyboard.press('Enter');
  await expect(page.locator('#selection-help-title')).toHaveText('Hilfe zu Beispiel Dokumenttyp');await expect(page.locator('#selection-help-dialog')).toBeVisible();expect(writes).toEqual([]);
  await page.locator('#selection-help-close').click();await page.locator('.tree-node[data-context-node=demo0]').click({button:'right'});await page.getByRole('menuitem',{name:'Verbindungen',exact:true}).click();
  await expect(page.locator('#inspector-title')).toHaveText('Beispiel Angabenfrage');await expect(page.locator('#relation-context')).toContainText('erfordert');expect(writes).toEqual([]);
});

test('graph context menu fits viewport edges and keeps native text editing commands',async ({page})=>{
  await page.setViewportSize({width:1536,height:760});await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');
  await page.locator('#graph [data-context-node=demo1]').click({button:'right'});await expect(page.getByRole('menu')).toHaveAttribute('aria-label','Befehle für Beispiel Dokumenttyp');
  await page.keyboard.press('Escape');
  // The event position can be at the viewport edge, independently of the node's position.
  await page.locator('#graph [data-context-node=demo1]').dispatchEvent('contextmenu',{clientX:1534,clientY:758});const menu=page.getByRole('menu');await expect(menu).toBeVisible();
  const rect=await menu.boundingBox();expect(rect.x+rect.width).toBeLessThanOrEqual(1536);expect(rect.y+rect.height).toBeLessThanOrEqual(760);
  expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.keyboard.press('Tab');await expect(menu).toBeHidden();
  await page.evaluate(()=>{window.textContextPrevented=null;document.addEventListener('contextmenu',event=>{if(event.target.id==='app-search')window.textContextPrevented=event.defaultPrevented;});});
  await page.locator('#app-search').click({button:'right'});await expect(menu).toBeHidden();expect(await page.evaluate(()=>window.textContextPrevented)).toBe(false);
});

test('context editing and saving use the protected draft workflow; removing an own addition needs confirmation',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');
  await page.locator('.tree-node[data-context-node=demo1]').click({button:'right'});await page.getByRole('menuitem',{name:'Bearbeiten',exact:true}).click();
  await expect(page.locator('#branch')).toHaveText('Mein Entwurf');await expect(page.locator('#detail-title')).toHaveText('Beispiel Dokumenttyp');
  const label=page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input');await expect(label).toBeFocused();await label.fill('Künstlicher Dokumenttyp aus dem Kontextmenü');
  await label.hover();await expect(page.getByRole('tooltip')).toContainText('keine konkrete Akte');
  await page.locator('.tree-node[data-context-node=demo0]').click({button:'right'});await page.getByRole('menuitem',{name:'Speichern',exact:true}).click();await expect(page.locator('#change-preview')).toBeVisible();await expect(page.locator('#preview-list')).toContainText('Bezeichnung');
  await page.locator('#confirm-save').click();await expect(page.locator('#notice')).toContainText('Fallvorlage gespeichert');
  await page.locator('[data-area=edit]').click();await page.locator('#new-node').click();await expect(page.locator('.tree-node[data-context-node="local.1"]')).toBeVisible();
  let cancelled=false;page.once('dialog',async dialog=>{cancelled=true;await dialog.dismiss();});
  await page.locator('.tree-node[data-context-node="local.1"]').click({button:'right'});await page.getByRole('menuitem',{name:'Entfernen',exact:true}).click();await expect.poll(()=>cancelled).toBe(true);await expect(page.locator('.tree-node[data-context-node="local.1"]')).toBeVisible();
  page.once('dialog',dialog=>dialog.accept());await page.locator('.tree-node[data-context-node="local.1"]').click({button:'right'});await page.getByRole('menuitem',{name:'Entfernen',exact:true}).click();await expect(page.locator('.tree-node[data-context-node="local.1"]')).toHaveCount(0);
});

test('context commands respect another-case drafts and common-term maintenance permissions',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');await page.locator('[data-area=edit]').click();await page.locator('#start-branch').click();await expect(page.locator('#branch')).toHaveText('Mein Entwurf');
  await page.locator('.case-item[data-context-case=demo-zwei]').click();await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-zwei');
  await page.locator('.tree-node[data-context-node=demo0]').click({button:'right'});const edit=page.getByRole('menuitem',{name:'Bearbeiten',exact:true});await expect(edit).toBeDisabled();await edit.hover();await expect(page.getByRole('tooltip')).toContainText('anderen Arbeitsbereich');await page.keyboard.press('Escape');
  // The same identity can read shared terms while lacking their separate maintenance role.
  await page.route('**/api/status',async route=>{const response=await route.fetch();const status=await response.json();await route.fulfill({json:{...status,ontology_maintainer:false}});});
  await page.reload();await page.locator('[data-menu=view]').click();await page.locator('#vocab-nav').click();await expect(page.locator('.vocab-item').first()).toBeVisible();
  const writes=[];page.on('request',request=>{if(request.method()!=='GET')writes.push(request.url());});
  await page.locator('.vocab-item').first().click({button:'right'});await expect(edit).toBeDisabled();await edit.hover();await expect(page.getByRole('tooltip')).toContainText('zusätzliche fachliche Berechtigung');
  await page.getByRole('menuitem',{name:'Hilfe zur Auswahl',exact:true}).click();await expect(page.locator('#selection-help-title')).toContainText('Hilfe zu Beispiel');expect(writes).toEqual([]);
});

test('opening another case from its context menu retains the unsaved-change guard',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-count')).toHaveText('2');await page.locator('.tree-node[data-context-node=demo0]').click({button:'right'});await page.getByRole('menuitem',{name:'Bearbeiten',exact:true}).click();
  const label=page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input');await label.fill('Nicht gespeicherte künstliche Änderung');
  page.once('dialog',dialog=>dialog.dismiss());await page.locator('.case-item[data-context-case=demo-zwei]').click({button:'right'});await page.getByRole('menuitem',{name:'Öffnen',exact:true}).click();await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');await expect(label).toHaveValue('Nicht gespeicherte künstliche Änderung');
  await page.locator('.case-item[data-context-case=demo-eins]').click({button:'right'});await page.getByRole('menuitem',{name:'Informationen',exact:true}).click();await expect(page.locator('#case-sources')).toBeVisible();await expect(page.locator('#summary-read')).toContainText('Künstliches Modell');
});

test('a pending save disables context mutations and closes an obsolete menu',async ({page})=>{
  await editArtificialLabel(page,'Künstliche Änderung vor verzögerter Vorschau');
  let release;const pending=new Promise(resolve=>{release=resolve;});let previews=0;
  await page.route('**/api/cases/demo-eins/preview',async route=>{previews++;await pending;await route.continue();});
  await page.locator('.tree-node[data-context-node=demo0]').click({button:'right'});await expect(page.getByRole('menu')).toBeVisible();
  await page.keyboard.press('Control+s');await expect.poll(()=>previews).toBe(1);await expect(page.getByRole('menu')).toBeHidden();
  await page.locator('#graph [data-context-node=demo0]').click({button:'right'});await expect(page.getByRole('menuitem',{name:'Bearbeiten',exact:true})).toBeDisabled();await expect(page.getByRole('menuitem',{name:'Speichern',exact:true})).toBeDisabled();await expect(page.getByRole('menu')).toBeFocused();
  await page.getByRole('menuitem',{name:'Bearbeiten',exact:true}).hover();await expect(page.getByRole('tooltip')).toContainText('laufenden Vorgang');
  release();await expect(page.locator('#change-preview')).toBeVisible();await expect(page.getByRole('menu')).toBeHidden();expect(previews).toBe(1);await expect(page.locator('#preview-list')).toContainText('Bezeichnung');
});
test('two-case search index and draft creation use configured catalog scope',async ({page})=>{
  const request=page.request;
  const index=await request.get('/api/case-index'); expect(index.status()).toBe(200);
  expect((await index.json()).case_count).toBe(2);
  const token=(await (await request.get('/api/status')).json()).token;
  const branch=await request.post('/api/start-branch',{headers:{'Origin':'http://127.0.0.1:18767','X-Editor-Token':token},data:{purpose:'case',case:'demo-eins'}});
  expect(branch.status()).toBe(200);
  expect((await branch.json()).case).toBe('demo-eins');
  const missing=await request.get('/api/cases/not-in-catalog'); expect(missing.status()).toBe(400);
});
test('release links to the delivered commit and data targets can be switched', async ({page}) => {
  const commit = 'b'.repeat(40);
  await page.route('**/api/release', route => route.fulfill({json: {commit}}));
  await page.goto('/');
  await expect(page.locator('#release-link')).toHaveText(commit.slice(0,12));
  await expect(page.locator('#release-link')).toHaveAttribute('href', 'https://github.com/ontologie8/editor8/commit/' + commit);
  await expect(page.locator('#repository-select option')).toHaveCount(2);
  await expect(page.locator('#editor-brand')).toBeVisible();
  await expect(page.locator('#data-brand')).toBeVisible();
  expect(await page.locator('#editor-brand').evaluate(image=>image.complete&&image.naturalWidth>0)).toBe(true);
  expect(await page.locator('#data-brand').evaluate(image=>image.complete&&image.naturalWidth>0)).toBe(true);
  const token=(await (await page.request.get('/api/status')).json()).token;
  await page.request.post('/api/drafts/leave', {headers: {'Origin':'http://127.0.0.1:18767', 'X-Editor-Token':token}, data: {}});
  await page.reload();
  await page.locator('#repository-select').selectOption('example/second-dataset');
  await expect(page.locator('#repository-name')).toHaveText('example/second-dataset');
  await expect(page.locator('#data-brand')).toBeHidden();
  await expect(page.locator('#case-list .case-item')).toHaveCount(2);
  await page.setViewportSize({width:500, height:800});
  await expect(page.locator('#session-user')).toHaveText('browser-tester');await expect(page.locator('#session-user')).toBeVisible();
  await expect(page.locator('#release-link')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('Office desktop controls fit the scaled 4K workplace and effective browser height',async ({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));await page.goto('/');await expect(page.locator('#case-count')).toHaveText('2');
  for(const [width,height] of [[1536,864],[1536,760],[1440,900],[1920,1080],[2560,1440],[3840,2160]]){
    await page.setViewportSize({width,height});
    expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    for(const selector of ['.menubar','.office-ribbon','.area-navigation','#repository-select','.release-footer']){
      const rect=await page.locator(selector).boundingBox();expect(rect,selector).toBeTruthy();expect(rect.x).toBeGreaterThanOrEqual(0);expect(rect.y).toBeGreaterThanOrEqual(0);expect(rect.x+rect.width).toBeLessThanOrEqual(width+1);expect(rect.y+rect.height).toBeLessThanOrEqual(height+1);
    }
  }
  await page.setViewportSize({width:1536,height:864});await expect(page.locator('[data-menu]')).toHaveCount(4);await expect(page.locator('[data-area]')).toHaveCount(3);await expect(page.locator('[data-menu=help]')).toHaveCount(1);expect(errors).toEqual([]);
});

test('ribbon and data tree collapse independently; general help differs from selection help',async ({page})=>{
  await page.goto('/');await expect(page.locator('#case-count')).toHaveText('2');
  await page.locator('#navigation-toggle').click();await expect(page.locator('.case-sidebar')).toBeHidden();await expect(page.locator('.area-navigation')).toBeVisible();await page.locator('#navigation-toggle').click();await expect(page.locator('.case-sidebar')).toBeVisible();
  await page.keyboard.press('Control+F1');await expect(page.locator('#office-ribbon')).toBeHidden();await page.locator('[data-menu=file]').click();await expect(page.locator('#office-ribbon')).toBeVisible();await page.locator('#app-search').click();await expect(page.locator('#office-ribbon')).toBeHidden();await page.keyboard.press('Control+F1');await expect(page.locator('#office-ribbon')).toBeVisible();
  await page.locator('[data-menu=help]').click();await expect(page.locator('#help-content h2')).toHaveText('Kurzanleitung');await page.locator('[data-help-topic=training]').click();await expect(page.frameLocator('#learning-frame').locator('#position')).toHaveText('Folie 1 von 18');await page.locator('[data-area=understand]').click();
  await page.locator('.tree-node').first().click();await expect(page.locator('#graph-inspector')).toBeVisible();await page.locator('#selection-help').click();await expect(page.locator('#selection-help-dialog')).toBeVisible();await expect(page.locator('#selection-help-title')).toContainText('Hilfe zu');await expect(page.locator('#selection-help-content')).toContainText('Künstlicher Fall');await page.locator('#selection-help-close').click();
  await page.locator('#app-search').fill('demo-zwei');await expect(page.locator('#case-list .case-item')).toHaveCount(1);await page.locator('#app-search').fill('');await page.locator('[data-menu=file]').click();await page.locator('#file-open').click();await expect(page.locator('#app-search')).toBeFocused();
  let printed=false;await page.exposeFunction('printed',()=>{printed=true});await page.evaluate(()=>{window.print=()=>window.printed()});await page.locator('[data-menu=file]').click();await page.locator('#print').click();await expect.poll(()=>printed).toBe(true);await expect(page.locator('#print-document')).toContainText('Künstlicher Fall');await page.emulateMedia({media:'print'});await expect(page.locator('#print-document')).toBeVisible();await expect(page.locator('.topbar')).toBeHidden();
});

test('Office editing saves an actual draft and submits it through the protected API',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');await page.locator('[data-area=edit]').click();await page.locator('#start-branch').click();await expect(page.locator('#branch')).toHaveText('Mein Entwurf');
  // Beginning a branch reloads the model; return to the editing area.
  await page.locator('[data-area=edit]').click();await page.locator('.tree-node').first().click();await page.locator('#edit-node').click();const label=page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input');await label.fill('Geprüfte künstliche Bezeichnung');
  await page.keyboard.press('Control+s');await expect(page.locator('#change-preview')).toBeVisible();await expect(page.locator('#preview-list')).toContainText('Bezeichnung');await page.locator('#confirm-save').click();await expect(page.locator('#notice')).toContainText('Fallvorlage gespeichert');await expect(page.locator('#save-current')).toBeDisabled();
  await page.locator('[data-area=review]').click();await page.locator('#change-reason').fill('Künstliche Browserprüfung des Office-Arbeitsablaufs.');await page.locator('#change-source').fill('Synthetische Testdaten');await page.locator('#submit-review').click();await expect(page.locator('#review-link')).toHaveAttribute('href','https://github.com/notariat8/ontology/pull/123456');await expect(page.locator('#branch')).toHaveText('Lesemodus');
});

async function editArtificialLabel(page, value) {
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');
  await page.locator('[data-area=edit]').click();await page.locator('#start-branch').click();await expect(page.locator('#branch')).toHaveText('Mein Entwurf');
  await page.locator('[data-area=edit]').click();await page.locator('.tree-node').first().click();await page.locator('#edit-node').click();
  const label=page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input');await label.fill(value);return label;
}

test('opening help during initial loading keeps the chosen view',async ({page})=>{
  let release;const gate=new Promise(resolve=>{release=resolve;});let delivered=false;
  await page.route('**/api/status',async route=>{const response=await route.fetch();await gate;await route.fulfill({response});delivered=true;});
  await page.goto('/');await page.locator('[data-menu=help]').click();await page.locator('[data-help-topic=training]').click();
  await expect(page.frameLocator('#learning-frame').locator('#position')).toContainText('Folie 1');
  release();await expect.poll(()=>delivered).toBe(true);await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');
  await expect(page.locator('#help-content')).toBeVisible();await expect(page.locator('#task-navigation button')).toHaveCount(6);
});

test('signing out asks before discarding input and cancelling retains the session',async ({page})=>{
  const label=await editArtificialLabel(page,'Noch offene künstliche Eingabe');let writes=0;
  await page.route('**/api/logout',async route=>{writes++;await route.fulfill({json:{ok:true}});});
  await page.route('**/login',route=>route.fulfill({contentType:'text/html',body:'<h1>Neue Anmeldung</h1>'}));
  const decisions=[];page.on('dialog',dialog=>{decisions.push(dialog.type());return decisions.length===1?dialog.dismiss():dialog.accept();});
  await page.locator('#logout').click();await expect(label).toHaveValue('Noch offene künstliche Eingabe');
  expect(writes).toBe(0);expect((await page.request.get('/api/status')).status()).toBe(200);await expect(page.locator('#save-current')).toBeEnabled();
  await page.locator('#logout').click();await expect(page.getByRole('heading',{name:'Neue Anmeldung'})).toBeVisible();
  expect(writes).toBe(1);expect(decisions).toEqual(['confirm','confirm']);
});

test('preview uses current input and repeated shortcuts create a single request',async ({page})=>{
  const label=await editArtificialLabel(page,'Erste künstliche Eingabe');let release;let requests=0;
  const gate=new Promise(resolve=>{release=resolve;});
  await page.route('**/api/cases/demo-eins/preview',async route=>{requests++;await gate;await route.fulfill({json:{changed:true,changes:['Bezeichnung geändert']}});});
  await page.keyboard.press('Control+s');await expect.poll(()=>requests).toBe(1);
  await page.keyboard.press('Control+s');await expect(page.locator('#save-current')).toBeDisabled();
  await label.fill('Neuere künstliche Eingabe');release();
  await expect(page.locator('#notice')).toContainText('während der Vorschau geändert');await expect(page.locator('#change-preview')).toBeHidden();
  await expect(label).toHaveValue('Neuere künstliche Eingabe');await expect(page.locator('#save-current')).toBeEnabled();
  await page.keyboard.press('Control+s');await expect(page.locator('#change-preview')).toBeVisible();expect(requests).toBe(2);
});

test('saving sends the reviewed snapshot once and keeps failed input available for retry',async ({page})=>{
  const value='Geschützte künstliche Eingabe';const label=await editArtificialLabel(page,value);
  await expect(page.locator('.tree-node.active')).toHaveText(value);
  await page.keyboard.press('Control+s');await expect(page.locator('#change-preview')).toBeVisible();
  let release;const gate=new Promise(resolve=>{release=resolve;});let writes=0;let submitted;
  await page.route('**/api/cases/demo-eins/save',async route=>{
    writes++;submitted=route.request().postDataJSON();
    if(writes===1){await gate;await route.fulfill({status:503,json:{error:'Künstlicher Verbindungsfehler'}});}
    else if(writes===2)await route.fulfill({status:503,contentType:'text/html',body:'<h1>Gateway unavailable</h1>'});
    else await route.continue();
  });
  await page.locator('#confirm-save').click();await expect.poll(()=>writes).toBe(1);
  await expect(page.locator('#confirm-save')).toBeDisabled();await expect(page.locator('#cancel-preview')).toBeDisabled();await expect(page.locator('#close-preview')).toBeDisabled();
  await page.keyboard.press('Escape');await page.keyboard.press('Control+s');await expect(page.locator('#change-preview')).toBeVisible();
  expect(writes).toBe(1);expect(submitted.nodes.some(node=>node.label===value)).toBe(true);release();
  await expect(page.locator('#preview-status')).toContainText('Künstlicher Verbindungsfehler');await expect(page.locator('#confirm-save')).toBeEnabled();await expect(page.locator('#confirm-save')).toBeFocused();
  await page.locator('#cancel-preview').click();await expect(label).toHaveValue(value);await expect(page.locator('#save-current')).toBeEnabled();
  await page.keyboard.press('Control+s');await expect(page.locator('#change-preview')).toBeVisible();await page.locator('#confirm-save').click();
  await expect(page.locator('#preview-status')).toContainText('keine gültige Antwort');await expect(page.locator('#confirm-save')).toBeEnabled();await expect(page.locator('#confirm-save')).toBeFocused();await page.keyboard.press('Enter');
  await expect(page.locator('#notice')).toContainText('Fallvorlage gespeichert');await expect(page.locator('#save-current')).toBeDisabled();expect(writes).toBe(3);
});

test('slow case responses cannot replace a newer selection or newly edited input',async ({page})=>{
  await page.goto('/?case=demo-eins');await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');
  let release;let requested=0;let delivered=0;const gate=new Promise(resolve=>{release=resolve;});
  await page.route('**/api/cases/demo-zwei',async route=>{requested++;const response=await route.fetch();await gate;await route.fulfill({response});delivered++;});
  await page.locator('#case-list').getByRole('button',{name:'Künstlicher Fall demo-zwei',exact:true}).click();await expect.poll(()=>requested).toBe(1);
  const newer=page.waitForResponse('**/api/cases/demo-eins');await page.locator('#case-list').getByRole('button',{name:'Künstlicher Fall demo-eins',exact:true}).click();await newer;
  release();await expect.poll(()=>delivered).toBe(1);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');
  await page.unroute('**/api/cases/demo-zwei');
  const label=await editArtificialLabel(page,'Erster künstlicher Stand');
  let releaseNext;const nextGate=new Promise(resolve=>{releaseNext=resolve;});let nextRequested=false;let nextDelivered=false;
  await page.route('**/api/cases/demo-zwei',async route=>{nextRequested=true;const response=await route.fetch();await nextGate;await route.fulfill({response});nextDelivered=true;});
  page.on('dialog',dialog=>dialog.accept());await page.locator('#case-list').getByRole('button',{name:'Künstlicher Fall demo-zwei',exact:true}).click();await expect.poll(()=>nextRequested).toBe(true);
  await label.fill('Eingabe während des Ladens');releaseNext();await expect.poll(()=>nextDelivered).toBe(true);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');await expect(label).toHaveValue('Eingabe während des Ladens');await expect(page.locator('#save-current')).toBeEnabled();
});

test('reload recovers unsaved model inputs and their reason without writing them',async ({page})=>{
  const label=await editArtificialLabel(page,'Wiederhergestellte künstliche Bezeichnung');
  await page.locator('[data-area=review]').click();await page.locator('#change-reason').fill('Künstlicher Grund bleibt nach dem Neuladen erhalten.');
  const cache=await page.evaluate(()=>Object.entries(sessionStorage).find(([key])=>key.startsWith('editor8:inputs:v1:')));
  expect(cache).toBeTruthy();expect(JSON.parse(cache[1])).not.toHaveProperty('token');expect(JSON.parse(cache[1])).not.toHaveProperty('csrf');
  let writes=0;page.on('request',request=>{if(request.url().endsWith('/save'))writes++;});
  page.on('dialog',dialog=>dialog.accept());await page.reload();await expect(page.locator('#input-recovery')).toBeVisible();
  await page.locator('#restore-inputs').click();await expect(page.locator('#input-recovery')).toBeHidden();
  await expect(page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input')).toHaveValue('Wiederhergestellte künstliche Bezeichnung');
  await expect(page.locator('#change-reason')).toHaveValue('Künstlicher Grund bleibt nach dem Neuladen erhalten.');expect(writes).toBe(0);
  await page.keyboard.press('Control+s');await expect(page.locator('#preview-comparison')).toBeVisible();
  await expect(page.locator('#preview-comparison .diff-changed[role=button]')).toHaveCount(2);
  await page.locator('#confirm-save').click();await expect(page.locator('#notice')).toContainText('Fallvorlage gespeichert');
  expect(await page.evaluate(()=>JSON.parse(sessionStorage.getItem(Object.keys(sessionStorage).find(key=>key.startsWith('editor8:inputs:v1:')))).base.nodes.find(node=>node.id==='demo0').label)).toBe('Wiederhergestellte künstliche Bezeichnung');
});

test('expired session preserves inputs through login and resumes the owned draft',async ({page,context})=>{
  await editArtificialLabel(page,'Eingabe vor dem Sitzungsende');
  const session=await (await context.request.get('/api/status')).json();
  await context.request.post('/api/drafts/leave',{headers:{Origin:'http://127.0.0.1:18767','X-Editor-Token':session.token},data:{}});
  await page.route('**/api/cases/demo-eins/preview',async route=>{await page.unroute('**/api/cases/demo-eins/preview');await route.fulfill({status:401,json:{error:'Synthetisch abgelaufene Sitzung'}});});
  await page.route('**/login',route=>route.fulfill({status:200,contentType:'text/html',body:'<p>Erneut angemeldet – synthetischer Anbieter</p>'}));
  await page.keyboard.press('Control+s');await expect(page).toHaveURL(/\/login$/);
  await page.goto('/');await expect(page.locator('#input-recovery')).toBeVisible();await page.locator('#restore-inputs').click();
  await expect(page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input')).toHaveValue('Eingabe vor dem Sitzungsende');await expect(page.locator('#branch')).toHaveText('Mein Entwurf');
});

test('recovery keeps concurrent unrelated changes and refuses a conflicting field',async ({page})=>{
  await editArtificialLabel(page,'Eigene künstliche Bezeichnung');page.on('dialog',dialog=>dialog.accept());
  await page.route('**/api/cases/demo-eins',async route=>{const response=await route.fetch();const model=await response.json();model.nodes.find(node=>node.id==='demo1').detail='Parallel geänderte Erläuterung';await route.fulfill({response,json:model});});
  await page.reload();await page.locator('#restore-inputs').click();await expect(page.locator('#input-recovery')).toBeHidden();
  expect(await page.evaluate(()=>state.current.nodes.find(node=>node.id==='demo1').detail)).toBe('Parallel geänderte Erläuterung');
  await page.unroute('**/api/cases/demo-eins');
  await page.route('**/api/cases/demo-eins',async route=>{const response=await route.fetch();const model=await response.json();model.nodes.find(node=>node.id==='demo0').label='Konkurrierende Bezeichnung';await route.fulfill({response,json:model});});
  await page.reload();await page.locator('#restore-inputs').click();await expect(page.locator('#input-recovery')).toBeVisible();
  await expect(page.locator('#recovery-status')).toContainText('nichts überschrieben');
  const download=page.waitForEvent('download');await page.locator('#export-inputs').click();const file=await download;expect(file.suggestedFilename()).toBe('editor8-eingaben.json');
});

test('recovery never offers another account or another model repository inputs',async ({page})=>{
  await editArtificialLabel(page,'Nur für das eigene Konto');
  await page.evaluate(()=>{state.dirty=false;const key=Object.keys(sessionStorage).find(key=>key.startsWith('editor8:inputs:v1:'));const record=JSON.parse(sessionStorage.getItem(key));record.user='anderes-konto';sessionStorage.setItem(key,JSON.stringify(record));});
  page.on('dialog',dialog=>dialog.accept());await page.reload();await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');
  await expect.poll(()=>page.evaluate(()=>Object.keys(sessionStorage).some(key=>key.startsWith('editor8:inputs:v1:')))).toBe(false);await expect(page.locator('#input-recovery')).toBeHidden();
  await page.evaluate(()=>{const repository=document.getElementById('repository-name').textContent==='example/second-dataset'?'notariat8/ontology':'example/second-dataset';sessionStorage.setItem('editor8:inputs:v1:browser-tester:'+repository,JSON.stringify({version:1,user:'browser-tester',repository,updated:Date.now(),model:{nodes:[{label:'Nicht der aktuelle Bestand'}]}}));});
  await page.reload();await expect(page.locator('#case-title')).toHaveText('Künstlicher Fall demo-eins');await expect(page.locator('#input-recovery')).toBeHidden();expect(await page.locator('body').innerText()).not.toContain('Nicht der aktuelle Bestand');
});

test('unavailable browser storage keeps inputs open and offers an in-memory export',async ({page})=>{
  await page.addInitScript(()=>{Storage.prototype.setItem=function(){throw new DOMException('synthetic unavailable storage','QuotaExceededError');};});
  await editArtificialLabel(page,'Ohne Browserspeicher erhalten');
  await page.route('**/api/cases/demo-eins/preview',route=>route.fulfill({status:401,json:{error:'Synthetisch abgelaufene Sitzung'}}));
  await page.keyboard.press('Control+s');await expect(page).not.toHaveURL(/\/login$/);await expect(page.locator('#input-recovery')).toBeVisible();
  await expect(page.locator('#reconnect-inputs')).toBeVisible();
  const downloading=page.waitForEvent('download');await page.locator('#export-inputs').click();const downloaded=await downloading;expect(downloaded.suggestedFilename()).toBe('editor8-eingaben.json');
  const stream=await downloaded.createReadStream();const buffers=[];for await(const chunk of stream)buffers.push(chunk);const entry=JSON.parse(Buffer.concat(buffers).toString());
  expect(entry.model.nodes.some(node=>node.label==='Ohne Browserspeicher erhalten')).toBe(true);expect(entry).not.toHaveProperty('token');
  await page.unroute('**/api/cases/demo-eins/preview');
  const session=await (await page.request.get('/api/status')).json();await page.request.post('/api/drafts/leave',{headers:{Origin:'http://127.0.0.1:18767','X-Editor-Token':session.token},data:{}});
  await page.locator('#reconnect-inputs').click();await expect(page.locator('#input-recovery')).toBeHidden();
  await expect(page.locator('#node-form label').filter({hasText:/^Bezeichnung$/}).locator('input')).toHaveValue('Ohne Browserspeicher erhalten');await expect(page.locator('#save-current')).toBeEnabled();
});

test.describe('scaled graph comparison',()=>{
test.use({deviceScaleFactor:2.5});
test('graph comparison is keyboard usable and fits the effective scaled desktop',async ({page})=>{
  await page.setViewportSize({width:1536,height:760});await editArtificialLabel(page,'Grafisch geprüfte künstliche Bezeichnung');
  await page.keyboard.press('Control+s');const comparison=page.locator('#preview-comparison');await expect(comparison).toBeVisible();
  const after=comparison.locator('.comparison-pane').last().getByRole('button',{name:'Geändert: Grafisch geprüfte künstliche Bezeichnung'});await after.focus();await page.keyboard.press('Enter');
  await expect(comparison.locator('.comparison-detail')).toContainText('Bezeichnung');await expect(comparison.locator('.comparison-detail')).toContainText('Grafisch geprüfte');
  const rect=await page.locator('#change-preview').boundingBox();expect(rect.x).toBeGreaterThanOrEqual(0);expect(rect.y+rect.height).toBeLessThanOrEqual(760);
  expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight)).toBe(true);
  await page.screenshot({path:'test-results/graph-comparison-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'test-results/graph-comparison-mobile.png',fullPage:true});
});
});

test('shared-term recovery merges separate fields and flags conflicting definitions',async ({page})=>{
  await page.goto('/');await expect(page.locator('#case-count')).toHaveText('2');
  const result=await page.evaluate(()=>{
    const base={terms:[{id:'Demo',label:'Künstlicher Begriff',comment:'Bisherige Bedeutung',kind:'class'}],revision:'old'};
    const local=structuredClone(base);local.terms[0].label='Eigene Bezeichnung';
    const latest=structuredClone(base);latest.terms[0].comment='Unabhängige neue Bedeutung';latest.revision='current';latest.expected_ref='current-ref';
    const merged=EditorRecovery.merge(base,local,latest,'vocabulary');
    local.terms[0].comment='Widersprüchliche eigene Bedeutung';
    return {merged,conflict:EditorRecovery.merge(base,local,latest,'vocabulary')};
  });
  expect(result.merged.conflicts).toEqual([]);expect(result.merged.model.terms[0]).toMatchObject({label:'Eigene Bezeichnung',comment:'Unabhängige neue Bedeutung'});expect(result.merged.model.expected_ref).toBe('current-ref');expect(result.conflict.conflicts).toHaveLength(1);
});

test('a committed save with a lost response is recovered without repeating its change',async ({page})=>{
  await editArtificialLabel(page,'Gespeichert trotz verlorener Antwort');
  await page.keyboard.press('Control+s');await page.route('**/api/cases/demo-eins/save',async route=>{await route.fetch();await route.fulfill({status:503,json:{error:'Antwort synthetisch verloren'}});});
  await page.locator('#confirm-save').click();await expect(page.locator('#preview-status')).toContainText('verloren');await page.locator('#cancel-preview').click();
  page.on('dialog',dialog=>dialog.accept());await page.reload();await page.locator('#restore-inputs').click();await expect(page.locator('#input-recovery')).toBeHidden();
  await expect(page.locator('#notice')).toContainText('bereits gespeichert');await expect(page.locator('#save-current')).toBeDisabled();
  expect(await page.evaluate(()=>Object.keys(sessionStorage).some(key=>key.startsWith('editor8:inputs:v1:')))).toBe(false);
});

test('reviewed changes show the same RDF-derived graph as the save preview',async ({page})=>{
  await editArtificialLabel(page,'Künstliche Änderung zur Prüfung');await page.keyboard.press('Control+s');
  const comparison=await page.evaluate(()=>fetch('/api/cases/demo-eins/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':state.token},body:JSON.stringify(state.current)}).then(response=>response.json()));
  await page.locator('#cancel-preview').click();
  await page.route('**/api/reviews',route=>route.fulfill({json:[{number:99,case:'demo-eins',author:'künstlicher-autor',draft:false}]}));
  await page.route('**/api/reviews/99',route=>route.fulfill({json:{number:99,title:'Künstliche Fachprüfung',case:'demo-eins',author:'künstlicher-autor',draft:false,url:'https://example.org/review/99',body:'Künstlicher Prüfgrund',changes:comparison.changes,comparison:comparison.comparison,can_review:true,can_approve:false,problem:''}}));
  await page.evaluate(()=>setView('fachpruefung'));await page.locator('#review-list .review-item').click();await expect(page.locator('#review-comparison')).toBeVisible();await expect(page.locator('#review-comparison .diff-changed[role=button]')).toHaveCount(2);await expect(page.locator('#approve-review')).toBeDisabled();
});

test('review notes survive reload after the model is saved and are cleared on logout',async ({page})=>{
  await editArtificialLabel(page,'Künstlicher gespeicherter Stand');await page.keyboard.press('Control+s');await page.locator('#confirm-save').click();await expect(page.locator('#save-current')).toBeDisabled();
  await page.locator('[data-area=review]').click();await page.locator('#change-reason').fill('Noch nicht eingereichte Begründung');
  page.on('dialog',dialog=>dialog.accept());await page.reload();await page.locator('#restore-inputs').click();await expect(page.locator('#input-recovery')).toBeHidden();
  await expect(page.locator('#change-reason')).toHaveValue('Noch nicht eingereichte Begründung');await expect(page.locator('#save-current')).toBeDisabled();
  await page.route('**/api/logout',route=>route.fulfill({json:{ok:true}}));await page.route('**/login',route=>route.fulfill({contentType:'text/html',body:'<h1>Neue Anmeldung</h1>'}));
  await page.locator('#logout').click();await expect(page.getByRole('heading',{name:'Neue Anmeldung'})).toBeVisible();expect(await page.evaluate(()=>Object.keys(sessionStorage).some(key=>key.startsWith('editor8:inputs:v1:')))).toBe(false);
});
