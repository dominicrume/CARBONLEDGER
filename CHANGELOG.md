# Changelog

## 0.2.0 (in progress, started 2026-10-11)
- Dependencies pinned. scripts/dev.sh and scripts/check.sh. docs/RUN-LOG.md tracks the autonomous run.
- Browser: one idempotency key per intent, honest timeout message, timeout above the server's worst case (F12, F13).
- API: lines must add up to the total (F15). Public receipt ids derive from content, not a counter (F14).
- Merkle anchoring (D15): one root per interval, a proof per receipt, memo v2, proof endpoint, browser verifier.
  Program revised for volume and three verifiers (not compiled). Postgres persistence (D4, D9) with a second guard.
  Self-hosted scripts with integrity hashes and a Content-Security-Policy (D7). CI pinned to commit hashes (D6).
- Screens: verify screen with a browser-side proof check, mandate screen, connection state, accessibility pass
  (axe at WCAG 2.1 AA, keyboard reach, reduced motion). Plain one-sentence 422 answers.
- Login (D2): API keys with hashed storage and roles, per-key rate limit, request size limit, server deadline.
  Agents are ed25519 keys and every agent request is signed and time-boxed (KYA), with 8 signature vectors.
- Server recomputation (D1): typed items on every retire request, priced by the server from its own tables and its
  own product lookup; 1,787 golden vectors from the app's activity functions; a lower total is refused.
- Labels are a closed vocabulary; free text is a hashed note (D8). Owner totals and history endpoints (T20); the
  browser mirrors the ledger and drops records the server does not have.
- Chain: confirm before claiming (D5). Anchor outbox with a worker, retries and a failed state. RPC fallback URL,
  per-call timeout, backoff, failure rate (T21). API split into models, state and app. Rule 6 refined.
- Browser: verify screen, connection state, loopback-only ?api= and ?ledger= overrides, dedicated error line on the
  confirm sheet. Playwright smoke test in headless Chromium (D13), run by scripts/e2e.sh and check.sh.
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
