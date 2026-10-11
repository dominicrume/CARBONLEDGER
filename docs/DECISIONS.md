# Decisions Log

Write each real decision on the day it is made.

---
Date: 2026-10-11
Decision: Build on Solana (devnet for the demo). Do not fork Solana or start an own chain now.
Why: The hackathon's Solana track scores products that integrate with Solana. A forked chain is not Solana, and
building one is a multi-month job. Details and sources in docs/DECISION-CHAIN.md.
Who agreed: Proposed by engineering. Awaiting Rume and the partner.

---
Date: 2026-10-11
Decision: Units are labelled simulated until a verifier attests real ones. The words "offset", "carbon neutral" and
"verified credit" are not used for pilot units.
Why: Without verification and a backing definition, those words are claims we cannot support.
Who agreed: Proposed by engineering. Awaiting Rume and the partner.

---
Date: 2026-10-11
Decision: The server is the source of truth for numbers and records. The browser holds no key.
Why: A browser can be edited by its user. A leaderboard and a register must not trust one.
Who agreed: Proposed by engineering. Awaiting Rume and the partner.

---
Date: 2026-10-11
Decision: The public receipt id is derived from the receipt content (CL- plus 12 hex of its digest). The sequential
receipt number stays inside the registry and never goes on-chain.
Why: A sequential id in a public memo tells anyone the run rate. The content digest tells them nothing.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: One idempotency key per user intent, created when the confirm sheet opens and reused on every retry. A
client timeout says the outcome is unconfirmed. Only the server says "Nothing was recorded."
Why: A fresh key per call turned a retry into a second retirement, and a timeout message that claimed nothing was
recorded could be false. Rule 4 requires that an error says truthfully what was not recorded.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: The Countries game is labelled symbolic on screen. A CLT is a tonne of simulated pilot units retired
against a project today, never a tonne of the 1850 stock.
Why: Keeps the unit definition clean and avoids the "immutable greenwashing" trap in docs/MRV-LAYERS.md.
Who agreed: Engineering, during the autonomous run. Awaiting Rume and the partner.

---
Date: 2026-10-11
Decision: Rule 6 refined. The API checks chain health before committing (if the chain is down, nothing is recorded).
The receipt then commits under the lock and an anchor worker submits and confirms outside the lock, retrying a
dropped transaction up to five times. Nothing is called "recorded on Solana" until confirmed. A failed anchor is
shown as failed on the receipt, in /health and in /v1/audit/verify.
Why: Holding the lock across a network call serialised every retirement behind one RPC round trip, and the old
flow said "recorded" on submission, before confirmation (D5). Merkle batch anchoring (SCALING item 2) needs
receipts to commit before the anchor anyway. The health check keeps the honest behaviour when the chain is down.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: Every write endpoint needs an API key sent as a bearer header. The server stores only a salted hash. A
key carries a role (personal, business, agent, verifier, authority) and an owner id. Mandate owners come from the
key, never from a field. Reads stay public so anyone can verify a receipt. The browser may hold an API key: it is
a login, like a password, kept in browser storage. It signs nothing and decides nothing. "The browser holds no
key" in CLAUDE.md means no signing key.
Why: D2 and T12. An open API lets anyone retire pilot units and spam the chain. Public reads keep receipts verifiable.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: Every retire request carries typed items (product by barcode or category, flight, ground, energy, meal, the
six business areas, partner reward). The server prices them with the same tables as the app, proven by golden
vectors, and refuses a total below its own figure. A higher total is allowed because estimates err high. Product
facts come from the server's own catalogue or its own Open Food Facts lookup, never from the client.
Why: D1 and T7. A browser total is a claim. The server must be able to stand behind every receipt it signs.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: With DATABASE_URL set, every committed change is written to Postgres in one transaction before the
in-memory state changes, so the database constraints (exclusion on serial ranges, append-only history, issuance
cap, anchors that only move forward, evidence decided once) are a second guard. At start the server rebuilds from
the rows and verifies the receipt chain; a broken chain refuses to start. Without DATABASE_URL, state is in memory.
Why: D4 and D9. A restart must not lose receipts or keys, and an insider with database access must still be
unable to rewrite history quietly.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: Anchor one Merkle root per interval instead of one memo per receipt. Each receipt keeps its proof path,
the API serves it, and the verify screen recomputes the root in the browser. The program design drops the
per-retirement account and gains an anchor_root instruction with contiguous intervals. Details in
docs/MERKLE-ANCHORING.md.
Why: D15 and T22. Memo per receipt and rent per retirement do not scale. A root per interval does, and a proof
per receipt keeps every receipt individually verifiable by anyone.
Who agreed: Engineering, during the autonomous run. Awaiting Rume.

---
Date: 2026-10-11
Decision: The Anchor program (not yet compiled) holds up to three verifier keys with add and rotate instructions,
needs two different verifiers to agree on any attestation above a threshold, has an unsuspend instruction, and
does not enable init-if-needed.
Why: T4 (one stolen verifier key), the missing lever to lift a suspension, and a known re-initialisation foot-gun.
Who agreed: Engineering, during the autonomous run. Awaiting Rume. Compiles and vectors wait on the toolchain.

---
Date: 2026-10-11
Decision: The receipt is the KYA receipt (knowyouragenticai-receipts 1.1.0, SPEC.md v1.3). Every attempt that
reaches a decision is sealed into the chain, ACCEPTED with its serial range or REFUSED with the rule that stopped
it, and the seal is the hash that is anchored and stored. CarbonLedger's own fields (receipt id, grams, serial
range, digests) are added to the wire format; the package's verifier and the verifier page check the seals
regardless. GET /v1/audit/receipts.json exports the bare chain. The `ledger` field names the decider and says the
units are simulated. Malformed and unauthenticated requests are not attempts and are not recorded.
Why: "What did it try to do that you stopped?" is the question an auditor asks about an agent, and the mandate path
exists for agents. A refusal that leaves no trace cannot be audited. One format, already specified and verifiable
by anyone, beats a private one.
Who agreed: Rume asked for it (2026-10-11). Engineering implemented it. Format rule 1 of the package applies: the
chain proves consistency, not origin; origin comes from the anchored root.

---
Date: 2026-10-11
Decision: The front end is rebuilt around the game loop from the partner call: a level ring in the header, a
Frontline mission strip on every acting screen, XP on the retire button (one gram is one point), a reward moment
above the receipt, a command centre on Me, a world clock on World fed by a new public GET /v1/stats/world, and a
celebration when a country is cleared. One accent (emerald), gold only for rewards, Outfit and DM Mono, Phosphor
icons vendored as a sprite, dark and light themes, motion off under reduced motion. The tab bar keeps the
partner's seven sections even though the guideline is five, because the demo needs each one reachable in one tap.
Why: the partner said it plainly: this is a highly gamified project, and the screens were dry. Wording rules,
the simulated tag and the server as the only source of truth are unchanged.
Who agreed: Rume asked for it after the call (2026-10-11). Engineering built it. Awaiting the partner's eye.
