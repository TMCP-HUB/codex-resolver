---
name: reopen-canon
description: Reopen an exact frozen Canon scope only under explicit authority and preserved version lineage; post-2.0 requires a declared lifecycle mode.
---

# Procedure

1. Verify exact frozen state and requested scope.
2. Require explicit reopen authority and reason.
3. Preserve the historical frozen artifact; create a new working lineage/version rather than rewriting history.
4. Record downstream impact and revalidation obligations.
5. After 2.0 require `ADDENDUM`, `EXPANSION`, `NEW_EDITION`, or `REOPEN`.
6. Return the new proposed/open state plus required next workflow; do not silently apply substantive changes inside this skill.

# Stop

Stop on missing authority, ambiguous target state, or an attempt to retcon history without provenance.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon transition over exact frozen state and exact reopen authority.

**Conditional / optional capabilities:** none by default; fetching unavailable state is a separate declared prerequisite.

**Mandatory evidence path:** emit the new lineage/open-state artifact with common envelope, exact prior-state ref, authority ref, reason, and downstream revalidation obligations.

Without required authority/upstream state do not execute; destination capability failure returns `ASSIGNMENT_NOT_ADMISSIBLE`.
