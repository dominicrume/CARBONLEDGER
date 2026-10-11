// App shell: mounts each view once and switches between them with the tab bar.
import { CONFIG } from './config.js';
import { mountShop } from './ui/shop.js';
import { mountTravel } from './ui/travel.js';
import { mountDaily } from './ui/daily.js';
import { mountCountries, refreshCountries } from './ui/countries.js';
import { mountMe, refreshMe } from './ui/me.js';
import { mountBusiness, refreshBusiness } from './ui/business.js';
import { mountVerify } from './ui/verify.js';
import { openSettings } from './ui/settings.js';
import { ledger } from './core/ledger.js';
import { levelFor } from './core/game.js';
import { $ } from './ui/dom.js';

const VIEWS = {
  shop: { mount: mountShop },
  travel: { mount: mountTravel },
  daily: { mount: mountDaily },
  countries: { mount: mountCountries, refresh: refreshCountries },
  me: { mount: mountMe, refresh: refreshMe },
  business: { mount: mountBusiness, refresh: refreshBusiness },
  verify: { mount: mountVerify },
};
let currentView = 'shop';

function updateChip() {
  const total = ledger.history('personal').reduce((s, r) => s + r.grams, 0);
  $('#level-chip').textContent = `Level ${levelFor(total).n}`;
}

function show(name) {
  if (!VIEWS[name]) name = 'shop';
  currentView = name;
  for (const [k, v] of Object.entries(VIEWS)) {
    const el = $(`#view-${k}`);
    el.hidden = k !== name;
    if (k === name) { if (!v.mounted) { v.mount(el); v.mounted = true; } else v.refresh?.(); }
  }
  document.querySelectorAll('.tabs [data-tab]').forEach(b => b.setAttribute('aria-current', b.dataset.tab === name ? 'page' : 'false'));
  try { localStorage.setItem('carbonledger.tab', name); } catch {}
  updateChip();
}

document.title = CONFIG.appName;
// Connection state (docs/ux/DESIGN-SYSTEM.md, add 3). The browser only reports who it is talking to.
async function showConnection() {
  const el = $('#conn');
  if (CONFIG.ledger !== 'solana-devnet') { el.textContent = 'Working on this device only'; el.dataset.state = 'local'; return; }
  try {
    const r = await fetch(`${CONFIG.api.baseUrl}/health`, { signal: AbortSignal.timeout(4000) });
    const h = await r.json();
    el.textContent = `Connected to the ledger (${h.chain})`; el.dataset.state = 'connected';
  } catch { el.textContent = 'Ledger not reachable'; el.dataset.state = 'down'; }
}
showConnection();
window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if (VIEWS[h]) show(h); });
document.querySelectorAll('.tabs [data-tab]').forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
$('#level-chip').addEventListener('click', () => show('me'));
// Settings changes (price, community total) redraw the open view; price labels refresh on next render.
$('#settings-btn').addEventListener('click', () => openSettings(() => { Object.entries(VIEWS).forEach(([k, v]) => { if (k !== 'countries') v.mounted = false; }); show(currentView); }));
// Any retirement updates the level chip.
const retire = ledger.retire.bind(ledger);
ledger.retire = async (e) => { const r = await retire(e); updateChip(); return r; };
let start = 'shop';
try { start = (location.hash.slice(1) || localStorage.getItem('carbonledger.tab') || 'shop'); } catch {}
show(start);
