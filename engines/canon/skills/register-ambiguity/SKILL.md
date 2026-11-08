---
name: register-ambiguity
description: Register explicitly protected ambiguity while preventing ordinary indecision or accidental contradiction from being aestheticized or canonized.
---

Adapted from source `ambiguity-ledger`.

## Procedure

1. State the unresolved proposition and exact scope/audience.
2. Verify explicit authority intends non-resolution or multiple readings.
3. If the project simply has not decided, route to `register-unknown`.
4. If claims conflict accidentally, route to `register-contradiction`.
5. Record allowed readings only as far as authority supports them, forbidden collapses, and downstream preservation requirements.
6. Assign/reuse stable identity and provenance.
7. Accept/freeze the ambiguity only through governing Canon authority.

## Invariants

Implementation determinism cannot by itself create a canonical answer. Do not make allowed interpretations artificially exhaustive.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon registration over supplied state/authority.

**Conditional / optional capabilities:** none by default; no external acquisition is implied.

**Mandatory evidence path:** write the ambiguity record into an envelope-compatible Canon artifact with exact provenance and authority refs.

Missing mandatory durable output capability means `ASSIGNMENT_NOT_ADMISSIBLE`.
