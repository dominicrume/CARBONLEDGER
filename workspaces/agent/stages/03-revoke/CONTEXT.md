# agent / 03-revoke: Revoke and audit

## Input
The owner's revoke request

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A revoked mandate and an audit trail

## Completion
A revoked mandate is refused on the next call.

## Do not
Never let anyone but the owner revoke.
