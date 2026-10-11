# Run Log

One line per step: time (UTC), what changed, the test that proves it, anything skipped. Resume from the last line.

## Steps
- 2026-10-11 Block 0 step 1: .venv created, 203 tests pass on Python 3.13.7.
- 2026-10-11 Block 0 step 2: dependencies pinned in requirements.txt and pyproject.toml. pip-audit: no known vulnerabilities.
- 2026-10-11 Block 0 step 3: tools present: node 20.20.2 (not 22), npm 10.8.2, docker 29.8.2 (daemon up), python 3.13.7. Missing: solana, anchor, cargo, psql, python 3.12. Block 5 will be skipped. Postgres will run in docker, psql through docker exec.
- 2026-10-11 Block 0 step 4: scripts/dev.sh and scripts/check.sh written. CI to call check.sh (Block 4 step 21).
- 2026-10-11 Block 1 step 5: idempotency key per intent (apps/web/js/ui/retire.js, core/ledger.js). Proof: apps/web/test/ledger.test.mjs.
- 2026-10-11 Block 1 step 6: timeout message honest, client timeout 40 s. Proof: same Node test.
- 2026-10-11 Block 1 step 7: lines must add up (RetireIn validator). Proof: tests/test_api.py lines tests.
- 2026-10-11 Block 1 step 8: wording, simulated tags, footer credits, symbolic game. Proof: tests/test_web_wording.py. ui/offset.js renamed ui/retire.js.
- 2026-10-11 Block 1 step 9: receipt ids from content. Proof: tests/test_api.py receipt id test. 210 tests, 4 Node tests, check.sh green.
- 2026-10-11 Block 1 done. ROOTS-SCORE unchanged (no HV check moved).
- 2026-10-11 Block 2 step 10: chain.confirm polls getSignatureStatuses until confirmed or the blockhash expires; anchor outbox (packages/core/carbonledger/outbox.py) with a worker, retries and failed state; API split into models.py, state.py, main.py. Proof: tests/test_api.py anchor tests, tests/test_chain_receipts.py fake RPC tests. Rule 6 refined, CLAUDE.md updated, decision recorded.
- 2026-10-11 Block 2 step 11: SOLANA_RPC_URL_FALLBACK, per-call timeout, retries with backoff, RpcStats failure rate. Proof: fallback and every-endpoint-down tests.
- 2026-10-11 Block 2 step 12: SKIPPED, no .env and no devnet key on this machine. Steps under Human gates. Dry-run path proven.
- 2026-10-11 Block 2 step 13: Playwright 1.49.1 and Chromium installed as a web dev dependency. apps/web/test/e2e/smoke.spec.mjs: retire from the demo shelf, receipt, verify screen intact, API-down path, banned words. 3 passed. Verify screen and connection state built early (Block 6 steps 25 and 27 partly done). Found: port 8000 on this machine belongs to an unrelated process (scripts/dev_demo.py, not this repo), so e2e.sh uses 8765 and 8787 and the app accepts a loopback-only ?api= override. check.sh runs e2e when Playwright is installed (SKIP_E2E=1 to skip).
- 2026-10-11 Block 2 done. ROOTS-SCORE: check 7 (contain failure) stays SEEDLING until Postgres triggers run; check 12 (CI) stays SEEDLING until the first push.
- 2026-10-11 Block 3 step 14: API keys (packages/core/carbonledger/auth.py), roles, token bucket, size limit, deadline; scripts/make_api_key.py; key field in Settings. Proof: tests/test_auth.py, tests/test_api.py login tests, e2e no-key test.
- 2026-10-11 Block 3 step 15: agent identity by ed25519 key, signed and time-boxed requests (agentsig.py); 8 signature vectors with public keys only. Proof: tests/test_registry_mandate.py signature vectors, tests/test_api.py signature tests.
- 2026-10-11 Block 3 step 16: label vocabulary, hashed note. Proof: tests/test_api.py note test.
- 2026-10-11 Block 3 step 17: apps/web/js/core/activities.js shared by every view; scripts/export_activities.mjs; activities.py port; typed items; recompute.py; server-side catalogue and Open Food Facts lookup. Proof: tests/test_activity_parity.py (1,789), tests/test_api.py recomputation tests. check.sh diffs the exported data.
- 2026-10-11 Block 3 step 18: /v1/accounts/me/totals and /history; the browser mirrors the ledger at load and after each retirement. Proof: tests/test_api.py totals test, e2e forged-record test.
- 2026-10-11 Block 3 done. 2,043 Python tests, 4 Node tests, 5 browser tests. ROOTS-SCORE check 9 and 11 pointers updated.
- 2026-10-11 Block 4 step 19: docker-compose.yml (Postgres 16 on 127.0.0.1:5433), db/migrations/0002_phase1.sql, scripts/migrate.py, services/api/carbonledger_api/store.py (write-through, rebuild at start), scripts/recheck.py. Proof: tests/test_db_migrations.py (7), tests/test_db_store.py (5), run against a local container. DATABASE_URL_TEST makes them run; CI provides it.
- 2026-10-11 Block 4 step 20: vendored ZXing, D3, topojson-client with SHA-384 integrity, CSP meta, scripts/vendor_hashes.sh. Proof: tests/test_web_supply_chain.py, browser test green under the CSP.
- 2026-10-11 Block 4 step 21: .github/workflows/ci.yml rewritten: actions pinned to commit hashes, Postgres service, Node 22, npm ci and npm audit, Playwright with deps, scripts/check.sh, migrations twice, recheck; an anchor job allowed to fail. .github/workflows/recheck.yml nightly (Block 7 step 29). Playwright moved from 1.49.1 to 1.64.0 after npm audit flagged a high advisory. apps/web/package-lock.json added. packages/core/carbonledger/merkle.py with 14 tests (start of step 23).
- 2026-10-11 Block 4 done.
- 2026-10-11 Block 5 step 22 (parts without the toolchain): init-if-needed removed; lib.rs revised (three verifiers with add and rotate, two-verifier threshold, unsuspend, no per-retirement account, anchor_root); tests/conformance.ts harness written; README updated. NOT compiled: no cargo or anchor here (Human gates).
- 2026-10-11 Block 5 step 23: Merkle anchoring live in the API: packages/core/carbonledger/merkle.py, outbox batches with one transaction per interval and a proof per receipt, memo v2, migration 0003, GET /v1/receipts/{id}/proof, browser verifier apps/web/js/core/merkle.js with shared vectors, verify screen recomputes the proof. Proof: tests/test_merkle.py, tests/test_outbox.py, tests/test_api.py proof test, tests/test_db_store.py proof after restart, apps/web/test/merkle.test.mjs, e2e proof check. docs/MERKLE-ANCHORING.md.
- 2026-10-11 Block 5 step 24: toolchain install steps are under Human gates; the memo path (now v2 with a root) is the integration.
- 2026-10-11 Block 6 step 25: verify screen (apps/web/js/ui/verify.js): hash, serial range, anchor status, slot, signature, explorer link, Merkle proof recomputed in the browser, whole-ledger check. Works without a key. Proof: e2e smoke test.
- 2026-10-11 Block 6 step 26: mandate screen (apps/web/js/ui/mandate.js) in the Business view: agent public key, cap, expiry, allowed projects, used against cap, revoke; refusal codes in plain words; GET /v1/accounts/me/mandates. 422 answers are now one plain sentence naming the field. Proof: tests/test_api.py mandate listing and 422 tests, e2e mandate tests.
- 2026-10-11 Block 6 step 27: connection state in the header (built in Block 2).
- 2026-10-11 Block 6 step 28: axe-core (WCAG 2.1 AA) on every tab, the shelf, the confirm sheet and the receipt, plus a keyboard-reach test and reduced motion (apps/web/test/e2e/a11y.spec.mjs). Fixed: muted text and inactive tabs at 4.0 to 1 raised to 5.6 to 1; the simulated tag raised to 6.9 to 1; the globe exposes data-autorotate and stops under reduced motion; the queue list is the globe's text alternative. Test output folders ignored by git. Found while running: a stale web server from the interrupted run held the test port (stopped).
- 2026-10-11 Block 7 step 29: .github/workflows/recheck.yml runs scripts/recheck.py nightly when RECHECK_ENABLED=1 and DATABASE_URL_RECHECK is set; it fails loudly. recheck.py exits 1 on a broken invariant or chain, 2 when failed anchors exist.
- 2026-10-11 Block 7 step 30: scripts/drills.py runs every drill against a live API. 10 of 10 pass. Results under the findings in BREAK.md. F2, F3, F4, F6, F7, F10 marked fixed with their tests; F16 and F17 added.
- 2026-10-11 Block 8 step 31: README.md written: what it is, what is simulated, how to run, verify a receipt, architecture, honest limits, third-party code and data.
- 2026-10-11 Block 8 step 32: DEBT.md reviewed (paid and new), ROOTS-SCORE.md re-scored (10 ROOTED, 3 SEEDLING), CHANGELOG.md 0.2.0, docs/PITCH-FACTS.md, docs/HACKATHON-48H.md checklist, START-HERE.txt.
- 2026-10-11 Block 8 step 33: final scripts/check.sh with the database and the browser suite, final commit.

