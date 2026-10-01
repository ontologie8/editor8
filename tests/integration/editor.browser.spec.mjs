// SPDX-License-Identifier: AGPL-3.0-or-later
import { test, expect } from '@playwright/test';

const origin = 'http://127.0.0.1:18766';

test.beforeEach(async ({ context }) => {
  await context.addCookies([{ name: 'nac_session', value: 'browser-session', url: origin }]);
});

test('all 20 maintained cases open with a rendered graph', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.request.get('/api/cases');
  expect(response.ok()).toBeTruthy();
  const cases = await response.json();
  expect(cases).toHaveLength(20);

  await page.goto('/');
  await expect(page.locator('#case-list button')).toHaveCount(20);
  for (const item of cases) {
    await page.locator('#case-list').getByRole('button', { name: item.title, exact: true }).click();
    await expect(page.locator('#case-title')).toHaveText(item.title);
    await expect(page.locator('#graph-status')).toContainText('Bausteine');
    await expect(page.locator('#graph .graph-node').first()).toBeAttached();
  }
  expect(errors).toEqual([]);
});

test('case search, graph keyboard access and catalog search work', async ({ page }) => {
  const modelResponse = await page.request.get('/api/cases/immobilienkaufvertrag');
  const model = await modelResponse.json();
  const connected = model.nodes.find(node => model.edges.some(edge => edge.from === node.id || edge.to === node.id));
  expect(connected).toBeTruthy();

  await page.goto('/?case=immobilienkaufvertrag');
  await expect(page.locator('#case-title')).toHaveText(model.title);
  await page.locator('#graph-find').click();
  await page.locator('#graph-query').fill(connected.label);
  await page.locator('#graph-query').press('ArrowDown');
  await expect(page.locator('#graph-results button').first()).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#case-node-search')).not.toBeVisible();
  await expect(page.locator('#graph-inspector')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#graph-inspector')).not.toBeVisible();

  const indexResponse = await page.request.get('/api/case-index');
  const index = await indexResponse.json();
  expect(index.case_count).toBe(20);
  const entry = index.entries.find(item => item.slug === 'erbausschlagung');
  await page.keyboard.press('Control+k');
  await expect(page.locator('#catalog-search')).toBeVisible();
  await page.locator('#case-index-query').fill(entry.label);
  const firstResult = page.locator('#case-index-results button').first();
  await expect(firstResult).toBeVisible();
  const selectedCase = (await firstResult.locator('small').textContent()).split(' · ')[0];
  await page.locator('#case-index-query').press('Enter');
  await expect(page.locator('#catalog-search')).not.toBeVisible();
  await expect(page.locator('#case-title')).toHaveText(selectedCase);
  await expect(page.locator('[data-view="bausteine"]')).toBeVisible();
});

test('mobile case selection has no horizontal page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 500, height: 900 });
  await page.goto('/?case=immobilienkaufvertrag');
  await expect(page.locator('#case-select')).toBeVisible();
  await page.locator('#case-select').selectOption('erbausschlagung');
  await expect(page.locator('#case-title')).toHaveText('Erbausschlagung');
  await expect(page.locator('#graph-status')).toContainText('Bausteine');
  for (const width of [500, 1100, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(1);
  }
});

test('editing remains unavailable until the first case has loaded', async ({ page }) => {
  let release;
  const pending = new Promise(resolve => { release = resolve; });
  await page.route('**/api/cases/adoption-familienrechtliche-erklaerungen', async route => {
    await pending;
    await route.continue();
  });
  await page.goto('/');
  await expect(page.locator('#start-branch')).toBeDisabled();
  release();
  await expect(page.locator('#case-title')).toHaveText('Adoption / familienrechtliche Erklärungen');
  await expect(page.locator('#start-branch')).toBeEnabled();
});

test('edit, review preview, save and submit through the browser', async ({ page }) => {
  await page.goto('/?case=immobilienkaufvertrag');
  await expect(page.locator('#case-title')).toHaveText('Immobilienkaufvertrag');
  await page.locator('#start-branch').click();
  await expect(page.locator('#notice')).toContainText('Änderung begonnen');
  await expect(page.locator('#branch')).toHaveText('Mein Entwurf');
  await page.locator('[data-view-button="bausteine"]').click();
  await page.locator('#node-list button').first().click();
  await page.locator('#edit-node').click();

  const label = page.locator('#node-form label').filter({ hasText: /^Bezeichnung$/ }).locator('input');
  const original = await label.inputValue();
  await label.fill(`${original} (lokale Browserprüfung)`);
  await expect(page.locator('#save')).toBeVisible();
  await page.locator('#save').click();
  await expect(page.locator('#change-preview')).toBeVisible();
  await expect(page.locator('#preview-list')).toContainText('Bezeichnung');
  await page.locator('#confirm-save').click();
  await expect(page.locator('#change-preview')).not.toBeVisible();
  await expect(page.locator('#notice')).toContainText('Fallvorlage gespeichert');

  await page.locator('[data-view-button="pruefung"]').click();
  await page.locator('#change-reason').fill('Lokale Browserprüfung des vollständigen Einreichungswegs.');
  await page.locator('#change-source').fill('Testfixture, aktueller Repository-Stand');
  await page.locator('#submit-review').click();
  await expect(page.locator('#notice')).toContainText('Pull Request eingereicht');
  await expect(page.locator('#review-link')).toHaveAttribute('href', 'https://github.com/notariat8/ontology/pull/123456');
  await expect(page.locator('#branch')).toHaveText('Lesemodus');
});
