# Plan, Revalidate, Apply Fence

> Classification: **Solution Pattern — optional**. This is one proven way to perform consequential mutations when current authoritative state must be inspected before applying changes. It is not required for trivial or fully transactional operations.

## Problem class

A production mutation is consequential and depends on current state. A dry-run plan can become stale between observation and apply, and command exit success is weaker than proof that the intended postcondition was reached.

## Production trace

This pattern came from operator migration/cutover work where a deterministic plan was generated from live state, mutation required explicit apply, and completion was accepted only after authoritative re-read showed the planner converged to the intended postcondition. The same class of work also exposed a TOCTOU risk if apply trusted an old plan without revalidation.

## Assumptions

- current authoritative state can be read before mutation;
- intended changes can be represented as a bounded plan or change set;
- apply has a meaningful review/commit boundary;
- stale state could make an earlier plan unsafe or wrong;
- authoritative state can be re-read after apply.

## Use when

Use when:

- bulk migrations or reconciliation modify production data;
- destructive cleanup or permission changes need explicit review;
- cutovers depend on current inventory or conflicts;
- imports/adoptions must preserve stronger target state;
- operator tooling needs a safe default and observable postcondition.

## Do not use when

Prefer another design when:

- the operation is trivial and easily reversible;
- one ordinary transaction with version/conflict checks already provides the complete boundary;
- state changes so rapidly that human-readable plans are immediately obsolete and a reconciler/lock is more appropriate;
- a declarative controller already owns continuous convergence;
- the plan cannot express the real semantic mutation faithfully.

## Pattern

### 1. Observe authoritative state

Read the exact target state required to decide what should change. Record target/environment identity where confusion is possible.

### 2. Build a deterministic plan

Produce an explicit representation of:

- intended writes/removals;
- preserved state;
- conflicts/ambiguities;
- expected postcondition;
- any preconditions/version markers needed for safe apply.

Dry-run should be side-effect free within the declared scope.

### 3. Review and authorize apply

Make mutation an explicit operation. Do not let inspection silently mutate state.

### 4. Revalidate before commit

Immediately before applying a consequential plan, verify that the authoritative assumptions/preconditions still hold.

Depending on architecture this may use:

- revision/version compare;
- conditional write;
- lock/lease;
- transaction;
- fresh recomputation and equality check;
- explicit conflict detection.

The pattern does not prescribe which mechanism to use.

### 5. Apply only the validated plan

Do not recompute materially different semantics inside apply without surfacing the new plan/conflict.

If preconditions fail, stop and re-plan rather than applying a stale change set.

### 6. Re-observe authoritative state

After mutation, read the actual target state again.

### 7. Assert the postcondition

Define success by resulting authoritative state, not process exit alone.

Where the planner is convergent, a useful proof is:

```text
re-plan after apply
→ zero pending writes / expected no-op
```

Use only when "zero pending" actually captures the intended postcondition.

## Why it works

It separates knowledge acquisition, authorization, mutation, and verification. Revalidation closes the most obvious stale-plan gap, while postcondition proof prevents a successful command from being mistaken for a successful state transition.

## Trade-offs

- extra reads and tooling;
- TOCTOU still exists unless revalidation/commit is strong enough for the environment;
- large plans can be difficult to review;
- may require conditional writes, locking, or transactions;
- postconditions can be falsely reassuring if specified too weakly.

## Alternatives

Consider instead:

- one transactional admin operation;
- declarative reconciler/controller;
- reviewed change-set artifact applied by infrastructure tooling;
- blue/green cutover;
- offline export/transform/import;
- vendor migration tooling;
- manual operator procedure for rare low-scale changes.

## Failure modes

- dry-run and apply use different planning semantics;
- apply trusts a stale plan without revalidation;
- revalidation checks the wrong version/scope;
- partial mutation succeeds but postcondition ignores missing work;
- command exit zero is treated as proof of convergence;
- "zero pending" hides unintended extra changes;
- apply automatically resolves conflicts that the plan reported as ambiguous;
- dry-run has hidden side effects.

## Verification

- identical authoritative state produces an equivalent plan;
- conflict/precondition change between plan and apply prevents stale mutation;
- dry-run leaves declared target state unchanged;
- explicit apply performs only planned authorized changes;
- partial/failing apply is visible and does not receive a false PASS;
- post-apply authoritative re-read is performed;
- postcondition or convergent second plan proves intended completion;
- rollback/backup expectations are verified separately when required.

## Related Core Principles

- `irreversible-boundary-reasoning` — identifies the consequential commit boundary;
- `exact-state-verification` — binds plan/revalidation/postcondition to exact target state;
- `evidence-and-authority` — separates plan evidence, apply authority, and completion claim;
- `authority-mapping` — identifies the target state owner and valid conflict rule.
