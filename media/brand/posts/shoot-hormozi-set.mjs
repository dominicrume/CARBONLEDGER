const { chromium } = await import('/Users/dominicorumeuririe/Downloads/CARBON LEDGER/apps/web/node_modules/playwright/index.mjs');
const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1080 } });
await p.goto('http://127.0.0.1:8872/brand/posts/hormozi-set.html'); await p.evaluate(() => window.ready()); await p.waitForTimeout(500);
const names = { p1: 'kya-1-homework', p2: 'kya-2-logs-everything', p3: 'kya-3-ask-your-agent', p4: 'kya-4-poster' };
for (const [id, n] of Object.entries(names)) await p.locator('#' + id).screenshot({ path: `media/brand/posts/out/${n}.png` });
await b.close(); console.log('ok');
