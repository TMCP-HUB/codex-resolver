# Transactional Semantic State

> Classification: **Solution Pattern — optional**. This is one proven way to prevent intermediate mutations inside one logical unit from becoming authoritative before the unit succeeds. It is not a substitute for every database transaction, event-sourced model, or saga.

## Problem class

A logical unit performs several internal mutations before it is semantically complete. Individual writes may succeed while the enclosing unit later fails. If intermediate state leaks into persistence, checkpoints, projections, or externally visible state, the system can publish a combination no valid completed operation authorized.

## Production trace

This pattern came from a stateful runtime where several mutations belonged to one higher-level semantic step. The stable design staged changes in a draft, kept published state unchanged during the unit, and advanced published state plus completion/pointer metadata only after the entire unit succeeded. Forced failures discarded the draft and preserved the last real published boundary.

## Assumptions

- there is a meaningful semantic unit above individual mutations;
- partial intermediate state is not valid authoritative truth;
- tentative state can be staged, copied, buffered, or otherwise isolated;
- the unit has a recognizable success/failure boundary;
- external consumers can be restricted to published state.

## Use when

Use when:

- one workflow/scene/turn/command contains several mutations that should become visible together;
- multi-field edits must not expose partial accepted state;
- checkpoints must represent only coherent domain boundaries;
- a later internal step can fail after earlier tentative mutations;
- retry should restart from the last published semantic boundary.

## Do not use when

Prefer another design when:

- every incremental mutation is intentionally authoritative;
- one ordinary database transaction already spans the entire semantic boundary cleanly;
- event sourcing is the chosen model and each event is intentionally authoritative;
- compensation/saga semantics are more truthful than discarding tentative changes;
- state is too large/expensive to copy and a different isolation mechanism is more appropriate.

## Pattern

### 1. Identify the semantic unit

Name the higher-level operation that must succeed as one meaningful transition.

Do not define the unit merely from existing function/file boundaries.

### 2. Derive a draft from published state

Create an isolated tentative representation from the last authoritative state.

The mechanism may be:

- copy-on-write object;
- transaction-local state;
- immutable command/result draft;
- buffered mutations;
- staged records;
- another architecture-specific isolation technique.

### 3. Apply internal mutations only to the draft

Intermediate operations may validate and transform the draft, but external projections/checkpoints must not treat it as authoritative.

### 4. Treat commit intent separately from publication

An internal instruction such as "commit" may authorize the unit to publish when all remaining requirements succeed. It should not necessarily publish immediately if later mandatory steps still belong to the same semantic unit.

### 5. Publish once at the real boundary

On full success, advance the authoritative state and any completion marker/pointer that semantically belongs to that transition as one coherent publication boundary.

Use the strongest atomicity mechanism the chosen architecture actually provides; do not claim cross-system atomicity that does not exist.

### 6. Discard draft on failure before publication

A failed unit should leave externally authoritative state at the prior published boundary unless the domain explicitly defines partial/compensated truth.

### 7. Expose checkpoints only from coherent boundaries

Persistence or resume snapshots should not serialize an active tentative unit as though it were published truth.

## Why it works

It aligns external authority with the domain's semantic commit boundary rather than with incidental mutation timing. Retry and recovery begin from a real accepted state instead of repairing combinations that should never have become public.

## Trade-offs

- additional draft/isolation state;
- more explicit lifecycle code;
- large state copies may be expensive;
- arbitrary mid-unit checkpoints become unavailable or more complex;
- debugging must distinguish tentative and published state;
- multi-system publication may still require outbox/saga/workflow patterns.

## Alternatives

Consider instead:

- native database transaction spanning the complete unit;
- event sourcing with intentionally authoritative events;
- immutable command/result followed by one apply;
- saga/compensation;
- durable workflow engine;
- intentionally authoritative incremental steps.

## Failure modes

- code mutates published state directly while a draft exists;
- an internal commit intent publishes before all mandatory steps succeed;
- checkpoint/export serializes tentative state;
- pointer/completion marker advances before state publication succeeds;
- retry resumes a half-finished draft rather than the last published boundary;
- draft is reused across unrelated operations;
- the pattern is used to pretend multiple independent external systems share one transaction.

## Verification

- inject failure after each intermediate mutation and assert authoritative state remains the previous published state;
- successful unit publishes exactly one coherent new state;
- external readers/projections never observe the active draft as authority;
- checkpoints cannot represent an active draft as completed truth;
- retry after pre-publication failure begins from the last published boundary;
- direct mutation bypasses are mechanically or structurally prevented where practical;
- cross-system effects are tested according to their real transaction boundaries.

## Related Core Principles

- `authority-mapping` — distinguishes draft carrier from authoritative published state;
- `irreversible-boundary-reasoning` — identifies the real publication/commit boundary;
- `exact-state-verification` — binds checkpoints and published state evidence;
- `evidence-and-authority` — prevents internal mutation success from being overclaimed as semantic completion.
