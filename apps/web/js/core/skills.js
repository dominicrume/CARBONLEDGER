// Skill trees. Each skill has levels with a target; a skill unlocks when the one before it in its
// branch reaches level 1 (the first skill of each branch needs the root). Mastery has no last level.
import { ledger } from './ledger.js';
import { ladder125 } from './game.js';
import { mass } from '../ui/dom.js';

const GREEN = new Set(['rail', 'bus', 'coach', 'ferry', 'ev']);
const sum = h => h.reduce((s, r) => s + r.grams, 0);
const n = (h, f) => h.filter(f).length;
const weeks = h => new Set(h.map(r => { const d = new Date(r.ts); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return +d; })).size;
const months = h => new Set(h.map(r => r.ts.slice(0, 7))).size;
const maxTo = h => { const m = new Map(); h.filter(r => r.mode === 'chosen').forEach(r => m.set(r.countryIso3, (m.get(r.countryIso3) || 0) + r.grams)); return Math.max(0, ...m.values()); };
const hasArea = a => h => n(h, r => (r.areas || []).includes(a));
const kg = v => v * 1000;

// unit: noun for counts, or 'g' for masses. levels: targets for each level.
const TREES = {
  personal: {
    root: { id: 'start', name: 'First steps', desc: 'Make your first offset', metric: h => h.length, unit: 'offset', levels: [1] },
    branches: [
      { id: 'shop', name: 'Shopper', skills: [
        { id: 'baskets', name: 'Basket', desc: 'Offset shopping baskets', metric: h => n(h, r => r.kind === 'shop'), unit: 'basket', levels: [1, 5, 25, 100, 500] },
        { id: 'big', name: 'Big shop', desc: 'Offset a single basket with many items', metric: h => Math.max(0, ...h.map(r => r.itemCount || 0)), unit: 'item in one basket', levels: [10, 25, 50] },
        { id: 'variety', name: 'Variety', desc: 'Offset different products', metric: h => new Set(h.flatMap(r => r.codes || [])).size, unit: 'different product', levels: [5, 25, 100, 250, 1000] },
      ] },
      { id: 'travel', name: 'Traveller', skills: [
        { id: 'journeys', name: 'Journeys', desc: 'Offset journeys', metric: h => n(h, r => r.kind === 'travel'), unit: 'journey', levels: [1, 5, 25, 100] },
        { id: 'green', name: 'Low-carbon travel', desc: 'Offset train, bus, coach, ferry or electric car trips', metric: h => n(h, r => GREEN.has(r.travelMode)), unit: 'low-carbon trip', levels: [1, 5, 25, 100] },
        { id: 'long', name: 'Long haul', desc: 'Offset long-haul flights', metric: h => n(h, r => r.longHaul), unit: 'long-haul flight', levels: [1, 3, 10] },
      ] },
      { id: 'daily', name: 'Everyday', skills: [
        { id: 'days', name: 'Everyday', desc: 'Offset everyday activities', metric: h => n(h, r => r.kind === 'daily'), unit: 'day logged', levels: [1, 7, 30, 100, 365] },
        { id: 'habit', name: 'Habit', desc: 'Offset in different weeks', metric: weeks, unit: 'active week', levels: [2, 4, 12, 26, 52] },
      ] },
      { id: 'front', name: 'Frontline', skills: [
        { id: 'frontline', name: 'Frontline', desc: 'Send offsets to the Frontline, the smallest country still to clear', metric: h => n(h, r => r.mode === 'frontline'), unit: 'Frontline offset', levels: [1, 5, 25, 100, 500] },
        { id: 'lifter', name: 'Heavy lifter', desc: 'Retire carbon at the Frontline', metric: h => sum(h.filter(r => r.mode === 'frontline')), unit: 'g', levels: [kg(1), kg(10), kg(100), kg(1000), kg(10000)] },
        { id: 'finisher', name: 'Finisher', desc: 'Make the offset that clears a country', metric: h => n(h, r => r.finished), unit: 'country finished', levels: [1, 3, 10, 25] },
      ] },
      { id: 'explore', name: 'Explorer', skills: [
        { id: 'supporter', name: 'Supporter', desc: 'Support different countries', metric: h => new Set(h.map(r => r.countryIso3).filter(Boolean)).size, unit: 'country', levels: [1, 3, 10, 25, 50, 100, 193] },
        { id: 'champion', name: 'Champion', desc: 'Retire carbon for one country you chose', metric: maxTo, unit: 'g', levels: [kg(1), kg(10), kg(100), kg(1000)] },
      ] },
      { id: 'partner', name: 'Partners', skills: [
        { id: 'rewards', name: 'Rewarded', desc: 'Earn grams through partners', metric: h => n(h, r => r.kind === 'partner'), unit: 'reward', levels: [1, 5, 25, 100] },
      ] },
    ],
    mastery: { id: 'mastery', name: 'Mastery', desc: 'Total carbon retired. This skill never ends.', metric: sum, unit: 'g', start: 1000 },
  },
  business: {
    root: { id: 'b-start', name: 'First steps', desc: 'Make your first business offset', metric: h => h.length, unit: 'offset', levels: [1] },
    branches: [
      { id: 'ops', name: 'Operations', skills: [
        { id: 'b-energy', name: 'Energy', desc: 'Offset energy use', metric: hasArea('energy'), unit: 'period', levels: [1, 3, 6, 12, 24] },
        { id: 'b-fleet', name: 'Vehicles', desc: 'Offset vehicle use', metric: hasArea('fleet'), unit: 'period', levels: [1, 3, 6, 12, 24] },
        { id: 'b-cover', name: 'Full coverage', desc: 'Cover different areas of the business', metric: h => new Set(h.flatMap(r => r.areas || [])).size, unit: 'area', levels: [2, 3, 4, 5, 6] },
      ] },
      { id: 'people', name: 'People', skills: [
        { id: 'b-commute', name: 'Commuting', desc: 'Offset staff commuting', metric: hasArea('commute'), unit: 'period', levels: [1, 3, 6, 12, 24] },
        { id: 'b-flights', name: 'Business travel', desc: 'Offset business flights', metric: hasArea('flights'), unit: 'period', levels: [1, 3, 6, 12, 24] },
        { id: 'b-head', name: 'Per head', desc: 'Retire carbon per employee', metric: (h, ctx) => sum(h) / Math.max(1, ctx.employees || 1), unit: 'g', levels: [kg(10), kg(50), kg(100), kg(500), kg(1000)] },
      ] },
      { id: 'products', name: 'Products', skills: [
        { id: 'b-products', name: 'Products', desc: 'Offset products sold', metric: hasArea('products'), unit: 'period', levels: [1, 3, 6, 12, 24] },
        { id: 'b-months', name: 'Consistency', desc: 'Offset in different months', metric: months, unit: 'active month', levels: [2, 6, 12, 24, 60] },
      ] },
      { id: 'front', name: 'Frontline', skills: [
        { id: 'b-frontline', name: 'Frontline', desc: 'Send offsets to the Frontline', metric: h => n(h, r => r.mode === 'frontline'), unit: 'Frontline offset', levels: [1, 5, 25, 100] },
        { id: 'b-finisher', name: 'Finisher', desc: 'Make the offset that clears a country', metric: h => n(h, r => r.finished), unit: 'country finished', levels: [1, 3, 10, 25] },
      ] },
    ],
    mastery: { id: 'b-mastery', name: 'Mastery', desc: 'Total carbon retired. This skill never ends.', metric: sum, unit: 'g', start: 100_000 },
  },
};

