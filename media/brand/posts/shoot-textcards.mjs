const { chromium } = await import('/Users/dominicorumeuririe/Downloads/CARBON LEDGER/apps/web/node_modules/playwright/index.mjs');
const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1080 } });
await p.goto('http://127.0.0.1:8872/brand/posts/textcards.html'); await p.evaluate(() => window.ready()); await p.waitForTimeout(500);
await p.locator('#d').screenshot({ path: 'media/brand/posts/out/textcard-dark.png' });
await p.locator('#w').screenshot({ path: 'media/brand/posts/out/textcard-white.png' });
await b.close(); console.log('ok');
