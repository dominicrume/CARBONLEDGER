    # Workspace: web

    What the person sees. The app shows and asks. It decides nothing and holds no key.

    ## Stages
    1. stages/01-wording/CONTEXT.md: Check every sentence
2. stages/02-screens/CONTEXT.md: Build or change a screen
3. stages/03-accessibility/CONTEXT.md: Check access

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