const ROMAN = ['0', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
export const roman = i => ROMAN[i] || String(i);

const PLURAL = { 'item in one basket': 'items in one basket', 'different product': 'different products', 'day logged': 'days logged',
  'country finished': 'countries finished', country: 'countries', 'low-carbon trip': 'low-carbon trips', 'long-haul flight': 'long-haul flights' };
export function describe(unit, v) {
  if (unit === 'g') return mass(v);
  const r = Math.round(v * 10) / 10;
  return `${r.toLocaleString('en-GB')} ${r === 1 ? unit : PLURAL[unit] || unit + 's'}`;
}

function evaluate(s, h, ctx, unlocked) {
  const value = s.metric(h, ctx);
  const level = s.levels.filter(t => value >= t).length;
  const next = s.levels[level];
  const prev = level ? s.levels[level - 1] : 0;
  return { ...s, value, level, max: s.levels.length, next, unlocked, maxed: level === s.levels.length,
    progress: next ? Math.max(0, Math.min(1, (value - prev) / (next - prev))) : 1,
    need: next ? describe(s.unit, next - value) : null };
}

export function skillTree(account = 'personal', ctx = {}) {
  const t = TREES[account], h = ledger.history(account);
  const root = evaluate(t.root, h, ctx, true);
  const branches = t.branches.map(b => {
    let open = root.level > 0;
    const skills = b.skills.map(s => { const e = evaluate(s, h, ctx, open); e.requires = open ? null : (b.skills[b.skills.indexOf(s) - 1]?.name || root.name); open = open && e.level > 0; return e; });
    return { ...b, skills, done: skills.reduce((x, s) => x + s.level, 0), total: skills.reduce((x, s) => x + s.max, 0) };
  });
  // Mastery: endless 1-2-5 ladder of total carbon retired.
  const m = t.mastery, v = m.metric(h, ctx);
  let level = 0, next = 0, prev = 0;
  for (const step of ladder125(m.start)) { if (v >= step) { level++; prev = step; } else { next = step; break; } }
  const mastery = { ...m, value: v, level, next, unlocked: root.level > 0, progress: (v - prev) / (next - prev), need: describe('g', next - v), endless: true };
  const all = branches.flatMap(b => b.skills);
  const done = all.reduce((x, s) => x + s.level, 0) + root.level, total = all.reduce((x, s) => x + s.max, 0) + root.max;
  // Next up: unlocked skills not yet maxed, closest to their next level first.
  const nextUp = [root, ...all, mastery].filter(s => s.unlocked && !s.maxed && s.next).sort((a, b) => b.progress - a.progress).slice(0, 3);
  return { root, branches, mastery, done, total, nextUp };
}
