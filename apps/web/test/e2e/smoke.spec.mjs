// Browser smoke test (D13). Runs against the real API in dry-run mode, served by scripts/e2e.sh.
// Proves in a browser what tests/test_api.py proves in Python: retire, receipt, verify intact, honest failure.
import { test, expect } from '@playwright/test';

const APP = process.env.APP_URL || 'http://127.0.0.1:8080';
const API = process.env.API_URL || 'http://127.0.0.1:8000';
const KEY = process.env.E2E_API_KEY || '';
const BUSINESS_KEY = process.env.E2E_BUSINESS_KEY || '';

// The key is a login. The test puts it where Settings would: this browser's storage.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(k => { try { localStorage.setItem('carbonledger.apiKey', JSON.stringify(k)); localStorage.setItem('carbonledger.onboarded', 'true'); } catch {} }, KEY);
});

test('retire pilot units from the demo shelf, see the receipt, verify the chain', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await expect(page.locator('#conn')).toHaveText(/Ledger: /);
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

test('without a login the demo makes one for you and the retirement goes through', async ({ page }) => {
  await page.addInitScript(() => { try { localStorage.removeItem('carbonledger.apiKey'); } catch {} });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await expect(page.locator('#conn')).toContainText('Ledger: ');
  await expect(page.locator('#conn')).not.toContainText('no login', { timeout: 10000 });
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toContainText('Retirement receipt');
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('carbonledger.apiKey') || '""'))).toMatch(/^clk_personal_/);
});

test('a revoked login is replaced on the spot, never a wall', async ({ page }) => {
  await page.addInitScript(() => { try { localStorage.setItem('carbonledger.apiKey', JSON.stringify('clk_personal_' + 'f'.repeat(48))); } catch {} });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.click('#shelf-btn');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toContainText('Retirement receipt');
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

test('a business sets a mandate for an agent key, sees use against cap, and revokes it', async ({ page }) => {
  await page.addInitScript(k => { try { localStorage.setItem('carbonledger.apiKey', JSON.stringify(k)); } catch {} }, BUSINESS_KEY);
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#business`);
  await page.reload();
  await page.fill('#m-agent', '11111111111111111111111111111111');          // a valid 32-byte base58 key (the system program id)
  await page.fill('#m-cap', '2');
  await page.fill('#m-days', '7');
  await page.fill('#m-projects', 'demo-pilot-1');
  await page.click('#mandate-create');
  const row = page.locator('#mandate-list .mandate').first();
  await expect(row).toContainText('0 g used of 2 kg');
  await expect(row).toContainText('demo-pilot-1');
  await expect(page.locator('#mandate-error')).toHaveText('');
  await row.locator('[data-revoke]').click();
  await expect(page.locator('#mandate-list .mandate').first()).toContainText('revoked');
  await expect(page.locator('#mandate-list [data-revoke]')).toHaveCount(0);
  // a name instead of a key is refused in plain words, and nothing is recorded
  await page.fill('#m-agent', 'agent-1-is-not-a-key-but-long-enough');
  await page.click('#mandate-create');
  await expect(page.locator('#mandate-error')).toContainText(/public key/);
});

test('on the demo, one login writes a mandate too (off the demo a personal key is refused: tests/test_api.py)', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#business`);
  await page.reload();
  await page.fill('#m-agent', '11111111111111111111111111111111');
  await page.click('#mandate-create');
  await expect(page.locator('#mandate-list .mandate').first()).toContainText('used of');
  await expect(page.locator('#mandate-error')).toHaveText('');
});

test('first visit shows the three-step welcome once, and its button opens the demo shelf', async ({ page }) => {
  await page.addInitScript(() => { try { localStorage.removeItem('carbonledger.onboarded'); } catch {} });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#me`);
  await expect(page.locator('.onboard h2')).toContainText('Every gram you retire moves the world');
  await page.click('#onboard-go');
  await expect(page.locator('.shelf')).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('carbonledger.onboarded'))).toBe('true');
});

test('travel offers a retire button for a flight and for a train, and both retire', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#travel`);
  await expect(page.locator('#retire-trip')).toContainText('XP');
  await page.click('#retire-trip'); await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toContainText('Retirement receipt');
  await page.click('.sheet-body button.primary[data-close]');
  await page.click('[data-mode="ground"]');
  await page.selectOption('#gmode', 'rail');
  await expect(page.locator('#retire-trip')).toBeVisible();
  await page.click('#retire-trip'); await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toContainText('Retirement receipt');
});

test('business retires with the same demo login, and the display name saves with a button', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#business`);
  await page.click('#retire-biz'); await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toContainText('Retirement receipt');
  await page.click('.sheet-body button.primary[data-close]');
  await page.click('[data-tab="me"]');
  await page.fill('#name', 'Ada Okafor');
  await page.click('#name-save');
  await expect(page.locator('#toast')).toContainText('Saved. You are Ada Okafor.');
  await expect(page.locator('#me-level .hero-title')).toContainText('Ada Okafor');
  await expect(page.locator('#today')).toContainText('of 3');
});
