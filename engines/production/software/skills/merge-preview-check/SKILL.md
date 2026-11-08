# Merge Preview Check

## Purpose

Use this skill before calling a branch ready to merge.

## Goal

Reduce cases where branch-local verification passes but behavior changes after integration into the target branch.

## Questions to answer

- Has the target branch moved since the task began?
- Does the branch still cleanly map to the original scope?
- Could conflict resolution or upstream changes alter runtime behavior?
- Has verification been repeated after syncing with the target branch, when possible?

## Minimum output

Produce merge preview notes that state:

- target branch checked
- target SHA at check time
- sync method considered: merge or rebase
- whether post-sync verification exists
- residual integration risk

## Escalate risk when

- many shared files changed upstream
- config or dependency files changed upstream
- code relied on outdated assumptions
- only narrow happy-path checks were run

## Verdicts

Use one of:

- low merge risk
- moderate merge risk
- high merge risk

Never hide residual risk behind a positive summary.
