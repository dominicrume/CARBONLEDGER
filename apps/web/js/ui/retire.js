// Shared "retire" action: shows the confirmation, records on the ledger, then shows the receipt.
// Wording follows rules/HARDENING-PRODUCT.md: pilot units are retired, never "offset", and are labelled as pilot units, not yet verified credits.
import { settings } from '../core/settings.js';
import { tonneShort } from '../core/serials.js';
import { track, account, live } from '../core/account.js';
import { store } from '../core/store.js';
import { ledger, gramsToClt, priceGBP, ref, getDemoLogin, apiHeaders } from '../core/ledger.js';
import { CONFIG } from '../config.js';
import { badgeBook, countryQueue } from '../core/game.js';
import { target, resolveTarget } from '../core/target.js';
import { COUNTRIES } from '../data/countries.js';
import { sheet, esc, mass, gbp } from './dom.js';
import { icon, rewardHTML, buzz, xp, countUp, brandMark } from './hud.js';
import { sizeXP, xpOf } from '../core/xp.js';

export const SIM_TAG = '<span class="tag">Pilot units</span>';
export function retireButtonLabel(grams) { return `Retire ${mass(grams)} for ${gbp(priceGBP(grams))} <span class="xp">+${xp(sizeXP(grams))}</span>`; }

// entry: { grams, kind, label, lines: [{name, grams}], ...extra }
const countryOptions = sel => [...COUNTRIES].sort((a, b) => a.name.localeCompare(b.name))
  .map(c => `<option value="${c.iso3}" ${c.iso3 === sel ? 'selected' : ''}>${esc(c.name)}</option>`).join('');

export function confirmRetirement(entry, onDone) {
  track('retire_open');
  const t = target.get(), front = countryQueue().current;
  const idempotencyKey = ref();   // one key for this intent; a retry after a timeout reuses it
  sheet(`
    <h2 class="sheet-title">Confirm retirement</h2>
    <dl class="kv">
      <div><dt>Footprint</dt><dd>${mass(entry.grams)} CO₂e</dd></div>
      <div><dt>CLT units</dt><dd class="mono">${gramsToClt(entry.grams)} CLT ${SIM_TAG}</dd></div>
      <div><dt>Price</dt><dd>${gbp(priceGBP(entry.grams))} <span class="muted">at ${gbp(settings.pricePerTonne())} per tonne</span></dd></div>
      <div><dt>Recorded on</dt><dd>${esc(ledger.info.name)}</dd></div>
    </dl>
    <fieldset class="choice">
      <legend class="label">Which country should this retirement count towards?</legend>
      <label class="opt"><input type="radio" name="tgt" value="frontline" ${t.mode !== 'chosen' ? 'checked' : ''}>
        <span><strong>The Frontline: ${esc(front?.name || '—')}</strong><small>The smallest country still to clear. Earns Frontline skills and badges.</small></span></label>
      <label class="opt"><input type="radio" name="tgt" value="chosen" ${t.mode === 'chosen' ? 'checked' : ''}>
        <span><strong>A country I choose</strong><select id="tgt-country" aria-label="Country">${countryOptions(t.iso3 || 'GBR')}</select></span></label>
    </fieldset>
    <p class="note" id="tgt-note"></p>
    ${payOn() ? '<p class="note">Test mode: you pay with Solana devnet test tokens from a wallet. No real money moves. Pilot units, not yet verified credits.</p><div class="pay-box" id="pay-box" hidden></div>' : '<p class="note">No payment is taken. Pilot units, not yet verified credits.</p>'}
    <p class="note bad" id="retire-error" role="alert"></p>
    <p class="row" id="retire-login" hidden><button class="btn ghost small" type="button" id="get-demo-login">Get a demo login</button><span class="note">A login for simulated units, kept in this browser. Then confirm again.</span></p>
    <div class="row"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirm-retire">${payOn() ? 'Pay and retire (test)' : 'Confirm retirement'}</button></div>
  `, { onOpen: (root, close) => {
    const pick = () => ({ mode: root.querySelector('[name=tgt]:checked').value, iso3: root.querySelector('#tgt-country').value });
    const note = () => {
      const r = resolveTarget(pick(), entry.grams);
      root.querySelector('#tgt-note').textContent = !r ? '' : r.finished ? `This retirement will finish clearing the symbolic share of ${r.name}.`
        : `${r.name} needs ${mass(r.remaining)} more to be cleared.`;
    };
    root.querySelectorAll('[name=tgt]').forEach(i => i.addEventListener('change', note));
    root.querySelector('#tgt-country').addEventListener('change', () => { root.querySelector('[name=tgt][value=chosen]').checked = true; note(); });
    note();
    let payRef = null;
    root.querySelector('#confirm-retire').addEventListener('click', async (e) => {
      e.target.disabled = true;
      if (payOn() && !payRef) {                        // D29: get a paid quote first; then this button retires
        try { payRef = await payFirst(root, entry.grams); } catch (err) { root.querySelector('#retire-error').textContent = err.message; e.target.disabled = false; return; }
      }
      const choice = pick(); target.set(choice);
      const dest = resolveTarget(choice, entry.grams);
      const account = entry.account || 'personal', ctx = { employees: store.get('biz', {}).employees };
      const before = new Set(badgeBook(account, ctx).all.map(b => b.id));
      const xpBefore = xpOf(ledger.history(account)).total;
      const attempt = () => ledger.retire({ ...entry, idempotencyKey, paymentReference: payRef, countryIso3: dest?.iso3, countryName: dest?.name, mode: dest?.mode, finished: !!dest?.finished });
      try {
        let rec;
        try { rec = await attempt(); }
        catch (err) {
          if (!/NO_KEY|BAD_KEY|REVOKED_KEY/.test(err.message)) throw err;
          await getDemoLogin('personal');                 // a demo server: log in and retry once, no wall for the person
          document.dispatchEvent(new CustomEvent('carbonledger:login'));
          rec = await attempt();
        }
        const fresh = badgeBook(account, ctx).all.filter(b => !before.has(b.id));
        const xpAfter = Math.max(xpOf(ledger.history(account)).total, xpBefore + sizeXP(rec.grams));
        buzz();
        close(); showReceipt(rec, fresh, { before: xpBefore, after: xpAfter, account }); onDone?.(rec);
      } catch (err) {
        e.target.disabled = false; root.querySelector('#retire-error').textContent = err.message;
        if (/NO_KEY|BAD_KEY|REVOKED_KEY/.test(err.message)) root.querySelector('#retire-login').hidden = false;
      }
    });
    root.querySelector('#get-demo-login').addEventListener('click', async (e) => {
      e.target.disabled = true;
      try {
        const owner = await getDemoLogin('personal');
        root.querySelector('#retire-error').textContent = '';
        root.querySelector('#retire-login').innerHTML = `<span class="note ok" id="retire-login-ok">Logged in as ${esc(owner)}. Press Confirm retirement again.</span>`;
        document.dispatchEvent(new CustomEvent('carbonledger:login'));
      } catch (err) { e.target.disabled = false; root.querySelector('#retire-error').textContent = err.message; }
    });
  } });
}

