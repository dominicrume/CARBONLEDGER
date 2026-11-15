# Tools: what an agent can call and always get the same answer

Risk: none, data (writes the database), chain (signs or sends), money (spends), secret (needs a secret), out
(contacts the outside world). Tier comes from loop/POLICY.md. Run Python with
`PYTHONPATH=packages/core:services/api`.

## Core library (`packages/core/carbonledger/`, pure, time injected)
| Tool | Returns | Risk |
|---|---|---|
| `estimate.estimate_product(product)` | grams (rounded up), tier, source, detail, alternatives | none |
| `activities.flight_grams`, `ground_grams`, `energy_grams`, `meal_grams`, `commute_grams` and the business variants | integer grams | none |
| `registry.Registry` (`retire`, `check_invariants`, and the authority levers) | a Retirement with a serial range, or a RegistryError code | none (in memory) |
| `mandate.authorize`, `consume`, `revoke` | None, or MandateError: OVER_CAP, EXPIRED, REVOKED, WRONG_AGENT, PROJECT_NOT_ALLOWED | none |
| `agentsig.verify_agent` | None, or AgentSigError | none |
| `receipts.verify(entries)` | index of the first bad receipt, or None | none |
| `merkle.root`, `proof`, `verify_proof` | root, path, bool | none |
| `units.grams_to_clt`, `price_gbp` | string, Decimal | none |
| `chain.SolanaMemoChain` | a confirmed record | chain, secret: NEVER from an agent |

## API (`services/api/carbonledger_api/`)
| Call | Risk | Tier |
|---|---|---|
| `GET /health`, `/v1/registry/summary`, `/v1/receipts/{id}`, `/v1/receipts/{id}/proof`, `/v1/audit/receipts.json`, `/v1/audit/verify`, `/v1/stats/world`, `/v1/league` | none | AUTO |
| `GET /v1/metrics` | secret (METRICS_TOKEN) | ASK for the token; reading is AUTO once given |
| `POST /v1/retire` on a dry-run or test server | data | AUTO |
| `POST /v1/retire` on the live server | data, chain | ASK |
| `POST /v1/mandates`, `/revoke` | data | ASK on live |
| `POST /v1/auth/email` | out (real email) | ASK |
| `DELETE /v1/accounts/me` | data (deletion) | only for the person asking |
| `POST /v1/studio/direct` | money | ASK |

## Scripts (`scripts/`)
| Script | Does | Tier |
|---|---|---|
| `check.sh` (`SKIP_E2E=1` to skip the browser) | The one gate: pytest, ROOTS, secret scan, JS syntax, data re-export and diff, node tests, e2e | AUTO |
| `drills.py` | 10 break drills against its own dry-run API | AUTO |
| `recheck.py` | Invariants, receipt chain and anchors against DATABASE_URL or API_URL | AUTO (read-only) |
| `scan_secrets.py` | Secret scan | AUTO |
| `e2e.sh` | Browser smoke and accessibility tests on dry-run servers | AUTO |
| `export_estimator.mjs`, `export_activities.mjs` | Regenerate data and vectors from the app | AUTO on a branch; the diff is a rule change (ASK) |
| `migrate.py` | Apply migrations; `--reset` drops the schema | ASK; `--reset` only on a `_test` database |
| `make_api_key.py` | Prints a live key once | ASK |
| `dev.sh` | Sources `.env`; may sign devnet transactions | ASK |
| `build_seeker_mwa.sh` | Network install, overwrites a vendored file | ASK |
| `brain/tools/brain_check.py` (`--sweep`) | Checks the brain; sweep lists overdue items | AUTO |

## Brand and studio
| Tool | Does | Tier |
|---|---|---|
| `python3 media/brand/check_post.py caption.txt [image.html]` | Selling rules: hook, line length, grade, links, lists, hype, palette, pilot label | AUTO |
| The owner's vorem-video kit (voice QC, voice score, layout audit, render, mix) | Film production | AUTO to render a draft; ASK to publish |

## Not a tool yet (build these before automating the job)
- An operator endpoint to suspend a project, and a re-anchor command (ROOTS check 7, D24).
- Evidence intake and a verifier review screen (D11). Until then verify-project is human work.
- An alert sender for recheck and RPC failure rate.
