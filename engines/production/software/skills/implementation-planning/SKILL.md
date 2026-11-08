---
name: implementation-planning
description: Plan bounded multi-step software implementation with applicable acceptance, evidence, dependencies, and capable actors.
---

# Implementation Planning

## Purpose

Use this skill before multi-step implementation, risky refactors, migrations, integrations, or delegated execution.

## Goal

Create a bounded, verifiable workstream that can be frozen before implementation and executed without hidden scope expansion.

This skill owns **planning the workstream**. `anti-loop-execution` owns execution mode and stop-condition behavior after the plan is frozen.

## When to use

Use when:

- a feature touches multiple files or systems;
- deployment or migration risk exists;
- UI, API, data, infrastructure, or external services interact;
- another agent or future session will continue the work;
- the implementation path has meaningful dependencies;
- a task needs explicit acceptance/release gates.

Do not use this skill for tiny single-file edits where ownership, dependency, and rollback questions are trivial.

## Inputs

- requested outcome;
- current repository/system state;
- relevant contracts and existing implementation;
- existing authoritative operational documents governing the touched scope (when any);
- likely dependencies and owners;
- known risks;
- available verification paths.

## Execution contract

- **Supplied-material mode:** Reason from sufficient material already provided. No external execution capability is inherently required; conclusions are limited to that material.
- **Repository/file-read mode:** When the plan needs additional source facts, read the exact relevant source through an authorized remote or local surface. A remote repository read requires `repository_remote_read`; a local source requires the selected surface's file-read access. This establishes source contents, not live, deployed, or visual behavior. A shell or checkout is needed only when the selected mode actually requires it.
- **Live-state mode:** Only if the planning assignment itself requires current runtime or visual observations, use the relevant accessible runtime, service, or browser/device surface. Such observation proves only what was actually observed in that state and environment.
- **Frozen-plan mode:** Only when the assignment requires the plan to be recorded, use `durable_artifact_write` or the admitted write capability of the existing destination, with readback when its applicable contract requires it. This establishes the recorded plan, not completion of the planned work.

Planning has no default network, browser, Preview, screenshot, deployment, or human-acceptance prerequisite. Select each required check for its actual claim and assign it to an actor with the necessary access and capabilities; those are the checking actor's requirements, not automatically the planner's. Static, runtime, and browser observations prove different claims; do not present a weaker mode as equivalent.

Before assignment, if a mandatory input or required plan-recording capability for this specific planning result is unavailable, return `ASSIGNMENT_NOT_ADMISSIBLE` for that assignment. If a proven capability disappears after admission, report `BLOCKED_RUNTIME_DRIFT` or the precise partial/unproven boundary as applicable. Preserve completed work and continue independent authorized work; an unavailable later checker does not by itself prevent an otherwise executable planning task.

## Required outputs

A plan should include:

- objective;
- owner;
- scope;
- non-goals;
- dependencies and dependency type;
- likely files/systems touched;
- completion delta: affected governing docs, and in-scope temporary/legacy mechanisms to retire where the authorized end state replaces them (or `NONE`);
- high-risk areas;
- implementation phases;
- acceptance criteria;
- gates when applicable;
- stop conditions;
- verification commands/checks when applicable;
- rollback/recovery notes where relevant;
- deferred-findings location.

## Frozen multi-PR workstream

When the Owner authorizes several dependent or parallel code changes as **one deliverable**, freeze their end outcome and necessary delivery order in the existing Issue/approved project record. Include per-stage and final outcome acceptance, any CI/Preview or independent verification actually required by the approved scope or applicable project contract, allowed merge transitions, blockers, non-goals and stop conditions.

A stage produces a PR only when it is a real reviewable code slice; do not create a PR per conceptual step or a second roadmap. The Director maintains a compact cursor in the same governing record and continues after accepted child results. Assignments are compiled/admitted separately at their execution time, and only currently admitted steps may run. The cursor is an existing Issue/HANDOFF projection, not a new artifact schema. Do not infer that a child's `COMPLETE` means the full workstream is complete, or that an ended Work session will wake automatically.

## Procedure

### 1. Define the objective

One or two sentences describing the observable outcome.

Do not encode an implementation choice as the objective unless the implementation itself is the requirement.

### 2. Assign ownership

Record the workstream owner and any shared decision surfaces it consumes from other owners.

If ownership is ambiguous, resolve it or use `dependency-ownership` before implementation.

### 3. Define scope and non-goals

List:

- systems touched;
- files/directories likely touched;
- contracts that may change;
- what explicitly must not change.

Non-goals are especially important when adjacent architecture is tempting to clean up.

For a staged replacement, migration, or temporary workaround, identify which in-scope aids are temporary and their authorized retirement point. Do not make them permanent architecture by omission or expand cleanup to unrelated historical artifacts.

### 4. Map dependencies

Classify meaningful dependencies as:

- hard implementation;
- contract;
- release;
- verification;
- informational.

Do not block work on a downstream implementation when a stable provider contract/fixture is sufficient.

### 5. Identify risks

Examples:

