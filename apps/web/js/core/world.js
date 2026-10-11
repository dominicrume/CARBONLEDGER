// World stats from the API (public, no personal data): totals by country and how many players took part.
// With the ledger connected the Countries screen reads these, so the line moves on its own as people play.
// On this device only, the local history is all there is.
import { CONFIG } from '../config.js';
import { setWorldTotals } from './game.js';

let cache = null;
export const world = {
  get: () => cache,
  async refresh() {
    if (CONFIG.ledger !== 'solana-devnet') return null;
    try {
      const r = await fetch(`${CONFIG.api.baseUrl}/v1/stats/world`, { signal: AbortSignal.timeout(CONFIG.api.timeoutMs) });
      if (!r.ok) return cache;
      cache = await r.json();
      const totals = {};
      for (const [iso, c] of Object.entries(cache.countries || {})) totals[iso] = c.grams;
      setWorldTotals(totals);
      document.dispatchEvent(new CustomEvent('carbonledger:world', { detail: cache }));
      return cache;
    } catch { return cache; }
  },
};
