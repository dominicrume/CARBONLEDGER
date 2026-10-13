// Levels, badges and the country queue.
// Badges come in families. Each family measures one thing and has an endless ladder of milestones,
// so there is always a next badge to earn. Country badges add one per country supported or cleared.
import { COUNTRIES } from '../data/countries.js';
import { ledger } from './ledger.js';
import { settings } from './settings.js';
import { mass } from '../ui/dom.js';

// ---- Ladders: endless milestone sequences ----
// 1, 2, 5, 10, 20, 50, ... times a starting unit
export function* ladder125(start = 1) { for (let p = start; ; p *= 10) { yield p; yield 2 * p; yield 5 * p; } }
// 1, 3, 5, 10, 25, 50, 100, 250, 500, 1000, ...
export function* ladderCount() { yield 1; yield 3; yield 5; for (let p = 10; ; p *= 10) { yield p; yield 2.5 * p; yield 5 * p; } }

function climb(gen, value) {
  const earned = [];
  for (const m of gen) { if (m > value) return { earned, next: m }; earned.push(m); }
}

// ---- Levels: endless, each a little further than the last ----
// Level n needs base × (n-1)^2.2 points. Called with XP (js/core/xp.js, base 80): level 2 at 80 XP, level 10 at about 10,000 XP.
export function levelFor(grams, base = 500) {
  const need = n => Math.round(base * Math.pow(n - 1, 2.2));
  let n = Math.max(1, Math.floor(Math.pow(grams / base, 1 / 2.2)) + 1);
  while (need(n + 1) <= grams) n++;
  while (n > 1 && need(n) > grams) n--;
  const lo = need(n), hi = need(n + 1);
  return { n, next: hi, toNext: hi - grams, progress: (grams - lo) / (hi - lo) };
}

// ---- Metrics ----
const sum = h => h.reduce((s, r) => s + r.grams, 0);
const count = (h, kind) => h.filter(r => !kind || r.kind === kind).length;
const weeks = h => new Set(h.map(r => { const d = new Date(r.ts); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return +d; })).size;
const months = h => new Set(h.map(r => r.ts.slice(0, 7))).size;
const products = h => new Set(h.flatMap(r => r.codes || [])).size;
const countries = h => new Set(h.map(r => r.countryIso3).filter(Boolean)).size;
const pl = (n, w) => `${n.toLocaleString('en-GB')} ${w}${n === 1 ? '' : 's'}`;

export const FAMILIES = {
  personal: [
    { id: 'retired', name: 'Carbon retired', metric: sum, ladder: () => ladder125(1000), label: v => `${mass(v)} retired`, fmt: mass },
    { id: 'retirements', name: 'Retirements made', metric: h => count(h), ladder: ladderCount, label: v => pl(v, 'retirement') },
    { id: 'baskets', name: 'Shopping baskets', metric: h => count(h, 'shop'), ladder: ladderCount, label: v => pl(v, 'basket') },
    { id: 'products', name: 'Different products', metric: products, ladder: ladderCount, label: v => pl(v, 'product') },
    { id: 'journeys', name: 'Journeys', metric: h => count(h, 'travel'), ladder: ladderCount, label: v => pl(v, 'journey') },
    { id: 'everyday', name: 'Everyday life', metric: h => count(h, 'daily'), ladder: ladderCount, label: v => pl(v, 'day') + ' logged' },
    { id: 'partners', name: 'Partner rewards', metric: h => count(h, 'partner'), ladder: ladderCount, label: v => pl(v, 'reward') },
    { id: 'weeks', name: 'Active weeks', metric: weeks, ladder: ladderCount, label: v => pl(v, 'week') },
    { id: 'frontline', name: 'Frontline retirements', metric: h => h.filter(r => r.mode === 'frontline').length, ladder: ladderCount, label: v => pl(v, 'Frontline retirement') },
    { id: 'finisher', name: 'Countries finished', metric: h => h.filter(r => r.finished).length, ladder: ladderCount, label: v => `Finished ${pl(v, 'country').replace('countrys', 'countries')}` },
    { id: 'countries', name: 'Countries supported', metric: countries, ladder: ladderCount, label: v => pl(v, 'country').replace('countrys', 'countries') },
  ],
  business: [
    { id: 'b-retired', name: 'Carbon retired', metric: sum, ladder: () => ladder125(100_000), label: v => `${mass(v)} retired`, fmt: mass },
    { id: 'b-retirements', name: 'Retirements made', metric: h => count(h), ladder: ladderCount, label: v => pl(v, 'retirement') },
    { id: 'b-per-head', name: 'Retired per employee', metric: (h, ctx) => sum(h) / Math.max(1, ctx.employees || 1), ladder: () => ladder125(1000), label: v => `${mass(v)} per employee`, fmt: mass },
    { id: 'b-months', name: 'Active months', metric: months, ladder: ladderCount, label: v => pl(v, 'month') },
    { id: 'b-areas', name: 'Areas covered', metric: h => new Set(h.flatMap(r => r.areas || [])).size, ladder: function* () { for (let i = 1; i <= 6; i++) yield i; }, label: v => v === 6 ? 'Every area covered' : pl(v, 'area') },
    { id: 'b-frontline', name: 'Frontline retirements', metric: h => h.filter(r => r.mode === 'frontline').length, ladder: ladderCount, label: v => pl(v, 'Frontline retirement') },
    { id: 'b-finisher', name: 'Countries finished', metric: h => h.filter(r => r.finished).length, ladder: ladderCount, label: v => `Finished ${pl(v, 'country').replace('countrys', 'countries')}` },
    { id: 'b-countries', name: 'Countries supported', metric: countries, ladder: ladderCount, label: v => pl(v, 'country').replace('countrys', 'countries') },
  ],
};

