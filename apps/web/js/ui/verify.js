// Verify view: a receipt id in, its hash, serial range and anchor state out. Works without a key and without an account.
// In local mode it checks this device's records. In solana-devnet mode it asks the API and shows the chain state.
import { CONFIG } from '../config.js';
import { ledger } from '../core/ledger.js';
import { $, esc, mass } from './dom.js';
import { SIM_TAG } from './retire.js';
import { verifyProof } from '../core/merkle.js';
import { brandMark } from './hud.js';
import { tonneText } from '../core/serials.js';

const anchorWords = (status, cluster) => {
  const where = cluster === 'dry-run' ? 'the dry-run chain (nothing was sent to Solana)' : `Solana ${cluster || 'devnet'}, a test network`;
  return { anchored: `Confirmed on ${where}.`, pending: `Submitted to ${where}, not yet confirmed.`,
    failed: 'The anchor failed after retries. The receipt exists and is marked failed. Nothing claims it is on-chain.' }[status] || status;
};

export function mountVerify(root) {
  root.innerHTML = `
    <section class="panel">
      <div class="verify-head">${brandMark(44)}<div><p class="eyebrow">Show your working</p><h1 class="h1">Verify a receipt</h1></div></div>
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
      <p class="note">Checks that every receipt still commits to the one before it. An edit, a deletion or a swap names the first bad index. Refused attempts are in the chain with equal weight.</p>
      <div class="row wrap"><button class="btn ghost" id="verify-all" type="button">Check the receipt chain</button>
      <a class="btn ghost" id="verify-export" href="${esc(CONFIG.api.baseUrl)}/v1/audit/receipts.json" download="carbonledger-receipts.json">Download receipts.json</a></div>
      <p class="note">The file is the KYA receipt format: check it with <span class="mono">python -m knowyouragenticai_receipts verify carbonledger-receipts.json</span> or drop it on the verifier page, with nothing installed and nothing uploaded.</p>
      <div id="verify-all-out" class="result" aria-live="polite"></div>
    </section>`;
  $('#verify-form', root).addEventListener('submit', async (e) => { e.preventDefault(); await lookup($('#verify-id', root).value.trim()); });
  $('#verify-all', root).addEventListener('click', checkAll);
  refreshVerify();
}

// On mount and every time the tab is shown: a ?id= in the URL is looked up, so "Verify it" always shows the new receipt.
export function refreshVerify() {
  const id = new URLSearchParams(location.hash.split('?')[1] || '').get('id');
  const field = $('#verify-id');
  if (id && field && field.value !== id) { field.value = id; lookup(id); }
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
        <div><dt>Outcome</dt><dd data-outcome="${esc(rc.outcome)}">${rc.outcome === 'REFUSED' ? 'Refused. No units were retired.' : 'Accepted.'} Rule: ${esc(rc.rule)}</dd></div>
        <div><dt>${rc.outcome === 'REFUSED' ? 'Attempted' : 'Retired'}</dt><dd>${mass(rc.grams)} CO₂e${rc.clt ? `, ${esc(rc.clt)} CLT` : ''} ${SIM_TAG}</dd></div>
        ${rc.serial_start != null ? `<div><dt>Serial range</dt><dd class="mono">${rc.serial_start} to ${rc.serial_end - 1} in batch ${esc(rc.batch_id)}</dd></div>
        <div><dt>From</dt><dd data-tonne>${esc(tonneText(rc.serial_start, rc.serial_end))} of batch ${esc(rc.batch_id)}. Evidence is kept per tonne, not per gram. None yet: pilot units.</dd></div>` : ''}
        <div><dt>Decided by</dt><dd>${esc(rc.ledger)}, under ${esc(rc.approved_by)}</dd></div>
        <div><dt>Receipt hash</dt><dd class="mono wrap">${esc(entry.hash)}</dd></div>
        <div><dt>Previous hash</dt><dd class="mono wrap">${esc(entry.prev_hash)}</dd></div>
        <div><dt>Chain</dt><dd data-anchor="${esc(a.anchor_status)}">${esc(anchorWords(a.anchor_status, a.cluster))}${a.slot ? ` Slot ${a.slot}.` : ''}
          ${a.explorer_url ? ` <a href="${esc(a.explorer_url)}" target="_blank" rel="noopener">View on the Solana explorer</a>` : ''}</dd></div>
        <div><dt>Proof</dt><dd id="verify-proof" data-proof="">${a.anchor_status === 'anchored' ? 'Checking the Merkle proof in this browser…' : 'No proof until the anchor is confirmed.'}</dd></div>
      </dl>
      <p class="note">What is on-chain: one Merkle root over many receipt hashes, in a memo. What is not: names, places, baskets. ${esc(rc.units)}</p>`;
    if (a.anchor_status === 'anchored') checkProof(id);
  } catch { out.innerHTML = '<p class="note">Could not reach the CarbonLedger API. Nothing was checked.</p>'; }
}

// Fetch the proof path and recompute the root here, with no trust in the API's own "proof_checks" flag.
async function checkProof(id) {
  const el = $('#verify-proof');
  try {
    const p = await (await fetch(`${CONFIG.api.baseUrl}/v1/receipts/${encodeURIComponent(id)}/proof`, { signal: AbortSignal.timeout(CONFIG.api.timeoutMs) })).json();
    if (!p.proof || !p.anchor_root) { el.textContent = 'No proof available.'; el.dataset.proof = 'none'; return; }
    const ok = await verifyProof(p.receipt_hash, p.proof, p.anchor_root);
    el.dataset.proof = ok ? 'ok' : 'bad';
    el.innerHTML = ok
      ? `Checks out: this receipt's hash sits under root <span class="mono">${esc(p.anchor_root.slice(0, 16))}…</span> in anchor ${esc(p.anchor_id)} (${p.proof.length} step${p.proof.length === 1 ? '' : 's'}), recomputed in this browser.`
      : `Does NOT check out: the proof path does not lead to the anchored root. Treat this receipt as unverified.`;
  } catch { el.textContent = 'Could not fetch the proof.'; el.dataset.proof = 'error'; }
}

async function checkAll() {
  const out = $('#verify-all-out');
  if (CONFIG.ledger !== 'solana-devnet') { out.innerHTML = '<p class="note">The whole-ledger check needs the API. This device keeps records only.</p>'; return; }
  try {
    const v = await (await fetch(`${CONFIG.api.baseUrl}/v1/audit/verify`, { signal: AbortSignal.timeout(CONFIG.api.timeoutMs) })).json();
    out.innerHTML = v.intact ? `<p class="ok" data-intact="true">Intact. ${v.count} receipt${v.count === 1 ? '' : 's'} (${v.accepted} accepted, ${v.refused} refused), head hash <span class="mono">${esc(v.head_hash.slice(0, 16))}…</span>. Anchors: ${v.anchors.anchored} confirmed, ${v.anchors.pending} pending, ${v.anchors.failed} failed.</p>`
      : `<p class="bad" data-intact="false">Not intact. The first bad receipt is at index ${v.first_bad_index}.</p>`;
  } catch { out.innerHTML = '<p class="note">Could not reach the CarbonLedger API. Nothing was checked.</p>'; }
}
