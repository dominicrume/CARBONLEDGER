// Operator dashboard: GET /v1/metrics with the operator token. The token stays in this tab (sessionStorage).
const $ = (s) => document.querySelector(s);
const n = (v) => Number(v || 0).toLocaleString('en-GB');
const kg = (g) => g >= 1e6 ? `${(g / 1e6).toLocaleString('en-GB', { maximumFractionDigits: 2 })} t` : g >= 1000 ? `${(g / 1000).toLocaleString('en-GB', { maximumFractionDigits: 1 })} kg` : `${n(g)} g`;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

async function show(e) {
  e?.preventDefault();
  const token = $('#m-token').value.trim() || sessionStorage.getItem('cl-metrics') || '';
  if (!token) { $('#m-msg').textContent = 'Type the operator token.'; return; }
  $('#m-msg').textContent = 'Loading…';
  try {
    const r = await fetch(`/v1/metrics?days=${$('#m-days').value}`, { headers: { authorization: `Bearer ${token}` } });
    if (r.status === 404) { sessionStorage.removeItem('cl-metrics'); $('#m-msg').textContent = 'That token is not right, or METRICS_TOKEN is not set on the server.'; return; }
    if (!r.ok) throw new Error(String(r.status));
    sessionStorage.setItem('cl-metrics', token); $('#m-token').value = '';
    render(await r.json());
  } catch { $('#m-msg').textContent = 'Could not reach the server.'; }
}

function render(m) {
  $('#m-msg').textContent = `Since ${m.since}. ${m.units}`;
  const k = [['players', n(m.players), 'players, all time'], ['return', `${Math.round(m.return_rate * 100)}%`, `came back in a second week (${n(m.returning_players)})`],
    ['ret', n(m.retirements), 'retirements, all time'], ['g', kg(m.grams), 'pilot units retired'], ['ref', n(m.refusals), 'refused, on the record'],
    ['man', n(m.mandates), 'agent mandates'], ['anc', `${n(m.anchors.anchored)}/${n((m.anchors.anchored || 0) + (m.anchors.pending || 0) + (m.anchors.failed || 0))}`, 'anchored on Solana']];
  $('#m-kpis').innerHTML = k.map(([, b, s]) => `<div class="m-kpi"><b>${esc(b)}</b><span>${esc(s)}</span></div>`).join('');
  const f = m.funnel, top = Math.max(1, f.site_view, f.app_open, f.retire_open, f.retirements);
  const steps = [['Website visits', f.site_view], ['App opens', f.app_open], ['Retirements started', f.retire_open], ['Retirements recorded', f.retirements], ['New players', f.new_players]];
  $('#m-funnel').innerHTML = steps.map(([label, v]) => `<div class="m-step"><span>${label}</span><div class="m-bar"><i style="width:${(100 * v / top).toFixed(1)}%"></i></div><b>${n(v)}</b></div>`).join('');
  const cols = [['site_view', 'Visits'], ['app_open', 'Opens'], ['scan_start', 'Scans'], ['retire_open', 'Started'], ['retirements', 'Retired'], ['players', 'Players'], ['new_players', 'New'], ['verify', 'Verified'], ['install', 'Installs'], ['statement', 'Statements']];
  const days = Object.entries(m.days).reverse();
  $('#m-days-table').innerHTML = `<thead><tr><th>Day</th>${cols.map(([, h]) => `<th>${h}</th>`).join('')}</tr></thead><tbody>${days.length ? days.map(([d, r]) => `<tr><td>${d}</td>${cols.map(([c]) => `<td>${r[c] ? n(r[c]) : '·'}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${cols.length + 1}">No activity in this period.</td></tr>`}</tbody>`;
  $('#m-out').hidden = false;
}

$('#m-login').addEventListener('submit', show);
$('#m-days').addEventListener('change', () => { if (sessionStorage.getItem('cl-metrics')) show(); });
if (sessionStorage.getItem('cl-metrics')) show();
