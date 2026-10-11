# retirement / 02-record: Record on a copy, then commit

## Input
A valid request

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
The registry change, the receipt and the chain record, together or not at all

## Completion
A chain failure leaves the registry and the receipt chain unchanged.

## Do not
Never commit before the chain client succeeds.
