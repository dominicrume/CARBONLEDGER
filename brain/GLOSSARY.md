# Glossary

The words as this company uses them. If a term here disagrees with common usage, this meaning wins inside the repo.

| Term | Meaning here | Source |
|---|---|---|
| Pilot unit | A gram-denominated unit backed only by a simulated attestation. Always "pilot units, not yet verified credits" | `services/api/carbonledger_api/models.py` |
| CLT | One tonne of pilot units, 1,000,000 grams, six decimals | `packages/core/carbonledger/units.py` |
| Retire | Permanently consume a serial range. Never "offset" | rules/HARDENING-PRODUCT.md |
| Serial range | Half-open `[start, end)` inside a batch; `end - start` equals the grams | `db/migrations/0001_registry.sql` |
| Batch | Units issued for one project and vintage; holds the `next_serial` counter | `packages/core/carbonledger/registry.py` |
| Attestation | A verifier's amount for a project; caps issuance | `registry.py` |
| Link | Tie an external registry credit to a batch, once ever | `registry.py` |
| Suspend | Freeze issuance and retirement on a project (model and program only, no API yet) | `registry.py` |
| Receipt (KYA receipt) | A knowyouragenticai-receipts 1.1.0 record: `seal = sha256(canonical(body) + prev)`; outcome ACCEPTED or REFUSED | `packages/core/carbonledger/receipts.py` |
| Refusal | A sealed receipt of an action the rules stopped, with its rule code. Evidence, not an error | docs/DECISIONS.md |
| Receipt id | `CL-` plus 12 hex of the content digest, so volume does not leak | `services/api/carbonledger_api/main.py` |
| Anchor | One Merkle root per interval written by Solana memo `carbonledger:v2:A-<first>-<last>:<root>` | docs/MERKLE-ANCHORING.md |
| Proof | The Merkle path from one receipt to an anchored root | `packages/core/carbonledger/merkle.py` |
| Mandate | A business's permission for an agent key: cap, allow-list, expiry, revoke | `packages/core/carbonledger/mandate.py` |
| KYA | Know Your Agent: mandates plus receipts for agent actions; patent pending GB2611754.9 | docs/PITCH-FACTS.md |
| Idempotency key | One per user intent, bound to the request digest and the caller | docs/DECISIONS.md |
| Typed items | What the server prices: product, flight, ground, energy, meal, fleet, business_flights, commute, products_sold, measured, partner | `models.py` |
| Tier | Estimate quality 1 to 4; tier 4 is "estimate, rounded up" with a 1.25 uplift | `packages/core/carbonledger/estimate.py` |
| Conformance vectors | JSON cases that define right; every port (Python, Rust, SQL, browser) must pass them | `conformance/` |
| XP | Log-scaled points per retirement (5 to 150), first five a day, weekly bonuses. Never proportional to grams | `services/api/carbonledger_api/xp.py` |
| League | Weekly anonymous ranking by XP, never by footprint | `services/api/carbonledger_api/growth.py` |
| Frontline, World clock, cleared country | The symbolic game: countries cleared smallest emitter first, from OWID data | rules/COMPLIANCE.md C13 |
| Dry run | The fake chain client; signatures start `dryrun-` | `packages/core/carbonledger/chain.py` |
| ROOTS, 13 gates, HV, SEEDLING, waiver | The ship-gate score; an HV check not ROOTED needs a dated waiver with an owner | rules/roots/, ROOTS-SCORE.md |
| Seeker, SGT | Solana Mobile phone; its Genesis Token earns a cosmetic badge only | docs/SEEKER-DAPP-STORE.md |
| DRI | The one named human who answers for a decision. Today: Rume | DEBT.md |
| VOREM style | Motion that follows the words, presenter's own labelled voice, audited layout, -14 LUFS | the owner's vorem-video skill |
| Sensor, policy, tool, gate, learning | The five layers of a self-improving loop | brain/README.md |
| Run record | One JSON line an agent appends after a task | brain/feedback/SCHEMA.md |
