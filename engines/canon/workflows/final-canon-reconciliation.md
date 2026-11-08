# Workflow: Final Canon Reconciliation

**Workflow ID:** `final_canon_reconciliation`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/validate-canon/SKILL.md`
  - `engines/canon/skills/freeze-canon/SKILL.md`
- optional_skills:
  - `engines/canon/skills/classify-canon-change/SKILL.md`

## Entry

Exact Canon 1.x state, exact production-era change records and explicit final Canon authority are required.

## Procedure

1. Lock Canon 1.x state and accepted production-era Canon change records.
2. Reconcile accepted outcomes, unresolved proposals, preserved ambiguities/contradictions and explicit final decisions into an envelope-compatible reconciliation result and Canon 2.0 candidate.
3. Reject implementation-only facts that never received Canon authority.
4. Run mandatory `validate-canon`.
5. Run mandatory `freeze-canon` as `CANON_2_0` only under the bound final Canon authority.

## Boundary

This closes Canon truth state. It does not grant generic product/release verification authority.
