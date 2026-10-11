# ROOTS Score

Scored by the people who built it, against what exists today. A ROOTED check has a pointer. An HV check that is not
ROOTED carries a dated waiver with an owner. Re-score after every phase.

| # | Check | State | Pointer | Waiver |
|---|-------|-------|---------|--------|
| 1 | Written rules | ROOTED | rules/ENGINEERING.md, HARDENING-ENGINEERING.md, HARDENING-PRODUCT.md, SCALING.md, COMPLIANCE.md | |
| 2 | Spec before code | ROOTED | workspaces/*/stages/*/CONTEXT.md, tests/test_repo_contracts.py | |
| 3 | Decomposition | ROOTED | one module per concern, size test in tests/test_repo_contracts.py | |
| 4 | Planning [HV] | SEEDLING | docs/HACKATHON-48H.md, rules/SCALING.md | 2026-10-11 owner Rume: plans exist for the hackathon and for scaling. No per-stage plan review yet. Review by 2026-10-14. |
| 5 | Exit criteria | ROOTED | every stage CONTEXT.md has a Completion section, checked by test | |
| 6 | Context management | ROOTED | every workspace CLAUDE.md has a What NOT to load table, checked by test | |
| 7 | Sandboxing [HV] | SEEDLING | rollback on chain failure, tests/test_api.py | 2026-10-11 owner Rume: code-level rollback is proven. No process isolation, no database triggers run, no kill switch. Review by 2026-10-18. |
| 8 | Trajectory [HV] | ROOTED | packages/core/carbonledger/receipts.py, tests/test_chain_receipts.py, GET /v1/audit/verify | |
| 9 | Guardrails | ROOTED | registry.py, mandate.py, API request models, tests/test_registry_mandate.py, tests/test_api.py | |
| 10 | Verification | ROOTED | 203 tests, shared vectors, random attack, BREAK.md | |
| 11 | Grounding [HV] | SEEDLING | estimator cites tier and source, parity-tested against the app | 2026-10-11 owner Rume and partner: no real MRV evidence exists and attestation is simulated. Units are labelled simulated. Review by 2026-10-25. |
| 12 | CI/CD [HV] | SEEDLING | .github/workflows/ci.yml | 2026-10-11 owner Rume: written, never run on a real runner. Review at first push, by 2026-10-13. |
| 13 | Feedback [HV] | SEEDLING | BREAK.md, DEBT.md, CHANGELOG.md | 2026-10-11 owner Rume: one finding found, fixed and recorded (F1). The loop has not yet turned over time. Review by 2026-10-18. |

Summary: 8 ROOTED, 5 SEEDLING (all five are HV checks with dated waivers), 0 ABSENT.
Verdict: fit for a hackathon demo that says plainly what is simulated. Not fit for real units, real money or a public URL.
