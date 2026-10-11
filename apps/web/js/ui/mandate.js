// Mandate screen (FLOWS 7, KYA): a business sets a cap, allowed projects, expiry and the agent's public key; sees
// used against cap; revokes at any time. The browser shows and asks. The API decides. Needs a business API key.
import { CONFIG } from '../config.js';
import { apiHeaders, apiKey } from '../core/ledger.js';
import { $, esc, mass } from './dom.js';

const WORDS = {
  OVER_CAP: 'The request would pass the cap.', EXPIRED: 'The mandate has expired.', REVOKED: 'The mandate was revoked.',
  WRONG_AGENT: 'A different agent key signed the request.', PROJECT_NOT_ALLOWED: 'The project is not on the allow-list.',
  BAD_AMOUNT: 'The amount was not a whole number above zero.', NO_SIGNATURE: 'The request was not signed.',
  BAD_SIGNATURE: 'The signature did not match the agent key and the request.', EXPIRED_SIGNATURE: 'The signature was too old (a replay or a slow clock).',
};
export const refusalWords = code => WORDS[code] || code;

const api = (path, opts = {}) => fetch(`${CONFIG.api.baseUrl}${path}`, { headers: apiHeaders(), signal: AbortSignal.timeout(CONFIG.api.timeoutMs), ...opts });
const when = ts => new Date(ts * 1000).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });

export function mandateHTML() {
  return `
    <p class="note">An agent may retire on your behalf only inside a mandate you set here: a cap in grams, an expiry, the projects it may use,
      and the agent's public key. The agent signs every request with that key. You can revoke at any time. Refusals are named in plain words.</p>
    ${CONFIG.ledger !== 'solana-devnet' ? '<p class="note">Mandates live on the ledger. Open the app with the ledger mode and a business API key to use them.</p>' : ''}
    <form id="mandate-form" class="form" ${CONFIG.ledger !== 'solana-devnet' ? 'hidden' : ''}>
      <label class="label" for="m-agent">Agent public key (base58 ed25519)</label>
      <input id="m-agent" autocomplete="off" spellcheck="false" minlength="32" maxlength="44" required placeholder="The agent's public key, never a name">
      <div class="grid2">
        <div><label class="label" for="m-cap">Cap (kg CO₂e)</label><input id="m-cap" type="number" min="0.001" step="any" value="1000" class="num" required></div>
        <div><label class="label" for="m-days">Expires in (days)</label><input id="m-days" type="number" min="1" max="365" value="30" class="num" required></div>
      </div>
      <label class="label" for="m-projects">Allowed projects (comma separated, blank for any)</label>
      <input id="m-projects" autocomplete="off" placeholder="demo-pilot-1">
      <p class="note bad" id="mandate-error" role="alert"></p>
      <div class="row"><button class="btn primary" type="submit" id="mandate-create">Create mandate</button></div>
    </form>
    <h3 class="h3">Your mandates</h3>
    <ul class="history" id="mandate-list"><li class="empty">Loading…</li></ul>`;
}

export function bindMandates(root) {
  const form = $('#mandate-form', root);
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const err = $('#mandate-error', root); err.textContent = '';
    const body = { agent: $('#m-agent', root).value.trim(), cap_g: Math.ceil((+$('#m-cap', root).value || 0) * 1000),
      ttl_seconds: Math.round((+$('#m-days', root).value || 0) * 86400) };
    const projects = $('#m-projects', root).value.split(',').map(s => s.trim()).filter(Boolean);
    if (projects.length) body.allow_projects = projects;
    try {
      const r = await api('/v1/mandates', { method: 'POST', body: JSON.stringify(body) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { err.textContent = typeof d.detail === 'string' ? d.detail : `Refused (${r.status}). Nothing was recorded.`; return; }
      form.reset(); $('#m-cap', root).value = 1000; $('#m-days', root).value = 30;
      await drawMandates(root);
    } catch { err.textContent = 'Could not reach the CarbonLedger API. Nothing was recorded.'; }
  });
  drawMandates(root);
}

export async function drawMandates(root) {
  const list = $('#mandate-list', root);
  if (!list) return;
  if (CONFIG.ledger !== 'solana-devnet' || !apiKey.get()) { list.innerHTML = '<li class="empty">No ledger connection or no API key. Mandates need both.</li>'; return; }
  let rows;
  try {
    const r = await api('/v1/accounts/me/mandates');
    if (!r.ok) { list.innerHTML = `<li class="empty">${r.status === 401 ? 'This API key is not accepted.' : 'Could not load mandates.'}</li>`; return; }
    rows = (await r.json()).mandates;
  } catch { list.innerHTML = '<li class="empty">Could not reach the CarbonLedger API.</li>'; return; }
  list.innerHTML = rows.length ? rows.map(m => `
    <li class="mandate" data-mandate="${esc(m.mandate_id)}">
      <div><strong class="mono">${esc(m.agent.slice(0, 8))}…${esc(m.agent.slice(-6))}</strong>
        <small>${mass(m.used_g)} used of ${mass(m.cap_g)} · ${m.revoked ? 'revoked' : m.active ? `expires ${when(m.expires_at)}` : 'expired'} · ${m.allow_projects ? esc(m.allow_projects.join(', ')) : 'any project'}</small>
        <div class="bar small"><span style="width:${Math.min(100, m.cap_g ? m.used_g / m.cap_g * 100 : 0).toFixed(1)}%"></span></div></div>
      ${m.active ? `<button class="btn ghost small" data-revoke="${esc(m.mandate_id)}">Revoke</button>` : '<span class="muted small">inactive</span>'}
    </li>`).join('') : '<li class="empty">No mandates yet.</li>';
  list.querySelectorAll('[data-revoke]').forEach(b => b.addEventListener('click', async () => {
    b.disabled = true;
    try { const r = await api(`/v1/mandates/${encodeURIComponent(b.dataset.revoke)}/revoke`, { method: 'POST' }); if (!r.ok) b.disabled = false; }
    catch { b.disabled = false; }
    drawMandates(root);
  }));
}
