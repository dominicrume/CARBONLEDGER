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

## Human gates
- Install Node 22 (`brew install node@22`) so CI and local match. Node 20 runs everything today.
- Install the Solana CLI, Rust and Anchor for Block 5 (commands in docs/ENVIRONMENT.md). Without them the memo path is the integration.
- First devnet call (D14), about 10 minutes once the Solana CLI is installed:
  1. `solana-keygen new --outfile ~/.config/solana/carbonledger-devnet.json` then `solana config set --url devnet` and `solana airdrop 2 ~/.config/solana/carbonledger-devnet.json`.
  2. `cp .env.example .env`, set CHAIN_MODE=solana-devnet and SOLANA_SECRET_KEY_B58 to the base58 secret (one-liner in .env.example). Never paste it anywhere else.
  3. `scripts/dev.sh`, then in another terminal:
     `curl -s -X POST http://127.0.0.1:8000/v1/retire -H 'content-type: application/json' -d '{"account":"personal","grams":1200,"kind":"shop","label":"Shopping basket","lines":[{"name":"Beef","grams":1200}],"target_iso3":"GBR","idempotency_key":"devnet-first-call-0001"}'`
  4. The response carries anchor_status, signature, slot and explorer_url. If anchor_status is pending, `curl http://127.0.0.1:8000/v1/receipts/<receipt_id>` until it says anchored. Expect to fix small things on the first call.
  5. Paste the explorer link into docs/RUN-LOG.md and docs/PITCH-FACTS.md.
