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

export const gramsToClt = g => (g / 1e6).toFixed(CONFIG.cltDecimals);
export const priceGBP = g => Math.max(0.01, (g / 1e6) * settings.pricePerTonne());

function ref() {
  const a = new Uint8Array(8);
  (globalThis.crypto?.getRandomValues ? crypto.getRandomValues(a) : a.forEach((_, i) => (a[i] = Math.random() * 256)));
  return 'CL-' + Array.from(a, b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
}

const all = () => store.get('ledger', []);
const filter = (recs, account) => account ? recs.filter(r => (r.account || 'personal') === account) : recs;

class LocalLedger {
  info = { name: 'Demo ledger on this device', explorer: false };
  async retire(entry) {
    const rec = { account: 'personal', ...entry, id: ref(), ts: new Date().toISOString(), clt: gramsToClt(entry.grams),
      priceGBP: priceGBP(entry.grams), pricePerTonne: settings.pricePerTonne(), ledger: 'local', explorerUrl: null };
    store.set('ledger', [rec, ...all()]);
    return rec;
  }
  history(account) { return filter(all(), account); }
}

class SolanaLedger {
  info = { name: `Solana ${CONFIG.solana.cluster} (through the CarbonLedger API)`, explorer: true };
  async retire(entry) {
    const body = {
      account: entry.account || 'personal', grams: entry.grams, kind: entry.kind || 'other', label: entry.label || '',
      lines: (entry.lines || []).map(l => ({ name: String(l.name), grams: Math.round(l.grams) })),
      target_iso3: entry.countryIso3 || null, idempotency_key: ref(),
    };
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), CONFIG.api.timeoutMs);
    let res;
    try {
      res = await fetch(`${CONFIG.api.baseUrl}/v1/retire`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), signal: ctrl.signal });
    } catch { throw new Error('Could not reach the CarbonLedger API. Nothing was recorded.'); }
    finally { clearTimeout(timer); }
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
