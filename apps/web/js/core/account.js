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

// ---- Sign in with Seeker: the phone's wallet signs one message (no transaction). Android only, loaded on demand. ----
// vendor/seeker-mwa-0.7.0.min.js is built by scripts/build_seeker_mwa.sh and pinned by this hash (tests check it).
export const SEEKER_MWA = { src: 'vendor/seeker-mwa-0.7.0.min.js', integrity: 'sha384-L+kDmrS1QTQFqoXeAstS0KNFpOCwSSXEIdqMhICxmd60JMWMAKgd8EQ0EI9IlwOX' };
export const seekerCapable = () => live() && /Android/i.test(navigator.userAgent || '');
let seekerReady = null;
function loadSeeker() {
  seekerReady ??= new Promise((resolve, reject) => {
    const s = Object.assign(document.createElement('script'), { src: SEEKER_MWA.src, integrity: SEEKER_MWA.integrity, crossOrigin: 'anonymous' });
    s.onload = () => { window.CarbonLedgerSeeker.register({ name: 'CarbonLedger', uri: location.origin, icon: 'brand/mark-192.png' }); resolve(window.CarbonLedgerSeeker); };
    s.onerror = () => { seekerReady = null; reject(new Error('The Seeker wallet connector could not load.')); };
    document.head.append(s);
  });
  return seekerReady;
}
export async function signInWithSeeker() {
  const mwa = await loadSeeker();
  const challenge = await call('/v1/auth/seeker/challenge', { method: 'POST' });
  const wait = new Promise((_, no) => setTimeout(() => no(new Error('No Seeker wallet answered. On a Seeker, open CarbonLedger in Chrome or from the dApp Store and try again. Nothing changed.')), 120_000));
  let signed;                                            // the wallet shows the message; signing moves nothing
  try { signed = await Promise.race([mwa.signIn(challenge), wait]); }
  catch (err) { throw new Error(/declin|reject|cancel/i.test(err?.message || '') ? 'You did not sign, so nothing changed.' : err.message); }
  const d = await call('/v1/auth/seeker/verify', { method: 'POST', body: JSON.stringify(signed) });
  apiKey.set(d.api_key);
  return d;
}

// Privacy-first counts: one event name, sent to our own server, which stores only the day and a number.
// Nothing is sent when the browser asks not to be tracked, or when the app runs on this device only.
export function track(name) {
  try {
    if (!live() || navigator.globalPrivacyControl || navigator.doNotTrack === '1') return;
    fetch(`${CONFIG.api.baseUrl}/v1/events`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name }), keepalive: true }).catch(() => {});
  } catch {}
}
