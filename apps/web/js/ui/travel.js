// Travel view: flights between airports, or ground journeys by distance.
import { GROUND, AIRPORTS, TRAVEL_SOURCE } from '../data/travel.js';
import { flightGrams, groundGrams } from '../core/activities.js';
import { $, esc, mass } from './dom.js';
import { confirmRetirement, retireButtonLabel } from './retire.js';

export function mountTravel(root) {
  const opts = AIRPORTS.map(a => `<option value="${a[0]}">${esc(a[1])} (${a[0]})</option>`).join('');
  root.innerHTML = `
    <section class="panel">
      <h1 class="h1">Retire pilot units for a journey</h1>
      <div class="seg" role="tablist">
        <button class="on" data-mode="flight" role="tab">Flight</button><button data-mode="ground" role="tab">Car, train, bus</button>
      </div>
      <form id="flight-form" class="form">
        <label class="label" for="from">From</label><select id="from">${opts}</select>
        <label class="label" for="to">To</label><select id="to">${opts}</select>
        <label class="label" for="cabin">Cabin</label>
        <select id="cabin"><option value="economy">Economy</option><option value="business">Business or first</option></select>
        <div class="row"><label class="check"><input type="checkbox" id="ret" checked> Return trip</label>
        <label class="label inline" for="fpeople">People</label><input id="fpeople" type="number" min="1" value="1" class="num"></div>
      </form>
      <form id="ground-form" class="form" hidden>
        <label class="label" for="gmode">How you travelled</label>
        <select id="gmode">${GROUND.map(g => `<option value="${g.id}">${esc(g.label)}</option>`).join('')}</select>
        <label class="label" for="gkm">Distance in km</label><input id="gkm" type="number" min="0" value="25" class="num">
        <label class="label" for="gpeople">People in the car (cars only)</label><input id="gpeople" type="number" min="1" value="1" class="num">
      </form>
      <div class="result" id="travel-result"></div>
      <p class="note">Factors: ${esc(TRAVEL_SOURCE)}. Flights include the warming effect of high-altitude emissions and an 8% routing uplift.</p>
    </section>`;
  $('#to', root).value = 'BCN';
  let mode = 'flight';
  root.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => {
    mode = b.dataset.mode;
    root.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('on', x === b));
    $('#flight-form', root).hidden = mode !== 'flight'; $('#ground-form', root).hidden = mode !== 'ground';
    update();
  }));
  root.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  root.querySelectorAll('form').forEach(f => f.addEventListener('submit', e => e.preventDefault()));

  function calc() {
    if (mode === 'flight') {
      const f = flightGrams({ from: $('#from').value, to: $('#to').value, cabin: $('#cabin').value, ret: $('#ret').checked, people: Math.max(1, +$('#fpeople').value || 1) });
      return f && { ...f, travelMode: 'flight', item: { type: 'flight', from: $('#from').value, to: $('#to').value, cabin: $('#cabin').value, ret: $('#ret').checked, people: Math.max(1, +$('#fpeople').value || 1) }, sub: `${f.dist.toLocaleString('en-GB')} km each way, ${f.band === 'long' ? 'long-haul' : f.band === 'short' ? 'short-haul' : 'domestic'}`, longHaul: f.band === 'long' };
    }
    const mode = $('#gmode').value, dist = Math.max(0, +$('#gkm').value || 0), people = Math.max(1, +$('#gpeople').value || 1);
    const r = groundGrams({ mode, km: dist, people });
    if (!r) return null;
    return { travelMode: mode, grams: r.grams, label: r.label, sub: r.share > 1 ? `your share of ${r.share} people` : '', item: { type: 'ground', mode, km: dist, people } };
  }
  function update() {
    const r = calc(), out = $('#travel-result', root);
    if (!r) { out.innerHTML = `<p class="muted">Choose two different places, or enter a distance.</p>`; return; }
    out.innerHTML = `<div class="total-row"><span>${esc(r.label)}<br><small class="muted">${esc(r.sub || '')}</small></span><strong>${mass(r.grams)} CO₂e</strong></div>
      <button class="btn primary block" id="retire-trip">${retireButtonLabel(r.grams)}</button>`;
    $('#retire-trip', out).addEventListener('click', () => confirmRetirement({ grams: r.grams, kind: 'travel', label: 'Journey', note: r.label, longHaul: !!r.longHaul, travelMode: r.travelMode, lines: [{ name: r.label, grams: r.grams }], items: [r.item] }));
  }
  update();
}
