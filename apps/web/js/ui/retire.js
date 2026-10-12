// Shared "retire" action: shows the confirmation, records on the ledger, then shows the receipt.
// Wording follows rules/HARDENING-PRODUCT.md: pilot units are retired, never "offset", and are labelled as pilot units, not yet verified credits.
import { settings } from '../core/settings.js';
import { store } from '../core/store.js';
import { ledger, gramsToClt, priceGBP, ref, getDemoLogin } from '../core/ledger.js';
import { badgeBook, countryQueue } from '../core/game.js';
import { target, resolveTarget } from '../core/target.js';
import { COUNTRIES } from '../data/countries.js';
import { sheet, esc, mass, gbp } from './dom.js';
import { icon, rewardHTML, buzz, xp, countUp, brandMark } from './hud.js';
import { levelFor } from '../core/game.js';

export const SIM_TAG = '<span class="tag">Pilot units</span>';
export function retireButtonLabel(grams) { return `Retire ${mass(grams)} for ${gbp(priceGBP(grams))} <span class="xp">+${xp(grams)}</span>`; }

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
    <p class="note">No payment is taken. Pilot units, not yet verified credits.</p>
    <p class="note bad" id="retire-error" role="alert"></p>
    <p class="row" id="retire-login" hidden><button class="btn ghost small" type="button" id="get-demo-login">Get a demo login</button><span class="note">A login for simulated units, kept in this browser. Then confirm again.</span></p>
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
      const totalBefore = ledger.history(account).reduce((s, r) => s + r.grams, 0);
      const attempt = () => ledger.retire({ ...entry, idempotencyKey, countryIso3: dest?.iso3, countryName: dest?.name, mode: dest?.mode, finished: !!dest?.finished });
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
        const totalAfter = ledger.history(account).reduce((s, r) => s + r.grams, 0);
        buzz();
        close(); showReceipt(rec, fresh, { before: totalBefore, after: Math.max(totalAfter, totalBefore + rec.grams), account }); onDone?.(rec);
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

export function showReceipt(rec, newBadges = [], reward = null) {
  const lines = (rec.lines || []).map(l => `<div class="r-line"><span>${esc(l.name)}</span><span>${mass(l.grams)}</span></div>`).join('');
  const base = reward?.account === 'business' ? 50_000 : 500;
  sheet(`
    ${reward ? rewardHTML({ grams: rec.grams, before: reward.before, after: reward.after, badges: newBadges, countryName: rec.countryName, finished: rec.finished, base }) : ''}
    <div class="receipt">
      <div class="r-head"><strong class="r-brand">${brandMark(20)}CarbonLedger</strong><span>Retirement receipt</span></div>
      <div class="r-meta mono">${esc(rec.id)}<br>${new Date(rec.ts).toLocaleString('en-GB')}</div>
      <div class="r-sub">${esc(rec.note || rec.label)}</div>
      ${lines}
      <div class="r-line r-total"><span>Total retired</span><span>${mass(rec.grams)} CO₂e</span></div>
      <div class="r-line mono"><span>CLT units</span><span>${rec.clt} ${SIM_TAG}</span></div>
      <div class="r-line"><span>${rec.paidBy ? `Paid by ${esc(rec.paidBy)}` : 'Price (demo, unpaid)'}</span><span>${gbp(rec.priceGBP)}</span></div>
      <div class="r-line"><span>Credited to</span><span>${esc(rec.countryName || '—')}${rec.mode === 'frontline' ? ' (Frontline)' : ''}</span></div>
      ${rec.finished ? `<div class="r-line r-total"><span>This retirement finished clearing the symbolic share of ${esc(rec.countryName)}</span><span></span></div>` : ''}
      <div class="r-foot">${rec.explorerUrl ? `Recorded on Solana devnet, a test network. <a href="${esc(rec.explorerUrl)}" target="_blank" rel="noopener">View on the Solana explorer</a>` : rec.ledger === 'solana-devnet' ? 'Recorded by the CarbonLedger API. Awaiting the Solana devnet record.' : 'Recorded on this device only.'} Pilot units, not yet verified credits.</div>
    </div>
    ${!reward && newBadges.length ? `<div class="new-badges">${newBadges.map((b, i) => `<span class="chip-badge" style="--i:${i}">${icon('medal')}${esc(b.name)}</span>`).join('')}</div>` : ''}
    <div class="row"><button class="btn ghost" id="receipt-verify" data-close>Verify it</button><button class="btn primary" data-close>Done</button></div>
  `, { onOpen: (root) => { countUp(root.querySelector('#reward-count'), rec.grams); root.querySelector('#receipt-verify')?.addEventListener('click', () => { history.pushState(null, '', `#verify?id=${encodeURIComponent(rec.id)}`); window.dispatchEvent(new PopStateEvent('popstate')); }); } });
}
