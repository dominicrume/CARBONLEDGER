// Shop view: scan or pick products, review the basket, retire pilot units for it.
import { basket } from '../core/basket.js';
import { lookupBarcode, catalogue } from '../core/lookup.js';
import { decodePhoto, startLive } from '../core/scanner.js';
import { TIERS } from '../core/estimate.js';
import { ESTIMATE_GROUPS } from '../data/factors.js';
import { $, esc, mass, toast, sheet } from './dom.js';
import { confirmRetirement, retireButtonLabel } from './retire.js';
import { missionHTML } from './hud.js';
import { countryQueue } from '../core/game.js';
import { world } from '../core/world.js';

let live = null;

export function mountShop(root) {
  root.innerHTML = `
    <section class="panel scan">
      <div id="mission-shop"></div>
      <h1 class="h1">Scan your shopping</h1>
      <p class="lead">Scan a barcode or tap the demo shelf. Every gram retired is a point, and every point moves the Frontline.</p>
      <div class="row wrap">
        <button class="btn primary" id="scan-btn">Scan a barcode</button>
        <input type="file" id="photo" accept="image/*" capture="environment" hidden>
        <button class="btn ghost" id="shelf-btn">Demo shelf</button>
      </div>
      <video id="video" playsinline muted hidden></video>
      <button class="btn ghost small" id="stop-live" hidden>Stop camera</button>
      <form id="code-form" class="row code-row">
        <label for="code" class="sr">Barcode number</label>
        <input id="code" inputmode="numeric" autocomplete="off" placeholder="Or type the barcode number">
        <button class="btn ghost" type="submit">Add</button>
      </form>
    </section>
    <section class="panel">
      <div class="row between"><h2 class="h2">Basket</h2><button class="link" id="clear" hidden>Clear</button></div>
      <ul class="items" id="items"></ul>
      <div id="totals"></div>
    </section>`;

  $('#scan-btn', root).addEventListener('click', startScan);
  $('#photo', root).addEventListener('change', onPhoto);
  $('#stop-live', root).addEventListener('click', stopLive);
  $('#shelf-btn', root).addEventListener('click', openShelf);
  $('#clear', root).addEventListener('click', () => basket.clear());
  $('#code-form', root).addEventListener('submit', (e) => {
    e.preventDefault(); const v = $('#code').value.replace(/\D/g, ''); if (v) { handleCode(v); $('#code').value = ''; }
  });
  basket.onChange(drawBasket);
  drawBasket();
  const mission = () => { const el = $('#mission-shop'); if (el) el.innerHTML = missionHTML(countryQueue(), world.get()); };
  mission(); document.addEventListener('carbonledger:world', mission);
}

async function startScan() {
  const video = $('#video');
  video.hidden = false;
  live = await startLive(video, handleCode);
  if (live) { $('#stop-live').hidden = false; return; }
  video.hidden = true;
  $('#photo').click(); // live camera not allowed here: take a photo instead
}
function stopLive() { live?.stop(); live = null; $('#video').hidden = true; $('#stop-live').hidden = true; }

async function onPhoto(e) {
  const file = e.target.files?.[0]; e.target.value = '';
  if (!file) return;
  toast('Reading barcode…');
  try { handleCode(await decodePhoto(file)); } catch (err) { toast(err.message); }
}

async function handleCode(code) {
  toast(`Looking up ${code}…`);
  const p = await lookupBarcode(code);
  if (p) return addProduct(p);
  chooseCategory(code);
}

function addProduct(p) {
  const est = basket.add(p);
  toast(`Added ${p.name}: ${mass(est.grams)} CO₂e`);
}

function chooseCategory(code) {
  sheet(`
    <h2 class="sheet-title">Product not found</h2>
    <p class="note">Barcode ${esc(code)} is not in the product databases. Pick the closest type and we'll use a cautious estimate.</p>
    <label class="label" for="grp">Type of product</label>
    <select id="grp">${ESTIMATE_GROUPS.map(g => `<option value="${g.id}">${esc(g.label)}</option>`).join('')}</select>
    <label class="label" for="wt">Pack weight in grams (if food)</label>
    <input id="wt" inputmode="numeric" placeholder="e.g. 500">
    <div class="row"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="add-est">Add estimate</button></div>
  `, { onOpen: (root, close) => root.querySelector('#add-est').addEventListener('click', () => {
    const g = ESTIMATE_GROUPS.find(x => x.id === root.querySelector('#grp').value);
    const grams = Number(root.querySelector('#wt').value) || null;
    close(); addProduct({ code, name: `${g.label} (estimate)`, groupId: g.id, grams });
  }) });
}

