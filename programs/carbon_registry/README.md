# carbon_registry (Anchor program)

STATUS 2026-10-11 night: COMPILES (Anchor 0.31.1, Agave 4.3.0 tools) and PASSES all 10 registry vectors, replayed in-process with LiteSVM (programs/carbon_registry/tests/conformance.ts). Program id 3dGd2V1ykcmahyCQvhri4R2WhabT83hmm2WNz2r788Zj (its keypair lives in target/deploy, outside git). NOT yet deployed to devnet (the hot key has no SOL yet) and NOT independently reviewed.

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

## How to build and replay the vectors
```
npm ci
npm run vectors        # anchor build -- --arch v0, then ts-mocha replays conformance/registry_vectors.json in LiteSVM
```
Why SBPF v0 and LiteSVM: the x86 test validator crashes under Rosetta on Apple silicon (SIGILL in BLST), and the
Anchor LiteSVM bridge loads v0 programs. Devnet accepts v0 programs. Rebuild without `--arch v0` for a v3 deploy.

## To do, in order
1. Fund the hot key (docs/RUN-LOG.md), then `anchor deploy --provider.cluster devnet`.
2. A second ChainClient in packages/core/carbonledger/chain.py that calls `anchor_root` instead of the memo, with the same confirm-before-claiming rule.
3. Independent review before any mainnet use. Authority and verifier keys belong in a multisig, not a laptop.
