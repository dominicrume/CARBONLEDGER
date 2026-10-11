# Threat Model

Status: BUILT means a test proves the control. PLANNED means it is written down and not built. OPEN means a known gap.

| ID | Threat | Impact | Control | Status |
|----|--------|--------|---------|--------|
| T1 | Retire the same unit twice | A tonne counted twice | Fresh serial range per retirement, unique PDA per range, exclusion constraint | BUILT in model, PLANNED in program and database |
| T2 | Link one external credit twice | Double counting across registries | Unique (registry, serial) link | BUILT in model, PLANNED in program and database |
| T3 | Issue units with no real project | Fake credits | Issuance needs a verifier attestation, capped by it | BUILT in model |
| T4 | Rogue or stolen verifier key | Fake attestation | Multisig, two verifiers, published decisions | PLANNED |
| T5 | Stolen registry authority key | Unlimited fake issuance | Multisig, hardware keys, time lock | PLANNED |
| T6 | Fake or reused evidence (GPS spoofing, recycled photos) | False attestation | Hash uniqueness, satellite cross-check, human review | PLANNED (MRV not built) |
| T7 | Client sends fewer grams than a basket owes | Under-retirement, leaderboard cheating | Server recomputes from items | OPEN (D1) |
| T8 | Replay a retire request | Double spend | Idempotency key bound to the request digest | BUILT |
| T9 | Chain write fails midway | Half-recorded state | Work on a copy, commit after chain success | BUILT |
| T10 | History edited by an insider | Tampering | Hash chain, anchored head, append-only triggers | BUILT in code, PLANNED in database |
| T11 | Newest receipts cut off | Hidden deletion | Anchored head hash disagrees | BUILT (tested) |
| T12 | Anyone can call the API | Abuse, spam, cost | Login, rate limits | OPEN (D2) |
| T13 | Signing key leaks | Fake memos, drained fee balance | Tiny hot balance, secret store, rotation | PLANNED |
| T14 | Success reported before the transaction lands | A receipt with no real transaction | Confirm status before replying | OPEN (D5) |
| T15 | Poisoned product lookup data (negative, huge, string) | Negative or absurd footprints, crashes | Validate outside numbers before use | FIXED today, 7 vectors |
| T16 | Script injection through product names | Account takeover in the browser | `esc()` on every outside string | BUILT in app (checked in shop view) |
| T17 | Tampered CDN script | Code runs in every user's browser | Self-host or integrity hashes, CSP | OPEN (D7) |
| T18 | Personal data in a receipt label | Privacy breach | Controlled vocabulary or hash the label | OPEN (D8) |
| T19 | Greenwashing claims on screen | Regulator, press, trust damage | Wording table, simulated labels | PARTLY (API labels built, app wording not yet changed) |
| T20 | Browser-side leaderboard gaming and fake accounts | Meaningless scores | Server totals, per-day caps, account checks | PLANNED |
| T21 | RPC outage or rate limit | Retirements fail | Second provider, timeout, alert, clear error | PLANNED |
| T22 | Memo or rent costs at volume | Cost blow-up | Merkle batch anchoring, see SCALING.md | PLANNED |
| T23 | Over-trust in the claim "single register" | Credibility loss | Careful wording, CAD Trust acknowledged | BUILT in docs |
| T24 | Hostile coding agent or prompt injection | Rules bypassed | Router, scope lock, ROOTS gate, no secrets in context | PARTLY |
