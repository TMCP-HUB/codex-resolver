# Systematic Debugging

## Purpose

Use this skill for technical issues where guessing would create churn: build failures, runtime bugs, API problems, deployment failures, UI regressions, data/state corruption, integration issues, or failing verification.

## Goal

Find the root cause before changing code. The output should identify the failing layer, the evidence, the smallest safe fix, and the verification result.

This skill owns **technical causal diagnosis**. It does not own workstream mode switching; `anti-loop-execution` decides when execution must stop and enter Causal Audit Mode.

## When to use

Use this skill when:

- tests fail;
- builds fail;
- forms or APIs behave unexpectedly;
- deployment/config/bindings fail;
- UI works in one state but breaks in another;
- data, cache, queue, analytics, or external integration behavior is wrong;
- a stop condition has moved the workstream into Causal Audit Mode.

Do not use this skill for planned feature work without a bug or unknown failure.

## Inputs

- expected behavior;
- actual behavior;
- exact error/evidence;
- current exact working state;
- environment;
- recent relevant changes;
- prior failed hypotheses/fixes if any.

## Required outputs

- Failure restated
- Exact state/environment
- Evidence collected
- Failure class
- Failing layer
- Root cause or best bounded hypothesis
- Minimal correction or next diagnostic experiment
- Verification performed
- Residual risk
- Verdict: pass, partial, blocked, or fail

## Iron rule

No fixes before root-cause evidence.

A hypothesis is allowed.
A blind patch is not.

## Debugging layers

Choose layers appropriate to the project. Typical examples:

| Layer | Evidence to collect |
|---|---|
| User/UI | user steps, rendered state, focus/layout, console, network |
| Application | exact stack/error, control flow, state transition, recent change |
| API/service | request, response, logs, contract/version, authorization |
| Data/state | schema, migration state, persisted revision, cache, queue, stale state |
| Build/toolchain | command, compiler output, dependency/lock state, generated files |
| Deployment/config | environment, bindings, routes, secrets/config names, artifact revision |
| External integration | accepted request identity, provider response, retry semantics |
| Observability | emitted event/log/trace, timestamp/source, gaps, sampling assumptions |

## Failure taxonomy

Preserve the class of failure until evidence justifies collapsing it into another cause.

Useful classes include, where relevant:

- **product/runtime defect** — implementation contradicts the accepted behavior;
- **test/evidence defect** — the check does not actually encode the property it claims to test;
- **workflow/tooling defect** — scripts, CI, generated artifacts, or automation are wrong;
- **environment/config defect** — target state, binding, dependency, credential, or platform differs;
- **contract/authority defect** — two components disagree about accepted semantics/ownership;
- **external/provider defect** — third-party behavior or availability is causal;
- **process/operation defect** — the procedure itself was invalid or executed against the wrong target;
- **unknown** — evidence is insufficient to classify yet.

These are diagnostic categories, not a universal ontology. Use the smallest set that preserves materially different correction paths.

A red check is evidence of a failed claim/check path; it is not automatically evidence that product code is wrong.

## Procedure

### 1. Restate the failure

Capture:

- expected behavior;
- actual behavior;
- exact command, route, input, or user action;
- first known bad state;
- environment;
- exact artifact/revision when relevant.

### 2. Read the exact error/evidence

Do not summarize from memory.
Use the real error text, status code, stack trace, failed assertion, log entry, or observed behavior.

If no explicit error exists, record that and gather evidence rather than inventing one.

### 3. Reproduce or bound the failure

Ask:

- deterministic or intermittent?
- local, CI, preview, production, or all?
- input/device/environment dependent?
- revision dependent?
- concurrency/timing dependent?

If reproduction is impossible, downgrade confidence.

### 4. Verify exact state before diagnosis

Confirm the state you are debugging is the state you think it is:

- current working revision;
- tested/reviewed revision where relevant;
- generated/config/schema versions;
- target environment.

Use `exact-state-verification` when identity is non-trivial.

### 5. Classify the failure before selecting a fix

Ask which correction path the evidence currently supports:

