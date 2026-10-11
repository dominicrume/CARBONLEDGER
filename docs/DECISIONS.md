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
