# Hardening: Engineering

How we make the system hard to break. Each control names the attack it stops. "Built" means a test proves it.

## Built
| Control | Attack it stops | Proof |
|---|---|---|
| Strict request models, bounds, unknown fields refused | Malformed or hostile input, overflow | tests/test_api.py hostile input |
| Idempotency key bound to the request digest | Replay and double spend | replay and mismatch tests |
| Work on a copy, commit after the chain write | Half-recorded state after a chain failure | failed chain test |
| Serial ranges per batch, never reused | Retiring the same gram twice | 20,000-step random attack |
| Hash-chained receipts, anchored head | Silent edit or deletion of history | tamper tests |
| Closed CORS unless an origin is named | Cross-site calls from other pages | cors test |
| Security headers, no docs in production | Click-jacking, sniffing, easy mapping | headers test |
| Offline signed memo, address pinned to the published one | Signing with a wrong program | chain tests |

## To build before any public URL (in this order)
1. Login for every caller, and per-caller rate limits. Today the API is open: keep it on a private network.
2. Request size limit and a server timeout in front of the API.
3. Confirm the Solana transaction before saying "recorded". Today the client submits and returns the signature.
   Fetch the signature status until `confirmed`, and fail the request if it never lands.
4. Server recomputation of footprints from items (D1), so a client cannot retire less than it owes for a basket.
5. Keys: the memo-signing key is a hot key with a tiny balance. The registry authority and verifier keys go in a
   multisig, never on a laptop. Rotate on any doubt.
6. Postgres: run db/migrations on a scratch database, add a migration test, least-privilege app role, backups with
   point-in-time restore, and a nightly job that re-checks every invariant and the anchored head hash.
7. RPC: a second provider, a timeout, and an alert when failures pass a set rate.
8. Web: a Content-Security-Policy, self-hosted scripts, integrity hashes on anything left on a CDN.
9. Dependency audit in CI, and a lockfile for the web build if one is added.

## Break drills (run them, write the result in BREAK.md)
- Send 1,000 identical retire requests at once. Expect one retirement.
- Kill the chain client mid-request. Expect nothing recorded and a plain error.
- Edit one receipt in the database. Expect `/v1/audit/verify` to name the index.
- Cut the last receipt off the table. Expect the anchored head to disagree.
- Give an agent a mandate, revoke it, then call. Expect REVOKED and no state change.
- Feed a product name with script tags. Expect it shown as text, never run.
