// Renders a badge book: one row per family with its latest badge and progress to the next,
// then the country badges. Shared by the personal and business pages.
import { esc } from './dom.js';

export function badgeBookHTML(book) {
  const fams = book.families.map(f => {
    const latest = f.earned.at(-1);
    return `<li class="fam ${latest ? 'on' : ''}">
      <div class="fam-top"><span class="fam-name">${esc(f.name)}</span><span class="fam-count">${f.earned.length}</span></div>
      <div class="fam-latest">${latest ? esc(latest.name) : '<span class="muted">Not started</span>'}</div>
      ${f.next != null ? `<div class="bar thin"><span style="width:${(f.progress * 100).toFixed(1)}%"></span></div>
      <small>Next: ${esc(f.nextLabel)}</small>` : '<small>Complete</small>'}
    </li>`;
  }).join('');
  const cb = book.countryBadges;
  const chips = cb.slice(0, 12).map(b => `<span class="chip-badge ${b.id.startsWith('cleared') ? 'gold' : ''}">${esc(b.name)}</span>`).join('');
  return `
    <p class="badge-total"><strong>${book.total.toLocaleString('en-GB')}</strong> badge${book.total === 1 ? '' : 's'} earned. Every family keeps going, so there is always a next one.</p>
    <ul class="fams">${fams}</ul>
    <h3 class="h3">Country badges</h3>
    <div class="chips">${chips || '<span class="muted">Each country your offsets support earns a badge, and another when it is cleared.</span>'}${cb.length > 12 ? `<span class="muted">and ${cb.length - 12} more</span>` : ''}</div>`;
}
