---
name: change-web
description: Change the CarbonLedger web app, landing page or Studio page: wording, screens, flows, game elements, failure states and accessibility. Use for any user-facing sentence or screen, so it stays honest (pilot units, not yet verified credits), accessible (WCAG 2.1 AA) and wired to the server as the source of truth.
---

# Change the web app

The browser shows and asks. It holds no signing key and decides nothing. A browser total is never a score.

## Load
- `workspaces/web/CLAUDE.md` and the stage in hand (01-wording, 02-screens, 03-accessibility).
- `rules/HARDENING-PRODUCT.md`, `docs/ux/DESIGN-SYSTEM.md`, `docs/ux/FLOWS.md`, `apps/web/js/config.js`.
- Never `apps/web/js/data/geo.js`.

## Rules
- Say "Retire pilot units". A unit count always carries the pilot label. Never offset, carbon neutral, net zero,
  climate positive, verified credits.
- Every failure says what happened and that nothing was recorded.
- No pressure copy, no punishing streaks, no real money in the game. Leagues rank XP, never footprint size.
- Scripts from self only (CSP); vendored files pinned with SRI hashes.
- Product UI keeps its green palette (docs/ux/DESIGN-SYSTEM.md). The light blue brand palette is for Rume and VOREM
  media, not the app.

## Gates
- `python -m pytest -q tests/test_web_wording.py tests/test_web_supply_chain.py tests/test_web_installable.py`
- `cd apps/web && npm test`; `scripts/e2e.sh` (smoke and axe accessibility).

## Policy
AUTO on a branch. ASK to deploy. NEVER weaken a wording test to make a sentence pass.

## Report
One run record.
