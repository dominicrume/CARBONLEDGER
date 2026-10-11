# ROOTS Score

Scored by the people who built it, against what exists today. A ROOTED check has a pointer. An HV check that is not
ROOTED carries a dated waiver with an owner. Re-score after every phase. Last re-score: 2026-10-11, end of the
autonomous run (docs/RUN-LOG.md).

| # | Check | State | Pointer | Waiver |
|---|-------|-------|---------|--------|
| 1 | Written rules | ROOTED | rules/ENGINEERING.md (rule 1 and 6 updated), HARDENING-ENGINEERING.md, HARDENING-PRODUCT.md, SCALING.md, COMPLIANCE.md, docs/MERKLE-ANCHORING.md | |
| 2 | Spec before code | ROOTED | workspaces/*/stages/*/CONTEXT.md, docs/AUTONOMOUS-RUN.md, tests/test_repo_contracts.py | |
| 3 | Decomposition | ROOTED | one module per concern (models, state, store, lookup, recompute, accounts, auth, agentsig, merkle, outbox), size test in tests/test_repo_contracts.py | |
| 4 | Planning [HV] | ROOTED | docs/AUTONOMOUS-RUN.md (eight blocks with exit criteria), docs/RUN-LOG.md (one line per step), docs/HACKATHON-48H.md, rules/SCALING.md | |
| 5 | Exit criteria | ROOTED | every stage CONTEXT.md has a Completion section, checked by test; every run step names its proving test | |
| 6 | Context management | ROOTED | every workspace CLAUDE.md has a What NOT to load table, checked by test | |
| 7 | Sandboxing [HV] | SEEDLING | rollback on chain failure (tests/test_api.py), database triggers and constraints proven (tests/test_db_migrations.py, tests/test_db_store.py), API keys, rate and size limits, server deadline | 2026-10-11 owner Rume: no process isolation, no suspend endpoint (the lever exists in the model only), no TLS in front. Review by 2026-10-18. |
| 8 | Trajectory [HV] | ROOTED | receipts.py, merkle.py, outbox.py, GET /v1/audit/verify, GET /v1/receipts/{id}/proof, browser verifier, tests/test_chain_receipts.py, tests/test_outbox.py | |
| 9 | Guardrails | ROOTED | registry.py, mandate.py, agentsig.py, auth.py, recompute.py, strict request models, tests/test_registry_mandate.py, tests/test_auth.py, tests/test_api.py | |
| 10 | Verification | ROOTED | 2,081 Python tests (incl. 12 on Postgres), 5 Node tests, 10 browser tests with axe, 10 drills (scripts/drills.py), shared vectors (registry, mandate, signature, estimate, activity, merkle), random attack, BREAK.md | |
| 11 | Grounding [HV] | SEEDLING | estimator and activities cite tier and source and are parity-tested against the app; the server prices every request itself; evidence table and decided-once rule exist (db/migrations/0002) | 2026-10-11 owner Rume and partner: no real MRV evidence exists and attestation is simulated. Units are labelled simulated. Review by 2026-10-25. |
| 12 | CI/CD [HV] | SEEDLING | .github/workflows/ci.yml (pinned to commit hashes, Postgres service, browser test, audits), .github/workflows/recheck.yml, scripts/check.sh | 2026-10-11 owner Rume: never run on a GitHub runner. Review at first push, by 2026-10-13. |
| 13 | Feedback [HV] | ROOTED | BREAK.md (F1 to F17, each fixed one carries its test), DEBT.md (paid items name their proof), CHANGELOG.md, drill results recorded 2026-10-11 | |

Summary: 10 ROOTED, 3 SEEDLING (all three are HV checks with dated waivers), 0 ABSENT.
Verdict: fit for a hackathon demo that says plainly what is simulated, and fit for a private pilot on Postgres with
API keys once TLS sits in front. Not fit for real units or real money until a verifier attests a real project and
the authority and verifier keys are in a multisig.
