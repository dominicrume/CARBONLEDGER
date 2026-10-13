// HUD: the game's shared pieces. Icons from the vendored Phosphor sprite, the level ring, the Frontline mission strip,
// the reward moment after a retirement, and a small confetti burst that stays still under reduced motion.
// XP rewards actions and habits (js/core/xp.js), never emitting more. Grams stay the shared total.
import { levelFor } from '../core/game.js';
import { LEVEL_BASE_XP } from '../core/xp.js';
import { esc, mass } from './dom.js';

export const icon = (name, cls = '') => `<svg class="ico ${cls}" aria-hidden="true"><use href="vendor/icons.svg#i-${name}-regular"/></svg>`;
export const xp = n => `${Math.round(n).toLocaleString('en-GB')} XP`;

// The brand mark (LOGO/ cropped into apps/web/brand), light and dark.
export const brandMark = (size = 40, cls = '') => `<picture class="${cls}"><source srcset="brand/mark-dark-128.png" media="(prefers-color-scheme: dark)"><img src="brand/mark-128.png" alt="" width="${size}" height="${size}" style="width:${size}px;height:${size}px"></picture>`;

// A name for every level, so a level is an identity and not only a number.
const TITLES = [[100, 'Earthkeeper'], [75, 'Guardian'], [50, 'Canopy'], [35, 'Forest'], [20, 'Grove'], [10, 'Sapling'], [5, 'Seedling'], [2, 'Sprout'], [1, 'Seed']];
export const levelTitle = n => TITLES.find(([min]) => n >= min)[1];

// Today's three quests, from this account's history. They reset at midnight and feed the weekly streak.
export function dailyQuests(h) {
  const today = new Date().toDateString();
  const t = h.filter(r => new Date(r.ts).toDateString() === today);
  const kinds = new Set(t.map(r => r.kind));
  return [
    { id: 'retire', name: 'Retire anything today', done: t.length > 0, icon: 'leaf' },
    { id: 'front', name: 'Send one to the Frontline', done: t.some(r => r.mode === 'frontline'), icon: 'target' },
    { id: 'two', name: 'Act in two different ways', done: kinds.size >= 2, icon: 'lightning', sub: `${Math.min(kinds.size, 2)} of 2` },
  ];
}

export function dailyHTML(h) {
  const q = dailyQuests(h), n = q.filter(x => x.done).length;
  return `<div class="daily-card">
    <div class="daily-head"><strong>${icon('flame')} Today</strong><span class="daily-count ${n === 3 ? 'all' : ''}">${n} of 3</span></div>
    <ul class="daily-list">${q.map(x => `<li class="${x.done ? 'done' : ''}">${icon(x.done ? 'check-circle' : x.icon)}<span>${esc(x.name)}${x.sub && !x.done ? ` <small>${esc(x.sub)}</small>` : ''}</span></li>`).join('')}</ul>
    ${n === 3 ? '<p class="daily-done">All three done. Come back tomorrow to keep the streak.</p>' : ''}
  </div>`;
}

