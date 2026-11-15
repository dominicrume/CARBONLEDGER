# Learning: how a failure becomes a better company

KYA gate 13 says each break, outage or near miss changes a rule, a test or a vector. This file makes that a loop
an agent can run, not a hope.

## The loop
1. Capture. Every agent run ends with one record in `brain/feedback/runs.jsonl` (brain/feedback/SCHEMA.md).
   Failures, refusals, missing tools and wrong context matter most. A human can add a record too.
2. Sweep. The sensor-sweep skill reads the sensors (loop/SENSORS.md), the run records since the last sweep, and
   `python3 brain/tools/brain_check.py --sweep`. It writes findings.
3. Triage. The triage-signal skill sorts each finding: discard (with reason), backlog (DEBT.md row), do now, or
   ask the DRI. It judges against the roadmap in CLAUDE.md scope lock.
4. Diagnose. For a do-now finding, the self-improve skill asks the five questions:
   - Was the context wrong or missing? Change brain/ or a workspace CONTEXT.md.
   - Was a skill unclear? Change the SKILL.md.
   - Was a tool missing or wrong? Add or fix the tool, with a test.
   - Did a gate miss it? Add the test or vector that would have caught it, first.
   - Was the policy wrong? Propose a policy change (ASK).
5. Change, behind the gates. A branch, a failing test first, the fix, the gates green, a pull request whose body
   names the run records it answers.
6. Close. The DRI merges (loop/POLICY.md). The record's `closed_by` is filled in. Next time the same task succeeds.

## What counts as learning
A change to context, a skill, a tool, a gate or a policy. A note that says "be careful" is not learning.

## Cadence
- Every run: capture.
- Daily (or after any deploy): sweep and triage.
- Weekly: self-improve on the top three findings; re-score ROOTS if anything moved.
- Monthly: regenerate brain/TRUTH.md and the drift table from the code, and compare (the user manual idea from the
  talk: the brain is rebuilt from the evidence, then diffed, so it cannot quietly rot).

## Seed findings from the 2026-11-09 extraction
These are the first items for the loop, ranked. Each is also in brain/feedback/runs.jsonl.
1. Turn on the nightly recheck and an alert (missing sensor, D6, ROOTS 12).
2. Run CI on GitHub once (D6). Until then gates 1 to 5 are local only.
3. Fix the drift table in brain/TRUTH.md, starting with README.md and docs/PITCH-FACTS.md (pitch risk).
4. Add `scripts/drills.py` to check.sh or CI.
5. Add a test that every API response carries the pilot label.
6. Build the suspend and re-anchor operator levers (ROOTS 7, D24).
7. Re-score ROOTS; three HV waivers are expired.
8. Make check_post.py's credits rule apply only to CarbonLedger content.
9. Add a user report endpoint (counts and codes only) so the product has a voice of the customer sensor.
