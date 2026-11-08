# Resource Governance Contract

This contract freezes the provider-neutral Resource Governance interface for Project Resolver. It defines semantics only. It does not implement forecasting, persistence, runtime adapters, CI, or Resolver behavior.

## Core separation

```text
SEMANTIC AUTHORITY
!= EXECUTABILITY
!= RESOURCE AUTHORITY
!= RESOURCE AVAILABILITY
!= ACTUAL RESOURCE CONSUMPTION
```

```text
SPAWN_READY
=
SEMANTICALLY_COMPILED
AND EXECUTABLE
AND RESOURCE_AUTHORIZED
AND RESOURCE_AVAILABLE
```

`COMPILED_ASSIGNMENT` remains semantic compilation.

`ASSIGNMENT_ADMISSIBILITY` remains destination/runtime executability: `CAN EXECUTE`.

`RESOURCE_ADMISSION` is an orthogonal Resource Governance proof: `MAY CONSUME`.

Neither substitutes for the other.

Existing authority remains in:

- `contracts/ASSIGNMENT_COMPILATION_CONTRACT.md`
- `contracts/EXECUTABILITY_CONTRACT.md`
- `roles/control-director/ROLE.md`
- `roles/executor/ROLE.md`
- `roles/control-verifier/ROLE.md`

Cross-ownership is tracked by #56, #57, #59, #61, #62, and parent #68.

## Canonical lifecycle

```text
selected execution route
→ route-bound RESOURCE_ESTIMATE
→ finite RESOURCE_GRANT
→ RESOURCE_ADMISSION
→ governed consumption
→ USAGE_EVENT
→ RUN_ACCOUNTING
```

`ESTIMATE != AUTHORIZATION`.

A grant proves authority, not availability or consumption.

Accounting records facts; it does not create acceptance authority.

## Frozen governance vocabulary and extensible resource identifiers

`RESOURCE_CLASS` and `RESOURCE_DIMENSION` are provider-neutral identifier namespaces, not closed enums. Canonical identifiers use uppercase snake-case matching `^[A-Z][A-Z0-9_]*$`.

Baseline `RESOURCE_CLASS` identifiers are:

```text
MODEL_INFERENCE
REMOTE_CI
REMOTE_BROWSER
GPU_COMPUTE
PAID_TOOL
EXTERNAL_API
```

Baseline `RESOURCE_DIMENSION` identifiers are:

```text
USD
RUNNER_MINUTES
GPU_SECONDS
TOKENS
MODEL_CALLS
TOOL_CALLS
AGENT_SPAWNS
```

A new resource class or dimension does not require a contract amendment merely because a new governed resource is encountered. It MUST remain provider-neutral, MUST NOT redefine the meaning of an existing identifier, and MUST NOT change authority, admission, limit, metering, exhaustion, or unknown-state semantics. Provider/product identity belongs in route/provenance/measurement surfaces, not in the canonical resource identifier itself.

The following governance vocabularies are closed contract semantics.

### LIMIT_MODE

```text
HARD_LIMIT
RESERVABLE_LIMIT
OBSERVATION_ONLY
```

### METERING_QUALITY

```text
AUTHORITATIVE_ACTUAL
NORMALIZED_ACTUAL
ESTIMATED
UNKNOWN
```

### RESOURCE_ADMISSION_VERDICT

```text
ADMISSIBLE
NOT_ADMISSIBLE
```

### RESOURCE_EXHAUSTION_STATE

```text
NOT_EXHAUSTED
ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY
EXHAUSTED
UNKNOWN
```

### UNKNOWN_RESOURCE_STATE

```text
KNOWN
ESTIMATE_UNKNOWN
ACTUAL_UNKNOWN
AVAILABILITY_UNKNOWN
METERING_UNAVAILABLE
```

Changing a closed governance state/mode or its meaning requires an explicit bounded contract amendment.

