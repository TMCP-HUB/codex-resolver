# Post-Commit Recovery Cursor

> Classification: **Solution Pattern — optional**. This is one way to recover a multi-step workflow after an authoritative effect has already committed but later continuation/presentation fails. It is not required when the whole operation is atomic or safely idempotent.

## Problem class

A workflow has two phases:

```text
authoritative domain work
→ later continuation / presentation / acknowledgement
```

The authoritative part can succeed, then a later step can fail. Re-running the whole operation would duplicate or contradict the already-committed effect.

## Production trace

This pattern came from a stateful UI/runtime flow where an accepted gate/scene transition could commit successfully before presentation finalization finished. Recovery had to continue after the committed boundary without replaying the accepted gate or re-running already-published domain effects.

## Assumptions

- an irreversible or non-repeatable commit boundary exists;
- later continuation steps can fail independently;
- the system can retain a small amount of ephemeral/durable continuation state;
- replaying the original operation after commit is unsafe or semantically wrong.

## Use when

Use when:

- payment/order/domain commit succeeds before UI/notification completion;
- workflow engine advances before presentation/cleanup finishes;
- an external side effect succeeds before response delivery;
- a multi-step job needs to resume remaining work without replaying earlier steps;
- recovery can be expressed as a bounded continuation cursor.

## Do not use when

Prefer another design when:

- the full operation is already atomic;
- all steps are safely idempotent and whole-operation replay is simpler;
- a durable workflow engine already persists step completion;
- compensation rather than continuation is the required business behavior;
- the continuation state would become as large/complex as the whole workflow.

## Pattern

### 1. Identify the commit boundary first

Use `irreversible-boundary-reasoning`.

Example:

```text
step A tentative
step B authoritative commit
step C presentation
step D cleanup
```

A failure in C/D must not replay B.

### 2. Choose recovery identity according to process-loss risk

The recovery design must distinguish two cases.

#### Case A — process loss does not matter

If losing the current process cannot cause unsafe replay of B and cannot lose required continuation, an ephemeral cursor recorded after B may be sufficient. It can retain enough state to answer:

```text
what authoritative work is already done?
what remaining step must resume?
what resources/lease must still be released?
```

#### Case B — process loss matters

If the process can die between B and later cursor persistence, a separately persisted cursor written only after B is **not sufficient**. The system must establish a durable recovery identity using one of these mechanisms:

1. persist the continuation/recovery marker atomically with authoritative commit B; or
2. create a durable pre-commit operation/recovery record before B, then reconcile that operation identity against authoritative state after restart.

The second mechanism does not require one database technology or a workflow engine. Its requirement is durable operation identity before the unsafe gap, plus restart reconciliation against authoritative truth.

Examples of bounded recovery identity include:

- committed step index;
- operation ID;
- resource/lease owner;
- presentation-finalization phase;
- retry-safe continuation token.

Do not persist the entire workflow unless needed.

### 3. Separate pre-commit retry from post-commit continuation

```text
failure before B
→ clean retry / abort according to normal rules

failure after B
→ resume C/D only
```

The recovery UI/API should know which class it is handling.

### 4. Make continuation idempotent

The remaining post-commit steps should tolerate duplicate recovery attempts where feasible.

Examples:

- release lease only if still owned;
- mark presentation complete only once;
- re-deliver committed result without re-committing;
- cleanup checks current state before acting.

### 5. Block dependent next work until continuation resolves

If unfinished continuation owns a resource/frontier/lock required by the next operation, prevent the next operation from proceeding until recovery or explicit reset resolves it.

### 6. Define reset semantics separately

A reset/session replacement may discard continuation state only if it also safely resolves/abandons the owned resources and respects already-committed domain truth.

Do not call reset a rollback if committed truth remains.

## Why it works

It represents recovery as continuation from the true committed state rather than trying to time-travel back before an irreversible effect.

The cursor is small because it records only what remains, not a duplicate copy of the whole domain workflow.

When process loss matters, durable recovery identity exists before the unsafe replay gap or is committed atomically with B, so restart can determine whether B already happened rather than guessing from a missing post-B cursor.

## Trade-offs

- introduces another explicit recovery state;
- continuation state must be cleaned up;
- UI/operations need to distinguish failure classes;
- process-loss-safe continuation requires durable recovery identity;
- too many continuation phases may signal the need for a workflow engine, but this pattern does not require one.

## Alternatives

Consider instead:

- transactional workflow that commits only after all required steps;
- durable workflow/orchestration engine;
- idempotent whole-command replay;
- transactional outbox for post-commit side effects;
- compensation/saga when the committed effect should be counteracted;
- operator/manual reconciliation for rare high-risk failures.

## Failure modes

- recovery blindly reruns the original domain command;
- committed gate/payment/send occurs twice;
- B commits, the process dies before a separately persisted recovery cursor, and restart replays B;
- next operation starts while previous continuation still owns a lease/resource;
- continuation cursor is persisted but never invalidated;
- reset deletes recovery state while leaving stranded resources;
- UI reports rollback even though authoritative state advanced;
- cursor grows into a second full workflow state machine.

## Verification

- forced failure immediately before commit uses pre-commit retry path;
- forced failure immediately after commit resumes only continuation;
- when process loss matters, kill the process after B but before any separately attempted post-B cursor write and prove B cannot be replayed because that cursor write was lost;
- after restart, recovery identity plus authoritative-state reconciliation determines whether B already occurred;
- where exactly-once authoritative effect is claimed, repeated restart/recovery proves B remains exactly once;
- continuation can safely be attempted more than once where promised;
- dependent next work is blocked until resource/frontier is released;
- reset/reconciliation cannot resurrect or replay the committed action;
- process-loss behavior matches whether the cursor is legitimately ephemeral or backed by durable recovery identity.

## Related Core Principles

- `irreversible-boundary-reasoning` — defines why pre/post recovery differ;
- `authority-mapping` — identifies the actual domain commit owner;
- `anti-loop-execution` — repeated recovery attempts without changed evidence should stop;
- `exact-state-verification` — recovery must reconcile against current authoritative state.
