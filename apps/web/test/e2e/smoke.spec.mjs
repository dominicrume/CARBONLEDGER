// Browser smoke test (D13). Runs against the real API in dry-run mode, served by scripts/e2e.sh.
// Proves in a browser what tests/test_api.py proves in Python: retire, receipt, verify intact, honest failure.
import { test, expect } from '@playwright/test';

const APP = process.env.APP_URL || 'http://127.0.0.1:8080';
const API = process.env.API_URL || 'http://127.0.0.1:8000';
const KEY = process.env.E2E_API_KEY || '';

// The key is a login. The test puts it where Settings would: this browser's storage.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(k => { try { localStorage.setItem('carbonledger.apiKey', JSON.stringify(k)); } catch {} }, KEY);
});

test('retire pilot units from the demo shelf, see the receipt, verify the chain', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await expect(page.locator('#conn')).toHaveText(/Connected to the ledger/);
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await expect(page.locator('#items .item')).toHaveCount(1);
  await page.click('#retire-basket');
  await expect(page.locator('.sheet-title')).toHaveText('Confirm retirement');
  await expect(page.locator('.sheet-body')).toContainText('Simulated pilot units');
  await page.click('#confirm-retire');
  const receipt = page.locator('.receipt');
  await expect(receipt).toContainText('Retirement receipt');
  await expect(receipt).toContainText('Simulated pilot units, not verified credits');
  const id = (await receipt.locator('.r-meta').innerText()).split('\n')[0].trim();
  expect(id).toMatch(/^CL-[0-9A-F]{12}$/);
  await page.click('.sheet-body button[data-close]');
  // the verify screen
  await page.click('[data-tab="verify"]');
  await page.fill('#verify-id', id);
  await page.click('#verify-form button[type=submit]');
  await expect(page.locator('#verify-out')).toContainText(id);
  await expect(page.locator('#verify-out [data-anchor]')).toHaveAttribute('data-anchor', 'anchored');
  await expect(page.locator('#verify-proof')).toHaveAttribute('data-proof', 'ok');
  await expect(page.locator('#verify-proof')).toContainText('recomputed in this browser');
  await page.click('#verify-all');
  await expect(page.locator('#verify-all-out [data-intact]')).toHaveAttribute('data-intact', 'true');
  // the API agrees
  const v = await (await page.request.get(`${API}/v1/audit/verify`)).json();
  expect(v.intact).toBe(true);
  expect(v.count).toBeGreaterThanOrEqual(1);
});

test('history is mirrored from the ledger and a browser edit is never a score', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toBeVisible();
  await page.click('.sheet-body button[data-close]');
  // forge a huge local record, then reload: the mirror drops it
  await page.evaluate(() => { const k = 'carbonledger.ledger'; const l = JSON.parse(localStorage.getItem(k) || '[]'); l.unshift({ id: 'CL-FORGED', ts: new Date().toISOString(), grams: 9e12, kind: 'shop', label: 'Shopping basket', account: 'personal' }); localStorage.setItem(k, JSON.stringify(l)); });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#me`);
  await page.reload();     // a hash change alone is not a reload; the mirror runs at load
  await expect(page.locator('#me-level')).toContainText('totals from the ledger');
  await expect.poll(async () => page.evaluate(() => JSON.parse(localStorage.getItem('carbonledger.ledger') || '[]').some(r => r.id === 'CL-FORGED'))).toBe(false);
  await expect(page.locator('#history')).not.toContainText('CL-FORGED');
  await expect(page.locator('#history li').first()).toContainText('Shopping basket');
});

test('no banned claim words on any screen', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  for (const tab of ['shop', 'travel', 'daily', 'countries', 'me', 'business', 'verify']) {
    await page.click(`[data-tab="${tab}"]`);
    const text = await page.locator('main').innerText();
    expect(text, tab).not.toMatch(/\boffsets?\b|carbon[ -]neutral|net[ -]zero|verified credits?(?! until)/i);
  }
});

test('without a key the ledger refuses and says nothing was recorded', async ({ page }) => {
  await page.addInitScript(() => { try { localStorage.removeItem('carbonledger.apiKey'); } catch {} });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await page.click('#confirm-retire');
  await expect(page.locator('#retire-error')).toContainText('NO_KEY');
  await expect(page.locator('#retire-error')).toContainText('Nothing was recorded');
});

test('when the API is down the app says so and records nothing', async ({ page }) => {
  await page.route(`${API}/**`, route => route.abort('connectionrefused'));
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await expect(page.locator('#conn')).toHaveText(/not reachable/);
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await page.click('#confirm-retire');
  await expect(page.locator('#retire-error')).toContainText('Nothing was recorded');
  await expect(page.locator('.receipt')).toHaveCount(0);
});
