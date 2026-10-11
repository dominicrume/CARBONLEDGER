# Debt: What Is Not True Yet

Each item has an owner and a date to review. "Rume" is the owner until the team names others.

Reviewed 2026-10-11 at the end of the autonomous run. PAID items keep their row with the test that proves them.
Open: D3, D6 (part), D11, D12, D14, D18 to D25. Paid: D1, D2, D4, D5, D7, D8, D9, D10, D13, D15, D16, D17.

| ID | Debt | Why it matters | Owner | Review |
|----|------|----------------|-------|--------|
| D1 | PAID 2026-10-11. The server recomputes every footprint from typed items and refuses a lower total. Proof: tests/test_activity_parity.py (1,787 vectors), tests/test_api.py recomputation tests. Live Open Food Facts lookup runs server side; an unknown barcode needs a chosen category. | | | |
| D2 | PAID 2026-10-11. API keys (hashed, roles), per-key rate limit, request size limit, server deadline. Agents are ed25519 keys with signed requests. Proof: tests/test_auth.py, tests/test_api.py login and signature tests. Still needed before a public URL: TLS termination and a reverse proxy in front (D19). | | | |
| D3 | PART PAID 2026-10-11 night: the Anchor program compiles and passes all 10 registry vectors in LiteSVM (programs/carbon_registry/tests/conformance.ts, `npm run vectors`). Not deployed to devnet (hot key unfunded), not independently reviewed, the API still anchors by memo. | The on-chain rules are proven in a test runtime, not on a cluster | Rume | at devnet deploy |
| D4 | PAID 2026-10-11. Migrations 0001 and 0002 run by scripts/migrate.py; the exclusion constraint, append-only triggers, issuance cap, anchor forward-only and evidence decided-once rules are tested. Proof: tests/test_db_migrations.py. | | | |
| D5 | PAID 2026-10-11. The anchor worker confirms before anything says anchored; a failed anchor is shown as failed. Proof: tests/test_api.py anchor tests, tests/test_chain_receipts.py fake RPC tests. | | | |
| D6 | PART PAID 2026-10-11. CI is written with every action pinned to a commit hash, a Postgres service, the browser test, pip-audit and npm audit, plus a nightly recheck workflow. It has not run on a GitHub runner yet (first push is a human gate). Authority and verifier keys are still not in a multisig (they exist only in the model). | Gates and key safety unproven | Rume | at first push |
| D7 | PAID 2026-10-11. ZXing, D3 and topojson-client are self-hosted at pinned versions with SHA-384 integrity attributes, and the page carries a Content-Security-Policy (scripts from self only). Proof: tests/test_web_supply_chain.py. A deployed copy must set connect-src to the real API origin (D21). | | | |
| D8 | PAID 2026-10-11. Labels are a closed vocabulary; free text is a hashed note, never stored. Proof: tests/test_api.py note test. | | | |
| D9 | PAID 2026-10-11. With DATABASE_URL the API writes every commit to Postgres first and rebuilds from the rows at start, verifying the receipt chain. Keys, mandates, idempotency and anchors persist. Proof: tests/test_db_store.py. Without DATABASE_URL state stays in memory (dry runs and tests only). | | | |
| D10 | PAID 2026-10-11. Screens say "Retire pilot units", every unit count carries a simulated tag, data credits in the footer. Proof: tests/test_web_wording.py. | | | |
| D11 | No real verification. The attestation is simulated. The evidence table and the decided-once rule exist in the database; no evidence has been ingested. | Units are not real credits | Partner and Rume | 2026-10-25 |
| D12 | Data licences and credits are unchecked (COMPLIANCE C13). | Licence breach | Rume | before any public demo |
| D13 | PAID 2026-10-11. Playwright smoke test in headless Chromium against the live API: retire, receipt, verify intact, API down path, banned words. Proof: scripts/e2e.sh, apps/web/test/e2e/smoke.spec.mjs. | | | |
| D14 | The Solana send path has never touched a network. The RPC client is now exercised against a fake transport (confirm, expiry, fallback). The first real call waits on a funded key (docs/RUN-LOG.md, Human gates). | First devnet call may fail | Rume | 2026-10-12 |
| D15 | PAID 2026-10-11 for the API: one Merkle root per interval, a proof per receipt, no per-retirement account in the revised program design. Proof: tests/test_outbox.py, tests/test_merkle.py, tests/test_api.py proof test, browser proof check. The hot counter per batch remains (D23). | | | |
| D16 | PAID 2026-10-11. The browser made a new idempotency key on every call, so a retry after a timeout could retire twice, and the timeout message claimed nothing was recorded. Now one key per intent and an honest timeout message. Proof: apps/web/test/ledger.test.mjs. | | | |
| D17 | PAID 2026-10-11. Receipt ids were a sequential counter in the public memo, leaking volume. Now derived from the receipt content. Proof: tests/test_api.py receipt id test. | | | |
| D18 | The retire lock is still held across the in-memory deep copy of the registry (O(n) in retirements). Not across network calls any more. Postgres row locks replace it in Block 4. | Throughput at pilot volume | Rume | 2026-10-18 |
| D19 | PAID 2026-10-11 for the demo: Railway terminates TLS in front of uvicorn (HSTS on, proxy headers trusted). A WAF and request limits at the edge are still Railway's defaults. | | | |
| D20 | Server-side Open Food Facts lookup has no persistent cache and no circuit breaker. A burst of unknown barcodes makes a burst of outbound calls. | Latency, rate limiting by OFF | Rume | 2026-10-18 |
| D21 | PAID 2026-10-11: the API serves the app from its own origin, so the page's CSP 'self' covers the API and no loopback entry is needed in production. | | | |
| D22 | The Postgres store opens a connection per transaction and has no pool, no retry and no read replica. The in-memory copy is still the read path. | Latency under load | Rume | before stage 2 |
| D23 | One batch, one hot counter. Every retirement in the demo batch still serialises on it in memory and in the batches row. Fix at pilot: several smaller batches and route a retirement to any batch with units left. | Throughput | Rume | before stage 2 |
| D24 | A receipt whose anchor failed after five tries is shown as failed and is not re-anchored automatically. scripts/recheck.py exits 2 when any exist. Add a re-anchor command for operators. | Stuck receipts | Rume | 2026-10-18 |
| D25 | scripts/e2e.sh checks that the API on its port is ours but not that the web server on its port is ours. A stale server on the web port made every browser test fail once (F16). | Confusing test failures | Rume | 2026-10-18 |
| D26 | The receipt format changed to KYA receipts. Rows written before 2026-10-11 (the first four demo receipts on Railway) do not carry seals and cannot be converted, so the demo database is reset at this deploy. A real pilot would need a dated format cutover instead. | Old rows refuse to load | Rume | at this deploy |
| D27 | PAID 2026-10-11. A first-time visitor to the demo saw NO_KEY. The demo now mints a login silently at load and replaces a refused one on the spot. Proof: browser tests for both paths. Servers without demo logins still show the button and the Settings field. | | | |
