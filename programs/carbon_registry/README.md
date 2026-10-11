# carbon_registry (Anchor program)

STATUS: source written, NOT compiled and NOT tested. No Rust toolchain existed where it was written.

Source of truth for behaviour: packages/core/carbonledger/registry.py (tested) and conformance/registry_vectors.json.

## Mapping from reference model to program
| Reference model | Program |
|---|---|
| register_project | register_project (authority signs) |
| attest_project | attest_project (verifier signs) |
| issue_batch | issue_batch (authority signs, needs attestation) |
| link_external | link_external_credit (PDA init fails on a second link: DUPLICATE_LINK) |
| retire | retire (fresh serial range, one PDA per range) |
| suspend_project | suspend_project |

The error names in `RegistryError` match the codes in the vectors. DUPLICATE_LINK and EXISTS surface as Anchor's
"account already in use" error, so the test harness must map that error to those two codes.

## To do, in order
1. anchor build, fix compile errors.
2. Write programs/carbon_registry/tests/conformance.ts: load the JSON, run each step, compare the error name.
3. Replay all 10 registry vectors. Only then deploy to devnet.
4. Add a Token-2022 non-transferable receipt mint (plan, not written).
5. Independent review before any mainnet use. Authority and verifier keys belong in a multisig, not a laptop.
