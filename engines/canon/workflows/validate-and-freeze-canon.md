# Workflow: Validate and Freeze Canon

**Workflow ID:** `validate_and_freeze_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/validate-canon/SKILL.md`
  - `engines/canon/skills/freeze-canon/SKILL.md`

Internal Canon validation is not independent Verification Engine authority, and Verification cannot mutate Canon state.

## Entry

Exact candidate identity, maturity, target scope and explicit freeze authority must be bound before this workflow is executable.

## Procedure

1. Lock exact candidate identity/version and target scope.
2. Run `validate-canon`.
3. If validation blocks, emit findings and stop without mutation.
4. If freeze authority is missing or invalid, do not run freeze; return the appropriate non-frozen result.
5. Run `freeze-canon` only under exact authority and maturity prerequisites.
6. Emit envelope-compatible `CANON_FREEZE_RECORD` and the exact resulting Canon ref.

## Exit

A freeze is scoped stability, not maximal specification, release authority, or permission for silent later mutation.
