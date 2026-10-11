# The Thirteen Checks (ship gate)

Score every check PASS-level (ROOTED), SEEDLING, or ABSENT in ROOTS-SCORE.md.
ROOTED needs a pointer: the file or mechanism that proves it. Saying "we
handle that" earns nothing.

Six checks are high-vigilance (HV). If an HV check is not ROOTED, it needs a
dated waiver with an owner, or the gate refuses to pass:
4 planning, 7 sandboxing, 8 trajectory, 11 grounding, 12 CI/CD, 13 feedback.

1 Written rules            2 Spec before code        3 Small pieces
4 Plan, not reflex [HV]    5 Exit criteria           6 Context discipline
7 Contain failure [HV]     8 Show your working [HV]  9 Fences that hold
10 Check your own work     11 Sources for facts [HV] 12 Ship through a gate [HV]
13 Learn from last run [HV]

Run: python rules/roots/check_roots.py .
For an exchange, a waiver is never permanent. Each one carries a repay date.