- merge drift;
- shared-schema ownership;
- external provider dependency;
- irreversible side effect;
- compatibility with persisted state;
- concurrency/stale-client behavior;
- deployment/config mismatch;
- mobile/accessibility regression;
- generated-artifact drift.

Use project-specific risks rather than copying this list mechanically.

### 6. Split into bounded phases

Good phase boundaries correspond to independently understandable outputs or proof gates.

Examples, only when applicable:

- contract/discovery;
- implementation slice;
- migration/data transition;
- integration;
- verification;
- deployment;
- operational QA when needed.

Avoid giant phases such as "implement everything".

### 7. Define acceptance criteria

Use observable outcomes. For an authorized replacement or retirement, the outcome includes removal of obsolete in-scope code, scripts, fallback paths, and governing instructions where they cease to be needed; disabling a retired mechanism or deferring its cleanup is not equivalent to removing it.

Bad:

```text
Architecture improved.
```

Good:

```text
Every writer preserves fields it does not own and stale revisions are rejected by the declared conflict rule.
```

### 8. Define gates

A gate is evidence or authority required before the workstream may advance or close. Include only gates required by the actual outcome or applicable contract.

Examples, only when applicable:

- contract/schema accepted;
- required exact-candidate checks complete;
- migration replay verified;
- browser/device QA for a claim that needs it;
- upstream dependency accepted;
- release authority explicitly granted.

Do not make green CI the universal gate for semantic/product decisions.

### 9. Define stop conditions

A plan without stop conditions encourages loops.

Include conditions such as:

- two mutating correction generations are followed by actually executed red required checks on the same candidate/repair boundary, even with different error classes;
- one tool/process operation fails identically twice without new evidence;
- authoritative state becomes ambiguous;
- required scope crosses a non-goal;
- dependency contract is contradictory;
- irreversible effect cannot be recovered safely;
- exact tested/reviewed state diverges from working state.

Execution behavior after a stop condition is owned by `anti-loop-execution`.

### 10. Define verification

Select evidence for the approved outcome and each actual acceptance claim. Use relevant existing checks or bounded semantic/visual assessment when needed; do not require new tests, a person, screenshots, or Preview by default. Assign every required check to an actor able to perform it. When independence is required, an eligible Director who did not implement may review where allowed; use a separate capable agent when required or selected.

Keep selected proof mandatory: code inspection alone does not establish live or visual behavior. If required evidence is unavailable, mark only the affected result unproven, report completed work accurately, and continue independent authorized work; do not claim the full outcome complete without its required proof. Tie important evidence to the exact candidate using `exact-state-verification`.

### 11. Freeze the plan

Before substantial implementation, record the plan as the current workstream contract.

If scope must change later, explicitly replan/refreeze rather than letting implementation silently redefine the task.

### 12. Record deferred findings

Choose where non-blocking discoveries go: issue, backlog, audit note, TODO registry, or another durable artifact.

Do not fix them inside the frozen workstream merely because they were noticed.

## Anti-patterns

Avoid:

- vague architecture plans;
- scope defined only by a list of files;
- no owner for shared state/contracts;
- every relationship marked as a hard dependency;
- giant rewrite phases;
- hidden scope expansion during implementation;
- no rollback/recovery notes for irreversible changes;
- plans that assume chat-only context;
- verification that depends only on confidence;
- no explicit point at which implementation must stop and audit assumptions.

## Minimal plan structure

```md
# Objective
# Owner
# Scope
# Non-goals
# Dependencies
# Risks
# Phases
# Acceptance criteria
# Gates
# Stop conditions
# Verification
# Rollback / recovery
# Deferred findings
```

## Minimal verdict format

State the bounded plan, selected claims with their evidence and responsible actors, and any result whose required proof is unavailable.

## Strategy 2030 product planning

Apply `kernel/STRATEGY_2030.md` using this existing plan. Identify the authoritative domain/service seam before interface design; UI, API and agent adapters consume it. MCP functions may ship ahead of UI and need not wait for UI parity. Include required AI-search optimization and semantic HTML projections for public discoverable product information. For applicable agent-enabled products, include A2A implementation as required work with a bounded stage and evidence; a deferral remains open, not optional or complete. Record non-applicability only where the actual product/scope supports it. No dummy server, extra infrastructure or unrelated retrofit is implied by a small repair.

For site-to-agent integration, evaluate existing WebMCP/MCP/A2A approaches against the actual missing capability before the Owner's conditional separate-repository project is activated. A draft is not an adopted standard and differing names do not establish a gap.

## Conditional Admin/API readiness

When designing an Admin UI or business API, check whether the current domain operations already live behind one authoritative service/API boundary that another client could reuse. If MCP is not requested, preserve that seam and stop; no MCP endpoint, tool-parity matrix, queue, gateway, or additional test is mandatory. When MCP is in scope, select `mcp-adapter-intake` first and only the other four MCP skills relevant to the exact assignment. Keep business authority and authentication in their existing owners.

## Pair with

- `dependency-ownership` for multi-workstream DAGs;
- `authority-mapping` for shared decision ownership;
- `anti-loop-execution` after the plan is frozen;
- `irreversible-boundary-reasoning` for non-repeatable effects;
- `proof-loop-verification` for completion.
