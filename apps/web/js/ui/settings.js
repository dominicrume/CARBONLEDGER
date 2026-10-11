// Settings sheet: trustee price per tonne, demo community total, method notes and reset.
import { CONFIG } from '../config.js';
import { settings } from '../core/settings.js';
import { store } from '../core/store.js';
import { ledger, apiKey, getDemoLogin } from '../core/ledger.js';
import { TIERS } from '../core/estimate.js';
import { sheet, esc, gbp, toast } from './dom.js';

export function openSettings(onChange) {
  sheet(`
    <h2 class="sheet-title">Settings</h2>
    <form id="settings-form" class="form">
      <label class="label" for="s-price">CLT price per tonne (£)</label>
      <input id="s-price" type="number" min="0.01" step="any" value="${settings.pricePerTonne()}" class="num">
      <small>Set by trustees. That is ${gbp(settings.pricePerTonne() / 1000)} per kilogram. Default ${gbp(CONFIG.pricePerTonneGBP)}.</small>
      <label class="label" for="s-community">Simulated community total (tonnes)</label>
      <input id="s-community" type="number" min="0" step="any" value="${settings.communityTonnes()}" class="num">
      <small>Added to your own retirements so the Countries view shows progress during demos. Set to 0 to show your own retirements only.</small>
      <label class="label" for="s-apikey">API key (login for the ledger)</label>
      <input id="s-apikey" type="password" autocomplete="off" spellcheck="false" value="${esc(apiKey.get())}" placeholder="clk_...">
      <small>Given to you once by whoever runs the API. It is a login, not a wallet: it signs nothing. Kept in this browser only.</small>
      <p class="row wrap" id="s-demo-row" hidden><button class="btn ghost small" type="button" id="s-demo-personal">Get a personal demo login</button><button class="btn ghost small" type="button" id="s-demo-business">Get a business demo login</button></p>
      <p class="note" id="s-demo-note"></p>
      <div class="row"><button class="btn ghost" type="button" data-close>Cancel</button><button class="btn primary" type="submit">Save</button></div>
    </form>
    <h3 class="h3">About the figures</h3>
    <p class="note">Each product's footprint comes from the first available of: ${Object.values(TIERS).join('; ')}. Where an international and a national figure both exist, the higher is used, and estimates include a safety margin. One CLT is one tonne of CO₂ from the historical stock and divides down to a gram. Ledger: ${esc(ledger.info.name)}. Product data: Open Food Facts (ODbL). Map: Natural Earth.</p>
    <h3 class="h3">Demo data</h3>
    <button class="link" id="s-reset" type="button">Clear all retirements, badges and basket on this device</button>
    <p class="note" id="s-reset-confirm" hidden>This cannot be undone. <button class="link" id="s-reset-yes" type="button">Yes, clear everything</button></p>
  `, { onOpen: (root, close) => {
    root.querySelector('#settings-form').addEventListener('submit', e => {
      e.preventDefault();
      settings.setPricePerTonne(+root.querySelector('#s-price').value);
      settings.setCommunityTonnes(+root.querySelector('#s-community').value);
      apiKey.set(root.querySelector('#s-apikey').value);
      close(); toast(`Saved. CLT price ${gbp(settings.pricePerTonne())} per tonne.`); onChange?.();
    });
    root.querySelector('#s-reset').addEventListener('click', () => { root.querySelector('#s-reset-confirm').hidden = false; });
    if (CONFIG.ledger === 'solana-devnet') {
      fetch(`${CONFIG.api.baseUrl}/health`, { signal: AbortSignal.timeout(4000) }).then(r => r.json()).then(h => { if (h.demo_keys) root.querySelector('#s-demo-row').hidden = false; }).catch(() => {});
      for (const [id, role] of [['#s-demo-personal', 'personal'], ['#s-demo-business', 'business']]) {
        root.querySelector(id).addEventListener('click', async (e) => {
          e.target.disabled = true;
          try { const owner = await getDemoLogin(role); root.querySelector('#s-apikey').value = apiKey.get(); root.querySelector('#s-demo-note').textContent = `Logged in as ${owner}. Saved in this browser.`; document.dispatchEvent(new CustomEvent('carbonledger:login')); }
          catch (err) { root.querySelector('#s-demo-note').textContent = err.message; }
          e.target.disabled = false;
        });
      }
    }
    root.querySelector('#s-reset-yes').addEventListener('click', () => { store.set('ledger', []); store.set('basket', []); location.reload(); });
  } });
}