## Route-bound RESOURCE_ESTIMATE

An estimate used for admission MUST bind the selected route through `route_ref`.

The same semantic obligation may have different resource consequences on different execution surfaces, so a non-route-bound estimate is not admission-grade evidence.

The estimate may carry point estimates, generic quantiles, upper bounds, confidence, historical sample count, or explicit unknown state. This contract does not prescribe the forecasting algorithm.

When an authorized total covers several classes in the same dimension, a single applicable known component already supplies its forecast. For multiple components whose estimates may overlap, `RESOURCE_ESTIMATE.shared_estimates` may carry a normalized total claimed by the responsible estimator and its stated basis, associated with the exact grant and shared limit. That actor establishes the real provenance before supplying the value: the builder and admission check the references' structure and membership, but do not resolve them or independently establish the amount. They do not automatically add potentially duplicate projections. A known forecast for an authorized superset covers its non-negative subset. An unavailable total remains unknown. A historical upper observation is a forecast, not a guarantee of an external provider bill.

## Finite RESOURCE_GRANT authority

`RESOURCE_GRANT` MUST distinguish:

```text
issued_by
authority_source
```

`issued_by` identifies the control role that materialized the grant.

`authority_source` identifies durable upstream resource authority. Supported authority-source families are Owner-approved resource authority, an autonomy envelope, a parent resource grant, or another explicit durable resource authority.

Materializing a grant does not create authority from nothing.

When `authority_source.authority_type=PARENT_RESOURCE_GRANT`, `parent_grant_ref` MUST be non-null. A non-null `parent_grant_ref` MUST identify `PARENT_RESOURCE_GRANT` as the authority-source family.

Required monotonic law:

```text
CHILD_RESOURCE_AUTHORITY
⊆
PARENT_RESOURCE_AUTHORITY
```

A child may narrow scope, resource classes, candidate/route binding, finite amount, attempt count, validity lifetime, and enforcement strictness. It MUST NOT silently broaden them.

A child scope is admissible only when the cross-artifact validator can prove:

```text
CHILD_SCOPE ⊆ PARENT_SCOPE
```

Equality is sufficient. A different `scope_ref` requires governed scope-relation evidence available to the validator. A missing or unknown scope relation fails closed. String inequality by itself is neither proof of narrowing nor proof of expansion.

Enforcement may become stricter:

```text
HARD_LIMIT → RESERVABLE_LIMIT → OBSERVATION_ONLY
```

The reverse is not automatically permitted. Observation-only authority cannot become spend authority in a child.

For finite blocking limits, ordinary capacity and protected finalization capacity are separately monotonic:

```text
CHILD_ORDINARY_LIMIT <= PARENT_ORDINARY_LIMIT
CHILD_FINALIZATION_RESERVE <= PARENT_FINALIZATION_RESERVE
```

Comparing only `ordinary_limit + finalization_reserve` is invalid because it can silently repurpose protected finalization capacity for ordinary work.

Cross-artifact narrowing is a contract law. RG-01 does not implement the runtime validator.

`CAPABILITY_AVAILABLE != RESOURCE_AUTHORIZED`.

## Multidimensional limits

A resource class may use multiple dimensions. Different dimensions MUST NOT be added as if they shared a unit.

An explicitly Owner-authorized shared total across classes is one limit, not a separate copy per class. The existing resource ledger registers that total from the Owner record and counts relevant committed and reserved allocations at each bound ancestor in the same reservation transaction, including prior history. A protected finalization reserve is inside the total; ordinary work cannot consume it, while otherwise authorized finalization can consume remaining total. Registration and reservations govern this ledger's own allocations, not external billing or unrecorded usage.

