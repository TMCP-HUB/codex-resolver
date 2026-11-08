---
name: register-unknown
description: Make unresolved project knowledge or decisions explicit without converting absence of knowledge into Canon truth or intended ambiguity.
---

Adapted from the unknown side of source `ambiguity-ledger` and `SEED_CANON_MODEL`.

## Procedure

1. State the unresolved question/dimension precisely.
2. Record stable ID, scope, why it matters, provenance and whether it blocks the current gate.
3. Record expected resolution path: Research, Owner decision, production discovery, external dependency, or unknown.
4. Link dependent facts/assumptions/decisions where useful.
5. Keep it `UNKNOWN` until an explicit reconciliation/decision closes it.
6. A Foundation 0.x freeze may preserve an unknown as unresolved state; never rewrite the unknown as an answer.

## Route elsewhere

If authority explicitly chooses to preserve multiple readings, use `register-ambiguity`. If incompatible accepted claims exist, use `register-contradiction`.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon registration over supplied state/authority.

**Conditional / optional capabilities:** none by default. Research or external dependency execution is not implied by recording an unknown.

**Mandatory evidence path:** write the unknown record into an envelope-compatible Canon artifact with exact provenance, blocker state, and resolution path.

Missing mandatory durable output capability means `ASSIGNMENT_NOT_ADMISSIBLE`.
