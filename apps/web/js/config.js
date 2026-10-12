// Central settings. Change values here rather than inside modules.
// True when the page comes from the API itself (any https origin, or a loopback port that is not the 8080 file server).
function servedByApi() {
  const l = globalThis.location;
  if (!l || !l.origin || l.protocol === 'file:') return false;
  if (l.protocol === 'https:') return true;
  return (l.hostname === '127.0.0.1' || l.hostname === 'localhost') && l.port !== '8080' && l.port !== '8787';
}
function loopbackOverride(name) {
  try {
    const v = new URLSearchParams(globalThis.location?.search || '').get(name);
    if (!v) return null;
    const u = new URL(v);
    return (u.hostname === '127.0.0.1' || u.hostname === 'localhost') && u.protocol === 'http:' ? u.origin : null;
  } catch { return null; }
}
export const CONFIG = {
  appName: 'CarbonLedger',
  // Trustee-set price (demo, no payment taken).
  pricePerTonneGBP: 100,
  // 1 CLT = 1 tonne CO2e. 6 decimals = whole grams.
  cltDecimals: 6,
  // Which ledger records retirements: 'local' (this device) now; 'solana-devnet' once the CLT is live.
  // Served from the API's own origin (a deployment): talk to that origin and use the ledger. Served from a plain file
  // server on a laptop: records stay on this device unless ?ledger=solana-devnet is given.
  ledger: (globalThis.location && new URLSearchParams(globalThis.location.search).get('ledger')) || (servedByApi() ? 'solana-devnet' : 'local'),
  // The CarbonLedger API signs and records retirements. Browsers never hold a signing key.
  // ?api=http://127.0.0.1:PORT may override the address for a local demo or test. Loopback only: a link can never
  // point the app at a stranger's server. The timeout sits above the API's worst case (two RPC calls at 15 s each).
  api: { baseUrl: loopbackOverride('api') || (servedByApi() ? globalThis.location.origin : 'http://127.0.0.1:8000'), timeoutMs: 40000 },
  solana: { cluster: 'devnet', rpcUrl: 'https://api.devnet.solana.com', mint: null, programId: '3dGd2V1ykcmahyCQvhri4R2WhabT83hmm2WNz2r788Zj', explorer: 'https://explorer.solana.com/tx/{sig}?cluster=devnet' },
  // Live product lookup when the browser allows it; the built-in catalogue always works offline.
  openFoodFacts: { enabled: true, timeoutMs: 4000 },
  // Pack weight assumed when a product has none recorded (high on purpose).
  unknownWeightGrams: 1000,
  // Highest plausible kg CO2e per kg from an outside lookup (ASSUMPTION: beef, the highest table value, is about 99). Above this, the value is ignored.
  maxAgribalyseKgPerKg: 1000,
  // Uplift applied to educated guesses (tier 4), so estimates err high.
  estimateUplift: 1.25,
  // Demo: a simulated community total so the Countries view shows progress. Labelled as simulated in the UI.
  demoCommunityTonnes: 500000,
};
