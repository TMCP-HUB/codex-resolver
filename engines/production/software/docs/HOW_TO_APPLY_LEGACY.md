# How to Apply This Playbook

## Recommended model

Do not use this repository as a second live repository attached to the same coding task.
Instead, copy the parts you need into the actual product repository before active work starts.

## Best workflow for a new project

1. Create the real product repository.
2. Copy in a tailored `AGENTS.md`.
3. Copy only the skills you want.
4. Copy only the templates you will actually maintain.
5. If needed, adapt local Codex hooks.
6. Start work in the product repository itself.

## Why this is better

The product repository remains the source of truth.
The agent reads the instructions from inside the repository it is actually changing.
This avoids confusion about cross-repository context and avoids hidden dependencies.

## Do not do this

- do not rely on a separate instruction repo staying open in the same coding context
- do not dump the entire playbook into a base prompt
- do not keep dead instruction files forever if they are no longer useful

## What to keep in the product repository

Keep only:

- repository-specific `AGENTS.md`
- a small set of current templates or state files
- only the skills that are useful for that repository

## What to remove later

When the project is mature, you may remove:

- temporary handoff files for finished tasks
- temporary task evidence files no longer needed
- unused templates copied only for setup

Usually keep:

- `AGENTS.md`
- project chronicle if it provides lasting value
- any useful verification or workflow scripts
