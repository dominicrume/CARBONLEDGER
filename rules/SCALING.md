# Scaling: Product and Technical

Figures marked ASSUMPTION are working numbers to test. Figures marked CHECK need a live lookup before use.

## Stages
| Stage | What exists | Gate to enter the next stage |
|---|---|---|
| 0 Demo | In-memory API, DryRun or devnet memo, simulated units | Hackathon submitted, receipts verify, claims reviewed |
| 1 Pilot | Postgres, login, one verifier, one real project, Solana devnet then mainnet | Trust structure and backing decided, counsel sign-off, Anchor program independently reviewed |
| 2 Network | Several projects and verifiers, link to the Climate Action Data Trust, public explorer, MRV evidence flow | Verifier agreements signed, evidence process audited once |
| 3 Market | Payments, partners, business accounts at volume | Consumer-law and payments checks done |
| 4 Own chain review | Only if a trigger below fires | See docs/DECISION-CHAIN.md |

## Technical scaling facts to design for
1. One batch, one hot counter. Every retirement in a batch writes that batch's `next_serial`, so retirements to one
   batch run one after another. Fix: many smaller batches, and routing a retirement to any batch with units left.
2. Per-retirement accounts cost rent. The Retirement account is about 140 bytes, and rent-exempt storage is roughly
   0.0019 SOL each (ASSUMPTION from the usual 6,960 lamports per byte including a 128 byte header; CHECK with
   `solana rent 140`). A million retirements would lock about 1,900 SOL. Fix before volume: anchor a Merkle root
   of many receipts in one transaction, keep receipts in Postgres, and prove any receipt against the root.
3. Base fee is small (ASSUMPTION: 5,000 lamports a signature; CHECK). Fees are not the limit. Rent and hot accounts are.
4. Memo-per-receipt (today) is simple and fine for a demo. It does not scale as the long-term design.
5. Estimation is cheap CPU. The estimator can sit behind a cache keyed by product code and weight.
6. Reads dominate. Put the public explorer on read replicas and a cache, never on the signing service.

## Product scaling
- One country queue, one price, one trust. Add projects only when a verifier exists for each.
- Business accounts need roles, invoices, and a signed statement of what was retired and why.
- Partner-funded retirements (the app's "partners pay the trustee price") need contracts and a clear statement of who
  pays, who receives the receipt, and what it may be called.

## Triggers that justify an own chain
Revisit only if one is true and written down:
- A registry, regulator or standards body requires a permissioned validator set for adoption.
- Volume or finality needs are shown, with data, to exceed what a shared chain gives at acceptable cost.
- A governance body of registries wants to run validators and set rules together.
- Data residency rules require it.
Even then, prefer an SVM rollup or app-chain framework, or an integration with the Climate Action Data Trust, over
forking the base validator client.
