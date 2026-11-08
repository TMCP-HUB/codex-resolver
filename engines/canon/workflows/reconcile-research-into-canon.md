# Workflow: Reconcile Research Into Canon

**Workflow ID:** `reconcile_research_into_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/reconcile-research-into-canon/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`
- optional_skills: bounded registration skills and `freeze-canon` only when authorized.

## Entry

- exact current `CANON_FOUNDATION` or `CANON_STATE` ref;
- exact Research release/findings with provenance;
- reconciliation scope and authority boundary;
- destination assignment is admissible.

## Invariant

`RESEARCH → EVIDENCE/FINDINGS → CANON RECONCILIATION → ACCEPTED CANON`.

A Research finding is never accepted Canon merely because Research supports it.

The reconciliation disposition contract is exactly:
`ACCEPT_ADD_PROPOSAL`, `REJECT_PROPOSAL`, `RETAIN`, `SUPERSEDE_PROPOSAL`,
`CLOSE_UNKNOWN_PROPOSAL`, `RETAIN_UNKNOWN`, `PRESERVE_AMBIGUITY`,
`REGISTER_CONTRADICTION`, `REQUIRE_OWNER_DECISION`, `DEFER_OUT_OF_SCOPE`.
Producer, schema and template surfaces must use this same vocabulary.

## Procedure

1. Lock exact current Canon and upstream Research identities.
2. Run `reconcile-research-into-canon` and construct envelope-compatible reconciliation/change-proposal candidates using only the declared disposition contract.
3. Structurally validate each candidate before durable output. Proposal/retain/defer/classification results remain non-accepted unless explicit acceptance is actually selected.
4. Before durably materializing any `status: ACCEPTED` `CANON_RECONCILIATION_RESULT` or `CANON_CHANGE_PROPOSAL`, call `guard_mutation_materialization()` from `engines/canon/tools/mutation_authority.py` with workflow id `reconcile_research_into_canon` and the governed supplied artifacts.
5. Only a `PROVEN` gate result may be written as `ACCEPTED` or applied into resulting Canon state. A rejected gate is a controlled blocker; never downgrade or bypass it. A `NOT_REQUIRED` result is valid only for non-accepted output.
6. Preserve the validated authority ref in the accepted artifact and include that authority plus the exact source Canon target in `related_artifacts`.
7. Run mandatory `validate-canon` on any resulting exact candidate.
8. Route to `validate_and_freeze_canon` only when freeze authority and maturity prerequisites are separately present.

## Stop

Stop on protected Owner conflict, equal-authority conflict, unsupported stronger claim, missing mutation authority for an accepted change, or unresolved mandatory upstream evidence. Preserve UNKNOWN/AMBIGUITY/CONTRADICTION rather than manufacturing closure.
