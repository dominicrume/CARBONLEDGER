// Renders the short frame by frame: node render.mjs stills <outdir>   or   node render.mjs frames <outdir> [fps]
import { chromium } from '../../apps/web/node_modules/playwright/index.mjs';
const [mode, out, fpsArg] = process.argv.slice(2);
const fps = +(fpsArg || 30), PORT = process.env.PORT || 8811;
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(`http://127.0.0.1:${PORT}/index.html`);
const S = await page.evaluate(() => window.load());
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
if (mode === 'stills') {
  for (const sc of S.scenes) for (const f of [0.55, 0.97]) {
    const t = sc.start + sc.dur * f;
    await page.evaluate(t => window.render(t), t);
    await page.screenshot({ path: `${out}/${sc.id}-${Math.round(f * 100)}.png` });
  }
  console.log('total seconds', S.total.toFixed(2));
} else {
  const n = Math.ceil(S.total * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    await page.screenshot({ path: `${out}/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  console.log('frames', n, 'seconds', S.total.toFixed(2));
}
await b.close();
