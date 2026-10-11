// Countries view: a globe and a queue of national shares of the historical CO2 stock, cleared smallest first.
import { countryQueue } from '../core/game.js';
import { settings } from '../core/settings.js';
import { COUNTRIES } from '../data/countries.js';
import { createGlobe } from './globe.js';
import { target } from '../core/target.js';
import { $, esc, tonnes, sheet } from './dom.js';

const TOTAL_T = COUNTRIES.reduce((s, c) => s + c.tonnes, 0);
const byIso = new Map(COUNTRIES.map(c => [c.iso3, c]));
let globe = null, simTonnes = 0, status = new Map(), queue = null;

const simValue = v => v === 0 ? 0 : Math.round(10 ** (3 + v * 0.0938)); // slider 1..100 -> 1,000 t to ~2,400 billion t

const GLOBE_STATUS = { cleared: 'cleared', front: 'current', supported: 'current', waiting: 'waiting' };
function computeStatus() {
  queue = simTonnes ? countryQueue(simTonnes, []) : countryQueue();
  status = new Map([...queue.byIso.values()].map(c => [c.iso3, GLOBE_STATUS[c.status]]));
}

export function mountCountries(root) {
  root.innerHTML = `
    <section class="panel">
      <p class="eyebrow">Clearing the historical stock</p>
      <h1 class="h1">Countries</h1>
      <p class="lead">Each country carries its share of the ${tonnes(TOTAL_T)} of CO₂ emitted since 1850. Send your retirements to any country, or play the Frontline: clear the world smallest share first. This is a symbolic game: a CLT is a tonne of simulated pilot units retired today, not a tonne of the 1850 stock.</p>
      <div class="target-box" id="target-box"></div>
      <div class="globe-wrap">
        <canvas id="globe" class="globe" aria-label="Globe showing which countries are cleared, in progress or waiting"></canvas>
        <p class="globe-fallback muted" hidden>The globe could not load. The queue below shows the same information.</p>
      </div>
      <div class="legend"><span class="sw ok"></span>Cleared <span class="sw warn"></span>In progress <span class="sw bad"></span>Waiting</div>
      <p class="hint muted">Drag to turn the globe. Tap a country for details.</p>
      <div id="picked" class="picked" hidden></div>
      <label class="label" for="sim">Simulate a community total</label>
      <input type="range" id="sim" min="0" max="100" value="0">
      <div id="sim-out" class="sim-out"></div>
      <div id="front"></div>
    </section>
    <section class="panel">
      <h2 class="h2">The queue</h2>
      <ol class="queue" id="queue"></ol>
    </section>
    <section class="panel">
      <h2 class="h3">How shares are worked out</h2>
      <p class="note">Each country's cumulative CO₂ emissions within its borders from 1850 to 2019, including land-use change (Global Carbon Project, via Our World in Data). These are scaled so the total equals the IPCC AR6 figure of 2,400 billion tonnes. The game is symbolic: clearing a share here does not remove historical emissions, and a CLT is a tonne of simulated pilot units retired against a project today. Other methods, such as consumption-based accounting, would give different shares. Map: Natural Earth.</p>
    </section>`;
  computeStatus();
  globe = createGlobe($('#globe', root), { statusOf: id => status.get(id) || null, onSelect: showPicked });
  if (!globe) { $('#globe', root).hidden = true; $('.globe-fallback', root).hidden = false; }
  $('#sim', root).addEventListener('input', e => { simTonnes = simValue(+e.target.value); refreshCountries(); });
  refreshCountries();
}

function showPicked(iso3, mapName) {
  const box = $('#picked');
  if (!iso3) { box.hidden = true; return; }
  const c = byIso.get(iso3), s = status.get(iso3);
  const q = c ? queue.byIso.get(iso3) : null;
  const label = { cleared: 'Cleared', current: q?.status === 'front' ? 'Frontline' : 'In progress', waiting: 'Waiting' }[s] || 'Not in the queue';
  const pos = c ? COUNTRIES.indexOf(c) + 1 : null;
  box.hidden = false;
  box.innerHTML = `<strong>${esc(c?.name || mapName || iso3)}</strong>
    <span class="pill ${s || ''}">${label}</span>
    <small>${c ? `Share ${tonnes(c.tonnes)}, ${Math.floor((q?.progress || 0) * 100)}% cleared. Position ${pos} of ${COUNTRIES.length} in the queue.` : 'No separate share in the emissions data.'}</small>
    ${c && s !== 'cleared' ? `<button class="btn ghost small" id="send-here">Send my retirements to ${esc(c.name)}</button>` : ''}`;
  $('#send-here')?.addEventListener('click', () => { target.set({ mode: 'chosen', iso3 }); drawTarget(); });
}