## Human gates
- First push to GitHub: create the repository, push, watch the ci workflow. Set the repository variable RECHECK_ENABLED=1 and the secret DATABASE_URL_RECHECK (a read-only role) to turn on the nightly recheck.
- Install Node 22 (`brew install node@22`) so CI and local match. Node 20 runs everything today.
- Install the Solana CLI, Rust and Anchor for Block 5 (commands in docs/ENVIRONMENT.md). Without them the memo path is the integration.
- First devnet call (D14), about 10 minutes once the Solana CLI is installed:
  1. `solana-keygen new --outfile ~/.config/solana/carbonledger-devnet.json` then `solana config set --url devnet` and `solana airdrop 2 ~/.config/solana/carbonledger-devnet.json`.
  2. `cp .env.example .env`, set CHAIN_MODE=solana-devnet and SOLANA_SECRET_KEY_B58 to the base58 secret (one-liner in .env.example). Never paste it anywhere else.
  3. In .env also set APP_ENV=dev and API_DEMO_KEY to any string starting clk_personal_ (a dev-only login). `scripts/dev.sh`, then in another terminal, with that key:
     `curl -s -X POST http://127.0.0.1:8000/v1/retire -H 'content-type: application/json' -H "authorization: Bearer $API_DEMO_KEY" -d '{"account":"personal","grams":1200,"kind":"shop","label":"Shopping basket","lines":[{"name":"Beef","grams":1200}],"items":[{"type":"products_sold","gPerUnit":1200,"n":1}],"target_iso3":"GBR","idempotency_key":"devnet-first-call-0001"}'`
  4. The response carries anchor_status, signature, slot and explorer_url. If anchor_status is pending, `curl http://127.0.0.1:8000/v1/receipts/<receipt_id>` until it says anchored. Expect to fix small things on the first call.
  5. Paste the explorer link into docs/RUN-LOG.md and docs/PITCH-FACTS.md.
- The partner meeting and the open decisions in CONTEXT.md (backing, price, trust, licence, ownership of the baseline app). Nothing in the code decides these.
- Counsel: the items in rules/COMPLIANCE.md, and the Open Food Facts ODbL share-alike question next to the patent and licence choice (C12, C13).
- Before any public URL: TLS termination and a reverse proxy in front of uvicorn (D19), the real API origin in the page's Content-Security-Policy (D21), the authority and verifier keys in a multisig (D6).
- After the first anchor build: replay the registry vectors (programs/carbon_registry/tests/conformance.ts), deploy to devnet, then switch the chain client from the memo to anchor_root.
