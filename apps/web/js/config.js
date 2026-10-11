// Central settings. Change values here rather than inside modules.
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
  pricePerTonneGBP: 250,
  // 1 CLT = 1 tonne CO2e. 6 decimals = whole grams.
  cltDecimals: 6,
  // Which ledger records retirements: 'local' (this device) now; 'solana-devnet' once the CLT is live.
  ledger: (globalThis.location && new URLSearchParams(globalThis.location.search).get('ledger')) || 'local',   // ?ledger=solana-devnet overrides for a demo or a test
  // The CarbonLedger API signs and records retirements. Browsers never hold a signing key.
  // ?api=http://127.0.0.1:PORT may override the address for a local demo or test. Loopback only: a link can never
  // point the app at a stranger's server. The timeout sits above the API's worst case (two RPC calls at 15 s each).
  api: { baseUrl: loopbackOverride('api') || 'http://127.0.0.1:8000', timeoutMs: 40000 },
  solana: { cluster: 'devnet', rpcUrl: 'https://api.devnet.solana.com', mint: null, explorer: 'https://explorer.solana.com/tx/{sig}?cluster=devnet' },
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
