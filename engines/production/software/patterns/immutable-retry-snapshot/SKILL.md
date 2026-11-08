# Immutable Retry Snapshot

> Classification: **Solution Pattern — optional**. This is one proven way to retry an uncertain mutation without accidentally creating a new semantic operation. Use it only when its assumptions match; it is not a universal retry architecture.

## Problem class

A mutation may have committed even though the caller receives a timeout, disconnect, or lost acknowledgement. Rebuilding the request from current UI state can change semantic fields and turn one user intent into a second or conflicting operation.

## Production trace

This pattern came from a production submission flow where the logical operation needed a stable identity and stable normalized business payload across an uncertain retry, while a short-lived anti-abuse proof could legitimately be refreshed. Treating the whole request as disposable would have broken idempotency semantics.

## Assumptions

- the operation has a stable semantic identity for the retry window;
- the authoritative boundary supports idempotency, operation identity, or equivalent reconciliation;
- uncertain outcome is possible;
- the semantic payload can be normalized once and retained temporarily;
- any refreshable ephemeral fields can be clearly separated from semantic operation identity.

## Use when

Use when:

- orders, payments, submissions, provisioning, or other duplicate-sensitive mutations may lose acknowledgement;
- retry must mean "continue the same intent" rather than "submit whatever the form contains now";
- idempotency keys are meaningful only when paired with the same semantic payload;
- ephemeral security/transport proof can expire independently of the business operation.

## Do not use when

Prefer another design when:

- every retry is intentionally a new operation;
- the server cannot reconcile stable operation identity;
- the semantic payload is expected to change on retry;
- a durable workflow engine already owns command identity and payload versioning;
- the operation is inherently idempotent and whole-command replay is simpler.

## Pattern

### 1. Create stable operation identity

Generate or receive an opaque operation/idempotency identity that does not expose sensitive business data.

### 2. Normalize semantic payload once

Convert the user's accepted intent into the canonical request representation once for the retry window.

Examples may include normalized amounts, selected resources, consent state, destination, or other business facts.

### 3. Freeze the semantic snapshot

Persist or retain enough state so an uncertain retry sends the **same semantic operation**.

Do not regenerate timestamps, defaults, derived fields, or consent/tracking values if those fields are part of authoritative meaning.

### 4. Separate ephemeral proof

Classify fields such as anti-abuse tokens, short-lived transport credentials, or challenge proofs separately only when the authoritative contract says they are not part of business identity.

A retry may refresh those fields without changing the semantic snapshot.

### 5. Distinguish definite rejection from uncertain outcome

```text
definite pre-commit validation/rejection
→ discard or rebuild according to policy

uncertain timeout/lost acknowledgement
→ same operation identity + same semantic snapshot
```

Use `irreversible-boundary-reasoning` to classify the boundary.

### 6. Reject key/payload mismatch

If the same operation identity arrives with a different semantic payload, treat it as a conflict or explicit new operation—not a silent update.

### 7. Expire snapshots intentionally

A retry snapshot is not an indefinite hidden draft. Define the retry window, user-visible restart semantics, and cleanup.

## Why it works

It makes retry identity correspond to one user/domain intent instead of one network attempt. A lost acknowledgement no longer gives the client permission to reconstruct a similar but different command.

## Trade-offs

- extra temporary state;
- normalization rules become part of operation identity;
- UI must distinguish uncertain outcome from definite failure;
- edits made after an uncertain send may require an explicit "start new operation" action;
- snapshot retention/cleanup needs a policy.

## Alternatives

Consider instead:

- server-issued durable operation handle;
- durable workflow/orchestration engine;
- naturally idempotent command;
- transactional queue/outbox where it owns the whole operation;
- manual reconciliation for rare high-risk operations.

## Failure modes

- reusing the same key with changed semantic payload;
- generating a new key after timeout and duplicating a committed operation;
- treating timeout as definite failure;
- deriving operation identity from PII or mutable data;
- including single-use transport proof in the semantic identity without need;
- regenerating semantic timestamps/defaults on retry;
- retaining snapshots indefinitely.

## Verification

- same identity + same semantic snapshot after lost response produces one accepted operation;
- same identity + changed semantic payload is rejected or explicitly reconciled;
- refreshable ephemeral proof does not change canonical operation identity;
- forced failure before commit can rebuild only when policy allows;
- forced failure after commit retries the same operation rather than duplicating it;
- concurrent duplicate retries remain one semantic operation;
- snapshot expiry creates an explicit new-operation boundary.

## Related Core Principles

- `irreversible-boundary-reasoning` — classifies definite vs uncertain pre/post-commit outcomes;
- `authority-mapping` — identifies the authoritative mutation owner;
- `exact-state-verification` — binds retry snapshot/contract evidence to the current state;
- `async-lifetime-ownership` — identifies who owns the mutation after initiation/acknowledgement loss.
