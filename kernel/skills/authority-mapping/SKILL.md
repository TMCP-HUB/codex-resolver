# Authority Mapping

## Purpose

Use this skill when a system has multiple components that can observe, store, transform, project, cache, or mutate the same conceptual state.

## Goal

Make decision ownership explicit before implementation so the system does not accidentally create competing sources of truth.

This skill does **not** prescribe server authority, client authority, event sourcing, databases, state machines, or any particular architecture. It asks which component is authoritative for each decision in the architecture you actually choose.

## When to use

Use when:

- UI, API, storage, cache, workers, queues, generated artifacts, or external services interact;
- multiple subsystems write one shared record or session;
- a read model/projection may be mistaken for writable source state;
- stale clients or concurrent actors can observe different revisions;
- recovery behavior depends on knowing what has already become authoritative;
- a refactor moves logic across boundaries.

## Do not use when

Do not use this skill to:

- force all authority into one process;
- replace domain modeling;
- justify a centralized coordinator for every system;
- label every value "authoritative" without specifying the decision it owns.

## Inputs

- conceptual facts or decisions in the feature;
- components that read/write them;
- persistence and transport boundaries;
- external systems involved;
- existing contracts and invariants.

## Required output

An authority map. Minimum shape:

| Decision / fact | Authority owner | Allowed writers | Readers / projections | Persistence / carrier | Conflict rule |
|---|---|---|---|---|---|

Also record any unresolved authority conflict.

## Procedure

### 1. Name decisions, not containers

Bad:

```text
Database is authoritative.
```

Better:

```text
Order payment status is accepted only by payment-confirmation logic.
The database stores the accepted result.
```

A storage location can carry authority without being the component that decides meaning.

### 2. Separate these roles

For each important state item, distinguish where applicable:

- **decision authority** — decides whether a transition/fact is accepted;
- **writer** — may persist or publish the accepted result;
- **carrier** — transports/stores state;
- **projection** — read-only or reduced view;
- **presentation** — displays state;
- **observer** — records evidence about state;
- **external authority** — third-party system whose decision the product must respect.

One component may hold several roles, but do not assume that automatically.

### 3. Identify illegal authority elevation

Look for patterns such as:

- UI appearance being treated as proof a command succeeded;
- cache contents overriding newer source state;
- analytics/observer data being replayed as canonical business state;
- a generated artifact silently redefining its source contract;
- a partial writer reconstructing a shared object and dropping fields it does not own;
- a stale client overwriting a newer revision;
- a transport retry being interpreted as a new domain action.

### 4. Define mutation ownership

For shared state, specify which subsystem owns each field or transition.

A subsystem that does not own a field should normally preserve it, ignore it, or operate through the owning interface—not reconstruct it from a partial local model.

### 5. Enforce decisive invariants at a boundary that cannot be bypassed

If an invariant decides whether an externally reachable read/mutation may occur, identify the authority-bearing boundary that can actually accept or perform the operation.

UI hiding, disabled controls, client validation, or an early preflight may improve UX, but they do not replace enforcement when stale clients, direct requests, alternate callers, races, or modified consumers can bypass them.

Examples of decisive invariants include:

- authorization/scope checks;
- feature/capability enablement that governs whether an operation is legal;
- uniqueness or ownership constraints;
- stale-revision rejection;
- terminal/closed-state mutation prohibitions.

The exact enforcement mechanism depends on architecture. A database constraint, service check, capability boundary, conditional write, or another mechanism can all be valid if it actually sits below the relevant bypass paths.

### 6. Reflect ownership in capability topology where practical

A component documented as "not an owner" can still become an accidental owner if it holds broad credentials, bindings, write access, or mutation-capable service references that bypass the declared interface.

Ask whether non-owners need the direct capability at all.

Prefer the smallest capability surface consistent with the chosen architecture, while avoiding a universal rule that every ownership boundary must be enforced by network separation or separate databases.

Capability topology is supporting enforcement for the authority map, not a substitute for the semantic map itself.

### 7. Define conflict behavior

For every place two authorities could disagree, choose an explicit rule:

- reject stale mutation;
- reconcile from owner;
- merge by declared field ownership;
- compensate;
- require declared authority/operational resolution;
- fail closed;
- fail open where correctness allows.

Do not let "last response wins" become an accidental conflict policy.

### 8. Audit projections

A projection may intentionally omit information. Record whether it is:

- read-only;
- stale-tolerant;
- safe to cache;
- safe to expose publicly;
- sufficient for a specific consumer;
- forbidden as a mutation source.

A derived/composite projection must not claim a stronger state than the authoritative predicates it actually has. Missing predicates should remain unknown/partial unless the domain explicitly defines a safe default.

## Decision rules

- Authority is scoped to a **decision**, not awarded to a technology category.
- Having a copy of data does not grant mutation authority.
- Presentation and observability do not automatically create domain facts.
- UI/preflight checks do not substitute for decisive enforcement at a bypass-resistant authority-bearing boundary.
- Non-owner components should not retain broad mutation capabilities merely by convention when a narrower owned interface is practical.
- A retry does not automatically create a new intent.
- Shared state needs explicit ownership or an explicit merge rule.
- Derived/composite claims cannot be stronger than their current authoritative predicates.
- If two components can independently make contradictory decisions about the same fact, the architecture has an unresolved authority conflict.

## Anti-patterns

Avoid:

- "the frontend knows" / "the backend knows" without naming the fact;
- global singleton coordinators added only to hide unclear ownership;
- treating database rows as self-interpreting truth;
- reconstructing authoritative state from logs because the actual owner is inconvenient;
- exposing a full internal object when a bounded projection is sufficient;
- allowing multiple partial writers to replace one shared envelope/document wholesale;
- relying on hidden/disabled UI as the only enforcement for a reachable operation;
- giving a non-owner broad direct write capability and relying only on code-review convention not to use it.

## Verification checklist

- [ ] Every important decision has an owner.
- [ ] Writers and readers are distinguished from decision authority.
- [ ] Projections cannot silently become mutation sources.
- [ ] Shared-state field ownership is explicit where needed.
- [ ] Decisive externally reachable invariants are enforced at a boundary that relevant bypass paths cannot skip.
- [ ] Non-owner capability surfaces are no broader than the architecture actually requires, where practical.
- [ ] Composite/derived projections do not overclaim missing predicates.
- [ ] Stale/concurrent conflicts have a declared rule.
- [ ] Recovery paths respect already-authoritative decisions.
- [ ] No technology is declared globally authoritative without a scoped reason.

## Pair with

- `dependency-ownership` for workstream/component boundaries;
- `irreversible-boundary-reasoning` for accepted effects that cannot be replayed;
- `exact-state-verification` for revision/provenance checks;
- `evidence-and-authority` when a derived claim depends on partial predicates;
- `security-property-calibration` when ownership is part of an authorization/security claim;
- `implementation-planning` before multi-system changes.
