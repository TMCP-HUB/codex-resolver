# Git Branch Integrity

## Purpose

Use this skill before major edits, during long-running branch work, before handoff, and before declaring a branch ready for review.

## Goal

Prevent branch-local success from hiding provenance, HEAD divergence, unintended scope, or merge-state problems.

This skill is Git-specific. Use `exact-state-verification` for the broader principle that evidence belongs to an exact artifact state.

## Capture at start

Record:

- repository;
- current working branch;
- target branch;
- base SHA;
- merge-base SHA;
- intended scope;
- expected files/systems touched;
- current workstream/issue.

## Track state identities

For non-trivial work, distinguish these identities when they exist:

- **working HEAD** — current branch commit being edited/tested;
- **intended HEAD** — commit the workstream claims should be reviewed/merged;
- **PR HEAD** — commit actually attached to the pull request;
- **reviewed HEAD** — commit for which review evidence was produced;
- **tested HEAD** — commit for which relevant CI/tests were produced;
- **target HEAD** — current target/base branch state when integration risk was checked.

They may all be equal. The important rule is that unexplained inequality is not ignored.

## Capture during work

Keep branch state updated with:

- current HEAD after meaningful commits;
- newly touched files;
- scope changes/refreeze events;
- blockers;
- assumptions;
- dependency on upstream changes;
- PR HEAD if a PR exists;
- latest reviewed/tested HEAD where relevant.

## Stop conditions

Treat these as stop conditions until explained:

- working HEAD differs from intended HEAD without an explicit reason;
- PR HEAD differs from intended reviewable implementation;
- reviewed/tested HEAD is older than material code changes but readiness still relies on that evidence;
- branch is built from an unexpected base/merge base;
- unrelated commits/files entered the branch;
- a detached commit/tree contains intended work but the branch ref does not;
- force-push/rebase changed provenance and old evidence is still being quoted as current.

Do not create another branch merely to hide unresolved divergence.

## Verify before sign-off

1. Confirm the current branch is the intended workstream branch.
2. Confirm current working HEAD equals intended HEAD.
3. If a PR exists, confirm PR HEAD equals intended HEAD.
4. Confirm review/test evidence applies to the current intended HEAD or explicitly document what changed afterward.
5. Confirm the branch diff still matches frozen scope.
6. Check whether target branch moved since work began.
7. Recompute merge base or compare state when target drift matters.
8. Note whether verification was branch-local only or repeated against synchronized/integrated state.
9. Confirm no detached/unpushed intended commit exists outside the branch ref.

## Decision rules

- Branch names are not evidence of content identity.
- PR presence does not prove PR HEAD is the commit you intended to review.
- A detached commit is not authoritative workstream state until the intended branch ref points to it.
- Review/test evidence becomes stale for affected claims after material HEAD changes.
- Target branch drift is a risk to assess, not automatic permission to rebase blindly.
- Force updates require explicit provenance review.

## Required caution

Do not say `ready to review` or `ready to merge` when the workstream cannot answer:

```text
What exact HEAD is intended?
What exact HEAD was reviewed?
What exact HEAD was tested?
What exact target state was integration risk checked against?
```

## Recommended artifact

Update `engines/production/software/templates/BRANCH_STATE.md` or equivalent with:

- base SHA;
- merge-base SHA;
- current working/intended HEAD;
- PR HEAD;
- reviewed HEAD;
- tested HEAD;
- target HEAD at last check;
- scope/diff summary;
- merge risk notes;
- verification status.

## Anti-patterns

Avoid:

- relying on an old CI run after HEAD moved;
- testing a detached commit while PR points elsewhere;
- using force-push to conceal confusing history without re-establishing evidence;
- saying "same branch" when the commit changed;
- merging unrelated upstream fixes into a frozen feature branch without scope review;
- opening duplicate PRs to manufacture fresh CI while losing track of authoritative HEAD.

## Pair with

- `exact-state-verification` for evidence binding beyond Git;
- `merge-preview-check` for target integration drift;
- `anti-loop-execution` when divergence becomes a stop condition;
- `proof-loop-verification` before completion claims.