// ---- Test-mode payments (docs/DECISIONS.md 2026-11-15, D29): Solana Pay on devnet, no real money ----
const payOn = () => CONFIG.ledger === 'solana-devnet' && ledger.info.payments && ledger.info.payments !== 'off';
async function payFirst(root, grams) {
  const r = await fetch(`${CONFIG.api.baseUrl}/v1/pay/quote`, { method: 'POST', headers: apiHeaders(), body: JSON.stringify({ grams }) });
  const q = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof q.detail === 'string' ? q.detail : 'Could not get a payment quote. Nothing was recorded.');
  const box = root.querySelector('#pay-box'); box.hidden = false;
  box.innerHTML = `<p><strong>Pay ${esc(q.amount)} ${esc(q.currency)}</strong><br><small>${esc(q.note)}</small></p>
    <div class="row" style="margin-top:0"><a class="btn small" href="${esc(q.url)}" id="pay-open">Open in wallet</a><button class="btn ghost small" type="button" id="pay-copy">Copy payment link</button></div>
    <p class="note" id="pay-status" role="status">Waiting for the payment on Solana devnet…</p>`;
  box.querySelector('#pay-copy').addEventListener('click', () => navigator.clipboard?.writeText(q.url).then(() => { box.querySelector('#pay-status').textContent = 'Link copied. Paste it into a wallet set to devnet.'; }).catch(() => {}));
  const until = Date.now() + 10 * 60 * 1000;
  while (Date.now() < until && box.isConnected) {
    await new Promise(res => setTimeout(res, 2500));
    const s = await (await fetch(`${CONFIG.api.baseUrl}/v1/pay/${encodeURIComponent(q.reference)}`)).json().catch(() => ({}));
    if (s.status === 'paid') { box.querySelector('#pay-status').textContent = 'Payment confirmed on Solana devnet (test). Recording your retirement…'; return q.reference; }
    if (s.status === 'invalid') throw new Error(`The payment did not match the quote (${s.code}). Nothing was recorded.`);
  }
  throw new Error('No payment arrived in 10 minutes. Nothing was recorded. Try again for a new quote.');
}

// Opens Verify for one receipt, the same way a typed #verify?id= link does.
export function openVerify(id) { history.pushState(null, '', `#verify?id=${encodeURIComponent(id)}`); window.dispatchEvent(new PopStateEvent('popstate')); }

