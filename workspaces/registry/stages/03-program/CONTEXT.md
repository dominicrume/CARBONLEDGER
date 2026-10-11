# registry / 03-program: Mirror the rules on Solana

## Input
The passing model and vectors

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
programs/carbon_registry passing the same vectors

## Completion
anchor build succeeds and all registry vectors pass against it.

## Do not
Never deploy to mainnet without an independent review and multisig keys.
