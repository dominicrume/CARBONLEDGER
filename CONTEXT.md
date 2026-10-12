# CarbonLedger: Context

Read this first in any new session, after CLAUDE.md. Updated 2026-10-12.

## What it is, in one breath
A gamified app where people and businesses retire simulated pilot carbon units for what they buy, travel and use,
watch countries clear together, and verify every receipt on Solana. One register, one receipt format, one proof
anyone can check. Units stay labelled simulated until a named verifier attests a real project.

## What is live now
| Piece | Where | State |
|---|---|---|
| App and API | https://carbonledger-production.up.railway.app | Live, Postgres, demo logins on |
| Chain mode | Solana devnet | Live since 2026-10-12. First real anchor: [393qHy9N...KMJ7](https://explorer.solana.com/tx/393qHy9NgYoNaEg8pYm3CikXono4PjDdxtbAep3Ki4YfRyzDLevmrzuTbpiHoKRUQ9tBbGp8rxn2V9vvqmXMKM7J?cluster=devnet), slot 510097199 |
| Registry program | devnet `3dGd2V1ykcmahyCQvhri4R2WhabT83hmm2WNz2r788Zj` | Deployed 2026-10-12, passes all 10 registry vectors in LiteSVM. Not yet called by the API (it anchors by memo) |
| Hot key | `7DQZmWuTomLpBSHD44D3whxjPUja2Rt7Mm3LNGNewiyh` | Devnet only. File at ~/.config/solana/carbonledger-devnet.json, secret on Railway. Upgrade authority of the program |
| Code | github.com/dominicrume/CARBONLEDGER (private) | main |
| Brand | LOGO/ (source), apps/web/brand/ (cropped mark, favicon, share card) | In the header, favicon, receipt, reward, onboarding, Verify |

## Do we have our own chain?
No, and that is on purpose (docs/DECISION-CHAIN.md). We have our own **register on Solana**: the registry program
above, plus the API's receipt chain anchored to devnet. Any marketplace can check a CarbonLedger receipt against
the public chain without trusting us. An own chain stays possible later because the rules live in the
conformance vectors, not in Solana types.

## How the pieces fit
Browser (apps/web, shows and asks) -> API (services/api, prices, decides, records, holds the signing key) ->
Postgres (rows, second guard) and Solana devnet (one Merkle root per interval, by memo). Receipts are KYA receipts
(knowyouragenticai-receipts): refusals are recorded too. Details in ARCHITECTURE.md and docs/MERKLE-ANCHORING.md.

## The product rules that matter most
- Retire pilot units, never "offset". Simulated tag beside every unit count.
- The server prices every retirement itself. A browser total is never a score.
- One gram retired is one XP. Levels, titles, badges, streaks and daily quests all derive from server history.
- A demo login is minted silently on the demo, and plays both the personal and the business league (D27, D28).

## The game, as built
Level ring with a title (Seed to Earthkeeper) in the header, Frontline mission strip on every acting screen, XP on
every retire button, a reward moment with count-up, level-up and badges, Today (three daily quests), next quests
from the skill tree, a badge shelf, leagues, the World clock with a celebration when a country is cleared,
a first-visit welcome. See docs/ux/DESIGN-SYSTEM.md.

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
