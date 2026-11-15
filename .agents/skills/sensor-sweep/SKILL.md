---
name: sensor-sweep
description: Read every CarbonLedger and VOREM sensor (health, chain audit, refusals by rule code, usage funnel, tests, drills, overdue debt, expired waivers, open agent run records) and write a short, ranked findings list. Use daily, after a deploy, or when asked what is happening, what broke or what to do next.
---

# Sensor sweep

Read, do not act. The output feeds triage-signal.

## Steps (all AUTO; skip a sensor you cannot reach and say so)
1. `python3 brain/tools/brain_check.py --sweep`: overdue debt, expired ROOTS waivers, router lines that contradict
   DEBT.md, open run records.
2. `python3 brain/tools/brain_check.py` and `SKIP_E2E=1 scripts/check.sh`: is the repo green?
3. `python3 scripts/drills.py`: do the attacks still fail?
4. Live, if reachable: `GET /health`, `GET /v1/audit/verify` (intact? failed anchors?).
5. Live refusals: `GET /v1/audit/receipts.json`, count REFUSED by rule code. A rising code is a product signal
   (users hitting a wall) or an attack.
6. Funnel, only if the operator gave the token: `GET /v1/metrics?days=7` (site_view to app_open to retire_open to
   retirements, return rate).
7. `git log --since` the last sweep: what changed that a document should now say?

## Output
A list, most urgent first. Each finding: what, evidence (command and number), the layer it points at (sensor,
policy, tool, gate, context, skill), and a suggested next step. Then one run record with `skill` sensor-sweep.

## Urgency
1. Chain not intact, or failed anchors. 2. Gate red. 3. A claim in a public document that is now false. 4. Expired
HV waivers. 5. Overdue debt. 6. Product signals.

Never paste personal data into findings: counts and codes only.
