// Me view: level, badges, league, partner rewards and history for a personal account.
import { ledger } from '../core/ledger.js';
import { levelFor, badgeBook } from '../core/game.js';
import { PARTNERS, EXAMPLE_PLAYERS } from '../data/partners.js';
import { store } from '../core/store.js';
import { $, esc, mass } from './dom.js';
import { showReceipt, confirmRetirement } from './retire.js';
import { badgeBookHTML } from './badges.js';
import { skillTreeHTML, bindSkillTree } from './skilltree.js';

export function mountMe(root) {
  root.innerHTML = `
    <section class="panel" id="me-level"></section>
    <section class="panel"><h2 class="h2">Skill tree</h2><div id="skills"></div></section>
    <section class="panel"><h2 class="h2">Badges</h2><div id="badges"></div></section>
    <section class="panel"><h2 class="h2">League</h2><ol class="league" id="league"></ol></section>
    <section class="panel">
      <h2 class="h2">Earn with partners</h2>
      <p class="note">Partners pay for simulated pilot units retired in your name. These partners are examples.</p>
      <ul class="partners">${PARTNERS.map(p => `<li><div><strong>${esc(p.name)}</strong><small>${esc(p.kind)}. ${esc(p.note)}.</small></div>
        <button class="btn ghost small" data-partner="${p.id}">${esc(p.action)}: earn ${mass(p.grams)}</button></li>`).join('')}</ul>
    </section>
    <section class="panel"><h2 class="h2">History</h2><ul class="history" id="history"></ul></section>
    <section class="panel">
      <div class="row"><label class="label inline" for="name">Your display name</label><input id="name" placeholder="You" maxlength="24"></div>
    </section>`;
  const nameEl = $('#name', root);
  nameEl.value = store.get('name', '');
  nameEl.addEventListener('change', () => { store.set('name', nameEl.value.trim()); refreshMe(); });
  root.querySelectorAll('[data-partner]').forEach(b => b.addEventListener('click', () => {
    const p = PARTNERS.find(x => x.id === b.dataset.partner);
    confirmRetirement({ grams: p.grams, kind: 'partner', label: 'Partner reward', note: `${p.name} reward`, paidBy: p.name, account: 'personal', lines: [{ name: p.action, grams: p.grams }], items: [{ type: 'partner', id: p.id }] }, refreshMe);
  }));
  refreshMe();
}

export function levelHTML(total, lv, unitNote) {
  return `<p class="eyebrow">Your level</p>
    <div class="level"><span class="level-id">${lv.n}</span><div><strong>${mass(total)} CO₂e retired</strong>
      <small class="muted">${mass(lv.toNext)} to level ${lv.n + 1}</small></div></div>
    <div class="bar"><span style="width:${(lv.progress * 100).toFixed(1)}%"></span></div>
    <p class="note">Levels never run out. Each one needs a little more than the last${unitNote || ''}.</p>`;
}

export function historyHTML(h) {
  return h.length ? h.map(r => `<li><button class="hist" data-rec="${r.id}"><span>${esc(r.note || r.label)}<small>${new Date(r.ts).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })} · ${esc(r.countryName || '')}</small></span><span>${mass(r.grams)}</span></button></li>`).join('')
    : `<li class="empty">No retirements yet.</li>`;
}

export function refreshMe() {
  const h = ledger.history('personal'), total = h.reduce((s, r) => s + r.grams, 0);
  $('#me-level').innerHTML = levelHTML(total, levelFor(total));
  $('#skills').innerHTML = skillTreeHTML('personal'); bindSkillTree($('#skills'), 'personal');
  $('#badges').innerHTML = badgeBookHTML(badgeBook('personal'));
  const me = { name: store.get('name', '') ? `${store.get('name', '')} (you)` : 'You', grams: total, league: 'Individuals', you: true };
  $('#league').innerHTML = [...EXAMPLE_PLAYERS.filter(p => p.league !== 'Businesses'), me].sort((a, b) => b.grams - a.grams)
    .map(p => `<li class="${p.you ? 'you' : ''}"><span>${esc(p.name)}<small>${esc(p.league)}</small></span><span>${mass(p.grams)}</span></li>`).join('');
  $('#history').innerHTML = historyHTML(h);
  $('#history').querySelectorAll('[data-rec]').forEach(b => b.addEventListener('click', () => showReceipt(h.find(r => r.id === b.dataset.rec))));
}
