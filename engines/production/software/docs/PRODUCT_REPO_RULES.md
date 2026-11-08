# Product Repository Rules

Copy or adapt these rules into the real product repository.

## Workflow infrastructure protection

Treat active workflow files as project infrastructure, not disposable task output.
Do not casually delete, rename, or rewrite files still needed by active requirements.

This includes:

- `AGENTS.md`
- files under `.agents/skills/`
- workflow scripts under `scripts/`
- durable templates kept for active project use

An authorized removal or replacement includes removing or adjusting in-scope workflow scripts, checks and state used only by the retired element. It does not require a separate playbook-maintenance task. A temporary check for that element's absence is removed after its first successful result. Preserve active workflow needs and approved Owner, security and protected-data boundaries.

## Product repository rules block

You can paste this directly into a product repo `AGENTS.md`:

```md
Treat active workflow files as project infrastructure, not disposable task output.
Do not casually delete, rename, or rewrite files still needed by active requirements.
This includes AGENTS.md, files under .agents/skills/, workflow scripts under scripts/, and durable templates kept for active project use.
An authorized removal or replacement includes removing or adjusting in-scope workflow scripts, checks and state used only by the retired element; no separate playbook-maintenance task is required.
Remove a temporary check for that element's absence after its first successful result. Preserve active workflow needs and approved Owner, security and protected-data boundaries.
The product repository is the single source of truth.
```
