// Countries view: a globe and a queue of national shares of the historical CO2 stock, cleared smallest first.
import { countryQueue } from '../core/game.js';
import { settings } from '../core/settings.js';
import { COUNTRIES } from '../data/countries.js';
import { createGlobe } from './globe.js';
import { target } from '../core/target.js';
import { $, esc, tonnes, sheet, mass, toast } from './dom.js';
import { icon, confettiHTML } from './hud.js';
import { world } from '../core/world.js';

const TOTAL_T = COUNTRIES.reduce((s, c) => s + c.tonnes, 0);
const byIso = new Map(COUNTRIES.map(c => [c.iso3, c]));
let globe = null, simTonnes = 0, status = new Map(), queue = null;

const simValue = v => v === 0 ? 0 : Math.round(10 ** (3 + v * 0.0938)); // slider 1..100 -> 1,000 t to ~2,400 billion t

const GLOBE_STATUS = { cleared: 'cleared', front: 'current', supported: 'current', waiting: 'waiting' };
function computeStatus() {
  queue = simTonnes ? countryQueue(simTonnes, []) : countryQueue();
  status = new Map([...queue.byIso.values()].map(c => [c.iso3, GLOBE_STATUS[c.status]]));
}

let lastCleared = null;   // to notice when a country gets finished while this screen is open

export function mountCountries(root) {
  root.innerHTML = `
    <section class="panel plain">
      <div class="clock" id="clock" aria-live="polite"></div>
      <p class="lead">Each country carries its share of the ${tonnes(TOTAL_T)} of CO₂ emitted since 1850. Clear the smallest share first, together, then the next. A symbolic game: a CLT is a tonne of pilot units retired today, not a tonne of the 1850 stock.</p>
      <div class="target-box" id="target-box"></div>
      <div class="globe-wrap">
        <canvas id="globe" class="globe" aria-label="Globe showing which countries are cleared, in progress or waiting"></canvas>
        <p class="globe-fallback muted" hidden>The globe could not load. The queue below shows the same information.</p>
      </div>
      <div class="legend"><span class="sw ok"></span>Cleared <span class="sw warn"></span>In progress <span class="sw wait"></span>Waiting</div>
      <p class="hint muted">Drag to turn the globe. Tap a country for details.</p>
      <div id="front"></div>
      <div id="picked" class="picked" hidden></div>
      <label class="label" for="sim">Simulate a community total</label>
      <input type="range" id="sim" min="0" max="100" value="0">
      <div id="sim-out" class="sim-out"></div>
    </section>
    <section class="panel">
      <h2 class="h2">${icon('path')} The queue</h2>
      <p class="note">Smallest share first. Finish one and the next becomes the Frontline.</p>
      <ol class="queue" id="queue"></ol>
    </section>
    <section class="panel">
      <h2 class="h3">How shares are worked out</h2>
      <p class="note">Each country's cumulative CO₂ emissions within its borders from 1850 to 2019, including land-use change (Global Carbon Project, via Our World in Data). These are scaled so the total equals the IPCC AR6 figure of 2,400 billion tonnes. The game is symbolic: clearing a share here does not remove historical emissions, and a CLT is a tonne of pilot units retired against a project today. Other methods, such as consumption-based accounting, would give different shares. Map: Natural Earth.</p>
    </section>`;
  computeStatus();
  globe = createGlobe($('#globe', root), { statusOf: id => status.get(id) || null, onSelect: showPicked });
  if (!globe) { $('#globe', root).hidden = true; $('.globe-fallback', root).hidden = false; }
  $('#sim', root).addEventListener('input', e => { simTonnes = simValue(+e.target.value); refreshCountries(); });
  refreshCountries();
  const pick = new URLSearchParams(location.hash.split('?')[1] || '').get('pick');
  if (pick && byIso.has(pick)) { globe?.focus(pick); showPicked(pick); }
}

function clockHTML(q) {
  const w = world.get();
  const clearedT = q.cleared.reduce((s, c) => s + c.tonnes, 0) + (q.current ? q.current.doneGrams / 1e6 : 0);
  const pct = clearedT / TOTAL_T * 100;
  return `
    <div class="clock-big"><em>${q.cleared.length}</em> of ${q.totalCountries} cleared</div>
    <div class="clock-sub">${tonnes(clearedT)} of the ${tonnes(TOTAL_T)} symbolic stock, ${pct < 0.01 ? 'under 0.01' : pct.toFixed(2)}%</div>
    <div class="clock-stats">
      <div class="stat"><b>${w ? w.players.toLocaleString('en-GB') : '1'}</b><small>player${w && w.players === 1 ? '' : 's'}</small></div>
      <div class="stat"><b>${w ? mass(w.retired_g) : mass(0)}</b><small>retired on the ledger</small></div>
      <div class="stat"><b>${w ? w.retirements.toLocaleString('en-GB') : '0'}</b><small>receipts</small></div>
    </div>`;
}

