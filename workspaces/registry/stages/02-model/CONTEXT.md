# registry / 02-model: Change the reference model

## Input
A failing vector

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
registry.py passing every vector and the random attack

## Completion
pytest is green and check_invariants holds across 20,000 steps.

## Do not
Never weaken an invariant to make a test pass.
