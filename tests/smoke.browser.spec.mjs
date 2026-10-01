// SPDX-License-Identifier: AGPL-3.0-or-later
import {test, expect} from '@playwright/test';
test.beforeEach(async ({context})=>{
  await context.addCookies([{name:'nac_session',value:'browser-session',url:'http://127.0.0.1:18767'}]);
});
test('software opens a two-case external dataset and renders its graph',async ({page})=>{
  const errors=[]; page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#case-list button')).toHaveCount(2);
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
  await expect(page.locator('#case-list button')).toHaveCount(2);
  await page.setViewportSize({width:500, height:800});
  await expect(page.locator('#release-link')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
