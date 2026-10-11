// Exports the activity factor tables, the partner rewards and the product catalogue as JSON, and records golden
// vectors from the app's OWN activity functions. packages/core/carbonledger/activities.py must reproduce every
// vector exactly (tests/test_activity_parity.py). Run: node scripts/export_activities.mjs
import { writeFileSync } from 'node:fs';
import * as T from '../apps/web/js/data/travel.js';
import { PARTNERS } from '../apps/web/js/data/partners.js';
import { PRODUCTS } from '../apps/web/js/data/products.js';
import * as A from '../apps/web/js/core/activities.js';

writeFileSync('packages/core/carbonledger/data_activities.json', JSON.stringify({
  FLIGHT: T.FLIGHT, FLIGHT_UPLIFT: T.FLIGHT_UPLIFT, GROUND: T.GROUND, ENERGY: T.ENERGY, MEALS: T.MEALS, AIRPORTS: T.AIRPORTS,
  UK_AIRPORTS: [...T.UK_AIRPORTS], FLIGHT_KM: A.FLIGHT_KM, SHORT_HAUL_MAX_KM: A.SHORT_HAUL_MAX_KM, TRAVEL_SOURCE: T.TRAVEL_SOURCE,
  PARTNERS: PARTNERS.map(p => ({ id: p.id, name: p.name, grams: p.grams })),
}, null, 1));
writeFileSync('packages/core/carbonledger/data_products.json', JSON.stringify(PRODUCTS.map(p => ({
  code: p.code, name: p.name, grams: p.grams ?? null, cats: p.cats || [], agribalyseKgPerKg: p.agribalyseKgPerKg ?? null, hint: p.hint || '' })), null, 0));

const V = [];
const codes = T.AIRPORTS.map(a => a[0]);
for (const from of ['LHR', 'MAN', 'EDI', 'DUB', 'JFK', 'SYD', 'NBO'])
  for (const to of codes)
    for (const cabin of ['economy', 'business'])
      for (const [ret, people] of [[false, 1], [true, 1], [true, 3]])
        V.push({ fn: 'flight', in: { from, to, cabin, ret, people }, out: A.flightGrams({ from, to, cabin, ret, people }) });
V.push({ fn: 'flight', in: { from: 'LHR', to: 'XXX', cabin: 'economy', ret: false, people: 1 }, out: null });
V.push({ fn: 'flight', in: { from: 'LHR', to: 'LGW', cabin: 'first', ret: false, people: 1 }, out: null });
for (const g of T.GROUND) for (const km of [0, 1, 25, 300.5, 12000]) for (const people of [1, 2, 5])
  V.push({ fn: 'ground', in: { mode: g.id, km, people }, out: A.groundGrams({ mode: g.id, km, people }) });
V.push({ fn: 'ground', in: { mode: 'rocket', km: 10, people: 1 }, out: null });
for (const [e, g] of [[0, 0], [8, 30], [2400, 3000], [0.5, 0], [1e6, 1e6], [-5, 10]])
  V.push({ fn: 'energy', in: { electricityKwh: e, gasKwh: g }, out: A.energyGrams({ electricityKwh: e, gasKwh: g }) });
for (const m of T.MEALS) for (const n of [0, 1, 3, 10])
  V.push({ fn: 'meal', in: { meal: m.id, n }, out: A.mealGrams({ meal: m.id, n }) });
V.push({ fn: 'meal', in: { meal: 'cake', n: 1 }, out: null });
for (const fuel of ['diesel', 'petrol', 'ev', 'rail']) for (const km of [0, 1500, 99999])
  V.push({ fn: 'fleet', in: { fuel, km }, out: A.businessFleetGrams({ fuel, km }) });
for (const band of ['domestic', 'short', 'long', 'orbit']) for (const n of [0, 1, 2, 40])
  V.push({ fn: 'business_flights', in: { band, n }, out: A.businessFlightGrams({ band, n }) });
for (const mode of ['petrol', 'rail', 'bus']) for (const [km, days, employees] of [[20, 20, 10], [0, 20, 10], [5, 1, 1], [300, 250, 2000]])
  V.push({ fn: 'commute', in: { mode, km, days, employees }, out: A.commuteGrams({ mode, km, days, employees }) });
for (const [gPerUnit, n] of [[0, 0], [250, 1000], [0.5, 3], [99999, 99999]])
  V.push({ fn: 'products_sold', in: { gPerUnit, n }, out: A.productsSoldGrams({ gPerUnit, n }) });
for (const kg of [0, 1.234, 1000000, -1])
  V.push({ fn: 'measured', in: { kg }, out: A.measuredGrams({ kg }) });
writeFileSync('conformance/activity_vectors.json', JSON.stringify(V));
console.log('activities, products, partners and', V.length, 'activity vectors written');
