    # Workspace: estimator

    Turn what a person buys or does into grams of CO2e, with a cited source. Code only. A model may suggest a category.

    ## Stages
    1. stages/01-sources/CONTEXT.md: Load and cite the factor tables
2. stages/02-estimate/CONTEXT.md: Compute the estimate
3. stages/03-review/CONTEXT.md: Let a person overrule a category

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
