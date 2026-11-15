const { chromium } = await import('/Users/dominicorumeuririe/Downloads/CARBON LEDGER/apps/web/node_modules/playwright/index.mjs');
const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
await p.goto('http://127.0.0.1:8872/brand/posts/answer-record.html'); await p.evaluate(() => window.ready()); await p.waitForTimeout(500);
await p.locator('#p1').screenshot({ path: 'media/brand/posts/out/answer-record-reminder.png' });
await p.locator('#p3').screenshot({ path: 'media/brand/posts/out/answer-record-thumbnail.png' });
await b.close(); console.log('ok');
