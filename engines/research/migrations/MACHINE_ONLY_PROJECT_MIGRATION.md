# Existing Research Project Migration — Machine-Only Remediation

Status: ACTIVE MIGRATION PROCEDURE

For every project using Research Engine:

1. Inspect active research architecture, plans, questions, work packages, methods, experiments, roles, prompts, templates, and pending collection runs.
2. Classify every human-related reference as `ACTIVE_DEPENDENCY`, `HISTORICAL_REFERENCE`, `STATIC_EXTERNAL_SOURCE`, `EXPLICIT_PROHIBITION`, or `OWNER_AUTHORITY`.
3. Preserve stable IDs and historical provenance.
4. Supersede active non-owner human dependencies; do not rewrite history.
5. Cancel or retire unexecuted project-generated human collection runs without executing them.
6. Retain legitimate pre-existing external human-derived evidence as source provenance.
7. Replace prohibited active methods with machine-accessible evidence, corpus/computational/model proxies, simulation, structural/typological analysis, or explicit unknown/insufficient-evidence outcomes.
8. Convert generic human authority gates to explicit `OWNER_*` gates where Owner/K0 authority was intended.
9. Mark direct human constructs as unmeasured when no valid machine measurement exists.
10. Validate every active question and work package with `tools/research_policy.py`.
11. Run repository policy lint and regression tests.
12. Migration passes only when required non-owner humans, Owner manual research labor, external human review, active human collection paths, and ambiguous generic human authority gates must be zero.

Already-collected historical project-generated human data remains historical lineage and is classified accurately. The new default prevents NEW generation unless Owner/K0 separately creates an exact bounded human-research workstream.
