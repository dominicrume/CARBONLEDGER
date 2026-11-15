---
name: watch-security
description: Monitor and defend CarbonLedger. Use to run the integrity recheck, the break drills and the secret scan, to respond to an incident (broken chain, failed anchors, leaked key, abuse), to review a change for attacks, or to update BREAK.md and the threat model.
---

# Watch security

## Load
- `workspaces/security/CLAUDE.md` and the stage in hand (01-monitor, 02-drill, 03-respond).
- `BREAK.md`, `docs/THREAT-MODEL.md` (partly stale: check DEBT.md first), `rules/HARDENING-ENGINEERING.md`.

## Monitor
- `python3 scripts/recheck.py` with API_URL or DATABASE_URL: exit 0 ok, 1 broken invariant or chain, 2 failed anchors.
- `GET /health` and `GET /v1/audit/verify` on the live API.
- `python3 scripts/scan_secrets.py`.

## Drill
- `python3 scripts/drills.py`: 10 attacks against its own dry-run API. Record results under the finding in BREAK.md.

## Respond
1. Say what is known and what is not. Never delete evidence or receipts.
2. Exit 1 (broken chain): stop writes is a human call (ASK). Name the first bad index.
3. Exit 2 (failed anchors): list them; there is no re-anchor command yet (D24), so an operator does it (ASK).
4. A suspected leaked key: tell the DRI at once; rotation is human work.
5. Afterwards: a new test or vector that would have caught it, a BREAK.md entry, a changelog line.

## Known gaps
No suspend endpoint (ROOTS 7); nightly recheck off; no alerting; authority and verifier keys not in a multisig.

## Policy
Monitoring and drills are AUTO. Every response action on the live system is ASK. NEVER open `.env` or key files,
even during an incident.

## Report
One run record per check or incident.