// Count a number up to its value: feedback that the score moved. Instant under reduced motion.
export function countUp(el, to, fmt = v => Math.round(v).toLocaleString('en-GB')) {
  if (!el) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = fmt(to); return; }
  const t0 = performance.now(), d = 900;
  const step = now => { const k = Math.min(1, (now - t0) / d), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(to * e); if (k < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}

export function levelChip(totalXP, base = LEVEL_BASE_XP) {
  const lv = levelFor(totalXP, base);
  return { ...lv, ring: Math.round(Math.max(0, Math.min(1, lv.progress)) * 100), title: levelTitle(lv.n), text: `Level ${lv.n}`, toNext: `${xp(lv.toNext)} to level ${lv.n + 1}` };
}

// The Frontline strip: the smallest country still to clear, how far it is, how many players are on it.
export function missionHTML(q, world) {
  const c = q.current;
  if (!c) return `<div class="mission" role="status">${icon('trophy')}<div><div class="mission-name">Every country is cleared</div></div></div>`;
  const players = world?.countries?.[c.iso3]?.players || 0;
  const pct = Math.min(100, c.progress * 100);
  return `<button class="mission" type="button" data-mission="${esc(c.iso3)}" aria-label="The Frontline: ${esc(c.name)}, ${pct.toFixed(1)} percent cleared">
    ${icon('target')}
    <div><div class="mission-name">Frontline: ${esc(c.name)}</div>
      <div class="mission-sub">${players ? `${players} player${players === 1 ? '' : 's'} on it. ` : ''}${mass(Math.max(0, c.tonnes * 1e6 - c.doneGrams))} to go. Symbolic share.</div>
      <div class="bar thin"><span style="width:${Math.max(0.5, pct).toFixed(2)}%"></span></div></div>
    <span class="mission-pct">${pct < 10 ? pct.toFixed(1) : Math.round(pct)}%</span>
  </button>`;
}

export function confettiHTML(n = 18) {
  const colours = ['var(--gold-line)', 'var(--primary)', 'var(--warn)', 'var(--fg)'];
  let out = '<div class="confetti" aria-hidden="true">';
  for (let i = 0; i < n; i++) out += `<i style="--x:${(i * 37) % 100};--d:${(i * 53) % 400};--r:${(i * 97) % 360};--c:${colours[i % colours.length]}"></i>`;
  return out + '</div>';
}

// The reward moment: XP gained, level progress from before to after, a level-up banner, new badges, the country line.
// before and after are XP totals; grams is what was retired. Many badges at once collapse to six and a count.
export function rewardHTML({ grams, gained, before, after, badges = [], countryName, finished, base = LEVEL_BASE_XP }) {
  const a = levelFor(after, base), b = levelFor(before, base);
  // Habit and country badges lead; of the "kg retired" ladder only the highest shows, so size is not the headline.
  const kg = badges.filter(x => x.id.startsWith('retired:')), rank = x => x.id.startsWith('cleared') ? 0 : x.id.startsWith('retired:') ? 2 : 1;
  badges = [...badges.filter(x => !x.id.startsWith('retired:')), ...kg.slice(-1)].sort((x, y) => rank(x) - rank(y));
  const up = a.n > b.n, more = Math.max(0, badges.length - 6);
  badges = badges.slice(0, 6);
  const chips = badges.map((x, i) => `<span class="chip-badge ${x.id.startsWith('cleared') ? 'gold' : ''}" style="--i:${i}">${icon(x.id.startsWith('cleared') ? 'crown' : 'medal')}${esc(x.name)}</span>`).join('')
    + (more ? `<span class="chip-badge" style="--i:6">+${more} more</span>` : '');
  return `<div class="reward" data-xp="${Math.round(gained)}">
    ${up || badges.length ? confettiHTML() : ''}
    ${brandMark(36, 'reward-mark')}
    <div class="reward-xp">+<span id="reward-count">0</span> XP</div>
    <div class="reward-sub">${esc(mass(grams))} of pilot units retired${countryName ? ` for ${esc(countryName)}` : ''}</div>
    ${up ? `<div class="levelup">${icon('sparkle')} Level up! Level ${a.n}, ${esc(levelTitle(a.n))}</div>` : ''}
    <div class="bar gold"><span style="width:${(a.progress * 100).toFixed(1)}%"></span></div>
    <div class="reward-lv"><span>Level ${a.n}</span><span>${esc(xp(a.toNext))} to level ${a.n + 1}</span></div>
    ${finished ? `<div class="levelup">${icon('crown')} You finished ${esc(countryName)}'s symbolic share</div>` : ''}
    ${chips ? `<div class="new-badges">${chips}</div>` : ''}
  </div>`;
}

export function buzz() { try { if (navigator.vibrate && !matchMedia('(prefers-reduced-motion: reduce)').matches) navigator.vibrate(12); } catch {} }
