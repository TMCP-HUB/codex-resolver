# TASK-56-B — Provider-neutral durable materialization and independent readback port

## Status

**STAGED MANUAL ASSIGNMENT SPEC — NOT YET FROZEN**

Do not execute this file directly until the predecessor gate is satisfied and Project Control materializes this task on a bounded work branch from the then-current exact authoritative `main`.

Parent: **#56 — Durable artifact completion: system-of-record materialization and independent readback**

Tracker: **#77 — PAC-READY-00**

---

## Predecessor gate

Execution is allowed only after all of the following are true:

1. 56-A1 has passed independent verification.
2. 56-A1 has been merged into authoritative `main`.
3. Current `main` has been re-read and an exact execution basis has been recorded.
4. No later main change has materially superseded the A1 durable-output contract.

If any condition is false:

```text
STATUS: BLOCKED_BY_PREDECESSOR
```

Do not repair A1 inside this task.

---

## Source and destination roles

```text
SOURCE_ROLE:
OWNER / K0 / PROJECT CONTROL

DESTINATION_ROLE:
SOFTWARE EXECUTOR /
BOUNDED DURABLE-PORT IMPLEMENTER /
SYSTEM-OF-RECORD READBACK PRIMITIVE IMPLEMENTER
```

Destination surface:

```text
CODEX with authoritative repository checkout/materialization
```

---

## Mode

```text
BOUNDED CONTRACT + REFERENCE IMPLEMENTATION
ONE WORK BRANCH
ONE PR
NO MERGE
NO GITHUB ACTIONS
NO GITHUB/DRIVE PROVIDER ADAPTER
NO PAC
NO #58 IMPLEMENTATION
NO VERIFICATION POLICY REDESIGN
NO TRANSITION ADVANCEMENT REDESIGN
```

---

## Purpose

Materialize the next #56 seam after A1:

```text
DURABLE OUTPUT REQUIREMENT
        ↓
DECLARED DURABLE SYSTEM-OF-RECORD TARGET
        ↓
MATERIALIZE
        ↓
STABLE OPAQUE ARTIFACT REF
        ↓
INDEPENDENT READBACK BY REF
```

56-B creates the provider-neutral primitive that later work can enforce.

It does **not** yet make Control advancement depend on successful readback. That is 56-C.

---

## Frozen laws from A1

Treat the merged A1 laws as upstream authority:

```text
ASSIGNMENT.required_durable_outputs
declares opaque assignment-local output identities

EXECUTOR_RESULT.durable_output_refs
binds those identities to opaque non-blank refs

DURABLE REF PRESENT
!=
DURABLE READBACK PROVEN
```

Do not reinterpret or replace those semantics.

---

## Required semantic distinction

Freeze and implement:

```text
SYSTEM-OF-RECORD IDENTITY
!=
PROVIDER MECHANICS

ARTIFACT REF
!=
LOCAL PATH

MATERIALIZATION SUCCESS
!=
CLAIM TRUTH

READBACK SUCCESS
!=
CLAIM VERIFICATION
```

Readback proves only that the exact required durable object can be independently resolved from its declared durable authority surface.

It does not prove that factual claims inside the object are true.

---

## Required design outcome

Inspect current architecture first and reuse existing owners where possible.

The implementation must expose a provider-neutral contract equivalent in capability to:

```text
materialize(
    system_of_record_ref,
    output_identity,
    payload_or_source
)
→ durable_artifact_ref

readback(
    system_of_record_ref,
    durable_artifact_ref
)
→ readback observation / resolved artifact
```

Exact names may differ if existing architecture provides a better owner.

### Required properties

1. `system_of_record_ref` is explicit and opaque/provider-neutral.
2. A durable artifact ref is created only after successful materialization to that declared system of record.
3. A readback operation resolves by durable ref from the declared system of record.
4. Readback must not depend on executor-local object identity, local path, predecessor chat, or hidden in-memory state.
5. Materialization and readback must be invocable by distinct caller instances.
6. Wrong system-of-record binding fails closed.
7. Unknown/unresolvable refs fail closed.
8. Ref identity must be stable enough for later exact-result and verification binding.
9. Provider-specific credentials, URL structures, filesystem layout, GitHub object models, Google Drive IDs, browser state, and PAC mechanics stay outside the universal semantic contract.
10. Existing A1 result-ref shape remains valid unless a true contract gap is proven.

