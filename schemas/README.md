# Artifact Schemas

These are lightweight standalone JSON Schemas for role-native and shared control artifacts. They intentionally avoid a framework/runtime dependency.

Every schema includes the common envelope: `artifact_type`, `artifact_id`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, and `related_artifacts`. Pre-assignment artifacts may use `assignment_id: null`. Role/control-specific fields are added by each artifact type.

## Bootstrap runtime observation

`schemas/sbc-runtime-context.schema.json` is intentionally not a role-native durable control artifact and does not use the common artifact envelope. It is a closed V0 observation **when supplied by an actual SBC Browser runtime**, distinguishing `SBC_BROWSER` from absent-context `ORDINARY_CHAT`. The Owner-confirmed parallel transport work (current Issue #12) is not proof of deployed physical dispatch or this runtime. The observation does not replace `CAPABILITY_PROFILE`, carry semantic authority, or advertise provider/tab/session identity.

Assignment compilation and destination executability use four linked artifacts:

1. `COMPILED_ASSIGNMENT` — authority/movability, authorized claim bindings, context authority, responsibility partition, exact execution-envelope ref/result, and authorized action-plus-evidence capability closure;
2. `CAPABILITY_PROFILE` — evidence-bearing, freshness-bounded capabilities for one exact destination/runtime;
3. `ASSIGNMENT_ADMISSIBILITY` — exact compiled-assignment binding, mandatory-action accounting, and deterministic required-vs-available comparison;
4. `ASSIGNMENT.execution_contract` — binds the same compiled assignment and is materialized as executable work only when the cited admissibility proof is `ADMISSIBLE` and no required capability is unsatisfied.

The schemas constrain shape; `tools/executability.py` validates cross-field and cross-artifact consistency such as capability evidence coverage, mandatory-action closure, exact profile binding, and the subset relation.
# Executability parity matrix

| Artifact | Required deterministic/schema constraints |
|---|---|
| `CAPABILITY_PROFILE` | exact destination/runtime, unique capability sets, strict freshness timestamps, evidence references and optional non-authoritative transport copies |
| `CAPABILITY_EVIDENCE` | exact artifact/runtime/capabilities, producer and state identity, observation/validity timestamps, observation method, provenance, related artifacts, created-from lineage; governed resolution is a reference-validator semantic gate |
| `ASSIGNMENT_ADMISSIBILITY` | exact draft/compiled-assignment/profile/runtime and `route_ref`, mandatory-action union, evidence-path equality, empty missing set iff admissible |
| `EXECUTION_ROUTE` | exact draft/structured final result identity, exactly one of each logical role, directional source/target handoff requirements or same-surface internal transfer when applicable, and an optional Director-declared same-actor continuation; segment-id uniqueness, ordered-edge topology, profile resolution, cross-artifact execution identity, and subset/equivalence checks are explicit reference-only semantic gates |
| `ASSIGNMENT` | complete common/assignment fields, proven execution contract, exact draft/profile/admissibility/route bindings, empty missing set, and `result_to` equality with the route final destination |

`tests/test_executability_parity.py` executes a bounded JSON-Schema keyword subset against committed fixtures because this repository has no JSON-Schema runtime dependency. It compares schema and reference acceptance for their shared structural surface and explicitly labels cross-artifact/topological rules that are intentionally reference-only rather than pretending standalone schemas can express them.

The shared timestamp structure is the documented Python-datetime-compatible RFC3339 subset: complete seconds, optional non-empty fractional seconds, `Z` or an offset with hour `00`–`23` and minute `00`–`59`, and ordinary clock minutes/seconds `00`–`59`. Calendar validity and UTC-normalization overflow remain deterministic reference/runtime-domain checks rather than standalone schema claims. The bounded parity runner executes `pattern` but does not claim general JSON-Schema `format` support.
| `COMPILED_ASSIGNMENT` | exact authority class, context-authority enum, responsibility partition, supported envelope, authorized action/capability closure, and explicit rejection errors |
| `EXECUTION_ENVELOPE` | stable local control-state identity and the bounded obligation classes supported by the current Resolver surface portfolio |
