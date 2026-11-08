# Codex Playbook

This repository contains a practical Codex playbook for safe, bounded, evidence-driven software work across different stacks and project types.

The playbook has two intentionally different knowledge layers:

1. **Core engineering principles** — architecture-neutral rules for planning, authority, dependency ownership, anti-loop execution, exact-state evidence, irreversible boundaries, security-property calibration, async lifetime ownership, and acceptance.
2. **Solution patterns** — optional implementation recipes for narrower technical problem classes. A successful pattern is never treated as the mandatory architecture for every project.

## Structure

- `AGENTS.md` — root operating rules for Codex;
- `SKILLS_INDEX.md` — progressive skill discovery layer;
- `.agents/skills/` — on-demand skills for recurring workflows and optional patterns;
- `templates/` — reusable state, evidence, QA, spike, and design templates;
- `.codex/` — local Codex config placeholders.

## Goals

- stop guess-and-patch execution loops;
- freeze non-trivial workstreams before implementation;
- make decision/source-of-truth ownership explicit;
- prevent accidental dependency/coordination cycles;
- preserve branch and artifact provenance;
- bind evidence to the exact state that produced it;
- reason correctly about retry/recovery around irreversible effects;
- calibrate security claims before selecting controls;
- give correctness-relevant async side effects explicit lifetime/acknowledgement ownership;
- distinguish mechanical checks, engineering judgment, and acceptance authority;
- require evidence before declaring work complete;
- keep durable session handoffs and project history;
- debug from root cause instead of repeated patching;
- make reusable technical recipes easy to find without turning them into mandatory architecture;
- preserve the freedom to choose different technical solutions when project assumptions differ.

## Core engineering principles

- `anti-loop-execution`
- `authority-mapping`
- `dependency-ownership`
- `exact-state-verification`
- `irreversible-boundary-reasoning`
- `evidence-and-authority`
- `security-property-calibration`
- `async-lifetime-ownership`

These skills describe **how to reason and execute**, not which database, cloud, frontend framework, telemetry architecture, state model, security product, queue/runtime, or provider to select.

## Optional Solution Patterns

The repository also carries concrete recipes extracted from production engineering problems. Each pattern is intentionally assumption-bound and includes `Do not use when`, trade-offs, alternatives, failure modes, and verification.

### State / provenance / concurrency

- `versioned-signed-state-envelope`
- `immutable-deployment-data-pinning`
- `single-writer-session-reconciliation`
- `stable-semantic-identifiers`
- `legacy-schema-adoption`
- `transactional-semantic-state`

### Events / retry / recovery

- `server-authoritative-event-journal`
- `post-commit-recovery-cursor`
- `immutable-retry-snapshot`
- `capture-on-get-consume-on-post`
- `plan-revalidate-apply-fence`

### Delivery / observation / provider / presentation

- `publication-frontier`
- `read-only-observer-facade`
- `provider-late-binding`
- `presentation-completion-barrier`
- `accessibility-commit-announcement`

### Architecture enforcement

- `architectural-dependency-fence`

These are **not defaults**. For example, `server-authoritative-event-journal` is useful for a certain class of ordered accepted-event traces, while browser analytics, OpenTelemetry, event streams, transactional outboxes, or simple audit tables may be more appropriate elsewhere.

## Core execution/support skills

- `implementation-planning`
- `systematic-debugging`
- `git-branch-integrity`
- `proof-loop-verification`
- `pre-merge-review`
- `merge-preview-check`
- `session-handoff`
- `project-chronicle`

## Design, QA, audit, and documentation

- `design-system-authoring`
- `webapp-dogfood-qa`
- `playwright-dogfood-harness`
- `operational-auditing`
- `docs-assembly`
- `spike-prototyping`
- `skill-authoring`
- `laravel-contract-first`

## Core principle vs solution pattern

A core principle may say:

> Identify the irreversible boundary before designing retries.

A solution pattern may say:

> Under assumptions A/B/C, retain a small post-commit continuation cursor so recovery resumes remaining work without replaying the committed action.

The first is broadly applicable reasoning discipline. The second is a selectable technical design with assumptions and trade-offs.

This distinction is deliberate: the playbook should become smarter from prior projects without trapping future projects inside prior architecture.

## Important loading rule

Do not load the whole playbook into every task.

Use:

1. `SKILLS_INDEX.md`;
2. the smallest useful Core or workflow skill that owns the current decision;
3. only then load a Solution Pattern if its assumptions match the actual technical problem;
4. supporting templates only when required.

Never choose a Solution Pattern just because its title sounds similar to the task. Read its alternatives and rejection conditions first.

Adapt the playbook per repository instead of dumping everything into one giant permanent prompt.
