# Workflow: Form Project Foundation

**Workflow ID:** form_project_foundation

## Role contract

- executing_role: `roles/executor/ROLE.md`
- consuming_role: `roles/control-director/ROLE.md`
- required_skills:
  - `engines/foundation/skills/develop-project-seed/SKILL.md`
  - `engines/foundation/skills/define-project-outcome/SKILL.md`
  - `engines/foundation/skills/classify-consequential-unknowns/SKILL.md`
  - `engines/foundation/skills/plan-project-topology/SKILL.md`
- optional_skills:
  - `engines/foundation/skills/design-discovery/SKILL.md` only when exploration materially improves the working project definition.

## Entry

- Liaison selected ROUTE for governed project formation;
- exact Owner material/provenance, assignment identity and destination executability are established;
- durable system of record and capabilities for bootstrap/readback are declared.

## Required durable outputs and sequencing

The assignment-declared required_durable_outputs must include:
- PROJECT_SEED
- PROJECT_OUTCOME
- CONSEQUENTIAL_UNKNOWN_MAP
- TOPOLOGY_PLAN
- PROJECT_TOPOLOGY_BOOTSTRAP (one logical transaction containing TOPOLOGY_MANIFEST, PROJECT_INDEX and minimal structural shell)

The first four are non-authoritative WORKING bootstrap/control state. They MAY materialize before topology admission without circularity. Their durable_output_refs must be independently read back through the existing generic durable-output/readback contract.

The fifth output is an atomic logical bootstrap package persisted through the same generic durable port. A local/session copy and a bare artifact ref do not prove completion. The package has a root index, declared semantic namespaces, bounded namespace navigation indexes and minimal structural shell. It MUST be independently read back and passed through tools.project_topology.verify_bootstrap (cold-start navigation proof) before TOPOLOGY_ADMITTED. For a real provider, exact physical index/shell materialization and its independent readback must also be proven when required; a reference-backend logical shell is not a claim that GitHub or Drive directories were created.

FOUNDATION_READY_FOR_OWNER_GATE requires durable coverage, independent readback of all declared outputs, independently verified topology/cold-start navigation, and any assignment-required provider physical shell proof. Missing evidence yields a bounded blocker, not readiness. The status does not create Owner/K0 authority and it does not create Canon authority.

## Procedure

1. Consume bounded Liaison routing frame, exact Owner material and relevant admitted state.
2. Use develop-project-seed to preserve explicit Owner statements separately from model interpretation, proposals and unresolved questions.
3. Use define-project-outcome to define required outcome and whether downstream realization is needed, without presuming software.
4. Use optional design-discovery only when materially useful.
5. Use classify-consequential-unknowns; classification is not Research dispatch or fact resolution.
6. Reconcile PROJECT_SEED, PROJECT_OUTCOME and CONSEQUENTIAL_UNKNOWN_MAP as working artifacts.
7. Use plan-project-topology to derive minimal semantic classes, project-specific namespaces and navigation indexes from the actual outcome; no fixed folder template or agent/date/run directory.
8. Produce TOPOLOGY_PLAN as WORKING/non-authoritative and verify against topology-plan schema.
9. Build and materialize a single PROJECT_TOPOLOGY_BOOTSTRAP through the existing durable materialization/readback surface. Its contents are TOPOLOGY_MANIFEST, PROJECT_INDEX and the minimal structural shell. Do not admit project payload yet.
10. Require independent readback and cold-start proof from the root index to each namespace index, current Canon pointer (which may be explicitly unset before Owner gate), and required workstream locations. No global search or file-by-file enumeration.
11. Reconcile required_durable_outputs with exact durable_output_refs and independent readback proofs. A failed bootstrap or missing physical materialization proof MUST leave downstream payload blocked.
12. Only after full completion return FOUNDATION_READY_FOR_OWNER_GATE and STOP. Do not execute Owner Foundation Gate, Canon acceptance/mutation, Research dispatch or Production.

## Existing handoff when Canon is requested

Return the relevant existing `PROJECT_SEED`, `PROJECT_OUTCOME` and `CONSEQUENTIAL_UNKNOWN_MAP` references, their provenance and applicable already-recorded Owner decisions to Control for the existing `establish_canon_foundation` route. Pass the actual state and source refs, not a new handoff form. These are working inputs: their presence neither accepts their contents as Canon nor grants mutation or freeze authority. Reuse existing applicable Owner authorization rather than asking again; preserve any genuinely unresolved authority or outcome blocker. If Canon formation is not requested, do not start it merely because these artifacts exist. This does not impose full Foundation formation on an already-authorized bounded task.

## Persistent project payload law (later stages)

BOOTSTRAP / CONTROL STATE != PROJECT PAYLOAD.

Research findings, sources, evidence, decisions, Canon, long-lived production/runtime payload and archives MUST resolve a semantic class and scope against the current admitted topology before persistent materialization. The worker's pathname is not authority. Use tools.project_topology.materialize_project_payload as the provider-neutral semantic pre-write front door, and the existing durable port for physical bytes/readback. Unknown class, missing scope, ad hoc top-level path or unverified topology yields TOPOLOGY_CHANGE_REQUIRED or fail-closed equivalent.

Later writers must re-resolve every project payload address (anti-entropy); topology admission is not a one-time exemption. TOPOLOGY_EXTENSION adds an admitted semantic namespace. TOPOLOGY_REPLACEMENT replaces existing canonical addresses only after the existing Owner architecture choice PRESERVE/MIGRATE vs DESTRUCTIVE CUTOVER, migration/readback proof, index/ref reconciliation and retirement of the old-current topology. No parallel current realities.

## Cognitive and stop boundary

This workflow is guidance-first. Zero clarification questions is valid; no fixed questionnaire is imposed. The bootstrap is not authoritative Canon. On missing provenance, executability, durable readback, cold-start navigation or legitimate topology-change authority, STOP with the smallest bounded blocker. No second Engine, filesystem manager or Foundation-specific spawn runtime is introduced.
