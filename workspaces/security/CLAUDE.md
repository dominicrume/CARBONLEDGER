    # Workspace: security

    Watch the system, break it on purpose, and respond when it breaks.

    ## Stages
    1. stages/01-monitor/CONTEXT.md: Check invariants and the anchored head
2. stages/02-drill/CONTEXT.md: Run the break drills
3. stages/03-respond/CONTEXT.md: Respond to an incident

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
