# verification / 03-attest: Attest and unlock issuance

## Input
An accepted evidence set

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
attest_project with an attested amount

## Completion
Issuance cannot exceed the attested amount and the attestation is logged.

## Do not
Never issue units for an unattested project.
