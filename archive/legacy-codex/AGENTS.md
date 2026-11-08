# AGENTS.md

This repository is a reusable Codex playbook for agent-driven software engineering.

## Purpose

Use this repository as a source of practical operating rules for software work.
The priority is not verbosity. The priority is bounded execution, clear authority, branch/state integrity, durable context, and verifiable completion.

## Core operating rules

1. Never claim a task is complete without evidence for the exact candidate being claimed complete.
2. Before substantial work, define objective, owner, scope, non-goals, dependencies, acceptance criteria, gates, and stop conditions; then freeze the workstream.
3. Work in exactly one execution mode at a time:
   - **EXECUTION MODE** — implement frozen scope;
   - **CAUSAL AUDIT MODE** — stop feature work and establish cause after a stop condition.
4. Repeated same-class failure is a signal to stop guessing, not permission for another point-fix.
5. New out-of-scope findings are recorded separately unless they directly block correctness/security of frozen scope.
6. Map decision authority when multiple components can observe, store, project, or mutate the same conceptual state.
7. Do not confuse a carrier/projection/presentation/observer with the authority that decides a fact.
8. Model multi-workstream dependencies explicitly; avoid provider/consumer coordination cycles.
9. Evidence belongs to the exact artifact/state that produced it. Material state changes require re-evaluation of affected evidence.
10. Identify irreversible/non-repeatable boundaries before designing retries or recovery.
11. Distinguish mechanical evidence, engineering/semantic evidence, and explicit acceptance/release authority.
12. Prefer small, reviewable changes over broad rewrites.
13. Do not overwrite or delete unrelated code to make a local task pass.
14. Record branch provenance before major edits and treat unexplained HEAD divergence as a stop condition.
15. Keep durable handoff state in files/issues/artifacts, not only in chat history.
16. Separate tactical handoff from long-term project history.
17. When uncertain, preserve information rather than compressing it away.
18. For UI work, use an explicit design contract instead of inventing one-off styling.
19. Load only the skills needed for the current decision/work phase.

## Core principle vs solution pattern

Keep these categories separate.

### Core engineering principle

A broad rule about reasoning, ownership, execution, evidence, or recovery that remains useful across technology choices.

Examples:

- stop repeated guess-and-patch loops;
- identify authority before shared-state implementation;
- bind evidence to exact state;
- distinguish recovery before/after irreversible effects.

### Solution pattern

An optional implementation strategy for a narrower technical problem.

A solution pattern must never become a global architecture mandate merely because it worked well before. It should state:

- problem class;
- assumptions;
- use when;
- do not use when;
- pattern;
- trade-offs;
- alternatives;
- failure modes;
- verification.

Projects remain free to choose a different solution when assumptions differ.

## Progressive skill loading

Do not read the whole playbook by default.

Use:

1. `SKILLS_INDEX.md` first;
2. load the smallest skill that owns the current decision;
3. add paired skills only when the work crosses a real boundary;
4. load templates only if required.

The playbook should behave like a toolbox, not one giant permanent prompt.

## Workstream minimum

Before substantial implementation, capture:

- objective;
- owner;
- current authoritative state;
- scope;
- non-goals;
- dependencies;
- acceptance criteria;
- gates;
- stop conditions;
- deferred-findings location.

Then freeze the scope before entering Execution Mode.

## Branch integrity minimum

Before substantial branch work, capture:

- current branch;
- target branch;
- base commit SHA;
- merge base with target branch;
- intended HEAD when established;
- intended scope;
- touched files.

Before final sign-off, verify:

- working HEAD equals intended HEAD;
- PR HEAD equals intended HEAD if a PR exists;
- review/test evidence applies to current HEAD or staleness is explicit;
- diff still matches frozen scope;
- target branch has not invalidated the work;
- merge/rebase risk has been assessed.

## Durable artifacts

Useful artifacts include:

- frozen implementation plan;
- dependency/ownership map;
- authority map;
- causal audit note;
- task evidence;
- session handoff;
- branch state;
- merge preview notes;
- project chronicle;
- design contract;
- QA report;
- spike report.

Templates live in `templates/`.
Skills live in `.agents/skills/`.

## Core engineering principles in this repository

- `anti-loop-execution`
- `authority-mapping`
- `dependency-ownership`
- `exact-state-verification`
- `irreversible-boundary-reasoning`
- `evidence-and-authority`
- `security-property-calibration`
- `async-lifetime-ownership`

## Existing execution/support skills

- `implementation-planning`
- `systematic-debugging`
- `git-branch-integrity`
- `proof-loop-verification`
- `pre-merge-review`
- `merge-preview-check`
- `session-handoff`
- `project-chronicle`
- `design-system-authoring`
- `webapp-dogfood-qa`
- `playwright-dogfood-harness`
- `operational-auditing`
- `docs-assembly`
- `spike-prototyping`
- `skill-authoring`
- `laravel-contract-first`

## Authoring guidance

Keep files concise and decision-oriented.
Prefer decision rules, procedures, evidence requirements, and failure modes over essays.
Do not turn this repository into a giant generic prompt dump.
Do not create a second skill merely to rename an existing responsibility.
Do not encode one project's successful implementation choice as a universal engineering law.
