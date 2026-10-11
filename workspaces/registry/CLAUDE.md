    # Workspace: registry

    The rules of the register: who may issue, retire and link, and what can never happen twice.

    ## Stages
    1. stages/01-rules/CONTEXT.md: Write or change a rule
2. stages/02-model/CONTEXT.md: Change the reference model
3. stages/03-program/CONTEXT.md: Mirror the rules on Solana
4. stages/04-database/CONTEXT.md: Mirror the rules in Postgres

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
