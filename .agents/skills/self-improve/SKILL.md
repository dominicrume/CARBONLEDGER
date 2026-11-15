---
name: self-improve
description: Turn a failed or awkward agent run, a red gate, a drift item or a triaged finding into a lasting fix to a context file, a skill, a tool, a gate or the policy, behind the gates and up to a pull request. Use when a run record is open, when the same task failed twice, or when asked to make the system better on its own.
---

# Self-improve

The aim: the next time someone asks the same thing, it works. A note saying "be careful" is not a fix.

## Inputs
Open run records (`python3 brain/tools/brain_check.py --sweep` lists them), or one finding from triage-signal.

## Steps
1. Reproduce. Re-run the failed task or the failing gate. If it now passes, record why and close it.
2. Diagnose with the five questions in `brain/loop/LEARNING.md`: context, skill, tool, gate, policy. Pick the
   smallest layer that fixes it. Prefer a deterministic tool or a test over more prose.
3. Branch: `git switch -c improve/<short-name>`.
4. Gate first. Write the test, vector or checker rule that fails because of the problem. Watch it fail.
5. Fix. Change the context, skill, tool or code until it passes.
6. Run the gates for that change (`brain/loop/GATES.md`). For any rule, receipt, chain or claim change, ask a second
   agent to break it, giving it the diff only.
7. Update `brain/TRUTH.md` or the drift table if a fact changed.
8. Open a pull request (or, if you cannot push, leave the branch) with: the run records it answers, the failing then
   passing gate, and the tier. Fill `closed_by` in those records with the branch or PR.
9. Stop. Merging is ASK (`brain/loop/POLICY.md`).

## Limits
- One problem per branch. Never weaken a test to make it pass. Never touch rules, vectors, factors, the chain or
  prices without a decision entry first.
- If the fix needs a secret, money, a person or the live system, stop at a written proposal (outcome `asked`).
