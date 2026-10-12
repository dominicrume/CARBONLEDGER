// Me: the command centre. Level, XP, streak, next quests, badge shelf, skill tree, league, partners, history.
// Totals come from the ledger when it is connected; a browser total is never a score.
import { ledger } from '../core/ledger.js';
import { levelFor, badgeBook } from '../core/game.js';
import { skillTree } from '../core/skills.js';
import { PARTNERS, EXAMPLE_PLAYERS } from '../data/partners.js';
import { store } from '../core/store.js';
import { $, esc, mass, toast } from './dom.js';
import { showReceipt, confirmRetirement, openVerify } from './retire.js';
import { badgeBookHTML, BADGE_ICON } from './badges.js';
import { skillTreeHTML, bindSkillTree } from './skilltree.js';
import { icon, xp, levelChip, dailyHTML, brandMark } from './hud.js';

const weeksActive = h => new Set(h.map(r => { const d = new Date(r.ts); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return +d; })).size;
const streak = h => {   // consecutive weeks ending this week with at least one retirement
  const weeks = new Set(h.map(r => { const d = new Date(r.ts); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return +d; }));
  let n = 0; const d = new Date(); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  while (weeks.has(+d)) { n++; d.setUTCDate(d.getUTCDate() - 7); }
  return n;
};

export function mountMe(root) {
  root.innerHTML = `
    <section class="panel plain" id="me-level"></section>
    <section class="panel" id="today"></section>
    <section class="panel"><h2 class="h2">${icon('target')} Next quests</h2><ul class="quests" id="quests"></ul></section>
    <section class="panel plain"><h2 class="h2">${icon('medal')} Badge shelf</h2><div class="shelf-row" id="badge-shelf" tabindex="0" role="region" aria-label="Badge shelf, scrolls sideways"></div></section>
    <section class="panel"><h2 class="h2">${icon('path')} Skill tree</h2><div id="skills"></div></section>
    <section class="panel"><h2 class="h2">${icon('trophy')} League</h2><p class="note">Example entries beside your own total from ${esc(ledger.info.source)}. A browser total is never a score.</p><ol class="league" id="league"></ol></section>
    <section class="panel">
      <h2 class="h2">${icon('hand-coins')} Partner quests</h2>
      <p class="note">Partners pay for pilot units retired in your name. These partners are examples.</p>
      <ul class="partners">${PARTNERS.map(p => `<li><div><strong>${esc(p.name)}</strong><small>${esc(p.kind)}. ${esc(p.note)}.</small></div>
        <button class="btn ghost small" data-partner="${p.id}">${esc(p.action)} <span class="xp">+${xp(p.grams)}</span></button></li>`).join('')}</ul>
    </section>
    <section class="panel"><h2 class="h2">${icon('receipt')} All badges</h2><div id="badges"></div></section>
    <section class="panel"><h2 class="h2">Your receipts</h2><ul class="history" id="history"></ul></section>
    <section class="panel">
      <form id="name-form" class="form">
        <label class="label" for="name">Your display name</label>
        <div class="row" style="margin-top:0"><input id="name" placeholder="You" maxlength="24" autocomplete="nickname"><button class="btn primary" type="submit" id="name-save">Save</button></div>
        <small>Shown in the league on this device. Not sent to the ledger.</small>
      </form>
    </section>`;
  const nameEl = $('#name', root);
  nameEl.value = store.get('name', '');
  $('#name-form', root).addEventListener('submit', (e) => {
    e.preventDefault();
    store.set('name', nameEl.value.trim());
    refreshMe();
    toast(nameEl.value.trim() ? `Saved. You are ${nameEl.value.trim()}.` : 'Saved. You show as You.');
  });
  root.querySelectorAll('[data-partner]').forEach(b => b.addEventListener('click', () => {
    const p = PARTNERS.find(x => x.id === b.dataset.partner);
    confirmRetirement({ grams: p.grams, kind: 'partner', label: 'Partner reward', note: `${p.name} reward`, paidBy: p.name, account: 'personal', lines: [{ name: p.action, grams: p.grams }], items: [{ type: 'partner', id: p.id }] }, refreshMe);
  }));
  refreshMe();
}

export function heroHTML(account, h, ctx = {}) {
  const total = h.reduce((s, r) => s + r.grams, 0);
  const base = account === 'business' ? 50_000 : 500;
  const lv = levelChip(total, base), book = badgeBook(account, ctx), s = streak(h);
  const name = account === 'business' ? (ctx.name || 'Your business') : (store.get('name', '') || 'You');
  return `<div class="hero-card">
    <div class="hero-top">
      <span class="ring big" style="--p:${lv.ring}"><b>${lv.n}</b></span>
      <div><div class="hero-title">${esc(name)}, level ${lv.n}</div><div class="hero-rank">${icon('tree-evergreen')} ${esc(lv.title)}</div>
        <div class="hero-sub">${esc(lv.toNext)}, totals from ${esc(ledger.info.source)}.</div>
        <div class="bar gold thin"><span style="width:${lv.ring}%"></span></div></div>
    </div>
    <div class="stats">
      <div class="stat-tile">${icon('leaf')}<b>${esc(mass(total))}</b><small>retired <span class="tag">Pilot units</span></small></div>
      <div class="stat-tile">${icon('fire')}<b>${s} wk</b><small>streak${s ? '' : ', retire this week to start'}</small></div>
      <div class="stat-tile">${icon('medal')}<b>${book.total}</b><small>badge${book.total === 1 ? '' : 's'}</small></div>
    </div>
  </div>`;
}

