    # Workspace: agent

    Let an AI agent retire on a business's behalf, inside limits the owner set and can revoke.

    ## Stages
    1. stages/01-mandate/CONTEXT.md: Create a mandate
2. stages/02-act/CONTEXT.md: Act within the mandate
3. stages/03-revoke/CONTEXT.md: Revoke and audit

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