The root ledger selects one complete Owner view. Ordinary registration never
adds a second, incompatible view; equivalent boundaries in that view count
once, while genuinely different authorized groups all apply. Admission uses
the selected view, and spawn may register it when registration is the only
missing input. A direct ledger caller must also register it before expecting
shared enforcement. To correct a selected view, the responsible actor checks
the same original source, prepares the complete corrected view, then supplies
the previously read selection snapshot and source fingerprint to the ledger's
explicit replacement operation. Replacement checks both atomically and
recalculates availability from current allocations, including overruns and
previously issued reservations. A smaller corrected total can show a deficit;
it does not erase history. Shared-group correction alone does not change a
per-class grant limit. An explicitly reviewed per-class correction uses the
same selected Owner view and original grant identity; the ledger preserves
previous effective values and recalculates remaining capacity from the same
allocations. Subsequent child registration uses the effective parent limit,
and existing children remain subject to every ancestor without automatically
acquiring additional authority.

Within one authority or aggregate surface, `(resource_class, dimension)` MUST be unambiguous. Duplicate entries that create competing quantities for the same key are invalid.

### HARD_LIMIT

A finite ceiling that MUST NOT knowingly be exceeded. Reservation is not required by this mode itself.

### RESERVABLE_LIMIT

A finite ceiling whose competing consumers MUST reserve capacity before governed consumption.

### OBSERVATION_ONLY

Telemetry/accounting only. It does not grant spend authority and does not independently block admission.

`OBSERVATION_ONLY` is not infinite authority.

An observation-only evaluation may have unavailable or unknown telemetry without blocking resource admission. Its evaluation MUST remain non-blocking; `METERING_UNAVAILABLE` or another telemetry unknown does not become `UNKNOWN_REQUIRED_RESOURCE` solely because the observation cannot be measured. The top-level admission unknown state represents unresolved blocking resource state, not observation-only telemetry quality.

## Finalization reserve

A finite blocking limit may separate:

```text
ordinary_limit
finalization_reserve
```

Normal work consumes ordinary capacity only.

Protected finalization capacity may be used only for bounded purposes authorized by the grant:

```text
RESULT_RECONCILIATION
DURABLE_PARTIAL_OUTPUT
FINAL_ACCOUNTING
CONTROL_HANDOFF
```

It MUST NOT be borrowed to continue ordinary depleted work.

For an explicitly assigned finalization, the existing spawn resource input may carry `finalization_purpose`. Admission checks that purpose against every grant in the chain and reads finalization availability at both per-class and shared boundaries; the resulting admission and execution contract retain the purpose so the executor can reserve with that same purpose. Without it, admission uses ordinary availability as before. This records the assigned purpose; it does not independently prove the meaning of arbitrary task prose.

## RESOURCE_ADMISSION

Resource admission binds the exact route, estimate, grant, and current availability evidence.

`ADMISSIBLE` requires all blocking resource evaluations to be admissible, no blocking reasons, and no unknown required blocking state.

Observation-only evaluations are explicitly non-blocking and therefore may remain admissible while carrying an observation-specific unknown state such as `METERING_UNAVAILABLE`.

Canonical blocking reasons include:

```text
GRANT_MISSING
AUTHORITY_SOURCE_UNRESOLVED
GRANT_SCOPE_MISMATCH
GRANT_EXPIRED
PARENT_AUTHORITY_VIOLATION
ESTIMATE_MISSING
ESTIMATE_ROUTE_MISMATCH
ROUTE_MISMATCH
HARD_LIMIT_EXCEEDED
RESERVABLE_LIMIT_INSUFFICIENT
UNKNOWN_REQUIRED_RESOURCE
UNCLASSIFIED_METERED_SIDE_EFFECT
OTHER_CONTRACT_BLOCK
```

Required fail-closed law:

```text
UNKNOWN REQUIRED RESOURCE
→ RESOURCE_ADMISSION = NOT_ADMISSIBLE
```

Unknown is not zero.

Resource admission does not alter semantic authority or executability proof.

## Metering quality and unknowns

