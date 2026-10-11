// The ledger records retirements of CLT units. Every ledger has the same shape, so the app does not
// care which one is active:
//   retire({ grams, kind, label, lines, account, ... }) -> record
//   history(account?) -> records (newest first); account is 'personal' or 'business'
//   info -> { name, explorer: bool }
// 'local' keeps records on this device. 'solana-devnet' sends the retirement to the CarbonLedger API,
// which allocates serial units, writes the receipt chain and records its hash on Solana, then returns the
// transaction signature for the explorer link.
import { CONFIG } from '../config.js';
import { store } from './store.js';
import { settings } from './settings.js';
import { COUNTRIES } from '../data/countries.js';

const countryName = iso3 => COUNTRIES.find(c => c.iso3 === iso3)?.name || '';

export const gramsToClt = g => (g / 1e6).toFixed(CONFIG.cltDecimals);
export const priceGBP = g => Math.max(0.01, (g / 1e6) * settings.pricePerTonne());

// A fresh id for one intent. The caller makes it once (when the confirm sheet opens) and reuses it on retry,
// so the API's idempotency rule turns a retry into the same retirement, never a second one.
export function ref() {
  const a = new Uint8Array(8);
  (globalThis.crypto?.getRandomValues ? crypto.getRandomValues(a) : a.forEach((_, i) => (a[i] = Math.random() * 256)));
  return 'CL-' + Array.from(a, b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
}

const all = () => store.get('ledger', []);

// The API key is a login, like a password. It signs nothing and decides nothing. It lives in this browser's storage
// like any session and is sent as a bearer header. It is never a wallet key. Set it in Settings.
export const apiKey = { get: () => store.get('apiKey', ''), set: v => store.set('apiKey', String(v || '').trim()) };
export function apiHeaders() {
  const h = { 'content-type': 'application/json' };
  const k = apiKey.get();
  if (k) h.authorization = `Bearer ${k}`;
  return h;
}
const filter = (recs, account) => account ? recs.filter(r => (r.account || 'personal') === account) : recs;

export class LocalLedger {
  info = { name: 'Demo ledger on this device', explorer: false, source: 'this device only' };
  async sync() { return false; }
  async retire(entry) {
    const rec = { account: 'personal', ...entry, id: ref(), ts: new Date().toISOString(), clt: gramsToClt(entry.grams),
      priceGBP: priceGBP(entry.grams), pricePerTonne: settings.pricePerTonne(), ledger: 'local', explorerUrl: null };
    store.set('ledger', [rec, ...all()]);
    return rec;
  }
  history(account) { return filter(all(), account); }
}

export class SolanaLedger {
  info = { name: `Solana ${CONFIG.solana.cluster} (through the CarbonLedger API)`, explorer: true, source: 'the ledger' };

  // Mirror the server's history for this key into the local cache (T20). Records the server does not have are
  // dropped, so a browser edit is never a score. Game fields (country name, mode, finished) are kept from the
  // local copy when the server record matches by id. Returns true when the mirror came from the server.
  async sync() {
    if (!apiKey.get()) return false;
    let res;
    try { res = await fetch(`${CONFIG.api.baseUrl}/v1/accounts/me/history`, { headers: apiHeaders(), signal: AbortSignal.timeout(CONFIG.api.timeoutMs) }); }
    catch { return false; }
    if (!res.ok) return false;
    const { records } = await res.json();
    const local = new Map(all().map(r => [r.id, r]));
    const merged = records.map(s => {
      const l = local.get(s.id) || {};
      return { account: s.account, grams: s.grams, kind: s.kind, label: s.label, id: s.id, ts: s.ts, clt: s.clt, ledger: 'solana-devnet',
        priceGBP: priceGBP(s.grams), pricePerTonne: settings.pricePerTonne(), countryIso3: s.target_iso3, countryName: l.countryName || countryName(s.target_iso3),
        mode: l.mode, finished: l.finished, note: l.note, lines: l.lines, codes: l.codes, itemCount: l.itemCount, areas: l.areas, travelMode: l.travelMode, longHaul: l.longHaul,
        paidBy: l.paidBy, explorerUrl: s.explorer_url, receiptHash: s.receipt_hash, serialStart: s.serial_start, serialEnd: s.serial_end, signature: s.signature, anchorStatus: s.anchor_status };
    });
    store.set('ledger', merged);
    return true;
  }
  async retire(entry) {
    const body = {
      account: entry.account || 'personal', grams: entry.grams, kind: entry.kind || 'other', label: entry.label || 'Shopping basket',
      note: entry.note ? String(entry.note).slice(0, 120) : null,
      lines: (entry.lines || []).map(l => ({ name: String(l.name), grams: Math.round(l.grams) })),
      items: entry.items || [],
      target_iso3: entry.countryIso3 || null, idempotency_key: entry.idempotencyKey || ref(),
    };
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), CONFIG.api.timeoutMs);
    let res;
    try {
      res = await fetch(`${CONFIG.api.baseUrl}/v1/retire`, { method: 'POST', headers: apiHeaders(), body: JSON.stringify(body), signal: ctrl.signal });
    } catch (err) {
      // A timeout is not a refusal. The server may have recorded it. Only the server may say "Nothing was recorded."
      if (err?.name === 'AbortError') throw new Error('We could not confirm whether this was recorded. Check your history before trying again.');
      throw new Error('Could not reach the CarbonLedger API. Nothing was recorded.');
    } finally { clearTimeout(timer); }
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(typeof d.detail === 'string' ? d.detail : `The ledger refused this retirement (${res.status}). Nothing was recorded.`);
    }
    const r = await res.json();
    const rec = { account: 'personal', ...entry, id: r.receipt_id, ts: r.ts, clt: gramsToClt(entry.grams),
      priceGBP: priceGBP(entry.grams), pricePerTonne: settings.pricePerTonne(), ledger: 'solana-devnet',
      explorerUrl: r.explorer_url, receiptHash: r.receipt_hash, serialStart: r.serial_start, serialEnd: r.serial_end, signature: r.signature };
    store.set('ledger', [rec, ...all()]);
    return rec;
  }
  history(account) { return filter(all(), account); }
}

export const ledger = CONFIG.ledger === 'solana-devnet' ? new SolanaLedger() : new LocalLedger();
