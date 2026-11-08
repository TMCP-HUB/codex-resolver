# Async Lifetime Ownership

## Purpose

Use this skill when a request, command, job, UI action, or workflow starts asynchronous side effects whose completion may outlive the initiating call or user-visible response.

## Goal

Make every meaningful asynchronous side effect have an explicit lifetime, acknowledgement, loss, retry, and failure owner so critical work cannot accidentally become best-effort merely because the programming model makes it easy to launch and forget.

This skill is architecture-neutral. It does **not** require a specific queue, runtime, workflow engine, Promise API, thread model, or provider.

## When to use

Use when:

- code starts asynchronous work without directly awaiting/returning it;
- a response can complete before a side effect finishes;
- work may be delegated to a queue, scheduler, worker, runtime continuation, callback, or provider;
- telemetry/notification and canonical writes coexist but have different loss semantics;
- process/request cancellation may interrupt outstanding work;
- "fire and forget" appears in design or review.

## Do not use when

Do not use this skill to:

- require every operation to block the user until all background work finishes;
- ban best-effort work whose loss is explicitly acceptable;
- replace `irreversible-boundary-reasoning` for retry after an authoritative commit;
- replace a workflow engine's own durable lifetime model when it already supplies the required guarantees.

## Inputs

- initiating action/request/job;
- every asynchronous side effect it starts;
- which effects affect correctness or authority;
- runtime/process/request lifetime guarantees;
- retry/idempotency behavior;
- observability and failure handling;
- accepted loss/degradation policy.

## Required outputs

Produce an async-lifetime table:

| Side effect | Correctness class | Lifetime owner | Completion/ack boundary | Loss allowed? | Retry/reconcile owner | Failure visibility |
|---|---|---|---|---|---|---|

Classify each effect at minimum as one of:

- **required for authoritative success**;
- **required continuation after authoritative success**;
- **best-effort / degradable**;
- **purely observational**.

Projects may use different names, but the loss semantics must remain explicit.

## Procedure

### 1. Inventory async side effects

Look beyond obvious network calls. Include where relevant:

- persistence writes;
- session/credential changes;
- authorization/consent state;
- emails/messages/webhooks;
- object writes;
- cache invalidation;
- analytics/telemetry;
- cleanup/release;
- durable job publication;
- UI/background continuations.

### 2. Classify correctness dependence

Ask for each effect:

```text
If this never runs, is the operation still truthful/correct?
If it runs twice, is that safe?
If the caller never learns its result, who owns reconciliation?
```

Do not group canonical writes and best-effort telemetry merely because both are asynchronous.

### 3. Name the lifetime owner

A lifetime owner is the component/process/protocol that guarantees the work remains eligible to finish after initiation.

Examples may include:

- current request because it awaits/returns the operation;
- a durable queue after successful enqueue acknowledgement;
- a workflow engine after durable step registration;
- a platform-supported post-response continuation;
- intentionally nobody, only when loss is explicitly acceptable.

Do not infer lifetime from syntax. Launching a task does not prove the runtime will keep it alive.

### 4. Define the acknowledgement boundary

For required work, distinguish:

```text
scheduled
!=
enqueued durably
!=
accepted by provider
!=
committed authoritatively
!=
fully completed
```

The user-visible success claim must match the strongest boundary actually required by the product contract.

### 5. Define loss and process-death behavior

Record what happens if:

- request ends;
- process crashes;
- tab/page closes;
- runtime cancels background work;
- queue/provider is unavailable;
- acknowledgement is lost.

If correctness depends on completion, a best-effort lifetime is insufficient unless another durable owner has already accepted responsibility.

### 6. Define retry/reconciliation ownership

For effects that may have committed before acknowledgement, use `irreversible-boundary-reasoning` and an appropriate retry/recovery pattern.

For best-effort effects, decide whether silent loss, bounded retry, or explicit gap accounting is acceptable.

### 7. Keep failure visibility proportional to semantics

A best-effort metric can fail without failing the product, but the design may still need observable gaps/errors.

A canonical write/authentication exchange/session revocation/authorization mutation should not be silently abandoned merely because a detached async task failed.

### 8. Verify runtime assumptions

Read the actual runtime/platform contract when lifetime behavior matters. Do not assume all environments keep detached work alive after response/process completion.

Bind evidence to the exact environment with `exact-state-verification` when appropriate.

## Decision rules

- Async syntax does not define durability.
- Every correctness-relevant side effect needs a lifetime owner through the boundary its contract requires.
- Best-effort is a semantic classification, not a convenient implementation escape hatch.
- User-visible success must not imply stronger completion than the owned lifetime can guarantee.
- Post-commit continuation and pre-commit required work are different classes.
- If no component owns retry/reconciliation after uncertain completion, the failure model is incomplete.

## Anti-patterns

Avoid:

- untracked "fire and forget" for canonical state;
- assuming process/request lifetime from local development behavior;
- returning success before a required durable owner accepted the work;
- swallowing detached-task failures that affect correctness;
- treating telemetry loss and payment/session/auth loss as equivalent;
- retrying an uncertain non-repeatable effect without reconciliation;
- creating a queue but failing to define what successful enqueue means.

## Verification checklist

- [ ] All meaningful async side effects are inventoried.
- [ ] Correctness/loss class is explicit for each.
- [ ] Lifetime owner exists through the required boundary.
- [ ] Acknowledgement semantics are explicit.
- [ ] Process/request cancellation behavior is known.
- [ ] Retry/reconciliation ownership is explicit where needed.
- [ ] Best-effort work cannot silently become authority.
- [ ] Success/failure reporting matches the actual guarantee.

## Pair with

- `irreversible-boundary-reasoning` for pre/post-commit retry and uncertain outcomes;
- `post-commit-recovery-cursor` when committed work needs bounded continuation;
- `authority-mapping` for canonical vs secondary effects;
- `evidence-and-authority` for truthful completion claims;
- `provider-late-binding` for external provider lifetimes and certification.
