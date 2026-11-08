# Docs Assembly

## Purpose

Use this skill to generate and maintain operational documentation from the real repository state instead of vague summaries.

## Goal

Create docs that help future contributors, agents, and maintainers understand:

- architecture
- workflows
- deployment
- QA
- environment assumptions
- operational risks

without becoming stale marketing text.

## When to use

Use this skill when:

- onboarding a repository
- after major architecture changes
- before handoff
- before scaling agent workflows
- when setup requires tribal knowledge
- when deployment/debugging repeatedly confuses contributors

## Change-bound documentation maintenance

For an implementation assignment, maintain the **existing governing documents affected by the authorized change** in the same candidate/PR before completion. A documentation delta is required only when the change makes an existing active instruction, contract, workflow, architecture description, runbook, or operational claim inaccurate. A local fix with no such impact is `NO_DOCUMENTATION_IMPACT`; do not invent files, ceremony, or review work.

- Determine the relevant documents from the task's scope and authority, not by rewriting the whole repository.
- Replace or remove superseded active statements rather than appending contradictory corrections.
- Update current documents in place; use Git history for historical versions. Do not create parallel current carriers.
- Keep approved Owner/Canon meaning and explicit non-goals intact. A discovered new substantive Canon choice goes through existing Canon authority rather than being inferred from code.
- Documentation maintenance is part of the original implementation scope when necessary to make the approved change coherent. It is not permission for unrelated cleanup.
- Return changed document paths, or `NO_DOCUMENTATION_IMPACT`, with the exact implementation handoff.

## Documentation types

| Type | Purpose |
|---|---|
| README | Entry point and quick understanding |
| ARCHITECTURE.md | System structure and responsibilities |
| DEPLOYMENT.md | Deployment and environment workflow |
| QA.md | Testing and QA process |
| CONTRIBUTING.md | Contributor workflow |
| DESIGN.md | UI and design contract |
| RUNBOOK.md | Recovery/debugging operations |

## Procedure

1. Inspect repository structure and scripts.
2. Identify frameworks, deployment targets, and integrations.
3. Document actual workflows, not aspirational workflows.
4. Prefer checklists, commands, and diagrams over essays.
5. Record operational assumptions explicitly.
6. Link related docs together.
7. Keep docs scoped and modular.

## Good documentation properties

| Property | Meaning |
|---|---|
| Operational | Contains commands and workflows |
| Verifiable | References real scripts and paths |
| Minimal | Avoids giant walls of text |
| Durable | Explains concepts unlikely to change daily |
| Modular | Split by responsibility |
| Honest | Calls out limitations and risks |

## Anti-patterns

Avoid:

- AI marketing prose
- documenting systems that do not exist
- giant README files covering everything
- stale setup instructions
- hiding deployment assumptions
- duplicating the same instructions across files

## Required outputs

- docs created or updated
- workflows documented
- commands verified where possible
- missing information called out explicitly
- documentation coverage verdict
