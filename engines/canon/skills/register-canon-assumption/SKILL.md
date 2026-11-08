---
name: register-canon-assumption
description: Register an explicit project assumption without laundering it into accepted factual truth.
---

# Inputs

Assumption proposition, reason, scope, provenance, risk if false, resolution path when known.

# Procedure

1. Confirm the proposition is being relied on without sufficient authority/evidence to call it a fact.
2. Assign/reuse a stable ID and affected scope.
3. Record why it is assumed, provenance, risk, dependent state and expected evidence/decision that could close it.
4. Record authority for using the assumption if required by the current gate.
5. Keep epistemic type `ASSUMPTION` even if the project explicitly accepts using it.
6. Emit downstream revalidation obligations if the assumption changes.

# Invariant

`accepted assumption record` means the project accepts relying on it as an assumption; it does not mean the proposition is accepted as factual Canon.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon registration over supplied state/authority.

**Conditional / optional capabilities:** none by default.

**Mandatory evidence path:** write the assumption record into an envelope-compatible Canon artifact preserving its epistemic type, provenance, and authority ref.

Missing mandatory durable output capability means `ASSIGNMENT_NOT_ADMISSIBLE`.
