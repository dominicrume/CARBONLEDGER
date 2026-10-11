# verification / 01-evidence: Collect evidence

## Input
Photos, satellite data, audits from the project

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
Evidence records with a content hash, coarse location and a verifier decision field

## Completion
Each record follows docs/MRV-LAYERS.md and raw files stay off-chain.

## Do not
Never store precise coordinates in a public place. Never reuse evidence across plots.
