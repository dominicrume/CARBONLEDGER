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
  await expect(page.locator('.sheet-body')).toContainText('Pilot units');
  await page.click('#confirm-retire');
  const receipt = page.locator('.receipt');
  await expect(receipt).toContainText('Retirement receipt');
  await expect(receipt).toContainText('Pilot units, not yet verified credits');
  await expect(receipt.locator('[data-tonne]')).toContainText(/pilot tonne \d+, ([\d.]+%|under 0\.01%) of it|pilot tonnes \d+/);   // evidence is per tonne
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
  // the list shows receipt numbers, not what was bought, and one tap verifies any of them
  const row = page.locator('#history li').first();
  await expect(row).not.toContainText('Shopping basket');
  const id = (await row.locator('[data-rec]').getAttribute('data-rec'));
  expect(id).toMatch(/^CL-[0-9A-F]{12}$/);
  await expect(row).toContainText(id);
  await row.locator('[data-verify]').click();
  await expect(page.locator('#verify-id')).toHaveValue(id);
  await expect(page.locator('#verify-out [data-tonne]')).toContainText(/pilot tonne \d+ \(grams [\d,]+ to [\d,]+ of it, /);
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

// ---- regressions from the QA sweep of 2026-10-12 ----
test('Back returns to the previous tab, and a reloaded verify link opens Verify with its id', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.click('[data-tab="travel"]'); await page.click('[data-tab="daily"]');
  await page.goBack();
  await expect(page.locator('#view-travel')).toBeVisible();
  await page.goBack();
  await expect(page.locator('#view-shop')).toBeVisible();
  await page.click('[data-tab="travel"]');
  await page.click('#retire-trip'); await page.click('#confirm-retire');
  const id1 = (await page.locator('.receipt .r-meta').innerText()).split('\n')[0].trim();
  await page.click('#receipt-verify');
  await expect(page.locator('#verify-id')).toHaveValue(id1);
  await page.click('[data-tab="daily"]'); await page.click('#retire-daily'); await page.click('#confirm-retire');
  const id2 = (await page.locator('.receipt .r-meta').innerText()).split('\n')[0].trim();
  await page.click('#receipt-verify');
  await expect(page.locator('#verify-id')).toHaveValue(id2);            // the second "Verify it" shows the second receipt
  await expect(page.locator('#verify-out [data-anchor]')).toContainText('dry-run chain');   // honest about where it was recorded
  await page.reload();
  await expect(page.locator('#view-verify')).toBeVisible();
  await expect(page.locator('#verify-id')).toHaveValue(id2);
});

test('a long display name wraps and never pushes the tab bar off screen; Escape closes a sheet', async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#me`);
  await page.fill('#name', 'X'.repeat(24)); await page.click('#name-save');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(430);
  await page.click('[data-tab="shop"]');
  await page.click('#shelf-btn'); await expect(page.locator('.shelf')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.shelf')).toHaveCount(0);
});

test('feedback where there was none: letters-only barcode, send-here, an impossible distance', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.fill('#code', 'abc'); await page.click('#code-form button[type=submit]');
  await expect(page.locator('#toast')).toContainText('Type the digits');
  await page.click('[data-tab="travel"]'); await page.click('[data-mode="ground"]');
  await page.fill('#gkm', '99999999');
  await expect(page.locator('#travel-result')).toContainText('up to 20,000 km');
  await expect(page.locator('#retire-trip')).toHaveCount(0);
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#countries?pick=NOR`);
  await page.click('#send-here');
  await expect(page.locator('#toast')).toContainText('Norway');
});