export function showReceipt(rec, newBadges = [], reward = null) {
  const lines = (rec.lines || []).map(l => `<div class="r-line"><span>${esc(l.name)}</span><span>${mass(l.grams)}</span></div>`).join('');
  sheet(`
    ${reward ? rewardHTML({ grams: rec.grams, gained: reward.after - reward.before, before: reward.before, after: reward.after, badges: newBadges, countryName: rec.countryName, finished: rec.finished }) : ''}
    <div class="receipt">
      <div class="r-head"><strong class="r-brand">${brandMark(20)}CarbonLedger</strong><span>Retirement receipt</span></div>
      <div class="r-meta mono">${esc(rec.id)}<br>${new Date(rec.ts).toLocaleString('en-GB')}</div>
      <div class="r-sub">${esc(rec.note || rec.label)}</div>
      ${lines}
      <div class="r-line r-total"><span>Total retired</span><span>${mass(rec.grams)} CO₂e</span></div>
      <div class="r-line mono"><span>CLT units</span><span>${rec.clt} ${SIM_TAG}</span></div>
      <div class="r-line"><span>${rec.paidBy ? `Paid by ${esc(rec.paidBy)}` : 'Price (demo, unpaid)'}</span><span>${gbp(rec.priceGBP)}</span></div>
      ${rec.serialStart != null ? `<div class="r-line"><span>From</span><span data-tonne>${esc(tonneShort(rec.serialStart, rec.serialEnd))}</span></div>` : ''}
      <div class="r-line"><span>Credited to</span><span>${esc(rec.countryName || '—')}${rec.mode === 'frontline' ? ' (Frontline)' : ''}</span></div>
      ${rec.finished ? `<div class="r-line r-total"><span>This retirement finished clearing the symbolic share of ${esc(rec.countryName)}</span><span></span></div>` : ''}
      <div class="r-foot">${rec.explorerUrl ? `Recorded on Solana devnet, a test network. <a href="${esc(rec.explorerUrl)}" target="_blank" rel="noopener">View on the Solana explorer</a>` : rec.ledger === 'solana-devnet' ? 'Recorded by the CarbonLedger API. Awaiting the Solana devnet record.' : 'Recorded on this device only.'} Pilot units, not yet verified credits.</div>
    </div>
    ${!reward && newBadges.length ? `<div class="new-badges">${newBadges.map((b, i) => `<span class="chip-badge" style="--i:${i}">${icon('medal')}${esc(b.name)}</span>`).join('')}</div>` : ''}
    ${reward && live() ? `<div class="save-progress" id="save-progress" hidden role="region" aria-label="Save your progress">
      <p><strong>${icon('seal-check')} Keep this progress</strong><br><small>Right now it lives in this browser only. Save it to your email or your Seeker wallet, and it follows you to any device.</small></p>
      <div class="row" style="margin-top:0"><button class="btn small" id="save-go" data-close>Save my progress</button><button class="btn ghost small" id="save-later" type="button">Not now</button></div>
    </div>` : ''}
    <div class="row"><button class="btn ghost" id="receipt-verify" data-close>Verify it</button>${live() && rec.id ? '<button class="btn ghost" id="receipt-share" type="button">Share</button>' : ''}<button class="btn primary" data-close>Done</button></div>
    <p class="note" id="share-msg" role="status"></p>
  `, { onOpen: (root) => {
    countUp(root.querySelector('#reward-count'), reward ? reward.after - reward.before : 0);
    root.querySelector('#receipt-verify')?.addEventListener('click', () => openVerify(rec.id));
    root.querySelector('#receipt-share')?.addEventListener('click', () => shareReceipt(rec, root.querySelector('#share-msg')));
    offerSave(root);
  } });
}

// Straight after a retirement, the moment there is something to lose: ask once to save progress, until it is saved
// or the person says not now. Asking is counted (save_prompt); a finished sign-in is counted by the server.
async function offerSave(root) {
  const box = root.querySelector('#save-progress');
  if (!box || store.get('saveDeclined', false)) return;
  let p;
  try { p = await account.profile(); } catch { return; }
  if (p.signed_in || !box.isConnected) return;
  box.hidden = false; track('save_prompt');
  box.querySelector('#save-later').addEventListener('click', () => { store.set('saveDeclined', true); box.hidden = true; });
  box.querySelector('#save-go').addEventListener('click', () => {
    history.pushState(null, '', '#me'); window.dispatchEvent(new PopStateEvent('popstate'));
    setTimeout(() => { const f = document.querySelector('#seeker-signin') || document.querySelector('#signin-email'); f?.scrollIntoView({ block: 'center' }); f?.focus(); }, 300);
  });
}

// A link anyone can open to check this receipt on the public Verify screen. The words carry the pilot label.
export const shareText = (rec) => `I retired ${mass(rec.grams)} of CO2e in pilot units, not yet verified credits. Check my receipt:`;
async function shareReceipt(rec, msg) {
  const url = `${location.origin}/app#verify?id=${encodeURIComponent(rec.id)}`, text = shareText(rec);
  track('share');
  try {
    if (navigator.share) { await navigator.share({ title: 'My CarbonLedger receipt', text, url }); return; }
    await navigator.clipboard.writeText(`${text} ${url}`);
    msg.textContent = 'Link copied. Paste it anywhere.';
  } catch (err) {
    if (err?.name !== 'AbortError') msg.textContent = `Could not share from this browser. The receipt id is ${rec.id}.`;
  }
}
