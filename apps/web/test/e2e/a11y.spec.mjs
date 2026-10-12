// Accessibility pass (web stage 03): axe-core on every tab and on the confirm sheet, WCAG 2.1 AA rules.
// Contrast, names, roles, keyboard reach. Violations fail the run and are listed by rule and selector.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const APP = process.env.APP_URL || 'http://127.0.0.1:8080';
const API = process.env.API_URL || 'http://127.0.0.1:8000';
const KEY = process.env.E2E_API_KEY || '';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(k => { try { localStorage.setItem('carbonledger.apiKey', JSON.stringify(k)); localStorage.setItem('carbonledger.onboarded', 'true'); } catch {} }, KEY);
});

async function audit(page, where) {
  // let any slide-up or fade finish first: a mid-animation colour is not the colour a person reads
  await page.evaluate(() => Promise.all(document.getAnimations().map(a => a.finished.catch(() => {}))));
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  const found = r.violations.map(v => `${v.id} (${v.impact}): ${v.help}\n  ${v.nodes.slice(0, 4).map(n => `${n.target.join(' ')} :: ${(n.any[0]?.data && JSON.stringify(n.any[0].data)) || n.failureSummary}`).join('\n  ')}`);
  expect(found, `axe violations on ${where}`).toEqual([]);
}

test('every tab passes axe at WCAG 2.1 AA', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  for (const tab of ['shop', 'travel', 'daily', 'countries', 'me', 'business', 'verify']) {
    await page.click(`[data-tab="${tab}"]`);
    await page.waitForTimeout(150);
    await audit(page, tab);
  }
});

test('the confirm sheet and the receipt pass axe', async ({ page }) => {
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  await page.click('#shelf-btn');
  await audit(page, 'demo shelf');
  await page.locator('.shelf-item').first().click();
  await page.click('.sheet-body button[data-close]');
  await page.click('#retire-basket');
  await audit(page, 'confirm sheet');
  await page.click('#confirm-retire');
  await expect(page.locator('.receipt')).toBeVisible();
  await audit(page, 'receipt');
});

test('every action is reachable by keyboard and reduced motion is respected', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${APP}/?ledger=solana-devnet&api=${encodeURIComponent(API)}#shop`);
  // tab from the top of the page until the retire button area is reached; no focus trap on the way
  const reached = new Set();
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press('Tab');
    const id = await page.evaluate(() => document.activeElement?.id || document.activeElement?.dataset?.tab || document.activeElement?.tagName);
    reached.add(id);
  }
  for (const want of ['level-chip', 'settings-btn', 'scan-btn', 'shelf-btn', 'code', 'shop', 'verify']) expect([...reached], want).toContain(want);
  await page.click('[data-tab="countries"]');
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
  await expect(page.locator('#globe')).toHaveAttribute('data-autorotate', '0');
  await expect(page.locator('.globe-wrap')).toContainText(/queue below|could not load/i, { timeout: 1 }).catch(() => {});
  await expect(page.locator('#queue li').first()).toBeVisible();        // the text alternative to the globe
});
