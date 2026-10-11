# retirement / 03-receipt: Return and verify

## Input
A committed retirement

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A receipt with hash, serial range and signature, and a working verify endpoint

## Completion
audit/verify names the first bad index after any edit.

## Do not
Never put personal data in a memo or an on-chain field.
