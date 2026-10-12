// Landing page behaviour. Same origin as the API, so the live figures come from /v1/audit/verify with no CORS.
// Old links into the app (/#verify?id=..., /#shop) predate the landing page: send them on to /app with the hash intact.
const APP_TABS = /^#(shop|travel|daily|countries|me|business|verify|settings)\b/;
if (APP_TABS.test(location.hash)) location.replace(`/app${location.search}${location.hash}`);

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s) => document.querySelector(s);
const n = (v) => v.toLocaleString('en-GB');

// Hero: grams of carbon drifting down onto ledger lines and settling. Still frame when motion is reduced.
function field() {
  const c = $('#field'); if (!c) return;
  const ctx = c.getContext('2d'); let W = 0, H = 0, parts = [], lines = [];
  const spawn = (any) => ({ x: Math.random() * W, y: any ? Math.random() * H : -10, v: .15 + Math.random() * .45, r: .6 + Math.random() * 1.6, a: .25 + Math.random() * .6, s: Math.random() * 6.28 });
  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2); W = c.clientWidth; H = c.clientHeight;
    c.width = W * dpr; c.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    lines = []; for (let y = 48; y < H; y += 48) lines.push(y);
    parts = Array.from({ length: Math.round(Math.min(160, W * H / 9000)) }, () => spawn(true));
  }
  function draw(t) {
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(61,220,151,0.07)'; ctx.lineWidth = 1;
    for (const y of lines) { ctx.beginPath(); ctx.moveTo(0, y + .5); ctx.lineTo(W, y + .5); ctx.stroke(); }
    parts.forEach((p, j) => {
      if (!reduce) { p.y += p.v; p.x += Math.sin(t / 1600 + p.s) * .18; if (p.y > H + 10) { parts[j] = spawn(false); return; } }
      const near = 1 - Math.min(1, Math.abs(((p.y % 48) + 48) % 48 - 47) / 6);
      ctx.fillStyle = `rgba(61,220,151,${(p.a * (.55 + near * .45)).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r + near * .8, 0, 6.283); ctx.fill();
    });
    if (!reduce) requestAnimationFrame(draw);
  }
  size(); addEventListener('resize', () => { size(); if (reduce) draw(0); });
  reduce ? draw(0) : requestAnimationFrame(draw);
}

// Cost: a log slider from 1 g to 1 t at the demo price of £100 a tonne. Integers only: £100/t is 1p per 100 g,
// rounded up to the next penny, the way the app rounds (never under a penny).
const PENCE_PER_TONNE = 10000;
function calc() {
  const r = $('#grams'); if (!r) return;
  const grams = (v) => Math.max(1, Math.round(10 ** (v / 100 * 6)));
  const slider = (g) => Math.round(Math.log10(Math.max(1, g)) / 6 * 100);
  const mass = (g) => g >= 1e6 ? `${n(Math.round(g / 1e4) / 100)} t` : g >= 1000 ? `${n(Math.round(g / 100) / 10)} kg` : `${n(g)} g`;
  const price = (g) => { const p = Math.max(1, Math.ceil(g * PENCE_PER_TONNE / 1e6)); return `£${Math.floor(p / 100)}.${String(p % 100).padStart(2, '0')}`; };
  const clt = (g) => `${Math.floor(g / 1e6)}.${String(g % 1e6).padStart(6, '0')} CLT`;
  function show(g) {
    $('#out-mass').textContent = mass(g); $('#out-price').textContent = price(g); $('#out-clt').textContent = clt(g);
    document.querySelectorAll('.presets button').forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.g === g)));
  }
  r.addEventListener('input', () => show(grams(+r.value)));
  document.querySelectorAll('.presets button').forEach(b => b.addEventListener('click', () => { const g = +b.dataset.g; r.value = slider(g); show(g); }));
  r.value = slider(2500); show(2500);
}

function copy() {
  document.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', async () => {
    const txt = document.getElementById(b.dataset.copy).textContent.trim(), was = b.textContent;
    try { await navigator.clipboard.writeText(txt); b.textContent = 'Copied'; } catch { b.textContent = 'Select and copy'; }
    setTimeout(() => { b.textContent = was; }, 1400);
  }));
}

// Live figures from the public audit endpoint. If it cannot be reached, the dated snapshot stays and says so.
async function live() {
  try {
    const r = await fetch('/v1/audit/verify', { signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json(), a = d.anchors || {};
    $('#s-receipts').textContent = n(d.count); $('#s-accepted').textContent = n(d.accepted); $('#s-refused').textContent = n(d.refused);
    $('#s-anchored').innerHTML = `${n(a.anchored ?? 0)}<small>/${n(d.count)}</small>`; $('#s-failed').textContent = n(a.failed ?? 0);
    const st = $('#live-state'); st.textContent = `Live · checked ${new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`; st.classList.add('on');
    $('#live-note').textContent = d.intact
      ? `Receipt chain intact, checked just now from the public audit endpoint.${a.pending ? ` ${n(a.pending)} anchor${a.pending === 1 ? '' : 's'} waiting for Solana to confirm.` : ''}`
      : `The receipt chain does not check out at index ${d.first_bad_index}. Shown as it is.`;
  } catch { $('#live-note').textContent = 'Could not reach the audit endpoint just now. These are the figures from the dated snapshot.'; }
}

field(); calc(); copy(); live();
