// Skill tree view: Next up goals, the root, one column per branch, and the endless Mastery skill.
import { skillTree, roman, describe } from '../core/skills.js';
import { esc, sheet } from './dom.js';
import { icon } from './hud.js';

const LOCK = icon('lock-key');

function node(s) {
  const state = !s.unlocked ? 'locked' : s.maxed ? 'maxed' : s.level ? 'active' : 'open';
  const ring = state === 'locked' ? 0 : s.maxed ? 100 : (s.progress * 100).toFixed(0);
  return `<button class="skill ${state}" data-skill="${s.id}" style="--p:${ring}">
    <span class="skill-ring"><span class="skill-core">${state === 'locked' ? LOCK : s.endless ? s.level : `${roman(s.level)}`}</span></span>
    <span class="skill-name">${esc(s.name)}</span>
    <span class="skill-sub">${state === 'locked' ? 'Locked' : s.endless ? `Level ${s.level}` : `${s.level} of ${s.max}`}</span>
  </button>`;
}

export function skillTreeHTML(account, ctx) {
  const t = skillTree(account, ctx);
  const nextUp = t.nextUp.length ? t.nextUp.map(s => `<li><button class="next" data-skill="${s.id}">
      <span><strong>${esc(s.name)} ${s.endless ? `level ${s.level + 1}` : roman(s.level + 1)}</strong><small>${esc(s.need)} to go</small></span>
      <span class="bar thin"><span style="width:${(s.progress * 100).toFixed(0)}%"></span></span></button></li>`).join('')
    : '<li class="muted">Every unlocked skill is complete. Mastery keeps going.</li>';
  return `
    <div class="tree-summary"><span><strong>${t.done}</strong> of ${t.total} skill levels</span>
      <span class="bar"><span style="width:${(t.done / t.total * 100).toFixed(1)}%"></span></span></div>
    <h3 class="h3">Next up</h3><ul class="next-up">${nextUp}</ul>
    <div class="tree">
      <div class="tree-root">${node(t.root)}</div>
      <div class="tree-scroll"><div class="branches">${t.branches.map(b => `
        <div class="branch"><div class="branch-head">${esc(b.name)}<small>${b.done} of ${b.total}</small></div>
          ${b.skills.map(node).join('<span class="link-line"></span>')}</div>`).join('')}</div></div>
      <div class="tree-root mastery">${node(t.mastery)}</div>
    </div>
    <p class="note">Tap a skill to see each level. Locked skills open when the skill above them reaches level I. Swipe sideways to see every branch.</p>`;
}

export function bindSkillTree(root, account, ctx) {
  root.querySelectorAll('[data-skill]').forEach(b => b.addEventListener('click', () => {
    const t = skillTree(account, ctx);
    const s = [t.root, t.mastery, ...t.branches.flatMap(x => x.skills)].find(x => x.id === b.dataset.skill);
    if (!s) return;
    const levels = s.endless ? [] : s.levels.map((target, i) => `<li class="${s.level > i ? 'done' : ''}"><span class="lv">${roman(i + 1)}</span><span>${esc(describe(s.unit, target))}</span><span>${s.level > i ? 'Done' : ''}</span></li>`).join('');
    sheet(`
      <h2 class="sheet-title">${esc(s.name)}</h2>
      <p class="lead">${esc(s.desc)}.</p>
      ${!s.unlocked ? `<p class="locked-note">Locked. Reach level I of ${esc(s.requires)} to unlock this skill.</p>` : ''}
      <dl class="kv"><div><dt>So far</dt><dd>${esc(describe(s.unit, s.value))}</dd></div>
        ${s.next ? `<div><dt>Next level</dt><dd>${esc(describe(s.unit, s.next))} (${esc(s.need)} to go)</dd></div>` : '<div><dt>Status</dt><dd>Complete</dd></div>'}</dl>
      ${levels ? `<ol class="levels">${levels}</ol>` : `<p class="note">Mastery has no final level. Each one asks for a little more: 1, 2, 5, 10, 20, 50 and so on.</p>`}
      <div class="row"><button class="btn primary" data-close>Close</button></div>`);
  }));
}
