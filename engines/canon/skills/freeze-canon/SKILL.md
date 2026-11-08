---
name: freeze-canon
description: Freeze an explicitly authorized Canon scope at Foundation 0.x, Canon 1.0 or Canon 2.0 after maturity-appropriate validation gates pass.
---

# Freeze Canon

## Purpose and goal

Freeze a validated, explicitly authorized Canon scope at its applicable maturity without expanding its authority or concealing unresolved state.

## When to use and inputs

Use for an assigned Canon freeze with exact candidate, maturity, scope, validation and applicable authority. Research evidence is an input only when the outcome needs it or relevant Research must be reconciled.

## Required outputs

A scoped `CANON_FREEZE_RECORD` when authorized and ready, or an existing non-frozen verdict with the actual blocker or missing authority.

Adapted from source `canon-freeze`, with maturity-specific Project Resolver semantics.

## Procedure

1. Lock exact candidate, target scope, validation result and requested maturity.
2. Reject stale/mismatched validation or any blocking finding.
3. Require explicit authority for the state transition.
4. For `CANON_FOUNDATION_0_X`, allow explicit assumptions/unknowns/contradictions that are recorded as unresolved and do not misrepresent research completion.
5. For `CANON_1_0`, disposition consequential unknowns and genuine blockers against the declared outcome/freeze scope. If Research was needed or relevant Research exists for that outcome, require its current reconciliation through the existing authority boundary; unresolved required evidence remains a blocker. If no Research was needed and none applicable exists, require neither Research nor a fabricated reconciliation. Retain nonblocking or out-of-scope unknowns only as allowed by existing authority.
6. For `CANON_2_0`, require current final production-era reconciliation.
7. Freeze only the declared scope; partial freeze is valid.
8. Emit envelope-compatible `CANON_FREEZE_RECORD` with exact state ref, scope, authority, unresolved-but-permitted items and downstream authorization.
9. If an already-authorized resulting state is designated current, follow `Current Canon carrier continuity` in `engines/canon/docs/CANON_AUTHORITY.md` for the existing carrier. The freeze record itself does not designate current Canon.

## Verdict

`FROZEN`, `READY_BUT_NOT_AUTHORIZED`, or `BLOCKED`.

Freeze means stability, not maximal detail. Do not fabricate Research, ignore needed findings, treat a working proposal as accepted, or ask again for an applicable decision already authorized.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon state transition over an exact supplied candidate and authority artifact.

**Conditional / optional capabilities:** none by default; external state acquisition is a separately declared prerequisite.

**Mandatory evidence path:** emit `CANON_FREEZE_RECORD` with common envelope, exact state ref, maturity, scope, and authority ref when frozen.

Without proven durable output capability or required authority/upstream state, do not spawn or freeze; use `ASSIGNMENT_NOT_ADMISSIBLE` for destination capability failure.
