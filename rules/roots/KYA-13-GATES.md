# The 13 Gates, Applied to CarbonLedger (with attack drills)

The ROOTS audit has 13 checks. HV marks the high-vigilance ones: an unrooted HV check blocks shipping unless a
dated waiver names an owner. For each gate: what it means here, how to BREAK it, and what a pass looks like.
Run the drill. If it breaks, record it in BREAK.md and fix or waive it with a date.

| # | Gate | What it means here |
|---|------|--------------------|
| 1 | Written rules | rules/*.md exist, are numbered, and the router points to them |
| 2 | Spec before code | Every workspace stage has a CONTEXT.md contract before code exists |
| 3 | Small pieces | Modules stay small, one job each |
| 4 | Plan, not reflex [HV] | A written plan precedes each phase: docs/HACKATHON-48H.md, SCALING.md |
| 5 | Exit criteria | Every stage states how we know it is done |
| 6 | Context discipline | Each workspace lists what to load and what NOT to load |
| 7 | Contain failure [HV] | A failure in one part cannot corrupt another: rollback, least privilege, kill switch |
| 8 | Show your working [HV] | Every decision leaves a hash-chained receipt that anyone can check |
| 9 | Fences that hold | Limits are enforced in code, not in prose: caps, ranges, attestation |
| 10 | Check your own work | Tests, vectors, random attacks, and a hostile review of our own output |
| 11 | Sources for facts [HV] | Every number cites a source tier, and no unit exists without an attestation |
| 12 | Ship through a gate [HV] | CI must pass before anything ships: tests, scanner, ROOTS gate |
| 13 | Learn from last run [HV] | Each break, outage or near miss changes a rule, a test or a vector |

## Attack drills

### 1 Written rules
Break it: ask a coding agent to "just retire some units for the demo" without a verifier. Does CLAUDE.md stop it?
Pass: the rule is written, and a test fails when the registry allows issuance without attestation.

### 2 Spec before code
Break it: delete one stage CONTEXT.md and run the tests. Pass: tests/test_repo_contracts.py fails and names the stage.

### 3 Small pieces
Break it: paste a 600-line module into the core. Pass: the size test fails.

### 4 Plan, not reflex [HV]
Break it: start building payments before the plan names them. Pass: the router calls it a new brief and demands a
decision entry. Current state: planned, waived until the hackathon is submitted (ROOTS-SCORE.md).

### 5 Exit criteria
Break it: open any stage CONTEXT.md with no Completion section. Pass: the contract test fails.

### 6 Context discipline
Break it: look for a workspace file that loads secrets or another workspace's internals. Pass: every L1 file has a
What NOT to load table, and the contract test checks it exists.

### 7 Contain failure [HV]
Break it: make the chain client throw in the middle of a retirement. Pass: nothing is recorded (tested).
Also try: a second process writing history. Pass (once Postgres runs): append-only triggers refuse it.
Current state: code-level rollback proven. Process sandboxing and database triggers not yet, so this stays waived.

### 8 Show your working [HV]
Break it: change one receipt, delete one, swap two, cut the tail. Pass: verify names the first bad index, and the
cut tail disagrees with the anchored head (all tested).

### 9 Fences that hold
Break it: 20,000 random hostile calls to the registry, plus hostile JSON to the API. Pass: invariants hold, 422 on
bad input (tested). Also: a stranger calls attest or issue. Pass: UNAUTHORISED.

### 10 Check your own work
Break it: change one factor in the table. Pass: a golden vector fails, because 133 vectors come from the app's own code.
Also: have another person try to break BREAK.md's findings.

### 11 Sources for facts [HV]
Break it: ask the estimator for something not in the tables. Pass: it falls to tier 4 with a margin and says so.
Break it harder: try to issue units with no evidence. Pass today: attestation is required, but the attestation is
simulated and no real evidence is ingested. So this gate is NOT rooted: it is waived until MRV exists.

### 12 Ship through a gate [HV]
Break it: push a change that breaks a vector. Pass: CI fails. Current state: CI is written and has not run.

### 13 Learn from last run [HV]
Break it: find a failure that left no trace in rules, tests or DEBT. Pass: none. Current state: the log is new, so the
loop has not turned once. Waived until the first real incident or drill result is recorded.
