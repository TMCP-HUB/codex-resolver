# Resource Accounting Protocol

This protocol freezes provider-neutral accounting semantics for Resource Governance. It does not select a persistence backend, transaction technology, forecasting algorithm, provider adapter, or execution platform.

## Canonical key

A governed quantity is keyed by:

```text
(resource_class, dimension)
```

`resource_class` and `dimension` are extensible provider-neutral identifier namespaces using uppercase snake-case. The baseline shared identifiers below define common meanings but are not closed enums.

Baseline resource classes:

```text
MODEL_INFERENCE
REMOTE_CI
REMOTE_BROWSER
GPU_COMPUTE
PAID_TOOL
EXTERNAL_API
```

Baseline dimensions:

```text
USD
RUNNER_MINUTES
GPU_SECONDS
TOKENS
MODEL_CALLS
TOOL_CALLS
AGENT_SPAWNS
```

A new class/dimension may be introduced without changing this protocol when it represents a genuinely new provider-neutral resource kind/unit, preserves existing identifier meanings, and does not alter governance semantics. Provider/product identity belongs in route/provenance/measurement references rather than in the canonical key.

A class may use multiple dimensions. Different dimensions are never summed as one unit.

Where one artifact expresses authoritative limits or aggregate totals, duplicate `(resource_class, dimension)` entries that create competing quantities are invalid.

## Limit modes

### HARD_LIMIT

Finite ceiling. Admission/consumption MUST NOT knowingly exceed it.

Reservation is not required by the semantic definition.

### RESERVABLE_LIMIT

Finite shared ceiling. Competing governed work MUST reserve capacity before consumption.

### OBSERVATION_ONLY

Telemetry/accounting only. It does not grant spend authority and does not independently block admission.

Observation-only is not unlimited authority.

Unknown/unavailable observation-only telemetry remains non-blocking. An observation-only evaluation may carry `METERING_UNAVAILABLE`, `ACTUAL_UNKNOWN`, or another observation-specific unknown without converting that telemetry gap into a blocking resource requirement. Top-level resource-admission unknown state describes unresolved blocking resource state, not mere telemetry quality.

## Grant capacity

For a blocking finite dimension:

```text
AUTHORIZED_TOTAL
=
ordinary_limit
+
finalization_reserve
```

Normal work uses `ordinary_limit`.

Protected finalization capacity is usable only for purposes authorized by the grant.

Parent-child narrowing MUST compare these capacities separately:

```text
CHILD_ORDINARY_LIMIT <= PARENT_ORDINARY_LIMIT
CHILD_FINALIZATION_RESERVE <= PARENT_FINALIZATION_RESERVE
```

A total-only comparison is invalid because it permits protected finalization capacity to be reclassified as ordinary capacity.

## Reservation / commit / release

For `RESERVABLE_LIMIT`:

```text
AVAILABLE
→ RESERVED
→ COMMITTED
```

or:

```text
AVAILABLE
→ RESERVED
→ RELEASED
```

Accounting balance and usable capacity:

```text
BALANCE
=
LIMIT
- COMMITTED
- RESERVED

AVAILABLE = max(0, BALANCE)
DEFICIT   = max(0, -BALANCE)
```

`RESERVED != SPENT`.

Commit records the actual reported quantity against the reservation and its
ancestor allocations, even when that quantity exceeds the original reservation.
The original reserved quantity remains visible; the excess is an observation,
not additional Owner authority. If an actual arrives after release or expiry,
the terminal reservation status is retained while the observed quantity is
accounted. A supplied measurement-source reference is retained as supplied;
the reference alone does not establish an authoritative provider bill.

New reservations remain subject to each pool's original limit and to the
combined ordinary plus protected total. If a recorded overrun creates a
negative balance, its deficit remains visible and usable capacity is zero;
already-issued reservations are not erased.

Release returns unused reserved capacity.

Retries of the same reservation/idempotency identity require idempotent semantics. One logical operation may contain distinct real costs; its operation ID alone does not prove a duplicate payment. This protocol does not prescribe storage, locking, or transaction mechanics.

The existing `ResourceLedger` reference implementation can record a reported
actual that has **no reservation** with `record_unreserved_usage`. Use the
same observation ID for a retry and the current revision for a correction;
`withdraw_unreserved_usage` removes an explicitly erroneous or duplicate
accounting record from totals while retaining its history and the stated
reason. Use the existing `commit` path for actuals associated with a
reservation. The caller establishes whether two records describe the same
fact; a shared operation or measurement source alone does not establish it.
These calls record supplied facts, not spend authority, provider billing, or
an automatic provider event producer. An operation ID is optional for this
ledger observation; the separate canonical `USAGE_EVENT` schema retains its
own required fields and allowed states.

When an actual is unknown, the ledger keeps its quantity null and identifies
any older amount separately as last known. Unknown finite availability remains
unknown. Observation-only telemetry remains non-blocking; where its unknown
does not block, a numerical availability based on known records is marked
`KNOWN_RECORDED_ONLY` and is not proof of the provider's complete balance.

## HARD_LIMIT behavior

