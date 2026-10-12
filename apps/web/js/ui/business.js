// Business view: a company profile, a footprint calculator across six areas, business badges and league.
import { ledger } from '../core/ledger.js';
import { badgeBook } from '../core/game.js';
import { store } from '../core/store.js';
import { GROUND, TRAVEL_SOURCE } from '../data/travel.js';
import { FLIGHT_KM, businessEnergyGrams, businessFleetGrams, businessFlightGrams, commuteGrams, productsSoldGrams, measuredGrams } from '../core/activities.js';
import { EXAMPLE_BUSINESSES } from '../data/partners.js';
import { $, esc, mass } from './dom.js';
import { confirmRetirement, retireButtonLabel, showReceipt } from './retire.js';
import { badgeBookHTML } from './badges.js';
import { skillTreeHTML, bindSkillTree } from './skilltree.js';
import { heroHTML, historyHTML, bindHistory, questsHTML, leagueHTML } from './me.js';
import { mandateHTML, bindMandates } from './mandate.js';

const car = id => GROUND.find(g => g.id === id);

const AREAS = [
  { id: 'energy', label: 'Energy' }, { id: 'fleet', label: 'Vehicles' }, { id: 'flights', label: 'Business flights' },
  { id: 'commute', label: 'Staff commuting' }, { id: 'products', label: 'Products sold' }, { id: 'other', label: 'Other' },
];

const profile = () => store.get('biz', { name: '', employees: 10 });