function openShelf() {
  sheet(`
    <h2 class="sheet-title">Demo shelf</h2>
    <p class="note">Real UK products from Open Food Facts. Tap to add, as if scanned.</p>
    <ul class="shelf">${catalogue().map(p => `<li><button class="shelf-item" data-code="${esc(p.code)}"><span>${esc(p.name)}</span><small>${esc([p.brand, p.quantity].filter(Boolean).join(' · '))}</small></button></li>`).join('')}</ul>
    <div class="row"><button class="btn primary" data-close>Done</button></div>
  `, { onOpen: (root) => root.querySelectorAll('.shelf-item').forEach(b => b.addEventListener('click', () => handleCode(b.dataset.code))) });
}

function drawBasket() {
  const items = basket.items(), list = $('#items'), totals = $('#totals');
  if (!list) return;
  $('#clear').hidden = !items.length;
  list.innerHTML = items.length ? items.map(i => `
    <li class="item">
      <button class="item-main" data-detail="${i.id}">
        <span class="item-name">${esc(i.name)}</span>
        <span class="item-sub">${esc([i.brand, i.quantity].filter(Boolean).join(' · '))}</span>
        <span class="tier t${i.est.tier}">${TIERS[i.est.tier]}</span>
      </button>
      <span class="item-co2">${mass(i.est.grams * i.qty)}</span>
      <span class="stepper"><button data-dec="${i.id}" aria-label="One fewer">−</button><span>${i.qty}</span><button data-inc="${i.id}" aria-label="One more">+</button></span>
    </li>`).join('') : `<li class="empty">Your basket is empty. Scan a barcode, type one in, or open the demo shelf.</li>`;
  list.querySelectorAll('[data-inc]').forEach(b => b.onclick = () => { const i = items.find(x => x.id === b.dataset.inc); basket.setQty(i.id, i.qty + 1); });
  list.querySelectorAll('[data-dec]').forEach(b => b.onclick = () => { const i = items.find(x => x.id === b.dataset.dec); basket.setQty(i.id, i.qty - 1); });
  list.querySelectorAll('[data-detail]').forEach(b => b.onclick = () => showDetail(items.find(x => x.id === b.dataset.detail)));

  const total = basket.totalGrams();
  const count = items.reduce((s, i) => s + i.qty, 0);
  totals.innerHTML = items.length ? `
    <div class="total-row"><span>${count} item${count === 1 ? '' : 's'}</span><strong>${mass(total)} CO₂e</strong></div>
    <button class="btn primary block" id="retire-basket">${retireButtonLabel(total)}</button>` : '';
  $('#retire-basket')?.addEventListener('click', () => confirmRetirement({
    grams: total, kind: 'shop', label: 'Shopping basket', itemCount: count, codes: items.map(i => i.code).filter(Boolean),
    lines: items.map(i => ({ name: `${i.qty} × ${i.name}`, grams: i.est.grams * i.qty })),
    items: items.map(i => ({ type: 'product', code: i.code || null, groupId: i.groupId || null, packGrams: i.packGrams ?? null, qty: i.qty })),
  }, () => basket.clear()));
}

function showDetail(i) {
  sheet(`
    <h2 class="sheet-title">${esc(i.name)}</h2>
    <dl class="kv">
      <div><dt>Footprint</dt><dd>${mass(i.est.grams)} CO₂e each</dd></div>
      <div><dt>Source</dt><dd>${TIERS[i.est.tier]}: ${esc(i.est.source)}</dd></div>
      <div><dt>Basis</dt><dd>${esc(i.est.detail)}</dd></div>
      ${i.code ? `<div><dt>Barcode</dt><dd class="mono">${esc(i.code)}</dd></div>` : ''}
    </dl>
    <p class="note">Figures are estimates. Where two sources disagree, CarbonLedger uses the higher.</p>
    <div class="row"><button class="btn primary" data-close>Close</button></div>`);
}
