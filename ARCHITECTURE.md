# Architecture

## The core product
A register where each tonne of CO2e is one unit, each unit can be retired once, and every retirement leaves a
receipt anyone can verify. People reach it through a friendly app: scan a basket, count a journey, run a business
footprint, retire pilot units, watch countries clear. Agents can retire for a business, but only within a mandate.

## What "single register" means here, stated carefully
- It is a register of units issued under our own attested projects, with a rule that stops the same unit being
  retired twice or the same external credit being linked twice.
- It is not a claim that the world has no register. About 26 registries exist (Straits Times via the World Bank),
  and the Climate Action Data Trust already links their data. Our wedge is the retirement and receipt layer with a
  consumer front end, plus an anti double-count rule across registries we link.
- Verra requires written consent for tokens built on its credits (registry terms, clause 1.9, per Verra's statement
  quoted in January 2026). So we do not wrap Verra credits. Backing is an open decision (CONTEXT.md, item 3).

## Layers
```
 Browser app (apps/web)           shows, never decides. No key.
        |  HTTPS
        v
 API (services/api)               validates, decides, records. Holds the signing key.
   |- estimator   (packages/core) cited factor tables, server side
   |- registry    (packages/core) reference model, same rules as the program
   |- mandate     (packages/core) agent limits: cap, allow-list, expiry, revoke
   |- receipts    (packages/core) hash chain, head hash is what goes on-chain
   |- chain client                DryRun now, Solana memo next, Anchor program after
        |
        v
 Solana (devnet first)            memo carries receipt id and hash only
 Anchor program (later)           registry rules enforced on-chain, PDAs make double use impossible
 Postgres (later)                 same rules again, as constraints and append-only triggers
```

## The retire flow
1. The app sends grams, kind, label and a country. It includes an idempotency key.
2. The API checks the request shape strictly, then any mandate, then the registry rules on a copy of the state.
3. It builds the receipt, computes the hash it will have, and writes that hash to the chain client.
4. Only if the chain write succeeded does it commit the registry change and the receipt. Otherwise nothing is recorded.
5. It returns the receipt, the serial range, the signature and the explorer link. The same key replays the same answer.

## Three layers of truth (from your biomass work)
Blockchain records what it is told. A register is only as honest as its inputs.
- Layer A, ground truth: GPS photos from a farmer app plus satellite imagery. Real MRV. Not built. Offered verbally.
- Layer B, the ledger: this repo. Cheap, replaceable, honest about what it knows.
- Layer C, attestation: a named verifier signs. No attestation, no issuance. This is rule one of the registry.
Layer A is the durable part. Layer B can change chain without losing anything.

## Chain strategy
Solana now. Portable by design: the rules live in a language-neutral set of vectors, the core has no Solana types,
and the chain client is an interface. An own SVM chain or rollup, or an EVM port, stays a deployment decision.
See docs/DECISION-CHAIN.md for the facts and the triggers for revisiting.

## What is built today
| Piece | State |
|-------|-------|
| Estimator port, 133 golden vectors from the app's own code | Built, tested |
| Units and price rules | Built, tested |
| Registry reference model, 10 vectors and a 20,000-step random attack | Built, tested |
| Mandate, 8 vectors | Built, tested |
| Receipt chain with tamper tests | Built, tested |
| API: strict input, idempotency, rollback, mandates, audit verify, closed CORS | Built, tested |
| Solana memo transaction, built and signed offline, address verified | Built, tested offline |
| Sending that transaction to devnet | Written, NOT run (no network in the sandbox) |
| Web ledger wired to the API | Ran in Node against the live API, NOT yet in a browser |
| Anchor program | Written, NOT compiled |
| Postgres schema | Written, NOT executed |
| Server recomputation of footprints, login, MRV, payments | Not built |

## Folder map
```
carbonledger/
  START-HERE.txt  CLAUDE.md  CONTEXT.md  ARCHITECTURE.md  BREAK.md  DEBT.md  ROOTS-SCORE.md  CHANGELOG.md
  rules/        ENGINEERING  HARDENING-ENGINEERING  HARDENING-PRODUCT  SCALING  COMPLIANCE
    roots/      ROOTS.md  KYA-13-GATES.md  check_roots.py
  docs/         DECISION-CHAIN  THREAT-MODEL  MRV-LAYERS  HACKATHON-48H  PITCH-FACTS  PROVENANCE  DECISIONS
    ux/         DESIGN-SYSTEM  FLOWS
  workspaces/   estimator registry retirement verification agent web security  (each: CLAUDE.md + stages/NN/CONTEXT.md)
  apps/web/     the app (imported baseline, patched ledger)
  services/api/ carbonledger_api
  packages/core/carbonledger/   units estimate registry mandate receipts chain data_factors.json
  programs/carbon_registry/     Anchor program, Cargo.toml, README
  db/migrations/                0001_registry.sql
  conformance/                  estimate_vectors.json registry_vectors.json mandate_vectors.json
  tests/                        pytest
  scripts/                      export_estimator.mjs  scan_secrets.py
  .github/workflows/ci.yml
```
