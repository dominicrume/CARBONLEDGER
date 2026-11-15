# KYA Record Sprint: the offer for November 2026

Status: draft for Rume. Price: Rume sets it. Before the first invoice: a decision entry for service revenue taken
outside the app (payments in the app stay out of scope, CLAUDE.md scope lock and COMPLIANCE C10).

## Who it is for
The CTO, head of engineering or operations lead at a UK small company or scale-up with one AI agent already live
where it touches money or customers: refunds, support, operations. They have shipped the agent. They cannot yet
answer three questions about it: What did it do? What was it refused? Who can check?

## The promise
In one sprint, one of your agent workflows gets a record the agent cannot edit, and you can show a buyer, an
auditor or your board every action and every refusal.

## What is in it (all of it exists in code today)
1. **Gates audit.** The workflow is scored against the 13 KYA gates (`rules/roots/KYA-13-GATES.md`, method patent
   pending GB2611754.9). You get the score, the gaps and the order to close them.
2. **A working mandate around the riskiest action.** A cap, an allow-list, an expiry and a revoke switch. The agent
   signs every request with its own key (ed25519). Code: `packages/core/carbonledger/mandate.py`, `agentsig.py`.
3. **A sealed receipt for every decision.** Accepted and refused alike, hash-chained, anchored as a Merkle root on
   Solana devnet, a test network. Code: `receipts.py`, `merkle.py`, tests `tests/test_kya_receipts.py`.
4. **A walkthrough film.** A short VOREM film of your own workflow refusing an over-cap request and showing the
   receipt. For your team, your board or your buyers.

## What is honestly not in it
Production readiness, mainnet, a security audit, multisig keys (DEBT D6), rules enforced on chain by the API
(D3), compliance certification, and anything about carbon units. The receipts are a working prototype on a test
network.

## Proof to show on the call
- A live refusal: an agent goes over its cap, the refusal is sealed, the receipt checks in the browser, the root
  is on the devnet explorer (first anchor 393qHy9N...KMJ7, Solana devnet, a test network).
- The test suite: over 2,100 Python tests, refreshed by `scripts/check.sh` before the call.
- An honest self-score of CarbonLedger against the same 13 gates, open waivers included.

## Three design-partner places
Three places only, so each workflow gets full attention. A design partner gives a short written quote and lets
the anonymised refusal record be shown, if both sides agree.

## Outreach message (passes `check_post.py`)
See `kya-sprint-dm.txt` in this folder.
