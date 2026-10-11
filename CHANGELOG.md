# Changelog

## 0.2.0 (in progress, started 2026-10-11)
- Dependencies pinned. scripts/dev.sh and scripts/check.sh. docs/RUN-LOG.md tracks the autonomous run.
- Browser: one idempotency key per intent, honest timeout message, timeout above the server's worst case (F12, F13).
- API: lines must add up to the total (F15). Public receipt ids derive from content, not a counter (F14).
- Screens: "Retire pilot units" everywhere, simulated tag beside every unit count, data credits and a verify link
  in the footer, the Countries game labelled symbolic (D10, F9). tests/test_web_wording.py guards the words.

## 0.1.0 (2026-10-11)
- Imported the CarbonLedger baseline app. Replaced the Solana ledger stub with a call to the API.
- Core: units, server estimator (140 golden vectors from the app), registry reference model (10 vectors, 20,000-step
  random attack), KYA mandate (8 vectors), hash-chained receipts, Solana memo client (signed offline, address verified).
- API: strict input, idempotency, rollback on chain failure, mandates, audit verify, closed CORS, security headers.
- Found and fixed F1: outside numbers could make the estimator return negative or absurd footprints, or crash.
- Proven: the full path over real HTTP, and the app's own ledger module against the live API in Node (receipt, history, failure path).
- Written, not run: Anchor program, Postgres schema, CI, sending to devnet, a browser run.
- Decision recorded: Solana, no fork (docs/DECISION-CHAIN.md).
