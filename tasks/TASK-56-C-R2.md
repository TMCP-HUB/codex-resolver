# TASK-56-C-R2 — Repository-test correction after authoritative Codespaces run

## Status

**IMMUTABLE BOUNDED REPAIR PACKET**

Corrective child task for `TASK-56-C.md` after an authoritative Codespaces test run.

Parent PR: **#88**

Starting candidate under repair:

```text
e0dc77318e687ce6cbb015e8462e9c76ac4c3fdf
```

Do not edit `tasks/TASK-56-C.md` or `tasks/TASK-56-C-R1.md`.
Do not start 56-D.
Do not redesign 56-C, A1, or 56-B.

---

## Authoritative test evidence

The exact branch HEAD was verified in GitHub Codespaces:

```text
git rev-parse HEAD
e0dc77318e687ce6cbb015e8462e9c76ac4c3fdf
```

Required repository tests were then run:

```text
python -m unittest -v tests.test_durable_output_contract
python -m unittest -v tests.test_durable_readback_enforcement
```

Observed results:

```text
tests.test_durable_output_contract
18 tests
17 PASS
1 FAIL

FAIL:
test_partial_may_report_only_materialized_subset
expected:
  WAIT / AUTHORIZED_REQUIREMENT_PENDING
actual:
  ESCALATE / VERIFICATION_DURABLE_READBACK_MISMATCH
```

and:

```text
tests.test_durable_readback_enforcement
13 tests
12 PASS
1 FAIL

FAIL:
test_confirmed_is_rejected_without_required_readback_proof

Control correctly returned:
  ESCALATE / VERIFICATION_DURABLE_READBACK_MISMATCH

with error:
  verification result is missing durable readback proofs: ['report']

but the test additionally asserted that some error string must literally contain
"CONFIRMED".
```

---

## Finding A — real implementation defect

`evaluate_required_durable_readback()` intentionally returns `READBACK_NOT_REQUIRED` when the executor status is not `COMPLETE`.

That is correct and preserves the frozen law:

```text
PARTIAL / BLOCKED / FAILED
must not be forced to fabricate durable readback proofs
```

However, `resolve_transition()` currently continues into:

```text
validate_verification_durable_readback_proofs(...)
```

with `expected_proofs=None` even when durable readback is `READBACK_NOT_REQUIRED`.

For a PARTIAL result with required durable outputs and a normal verification artifact, that validator then treats the missing readback proof as a verification mismatch and escalates before existing incomplete-result semantics can return the authorized WAIT path.

This is a bounded integration defect.

```text
CONTRACT_GAP_FOUND: NO
IMPLEMENTATION_DEFECT_A: YES
```

### Required correction A

Make the smallest possible correction so durable verification-proof enforcement applies only when durable readback is actually required/proven for the governed completion attempt.

Equivalent required behavior:

```text
COMPLETE + required durable outputs
→ durable readback required
→ exact verifier durable-proof binding required

PARTIAL / BLOCKED / FAILED
→ durable readback NOT_REQUIRED
→ do not require fabricated verifier durable-readback proof
→ continue through existing incomplete-result / verification semantics
```

The existing `test_partial_may_report_only_materialized_subset` must pass unchanged unless a stronger existing canonical expectation proves otherwise.

Do not weaken COMPLETE enforcement.
Do not let a COMPLETE result bypass readback-proof binding.
Do not invent a new Control state.

Expected owner is normally `tools/resolver_transition.py`; change another production owner only if directly necessary.

---

## Finding B — test assertion defect, not production defect

For a COMPLETE result whose artifact was independently read back but whose `VERIFICATION_RESULT` omits the required `durable_readback_proofs`, current production behavior is already fail-closed:

```text
ESCALATE
VERIFICATION_DURABLE_READBACK_MISMATCH
error: verification result is missing durable readback proofs: ['report']
```

That satisfies the 56-C semantic requirement that `CONFIRMED` cannot be accepted without required durable readback proof.

The failing regression additionally requires an implementation diagnostic string to literally contain `CONFIRMED`:

```python
self.assertTrue(any("CONFIRMED" in error for error in resolved["errors"]), resolved)
```

The frozen task does not require that wording. The observable semantic outcome and missing-proof reason are sufficient.

```text
CONTRACT_GAP_FOUND: NO
IMPLEMENTATION_DEFECT_B: NO
TEST_ASSERTION_DEFECT_B: YES
```

### Required correction B

Correct the regression to assert the actual semantic contract, for example all of:

```text
control_state == ESCALATE
reason == VERIFICATION_DURABLE_READBACK_MISMATCH
errors identify missing durable readback proof for report
```

Do not change production code merely to inject the word `CONFIRMED` into an error message unless an already-canonical contract explicitly requires that exact diagnostic wording.

Expected owner:

- `tests/test_durable_readback_enforcement.py`

---

## Required regressions

After correction, prove at least:

1. PARTIAL + declared required durable outputs + subset binding
   - does not require readback proof;
   - does not escalate merely because durable proof is absent;
   - reaches existing `WAIT / AUTHORIZED_REQUIREMENT_PENDING` path.

2. BLOCKED and FAILED continue to avoid fabricated durable-readback proof requirements.

3. COMPLETE + required durable outputs still cannot proceed without independent readback.

4. COMPLETE + proven readback + missing verifier durable proof still fails closed with `VERIFICATION_DURABLE_READBACK_MISMATCH`.

5. Exact verifier proof binding success path remains green.

6. R1 UTF-8 pre-spawn regressions remain green.

---

## Required verification

Run in the same authoritative Codespaces checkout after implementation:

```text
python -m unittest -v tests.test_durable_output_contract
python -m unittest -v tests.test_durable_readback_enforcement
```

Both modules must report zero failures.

Then also run the directly affected transition module:

```text
python -m unittest -v tests.test_resolver_transition
```

No GitHub Actions.
No provider integration tests.

---

## Explicit non-goals

Do not implement or modify:

- 56-D;
- provider adapters;
- PAC/browser/MCP;
- #58 lifecycle;
- #61;
- Resource Governance;
- execution tickets;
- 56-B port semantics;
- A1 identity model;
- Unicode normalization policy;
- a second verifier/readback subsystem;
- new terminal Control states.

---

## Acceptance

R2 passes only when:

```text
PARTIAL / BLOCKED / FAILED
→ NO FABRICATED DURABLE PROOF REQUIREMENT

COMPLETE + REQUIRED DURABLE OUTPUTS
→ READBACK ENFORCEMENT UNCHANGED

COMPLETE + READBACK PROVEN + VERIFIER PROOF MISSING
→ FAIL CLOSED

TEST DIAGNOSTICS
→ ASSERT SEMANTICS, NOT UNREQUIRED WORDING

REQUIRED CODESPACE MODULES
→ ZERO FAILURES

56-D
→ NOT STARTED
```

---

## Required final report

Return:

- exact R2 starting HEAD;
- exact final HEAD/tree;
- changed-file list after R2;
- precise correction A;
- precise correction B;
- exact results of:
  - `tests.test_durable_output_contract`;
  - `tests.test_durable_readback_enforcement`;
  - `tests.test_resolver_transition`;
- checks not run;
- confirmation that R1 task and original C task are unchanged;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `IMPLEMENTATION_DEFECT_A: REPAIRED|NOT_REPAIRED`;
- `TEST_ASSERTION_DEFECT_B: REPAIRED|NOT_REPAIRED`;
- `MERGE READINESS` for independent exact-candidate verification.

Do not merge PR #88.
