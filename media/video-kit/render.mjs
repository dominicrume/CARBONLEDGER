// node render.mjs stills <dir> [t,t,...]  |  node render.mjs frames <dir> <fps> <part> <parts>
// Needs Playwright: set PLAYWRIGHT to its index.mjs (in this repo: apps/web/node_modules/playwright/index.mjs).
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');
const [mode, out, a3, a4, a5] = process.argv.slice(2), PORT = process.env.PORT || 8822;
const b = await chromium.launch(), page = await b.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
await page.goto(`http://127.0.0.1:${PORT}/stage.html`);
const S = await page.evaluate(() => window.load()); await page.waitForTimeout(800);
if (mode === 'stills') {
  const ts = a3 ? a3.split(',').map(Number) : S.beats.map(x => x.speak + Math.min(x.voice_s * .75, x.voice_s - .5));
  for (const t of ts) { await page.evaluate(t => window.render(t), t); await page.screenshot({ path: `${out}/s${t.toFixed(1).padStart(6, '0')}.jpg`, type: 'jpeg', quality: 80 }); }
  console.log('total', S.total.toFixed(1), 's');
} else {
  const fps = +a3, part = +a4, parts = +a5, n = Math.ceil(S.total * fps), per = Math.ceil(n / parts), lo = part * per, hi = Math.min(n, lo + per);
  for (let i = lo; i < hi; i++) { await page.evaluate(t => window.render(t), i / fps); await page.screenshot({ path: `${out}/f${String(i).padStart(6, '0')}.jpg`, type: 'jpeg', quality: 92 }); }
  console.log(`part ${part}: frames ${lo}..${hi - 1} of ${n}`);
}
await b.close();
