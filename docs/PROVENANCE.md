# Provenance of the Baseline App

apps/web/ was imported from the public CarbonLedger artifact (https://claude.ai/artifact/GPXQScDQFMNPCHn1w3kd98),
32 files. The artifact belongs to someone in another organisation. Our understanding, not confirmed: it was built by the
partner. Ownership must be written into Schedule 2 of the Founders Heads of Terms before the repo is published.

## What we changed
| File | Change |
|---|---|
| apps/web/js/config.js | Added the API address and a ceiling for outside Agribalyse values |
| apps/web/js/core/ledger.js | Replaced the stub that threw "not connected yet" with a call to the API |
| apps/web/js/core/estimate.js | Outside numbers are validated before use (found by attack, see BREAK.md F1) |
| apps/web/package.json | Added, so Node can check the modules |

Everything else is as received. Not yet changed, and should be: the "Offset" wording, the missing simulated banner, the
missing script integrity hashes, and credits for data sources (COMPLIANCE C13).

## Data and libraries inside it
Poore and Nemecek (2018) via Our World in Data, Agribalyse, Open Food Facts (live lookup), Our World in Data CO2 series
for country targets, ZXing, D3, TopoJSON, Google Fonts. Licences are not yet checked (COMPLIANCE C13).
