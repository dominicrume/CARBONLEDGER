# Quality gates: how we know the work is right

A change ships only through a gate that would have failed if the change were wrong. "Looks fine" is not a gate.

## The ladder
| Level | Gate | Command | Catches |
|---|---|---|---|
| 1 | Deterministic checks | `scripts/check.sh` | Broken invariants, parity with the app, banned words, secrets, supply chain, repo contracts, brain rot |
| 2 | Conformance vectors | inside pytest; `npm run vectors` for the program | A port that disagrees about a rule |
| 3 | Postgres rules | `DATABASE_URL_TEST=... python -m pytest tests/test_db_*.py` (`docker compose up -d db`) | Constraints and triggers that refuse what the model refuses |
| 4 | Break drills | `python3 scripts/drills.py` | Attacks: replay, chain down, tamper, cut tail, revoke then call, script in a name |
| 5 | Browser | `scripts/e2e.sh` | Real flows, API down, wording, accessibility (axe, WCAG 2.1 AA) |
| 6 | Brand | `python3 media/brand/check_post.py`; vorem-video voice QC, voice score, layout audit, loudness | Selling rules, false claims, bad takes, overlaps |
| 7 | Hostile review | A second agent given the diff, not your conclusion, asked to break it | What the tests did not think of |
| 8 | Human review | The DRI | Everything in the ASK tier; high stakes, novel or emotional calls |

Levels 1 to 6 are AUTO. Level 7 is AUTO for any change to a rule, vector, receipt, chain or claim. Level 8 is
required for the ASK tier.

## Which gate for which change
| Change | Minimum gates |
|---|---|
| Docs, brain, skill text | 1 |
| Core library, API | 1, 2, 4, 7 |
| Migration | 1, 3, 7, 8 |
| Program (Rust) | 2, 7, 8; never deploy without review and multisig |
| Screens, wording | 1, 5 |
| Post, caption, film | 6, 8 before publishing |

## Known holes (do not trust a green run here)
- verify-project has no code and no gate. Any "verification" is human work.
- `scripts/drills.py` is not in check.sh or CI. Run it by hand on any retirement or receipt change.
- Rules 11 to 15 and 18 in rules/ENGINEERING.md have no test (time injection, error code parity, id-only logs,
  one config source, decision entries, change bundles).
- The pilot label is tested on screens but no test asserts it on every API response.
- CI has never run on GitHub (D6). Until it does, a green CI badge is not evidence.
- The Anchor program job is allowed to fail in CI.
- check_post.py fails any text containing "credits" without the pilot label, even when the post is not about
  CarbonLedger. Override only with a written reason in the run record.
