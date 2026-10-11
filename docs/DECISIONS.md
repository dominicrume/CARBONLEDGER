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
