# TASK-56-D — Fresh independent consumer conformance and #56 closure proof

## Status

**STAGED MANUAL ASSIGNMENT SPEC — NOT YET FROZEN**

Do not execute until 56-C is independently verified, merged, and current authoritative `main` is refrozen.

Parent: **#56**

Tracker: **#77**

---

## Predecessor gate

Required:

```text
56-A1 MERGED
+
56-B MERGED
+
56-C MERGED
+
current main verified
```

This task is primarily a conformance/closure task.

It must not invent new architecture merely because a test is inconvenient.

---

## Source and destination roles

```text
SOURCE_ROLE:
OWNER / K0 / PROJECT CONTROL

DESTINATION_ROLE:
SOFTWARE VERIFICATION EXECUTOR /
DURABLE-COMPLETION CONFORMANCE IMPLEMENTER /
FRESH-CONSUMER REGRESSION AUTHOR
```

---

## Mode

```text
BOUNDED CONFORMANCE + MINIMAL CORRECTION
ONE WORK BRANCH
ONE PR
NO MERGE
NO GITHUB ACTIONS
NO PROVIDER INTEGRATION
NO PAC
NO #58 FEATURE IMPLEMENTATION
```

---

## Purpose

Prove the defining #56 operational acceptance condition:

> A fresh independent consumer, given only current durable project state, required durable artifact refs, role contract, and current assignment/handoff, can locate and consume every required upstream artifact without predecessor chat, predecessor memory, predecessor local workspace, or hidden session state.

Core law:

```text
PREDECESSOR LOCAL ACCESS
MUST NOT BE REQUIRED
FOR DURABLE COMPLETION
```

---

## Scope

Build an end-to-end conformance harness around the merged A1/B/C semantics.

The harness must simulate a predecessor executor and a genuinely fresh downstream consumer boundary.

It must prove that all required upstream artifacts are recoverable only from durable state/refs and declared durable authority.

The test must not pass because both sides share:

- the same in-memory Python object;
- the same temporary local output path;
- the same mutable executor workspace;
- predecessor chat transcript;
- predecessor process globals;
- implicit fixture state that represents hidden predecessor memory.

---

## Required fresh-consumer input boundary

The downstream consumer may receive only equivalents of:

- current durable project/control state required by current architecture;
- required durable artifact refs;
- declared system-of-record identity needed to resolve those refs;
- role contract / authorized consumer role context;
- current assignment or handoff;
- other already-canonical durable refs explicitly required by existing contracts.

It must not receive the predecessor's local output object or hidden lookup table.

---

## Required conformance sequence

At minimum, prove an equivalent lifecycle:

```text
PREDECESSOR EXECUTOR
creates local output
        ↓
materializes through 56-B port
        ↓
returns A1 durable ref binding
        ↓
56-C independent readback / verification succeeds
        ↓
predecessor-local execution context is destroyed or made inaccessible
        ↓
fresh consumer is constructed
        ↓
fresh consumer receives only durable allowed inputs
        ↓
fresh consumer resolves and consumes required upstream artifact
        ↓
continuation succeeds
```

Then prove the negative case:

```text
local output exists
BUT durable materialization/readback does not
        ↓
predecessor context removed
        ↓
fresh consumer cannot continue
        ↓
system must not call upstream work operationally complete
```

---

## Relationship to #58

This task must **not** implement the general Agent Instance lifecycle from #58.

The fresh consumer here is a conformance test boundary for #56 only.

Allowed:

- create a new process/object/test fixture representing an independent consumer;
- explicitly remove predecessor-local state;
- prove durable-only reconstruction of the required artifact.

Not allowed:

- define global `AGENT_INSTANCE`;
- define `SESSION_EPOCH`;
- implement general role rotation;
- implement PAC physical instance identity;
- implement general context-handoff lifecycle.

If true #58 semantics are required merely to test #56, stop and report the exact dependency instead of implementing #58 here.

---

## Required adversarial cases

Prove at minimum:

