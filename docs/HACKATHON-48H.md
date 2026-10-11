# Hackathon Plan: Crypto World's Fair

Facts are from Colosseum's official rules PDF unless marked. Deadline: 11:59pm Pacific, 12 October 2026 = 06:59 UTC
on 13 October = 07:59 BST. Submit at least six hours earlier (ASSUMPTION: a safe buffer).

## Rules that can disqualify you
- Every team member registers on colosseum.com before the deadline. The Team Leader uploads the submission.
- One person, one team. One team, one project.
- Content in English. No infringing material. Everyone shown must have agreed.
- Each entrant confirms taking part breaches no employer or other contract.
- Colosseum pays prizes to the Team Leader. Winning also needs due diligence and signed prize documents.
- Winners are announced by 5 December 2026.
- Disclose open-source and third-party code (rule 9). The baseline app is third-party to the team until ownership is settled.

## What is scored (rule 8)
Functionality, potential impact, novelty, user experience, open source and composability, business plan and team.

| Criterion | What we show |
|---|---|
| Functionality | The full path works with a real devnet signature. 203 tests, shared vectors, a random attack. |
| Potential impact | The retirement and receipt layer for consumers and businesses. Cite a market size only after looking it up. |
| Novelty | An anti double-count rule at the register, agent mandates, a consumer layer. Not a new registry claim. |
| UX | The imported app, with honest wording and a verify screen. |
| Open source and composability | Public repo. Memo program now. Mandates name an agent by its ed25519 public key and every agent request is signed (packages/core/carbonledger/agentsig.py), which is the same key shape the Solana Agent Registry uses for identity, so a mandate can later point at a registered agent. Token-2022 non-transferable receipts next. |
| Business plan | App users, business footprints, partner-funded retirements. Price set by the trust, basis still open (CONTEXT item 6). |

## Blocks (UK time, ASSUMPTION: you start now)
1. Now, 30 minutes: both founders register, choose the Team Leader, sign the Founders Heads of Terms, decide the licence question (CONTEXT 7).
2. Block A, 4 hours: run the API and the app locally. Create a free devnet key outside the repo, fund it from the faucet,
   set CHAIN_MODE=solana-devnet, record one real memo. Paste the explorer link into your notes.
3. Block B, 6 hours: confirm the transaction before replying (D5), change the screen wording (HARDENING-PRODUCT), add the verify screen and the mandate screen.
4. Block C, 8 hours, only if Rust tooling works for you: anchor build, replay the 10 registry vectors, deploy to devnet, switch the API to call it.
   If it does not work by the end of the block, stop. The memo path is a legitimate integration. Say so in the pitch.
5. Block D, 6 hours: README, architecture picture, the 3-minute video, honest limits slide, dry run of the demo twice.
6. Submit with the buffer. Then sleep.

## The 3-minute demo
0:00 The problem in one sentence. Do not say no register exists. Say retirement is scattered and double counting is a known risk.
0:20 Scan a basket. Show the tier and source on each line. Press "Retire pilot units".
0:50 The receipt with its Solana signature. Open the explorer.
1:15 Verify: the audit page shows intact. Edit one receipt on screen. It shows the exact index that broke.
1:45 Replay the same request: one retirement. Try to retire more than exists: refused, nothing recorded.
2:10 An agent with a mandate of 1,000 g tries 1,001 g: refused. The owner revokes it: refused again.
2:40 Honest scope: simulated units, what a verifier adds, what ships next.

## Questions judges will ask (have answers)
What backs a unit? Who verifies? Why not wrap Verra credits? Who pays and who benefits? Why Solana? What breaks first at
volume? What happens when a verifier is wrong? Answers live in COMPLIANCE, MRV-LAYERS, SCALING and THREAT-MODEL.

## Submission checklist
- [ ] Both founders registered, Team Leader named, heads of terms signed
- [ ] Employer and contract confirmation made by each founder
- [ ] Public repo, licence chosen after the patent question, third-party code disclosed
- [ ] No key, token or seed in the repo (python scripts/scan_secrets.py)
- [ ] Demo records a real devnet signature, or the pitch says plainly that it uses a dry run
- [ ] Screens say "pilot units", never "offset" or "carbon neutral"
- [ ] Video under the form's limit (CHECK the submission form for video and deck rules)
- [ ] Submitted at least six hours early
