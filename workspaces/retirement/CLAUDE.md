    # Workspace: retirement

    Take a request to retire pilot units and turn it into a recorded, verifiable receipt, or into nothing.

    ## Stages
    1. stages/01-request/CONTEXT.md: Validate the request
2. stages/02-record/CONTEXT.md: Record on a copy, then commit
3. stages/03-receipt/CONTEXT.md: Return and verify

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