1. predecessor local file/object deleted after materialization, fresh consumer still succeeds from durable ref;
2. predecessor local file/object exists but durable materialization never occurred, fresh consumer fails;
3. stale/incorrect durable ref cannot be rescued by predecessor local state;
4. wrong system-of-record ref fails even if similarly named local output exists;
5. durable object changed/mismatched relative to bound identity fails closed;
6. predecessor chat/session metadata is absent and continuation still succeeds on valid durable state;
7. no hidden global/cache fixture is necessary for readback;
8. zero-required-durable-output legacy path remains unaffected;
9. factual claim verification remains separate from artifact availability;
10. downstream continuation uses the exact read-back artifact identity accepted by 56-C.

---

## Cleanup/isolation requirement

The test must actively demonstrate independence.

Use the smallest mechanism suitable for the repository, such as:

- distinct adapter/port instances;
- isolated temporary directories;
- fresh subprocess where practical;
- explicit destruction of predecessor workspace;
- re-opening the reference store from durable state.

Do not claim "fresh consumer" merely because a new function was called with the predecessor object still reachable.

---

## Minimal correction authority

56-D may make only a bounded correction if the conformance test exposes an implementation defect in the already-defined A1/B/C semantics.

Allowed correction characteristics:

- no new semantic subsystem;
- directly necessary to satisfy already-frozen #56 law;
- small and causally tied to the failing conformance case.

If the failure reveals a contract gap or #58 dependency:

```text
STOP
```

Do not broaden the task.

---

## Required repository-level closure review

After conformance passes, inspect parent #56 acceptance against the exact merged architecture and report a closure matrix:

```text
#56 law / acceptance item
→ owner
→ implementation ref
→ regression/conformance proof
→ PASS / GAP
```

At minimum cover:

- required refs cannot be empty/non-resolvable for accepted durable completion;
- verifier independently reads required outputs;
- fresh consumer continues without predecessor-local state;
- predecessor continued local access cannot cause false durable completion;
- provider-neutral design works without assuming GitHub-only storage.

Do not close #56 automatically unless the frozen task explicitly grants issue-closing authority.

The final report should state whether #56 is a closure candidate.

---

## Explicit non-goals

Do not implement:

- #58 lifecycle;
- PAC;
- browser/MCP;
- real GitHub/Drive provider adapters;
- resource governance;
- execution tickets;
- autonomy;
- general context engine;
- repository-wide cleanup;
- production storage provider.

---

## Stop conditions

Stop if:

- fresh-consumer success requires predecessor hidden/local state;
- A1/B/C semantics are insufficient in a way requiring new contract authority;
- generic Agent Instance lifecycle is required;
- provider-specific semantics are required in the core;
- more than a bounded correction is needed.

Return the exact causal gap.

---

## Acceptance

56-D passes only if:

```text
FRESH INDEPENDENT CONSUMER:
PASS

PREDECESSOR LOCAL STATE REQUIRED:
NO

DURABLE REF + DECLARED SYSTEM OF RECORD SUFFICIENT:
YES

LOCAL-ONLY OUTPUT FALSE COMPLETION:
IMPOSSIBLE IN TESTED GOVERNED PATH

#56 ACCEPTANCE MATRIX:
NO UNRESOLVED #56-OWNED GAP
```

If so:

```text
#56 CLOSURE CANDIDATE: YES
```

Otherwise:

```text
#56 CLOSURE CANDIDATE: NO
CAUSE: <exact remaining gap>
```

---

## Required final report

Return:

- exact starting `main`;
- exact task commit;
- exact final HEAD/tree;
- changed-file list;
- isolation method used for fresh consumer;
- allowed downstream inputs;
- proof that predecessor-local state was unavailable;
- positive fresh-consumer result;
- negative local-only result;
- adversarial cases and results;
- #56 closure matrix;
- any bounded correction made;
- tests/checks executed;
- checks not executed;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `#56 CLOSURE CANDIDATE: YES|NO`;
- `MERGE READINESS` for independent verification.

Do not merge.