export function levelHTML(total, lv, unitNote) {
  return `<p class="eyebrow">Your level <span class="muted">(totals from ${esc(ledger.info.source)})</span></p>
    <div class="level"><span class="level-id">${lv.n}</span><div><strong>${mass(total)} CO₂e retired</strong>
      <small class="muted">${mass(lv.toNext)} to level ${lv.n + 1}</small></div></div>
    <div class="bar"><span style="width:${(lv.progress * 100).toFixed(1)}%"></span></div>
    <p class="note">Levels never run out. Each one needs a little more than the last${unitNote || ''}.</p>`;
}

export function questsHTML(account, ctx = {}) {
  const t = skillTree(account, ctx);
  if (!t.nextUp.length) return '<li class="empty">Every unlocked skill is complete. Mastery keeps going.</li>';
  return t.nextUp.map(s => `<li><button class="quest" data-skill="${s.id}">
    <strong>${esc(s.name)} ${s.endless ? `level ${s.level + 1}` : ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'][s.level] || s.level + 1}</strong>
    <span class="xp">${Math.round(s.progress * 100)}%</span>
    <small>${esc(s.need)} to go</small>
    <span class="bar thin"><span style="width:${(s.progress * 100).toFixed(0)}%"></span></span></button></li>`).join('');
}

export function shelfHTML(book) {
  return book.families.map(f => {
    const latest = f.earned.at(-1);
    return `<div class="badge-tile ${latest ? '' : 'off'}">${icon(BADGE_ICON[f.id] || 'medal')}<b>${esc(latest ? latest.name : f.name)}</b><small>${latest ? esc(f.name) : `Next: ${esc(f.nextLabel)}`}</small></div>`;
  }).join('') + book.countryBadges.slice(0, 6).map(b => `<div class="badge-tile">${icon(b.id.startsWith('cleared') ? 'crown' : 'flag')}<b>${esc(b.name)}</b><small>${b.id.startsWith('cleared') ? 'Finisher' : 'Supporter'}</small></div>`).join('');
}

// Every receipt in one list: its number, when, how much. What was bought stays inside the receipt (tap the row).
// Verify opens the public check for that receipt, so anyone can spot-check any of their history at any time.
export function historyHTML(h) {
  return h.length ? h.map(r => `<li class="hist-row"><button class="hist" data-rec="${esc(r.id)}"><span><span class="mono">${esc(r.id)}</span><small>${new Date(r.ts).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}${r.countryName ? ` · ${esc(r.countryName)}` : ''}</small></span><span class="mono">${mass(r.grams)}</span></button><button class="btn ghost small" data-verify="${esc(r.id)}" aria-label="Verify receipt ${esc(r.id)}">Verify</button></li>`).join('')
    : `<li class="empty">No retirements yet. Scan a basket or log a journey to start.</li>`;
}

export function bindHistory(el, h) {
  el.querySelectorAll('[data-rec]').forEach(b => b.addEventListener('click', () => showReceipt(h.find(r => r.id === b.dataset.rec))));
  el.querySelectorAll('[data-verify]').forEach(b => b.addEventListener('click', () => openVerify(b.dataset.verify)));
}

export function leagueHTML(entries, me) {
  return [...entries, me].sort((a, b) => b.grams - a.grams)
    .map((p, i) => `<li class="${p.you ? 'you' : ''}"><span class="rank">${i + 1}</span><span style="flex:1">${esc(p.name)}<small>${esc(p.sub || '')}</small></span><span class="mono">${mass(p.grams)}</span></li>`).join('');
}

export function refreshMe() {
  const h = ledger.history('personal'), total = h.reduce((s, r) => s + r.grams, 0);
  $('#me-level').innerHTML = heroHTML('personal', h);
  $('#today').innerHTML = dailyHTML(h);
  $('#quests').innerHTML = questsHTML('personal');
  $('#badge-shelf').innerHTML = shelfHTML(badgeBook('personal'));
  $('#skills').innerHTML = skillTreeHTML('personal'); bindSkillTree($('#skills'), 'personal'); bindSkillTree($('#quests'), 'personal');
  $('#badges').innerHTML = badgeBookHTML(badgeBook('personal'));
  const me = { name: store.get('name', '') ? `${store.get('name', '')} (you)` : 'You', grams: total, sub: 'Individuals', you: true };
  $('#league').innerHTML = leagueHTML(EXAMPLE_PLAYERS.filter(p => p.league !== 'Businesses').map(p => ({ ...p, sub: p.league })), me);
  $('#history').innerHTML = historyHTML(h);
  bindHistory($('#history'), h);
}