// Every badge earned, plus the next milestone in each family.
export function badgeBook(account = 'personal', ctx = {}) {
  const h = ledger.history(account);
  const fams = FAMILIES[account].map(f => {
    const v = f.metric(h, ctx), { earned, next } = climb(f.ladder(), v);
    return { ...f, value: v, earned: earned.map(m => ({ id: `${f.id}:${m}`, name: f.label(m) })), next, nextLabel: next != null ? f.label(next) : null,
      progress: next ? Math.min(1, v / next) : 1 };
  });
  // One badge per country supported, and one per supported country that has since been cleared.
  const q = countryQueue();
  const cleared = new Set(q.cleared.map(c => c.iso3));
  const supported = [...new Map(h.filter(r => r.countryIso3).map(r => [r.countryIso3, r.countryName])).entries()];
  const countryBadges = [
    ...supported.map(([iso, name]) => ({ id: `supporter:${iso}`, name: `Supporter of ${name}` })),
    ...supported.filter(([iso]) => cleared.has(iso)).map(([iso, name]) => ({ id: `cleared:${iso}`, name: `Helped clear ${name}` })),
  ];
  const all = [...fams.flatMap(f => f.earned), ...countryBadges];
  return { families: fams, countryBadges, all, total: all.length };
}

// ---- Countries ----
// Each country's progress = retirements directed to it + its part of the simulated community total.
// The simulated total always goes to the Frontline: the smallest country not yet cleared.
// status: 'cleared' | 'front' (Frontline, in progress) | 'supported' (some progress) | 'waiting'
// Totals by country from the whole ledger (every player), set by core/world.js. Null = use this device's history.
let WORLD = null;
export function setWorldTotals(totals) { WORLD = totals; }

// On the live ledger only real retirements count; the community total is a what-if for the device-only demo.
export function countryQueue(extraTonnes = WORLD ? 0 : settings.communityTonnes(), history = ledger.history()) {
  const direct = new Map();
  if (WORLD) for (const [iso, g] of Object.entries(WORLD)) direct.set(iso, g);
  else for (const r of history) if (r.countryIso3) direct.set(r.countryIso3, (direct.get(r.countryIso3) || 0) + r.grams);
  let pool = extraTonnes * 1e6;
  const byIso = new Map(), cleared = [], rest = [];
  let current = null;
  for (const c of COUNTRIES) {
    const need = c.tonnes * 1e6;
    let done = direct.get(c.iso3) || 0;
    if (!current) { const take = Math.min(pool, Math.max(0, need - done)); pool -= take; done += take; }
    const status = done >= need ? 'cleared' : !current ? 'front' : done > 0 ? 'supported' : 'waiting';
    const rec = { ...c, doneGrams: done, progress: Math.min(1, done / need), status };
    byIso.set(c.iso3, rec);
    if (status === 'cleared') cleared.push(rec); else if (status === 'front') current = rec; else rest.push(rec);
  }
  return { cleared, current, rest, byIso, totalCountries: COUNTRIES.length };
}

export const currentCountry = () => countryQueue().current;
