---
name: register-contradiction
description: Register the smallest conflicting Canon proposition set with scope, authority and blocker status instead of selecting a silent winner.
---

Adapted from source `contradiction-audit`.

## Classes

`DIRECT`, `TEMPORAL`, `IDENTITY`, `TERMINOLOGY`, `DEPENDENCY`, `INTENTIONAL_TENSION`, `SCOPED_APPARENT_CONFLICT`, `NONBLOCKING_DUPLICATION`, `NEEDS_AUTHORITY`.

## Procedure

1. Lock exact involved Canon IDs/versions/scopes.
2. Compare proposition meaning, not wording alone.
3. Test scope, time, audience and condition before declaring a conflict.
4. Record evidence/provenance and authority status for each side.
5. Mark the conflict blocking when incompatible accepted/frozen authority remains unresolved.
6. Never auto-select newer/last-read/more convenient authority.
7. Route accidental conflict to change/reconciliation; preserve explicitly intended/scoped tension as such.

# Output

Durable contradiction record plus required next authority/action.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon registration over supplied exact state.

**Conditional / optional capabilities:** none by default.

**Mandatory evidence path:** write the contradiction record into an envelope-compatible Canon artifact with exact involved refs, provenance, blocker state, and authority status.

Missing mandatory durable output capability means `ASSIGNMENT_NOT_ADMISSIBLE`.
