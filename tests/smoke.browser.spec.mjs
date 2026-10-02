// SPDX-License-Identifier: AGPL-3.0-or-later
import {test, expect} from '@playwright/test';
test.beforeEach(async ({context,request})=>{
  await context.addCookies([{name:'nac_session',value:'browser-session',url:'http://127.0.0.1:18767'}]);
  await context.request.post('/api/drafts/leave',{headers:{Origin:'http://127.0.0.1:18767','X-Editor-Token':'browser-csrf'},data:{}});
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
  const branch=await request.post('/api/start-branch',{headers:{'Origin':'http://127.0.0.1:18767','X-Editor-Token':'browser-csrf'},data:{purpose:'case',case:'demo-eins'}});
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
  await page.request.post('/api/drafts/leave', {headers: {'Origin':'http://127.0.0.1:18767', 'X-Editor-Token':'browser-csrf'}, data: {}});
  await page.reload();
  await page.locator('#repository-select').selectOption('example/second-dataset');
  await expect(page.locator('#repository-name')).toHaveText('example/second-dataset');
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
  await page.locator('[data-menu=help]').click();await expect(page.locator('#help-content h2')).toHaveText('Kurzanleitung');await page.locator('[data-help-topic=example]').click();await expect(page.locator('#help-content')).toContainText('künstliches Beispiel');await page.locator('[data-area=understand]').click();
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