function drawTarget() {
  const t = target.get(), box = $('#target-box');
  const chosen = t.mode === 'chosen' ? COUNTRIES.find(c => c.iso3 === t.iso3) : null;
  box.innerHTML = `<span class="label">Your retirements go to</span>
    <div class="seg" role="radiogroup">
      <button role="radio" aria-checked="${!chosen}" class="${!chosen ? 'on' : ''}" data-t="frontline">The Frontline</button>
      <button role="radio" aria-checked="${!!chosen}" class="${chosen ? 'on' : ''}" data-t="chosen">${chosen ? esc(chosen.name) : 'A country I choose'}</button>
    </div>
    <small>${chosen ? 'Change country by tapping it on the globe, or when you confirm a retirement.' : 'Each retirement goes to the smallest country still to clear.'}</small>`;
  box.querySelector('[data-t=frontline]').onclick = () => { target.set({ mode: 'frontline' }); drawTarget(); };
  box.querySelector('[data-t=chosen]').onclick = () => sheet(`
    <h2 class="sheet-title">Choose a country</h2>
    <label class="label" for="pick-country">Country</label>
    <select id="pick-country">${[...COUNTRIES].sort((a, b) => a.name.localeCompare(b.name)).map(c => `<option value="${c.iso3}" ${c.iso3 === (chosen?.iso3 || 'GBR') ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}</select>
    <p class="note">You can also tap any country on the globe.</p>
    <div class="row"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="pick-ok">Send my retirements here</button></div>`,
    { onOpen: (r, close) => r.querySelector('#pick-ok').addEventListener('click', () => {
      const iso3 = r.querySelector('#pick-country').value; target.set({ mode: 'chosen', iso3 }); close(); drawTarget(); globe?.focus(iso3); showPicked(iso3);
    }) });
}

export function refreshCountries() {
  computeStatus();
  drawTarget();
  globe?.redraw();
  const q = queue, c = q.current;
  $('#sim-out').innerHTML = simTonnes
    ? `<strong>${tonnes(simTonnes)}</strong> retired would clear <strong>${q.cleared.length}</strong> of ${q.totalCountries} countries. Simulation only; the ledger is unchanged.`
    : `<span class="muted">Slide to see how the globe changes as the community grows.</span>`;
  $('#front').innerHTML = c ? `
    <div class="front">
      <span class="label">${simTonnes ? 'Frontline (simulated)' : 'The Frontline'}</span>
      <div class="front-name">${esc(c.name)}</div>
      <div class="bar"><span style="width:${Math.max(0.5, c.progress * 100).toFixed(2)}%"></span></div>
      <div class="row between small"><span>${tonnes(c.doneGrams / 1e6)} retired</span><span>${tonnes(c.tonnes)} share</span></div>
      <p class="note">The Frontline is the smallest country still to clear. Retirements sent here earn Frontline skills, and the retirement that clears it earns Finisher.</p>
      <div class="row"><button class="btn ghost small" id="show-current">Show on globe</button></div>
      <p class="note">${q.cleared.length} cleared: ${q.cleared.slice(0, 8).map(x => esc(x.name)).join(', ') || 'none yet'}${q.cleared.length > 8 ? ' and more' : ''}.${simTonnes ? '' : ` Includes a simulated community total of ${tonnes(settings.communityTonnes())} for the demo, changeable in Settings.`}</p>
    </div>` : `<p>Every country is cleared.</p>`;
  $('#show-current')?.addEventListener('click', () => { globe?.focus(c.iso3); showPicked(c.iso3); });
  const show = [...q.cleared.slice(-6).map(x => ({ ...x, s: 'cleared' })), ...(c ? [{ ...c, s: 'current' }] : []), ...q.rest.slice(0, 11).map(x => ({ ...x, s: 'waiting' }))];
  $('#queue').innerHTML = (q.cleared.length > 6 ? `<li class="q more"><span class="q-name">${q.cleared.length - 6} more cleared</span></li>` : '') +
    show.map(x => `<li class="q ${x.s}"><span class="q-name">${esc(x.name)}</span><span class="q-t">${tonnes(x.tonnes)}</span></li>`).join('') +
    (q.rest.length > 11 ? `<li class="q more"><span class="q-name">…and ${q.rest.length - 11} more, ending with ${esc(COUNTRIES.at(-1).name)}</span></li>` : '');
}