function celebrate(country) {
  sheet(`
    <div class="reward">${confettiHTML(24)}
      <div class="levelup">${icon('crown')} Country cleared</div>
      <div class="reward-xp" style="font-size:1.8rem">${esc(country.name)}</div>
      <div class="reward-sub">Its symbolic share of ${tonnes(country.tonnes)} is done. Everyone who sent retirements there earns the Finisher badge. The Frontline moves to the next smallest country.</div>
    </div>
    <div class="row"><button class="btn primary" data-close>On to the next</button></div>`);
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
  $('#send-here')?.addEventListener('click', (e) => { target.set({ mode: 'chosen', iso3 }); drawTarget(); e.target.disabled = true; e.target.textContent = `Your retirements now go to ${c.name}`; toast(`Your next retirements go to ${c.name}.`); });
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
  if ($('#clock')) $('#clock').innerHTML = clockHTML(q);
  if (!simTonnes) {
    if (lastCleared !== null && q.cleared.length > lastCleared) celebrate(q.cleared.at(-1));
    lastCleared = q.cleared.length;
  }
  $('#sim-out').innerHTML = simTonnes
    ? `<strong>${tonnes(simTonnes)}</strong> retired would clear <strong>${q.cleared.length}</strong> of ${q.totalCountries} countries. Simulation only; the ledger is unchanged.`
    : `<span class="muted">Slide to see how the globe changes as the community grows.</span>`;
  const players = world.get()?.countries?.[c?.iso3]?.players || 0;
  $('#front').innerHTML = c ? `
    <div class="front">
      <span class="label">${icon('target')} ${simTonnes ? 'Frontline (simulated)' : 'The Frontline'}${players ? ` · ${players} player${players === 1 ? '' : 's'} on it` : ''}</span>
      <div class="front-name">${esc(c.name)}</div>
      <div class="bar"><span style="width:${Math.max(0.5, c.progress * 100).toFixed(2)}%"></span></div>
      <div class="row between small"><span>${tonnes(c.doneGrams / 1e6)} retired</span><span>${tonnes(c.tonnes)} share</span></div>
      <p class="note">The Frontline is the smallest country still to clear. Retirements sent here earn Frontline skills, and the retirement that clears it earns Finisher.</p>
      <div class="row"><button class="btn ghost small" id="show-current">Show on globe</button></div>
      <p class="note">${q.cleared.length} cleared: ${q.cleared.slice(0, 8).map(x => esc(x.name)).join(', ') || 'none yet'}${q.cleared.length > 8 ? ' and more' : ''}.${simTonnes ? '' : ` Includes a simulated community total of ${tonnes(settings.communityTonnes())} for the demo, changeable in Settings.`}</p>
    </div>` : `<p>Every country is cleared.</p>`;
  $('#show-current')?.addEventListener('click', () => { globe?.focus(c.iso3); showPicked(c.iso3); });
  const show = [...q.cleared.slice(-4).map(x => ({ ...x, s: 'cleared' })), ...(c ? [{ ...c, s: 'current' }] : []), ...q.rest.slice(0, 8).map(x => ({ ...x, s: 'waiting' }))];
  $('#queue').innerHTML = (q.cleared.length > 4 ? `<li class="q more"><span class="q-name">${q.cleared.length - 4} more cleared</span></li>` : '') +
    show.map(x => `<li class="q ${x.s}"><span class="q-num">${x.s === 'cleared' ? icon('check-circle') : COUNTRIES.indexOf(byIso.get(x.iso3)) + 1}</span><span class="q-name">${esc(x.name)}${x.s === 'current' ? ` <small>${Math.floor(x.progress * 100)}% cleared</small>` : ''}</span><span class="q-t">${tonnes(x.tonnes)}</span></li>`).join('') +
    (q.rest.length > 8 ? `<li class="q more"><span class="q-name">and ${q.rest.length - 8} more, ending with ${esc(COUNTRIES.at(-1).name)}</span></li>` : '');
}
