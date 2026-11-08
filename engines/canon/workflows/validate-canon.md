# Workflow: Validate Canon

**Workflow ID:** `validate_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/validate-canon/SKILL.md`
- optional_skills: []

Internal Canon validation is read-only with respect to Canon state. It is not independent Verification Engine authority and does not grant acceptance or freeze authority.

## Entry

- exact Canon candidate ref;
- relevant state slice and ordinary assignment authority;
- destination assignment is admissible.

`explicit_freeze_authority` is not an entry requirement for this workflow because no freeze mutation is performed.

## Procedure

1. Lock exact candidate identity/version/scope.
2. Run `validate-canon` only.
3. Emit durable internal validation findings/verdict bound to the exact candidate.
4. Do not run `freeze-canon`, change Canon status, create a freeze record, or otherwise mutate Canon.
5. If a later assignment requests freeze, route separately to `validate_and_freeze_canon`, where explicit freeze authority is mandatory.

## Exit

Return internal Canon validation evidence and the unchanged exact Canon candidate ref.

## Stop

Stop if the exact candidate is unresolved or mandatory validation inputs/capabilities are unavailable. Validation failure emits findings; it does not authorize repair or mutation by itself.
