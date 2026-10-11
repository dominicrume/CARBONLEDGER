# carbon_registry (Anchor program)

STATUS: source written and revised 2026-10-11, NOT compiled and NOT tested. No Rust toolchain existed where it was written.

Source of truth for behaviour: packages/core/carbonledger/registry.py (tested) and conformance/registry_vectors.json.

## Design for volume (D15)
No per-retirement account. The batch holds the hot counters. The API records receipts in its hash chain and anchors
one Merkle root per interval with `anchor_root` (PDA seeded by the first receipt index, contiguous with the last
anchor). On-chain per entity: registry, project, batch, linked external credit, anchor. See docs/MERKLE-ANCHORING.md.

## Mapping from reference model to program
| Reference model | Program |
|---|---|
| register_project | register_project (authority signs) |
| attest_project | attest_project (a named verifier signs; above `attest_two_above_g` a second verifier must agree) |
| issue_batch | issue_batch (authority signs, needs attestation) |
| link_external | link_external_credit (PDA init fails on a second link: DUPLICATE_LINK) |
| retire | retire (fresh serial range from the batch counter, returned to the operator) |
| suspend_project | suspend_project, and unsuspend_project |
| (none) | add_verifier, rotate_verifier (up to three), anchor_root |

Error names in `RegistryError` match the codes in the vectors. DUPLICATE_LINK and EXISTS surface as Anchor's
"account already in use" error; tests/conformance.ts maps that error to those codes.

## To do, in order
1. Install the toolchain (docs/ENVIRONMENT.md), `anchor build`, fix compile errors, `anchor keys list`, put the id in declare_id!, Anchor.toml and apps/web/js/config.js.
2. `anchor test` runs tests/conformance.ts against every registry vector on a local validator.
3. Deploy to devnet. Switch the API's chain client from the memo to `anchor_root` (chain.py, a second ChainClient).
4. Independent review before any mainnet use. Authority and verifier keys belong in a multisig, not a laptop.
