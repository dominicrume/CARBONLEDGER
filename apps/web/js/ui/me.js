// Me: the command centre. Level, XP, streak, next quests, badge shelf, skill tree, league, partners, history.
// Totals come from the ledger when it is connected; a browser total is never a score.
import { ledger } from '../core/ledger.js';
import { levelFor, badgeBook } from '../core/game.js';
import { skillTree } from '../core/skills.js';
import { PARTNERS } from '../data/partners.js';
import { store } from '../core/store.js';
import { $, esc, mass, toast } from './dom.js';
import { showReceipt, confirmRetirement, openVerify } from './retire.js';
import { badgeBookHTML, BADGE_ICON } from './badges.js';
import { skillTreeHTML, bindSkillTree } from './skilltree.js';
import { icon, xp, levelChip, dailyHTML, brandMark } from './hud.js';
import { xpOf, sizeXP } from '../core/xp.js';
import { account, live, track, seekerCapable, signInWithSeeker } from '../core/account.js';
import { sheet } from './dom.js';

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
    <section class="panel"><h2 class="h2">${icon('trophy')} This week's league</h2><p class="note" id="league-note">Ranked by XP from the ledger: habits, not the size of a footprint.</p><ol class="league" id="league"></ol></section>
    <section class="panel">
      <h2 class="h2">${icon('hand-coins')} Partner quests</h2>
      <p class="note">Partners pay for pilot units retired in your name. These partners are examples.</p>
      <ul class="partners">${PARTNERS.map(p => `<li><div><strong>${esc(p.name)}</strong><small>${esc(p.kind)}. ${esc(p.note)}.</small></div>
        <button class="btn ghost small" data-partner="${p.id}">${esc(p.action)} <span class="xp">+${xp(sizeXP(p.grams))}</span></button></li>`).join('')}</ul>
    </section>
    <section class="panel"><h2 class="h2">${icon('receipt')} All badges</h2><div id="badges"></div></section>
    <section class="panel"><h2 class="h2">Your receipts</h2><ul class="history" id="history"></ul></section>
    <section class="panel" id="account-panel">
      <h2 class="h2">${icon('user')} Your account</h2>
      <form id="name-form" class="form">
        <label class="label" for="name">Your public name</label>
        <div class="row" style="margin-top:0"><input id="name" placeholder="Player name" maxlength="24" autocomplete="nickname"><button class="btn primary" type="submit" id="name-save">Save</button></div>
        <small id="name-note">Shown on this week's league. Leave it empty to show as a random player name.</small>
      </form>
      <div id="signin-box"></div>
      <div class="row wrap account-links"><a href="/privacy.html">How we use your data</a><button class="link danger" id="delete-me" type="button">Delete my data</button></div>
    </section>`;
  const nameEl = $('#name', root);
  nameEl.value = store.get('name', '');
  $('#name-form', root).addEventListener('submit', (e) => {
    e.preventDefault();
    const v = nameEl.value.trim();
    store.set('name', v);
    refreshMe();
    toast(v ? `Saved. You are ${v}.` : 'Saved. You show as You.');
    if (live()) account.saveProfile({ display_name: v }).then(() => refreshMe()).catch(err => toast(`Saved on this device. The league could not take that name: ${err.message}`));
  });
  $('#delete-me', root).addEventListener('click', confirmDelete);
  root.querySelectorAll('[data-partner]').forEach(b => b.addEventListener('click', () => {
    const p = PARTNERS.find(x => x.id === b.dataset.partner);
    confirmRetirement({ grams: p.grams, kind: 'partner', label: 'Partner reward', note: `${p.name} reward`, paidBy: p.name, account: 'personal', lines: [{ name: p.action, grams: p.grams }], items: [{ type: 'partner', id: p.id }] }, refreshMe);
  }));
  refreshMe();
}

export function heroHTML(account, h, ctx = {}) {
  const total = h.reduce((s, r) => s + r.grams, 0), points = xpOf(h).total;
  const lv = levelChip(points), book = badgeBook(account, ctx), s = streak(h);
  const name = account === 'business' ? (ctx.name || 'Your business') : (store.get('name', '') || 'You');
  return `<div class="hero-card">
    <div class="hero-top">
      <span class="ring big" style="--p:${lv.ring}"><b>${lv.n}</b></span>
      <div><div class="hero-title">${esc(name)}, level ${lv.n}</div><div class="hero-rank">${icon('tree-evergreen')} ${esc(lv.title)}</div>
        <div class="hero-sub">${esc(xp(points))}, ${esc(lv.toNext)}, totals from ${esc(ledger.info.source)}. XP rewards habits, not bigger footprints.</div>
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

export function refreshMe() {
  const h = ledger.history('personal'), total = h.reduce((s, r) => s + r.grams, 0);
  $('#me-level').innerHTML = heroHTML('personal', h);
  $('#today').innerHTML = dailyHTML(h);
  $('#quests').innerHTML = questsHTML('personal');
  $('#badge-shelf').innerHTML = shelfHTML(badgeBook('personal'));
  $('#skills').innerHTML = skillTreeHTML('personal'); bindSkillTree($('#skills'), 'personal'); bindSkillTree($('#quests'), 'personal');
  $('#badges').innerHTML = badgeBookHTML(badgeBook('personal'));
  renderLeague('personal', $('#league'), $('#league-note'));
  renderAccount();
  $('#history').innerHTML = historyHTML(h);
  bindHistory($('#history'), h);
}

