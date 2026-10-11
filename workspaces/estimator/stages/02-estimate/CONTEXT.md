# estimator / 02-estimate: Compute the estimate

## Input
A product: name, grams, hint, categories, an outside Agribalyse value (untrusted)

## Process
Follow rules/ENGINEERING.md. Work in small steps. Write the failing test or vector first, then the change.
Record any real decision in docs/DECISIONS.md.

## Output
grams (whole, rounded up), tier, source, detail, alternatives

## Completion
The result matches all 140 golden vectors, including the hostile ones.

## Do not
Never accept a negative, zero, non-numeric or absurd outside number. Ignore it and fall back.
