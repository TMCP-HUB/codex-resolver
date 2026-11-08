# TASK-57-A-R1 — Fail closed on malformed execution-surface readiness

Status: FROZEN REPAIR PACKET after this file's materialization commit. Do not modify this file during execution.

Parent: #57
Child issue: #90
PR: #91
Original frozen task: `tasks/TASK-57-A.md`

Rejected candidate under repair:

`7d17f2fd84ca3258ca292551968fd60d20095424`

Execution branch:

`task-57-a-execution-surface-profile`

## Finding

Independent exact-candidate review found one bounded implementation defect in the new `CAPABILITY_PROFILE.readiness` validation.

Current code obtains:

```python
readiness = profile.get("readiness")
if readiness not in CAPABILITY_PROFILE_READINESS:
    ...
```

without first proving that `readiness` is a string/hashable value.

Therefore malformed external/runtime input such as:

```python
{"readiness": []}
{"readiness": {}}
```

can raise `TypeError: unhashable type` instead of returning ordinary validation/control failure.

This violates the fail-closed runtime boundary because `validate_capability_profile()` is called on artifact/runtime input by Resolver paths.

## Required law

```text
MALFORMED READINESS VALUE
→ VALIDATION ERROR
→ CONTROLLED RESOLVER FAILURE / WAIT AS GOVERNED
→ NO UNCAUGHT EXCEPTION
```

and:

```text
VALID READINESS STRING
→ EXISTING 57-A SEMANTICS UNCHANGED
```

## Required correction

Make the smallest correction in the existing `CAPABILITY_PROFILE` validator so readiness is type-checked before membership in the allowed readiness set.

Do not broaden the repair into a new generic validation framework.

Equivalent acceptable behavior:

```python
if not isinstance(readiness, str) or readiness not in CAPABILITY_PROFILE_READINESS:
    errors.append("readiness is invalid")
```

Exact implementation wording is executor-local as long as the required law is satisfied.

## Required regressions

Add bounded regressions proving at least:

1. `validate_capability_profile()` with `readiness=[]` returns validation errors and does not raise;
2. `validate_capability_profile()` with `readiness={}` returns validation errors and does not raise;
3. the capability-profile JSON schema rejects those malformed readiness values;
4. `resolve_spawn()` given a cited profile with unhashable/malformed readiness returns a governed non-`SPAWN_READY` result and does not raise;
5. `resolve_transition()` current-executability revalidation with unhashable/malformed readiness returns the existing governed revalidation failure path and does not raise;
6. valid `READY` / `DEGRADED` behavior remains unchanged;
7. valid non-usable string readiness (`PROVISIONING_REQUIRED`, `AUTH_REQUIRED`, `UNAVAILABLE`) remains structurally valid but execution-inadmissible as already defined by 57-A.

Reuse current test helpers/fixtures. Do not duplicate the surface-profile test system.

## Allowed implementation scope

Expected production delta:

- `tools/executability.py`

Expected tests may touch:

- `tests/test_execution_surface_profile.py`
- and only another directly affected existing executability/resolver test file if genuinely necessary.

If a wider production change is required, STOP and report why.

## Frozen integrity

Do not modify:

- `tasks/TASK-57-A.md`
- `tasks/TASK-57-A-R1.md`

Preserve original task blob:

`6b1d5021659abfc05ae3254dc98548656e2d3617`

## Explicit non-goals

Do not:

- redesign `CAPABILITY_PROFILE`;
- create `EXECUTION_SURFACE_PROFILE`;
- change readiness vocabulary;
- add provider adapters;
- start 57-B or 57-C;
- change surface selection/ranking;
- implement provisioning workflow;
- implement PAC/MCP/browser control;
- implement TICKET/CLAIM;
- change Resource Governance, autonomy, Architecture Health, #58 or PACK;
- use GitHub Actions.

## Verification

Run the smallest directly affected tests available on the execution surface, including the new malformed-readiness regressions.

If an authoritative checkout/runtime is unavailable, report exactly which tests were not run; do not fabricate results.

## Completion report

Return:

- repair starting HEAD;
- final HEAD/tree;
- exact changed files after this repair packet;
- both frozen task blobs;
- malformed list readiness result;
- malformed object readiness result;
- spawn result;
- transition result;
- tests run / not run;
- `CONTRACT_GAP_FOUND: YES|NO`;
- `IMPLEMENTATION_DEFECT: REPAIRED|NOT_REPAIRED`;
- `DUPLICATE_PROFILE_CREATED: NO`;
- `MERGE READINESS: READY FOR INDEPENDENT RE-VERIFICATION|NOT READY`.

Do not merge PR #91.