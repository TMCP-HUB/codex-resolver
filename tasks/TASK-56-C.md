# TASK-56-C — Enforce durable materialization and independent readback before advancement

## Status

**STAGED MANUAL ASSIGNMENT SPEC — NOT YET FROZEN**

Do not execute until 56-B is independently verified, merged, and current authoritative `main` is refrozen for this workstream.

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
current main verified
```

56-C must consume the merged A1 declaration/reference semantics and merged B materialization/readback primitive.

Do not duplicate either.

---

## Source and destination roles

```text
SOURCE_ROLE:
OWNER / K0 / PROJECT CONTROL

DESTINATION_ROLE:
SOFTWARE EXECUTOR /
BOUNDED DURABLE-COMPLETION ENFORCER /
INDEPENDENT READBACK INTEGRATOR
```

---

## Mode

```text
BOUNDED ENFORCEMENT PATCH
ONE WORK BRANCH
ONE PR
NO MERGE
NO GITHUB ACTIONS
NO PROVIDER ADAPTER
NO PAC
NO #58 LIFECYCLE IMPLEMENTATION
NO GENERAL VERIFIER REDESIGN
```

---

## Purpose

Close the enforcement half of #56:

```text
EXECUTOR says COMPLETE
        ↓
required durable refs exist
        ↓
refs independently resolve from declared system of record
        ↓
Verifier verifies the exact read-back artifact
        ↓
ONLY THEN dependent Control advancement may occur
```

The central law:

```text
EXECUTOR_RESULT COMPLETE
!=
DURABLE COMPLETION ACCEPTED
```

until required outputs have been independently read back from the declared durable authority surface.

---

## Required laws

Mechanically enforce all of the following:

1. A required output that exists only in executor/session/local state cannot satisfy durable completion.
2. `COMPLETE` with structurally valid A1 refs is still insufficient when any required ref cannot be independently resolved.
3. Readback must use the 56-B provider-neutral port and declared system-of-record identity.
4. Readback must target the exact durable ref bound to the exact assignment-required output identity.
5. Verifier must evaluate the read-back object, not merely an executor-provided/local copy.
6. `VERIFICATION_RESULT = CONFIRMED` must be impossible for a required durable output whose readback is unresolved, mismatched, blocked, or not proven.
7. Control must not advance dependent work when required durable readback is not proven.
8. Materialization/readback availability proof must not be conflated with factual verification of claims inside the artifact.
9. Existing verification authority remains with the existing Verifier/Control architecture.
10. No new terminal Control state is introduced merely for durable readback.

---

## Integration discipline

Inspect existing owners before mutation, including at minimum the merged forms of:

- A1 durable-output validator;
- 56-B materialization/readback port;
- `EXECUTOR_RESULT`;
- `VERIFICATION_RESULT`;
- `resolve_transition()` and its direct validation owners;
- `EXECUTION_ROUTE.DURABLE_EVIDENCE_CONTROL`;
- relevant schemas/tests.

Prefer wiring the new law through existing validation/transition ownership.

Do not create a parallel "Durable Completion Director."

---

## Expected lifecycle

The governed lifecycle after 56-C must be equivalent to:

```text
ASSIGNMENT
declares required durable outputs / durable authority target
        ↓
EXECUTOR materializes outputs
        ↓
EXECUTOR_RESULT binds required output IDs to durable refs
        ↓
post-execution durable availability evaluation
        ↓
independent readback by durable refs
        ↓
Verifier evaluates exact read-back object
        ↓
VERIFICATION_RESULT
        ↓
Control transition
```

Where required readback is missing:

```text
NO ADVANCE
```

Use existing `WAIT` / `ESCALATE` / non-confirmed verification semantics according to current authoritative contracts rather than inventing a fifth terminal outcome.

---

## Exact-readback binding

The implementation must prove that the independently read object corresponds to:

- the exact assignment;
- the exact required durable output identity;
- the exact returned durable artifact ref;
- the exact declared system of record;
- the exact content/artifact identity established by the 56-B primitive.

A reader resolving "some artifact with the same filename/type" is insufficient.

---

## Verifier boundary

The Verifier may consume readback observations/evidence but must not become a storage adapter.

Required separation:

```text
DURABLE PORT
resolves exact artifact availability/content identity

VERIFIER
evaluates required claims/evidence against that exact read-back artifact
```

Do not make the Verifier responsible for provider authentication, browser navigation, filesystem discovery, or storage selection.

---

## Required failure behavior

At minimum, prove fail-closed behavior for:

- missing durable ref;
- blank/malformed durable ref;
- unknown/unresolvable ref;
- wrong system-of-record binding;
- readback identity mismatch;
- read failure/backend unavailable;
- executor-local copy available but durable readback unavailable;
- verifier presented with local copy while authoritative readback differs;
- `CONFIRMED` attempted without required durable readback proof.

No such case may advance dependent work as if durable completion were proven.

---

## Required regressions

Add bounded regressions proving at least:

1. valid A1 refs + successful independent readback can proceed to normal verification;
2. valid-looking ref that is unresolved cannot satisfy durable completion;
3. wrong system-of-record binding fails closed;
4. readback identity mismatch fails closed;
5. local executor copy cannot substitute for failed readback;
6. `VERIFICATION_RESULT=CONFIRMED` is rejected when a required durable output lacks proven readback;
7. a verifier operating on the exact read-back artifact can confirm when all other verification requirements are satisfied;
8. Control does not advance dependent work when readback is `NOT_PROVEN`/blocked;
9. assignment with zero required durable outputs preserves existing behavior;
10. PARTIAL/BLOCKED/FAILED executor results are not forced to fabricate readback proofs;
11. materialization/readback proof does not automatically confirm factual claims;
12. existing unrelated transition/verifier regressions remain green.

---

## Explicit non-goals

Do not implement:

- GitHub/Drive/provider adapters;
- fresh logical Agent Instance lifecycle;
- session epochs;
- context rebuild;
- #58;
- PAC/browser/MCP;
- Architecture Health;
- resource reservation;
- execution tickets;
- generalized evidence ontology redesign;
- new Control Director terminal state;
- artifact truth inference from successful readback.

---

## Stop conditions

Stop instead of expanding scope if this task requires:

- redesigning A1 output identities;
- redesigning B provider-neutral port;
- provider-specific logic in Resolver/Verifier;
- a second verification subsystem;
- #58 lifecycle semantics to make basic readback enforcement coherent;
- broad changes to unrelated transition authority.

Report:

```text
CONTRACT_GAP_FOUND: YES|NO
```

If YES, identify the minimum upstream repair.

---

## Acceptance

56-C is complete only when:

```text
STRUCTURAL COMPLETENESS:
A1 required refs enforced

MATERIALIZATION:
56-B durable port used

INDEPENDENT READBACK:
required outputs resolved from declared system of record

VERIFICATION:
CONFIRMED impossible without required readback proof

CONTROL:
dependent advancement impossible when required readback is missing/not proven

NOT CLAIMED:
fresh-agent continuation / #58 lifecycle
```

The remaining #56 work after C should be conformance/fresh-consumer proof, not another semantic completion subsystem.

---

## Required final report

Return:

- exact starting `main`;
- exact task commit;
- exact final HEAD/tree;
- changed-file list;
- exact integration path;
- readback proof shape consumed by verification;
- how local/session copies are prevented from substituting for authoritative readback;
- regressions run and exact results;
- checks not run;
- explicit statement that 56-D fresh-consumer conformance remains;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `MERGE READINESS` for independent verification.

Do not merge.
