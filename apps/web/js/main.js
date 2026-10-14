// App shell: mounts each view once and switches between them with the tab bar.
import { CONFIG } from './config.js';
import { mountShop } from './ui/shop.js';
import { mountTravel } from './ui/travel.js';
import { mountDaily } from './ui/daily.js';
import { mountCountries, refreshCountries } from './ui/countries.js';
import { mountMe, refreshMe } from './ui/me.js';
import { mountBusiness, refreshBusiness } from './ui/business.js';
import { mountVerify, refreshVerify } from './ui/verify.js';
import { openSettings } from './ui/settings.js';
import { ledger, apiKey, getDemoLogin } from './core/ledger.js';
import { levelChip } from './ui/hud.js';
import { xpOf } from './core/xp.js';
import { maybeOnboard } from './ui/onboard.js';
import { world } from './core/world.js';
import { $, toast } from './ui/dom.js';
import { account, track } from './core/account.js';

const VIEWS = {
  shop: { mount: mountShop },
  travel: { mount: mountTravel },
  daily: { mount: mountDaily },
  countries: { mount: mountCountries, refresh: refreshCountries },
  me: { mount: mountMe, refresh: refreshMe },
  business: { mount: mountBusiness, refresh: refreshBusiness },
  verify: { mount: mountVerify, refresh: refreshVerify },
};
let currentView = 'shop';

function updateChip() {
  const lv = levelChip(xpOf(ledger.history('personal')).total);
  $('#level-ring').style.setProperty('--p', lv.ring);
  $('#level-num').textContent = lv.n;
  $('#level-text').innerHTML = `${lv.text}<small>${lv.title}</small>`;
  $('#level-chip').setAttribute('aria-label', `${lv.text}, ${lv.toNext}`);
}

// The tab lives in the URL hash (#tab or #tab?query), so Back, reload and shared links all land on the right screen.
const tabOf = h => (h || '').replace(/^#/, '').split('?')[0];
function show(name, { push = true } = {}) {
  if (!VIEWS[name]) name = 'shop';
  const changed = currentView !== name;
  currentView = name;
  if (push && tabOf(location.hash) !== name) history.pushState(null, '', `#${name}`);
  if (changed) window.scrollTo({ top: 0, behavior: 'instant' });
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
    // Demo servers mint logins: a first-time visitor gets one here, silently, so the first retirement just works (D27).
    if (!apiKey.get() && h.demo_keys) { try { await getDemoLogin('personal'); document.dispatchEvent(new CustomEvent('carbonledger:login')); } catch {} }
    el.textContent = `Ledger: ${h.chain === 'dry-run' ? 'dry run' : `Solana ${h.chain}`}${apiKey.get() ? '' : ', no login yet'}`; el.title = 'Connected to the CarbonLedger API'; el.dataset.state = 'connected';
    ledger.info.name = h.chain === 'dry-run' ? 'the CarbonLedger API, dry-run chain (nothing is sent to Solana)' : `the CarbonLedger API, Solana ${h.chain}`;
  } catch { el.textContent = 'Ledger not reachable'; el.dataset.state = 'down'; }
}
showConnection();
world.refresh().then(() => { updateChip(); VIEWS[currentView].refresh?.(); });
document.addEventListener('carbonledger:world', () => VIEWS[currentView].refresh?.());
// Any Frontline strip opens the World tab on that country.
document.addEventListener('click', (e) => { const m = e.target.closest?.('[data-mission]'); if (m) { history.pushState(null, '', `#countries?pick=${m.dataset.mission}`); show('countries', { push: false }); } });
document.addEventListener('carbonledger:login', async () => { showConnection(); if (await ledger.sync()) { updateChip(); VIEWS[currentView].refresh?.(); } });
// Back, forward, links and typed hashes: the hash decides the tab (a query such as ?id= is read by the view).
window.addEventListener('popstate', () => { if (!handleSignIn()) show(tabOf(location.hash) || 'shop', { push: false }); });
window.addEventListener('hashchange', () => { if (!handleSignIn()) show(tabOf(location.hash) || 'shop', { push: false }); });
document.querySelectorAll('.tabs [data-tab]').forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
$('#level-chip').addEventListener('click', () => show('me'));
// Settings changes (price, community total) redraw the open view; price labels refresh on next render.
$('#settings-btn').addEventListener('click', () => openSettings(() => { Object.entries(VIEWS).forEach(([k, v]) => { if (k !== 'countries') v.mounted = false; }); show(currentView); }));
// Any retirement updates the level chip, after the server's history has been mirrored (T20).
const retire = ledger.retire.bind(ledger);
ledger.retire = async (e) => { const r = await retire(e); await ledger.sync(); await world.refresh(); updateChip(); VIEWS[currentView].refresh?.(); return r; };
ledger.sync().then(fromServer => { if (fromServer) { updateChip(); VIEWS[currentView].refresh?.(); } });
// A sign-in link from the email: #signin?t=TOKEN, on a fresh load or into an open app. The token leaves the
// address bar at once and is used once.
function handleSignIn() {
  const m = location.hash.match(/^#signin\?t=([A-Za-z0-9_-]{20,200})/);
  if (!m) return false;
  history.replaceState(null, '', '#me');
  show('me', { push: false });
  account.verify(m[1]).then(async (d) => { await ledger.sync(); updateChip(); VIEWS[currentView].refresh?.(); toast(`Signed in as ${d.email}. Your progress is saved.`); })
    .catch(err => toast(err.message));
  return true;
}
const signin = handleSignIn();
track('app_open');
addEventListener('appinstalled', () => track('install'));
if (!signin) maybeOnboard((tab) => show(tab));
let start = 'shop';
try { start = (tabOf(location.hash) || localStorage.getItem('carbonledger.tab') || 'shop'); } catch {}
show(start, { push: false });
if (!location.hash) history.replaceState(null, '', `#${currentView}`);

// Installable and opens offline (sw.js). The ledger itself is never served from a cache.
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('/sw.js').catch(() => {});
