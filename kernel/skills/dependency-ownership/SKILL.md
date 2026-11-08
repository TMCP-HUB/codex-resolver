# Dependency Ownership

## Purpose

Use this skill when a feature or release is split across multiple workstreams, subsystems, teams, agents, or staged deliverables.

## Goal

Create a dependency graph with explicit ownership and closure rules so workstreams can progress independently without inventing circular coordination.

This skill governs **delivery ownership**, not module architecture. The same principles apply to frontend/backend work, data pipelines, migrations, infrastructure, documentation, model training, release engineering, and other software work.

## When to use

Use when:

- one workstream produces an artifact another consumes;
- several issues touch a shared contract;
- a project is being delivered in waves/phases;
- multiple agents are working concurrently;
- a release has hard prerequisites;
- one component can be completed by proving contract sufficiency before its consumer exists.

## Do not use when

Do not use this skill to:

- invent dependencies for organizational neatness;
- serialize work that can safely proceed independently;
- require every provider to execute every downstream consumer test;
- hide shared ownership instead of resolving it.

## Inputs

- workstreams/issues;
- objective and scope of each;
- artifacts/contracts produced;
- artifacts/contracts consumed;
- shared resources or schemas;
- release gates.

## Required output

A dependency/ownership map containing for each workstream:

```text
owner
objective
owns
provides
consumes
hard dependencies
non-goals
closure proof
```

And an explicit DAG or ordered dependency list.

## Procedure

### 1. Assign one owner per decision surface

A workstream may touch another workstream's artifact, but it must not silently take ownership of that artifact's semantics.

If two workstreams both claim the same decision surface, resolve that before parallel implementation.

### 2. Distinguish dependency types

Classify each edge:

- **hard implementation dependency** — consumer cannot be correct until provider exists;
- **contract dependency** — consumer can proceed against a stable published contract/fixture;
- **release dependency** — implementation can proceed, but release cannot;
- **verification dependency** — acceptance requires integrated proof;
- **informational dependency** — useful context, not a blocker.

Do not turn every relationship into a hard blocker.

### 3. Publish provider contracts early

A provider should expose enough stable structure for consumers to build against without reconstructing private details.

Useful evidence includes:

- schema;
- interface;
- fixture;
- protocol contract;
- generated type;
- stable identifier set;
- migration contract;
- compatibility test.

The exact artifact depends on the system.

### 4. Use provider/consumer closure law

A provider may close when:

```text
provider implementation complete
+ provider contract stable
+ provider-side proof shows the contract is sufficient for its declared consumers
```

It does **not** necessarily need the consumer's full implementation to exist.

Forbidden cycle:

```text
provider waits for completed consumer
while
consumer waits for completed provider
```

If true integration is required for closure, make that a separate integration/release gate with an owner instead of creating mutual issue ownership.

### 5. Separate shared infrastructure ownership

When several workstreams mutate one shared schema/config/session/manifest/build primitive, create one owner for evolution of that shared surface or establish a strict merge/extension contract.

Feature workstreams should consume the shared contract rather than version it independently.

### 6. Order irreversible or high-risk dependencies late when possible

External providers, destructive migrations, irreversible cutovers, and production-only changes may be intentionally delayed until provider-neutral or reversible integration is already proven.

This is an ordering principle, not a command to always delay every integration.

### 7. Maintain a blocker graph, not a narrative list

For each open blocker, record:

- blocked workstream;
- blocking owner;
- required artifact/decision;
- whether the blocker is hard, release-only, or verification-only.

## Decision rules

- One decision surface should have one explicit owner or an explicit shared-authority contract.
- Consumers depend on provider **contracts**, not provider implementation details.
- A provider's closure proof should test contract sufficiency without requiring arbitrary downstream completion.
- Integration ownership is not automatically the same as feature ownership.
- A release DAG may be stricter than an implementation DAG.
- If dependency direction cannot be drawn without a cycle, ownership or closure criteria are probably wrong.

## Anti-patterns

Avoid:

- circular issue dependencies;
- "everyone owns the shared schema";
- consumers scraping prose, DOM, logs, or implementation internals because the provider omitted stable identifiers/contracts;
- one issue absorbing adjacent features because integration is inconvenient;
- closing a provider only after every possible consumer is complete;
- using release order as an excuse to block independent implementation.

## Verification checklist

- [ ] Every dependency edge has a type.
- [ ] Shared decision surfaces have an owner.
- [ ] Provider contracts are explicit enough for consumers.
- [ ] No accidental coordination cycle exists.
- [ ] Provider closure does not require unrelated consumer completion.
- [ ] Release-only dependencies are not misclassified as implementation blockers.
- [ ] Integration gates have a clear owner.

## Pair with

- `implementation-planning` for workstream definition;
- `authority-mapping` for semantic ownership inside shared state;
- `anti-loop-execution` when dependency confusion becomes a stop condition;
- `proof-loop-verification` for closure evidence.