A blocking hard limit compares required quantity with current availability before governed execution when the quantity is needed for admission.

Unknown blocking availability is not proof of availability.

A later runtime may use reservations for stronger concurrency control, but reservation is not part of the `HARD_LIMIT` semantic definition.

## OBSERVATION_ONLY behavior

Observation-only dimensions may produce usage/accounting telemetry.

They do not create resource authority.

They MUST NOT independently produce a blocking `NOT_ADMISSIBLE` evaluation. Missing telemetry is represented as an observation-specific unknown while the evaluation remains non-blocking.

## Parent-child authority

```text
CHILD_RESOURCE_AUTHORITY
⊆
PARENT_RESOURCE_AUTHORITY
```

Children may consume only authority already present in their parent chain.

For a shared finite dimension, downstream enforcement must prevent new child reservations from exceeding parent capacity. A previously incurred actual overrun may make committed plus already reserved quantities exceed that capacity; it is recorded rather than converted into additional authority.

A child may strengthen enforcement. It may not relax parent enforcement or broaden parent scope.

Scope narrowing is a semantic cross-artifact proof:

```text
CHILD_SCOPE ⊆ PARENT_SCOPE
```

Equal `scope_ref` is sufficient. Different scope refs require a governed scope relation that proves the subset. If the validator cannot establish that relation, narrowing fails closed. A different string alone never proves a narrower scope.

Observation-only parent authority cannot become child spend authority.

## Attempts

Attempt count is independent finite authority.

If both parent and child are attempt-bounded, the child limit MUST NOT exceed the parent limit.

Resource availability does not create extra attempt authority.

## Finalization reserve

Protected purposes may include:

```text
RESULT_RECONCILIATION
DURABLE_PARTIAL_OUTPUT
FINAL_ACCOUNTING
CONTROL_HANDOFF
```

When ordinary capacity is depleted but protected finalization capacity remains:

```text
ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY
```

New ordinary work is prohibited.

When protected capacity is also depleted:

```text
EXHAUSTED
```

Finalization capacity MUST NOT be silently repurposed for normal work, including through a child grant that increases ordinary capacity while reducing the protected reserve.

## Metering quality

```text
AUTHORITATIVE_ACTUAL
NORMALIZED_ACTUAL
ESTIMATED
UNKNOWN
```

`AUTHORITATIVE_ACTUAL`: actual usage from the governing measurement source. This quality requires a non-empty `measurement_source_ref` naming that source.

`NORMALIZED_ACTUAL`: actual usage transformed into canonical fields without changing factual meaning.

`ESTIMATED`: defensible estimate, not actual usage.

`UNKNOWN`: no defensible quantity.

```text
UNKNOWN != ZERO
```

Unknown canonical quantity is null, never numeric zero.

## Unknown-resource state

```text
KNOWN
ESTIMATE_UNKNOWN
ACTUAL_UNKNOWN
AVAILABILITY_UNKNOWN
METERING_UNAVAILABLE
```

A required blocking unknown fails closed at resource admission.

An observation-only telemetry unknown does not independently block admission.

## RESOURCE_ESTIMATE accounting

The estimate is route-bound.

Per resource class/dimension it may carry:

- point estimate;
- generic quantiles `(probability, quantity)`;
- upper bound;
- confidence;
- historical sample count;
- explicit unknown state.

No statistical algorithm is prescribed.

Historical sample count is evidence context, not authority.

## USAGE_EVENT accounting

One event represents exactly one resource class + dimension for one logical operation.

A multi-dimensional operation may emit multiple events.

Canonical fields include run/operation identity, optional agent hierarchy, quantity or explicit unknown, metering quality, measurement-source reference, interpretation revision reference, and bounded start/finish observations where available.

`AUTHORITATIVE_ACTUAL` without a non-empty `measurement_source_ref` is invalid because the claimed governing measurement source is not identified.

Provider-specific payload fields remain outside the core schema.

## RUN_ACCOUNTING aggregation

Run accounting aggregates one run while preserving units.

It distinguishes:

```text
resource estimate != actual/observed totals
wall time != aggregate machine/agent active time
```

Parallelism may make aggregate machine/agent time greater than wall time.

Estimate-error fields are calibration evidence only; they do not rewrite the original estimate or actual usage.

## Exhaustion state

```text
NOT_EXHAUSTED
ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY
EXHAUSTED
UNKNOWN
```

`UNKNOWN` means exhaustion cannot be established from trustworthy availability/accounting evidence.

## Interpretation revisions

When a quantity materially depends on a rate, quota, or equivalent interpretation source, accounting preserves a durable revision/source reference.

Historical records are not silently reinterpreted when later definitions change.

This protocol does not define the interpretation source.

## Failure behavior

Unauthorized, exhausted, unavailable, or unknown blocking resources stop or prevent the affected governed work according to Control state.

Insufficient resource authority MUST NOT become weaker evidence, an undeclared route, or a hidden retry.

Implementation friction is not a contract defect. A genuine frozen-interface defect returns `CONTRACT_GAP_FOUND` to Control and stops the affected downstream workstream pending explicit bounded contract amendment.