---

## Reference backend requirement

Implement one deliberately simple reference/fake backend sufficient to prove the port semantics.

It may use a local deterministic persistence mechanism suitable for tests.

The reference backend must prove at minimum:

```text
writer instance
→ materialize output
→ discard writer-local state
→ fresh reader instance
→ read back by system-of-record ref + artifact ref
→ recover exact durable object
```

A test that merely returns the same Python object from the same adapter instance is insufficient.

The fake backend is a conformance/reference implementation, not a universal storage engine.

---

## Identity and exactness

Later 56-C must be able to determine that the object read back is the object that was materialized.

Therefore 56-B must expose enough stable identity to compare materialization and readback.

Prefer the smallest deterministic mechanism already compatible with repository conventions, for example:

- exact artifact identity;
- content digest;
- immutable record identity;
- equivalent deterministic content identity.

Do not introduce cryptographic signing, distributed consensus, or provider-specific version models unless current architecture already requires them.

---

## Failure semantics

Materialization failure must not mint a successful durable ref.

Readback must distinguish at least the equivalent of:

- resolved;
- unresolved/not found;
- wrong system-of-record binding;
- malformed ref/input;
- backend/read failure.

Do not invent Control Director terminal states here.

Use bounded port/result semantics suitable for 56-C to consume.

---

## Required regressions

Add semantic regressions proving at least:

1. successful materialization returns a non-empty stable durable ref;
2. a fresh reader instance resolves the ref from the same declared system of record;
3. readback returns exact matching artifact/content identity;
4. wrong system-of-record ref fails closed;
5. unknown durable artifact ref fails closed;
6. failed materialization does not mint a valid ref;
7. reader does not require writer-local object/path/session state;
8. two distinct outputs cannot silently alias to the same identity unless content-addressed semantics intentionally and explicitly make them identical;
9. A1 legacy/no-durable-output behavior is unchanged;
10. no provider-specific storage identifiers are required by the universal contract.

---

## Explicit non-goals

Do not implement:

- GitHub adapter;
- Google Drive adapter;
- S3/R2/object-store adapter;
- database provider adapter;
- browser/PAC storage;
- `VERIFICATION_RESULT` readback enforcement;
- Control transition gating on readback;
- #58 agent lifecycle/session epoch;
- fresh-agent handoff contract;
- Architecture Health;
- external execution ticket;
- Resource Governance redesign;
- generic Artifact Manager / Storage Manager / Storage Engine;
- migration of unrelated artifacts.

---

## Stop conditions

Stop and return a bounded causal finding if implementation requires:

- rewriting the A1 required-output/reference contract;
- selecting one universal provider;
- provider credentials in universal schemas;
- browser/runtime identity in durable artifact semantics;
- a new global Engine/Director;
- broad artifact ontology redesign;
- #58 semantics;
- verifier/transition changes merely to make the port coherent.

If an upstream gap is real:

```text
CONTRACT_GAP_FOUND: YES
CAUSE: <exact gap>
MINIMUM UPSTREAM DECISION NEEDED: <bounded decision>
```

Do not repair outside this task.

---

## Acceptance

56-B is complete only when:

```text
DEFINED:
provider-neutral system-of-record materialization/readback boundary exists

MATERIALIZED:
one bounded implementation + reference backend implements it

PROVEN:
fresh reader instance can independently resolve the exact materialized artifact

NOT YET ENFORCED:
Control advancement and VERIFICATION_RESULT do not yet depend on readback

NOT CLAIMED:
provider integrations, claim truth, fresh-agent lifecycle, PAC
```

---

## Required final report

Return:

- exact starting `main`;
- exact task commit;
- exact final HEAD/tree;
- changed-file list;
- chosen provider-neutral port shape;
- how system-of-record identity is represented;
- how exact materialization/readback identity is proven;
- reference backend used;
- regressions executed and results;
- checks not executed;
- explicit statement that Control/Verifier enforcement remains for 56-C;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `MERGE READINESS` for independent verification only.

Do not merge.
