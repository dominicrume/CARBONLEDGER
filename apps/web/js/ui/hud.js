// HUD: the game's shared pieces. Icons from the vendored Phosphor sprite, the level ring, the Frontline mission strip,
// the reward moment after a retirement, and a small confetti burst that stays still under reduced motion.
// XP is grams: one gram of CO2e retired is one point, so the score and the receipt can never disagree.
import { levelFor } from '../core/game.js';
import { esc, mass } from './dom.js';

export const icon = (name, cls = '') => `<svg class="ico ${cls}" aria-hidden="true"><use href="vendor/icons.svg#i-${name}-regular"/></svg>`;
export const xp = g => `${Math.round(g).toLocaleString('en-GB')} XP`;

export function levelChip(total, base) {
  const lv = levelFor(total, base);
  return { ...lv, ring: Math.round(Math.max(0, Math.min(1, lv.progress)) * 100), text: `Level ${lv.n}`, toNext: `${mass(lv.toNext)} to level ${lv.n + 1}` };
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
export function rewardHTML({ grams, before, after, badges = [], countryName, finished, base }) {
  const a = levelFor(after, base), b = levelFor(before, base);
  const up = a.n > b.n;
  const chips = badges.map((x, i) => `<span class="chip-badge ${x.id.startsWith('cleared') ? 'gold' : ''}" style="--i:${i}">${icon(x.id.startsWith('cleared') ? 'crown' : 'medal')}${esc(x.name)}</span>`).join('');
  return `<div class="reward" data-xp="${Math.round(grams)}">
    ${up || badges.length ? confettiHTML() : ''}
    <div class="reward-xp">+${esc(xp(grams))}</div>
    <div class="reward-sub">${esc(mass(grams))} of simulated pilot units retired${countryName ? ` for ${esc(countryName)}` : ''}</div>
    ${up ? `<div class="levelup">${icon('sparkle')} Level up! You are level ${a.n}</div>` : ''}
    <div class="bar gold"><span style="width:${(a.progress * 100).toFixed(1)}%"></span></div>
    <div class="reward-lv"><span>Level ${a.n}</span><span>${esc(mass(a.toNext))} to level ${a.n + 1}</span></div>
    ${finished ? `<div class="levelup">${icon('crown')} You finished ${esc(countryName)}'s symbolic share</div>` : ''}
    ${chips ? `<div class="new-badges">${chips}</div>` : ''}
  </div>`;
}

export function buzz() { try { if (navigator.vibrate && !matchMedia('(prefers-reduced-motion: reduce)').matches) navigator.vibrate(12); } catch {} }
