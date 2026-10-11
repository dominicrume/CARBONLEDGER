# security / 01-monitor: Check invariants and the anchored head

## Input
The registry, the receipt chain and the chain records

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A report: invariants hold, head hash matches

## Completion
The check ran on a schedule and a mismatch pages a person.

## Do not
Never ignore a head hash that disagrees.
