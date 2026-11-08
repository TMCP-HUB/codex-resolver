# Server-Authoritative Event Journal

> Classification: **Solution Pattern — optional**. This is one proven architecture for event capture when accepted server-side facts matter more than browser-observed behavior. It is not the right telemetry model for every product.

## Problem class

A system needs an ordered event trace of authoritative actions, including retries and temporary analytics/storage outages, without letting observability failure break the primary workflow or letting client observations masquerade as accepted facts.

## Production trace

This pattern came from a long-lived interactive protocol where queued intent was deliberately **not** telemetry, accepted actions received server timestamps and monotonic sequence numbers, pending facts survived temporary storage failure, and event batches had to remain idempotent across lost responses and release changes.

## Assumptions

- the server/service boundary sees the events that matter;
- accepted facts are more important than pre-acceptance client intent;
- temporary telemetry storage failure must not invalidate the primary domain action;
- a bounded pending journal can fit in available durable or semi-durable state;
- gaps/degradation can be reported honestly rather than fabricated away.

## Use when

Use when:

- audit/protocol traces need server-accepted ordering;
- retries must not duplicate persisted events;
- temporary analytics storage outages are expected;
- the primary workflow must be fail-open relative to observability;
- client clocks/identities are untrusted or irrelevant;
- exact per-session/protocol sequencing matters.

## Do not use when

Prefer another design when:

- the goal is product analytics about impressions, clicks, dwell, scroll, or other browser-observed behavior;
- OpenTelemetry traces/metrics already model the needed operational signals;
- high-volume event streaming needs Kafka/Kinesis/PubSub or similar infrastructure;
- compliance requires synchronous durable audit logging before business commit;
- events originate legitimately from many independent clients and the server cannot authoritatively observe them;
- a simple database audit table is sufficient.

## Pattern

### 1. Define the event ontology at the acceptance boundary

Only create a canonical event when the system has accepted the corresponding fact.

Distinguish as needed:

```text
intent
!= accepted action
!= committed state
!= delivery/presentation evidence
```

The exact distinctions depend on the product.

### 2. Mint protocol/trace identity server-side

Use an opaque trace/protocol/session identifier if one ordered run needs grouping.

Do not expose it to the client unless the product actually needs to.

### 3. Assign monotonic event sequence

For each accepted occurrence:

```text
seq = next_event_seq
occurred_at = authoritative clock
append event
next_event_seq++
```

This gives ordering independent from transport batch boundaries.

### 4. Keep a bounded pending journal

If the analytics sink is unavailable, retain a bounded ordered set of accepted events in state that survives the expected outage window.

Measure the real size limit. Do not let the pending journal grow without bound.

### 5. Persist immutable idempotent batches

A batch can use an identity such as:

```text
(trace_id, batch_seq)
```

and store:

- first/last event sequence;
- immutable event envelope;
- hash/digest when useful;
- persistence time;
- relevant immutable release/provenance.

A retry with the same batch identity should either match exactly or be rejected/deferred as a conflict.

### 6. Degrade honestly when capacity is exceeded

When pending capacity cannot retain every event:

- preserve the primary workflow;
- record an explicit bounded degradation/gap state;
- never fabricate missing events later;
- resume capture according to a declared rule after recovery.

### 7. Preserve provenance across lifecycle changes when required

If a pending journal belongs to release/config/session A and the live session becomes B, do not silently relabel old events as B.

Either flush, retain explicit provenance, or start a new compatible journal according to the product's contract.

## Why it works

- canonical events are created where the system actually accepts facts;
- monotonic sequence preserves causal ordering across batching;
- idempotent immutable batches make lost-response retries safe;
- bounded degradation prevents telemetry from becoming a failure dependency of the product;
- explicit gaps preserve honesty.

## Trade-offs

- server-only traces miss purely client-observed UX signals;
- bounded pending state adds complexity and size pressure;
- exact sequencing may reduce batching flexibility;
- fail-open telemetry can produce incomplete traces by design;
- schema evolution and provenance need careful ownership;
- high-volume systems may outgrow this pattern.

## Alternatives

Consider instead:

- browser analytics platforms for behavioral analytics;
- OpenTelemetry for operational traces/metrics;
- append-only database audit log;
- durable queue/event stream + consumers;
- transactional outbox from the primary database;
- client event batches with server validation;
- synchronous compliance audit logging when dropping events is unacceptable.

## Failure modes

- queued/unaccepted intent is recorded as if accepted;
- client timestamps are treated as authoritative without need;
- analytics sink failure rolls back valid domain actions;
- pending journal grows until session/header/storage failure;
- retry creates duplicate batches;
- missing events are reconstructed by replaying domain logic;
- old pending events are relabeled with a newer release/config identity;
- analytics IDs become user identity without a real requirement.

## Verification

- accepted events receive strictly ordered sequence numbers;
- unaccepted/queued intent does not enter the canonical journal when that is the contract;
- lost batch response retries idempotently;
- conflicting duplicate batch is detected;
- sink outage does not break valid primary actions;
- bounded capacity enters explicit degradation before storage/transport overflow;
- recovery flushes retained events in order and does not fabricate gaps;
- provenance survives lifecycle/release changes according to the declared rule.

## Related Core Principles

- `authority-mapping` — decide which boundary may create canonical events;
- `irreversible-boundary-reasoning` — telemetry retry must not replay domain actions;
- `exact-state-verification` — release/config provenance may be part of event identity;
- `evidence-and-authority` — observability proves recorded events, not unobservable user intent or comprehension.
