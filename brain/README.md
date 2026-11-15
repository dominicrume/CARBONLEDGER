# The Company Brain

This folder is what CarbonLedger and VOREM know about themselves, written so that any agent (Claude, Codex,
Gemini, Cursor, a cron job) can load it, act on it, and report back into it. Built 2026-11-09 from the code, the
tests, the debt list, the decisions and the brand files, with every claim pointing at its source.

The software is disposable. This folder, the conformance vectors and the tests are not.

## The loop
The shape comes from Tom Blomfield's YC talk "How to Build a Self-Improving Company with AI" (2026): a company
run as loops, each with five layers. Here is each layer, mapped to what exists in this repo today.

```
 SENSORS ---> POLICY ---> TOOLS ---> QUALITY GATE ---> act (or refuse)
    ^                                                        |
    +----------------------- LEARNING <----------------------+
```

| Layer | Question it answers | File | State today |
|---|---|---|---|
| Sensors | What happened out there? | loop/SENSORS.md | Counts, refusals, anchors, recheck, CI. No alerting, no user feedback channel |
| Policy | What may an agent do alone, with permission, never? | loop/POLICY.md | Written here; the never-list is enforced by code and tests |
| Tools | What can an agent call that always gives the same answer? | loop/TOOLS.md | Strong: pure core library, API, scripts |
| Quality gate | How do we know the work is right? | loop/GATES.md | Strong for the ledger (2,000+ checks); missing for verification and brand |
| Learning | How does a failure become a better tool, skill or rule? | loop/LEARNING.md | Manual (BREAK.md, DEBT.md); now has a feedback log and a sweep |
| Rhythm | When does each part of the loop run? | loop/RHYTHM.md | Daily sweep workflow (2026-11-15); weekly fix, drill and approval days |

## Load order for any agent
1. `CLAUDE.md` (the router and the rules that never bend). Other agents: `AGENTS.md` sends you there.
2. `brain/TRUTH.md`: what is true today, what is not, and what must never be said. Read it before any claim.
3. `brain/COMPANY.md` and `brain/GLOSSARY.md` when the task touches the product or the business.
4. `brain/loop/POLICY.md` before acting. Then the one skill in `.agents/skills/` that fits the task.
5. After the task, append one record to `brain/feedback/runs.jsonl` (schema in `brain/feedback/SCHEMA.md`).

Do not load the whole folder for a small task. Each skill names what it needs.

## Skills
Skills live in `.agents/skills/<name>/SKILL.md` (the Agent Skills format, read by Claude Code, Codex, Gemini CLI
and others). `.claude/skills` points at the same folder, so there is one copy.

| Skill | Use it to |
|---|---|
| carbonledger-orient | Start any task: load the right context, pick the job, know the policy tier |
| estimate-footprint | Change or check the estimator, factors and activity tables |
| retire-units | Change or debug the retirement path, receipts and anchoring |
| change-registry | Change a registry rule across vectors, model, program and database |
| verify-project | Anything about evidence, verifiers or attestation (mostly human work) |
| run-agent | Mandates, agent keys, signed agent retirements |
| change-web | Screens, wording, accessibility of the app and site |
| watch-security | Recheck, drills, incidents, secrets |
| sensor-sweep | Read every sensor and write findings |
| triage-signal | Decide what to do with a finding or a request: discard, backlog, do now, ask |
| self-improve | Turn a failure into a change to a tool, skill, context or gate, behind the gates |
| record-decision | Write a decision entry, a debt row or a truth change the right way |
| sell-with-proof | Write any post, caption, script line or page that sells, and pass the checker |

## The checker
`python3 brain/tools/brain_check.py` checks the brain itself: every skill is well formed, every path it names
exists, every feedback record fits the schema. `tests/test_brain.py` runs it, so `scripts/check.sh` and CI fail
when the brain rots. `python3 brain/tools/brain_check.py --sweep` is a sensor: it lists overdue debt, expired
waivers and router lines that contradict DEBT.md.

## What is not in this folder, on purpose
This repo is public. People's names, voices, photos, client work, contact details, unverified personal claims and
commercial terms stay out. Agents that need them read the owner's private skills and memory on his own machine.
