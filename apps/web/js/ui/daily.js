// Daily view: home energy and meals.
import { MEALS, TRAVEL_SOURCE } from '../data/travel.js';
import { energyGrams, mealGrams } from '../core/activities.js';
import { PN_SOURCE } from '../data/factors.js';
import { $, esc, mass } from './dom.js';
import { confirmRetirement, retireButtonLabel } from './retire.js';
import { missionHTML } from './hud.js';
import { countryQueue } from '../core/game.js';
import { world } from '../core/world.js';

export function mountDaily(root) {
  root.innerHTML = `
    <section class="panel">
      <div id="mission-daily"></div>
      <h1 class="h1">Add up a day</h1>
      <p class="lead">Add up a day, a week or a month. Meter readings are on your energy bill or app.</p>
      <form class="form" id="daily-form">
        <h2 class="h3">Home energy</h2>
        <div class="grid2">
          <div><label class="label" for="elec">Electricity (kWh)</label><input id="elec" type="number" min="0" value="8" class="num"></div>
          <div><label class="label" for="gas">Gas (kWh)</label><input id="gas" type="number" min="0" value="30" class="num"></div>
        </div>
        <h2 class="h3">Meals</h2>
        <ul class="meals">${MEALS.map(m => `<li><label for="m-${m.id}">${esc(m.label)}</label><input id="m-${m.id}" data-meal="${m.id}" type="number" min="0" value="${m.id === 'chicken' || m.id === 'veggie' ? 1 : 0}" class="num small"></li>`).join('')}</ul>
      </form>
      <div class="result" id="daily-result"></div>
      <p class="note">Energy: ${esc(TRAVEL_SOURCE)}, rounded up. Meals: built from ${esc(PN_SOURCE)}.</p>
    </section>`;
  const form = $('#daily-form', root);
  form.addEventListener('submit', e => e.preventDefault());
  form.addEventListener('input', update);
  function update() {
    const items = [];
    const e = +$('#elec').value || 0, g = +$('#gas').value || 0;
    const lines = energyGrams({ electricityKwh: e, gasKwh: g });
    if (e || g) items.push({ type: 'energy', electricityKwh: e, gasKwh: g });
    form.querySelectorAll('[data-meal]').forEach(i => {
      const n = +i.value || 0, r = mealGrams({ meal: i.dataset.meal, n });
      if (r) { lines.push({ name: r.label, grams: r.grams }); items.push({ type: 'meal', meal: i.dataset.meal, n }); }
    });
    const total = lines.reduce((s, l) => s + l.grams, 0), out = $('#daily-result', root);
    out.innerHTML = total ? `<div class="total-row"><span>${lines.length} activit${lines.length === 1 ? 'y' : 'ies'}</span><strong>${mass(total)} CO₂e</strong></div>
      <button class="btn primary block" id="retire-daily">${retireButtonLabel(total)}</button>` : `<p class="muted">Enter some activity to see its footprint.</p>`;
    $('#retire-daily', out)?.addEventListener('click', () => confirmRetirement({ grams: total, kind: 'daily', label: 'Everyday activities', lines, items }));
  }
  update();
  const mission = () => { const el = $('#mission-daily'); if (el) el.innerHTML = missionHTML(countryQueue(), world.get()); };
  mission(); document.addEventListener('carbonledger:world', mission);
}
