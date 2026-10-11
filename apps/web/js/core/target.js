// Where a user's retirements go: the Frontline (smallest country not yet cleared) or a country they choose.
import { store } from './store.js';
import { countryQueue } from './game.js';
import { COUNTRIES } from '../data/countries.js';

const byIso = new Map(COUNTRIES.map(c => [c.iso3, c]));

export const target = {
  get: () => store.get('target', { mode: 'frontline' }),
  set(t) { store.set('target', t.mode === 'chosen' && byIso.has(t.iso3) ? { mode: 'chosen', iso3: t.iso3 } : { mode: 'frontline' }); },
};

// Resolve a target to the country that receives this retirement, and whether it finishes the share.
export function resolveTarget(t, grams) {
  const q = countryQueue();
  let c = t.mode === 'chosen' ? q.byIso.get(t.iso3) : q.current;
  if (!c || c.status === 'cleared') c = q.current; // a chosen country already cleared falls back to the Frontline
  if (!c) return null;
  const need = c.tonnes * 1e6;
  return { iso3: c.iso3, name: c.name, mode: c.iso3 === q.current?.iso3 ? 'frontline' : 'chosen',
    finished: c.doneGrams < need && c.doneGrams + grams >= need, remaining: Math.max(0, need - c.doneGrams) };
}
