# Sensors: how the company hears the world

A sensor is anything that reports what happened without being asked each time. Rule for every sensor here:
counts, codes, ids and hashes only. No personal data, no message bodies in the repo (rules/ENGINEERING.md rule 13,
COMPLIANCE C8). "Record everything" stops at consent and the law.

## Live sensors
| Sensor | What it tells you | How to read it | Feeds |
|---|---|---|---|
| Usage events | Daily counts of site_view, app_open, scan_start, retire_open, verify, install, signin_start, statement | `GET /v1/metrics?days=7` with the METRICS_TOKEN (operator only), or `apps/web/metrics.html` | Funnel, return rate |
| Refused receipts | Every action the rules stopped, with its rule code (BELOW_COMPUTED, OVER_CAP, EXPIRED, REVOKED, OVER_RETIREMENT and more) | `GET /v1/audit/receipts.json`, filter `outcome == REFUSED`; count by rule | Where users or agents hit walls |
| Chain integrity | Chain intact, first bad index, anchor counts | `GET /v1/audit/verify`; `python3 scripts/recheck.py` (exit 0 ok, 1 broken, 2 failed anchors) | Incidents |
| Health | Cluster, store kind, pending, anchored and failed anchors | `GET /health` | Incidents |
| Test and CI results | What broke in code | `scripts/check.sh`; GitHub Actions once CI runs (D6) | self-improve |
| Code quality audit | Security density, complexity, duplication, scope drift against spec.yaml | CI job `audit` (ai-code-quality-auditor) | self-improve |
| Break drills | Whether the 10 attacks still fail | `python3 scripts/drills.py` | BREAK.md |
| Brain sweep | Overdue debt, expired waivers, router lines that contradict DEBT.md | `python3 brain/tools/brain_check.py --sweep` | triage-signal |
| Agent run records | Where agents failed, and why | `brain/feedback/runs.jsonl` | self-improve |
| Git history | What changed, when, by whom | `git log` | Context for every sensor |

## Missing sensors (ranked by value)
1. Alerting. recheck.yml is off (RECHECK_ENABLED) and nothing pages a person. A broken chain would sit unseen.
2. A user feedback channel. Name filtering says "reports go to a person" (`growth.py`) but no report endpoint exists.
3. RPC failure rate. `RpcStats.failure_rate` is computed in `packages/core/carbonledger/chain.py` and exposed nowhere.
4. The `estimate` event is allowed by the API and never sent by the app, so the funnel has a hole before retire.
5. Structured logs. There is no logging framework, only prints.
6. Brand and sales signals: post reach, replies, inbound messages. They live on LinkedIn, X and WhatsApp; the owner's
   inbound-triage skill reads them by hand. Store only the decision and a count here, never the message.

## Adding a sensor
Add the row above, say what it feeds, prove it carries no personal data (a test like tests/test_growth.py
"events are counts only"), and add its read command to the sensor-sweep skill.
