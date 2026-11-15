const { chromium } = await import('/Users/dominicorumeuririe/Downloads/CARBON LEDGER/apps/web/node_modules/playwright/index.mjs');
const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
await p.goto('http://127.0.0.1:8872/brand/posts/posts.html'); await p.evaluate(() => window.ready()); await p.waitForTimeout(400);
for (const id of ['p1', 'p2', 'p3']) await p.locator('#' + id).screenshot({ path: `media/brand/posts/out/${id}.png` });
await b.close(); console.log('ok');