`AUTHORITATIVE_ACTUAL` means actual usage from the governing measurement source. An `AUTHORITATIVE_ACTUAL` usage event MUST carry a non-empty `measurement_source_ref`; provenance without the governing measurement-source identity is insufficient for this quality claim.

`NORMALIZED_ACTUAL` means actual usage transformed into the canonical shape without changing factual meaning.

`ESTIMATED` is not actual usage.

`UNKNOWN` means no defensible quantity exists.

```text
UNKNOWN RESOURCE CONSUMPTION
!=
ZERO RESOURCE CONSUMPTION
```

For `METERING_QUALITY=UNKNOWN`, canonical quantity is null, not numeric zero.

Where a quantity depends materially on a valuation/quota revision, accounting preserves a durable revision/source reference so historical runs are not silently reinterpreted later.

## USAGE_EVENT

One `USAGE_EVENT` represents one resource class + one dimension for one logical operation.

It records run/operation identity, optional agent hierarchy, quantity or explicit unknown, metering quality, measurement-source reference, interpretation revision reference, and bounded start/finish observations where available.

`METERING_QUALITY=AUTHORITATIVE_ACTUAL` requires a non-null, non-empty `measurement_source_ref` identifying the governing measurement source.

Provider-specific response payloads do not belong in the core schema.

## RUN_ACCOUNTING

`RUN_ACCOUNTING` aggregates one run without collapsing different units.

It distinguishes:

```text
estimate != actual/observed totals
wall time != aggregate machine/agent time
```

It may record estimate comparison, exhaustion state, finalization-reserve use, termination reason, and unknown states.

It is factual/derived evidence, not acceptance authority.

## Parent-child invariants

Downstream enforcement must prove, where applicable:

- child scope is equal to or proven narrower than parent scope; unknown scope relation fails closed;
- child resource classes are a subset of parent classes;
- child ordinary finite amount is not greater than parent ordinary finite amount;
- child protected finalization reserve is not greater than parent protected finalization reserve;
- child attempt limit is not greater than parent attempt limit;
- child validity does not extend beyond parent validity;
- parent candidate/route bindings are preserved;
- limit mode is not relaxed;
- observation-only parent authority does not become spend authority.

The persistence/transaction mechanism is outside this contract.

## Contract-gap handling

```text
IMPLEMENTATION CONVENIENCE
!=
CONTRACT DEFECT
```

A downstream implementation MUST NOT alter this interface to fit a preferred backend, estimator representation, SDK field shape, workflow topology, or storage model.

If frozen semantics are genuinely insufficient:

```text
CONTRACT_GAP_FOUND
→ downstream STOP
→ bounded contract amendment
→ merge
→ exact-main re-freeze
→ downstream restart
```

The downstream workstream must identify the exact insufficient semantic requirement and show why the defect is contract-level rather than implementation-specific.

`CONTRACT_GAP_FOUND` does not authorize downstream mutation of RG-01.

## Cross-ownership boundaries

- #56 owns durable materialization/readback. RG-01 only requires Resource Governance artifacts to remain compatible with that law.
- #57 owns provider-neutral execution surfaces and brokers. Resource Governance consumes route identity; it does not own provider adapters.
- #59 owns HC1-HC4/autonomy. An autonomy envelope may source a bounded grant; higher autonomy is not unlimited resource authority.
- #61 owns proportional assurance, evidence ceilings, and control-loop hardening. Resource Governance consumes those semantics rather than duplicating them.
- #62 owns deferred Software capabilities. Test-design and CI-pipeline design remain downstream workstreams.

## Non-goals

RG-01 defines no:

- estimator algorithm;
- ledger backend;
- transaction mechanism;
- provider/model SDK;
- tokenizer/pricing implementation;
- CI workflow design;
- verification-plan or verification-policy contract;
- execution-surface discovery;
- Resolver mutation;
- role runtime change;
- new Engine;
- second Director.

The frozen interface is implementation-independent by design.
