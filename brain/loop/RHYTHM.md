# Operating rhythm

How the loop runs every week, so findings turn into fixes without Rume carrying it in his head. Set 2026-11-15.

| When | What runs | Who | Output |
|---|---|---|---|
| Every day, 06:10 UTC | `.github/workflows/sweep.yml`: brain gate, sweep, live `/health` and `/v1/audit/verify` | GitHub Actions | Job summary; a red job means look today |
| Every day, after the sweep | `sensor-sweep`, then `triage-signal` on anything new | an agent | One short ranked list |
| Every commit | `python3 brain/tools/brain_check.py` (CI runs it inside pytest) | the committer | Gate stays green |
| Monday | `self-improve` on the top 3 findings: one branch each, up to a pull request | an agent | 3 pull requests |
| Wednesday | `scripts/drills.py` and `watch-security` | an agent | Drill results, threat model updates |
| Friday, 30 minutes | Rume's ASK batch: merge pull requests, re-score ROOTS, ratify decisions, approve posts (`sell-with-proof`, `check_post.py`) | Rume | Merged work, signed decisions |
| Monthly | Rebuild `TRUTH.md` from the code, diff it, `record-decision` for each change | an agent, then Rume | A truthful register |

Rules: an agent never merges, deploys, posts or spends (POLICY.md). Anything that changes the chain, the unit,
what backs a unit, or adds a payment is a new brief with a decision entry first (CLAUDE.md scope lock).
