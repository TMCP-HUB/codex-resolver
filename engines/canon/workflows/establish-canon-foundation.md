# Workflow: Establish Canon Foundation

**Workflow ID:** `establish_canon_foundation`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/establish-canon-foundation/SKILL.md`
  - `engines/canon/skills/validate-canon/SKILL.md`
- optional_skills: registration skills and `freeze-canon` only when the exact assignment requires them.

Neither role acquires Owner/K0 authority by executing or consuming this workflow.

## Entry

- exact assignment and state identity are known;
- explicit Owner/K0 intent or another authorized Foundation input exists with relevant provenance. Available Foundation working artifacts may inform the candidate but do not themselves confer acceptance authority;
- requested output is Canon Foundation, not Production Foundation;
- destination assignment is admissible under the generic Resolver execution chain.

## Procedure

1. Assemble only the relevant exact state slice and authorized inputs. When available, pass the existing `PROJECT_SEED`, `PROJECT_OUTCOME`, `CONSEQUENTIAL_UNKNOWN_MAP`, original Owner decisions and supporting source refs; do not create them solely to satisfy this handoff.
2. Run `establish-canon-foundation` to map the relevant material into a project-neutral 0.x candidate. Preserve explicit Owner statements and existing decisions separately from interpretations/proposals; map relevant unresolved questions with their actual scope, source and blocker status. Use the outcome as context, not automatic Canon.
3. Use bounded registration skills only when the assignment requires their semantic operation. Preserve source/authority refs using the existing artifact envelope and schema; do not invent a new handoff form or authority record.
4. Reuse an already-authorized decision within its actual scope without reapproval. Classify other inferences as proposed, never accepted merely because a working artifact contains them; stop only for a real missing authority or blocker for the requested transition.
5. Run mandatory `validate-canon` on the exact candidate.
6. If the assignment explicitly authorizes a 0.x freeze, load and run `freeze-canon`; otherwise do not infer freeze authority.
7. Emit durable envelope-compatible `CANON_FOUNDATION` and any explicitly authorized `CANON_FREEZE_RECORD`.
8. If this project uses a repository `PROJECT_INDEX` and the already-authorized transition designates a current Canon, update its existing `Current Canon` entry to that designated carrier reference while preserving the remaining index content. A proposal, draft or freeze record is not automatically current; the pointer is navigation, not authority. Do not repeat an accepted decision or require a repository for other projects.

## Stop

Stop for conflicting protected Owner intent, missing authority for acceptance/freeze, unresolved mandatory dependency, or attempted silent replacement of frozen Canon.
