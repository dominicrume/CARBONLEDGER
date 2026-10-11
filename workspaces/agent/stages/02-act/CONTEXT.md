# agent / 02-act: Act within the mandate

## Input
An agent's retire request with a mandate id

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A receipt, or a refusal with a code (OVER_CAP, EXPIRED, REVOKED, WRONG_AGENT, PROJECT_NOT_ALLOWED)

## Completion
Every refusal leaves state unchanged and every success consumes the cap.

## Do not
Never let an agent act without a named mandate.
