# Engineering Rules

Each rule has a number. Tests and reviews cite the number. A rule marked ENFORCED has a test that fails if it breaks.

1. ENFORCED (since 2026-10-11). The server records and holds the signing key; the browser holds none. The server prices every retirement itself from typed items (products by barcode from its own catalogue or lookup, flights, ground, energy, meals, the six business areas, partner rewards) with the same tables as the app, proven by 1,787 golden vectors, and refuses a total below its own figure. Tests: tests/test_activity_parity.py, tests/test_api.py recomputation tests.
2. ENFORCED. Grams are integers. Money is Decimal. A float near either is a bug.
3. ENFORCED. Validate at the edge. Strict models, unknown fields refused, every number bounded, every string capped.
4. ENFORCED. Fail loud. An error says what happened and what was NOT recorded. No silent defaults.
5. ENFORCED. Every write endpoint takes an idempotency key. The same key and request returns the same answer.
   The same key with a different request is refused.
6. ENFORCED. Refined 2026-10-11. Before committing, the API checks that the chain is reachable. If it is not,
   nothing is recorded. Under the lock it retires on a copy, appends the receipt and commits. The anchor worker then
   submits and confirms outside the lock. Nothing is called "recorded on Solana" until the chain confirmed it. A
   receipt whose anchor fails after retries is shown as failed, never claimed. Tests: tests/test_api.py anchor tests.
7. PARTLY. The receipt chain is append-only and tamper-checked in code (enforced). The database triggers are written and not yet run (DEBT D4).
8. Secrets live in the environment or a secret store. scripts/scan_secrets.py must pass before every commit. It runs in CI once CI has run (DEBT D6).
9. Dependencies are pinned. Run `pip-audit` and `npm audit` in CI. CDN scripts are pinned to exact versions, then
   moved to the repo or given integrity hashes (see DEBT D7).
10. Behaviour is defined by vectors in conformance/. The Python model passes them (enforced). The Anchor program and any
    future port must pass the same files (DEBT D3).
11. ENFORCED. Time is injected. Nothing reads the clock inside a rule.
12. Error codes are stable names (OVER_RETIREMENT, NOT_ATTESTED, ...). Python is tested. Rust and SQL use the same names and are not yet tested.
13. Logs hold ids and hashes only. No names, no coordinates, no free text from users.
14. One config source per runtime: apps/web/js/config.js for the app, environment variables for the server.
15. Write a dated entry in docs/DECISIONS.md when you decide something.
16. ENFORCED. No Python module over 400 lines (ASSUMPTION: a size that keeps files reviewable). Split first.
17. Text from outside is untrusted. In the UI, escape it with `esc()` before it touches HTML. In the server, never
    pass it to a model as an instruction.
18. A change to a rule, a vector or a factor table is a decision entry, a test change and a changelog line, together.

## Definition of done for any change
- A test fails first, then passes.
- `python -m pytest` is green and `python rules/roots/check_roots.py` exits 0.
- `python scripts/scan_secrets.py` finds nothing.
- ROOTS-SCORE.md and DEBT.md say what is still not true.
