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

## Human gates
- Install Node 22 (`brew install node@22`) so CI and local match. Node 20 runs everything today.
- Install the Solana CLI, Rust and Anchor for Block 5 (commands in docs/ENVIRONMENT.md). Without them the memo path is the integration.
- Create and fund the devnet hot key, then put CHAIN_MODE=solana-devnet and SOLANA_SECRET_KEY_B58 in .env (commands in .env.example). Until then every chain step runs dry-run.
