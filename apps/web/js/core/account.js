// The person behind a login: sign-in by email link, a public name, delete my data, the weekly league, the business
// statement. All of it lives on the server (carbonledger_api/growth.py); the browser keeps only the login, as before.
import { CONFIG } from '../config.js';
import { apiKey, apiHeaders } from './ledger.js';

export const live = () => CONFIG.ledger === 'solana-devnet';

async function call(path, opts = {}) {
  const r = await fetch(`${CONFIG.api.baseUrl}${path}`, { headers: apiHeaders(), signal: AbortSignal.timeout(CONFIG.api.timeoutMs), ...opts });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : `The request failed (${r.status}).`);
  return d;
}

export const account = {
  profile: () => call('/v1/accounts/me/profile'),
  saveProfile: (fields) => call('/v1/accounts/me/profile', { method: 'PUT', body: JSON.stringify(fields) }),
  emailLink: (email) => call('/v1/auth/email', { method: 'POST', body: JSON.stringify({ email }) }),
  async verify(token) {                      // the login this browser played with is sent along, so it joins the account
    const d = await call('/v1/auth/verify', { method: 'POST', body: JSON.stringify({ token }) });
    apiKey.set(d.api_key);
    return d;
  },
  deleteMe: () => call('/v1/accounts/me', { method: 'DELETE' }),
  league: (board) => call(`/v1/league?board=${encodeURIComponent(board)}`),
  async statement(accountName = 'business') {  // a CSV file the business keeps; every line checks by receipt id
    const r = await fetch(`${CONFIG.api.baseUrl}/v1/accounts/me/statement?account=${accountName}`, { headers: apiHeaders(), signal: AbortSignal.timeout(CONFIG.api.timeoutMs) });
    if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(typeof d.detail === 'string' ? d.detail : `No statement (${r.status}).`); }
    const name = (r.headers.get('content-disposition') || '').match(/filename="([^"]+)"/)?.[1] || 'carbonledger-statement.csv';
    const url = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  },
};

// Privacy-first counts: one event name, sent to our own server, which stores only the day and a number.
// Nothing is sent when the browser asks not to be tracked, or when the app runs on this device only.
export function track(name) {
  try {
    if (!live() || navigator.globalPrivacyControl || navigator.doNotTrack === '1') return;
    fetch(`${CONFIG.api.baseUrl}/v1/events`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name }), keepalive: true }).catch(() => {});
  } catch {}
}
