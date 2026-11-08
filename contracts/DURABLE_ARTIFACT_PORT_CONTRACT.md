# Durable Artifact Port Contract — 56-B

This contract materializes the provider-neutral durable materialization and independent readback seam owned by parent issue #56.

It is deliberately smaller than a storage subsystem. It defines one portable boundary and one conformance backend. It does not select a real provider, create an Artifact/Storage Manager, or change Control/Verifier policy.

**Current-state note:** this file defines the original **56-B port scope**, not the whole current runtime. The later 56-C enforcement is implemented in `tools/durable_readback_enforcement.py` and consumed by `tools/resolver_transition.py`; current Control/Verifier rules are described in `protocols/artifacts.md`. Provider-neutral local/reference readback must not be represented as verified publication to GitHub, Google Drive or another live system of record.

## Upstream A1 authority

56-B consumes the merged A1 laws without redefining them:

```text
ASSIGNMENT.required_durable_outputs
= opaque assignment-local output identities

EXECUTOR_RESULT.durable_output_refs
= opaque non-blank durable artifact refs bound to those identities

DURABLE REF PRESENT
!=
DURABLE READBACK PROVEN
```

The existing A1 assignment/result shapes remain valid.

## Mandatory distinctions

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

`system_of_record_ref` is an explicit opaque semantic identity for the declared durable authority surface. Provider credentials, URL structures, filesystem layout, provider object models, browser state, and runtime mechanics stay behind the port.

A durable artifact ref is an opaque stable identity. A caller must not need the writer's local object identity, local output path, predecessor chat, or hidden in-memory state to resolve it.

Materialization success proves only that the exact payload was persisted by the declared durable surface and a durable ref was returned after that success. It does not prove factual claims carried by the payload.

Readback success proves only that the exact durable object can be independently resolved from the declared durable surface and that its content identity matches the durable ref. It does not verify factual claims inside the payload.

## Provider-neutral port

The portable capability is equivalent to:

```text
materialize(
    system_of_record_ref,
    output_identity,
    exact_payload_bytes
)
→ MaterializationResult

readback(
    system_of_record_ref,
    durable_artifact_ref
)
→ ReadbackObservation
```

The universal port requires no GitHub id, Drive id, URL, filesystem path, database key, browser identity, credential, or PAC state.

The payload surface is exact bytes. Domain artifact serialization/deserialization remains owned by the producing/consuming role rather than becoming a new repository-wide artifact ontology.

## Materialization result semantics

The bounded materialization outcomes are:

- `MATERIALIZED` — persistence succeeded; a non-empty `artifact_ref` and `content_digest` are returned.
- `MALFORMED_INPUT` — the portable operation input is structurally invalid.
- `WRONG_SYSTEM_OF_RECORD` — the requested system-of-record identity does not match the backend binding.
- `BACKEND_FAILURE` — the backend could not persist the object.

A non-successful materialization MUST NOT return a successful durable artifact ref.

## Readback observation semantics

The bounded readback outcomes are:

- `RESOLVED` — the exact persisted payload and stable identity were independently recovered.
- `UNRESOLVED` — a structurally valid ref is unknown/not found on the declared system of record.
- `WRONG_SYSTEM_OF_RECORD` — the request or persisted record is bound to a different system of record.
- `MALFORMED_INPUT` — the portable operation input/ref is malformed.
- `BACKEND_FAILURE` — the backend could not read or validate the persisted record.

These are port outcomes only. They are not Control Director terminal states and are not `VERIFICATION_RESULT` verdicts.

## Stable exact identity

56-B must expose enough deterministic identity for later 56-C enforcement.

The reference implementation uses:

```text
content_digest = SHA-256(exact_payload_bytes)

artifact_ref = opaque deterministic identity over:
  system_of_record_ref
  output_identity
  content_digest
```

Callers treat the artifact ref as opaque. The digest is content identity, not a signature or claim-verification mechanism.

Distinct output identities are part of the reference identity, so two distinct outputs with identical payload bytes do not silently alias. Re-materializing the same system-of-record ref + output identity + exact bytes is idempotent and returns the same durable ref.

## Reference backend

`tools/durable_artifact_port.py` provides `LocalFileDurableReferencePort` solely as a conformance/reference backend.

Its local `storage_root` is backend configuration and is not part of the universal operation shape or durable artifact ref.

The conformance proof requires:

```text
writer instance
→ materialize
→ discard writer-local state
→ fresh reader instance
→ readback(system_of_record_ref, artifact_ref)
→ exact payload recovered
```

The backend fails closed for wrong system-of-record bindings, unknown refs, malformed refs, corrupt/read failures, and write failures.

## 56-C boundary and current integration

**Historical 56-B boundary:** the port alone did not change `VERIFICATION_RESULT`, `resolve_transition()`, or Control advancement. At that stage, readback capability did not yet establish readback enforcement.

**Current integrated behavior (56-C):** `evaluate_required_durable_readback()` independently resolves each assignment-required `COMPLETE` output via the declared port; `resolve_transition()` consumes that evaluation and the Verifier's matching exact readback proofs before advancing governed completion. This integration proves only the declared provider-neutral evidence boundary when the configured port actually supports it. It does not imply that every real provider adapter, in-place current-carrier workflow, or fresh-agent project continuation is implemented.

## GitHub Software candidate handoff is a distinct exact-state readback

The existing portable durable port governs declared `required_durable_outputs`.
Software candidate publication is a domain-specific repository operation with
separate GitHub PR/branch identity, draft/merge state, exact HEAD and assignment
binding. `tools/github_candidate_handoff.py` and the existing
`resolve_transition()` integrate an *independent GitHub source read* when
the issued assignment includes `github_candidate_delivery`.

That explicit Assignment declaration controls applicability in manual Stage 1.
There is no additional immutable-issuer selector, duplicate publication flag or
issuer-readback requirement. Control supplies the intended task and independently
checks its reported delivery. Non-code reports do not require a code candidate.
This does not provide tamper resistance for arbitrary edits to the supplied
Control bundle.

This does not create another general artifact storage port. A GitHub PR's
presence proves publication/identity only, not durable payload bytes through
`DurableArtifactPort`, code correctness, CI success, or promotion authority.
Use the original durable readback obligations independently when they are
declared. The GitHub reader must be backed by a live/current connector or
provider source in production; the pure function accepts a callback for
deterministic reference/conformance tests only.

## Non-goals of the 56-B port

The following describe what the **56-B port itself** does not implement or select; they are not claims that later Resolver work remains absent:

- GitHub, Google Drive, S3/R2/object-store, database, browser, or PAC adapters;
- provider credentials or provider-specific ids in universal semantics;
- a generic Artifact Manager, Storage Manager, Storage Engine, new Engine, or Director;
- claim verification;
- Control transition gating on readback;
- #58 lifecycle/session semantics;
- fresh-agent handoff contracts;
- Architecture Health;
- external execution tickets;
- Resource Governance redesign;
- migration of unrelated artifacts.
