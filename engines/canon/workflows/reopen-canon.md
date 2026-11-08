# Workflow: Reopen Canon

**Workflow ID:** `reopen_canon`

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/canon/skills/reopen-canon/SKILL.md`
- optional_skills:
  - `engines/canon/skills/validate-canon/SKILL.md`

## Entry

Exact frozen Canon ref, explicit reopen authority, reason, impact scope and post-2.0 lifecycle mode when applicable are required.

## Procedure

1. Run `reopen-canon` against the exact frozen state and authority.
2. Preserve historical frozen state; create a new version lineage rather than rewriting history.
3. Record prior ref, reason/evidence, scope, downstream impact and revalidation obligations.
4. Route substantive changes through normal Canon registration/reconciliation/change-classification workflows.
5. Validate/freeze the new lineage only in a later separately authorized gate.

When the project uses a repository current Canon carrier, retain its declared address for ordinary revision, freeze and reopen. If an authorized transition updates that carrier, use the existing exact-reference update and preserve `history_refs`; an open/proposed state does not become current merely by reopening. A change of carrier address or authority is a distinct action governed by its applicable existing authorization, not a consequence of a new version.

## Stop

No silent retcon, history rewrite, or authority inference from edit access.
