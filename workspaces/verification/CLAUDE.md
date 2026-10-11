    # Workspace: verification

    Decide whether real projects deserve real units. Humans decide. Software never attests.

    ## Stages
    1. stages/01-evidence/CONTEXT.md: Collect evidence
2. stages/02-review/CONTEXT.md: Verifier review
3. stages/03-attest/CONTEXT.md: Attest and unlock issuance

    ## What to load
    | Resource | Why |
    |---|---|
    | ../../CLAUDE.md and ../../rules/ENGINEERING.md | The rules that never bend |
    | This workspace's stage CONTEXT.md for the stage in hand | Only the contract you are working on |
    | ../../conformance/ files for this job | The vectors that define right |

    ## What NOT to load
    | Resource | Why |
    |---|---|
    | .env or any key | Secrets never go to a model |
    | Other workspaces' stage folders | Each job sees its own contract only |
    | apps/web/js/data/geo.js | Large map data with nothing to learn from |
