---
name: record-decision
description: Write a decision entry, a debt row, a changelog line or a truth register change for CarbonLedger the house way, so the company's memory stays legible to agents. Use whenever a choice is made or proposed, a rule, vector or factor changes, a debt is paid or found, or a claim becomes true or false.
---

# Record a decision

If it is not written down, it did not happen to the company's intelligence.

## Where things go
| What | File | Shape |
|---|---|---|
| A choice, with options and why | `docs/DECISIONS.md` | Dated heading; context; decision; why; status ("Awaiting Rume" until he confirms) |
| Something not true yet | `DEBT.md` | `| Dn | debt | why it matters | owner | review date |`; when paid, the row starts `PAID <date>` and names its proof test |
| Something that broke, and its fix | `BREAK.md` | Fn with the test that proves the fix |
| What shipped | `CHANGELOG.md` | One line per change |
| A claim that changed | `brain/TRUTH.md` | Move the row between "True today" and "Not true yet"; fix the drift table |
| A ship gate score | `ROOTS-SCORE.md` | Only the DRI re-scores (ASK) |

## Rules
- A change to a rule, a vector or a factor table comes with a decision entry, a test and a changelog line in the
  same commit (rules/ENGINEERING.md rule 18).
- Dates are absolute (2026-11-09), never "today" or "next week".
- No em or en dashes in documents (tests/test_repo_contracts.py).
- Write the decision as a proposal when the DRI has not confirmed it. Never mark it ratified for him.
- When a DEBT row is paid, check `CLAUDE.md` "Not yet true": `python3 brain/tools/brain_check.py --sweep` flags a
  paid D-number still listed there.

## Report
One run record naming the files changed.
