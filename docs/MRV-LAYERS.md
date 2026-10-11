# Verification: The Part That Makes a Unit Real

A ledger records what it is told. If the input is wrong, the record is wrong forever. Your own work on woody biomass
named this the "immutable greenwashing" trap. The fix is three layers.

## Layers
- Layer A, ground truth. Farmer phone app with GPS photos, plus free NASA and ESA satellite imagery, so claims about
  land and crops can be checked against the sky. The partner's technology contact has verbally agreed to contribute
  this. Nothing is written, shared or tested. NOT BUILT.
- Layer B, the ledger. This repository. Cheap, replaceable, honest about what it knows.
- Layer C, attestation. A named verifier signs that evidence supports a stated amount. No attestation, no issuance.
  Built as a rule in the registry. The attestation in the demo is simulated.

## Evidence record (the shape to build first)
```
evidence_id        text   unique
project_id         text
kind               gps_photo | satellite | field_audit | document
captured_at        timestamp
coarse_location    geohash, 5 characters at most (about a 5 km cell, ASSUMPTION: confirm with the verifier)
content_hash       sha256 of the raw file (the file itself stays off-chain and deletable)
submitted_by       account id
verifier_decision  pending | accepted | rejected, with a reason
verifier           named person or institution
```
Only `content_hash` and the decision ever leave the private store. Personal data never goes on a public chain.

## What to expect to go wrong
| Failure | Defence |
|---|---|
| Photos taken far from the claimed plot, or reused | Compare against satellite imagery, reject repeated hashes |
| A plot claimed twice, in two projects or two registries | Plot identifier unique across the register, plus the external link rule |
| A verifier key stolen or a verifier bribed | Two verifiers above a set size, key in a multisig, published decisions |
| Land use changes after issuance | Re-check on a schedule, and a suspend lever that freezes retirement |
| Satellite data misread | A human reviews every acceptance. Software never accepts. |

## Open questions that need answers before any real claim
Which standard or methodology applies, who accredits the verifier, how permanence and additionality are shown, and
what the farmers are told and paid. Without answers, every unit stays labelled "simulated pilot unit".
