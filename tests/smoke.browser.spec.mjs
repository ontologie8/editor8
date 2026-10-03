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
