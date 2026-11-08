# Irreversible Boundary Reasoning

## Purpose

Use this skill when a workflow contains effects that cannot be honestly replayed, rolled back, or treated as if they never happened.

## Goal

Identify the authoritative commit boundary and design different recovery behavior for failures before and after it.

This skill does not require transactions, queues, event sourcing, sagas, or any specific implementation pattern. It supplies the reasoning model needed to choose among them.

## When to use

Use for workflows involving:

- payments or financial capture;
- emails/messages already sent;
- external API side effects;
- destructive data changes;
- account/security transitions;
- deployment/cutover;
- signed/accepted user actions;
- jobs where duplicate execution is unsafe;
- multi-step workflows where state commits before presentation or acknowledgement finishes.

## Do not use when

Do not use this skill to:

- label every write irreversible;
- prohibit compensation where compensation is valid;
- assume database rollback can undo external side effects;
- force one recovery mechanism across every boundary.

## Inputs

- ordered workflow steps;
- authoritative state transitions;
- external side effects;
- retry/replay behavior;
- acknowledgement/response behavior;
- available idempotency or compensation mechanisms.

## Required output

A boundary map:

```text
steps before authoritative boundary
boundary itself
steps after boundary
reversibility classification
compensation classification
repeatability / retry classification
pre-boundary recovery
post-boundary recovery
retry identity/idempotency requirements
```

## Procedure

### 1. Classify effects on independent axes

For each meaningful effect, classify one value on **each** applicable axis. These axes are independent; do not collapse them into one mutually exclusive category.

**Axis 1 — Reversibility**

- **reversible** — can be rolled back without changing external truth;
- **irreversible** — cannot be honestly undone as if it never happened.

**Axis 2 — Compensation**

- **compensatable** — a separate explicit action can restore business intent or offset the effect;
- **non-compensatable / no defined compensation** — no valid compensating action is defined.

**Axis 3 — Repeatability / Retry**

- **idempotently repeatable with the same identity** — repeating the same operation under the same identity does not create a second effect;
- **conditionally repeatable** — replay is safe only after specified reconciliation/preconditions;
- **non-repeatable** — replay may duplicate or contradict reality.

An effect therefore occupies one value on each axis. The classification is semantic, not based only on storage technology.

Example: a payment capture may be **irreversible**, **compensatable** by a separate refund, and **idempotently repeatable with the same idempotency identity**. The refund is compensation, not rollback of the capture.

### 2. Find the authoritative boundary

Ask:

> At what point would it become dishonest to behave as if this operation never happened?

Examples include:

- third party confirmed capture;
- durable commit accepted;
- user decision accepted;
- unique job finalized;
- destructive cutover completed.

The UI acknowledgement or network response may occur before or after this point. Do not assume they coincide.

### 3. Define pre-boundary recovery

Before authoritative commit, recovery may often:

- retry the full operation;
- discard tentative state;
- restart from a clean boundary;
- ask the user again;
- abort safely.

Only choose these if no earlier irreversible effect already occurred.

### 4. Define post-boundary recovery

After authoritative commit, do not replay earlier accepted work merely because a later step failed.

Recovery may instead:

- resume remaining continuation steps;
- reconcile from authoritative state;
- repeat only retry-safe post-commit work under the required identity/preconditions;
- deliver a previously committed result again;
- compensate explicitly;
- escalate for manual repair.

### 5. Separate lost response from failed operation

A caller not receiving a response does not prove the operation failed.

Model at least these possibilities when relevant:

```text
request never accepted
request accepted but effect failed
irreversible effect succeeded but response was lost
response succeeded but caller state was stale
```

Retry semantics must distinguish them or use an idempotency mechanism that makes the distinction safe.

### 6. Protect continuation ownership

If post-boundary work can fail, define what state is needed to continue without replaying the irreversible part.

Keep this state no broader than necessary. Do not duplicate the entire workflow just to recover one continuation step.

### 7. Test both sides of the boundary

At minimum, test or reason explicitly about:

- failure immediately before commit;
- failure immediately after commit;
- lost acknowledgement/response;
- repeated retry;
- concurrent duplicate attempt where relevant.

## Decision rules

- Recovery semantics change when truth changes.
- Rollback of local state does not erase an already-visible external effect.
- A retry must not silently become a second intent.
- Compensation is a new action, not time travel.
- Reversibility, compensation, and retry repeatability must be reasoned about separately.
- Post-commit failure is often a continuation problem, not a reason to replay the original command.
- If the system cannot tell whether an irreversible effect occurred, design an identity/reconciliation strategy before relying on retries.

## Anti-patterns

Avoid:

- replaying payment/send/delete because the success screen failed;
- marking success before the system's real commit boundary;
- assuming HTTP timeout means no side effect;
- using database rollback language for effects outside that transaction;
- treating compensation as proof that the original effect was reversible;
- retrying with a new identity when the old operation may have succeeded;
- compensating silently while claiming the original effect never occurred.

## Verification checklist

- [ ] Irreversible effects are identified explicitly.
- [ ] Each relevant effect has independent reversibility, compensation, and repeatability/retry classifications.
- [ ] The authoritative commit boundary is explicit.
- [ ] Pre- and post-boundary recovery differ where truth differs.
- [ ] Lost response is distinguished from failed operation.
- [ ] Duplicate/retry behavior is safe or explicitly blocked.
- [ ] Compensation is modeled as a separate action, not rollback.
- [ ] Post-commit recovery does not replay already-authoritative work.

## Pair with

- `authority-mapping` to identify who accepts the authoritative transition;
- `systematic-debugging` for failures around the boundary;
- `exact-state-verification` for committed revision identity;
- solution patterns such as idempotency, outbox, continuation cursors, or compensation when a project chooses them.
