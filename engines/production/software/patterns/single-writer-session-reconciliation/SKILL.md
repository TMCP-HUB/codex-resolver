# Single-Writer Session Reconciliation

> Classification: **Solution Pattern — optional**. This is one way to prevent stale clients from overwriting newer shared session/workflow state. It is not a universal concurrency model.

## Problem class

Several browser tabs, clients, workers, or concurrent requests can mutate one logical session/workflow. A response created from stale state may arrive later and overwrite a newer authoritative revision.

## Production trace

This pattern came from a protected multi-tab web flow where a replaced session could be mutated by an older tab unless every write proved which session revision it believed it was updating.

## Assumptions

- there is one logical authoritative session/workflow state;
- mutations can carry an expected revision/mark/version;
- the authority can reject or reconcile stale writers;
- last-write-wins would be incorrect for at least some fields.

## Use when

Use when:

- multiple tabs/devices can mutate one session;
- long requests or lost responses make response order unreliable;
- session replacement/restart can occur while old clients remain open;
- several commands share one server-owned state object;
- stale writes could erase newer fields or resurrect old state.

## Do not use when

Prefer another model when:

- mutations are naturally commutative/mergeable;
- CRDT/event-sourced reconciliation is the actual requirement;
- each client owns independent state;
- optimistic concurrency is unnecessary because all writes are serialized elsewhere;
- conflicts should be merged field-by-field rather than rejected.

## Pattern

### 1. Give each accepted revision a monotonic or unique mark

The exact form may be:

- integer revision;
- opaque random session mark;
- ETag/version token;
- generation ID;
- durable sequence.

### 2. Require expected revision on mutation

```text
client read revision R
→ mutation(expected=R)
```

The authority checks the expectation before applying the mutation.

### 3. Reject stale writers before mutation

If authoritative revision is now `R+1` or a different session generation:

```text
expected R != authoritative R+1
→ no mutation
→ return explicit stale/session-changed result
```

Do not partially apply and reconcile afterward unless that is the declared model.

### 4. Reconcile by adopting authority, not replaying stale local state

After rejection, the stale client should usually:

- fetch/adopt current authoritative state;
- discard invalid pending assumptions;
- re-present user intent if still meaningful;
- retry only as a new deliberate action when safe.

Do not rebuild newer authority from stale local snapshots.

### 5. Preserve unrelated fields on valid writes

Expected-revision checking does not replace field ownership.
A valid writer still must preserve fields it does not own when mutating a shared object.

### 6. Separate request identity from session revision

A retry of the **same command** may need an idempotency key in addition to expected session revision.

Revision protects shared-state freshness.
Idempotency protects duplicate command execution.
They solve different problems.

## Why it works

The authority refuses to accept a write whose causal premise is known to be stale. This prevents delayed responses or stale tabs from silently reverting newer shared state.

## Trade-offs

- users may see conflict/reconciliation flows;
- every mutation path must propagate the revision correctly;
- long-running operations may need revalidation at commit time;
- offline-first editing may need a richer merge model;
- rejected intent may need UX to retry consciously.

## Alternatives

Consider instead:

- serialized actor/queue ownership;
- database optimistic concurrency/compare-and-swap;
- pessimistic locking;
- CRDT/operational transform for collaborative merge;
- append-only event commands with conflict resolution;
- independent per-tab sessions if cross-tab continuity is unnecessary.

## Failure modes

- revision is returned but not checked on every mutation path;
- restart creates a new session but old tabs can still mutate it;
- stale rejection is treated as a generic retryable network error and loops;
- a writer with the correct revision replaces the whole shared object from a partial model;
- revision and idempotency are conflated;
- client guesses/reconstructs authoritative revision after conflict.

## Verification

- two clients read same revision; first write succeeds, second stale write is rejected;
- session replacement invalidates old-generation mutations;
- stale rejection causes zero authoritative state mutation;
- reconciliation adopts current authority;
- unrelated fields survive valid subsystem mutations;
- lost-response retry behavior is separately safe/idempotent where needed;
- concurrent tests cover the actual storage/authority boundary rather than only UI state.

## Related Core Principles

- `authority-mapping` — decide who owns the shared session revision;
- `irreversible-boundary-reasoning` — stale retries must not replay already-committed actions;
- `exact-state-verification` — revision identity is the state being proved;
- `anti-loop-execution` — repeated conflict retries without changed state are a loop.
