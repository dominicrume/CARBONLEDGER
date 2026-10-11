# Changelog

## 0.1.0 (2026-10-11)
- Imported the CarbonLedger baseline app. Replaced the Solana ledger stub with a call to the API.
- Core: units, server estimator (140 golden vectors from the app), registry reference model (10 vectors, 20,000-step
  random attack), KYA mandate (8 vectors), hash-chained receipts, Solana memo client (signed offline, address verified).
- API: strict input, idempotency, rollback on chain failure, mandates, audit verify, closed CORS, security headers.
- Found and fixed F1: outside numbers could make the estimator return negative or absurd footprints, or crash.
- Proven: the full path over real HTTP, and the app's own ledger module against the live API in Node (receipt, history, failure path).
- Written, not run: Anchor program, Postgres schema, CI, sending to devnet, a browser run.
- Decision recorded: Solana, no fork (docs/DECISION-CHAIN.md).
