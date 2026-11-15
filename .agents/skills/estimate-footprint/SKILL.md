---
name: estimate-footprint
description: Change, check or explain how CarbonLedger turns a product, trip, meal, energy use or business activity into integer grams of CO2e. Use for factor tables, estimate tiers, parity between the browser and the server, unknown barcodes, and Open Food Facts lookups. Never use a model to supply a number.
---

# Estimate a footprint

The estimator is code with cited factor tables. A model may suggest a category, never a number. Estimates err high.

## Load
- `workspaces/estimator/CLAUDE.md` and the stage you are in (01-sources, 02-estimate, 03-review).
- `packages/core/carbonledger/estimate.py`, `packages/core/carbonledger/activities.py`.
- Vectors: `conformance/estimate_vectors.json` (140), `conformance/activity_vectors.json` (1,787).

## Facts to hold
- Grams are whole and rounded up. Tier 1 to 4; tier 4 is "estimate, rounded up" with a 1.25 uplift and 1,000 g
  for an unknown weight.
- The browser's JS is the source; `scripts/export_estimator.mjs` and `scripts/export_activities.mjs` regenerate the
  JSON tables and vectors, and `scripts/check.sh` fails if the export changes anything uncommitted.
- The server recomputes every retirement from typed items and refuses a lower total (BELOW_COMPUTED).
- An unknown barcode needs a person's chosen category, and the receipt should say a person chose.

## Tools and gates
- `python -m pytest -q tests/test_estimate_parity.py tests/test_activity_parity.py` with `PYTHONPATH=packages/core:services/api`.
- Full gate: `scripts/check.sh`.

## Policy
- AUTO: explain an estimate, add a test, fix a parity bug that matches the cited factor.
- ASK: change any factor, tier rule or table (a rule change: decision entry, regenerated vectors, changelog line,
  together; skill record-decision).
- NEVER: type a factor from memory or take one from a model or a web page without a cited source and tier.

## Report
One run record. If a factor's source was missing or unclear, set `layer` to `context` and say which factor.
