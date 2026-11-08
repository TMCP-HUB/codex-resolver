# Read-Only Observer Facade

> Classification: **Solution Pattern — optional**. This is one way to expose diagnostics or inspection without creating a second mutation/control plane. It is unnecessary when existing APIs already provide the safe observation surface you need.

## Problem class

Operators, developers, users, or diagnostic UI need to inspect selected runtime/domain state, but exposing live internal objects or service references would allow accidental mutation, future/private-state leakage, or hidden coupling.

## Production trace

This pattern came from a runtime that needed a utility/diagnostic surface for already-reached state and previously published events while explicitly forbidding command access, future content, raw session internals, and replay of domain logic.

## Assumptions

- some state is safe/useful to observe;
- observation should not mutate authoritative state;
- the underlying runtime contains more capability/data than should be exposed;
- snapshot freshness can be defined explicitly.

## Use when

Use when:

- adding a developer/operations inspector to a stateful app;
- user-facing diagnostics should expose only allowlisted current/reached facts;
- plugins/extensions need read-only snapshots but not service references;
- tests need stable observation seams without reaching into private internals;
- a diagnostic playback should use recorded/published facts rather than re-executing domain behavior.

## Do not use when

Prefer another design when:

- the consumer genuinely requires command/control capability;
- a standard authenticated API already provides the correct projection;
- copying snapshots is too expensive and a query service is more appropriate;
- the system requires streaming subscriptions with explicit consistency semantics;
- hiding fields in an in-process facade would create a false security boundary against untrusted code.

## Pattern

### 1. Define an allowlisted observer contract

Expose explicit methods such as:

```text
getStateSnapshot()
getHealthProjection()
getDecisionSummary()
```

Return only the values required by the observer use case.

### 2. Return detached values

Prefer copied/serialized DTOs rather than live references.

```text
runtime internals
→ allowlist/project
→ detach/copy
→ observer DTO
```

Mutating the DTO must not mutate authoritative state.

### 3. Exclude control capabilities

Do not expose through the facade:

- mutation methods;
- service/container references;
- network clients;
- persistence handles;
- raw authentication/session material;
- arbitrary internal object graphs.

If a command is needed, give it a separate explicit command interface with its own authority rules.

### 4. Bound information by reach/authorization

A read-only interface can still leak future/private information.

Define whether each field is:

- current only;
- already reached/published only;
- operator-only;
- safe public state;
- unavailable/withheld.

Read-only does not mean safe-to-expose.

### 5. Avoid domain re-execution for diagnostics

If the observer shows history/playback, source it from already committed/published records or projections.

Do not rerun domain transitions merely to reconstruct a diagnostic view unless re-execution is explicitly safe and intended.

### 6. Define lifecycle/revocation

When the underlying runtime/session loses authority, the observer should stop presenting stale capabilities as live state.

Options include:

- facade becomes unavailable;
- snapshots become explicitly historical;
- subscription is closed;
- references are detached during teardown.

### 7. State freshness semantics

Document whether snapshots are:

- point-in-time;
- eventually consistent;
- cached;
- recomputed on every query;
- tied to a revision.

## Why it works

The facade reduces the authority surface to a deliberate projection. Detached values eliminate accidental mutation through object references, and an allowlist makes future/private data exposure reviewable.

## Trade-offs

- projection code must be maintained as state evolves;
- snapshot copies may cost memory/CPU;
- diagnostics can become stale if freshness is unclear;
- an in-process facade is not a security sandbox against hostile code;
- observers may ask for more fields over time and gradually recreate the internal model.

## Alternatives

Consider instead:

- authenticated read-only API/query service;
- OpenTelemetry/logging/metrics for operational diagnostics;
- debug build with direct internal access;
- event stream/read model designed for observers;
- database/admin tools outside the product runtime;
- capability-secured command/query interfaces when observers also need actions.

## Failure modes

- facade returns live mutable objects;
- hidden mutation method slips into an ostensibly read-only interface;
- future/private data is exposed because "read-only" was treated as sufficient protection;
- diagnostics re-execute domain logic and create side effects;
- snapshot mutation changes runtime state;
- observer survives teardown and keeps stale authority references;
- facade grows into an undocumented second application API.

## Verification

- mutate returned snapshot and prove authoritative state does not change;
- representative forbidden fields/methods are absent, not merely unused by UI;
- observer operations create zero domain mutations for read-only use cases;
- unreached/unauthorized state is unavailable according to contract;
- diagnostic playback/query does not execute domain commands;
- teardown/revocation ends live observation authority as specified;
- freshness/revision semantics are testable or clearly documented.

## Related Core Principles

- `authority-mapping` — observation, presentation, and command authority remain distinct;
- `evidence-and-authority` — observer output proves only what the projection actually contains;
- `exact-state-verification` — snapshots may need revision identity;
- `stable-semantic-identifiers` — optional pattern for durable observer references.
