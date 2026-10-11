# Debt: What Is Not True Yet

Each item has an owner and a date to review. "Rume" is the owner until the team names others.

| ID | Debt | Why it matters | Owner | Review |
|----|------|----------------|-------|--------|
| D1 | The server does not recompute footprints. The API trusts the grams in the request. PART PAID 2026-10-11: lines must add up to the total (tests/test_api.py lines tests). Full recomputation is Block 3 step 17. | Under-retirement, leaderboard cheating | Rume | 2026-10-18 |
| D2 | No login and no rate limits. | Abuse, cost, spam on chain | Rume | before any public URL |
| D3 | The Anchor program is not compiled or tested. | The on-chain rules are unproven | Rume | 2026-10-13 |
| D4 | The Postgres schema has never run. | Database guards are unproven | Rume | 2026-10-18 |
| D5 | PAID 2026-10-11. The anchor worker confirms before anything says anchored; a failed anchor is shown as failed. Proof: tests/test_api.py anchor tests, tests/test_chain_receipts.py fake RPC tests. | | | |
| D6 | CI is written and has never run. Keys for authority and verifier are not in a multisig. | Gates and key safety unproven | Rume | 2026-10-13 |
| D7 | CDN scripts have no integrity hashes. No Content-Security-Policy. | Supply chain attack on every user | Rume | 2026-10-18 |
| D8 | Receipt labels are free text. | Personal data in the database | Rume | 2026-10-18 |
| D9 | State is in memory. Restart loses receipts and keys. | Lost history | Rume | 2026-10-18 |
| D10 | PAID 2026-10-11. Screens say "Retire pilot units", every unit count carries a simulated tag, data credits in the footer. Proof: tests/test_web_wording.py. | | | |
| D11 | No real verification. The attestation is simulated. | Units are not real credits | Partner and Rume | 2026-10-25 |
| D12 | Data licences and credits are unchecked (COMPLIANCE C13). | Licence breach | Rume | before any public demo |
| D13 | PAID 2026-10-11. Playwright smoke test in headless Chromium against the live API: retire, receipt, verify intact, API down path, banned words. Proof: scripts/e2e.sh, apps/web/test/e2e/smoke.spec.mjs. | | | |
| D14 | The Solana send path has never touched a network. The RPC client is now exercised against a fake transport (confirm, expiry, fallback). The first real call waits on a funded key (docs/RUN-LOG.md, Human gates). | First devnet call may fail | Rume | 2026-10-12 |
| D15 | One batch holds one hot counter, and per-retirement accounts cost rent. | Does not scale (SCALING.md) | Rume | before stage 2 |
| D16 | PAID 2026-10-11. The browser made a new idempotency key on every call, so a retry after a timeout could retire twice, and the timeout message claimed nothing was recorded. Now one key per intent and an honest timeout message. Proof: apps/web/test/ledger.test.mjs. | | | |
| D17 | PAID 2026-10-11. Receipt ids were a sequential counter in the public memo, leaking volume. Now derived from the receipt content. Proof: tests/test_api.py receipt id test. | | | |
| D18 | The retire lock is still held across the in-memory deep copy of the registry (O(n) in retirements). Not across network calls any more. Postgres row locks replace it in Block 4. | Throughput at pilot volume | Rume | 2026-10-18 |