// ---- The weekly league, from the server: ranked by XP, public names or "Player 7F3A" ----
const day = iso => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
export async function renderLeague(board, list, note) {
  if (!list) return;
  if (!live()) { list.innerHTML = '<li class="empty">The league needs the ledger. On this device only, there is no shared score.</li>'; return; }
  try {
    const L = await account.league(board);
    if (note) note.textContent = `Week of ${day(L.season)}, ends ${day(L.ends)}. ${L.players} ${L.players === 1 ? 'player' : 'players'}. Ranked by XP from the ledger: habits, not the size of a footprint.`;
    list.innerHTML = L.entries.length ? L.entries.map(e => `<li class="${e.you ? 'you' : ''}"><span class="rank">${e.rank}</span><span style="flex:1">${esc(e.name)}${e.you ? ' (you)' : ''}${e.seeker ? ' <span class="seeker-tag">Seeker</span>' : ''}<small>${e.retirements} retirement${e.retirements === 1 ? '' : 's'}, ${esc(mass(e.grams))}</small></span><span class="mono">${esc(xp(e.xp))}</span></li>`).join('')
      : '<li class="empty">Nobody has played this week yet. Your first retirement puts you on the board.</li>';
  } catch { list.innerHTML = '<li class="empty">Could not reach the ledger for the league just now.</li>'; }
}

// ---- Account: save progress by email, the public name, delete my data ----
async function renderAccount() {
  const box = $('#signin-box'), note = $('#name-note');
  if (!box) return;
  if (!live()) { box.innerHTML = '<p class="note">Saving progress needs the ledger. This device keeps everything for now.</p>'; return; }
  let p = null;
  try { p = await account.profile(); } catch { box.innerHTML = ''; return; }
  if (note) note.textContent = `Shown on this week's league as ${p.public_name}. Leave it empty to show as a random player name.`;
  const seekerTag = p.seeker ? ` <span class="seeker-tag">${icon('seal-check')} Seeker</span>` : '';
  if (p.signed_in) { box.innerHTML = `<p class="ok signed-in">${icon('check-circle')} ${p.email ? `Progress saved to ${esc(p.email)}. Sign in on another device with the same address.` : 'Progress saved to your Solana wallet.'}${seekerTag}</p>`; return; }
  box.innerHTML = `${seekerCapable() ? `<div class="seeker-box"><button class="btn primary" id="seeker-signin" type="button">${icon('seal-check')} Sign in with Seeker</button>
      <small>Your Seeker's wallet signs one message to prove it is yours. No transaction, no payment, nothing moves. A Seeker Genesis Token earns the Seeker badge.</small>
      <p class="note" id="seeker-msg" role="status"></p></div>` : ''}<form id="signin-form" class="form">
      <label class="label" for="signin-email">Save your progress</label>
      <div class="row" style="margin-top:0"><input id="signin-email" type="email" autocomplete="email" placeholder="you@example.com" required><button class="btn ghost" type="submit">Email me a link</button></div>
      <small>One sign-in link, valid once for 15 minutes. Your scores and receipts so far come with you.</small>
      <p class="note" id="signin-msg" role="status"></p></form>`;
  $('#seeker-signin')?.addEventListener('click', async (e) => {
    const msg = $('#seeker-msg'); e.target.disabled = true; msg.textContent = 'Opening your wallet…';
    try { const d = await signInWithSeeker(); toast(d.note); await ledger.sync(); refreshMe(); }
    catch (err) { msg.textContent = err.message || 'The wallet did not sign. Nothing changed.'; e.target.disabled = false; }
  });
  $('#signin-form').addEventListener('submit', async (e) => {
    e.preventDefault(); track('signin_start');
    const msg = $('#signin-msg'); msg.textContent = 'Sending…';
    try { msg.textContent = (await account.emailLink($('#signin-email').value.trim())).note; }
    catch (err) { msg.textContent = err.message; }
  });
}

function confirmDelete() {
  sheet(`<h2 class="sheet-title">Delete my data</h2>
    <p class="lead">This deletes your email, your public name and your sign-in links, and switches off this login on every device.</p>
    <p class="note">Your receipts stay on the public ledger, because a ledger cannot forget a retirement. They hold only an id that no longer leads to you.</p>
    <p class="note" id="delete-msg" role="status"></p>
    <div class="row"><button class="btn ghost" data-close>Keep my data</button><button class="btn primary danger" id="delete-go">Delete</button></div>`,
  { onOpen: (root) => root.querySelector('#delete-go').addEventListener('click', async (e) => {
      e.target.disabled = true;
      try {
        if (live()) await account.deleteMe();
        ['apiKey', 'name', 'ledger', 'biz', 'onboarded'].forEach(k => { try { localStorage.removeItem(`carbonledger.${k}`); } catch {} });
        location.replace('/');
      } catch (err) { e.target.disabled = false; root.querySelector('#delete-msg').textContent = err.message; }
    }) });
}
