// Shared "retire" action: shows the confirmation, records on the ledger, then shows the receipt.
// Wording follows rules/HARDENING-PRODUCT.md: pilot units are retired, never "offset", and are labelled simulated.
import { settings } from '../core/settings.js';
import { store } from '../core/store.js';
import { ledger, gramsToClt, priceGBP, ref } from '../core/ledger.js';
import { badgeBook, countryQueue } from '../core/game.js';
import { target, resolveTarget } from '../core/target.js';
import { COUNTRIES } from '../data/countries.js';
import { sheet, esc, mass, gbp } from './dom.js';

export const SIM_TAG = '<span class="tag">Simulated pilot units</span>';
export function retireButtonLabel(grams) { return `Retire ${mass(grams)} of pilot units for ${gbp(priceGBP(grams))}`; }

// entry: { grams, kind, label, lines: [{name, grams}], ...extra }
const countryOptions = sel => [...COUNTRIES].sort((a, b) => a.name.localeCompare(b.name))
  .map(c => `<option value="${c.iso3}" ${c.iso3 === sel ? 'selected' : ''}>${esc(c.name)}</option>`).join('');

export function confirmRetirement(entry, onDone) {
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
    <p class="note">Demo only. No payment is taken. These are simulated pilot units, not verified credits.</p>
    <div class="row"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirm-retire">Confirm retirement</button></div>
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
    root.querySelector('#confirm-retire').addEventListener('click', async (e) => {
      e.target.disabled = true;
      const choice = pick(); target.set(choice);
      const dest = resolveTarget(choice, entry.grams);
      const account = entry.account || 'personal', ctx = { employees: store.get('biz', {}).employees };
      const before = new Set(badgeBook(account, ctx).all.map(b => b.id));
      try {
        const rec = await ledger.retire({ ...entry, idempotencyKey, countryIso3: dest?.iso3, countryName: dest?.name, mode: dest?.mode, finished: !!dest?.finished });
        const fresh = badgeBook(account, ctx).all.filter(b => !before.has(b.id));
        close(); showReceipt(rec, fresh); onDone?.(rec);
      } catch (err) { e.target.disabled = false; root.querySelector('.note').textContent = err.message; }
    });
  } });
}

export function showReceipt(rec, newBadges = []) {
  const lines = (rec.lines || []).map(l => `<div class="r-line"><span>${esc(l.name)}</span><span>${mass(l.grams)}</span></div>`).join('');
  sheet(`
    <div class="receipt">
      <div class="r-head"><strong>CarbonLedger</strong><span>Retirement receipt</span></div>
      <div class="r-meta mono">${esc(rec.id)}<br>${new Date(rec.ts).toLocaleString('en-GB')}</div>
      <div class="r-sub">${esc(rec.label)}</div>
      ${lines}
      <div class="r-line r-total"><span>Total retired</span><span>${mass(rec.grams)} CO₂e</span></div>
      <div class="r-line mono"><span>CLT units</span><span>${rec.clt} ${SIM_TAG}</span></div>
      <div class="r-line"><span>${rec.paidBy ? `Paid by ${esc(rec.paidBy)}` : 'Price (demo, unpaid)'}</span><span>${gbp(rec.priceGBP)}</span></div>
      <div class="r-line"><span>Credited to</span><span>${esc(rec.countryName || '—')}${rec.mode === 'frontline' ? ' (Frontline)' : ''}</span></div>
      ${rec.finished ? `<div class="r-line r-total"><span>This retirement finished clearing the symbolic share of ${esc(rec.countryName)}</span><span></span></div>` : ''}
      <div class="r-foot">${rec.explorerUrl ? `Recorded on Solana devnet, a test network. <a href="${esc(rec.explorerUrl)}" target="_blank" rel="noopener">View on the Solana explorer</a>` : rec.ledger === 'solana-devnet' ? 'Recorded by the CarbonLedger API. Awaiting the Solana devnet record.' : 'Recorded on this device only.'} Simulated pilot units, not verified credits.</div>
    </div>
    ${newBadges.length ? `<div class="new-badges"><span class="label">New badge${newBadges.length > 1 ? 's' : ''}</span>${newBadges.map(b => `<span class="chip-badge">${esc(b.name)}</span>`).join('')}</div>` : ''}
    <div class="row"><button class="btn primary" data-close>Done</button></div>
  `);
}
