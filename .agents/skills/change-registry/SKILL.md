---
name: change-registry
description: Change a CarbonLedger registry rule (projects, attestation, batches, issuance, serials, links, suspension, retirement) consistently across the conformance vectors, the Python model, the Rust Anchor program and the Postgres migrations. Use whenever a rule of the register itself changes or is questioned.
---

# Change a registry rule

The rules live in the vectors. Every port (Python model, Rust program, SQL constraints, browser) must pass the same
vectors. This is the highest-risk job in the repo.

## Load
- `workspaces/registry/CLAUDE.md` and its four stages: 01-rules, 02-model, 03-program, 04-database.
- `conformance/registry_vectors.json`, `conformance/mandate_vectors.json`.
- `packages/core/carbonledger/registry.py`, `programs/carbon_registry/src/lib.rs`, `db/migrations/`.

## Order (never skip)
1. Decision entry first (skill record-decision). A rule change is a new brief under the scope lock.
2. Add the vector. Watch it fail.
3. Change the model until the vectors and the 20,000 step random attack pass.
4. Change the program; `npm run vectors` replays the vectors in LiteSVM (needs Rust, Solana, Anchor 0.31.1).
5. Change the migration; the Postgres tests must refuse what the model refuses.

## Gates
- `python -m pytest -q tests/test_registry_mandate.py`
- `DATABASE_URL_TEST=... python -m pytest -q tests/test_db_migrations.py tests/test_db_store.py`
- `npm run vectors`, `scripts/check.sh`, hostile review, human review.

## Policy
- ASK for every merge here. NEVER deploy the program, touch mainnet, or sign with the upgrade authority.
- Invariants that must survive any change: a gram retired once; issued never above attested; nothing issued
  without attestation; an external credit linked once; history append-only.

## Report
One run record naming the vector ids added.
