# Truth Register

Read this before writing any claim: in code, on a screen, in a pitch, a post or a reply. Checked 2026-11-09.
When something changes, change it here in the same commit (skill: record-decision).

## True today (say it, with the proof)
| Claim | Proof |
|---|---|
| The server recomputes every footprint from typed items and refuses a lower total | DEBT D1; tests/test_activity_parity.py (1,787 vectors), tests/test_api.py |
| Writes need a login: hashed API keys with roles, rate and size limits, a server deadline; agents sign with ed25519 | DEBT D2; tests/test_auth.py |
| Receipts are hash-chained KYA receipts; refusals are sealed too; tampering names the first bad entry | tests/test_kya_receipts.py, tests/test_chain_receipts.py |
| Receipts are anchored on Solana devnet as one Merkle root per interval, confirmed before shown as anchored | DEBT D5, D14, D15; first tx 393qHy9N...KMJ7, slot 510097199 |
| A gram is retired once; issued never exceeds attested; history is append-only | tests/test_registry_mandate.py (20,000 step attack), tests/test_db_migrations.py |
| The registry program compiles, passes all 10 vectors in LiteSVM, and is deployed on devnet | DEBT D3 (part paid); program 3dGd2V1ykcmahyCQvhri4R2WhabT83hmm2WNz2r788Zj |
| Personal data never goes on chain; free text is kept only as a hash | DEBT D8; tests/test_api.py note test |

## Not true yet (never claim it)
| Not true | Why | Tracked |
|---|---|---|
| Units are verified or real credits | The attestation is simulated; no evidence has been ingested; no verifier is named | D11, ROOTS check 11 |
| The API enforces the rules on chain | The program is deployed but the API anchors by memo and calls no instruction; the program is unreviewed and its upgrade authority is the devnet hot key | D3 |
| CI has run on GitHub | The workflows are written and pinned but have never run on a runner | D6, ROOTS check 12 |
| Keys are safe for production | Authority and verifier keys are not in a multisig | D6, BREAK F5 |
| An operator can suspend a project or re-anchor a failed receipt through the API | The suspend lever exists only in the model and the program; no re-anchor command | ROOTS check 7, D24 |
| Data licences are cleared | Open Food Facts (ODbL), OWID, Agribalyse unchecked | D12, COMPLIANCE C13 |
| Ready for real money or mainnet | No payments in phase 1; no legal review of claims, tokens or the trust | COMPLIANCE C5 to C10 |

## Never say (any channel)
- "offset", "carbon neutral", "net zero", "climate positive", "verified credits" (tests/test_web_wording.py bans them on screen).
- "Recorded on Solana" without "devnet, a test network".
- "The world has no registry for carbon credits" (false), "the only registry", "fully decentralised", "audited",
  "our patent" (say "patent pending").
- Any number without a source: no market sizes, no prices beyond the labelled demo price, no invented results.
- Any person's voice, face or words without their consent and an on-screen label for AI voices.

## Drift found on 2026-11-09 (documents that disagree with the code)
Fix the document, not the code, unless the code is wrong. Each line is a learning item (loop/LEARNING.md).
| Where | Says | Code says | Status |
|---|---|---|---|
| CLAUDE.md "Not yet true" | No server recompute, no login, program not compiled | D1, D2 paid; D3 part paid | Fixed 2026-11-09 |
| ARCHITECTURE.md "What is built today" | Devnet never sent, Postgres never run, no login, no compile | D4, D14, D2, D3 | Open |
| README.md, docs/PITCH-FACTS.md | First devnet transaction not sent | D14 paid 2026-10-12 | Open: a pitch would under-claim and contradict itself |
| CONTEXT.md, docs/DECISIONS.md, docs/ux/DESIGN-SYSTEM.md | One gram is one XP | Log scaled XP with daily and weekly bonuses (`services/api/carbonledger_api/xp.py`, commit d745f72) | Open |
| CONTEXT.md | Demo price GBP 250 a tonne | GBP 100 (`apps/web/js/config.js`) | Open |
| docs/THREAT-MODEL.md | T7, T12, T14, T17, T18 open | Paid in DEBT | Open |
| DEBT.md header | D14, D19 open | Rows say paid | Open |
| rules/ENGINEERING.md rule 7 | Triggers not yet run | D4 paid | Open |
| spec.yaml | No entries for accounts, auth, events, metrics, league, Seeker, Studio | All built since | Fixed 2026-11-15: declared; scope drift 11.00 to 1.00 |
| README.md, CLAUDE.md, rules/HARDENING-PRODUCT.md | The word "simulated" for units | Retired 2026-10-12 for "pilot units, not yet verified credits" (decision unconfirmed by Rume) | Open, needs Rume |
| ROOTS-SCORE.md | Waivers for checks 7, 11, 12 | Review dates 2026-10-13, 18, 25 passed; no re-score since 2026-10-11 | Open, needs Rume |
| docs/ENVIRONMENT.md | ANTHROPIC_API_KEY only for category suggestion | VOREM Studio spends it on scripts inside the ledger API | Open, needs a decision |
| media/brand/BRAND-VOICE.md | Say no price; clone in ElevenLabs from old samples; orange captions | Site shows GBP 100 demo price; F5 clone with scored refs; palette is light blue from 2026-10-28 | Open |
