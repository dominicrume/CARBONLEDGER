# Shared Pointers and Open Decisions

## Pointers
- packages/core/carbonledger/   units, estimator, registry model, mandate, receipts, chain clients
- services/api/                 the API
- programs/carbon_registry/     the Anchor program (not compiled yet)
- apps/web/                     the app (imported baseline, see docs/PROVENANCE.md)
- conformance/                  vectors every implementation must pass
- db/migrations/                Postgres schema (not executed yet)
- docs/DECISIONS.md             every real decision, dated

## Open decisions (the build waits on these)
| #  | Question | Status |
|----|----------|--------|
| 1  | Who wrote the baseline app, and how is its ownership recorded in the founders' agreement (Schedule 2)? | OPEN, ask today |
| 2  | Chain: Solana now, own chain never-or-later. Recommended in docs/DECISION-CHAIN.md. The partner prefers an own chain first. | OPEN, partner meeting |
| 3  | What backs one CLT? Units from the trust's own projects under an accredited methodology, or retired credits from a registry? Verra requires its written consent for tokens built on its credits. | OPEN, blocks any "real" claim |
| 4  | Verification: the partner's tech contact has verbally offered a farmer app with GPS photos plus satellite imagery. Nothing is written or shared. | OPEN |
| 5  | Trust structure for the land (charitable trust, crops to the farmer's family). Needs a lawyer. | OPEN |
| 6  | Price: 250 pounds a tonne is a demo setting in the app config. What sets the real price? | OPEN |
| 7  | Open-source licence for the hackathon repo, checked against the pending patent application. | OPEN, before publishing |
| 8  | Hackathon: Team Leader, both founders registered, heads of terms signed. | OPEN, today |
| 9  | Accelerator terms (SAFE plus token warrant, percentage unpublished): who reads and signs. | OPEN, only if we win |
| 10 | Login for the API, and where signing keys live. | OPEN, before any public URL |
| 11 | Funded devnet key for the demo (free faucet), held outside the repo. | OPEN, today |

## Decision for the partner meeting
The partner wants an own chain first. Our recommendation is Solana first, then decide. The short version to say aloud:
"A chain is a database that strangers trust. People trust the data, not the chain. We earn the data's trust first,
on a chain that already exists. The design stays portable, so an own chain stays possible."
