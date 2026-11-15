---
name: retire-units
description: Change, debug or explain the CarbonLedger retirement path, from the retire request to the sealed receipt, the anchor outbox and the Solana devnet Merkle root. Use for refusal codes, idempotency, serial ranges, receipts, proofs, failed or pending anchors, and the retire endpoint.
---

# Retire units

A request becomes a recorded, verifiable receipt, or nothing. A gram is retired once.

## Load
- `workspaces/retirement/CLAUDE.md` and the stage in hand (01-request, 02-record, 03-receipt).
- `services/api/carbonledger_api/main.py` (the retire route), `packages/core/carbonledger/registry.py`,
  `packages/core/carbonledger/receipts.py`, `packages/core/carbonledger/outbox.py`, `docs/MERKLE-ANCHORING.md`.

## The path, in order
1. Strict model: unknown fields, bad types and out of range numbers give 422.
2. Idempotency key per intent; same key with a different body is 409.
3. Mandate and agent signature checks when an agent calls.
4. Server recomputes grams from typed items; a lower client total is refused and sealed as a refusal.
5. Retire on a copy of the registry under the lock; Postgres first, then memory, then the receipt seal.
6. Queue in the anchor outbox. The worker batches, builds a Merkle root, sends the memo, confirms, and only then
   marks anchored. After 5 tries it marks failed and says so (no re-anchor command yet, D24).

## Gates
- `python -m pytest -q tests/test_api.py tests/test_chain_receipts.py tests/test_kya_receipts.py tests/test_outbox.py tests/test_merkle.py`
- `python3 scripts/drills.py` (not in check.sh: run it by hand for any change here).
- `scripts/check.sh`, then hostile review (gate 7).

## Policy
- AUTO: explain a refusal from its code, retire on a dry-run server, fix a bug with a failing test first.
- ASK: retire on the live server, change the receipt format, the memo, or the anchor rules.
- NEVER: say "recorded on Solana" before confirmation; sign with the hot key; edit or delete a receipt.

## Report
One run record. A refusal code you could not explain is a `context` finding.
