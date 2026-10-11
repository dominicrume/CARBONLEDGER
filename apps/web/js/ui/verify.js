// Verify view: a receipt id in, its hash, serial range and anchor state out. Works without a key and without an account.
// In local mode it checks this device's records. In solana-devnet mode it asks the API and shows the chain state.
import { CONFIG } from '../config.js';
import { ledger } from '../core/ledger.js';
import { $, esc, mass } from './dom.js';
import { SIM_TAG } from './retire.js';

const ANCHOR_WORDS = {
  anchored: 'Confirmed on Solana devnet, a test network.',
  pending: 'Submitted to Solana devnet, not yet confirmed.',
  failed: 'The anchor failed after retries. The receipt exists and is marked failed. Nothing claims it is on-chain.',
};

export function mountVerify(root) {
  root.innerHTML = `
    <section class="panel">
      <p class="eyebrow">Show your working</p>
      <h1 class="h1">Verify a receipt</h1>
      <p class="lead">Paste a receipt id. You will see its hash, its serial range and whether the chain confirmed it. ${SIM_TAG}</p>
      <form id="verify-form" class="row code-row">
        <label for="verify-id" class="sr">Receipt id</label>
        <input id="verify-id" autocomplete="off" placeholder="CL-..." spellcheck="false">
        <button class="btn primary" type="submit">Verify</button>
      </form>
      <div id="verify-out" class="result" aria-live="polite"></div>
    </section>
    <section class="panel">
      <h2 class="h2">Whole ledger</h2>
      <p class="note">Checks that every receipt still commits to the one before it. An edit, a deletion or a swap names the first bad index.</p>
      <button class="btn ghost" id="verify-all" type="button">Check the receipt chain</button>
      <div id="verify-all-out" class="result" aria-live="polite"></div>
    </section>`;
  $('#verify-form', root).addEventListener('submit', async (e) => { e.preventDefault(); await lookup($('#verify-id', root).value.trim()); });
  $('#verify-all', root).addEventListener('click', checkAll);
  const fromHash = new URLSearchParams(location.hash.split('?')[1] || '').get('id');
  if (fromHash) { $('#verify-id', root).value = fromHash; lookup(fromHash); }
}

async function lookup(id) {
  const out = $('#verify-out');
  if (!id) { out.innerHTML = '<p class="muted">Enter a receipt id.</p>'; return; }
  if (CONFIG.ledger !== 'solana-devnet') {
    const rec = ledger.history().find(r => r.id === id);
    out.innerHTML = rec ? `<dl class="kv"><div><dt>Receipt</dt><dd class="mono">${esc(rec.id)}</dd></div><div><dt>Retired</dt><dd>${mass(rec.grams)} CO₂e ${SIM_TAG}</dd></div>
      <div><dt>Recorded</dt><dd>On this device only. Switch to the ledger to verify against the API.</dd></div></dl>` : '<p class="note">No receipt with that id on this device.</p>';
    return;
  }
  out.innerHTML = '<p class="muted">Checking…</p>';
  try {
    const r = await fetch(`${CONFIG.api.baseUrl}/v1/receipts/${encodeURIComponent(id)}`, { signal: AbortSignal.timeout(CONFIG.api.timeoutMs) });
    if (r.status === 404) { out.innerHTML = '<p class="note">The ledger has no receipt with that id.</p>'; return; }
    const { entry, chain } = await r.json();
    const rc = entry.receipt, a = chain || { anchor_status: 'pending' };
    out.innerHTML = `
      <dl class="kv">
        <div><dt>Receipt</dt><dd class="mono">${esc(rc.receipt_id)}</dd></div>
        <div><dt>Retired</dt><dd>${mass(rc.grams)} CO₂e, ${esc(rc.clt)} CLT ${SIM_TAG}</dd></div>
        <div><dt>Serial range</dt><dd class="mono">${rc.serial_start} to ${rc.serial_end} in batch ${esc(rc.batch_id)}</dd></div>
        <div><dt>Receipt hash</dt><dd class="mono wrap">${esc(entry.hash)}</dd></div>
        <div><dt>Previous hash</dt><dd class="mono wrap">${esc(entry.prev_hash)}</dd></div>
        <div><dt>Chain</dt><dd data-anchor="${esc(a.anchor_status)}">${esc(ANCHOR_WORDS[a.anchor_status] || a.anchor_status)}${a.slot != null ? ` Slot ${a.slot}.` : ''}
          ${a.explorer_url ? ` <a href="${esc(a.explorer_url)}" target="_blank" rel="noopener">View on the Solana explorer</a>` : ''}</dd></div>
      </dl>
      <p class="note">What is on-chain: this receipt id and its hash. What is not: names, places, baskets. ${esc(rc.units)}</p>`;
  } catch { out.innerHTML = '<p class="note">Could not reach the CarbonLedger API. Nothing was checked.</p>'; }
}

async function checkAll() {
  const out = $('#verify-all-out');
  if (CONFIG.ledger !== 'solana-devnet') { out.innerHTML = '<p class="note">The whole-ledger check needs the API. This device keeps records only.</p>'; return; }
  try {
    const v = await (await fetch(`${CONFIG.api.baseUrl}/v1/audit/verify`, { signal: AbortSignal.timeout(CONFIG.api.timeoutMs) })).json();
    out.innerHTML = v.intact ? `<p class="ok" data-intact="true">Intact. ${v.count} receipt${v.count === 1 ? '' : 's'}, head hash <span class="mono">${esc(v.head_hash.slice(0, 16))}…</span>. Anchors: ${v.anchors.anchored} confirmed, ${v.anchors.pending} pending, ${v.anchors.failed} failed.</p>`
      : `<p class="bad" data-intact="false">Not intact. The first bad receipt is at index ${v.first_bad_index}.</p>`;
  } catch { out.innerHTML = '<p class="note">Could not reach the CarbonLedger API. Nothing was checked.</p>'; }
}