export function mountBusiness(root) {
  const p = profile();
  root.innerHTML = `
    <section class="panel">
      <p class="eyebrow">For organisations</p>
      <h1 class="h1">Business</h1>
      <p class="lead">Work out your organisation's footprint for a period and retire pilot units for it. Businesses play their own league.</p>
      <div class="grid2">
        <div><label class="label" for="biz-name">Business name</label><input id="biz-name" maxlength="40" placeholder="Your business" value="${esc(p.name)}"></div>
        <div><label class="label" for="biz-emp">Employees</label><input id="biz-emp" type="number" min="1" value="${p.employees}" class="num"></div>
      </div>
    </section>
    <section class="panel">
      <h2 class="h2">Footprint for a period</h2>
      <form class="form" id="biz-form">
        <label class="label" for="b-period">Period</label>
        <select id="b-period"><option>This month</option><option>This quarter</option><option>This year</option></select>
        <h3 class="h3">Energy</h3>
        <div class="grid2">
          <div><label class="label" for="b-elec">Electricity (kWh)</label><input id="b-elec" type="number" min="0" value="2400" class="num"></div>
          <div><label class="label" for="b-gas">Gas (kWh)</label><input id="b-gas" type="number" min="0" value="3000" class="num"></div>
        </div>
        <h3 class="h3">Vehicles</h3>
        <div class="grid2">
          <div><label class="label" for="b-fleet">Fuel type</label><select id="b-fleet"><option value="diesel">Diesel</option><option value="petrol">Petrol</option><option value="ev">Electric</option></select></div>
          <div><label class="label" for="b-fleetkm">Distance (km)</label><input id="b-fleetkm" type="number" min="0" value="1500" class="num"></div>
        </div>
        <h3 class="h3">Business flights (return trips)</h3>
        <div class="grid3">
          <div><label class="label" for="b-fdom">UK</label><input id="b-fdom" type="number" min="0" value="2" class="num small"></div>
          <div><label class="label" for="b-fshort">Europe</label><input id="b-fshort" type="number" min="0" value="1" class="num small"></div>
          <div><label class="label" for="b-flong">Long-haul</label><input id="b-flong" type="number" min="0" value="0" class="num small"></div>
        </div>
        <h3 class="h3">Staff commuting</h3>
        <div class="grid2">
          <div><label class="label" for="b-cmode">Main way staff travel</label><select id="b-cmode">${GROUND.map(g => `<option value="${g.id}">${esc(g.label)}</option>`).join('')}</select></div>
          <div><label class="label" for="b-ckm">Round trip per person (km)</label><input id="b-ckm" type="number" min="0" value="20" class="num"></div>
        </div>
        <label class="label" for="b-days">Working days in the period</label><input id="b-days" type="number" min="0" value="20" class="num">
        <h3 class="h3">Products sold</h3>
        <div class="grid2">
          <div><label class="label" for="b-pg">Footprint per unit (g)</label><input id="b-pg" type="number" min="0" value="0" class="num"></div>
          <div><label class="label" for="b-pn">Units sold</label><input id="b-pn" type="number" min="0" value="0" class="num"></div>
        </div>
        <h3 class="h3">Other</h3>
        <label class="label" for="b-other">Other emissions you have measured (kg CO₂e)</label><input id="b-other" type="number" min="0" value="0" class="num">
      </form>
      <div class="result" id="biz-result"></div>
      <p class="note">Factors: ${esc(TRAVEL_SOURCE)}. Flights assume typical one-way distances of ${FLIGHT_KM.domestic} km (UK), ${FLIGHT_KM.short.toLocaleString('en-GB')} km (Europe) and ${FLIGHT_KM.long.toLocaleString('en-GB')} km (long-haul), economy class.</p>
    </section>
    <section class="panel plain" id="biz-level"></section>
    <section class="panel"><h2 class="h2">Next quests</h2><ul class="quests" id="biz-quests"></ul></section>
    <section class="panel"><h2 class="h2">Business skill tree</h2><div id="biz-skills"></div></section>
    <section class="panel"><h2 class="h2">Business badges</h2><div id="biz-badges"></div></section>
    <section class="panel"><h2 class="h2">Business league</h2><ol class="league" id="biz-league"></ol></section>
    <section class="panel"><h2 class="h2">Business receipts</h2><ul class="history" id="biz-history"></ul></section>
    <section class="panel" id="biz-mandates"><h2 class="h2">Agent mandates</h2>${mandateHTML()}</section>`;
  bindMandates($('#biz-mandates', root));

  const saveProfile = () => { store.set('biz', { name: $('#biz-name').value.trim(), employees: Math.max(1, +$('#biz-emp').value || 1) }); refreshBusiness(); };
  $('#biz-name', root).addEventListener('change', saveProfile);
  $('#biz-emp', root).addEventListener('change', saveProfile);
  const form = $('#biz-form', root);
  form.addEventListener('submit', e => e.preventDefault());
  form.addEventListener('input', update);

  // Every line carries the typed item the server recomputes it from (D1). Browser totals are a preview only.
  function lines() {
    const v = id => Math.max(0, +$(id).value || 0), out = [];
    const add = (area, name, grams, item) => { if (grams > 0) out.push({ area, name, grams, item }); };
    add('energy', `Electricity ${v('#b-elec').toLocaleString('en-GB')} kWh`, businessEnergyGrams({ electricityKwh: v('#b-elec'), gasKwh: 0 }), { type: 'energy', electricityKwh: v('#b-elec'), gasKwh: 0 });
    add('energy', `Gas ${v('#b-gas').toLocaleString('en-GB')} kWh`, businessEnergyGrams({ electricityKwh: 0, gasKwh: v('#b-gas') }), { type: 'energy', electricityKwh: 0, gasKwh: v('#b-gas') });
    const f = car($('#b-fleet').value);
    add('fleet', `${f.label}s, ${v('#b-fleetkm').toLocaleString('en-GB')} km`, businessFleetGrams({ fuel: f.id, km: v('#b-fleetkm') }), { type: 'fleet', fuel: f.id, km: v('#b-fleetkm') });
    for (const [band, id, name] of [['domestic', '#b-fdom', 'UK'], ['short', '#b-fshort', 'Europe'], ['long', '#b-flong', 'Long-haul']])
      add('flights', `${v(id)} × ${name} return flight`, businessFlightGrams({ band, n: v(id) }), { type: 'business_flights', band, n: v(id) });
    const c = car($('#b-cmode').value), emp = profile().employees;
    add('commute', `Commuting: ${emp} staff, ${v('#b-days')} days`, commuteGrams({ mode: c.id, km: v('#b-ckm'), days: v('#b-days'), employees: emp }), { type: 'commute', mode: c.id, km: v('#b-ckm'), days: v('#b-days'), employees: emp });
    add('products', `${v('#b-pn').toLocaleString('en-GB')} units sold`, productsSoldGrams({ gPerUnit: v('#b-pg'), n: v('#b-pn') }), { type: 'products_sold', gPerUnit: v('#b-pg'), n: v('#b-pn') });
    add('other', 'Other measured emissions', measuredGrams({ kg: v('#b-other') }), { type: 'measured', kg: v('#b-other') });
    return out;
  }

  function update() {
    const ls = lines(), total = ls.reduce((s, l) => s + l.grams, 0), out = $('#biz-result', root);
    const byArea = AREAS.map(a => ({ ...a, g: ls.filter(l => l.area === a.id).reduce((s, l) => s + l.grams, 0) })).filter(a => a.g);
    out.innerHTML = total ? `
      <ul class="split">${byArea.map(a => `<li><span>${a.label}</span><span class="split-bar"><span style="width:${(a.g / total * 100).toFixed(1)}%"></span></span><span class="mono">${mass(a.g)}</span></li>`).join('')}</ul>
      <div class="total-row"><span>${esc($('#b-period').value)}</span><strong>${mass(total)} CO₂e</strong></div>
      <button class="btn primary block" id="retire-biz">${retireButtonLabel(total)}</button>` : `<p class="muted">Enter some activity to see the footprint.</p>`;
    $('#retire-biz', out)?.addEventListener('click', () => confirmRetirement({
      grams: total, kind: 'business', account: 'business', label: 'Business period', note: `${profile().name || 'Business'}: ${$('#b-period').value.toLowerCase()}`,
      areas: [...new Set(ls.map(l => l.area))], lines: ls.map(({ name, grams }) => ({ name, grams })), items: ls.map(l => l.item),
    }, refreshBusiness));
  }
  update();
  refreshBusiness();
}

export function refreshBusiness() {
  const p = profile(), h = ledger.history('business'), total = h.reduce((s, r) => s + r.grams, 0);
  const ctx = { employees: p.employees, name: p.name };
  $('#biz-level').innerHTML = heroHTML('business', h, ctx);
  $('#biz-quests').innerHTML = questsHTML('business', ctx); bindSkillTree($('#biz-quests'), 'business', ctx);
  $('#biz-skills').innerHTML = skillTreeHTML('business', ctx); bindSkillTree($('#biz-skills'), 'business', ctx);
  $('#biz-badges').innerHTML = badgeBookHTML(badgeBook('business', ctx));
  const me = { name: `${p.name || 'Your business'} (you)`, grams: total, sub: `${p.employees} staff, ${mass(total / Math.max(1, p.employees))} per employee`, you: true };
  $('#biz-league').innerHTML = leagueHTML(EXAMPLE_BUSINESSES.map(b => ({ ...b, sub: `${b.employees} staff, ${mass(b.grams / b.employees)} per employee` })), me);
  $('#biz-history').innerHTML = historyHTML(h);
  bindHistory($('#biz-history'), h);
}
