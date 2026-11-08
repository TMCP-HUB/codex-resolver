# TASK-56-B-R1 — UTF-8 fail-closed correction for durable artifact identities

## Status

**IMMUTABLE BOUNDED REPAIR PACKET**

This is a corrective child task for `TASK-56-B.md` only.

Parent implementation candidate under repair:

```text
PR: #87
BRANCH: task-56-b-durable-materialization-readback
REJECTED CANDIDATE HEAD:
fbd06651626ffa6f94e08a26af37d6f70fb29537
```

Do not edit `TASK-56-B.md`.
Do not start 56-C.
Do not redesign 56-B.

---

## Source finding

Independent review found one bounded implementation defect in `tools/durable_artifact_port.py`.

Current string validation accepts non-blank Python strings that cannot be encoded as UTF-8, including lone Unicode surrogate code points.

Example:

```python
output_identity = "\ud800"
```

Current behavior can reach:

```python
json.dumps(..., ensure_ascii=False).encode("utf-8")
```

and raise `UnicodeEncodeError` outside the bounded result contract.

The same class of defect can occur during readback if a corrupt persisted durable record contains an unencodable identity and recomputation of the deterministic artifact ref escapes the intended failure boundary.

This violates the already-defined 56-B law that malformed caller input and corrupt persisted state fail closed through bounded result statuses rather than uncaught exceptions.

```text
CONTRACT_GAP_FOUND: NO
IMPLEMENTATION_DEFECT: YES
```

---

## Required correction

Make the smallest possible change so every identity string accepted by the durable artifact port is safe for the exact UTF-8 encoding used by deterministic identity construction.

Prefer strengthening the existing validation boundary rather than adding a parallel manager/helper subsystem.

Equivalent acceptable behavior:

```text
caller-supplied non-UTF-8-encodable identity
→ MALFORMED_INPUT
→ no artifact ref minted
→ no uncaught UnicodeEncodeError
```

and:

```text
persisted corrupt non-UTF-8-encodable identity
→ BACKEND_FAILURE
→ no uncaught UnicodeEncodeError
```

The correction must cover all relevant 56-B identity inputs, including at minimum:

- `system_of_record_ref` used by `materialize()`;
- `output_identity` used by `materialize()`;
- `system_of_record_ref` used by `readback()`;
- persisted `output_identity` used during readback identity recomputation.

If the current implementation has another path that hashes/encodes the same semantic identities, include it only where necessary to preserve the same fail-closed law.

---

## Required regressions

Add bounded regressions proving at least:

1. `materialize(system_of_record_ref="valid", output_identity="\ud800", payload=b"x")`
   - returns `MALFORMED_INPUT`;
   - returns no successful artifact ref;
   - raises no exception.

2. `materialize(system_of_record_ref="\ud800", output_identity="valid", payload=b"x")`
   - returns `MALFORMED_INPUT`;
   - returns no successful artifact ref;
   - raises no exception.

3. `readback(system_of_record_ref="\ud800", artifact_ref=<syntactically valid ref>)`
   - returns `MALFORMED_INPUT`;
   - raises no exception.

4. a corrupt persisted durable record containing `output_identity="\ud800"`
   - returns `BACKEND_FAILURE`;
   - raises no exception.

Also rerun the existing 56-B regression suite and prove no behavior regression for normal UTF-8 identities.

---

## Explicit non-goals

Do not implement or modify:

- 56-C;
- Control advancement/readback enforcement;
- `VERIFICATION_RESULT`;
- A1 schemas/contracts;
- provider adapters;
- PAC/browser/MCP;
- #58;
- #61;
- Resource Governance;
- universal Unicode normalization policy;
- NFC/NFD canonicalization;
- transliteration;
- provider-specific identifier restrictions;
- a new storage/artifact subsystem.

This task is only about keeping the existing 56-B port total/fail-closed for malformed Unicode identities.

---

## Scope discipline

Expected implementation delta should be very small and remain inside existing 56-B ownership, normally:

- `tools/durable_artifact_port.py`;
- `tests/test_durable_artifact_port.py`.

Do not modify the original frozen `tasks/TASK-56-B.md`.

If a broader contract change becomes necessary, stop and report:

```text
CONTRACT_GAP_FOUND: YES
CAUSE: <exact cause>
MINIMUM UPSTREAM DECISION NEEDED: <bounded decision>
```

Do not repair outside this task.

---

## Verification

Use minimum sufficient local verification:

```text
python -m py_compile <changed Python owners>
python -m unittest -v tests.test_durable_artifact_port
```

Run additional direct tests only if required by the correction.

No GitHub Actions.
No provider integration tests.
No broad test-chasing loop.

---

## Acceptance

The repair passes only when:

```text
UNENCODABLE CALLER IDENTITY
→ bounded MALFORMED_INPUT
→ no exception

UNENCODABLE PERSISTED IDENTITY
→ bounded BACKEND_FAILURE
→ no exception

NORMAL 56-B PATH
→ unchanged

56-C
→ NOT STARTED
```

---

## Required final report

Return:

- exact repair starting HEAD;
- exact final HEAD/tree;
- exact changed-file list after this repair packet;
- precise validation change;
- results of the four required Unicode regressions;
- complete `tests.test_durable_artifact_port` result;
- `py_compile` result;
- checks not run;
- explicit `CONTRACT_GAP_FOUND: YES|NO`;
- `IMPLEMENTATION_DEFECT: REPAIRED|NOT_REPAIRED`;
- `MERGE READINESS` for independent re-verification only.

Do not merge PR #87.
