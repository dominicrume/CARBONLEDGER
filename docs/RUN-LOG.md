# Run Log

One line per step: time (UTC), what changed, the test that proves it, anything skipped. Resume from the last line.

## Steps
- 2026-10-11 Block 0 step 1: .venv created, 203 tests pass on Python 3.13.7.
- 2026-10-11 Block 0 step 2: dependencies pinned in requirements.txt and pyproject.toml. pip-audit: no known vulnerabilities.
- 2026-10-11 Block 0 step 3: tools present: node 20.20.2 (not 22), npm 10.8.2, docker 29.8.2 (daemon up), python 3.13.7. Missing: solana, anchor, cargo, psql, python 3.12. Block 5 will be skipped. Postgres will run in docker, psql through docker exec.
- 2026-10-11 Block 0 step 4: scripts/dev.sh and scripts/check.sh written. CI to call check.sh (Block 4 step 21).

## Human gates
- Install Node 22 (`brew install node@22`) so CI and local match. Node 20 runs everything today.
- Install the Solana CLI, Rust and Anchor for Block 5 (commands in docs/ENVIRONMENT.md). Without them the memo path is the integration.
- Create and fund the devnet hot key, then put CHAIN_MODE=solana-devnet and SOLANA_SECRET_KEY_B58 in .env (commands in .env.example). Until then every chain step runs dry-run.
