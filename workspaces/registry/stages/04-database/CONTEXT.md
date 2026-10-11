# registry / 04-database: Mirror the rules in Postgres

## Input
The passing model

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
db/migrations applied on a scratch database with a migration test

## Completion
The exclusion constraint refuses an overlapping range and the triggers refuse an edit.

## Do not
Never give the app role update or delete on history tables.
