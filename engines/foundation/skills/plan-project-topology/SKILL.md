---
name: plan-project-topology
description: Form a bounded semantic navigation topology before persistent project content, without granting Canon or storage-path authority to the producing model.
---

# Plan Project Topology

## Execution contract

Foundation plans one non-authoritative TOPOLOGY_PLAN from the working seed, outcome and consequential unknowns. The selected project system of record must support durable_artifact_write and independent readback. Reuse the existing generic durable port and Resolver execution/admissibility chain, not a second runtime.

The bootstrap/control outputs PROJECT_SEED, PROJECT_OUTCOME, CONSEQUENTIAL_UNKNOWN_MAP and TOPOLOGY_PLAN may exist before topology admission. Persistent project payload may not.

## Thinking guidance

Use native model reasoning to choose the smallest useful semantic navigation layout for this particular project. The same semantic classes can be physically organized differently for document-only, repository-only, mixed, research and media projects.

Choose one of DRIVE_ONLY, REPO_ONLY or DRIVE_THEN_REPO when warranted by the actual outcome and available durable systems. A project requiring code realization must have a repository before code realization. The storage choice does not silently change Canon authority or initiate a Drive/repository cutover.

Build from semantics: SOURCE, EVIDENCE, FINDING, PROJECT_DECISION, CANON, RUNTIME, ARCHIVE where applicable, extending with project-specific classes as necessary. Do not create all of them when unused. Give each admitted class a canonical namespace, a bounded index entrypoint and a deterministic scope key if needed. Zero clarification questions remains valid when the Owner intent and storage context are sufficient.

## Hard invariants

- No persistent project payload before independently proven topology admission.
- No LLM, issue, or worker-proposed pathname is itself storage authority.
- ROOT_IS_ROUTER; PARENT_BEFORE_CHILD; EVERY_ARTIFACT_HAS_A_CLASS; NO_AD_HOC_TOP_LEVEL; PROGRESSIVE_DISCLOSURE; SEMANTICS_OVER_PROVENANCE.
- Foundation bootstrap is WORKING and does not create Owner/K0 or Canon authority.
- Reuse existing durable materialization/readback; one logical bootstrap bundle must contain the topology manifest, project index and minimal shell.
- Before every later payload write, resolve its address again from admitted semantic class and scope.
- A topology extension is not a replacement. Replacing any current canonical namespace needs the existing Owner architecture replacement choice: PRESERVE/MIGRATE or DESTRUCTIVE CUTOVER, verified migration/readback, and old-current retirement. Do not create parallel current layouts.
- Do not organize persistent namespaces by producing agent, date, task run or arbitrary history by default.

## Procedure

1. Identify only project payload classes that matter for the declared outcome and foreseeable next work.
2. Produce TOPOLOGY_PLAN with explicit project identity, storage mode, semantic namespaces, namespace indexes, scope keys, and root index; mark it WORKING and non-authoritative.
3. Use tools.project_topology.build_bootstrap to derive one logical bootstrap of PROJECT_INDEX, TOPOLOGY_MANIFEST and the minimal structural shell.
4. Materialize this bootstrap through the existing durable port and retain its exact durable ref. Do not treat the returned ref as admission proof.
5. Independently read it back through verify_bootstrap and perform cold-start navigation from the root index without global search or directory enumeration.
6. If readback, semantic navigation, or physical provider realization required by the assignment is missing, report an exact blocker; do not claim FOUNDATION_READY_FOR_OWNER_GATE.
7. Route all subsequent permanent payload through materialize_project_payload (the semantic pre-write adapter to the existing durable port), deriving the address from current admitted topology.

## Stop condition

Stop at a verified, minimal navigable topology or a bounded blocker. Do not execute the Owner Foundation Gate, accept Canon, dispatch Research, or enter Production.
