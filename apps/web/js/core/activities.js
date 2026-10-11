// Activity footprints: flights, ground travel, home energy, meals and the six business areas.
// Pure functions over the factor tables in data/travel.js. The server port (packages/core/carbonledger/activities.py)
// must reproduce every golden vector recorded from these functions by scripts/export_activities.mjs.
// Grams are whole numbers, rounded up. Nothing here reads the clock or the network.
import { FLIGHT, FLIGHT_UPLIFT, GROUND, ENERGY, MEALS, AIRPORTS, UK_AIRPORTS } from '../data/travel.js';

// Typical one-way distances when a business counts flights rather than routes (assumption, shown on screen).
export const FLIGHT_KM = { domestic: 500, short: 1800, long: 7000 };
export const SHORT_HAUL_MAX_KM = 3700;

export function km(a, b) {
  const R = 6371, r = d => d * Math.PI / 180;
  const dLat = r(b[2] - a[2]), dLon = r(b[3] - a[3]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(r(a[2])) * Math.cos(r(b[2])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function flightGrams({ from, to, cabin, ret, people }) {
  const a = AIRPORTS.find(x => x[0] === from), b = AIRPORTS.find(x => x[0] === to);
  if (!a || !b || a === b || !FLIGHT.short[cabin]) return null;
  const dist = km(a, b) * FLIGHT_UPLIFT;
  const band = UK_AIRPORTS.has(from) && UK_AIRPORTS.has(to) ? 'domestic' : dist <= SHORT_HAUL_MAX_KM ? 'short' : 'long';
  const g = Math.ceil(dist * FLIGHT[band][cabin] * 1000 * (ret ? 2 : 1) * people);
  return { grams: g, dist: Math.round(dist), band, label: `${a[1]} to ${b[1]}${ret ? ' and back' : ''}` };
}

export function groundGrams({ mode, km: dist, people }) {
  const g = GROUND.find(x => x.id === mode);
  if (!g || !(dist > 0)) return null;
  const share = g.perVehicle ? Math.max(1, people || 1) : 1;
  return { grams: Math.ceil(dist * g.perKm * 1000 / share), label: `${g.label}, ${dist} km`, share };
}

export function energyGrams({ electricityKwh, gasKwh }) {
  const lines = [];
  const e = Math.max(0, electricityKwh || 0), g = Math.max(0, gasKwh || 0);
  if (e) lines.push({ name: `Electricity ${e} kWh`, grams: Math.ceil(e * ENERGY.electricity * 1000) });
  if (g) lines.push({ name: `Gas ${g} kWh`, grams: Math.ceil(g * ENERGY.gas * 1000) });
  return lines;
}

export function mealGrams({ meal, n }) {
  const m = MEALS.find(x => x.id === meal);
  if (!m || !(n > 0)) return null;
  return { grams: Math.ceil(n * m.kg * 1000), label: `${n} × ${m.label}` };
}

// Business areas. Each returns whole grams or 0.
export function businessFleetGrams({ fuel, km: dist }) { const f = GROUND.find(x => x.id === fuel); return f && dist > 0 ? Math.ceil(dist * f.perKm * 1000) : 0; }
export function businessFlightGrams({ band, n }) { return FLIGHT_KM[band] && n > 0 ? Math.ceil(n * 2 * FLIGHT_KM[band] * FLIGHT_UPLIFT * FLIGHT[band].economy * 1000) : 0; }
export function commuteGrams({ mode, km: dist, days, employees }) { const c = GROUND.find(x => x.id === mode); return c && dist > 0 && days > 0 && employees > 0 ? Math.ceil(employees * dist * days * c.perKm * 1000) : 0; }
export function productsSoldGrams({ gPerUnit, n }) { return gPerUnit > 0 && n > 0 ? Math.ceil(gPerUnit * n) : 0; }
export function measuredGrams({ kg }) { return kg > 0 ? Math.ceil(kg * 1000) : 0; }
export function businessEnergyGrams({ electricityKwh, gasKwh }) { return energyGrams({ electricityKwh, gasKwh }).reduce((s, l) => s + l.grams, 0); }
