# TASK-56-C-R1 — Pre-spawn durable identity compatibility repair

## Status

**IMMUTABLE BOUNDED REPAIR PACKET**

Corrective child task for `TASK-56-C.md` only.

Parent PR: **#88**

Rejected candidate under repair:

```text
49a7cc7bf8e0027461e97dc35f9a6df53cc824be
```

Do not edit `tasks/TASK-56-C.md`.
Do not start 56-D.
Do not redesign 56-C or 56-B.

---

## Finding

Independent verification found one bounded integration defect at the ASSIGNMENT → merged 56-B port boundary.

Current assignment validation in `tools/durable_output_contract.py` accepts any non-blank Python string as:

- a `required_durable_outputs` identity;
- `durable_system_of_record_ref`.

Merged 56-B intentionally has a stricter identity acceptance boundary: values accepted as `system_of_record_ref` / `output_identity` must also be encodable as UTF-8. This was frozen and repaired by 56-B-R1.

Therefore Control can currently issue an assignment such as:

```python
required_durable_outputs = ["\ud800"]
durable_system_of_record_ref = "SOR-PRIMARY"
```

or:

```python
required_durable_outputs = ["report"]
durable_system_of_record_ref = "\ud800"
```

and still reach `SPAWN_READY`, while the merged 56-B materialization boundary will reject the same identity as `MALFORMED_INPUT`.

That means Control can issue a governed assignment which is already known to be unmaterializable by the exact durable port contract that 56-C integrates.

```text
CONTRACT_GAP_FOUND: NO
IMPLEMENTATION_DEFECT: YES
```

---

## Required correction

Make the smallest possible correction so assignment-side durable identities accepted before `SPAWN_READY` are compatible with the already-merged 56-B identity acceptance boundary.

Prefer strengthening the existing durable assignment validation boundary rather than adding a new manager/helper subsystem.

At minimum:

```text
required durable output id
must be:
string
+ non-blank
+ UTF-8 encodable
```

and:

```text
durable_system_of_record_ref
must be:
string
+ non-blank
+ UTF-8 encodable
```

Normal valid UTF-8 identities must remain unchanged.

Do not introduce NFC/NFD normalization, transliteration, provider-specific restrictions, URL rules, or a new universal identifier grammar.

---

## Required pre-spawn regressions

Add regressions proving at least:

1. `required_durable_outputs = ["\ud800"]` with a valid SOR
   - does **not** reach `SPAWN_READY`;
   - fails through the existing final-assignment proof path.

2. `durable_system_of_record_ref = "\ud800"` with `required_durable_outputs = ["report"]`
   - does **not** reach `SPAWN_READY`;
   - fails through the existing final-assignment proof path.

3. ordinary UTF-8 output identity + ordinary UTF-8 SOR
   - still reaches the existing valid spawn/readback path.

Rerun the directly affected 56-C/A1 durable-output tests after the correction.

---

## Expected scope

Normally only existing owners should change:

- `tools/durable_output_contract.py`;
- `tests/test_durable_output_contract.py`;
- optionally a directly relevant 56-C regression file only if needed to prove the same boundary.

No schema redesign is required merely for this correction. JSON Schema does not need a new Unicode-normalization policy; runtime validation owns this bounded compatibility rule where necessary.

---

## Explicit non-goals

Do not modify or implement:

- 56-D;
- provider adapters;
- PAC/browser/MCP;
- `VERIFICATION_RESULT` semantics beyond the already implemented 56-C behavior;
- `resolve_transition()` unless the correction proves directly necessary there;
- 56-B port semantics;
- #58 lifecycle;
- #61;
- Resource Governance;
- execution tickets;
- a new artifact/storage/identity subsystem;
- Unicode normalization policy.

---

## Stop conditions

If this cannot be repaired by aligning the existing assignment identity validation with the already-merged 56-B boundary, stop and report the exact cause.

Do not broaden scope.

---

## Verification

Minimum expected local verification:

```text
python -m py_compile <changed Python/test owners>
python -m unittest -v tests.test_durable_output_contract
python -m unittest -v tests.test_durable_readback_enforcement
```

If repository checkout is available, run directly relevant existing transition regressions as appropriate.

No GitHub Actions.
No provider integration tests.

---

## Acceptance

Repair passes only when:

```text
UNENCODABLE REQUIRED OUTPUT ID
→ NO SPAWN_READY

UNENCODABLE DURABLE SOR REF
→ NO SPAWN_READY

NORMAL UTF-8 IDENTITIES
→ UNCHANGED

56-C READBACK / VERIFIER ENFORCEMENT
→ UNCHANGED

56-D
→ NOT STARTED
```

---

## Required final report

Return:

- exact repair starting HEAD;
- exact final HEAD/tree;
- changed-file list after this repair task;
- precise validation change;
- results of the two required invalid-identity regressions;
- valid UTF-8 compatibility result;
- affected 56-C/A1 regression results;
- `py_compile` result;
- checks not run;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `IMPLEMENTATION_DEFECT: REPAIRED|NOT_REPAIRED`;
- `MERGE READINESS` for independent re-verification only.

Do not merge PR #88.