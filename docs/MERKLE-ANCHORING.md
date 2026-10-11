# Merkle Anchoring

Written 2026-10-11. Replaces memo-per-receipt (SCALING.md item 2, D15, T22).

## What goes on-chain
One memo per interval: `carbonledger:v2:A-<first>-<last>:<root>`. `first` and `last` are receipt chain indices,
`root` is the Merkle root over the receipt entry hashes in that range. Nothing else. No names, no baskets, no ids
that count volume (receipt ids come from content).

Later, the Anchor program's `anchor_root` instruction records the same triple in a PDA seeded by `first`, so an
interval can be anchored once and intervals must be contiguous (programs/carbon_registry/src/lib.rs).

## How a receipt is proven
Each receipt keeps its proof path: the sibling hashes from its leaf to the root, with a side marker. Anyone with
the receipt hash, the path and the root can recompute the root. The verify screen does this in the browser
(apps/web/js/core/merkle.js) with no trust in the API, and GET /v1/receipts/{id}/proof returns the path.

Tree rules (packages/core/carbonledger/merkle.py): leaf = sha256(0x00 || hash), node = sha256(0x01 || left ||
right), an odd node pairs with itself. The 0x00 and 0x01 prefixes stop a leaf posing as a node. Vectors in
conformance/merkle_vectors.json are shared by the Python and browser verifiers.

## How the worker batches
A receipt commits with anchor_status pending. The worker waits ANCHOR_INTERVAL_SECONDS (default 2) after the first
pending receipt so more can join, takes up to 1,024 pending receipts in chain order, builds the root, submits one
transaction, confirms it, then marks each receipt anchored with the signature, slot, anchor id, root and proof.
A dropped transaction is retried up to five times, then each receipt in that batch is marked failed and shown as
failed. The API's answer to a retirement waits up to ANCHOR_WAIT_SECONDS (default 20) for this, so a demo still
shows a signature on the receipt.

## Costs
Before: one transaction and (in the program design) one rent-exempt account per retirement.
After: one transaction per interval regardless of count, and no per-retirement account. At 1,000 retirements a
minute and a 30 second interval that is two transactions a minute.

## What this changes in the rules
Rule 6 as refined: the receipt commits first; nothing is called recorded on-chain until confirmed; a failed anchor
is shown as failed. Rule 1 of the registry (serial ranges, attested before issued) is unchanged: anchoring is about
the witness, not the rules.
