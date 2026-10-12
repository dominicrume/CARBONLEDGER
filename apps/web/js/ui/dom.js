// Small shared UI helpers.
export const $ = (sel, root = document) => root.querySelector(sel);
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function mass(grams) {
  if (grams >= 1e12) return tonnes(grams / 1e6);
  if (grams < 1000) return `${Math.round(grams).toLocaleString('en-GB')} g`;
  if (grams < 1e6) return `${(grams / 1000).toLocaleString('en-GB', { maximumFractionDigits: grams < 1e4 ? 2 : 1 })} kg`;
  return `${(grams / 1e6).toLocaleString('en-GB', { maximumFractionDigits: 2 })} t`;
}
const n1 = v => v.toLocaleString('en-GB', { maximumFractionDigits: 1 });
export const tonnes = t => t >= 1e9 ? `${n1(t / 1e9)} billion t` : t >= 1e6 ? `${n1(t / 1e6)} million t` : `${Math.round(t).toLocaleString('en-GB')} t`;
export const gbp = v => `£${v.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

let toastTimer;
export function toast(msg) {
  const t = $('#toast');
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
}

// In-page dialog (the artifact viewer blocks alert/confirm).
export function sheet(html, { onOpen } = {}) {
  const root = $('#sheet');
  root.innerHTML = `<div class="sheet-scrim" data-close></div><div class="sheet-body" role="dialog" aria-modal="true">${html}</div>`;
  root.hidden = false;
  const back = document.activeElement;
  const onKey = e => { if (e.key === 'Escape') close(); };
  const close = () => { root.hidden = true; root.innerHTML = ''; document.removeEventListener('keydown', onKey); try { back?.focus?.({ preventScroll: true }); } catch {} };
  document.addEventListener('keydown', onKey);
  root.querySelectorAll('[data-close]').forEach(el => el.addEventListener('click', close));
  onOpen?.(root, close);
  root.querySelector('.sheet-body button, .sheet-body input, .sheet-body select, .sheet-body a')?.focus({ preventScroll: true });
  return close;
}
