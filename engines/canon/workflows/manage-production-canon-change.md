# Workflow: Manage Production-Time Canon Change

**Workflow ID:** `manage_production_canon_change`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/classify-canon-change/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`

Production observations may expose a Canon gap. Software or production execution cannot self-certify Canon truth.

## Procedure

1. Lock current Canon version, production state and exact observed signal.
2. Run `classify-canon-change`.
3. Construct an envelope-compatible `CANON_CHANGE_PROPOSAL` with impacted Canon refs, evidence refs, requested authority and downstream revalidation; classification/proposal output remains non-accepted by default.
4. Apply A/B/C/D gate semantics conservatively; C pauses affected production and D is a controlled authority stop.
5. Before durably materializing a `status: ACCEPTED` `CANON_CHANGE_PROPOSAL`, call `guard_mutation_materialization()` from `engines/canon/tools/mutation_authority.py` with workflow id `manage_production_canon_change` and the governed supplied artifacts.
6. Only a `PROVEN` gate result may be written as `ACCEPTED` or applied into resulting Canon state. A rejected gate is a controlled blocker; `NOT_REQUIRED` applies only to non-accepted classification/proposal output.
7. Preserve the validated authority ref in `authority_ref` and include that authority plus the exact prior Canon target in `related_artifacts`.
8. Run mandatory `validate-canon` on any authorized resulting Canon candidate.
9. Return exact changed/unchanged state and revalidation obligations to the Control Director.

## Stop

No class permits mutating Canon merely to match code, a bug, draft, translation, test, or convenient implementation.
