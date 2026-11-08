# Three.js Site Starter Bundle

Use this bundle for a new visual-heavy site such as an interactive product landing page.

## Copy these files first

### Always copy

- `AGENTS.md`
- `engines/production/software/skills/git-branch-integrity/SKILL.md`
- `engines/verification/skills/proof-loop-verification/SKILL.md`
- `protocols/skills/session-handoff/SKILL.md`
- `engines/production/software/templates/BRANCH_STATE.md`
- `protocols/templates/HANDOFF.md`
- `protocols/templates/TASK_EVIDENCE.md`
- `engines/production/software/docs/PRODUCT_REPO_RULES.md`

### Copy for longer or riskier projects

- `protocols/skills/project-chronicle/SKILL.md`
- `engines/production/software/skills/merge-preview-check/SKILL.md`
- `protocols/templates/PROJECT_CHRONICLE.md`
- `engines/production/software/templates/MERGE_PREVIEW.md`
- `engines/production/software/tools/check_branch_integrity.py`

## Why this bundle fits Three.js sites

Three.js or animation-heavy sites often have:

- many iterative visual changes
- easy accidental regressions
- bigger diffs than expected
- moving assumptions about assets, performance, and interaction

This bundle helps keep:

- change scope visible
- handoff state durable
- branch drift visible
- completion tied to evidence instead of visual optimism

## Practical note

Do not copy the entire playbook blindly.
Start with the minimum set, then add chronicle and merge-preview support if the project becomes long-running or multi-session.
