# estimator / 01-sources: Load and cite the factor tables

## Input
packages/core/carbonledger/data_factors.json (generated from the app by scripts/export_estimator.mjs)

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
Each factor with its source name and tier

## Completion
A change to a factor or a rule is a decision entry, a regenerated vector set and a changelog line, together.

## Do not
Never type a number from memory into a table. Never let a model supply a factor.