```text
product code?
test/evidence?
workflow/tooling?
environment/config?
contract/authority?
provider?
process?
unknown?
```

Do not weaken or rewrite a correct product contract merely because a flawed test or workflow is red.

Do not "fix CI" by changing tests until you have established that the test/evidence is the defective layer.

Preserve multiple contributing classes when the failure is genuinely composite.

### 6. Check recent changes and authority assumptions

Inspect:

- relevant diff/history;
- changed contracts/config/data;
- whether two components disagree about which state is authoritative;
- whether a projection/cache/log is being mistaken for source state;
- whether a retry may be crossing an irreversible boundary.

Use `authority-mapping` or `irreversible-boundary-reasoning` when those are the real questions.

### 7. Isolate the failing layer

Trace the shortest causal path from trigger to expected effect.

Do not jump directly from visible symptom to the most familiar component.

### 8. Form one falsifiable hypothesis

Write:

```text
Hypothesis: X is failing because Y.
Evidence: A, B, C.
Minimal discriminating test: Z.
```

Test one causal variable at a time when possible.

### 9. Apply the smallest source fix

After the hypothesis is supported:

- fix the source, not only the symptom;
- fix the correct failure class (product/test/workflow/environment/contract/etc.);
- avoid unrelated cleanup;
- preserve frozen scope;
- add regression evidence when the failure class warrants it.

### 10. Verify the correction on the current state

Use the strongest relevant check:

- originally failing test/path;
- broader regression suite if affected;
- build/typecheck/lint;
- migration/replay check;
- browser/manual reproduction;
- API/integration evidence;
- production/preview verification where appropriate.

Bind the result to the exact state verified.

## Anti-loop handoff

Repeated failed fixes are not permission for more guessing.

Default rule unless the frozen workstream defines a stricter threshold in advance:

```text
2 failed mutating correction generations on the same candidate/repair boundary
→ stop automatic mutating correction on that boundary, even if error classes differ
→ CAUSAL AUDIT MODE
→ re-check assumptions, authority, exact state, failure model, and failure classification
```

Count a correction failure only when a required check or observation actually runs and returns red on that boundary; an unavailable, not-executed or unknown check is not a red result. A red check is not by itself proof of a product-code defect. Separately, two identical failures of a tool/process operation without new evidence stop that operation; they do not by themselves count as two mutating correction generations or stop unrelated work. An initial red observation and read-only probes are not correction generations.

A materially different failure after a real state change is not automatically the same class. Classify it without resetting the same-boundary correction budget. Preserve the relevant state and failed-generation history in the existing Issue/PR or HANDOFF across sessions.

`anti-loop-execution` owns the mode transition and resumption decision.

## Anti-patterns

Avoid:

- changing code before reading the exact failure;
- assuming every red CI result is a product-code defect;
- weakening/deleting a semantically correct check without proving the evidence layer is wrong;
- fixing only the visible symptom;
- stacking multiple fixes before testing;
- retrying the same tool operation with no changed evidence;
- assuming local success means production success;
- assuming timeout means the operation did not happen;
- hiding partial verification behind confident language;
- starting a new branch to escape an unresolved causal model.

## Verification checklist

- [ ] Failure is stated against an exact relevant state.
- [ ] Evidence precedes code changes.
- [ ] Failure class is explicit enough to choose the right correction path.
- [ ] Red evidence was not automatically interpreted as product defect.
- [ ] Failing layer is bounded.
- [ ] Hypothesis is falsifiable.
- [ ] Correction is minimal and inside frozen scope.
- [ ] Original failure path is rechecked.
- [ ] Two failed same-boundary correction generations trigger bounded causal diagnosis before another automatic mutating correction.
- [ ] Residual uncertainty is explicit.

## Pair with

- `anti-loop-execution` for stop/resume discipline;
- `exact-state-verification` for provenance;
- `evidence-and-authority` when the failing check itself may be the defective evidence layer;
- `authority-mapping` for source-of-truth conflicts;
- `irreversible-boundary-reasoning` for post-commit/retry failures;
- `proof-loop-verification` after the correction is complete.
