---
name: validate-canon
description: Validate exact Canon structure, stable identity, authority/provenance, contradiction and maturity readiness without granting acceptance or independent verification authority.
---

# Validate Canon

## Purpose and goal

Assess the exact Canon candidate's structure, provenance, authority, conflicts and maturity readiness without granting acceptance or independent verification.

## When to use and inputs

Use when an assigned Canon candidate needs internal validation. Take its identity, declared outcome/scope, applicable authority and relevant evidence; Research is conditional on that outcome.

## Required outputs

The existing internal validation result and findings for the exact candidate, including any genuine blockers and evidence limitations.

Adapted from source `canon-validator`, `canon-acceptance-tests`, and `contradiction-audit`.

## Checks

1. Exact artifact identity/version/scope is known.
2. Schema/required fields are structurally valid where a schema applies, including the common Project Resolver artifact envelope.
3. Stable IDs are unique; dependencies resolve or are explicitly external.
4. Fact/assumption/unknown/ambiguity/contradiction types are not blurred.
5. Accepted/frozen claims carry explicit authority/provenance.
6. Equal accepted conflicts are blocking unless explicitly scoped/intentional.
7. Intended ambiguity has explicit preservation law.
8. Maturity gate is coherent:
   - 0.x may retain explicit unknowns/assumptions;
   - 1.0 requires disposition of consequential unknowns and blockers for the declared outcome/freeze scope. Reconcile relevant Research when it was needed or exists for that outcome; missing necessary evidence remains blocking. If no Research was needed and none applicable exists, do not require a Research release or reconciliation; preserve nonblocking unknowns only as allowed by existing authority;
   - 2.0 requires current final reconciliation.
9. Freeze metadata matches actual frozen scope.

## Verdict

`PASS`, `PASS_WITH_FINDINGS`, or `BLOCKED`.

A PASS is internal Canon validation only. It does not itself grant Owner acceptance, freeze authority, or independent Verification Engine proof. Do not infer acceptance from working artifacts, ignore relevant Research or invent a Research stage.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound internal Canon validation over exact supplied/current Canon artifacts.

**Conditional / optional capabilities:** schema/runtime tooling may be declared by a selected assignment when mandatory, but this skill does not imply shell, network, repository, or independent Verification access by default.

**Mandatory evidence path:** emit a durable internal Canon validation result/findings artifact with exact candidate identity and common envelope/provenance bindings.

Missing mandatory destination capability means `ASSIGNMENT_NOT_ADMISSIBLE`. Internal validation never mutates Canon and never substitutes for independent Verification.
