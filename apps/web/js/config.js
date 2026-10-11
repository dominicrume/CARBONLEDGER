// Central settings. Change values here rather than inside modules.
export const CONFIG = {
  appName: 'CarbonLedger',
  // Trustee-set price (demo, no payment taken).
  pricePerTonneGBP: 250,
  // 1 CLT = 1 tonne CO2e. 6 decimals = whole grams.
  cltDecimals: 6,
  // Which ledger records retirements: 'local' (this device) now; 'solana-devnet' once the CLT is live.
  ledger: 'local',
  // The CarbonLedger API signs and records retirements. Browsers never hold a signing key.
  api: { baseUrl: 'http://127.0.0.1:8000', timeoutMs: 40000 },   // above the API's worst case: two RPC calls at 15 s each
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
