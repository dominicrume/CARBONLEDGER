# retirement / 01-request: Validate the request

## Input
JSON from a caller

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
A strictly checked request, or a 422

## Completion
Unknown fields, bad types, out-of-range numbers and bad keys are all refused.

## Do not
Never coerce a type. Never accept a number without bounds.
