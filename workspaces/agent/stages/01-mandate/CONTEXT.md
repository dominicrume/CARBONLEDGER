# agent / 01-mandate: Create a mandate

## Input
An owner, an agent name, a cap, an expiry, an optional project list

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A mandate with an id

## Completion
The mandate shows the cap, the expiry and who may revoke.

## Do not
Never create an open-ended mandate. Cap and expiry are required.
