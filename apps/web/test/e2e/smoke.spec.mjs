// Browser smoke test (D13). Runs against the real API in dry-run mode, served by scripts/e2e.sh.
// Proves in a browser what tests/test_api.py proves in Python: retire, receipt, verify intact, honest failure.
import { test, expect } from '@playwright/test';

const APP = process.env.APP_URL || 'http://127.0.0.1:8080';
const API = process.env.API_URL || 'http://127.0.0.1:8000';

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
  await page.click('#verify-all');
  await expect(page.locator('#verify-all-out [data-intact]')).toHaveAttribute('data-intact', 'true');
  // the API agrees
  const v = await (await page.request.get(`${API}/v1/audit/verify`)).json();
  expect(v.intact).toBe(true);
  expect(v.count).toBeGreaterThanOrEqual(1);
});

test('no banned claim words on any screen', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  for (const tab of ['shop', 'travel', 'daily', 'countries', 'me', 'business', 'verify']) {
    await page.click(`[data-tab="${tab}"]`);
    const text = await page.locator('main').innerText();
    expect(text, tab).not.toMatch(/\boffsets?\b|carbon[ -]neutral|net[ -]zero|verified credits?(?! until)/i);
  }
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
