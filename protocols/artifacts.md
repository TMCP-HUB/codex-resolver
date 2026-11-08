# Common Artifact Protocol

The legacy software sequence `PLAN → IMPLEMENTATION → QA → REVIEW → MERGE` is not a universal system law. Engines may define such a workflow locally.

## Ownership

A **PRIMARY ARTIFACT** is produced by the role that created the underlying knowledge/work. A **DERIVED ARTIFACT** is computed or summarized from primary artifacts and must retain provenance to them.

There is no universal Artifact Agent. Artifact production is role-native.

## Required common artifact types

- `CAPABILITY_PROFILE` — freshness-bounded evidence of concrete execution surfaces available to one exact destination/runtime instance; it carries no authority by itself.
- `COMPILED_ASSIGNMENT` — normalized authority/movability, context-fact authority, responsibility, evidence, envelope, mandatory-action, and capability semantics authorized by deterministic Control-layer compilation.
- `ASSIGNMENT_ADMISSIBILITY` — pre-assignment control proof comparing mandatory required capabilities/evidence paths with one exact destination capability profile.
- `ASSIGNMENT` — bounded instruction for current work; executable only when its destination-bound execution contract cites an `ADMISSIBLE` proof and contains no unsatisfied required capability. It may declare `required_durable_outputs` as unique opaque assignment-local output identities; when that list is non-empty it also declares the opaque `durable_system_of_record_ref` from which those outputs must be independently read back.
- `EXECUTOR_RESULT` — what the Executor actually did, resulting state, evidence refs, limitations/deferred findings. `durable_output_refs`, when present, bind assignment-declared required durable output identities to opaque non-blank artifact refs; `COMPLETE` requires full unique coverage of those declared identities.
- `VERIFICATION_RESULT` — independent claim-by-claim verification of an exact result/candidate. For assignments with required durable outputs, `CONFIRMED` additionally carries `durable_readback_proofs` whose assignment/output/system-of-record/ref/content-digest identity must exactly match Control's independent #56-B readback observations.
- `DIRECTOR_DECISION` — admissible next transition selected from current state plus relevant results.
- `OWNER_DECISION_RECORD` — durable materialization of an Owner/K0 choice.
- `STATE_MUTATION_PROPOSAL` — requested governed state change before authority acceptance.
- `HANDOFF` — bounded continuation transfer between role instances.

## Engine-owned Foundation working artifacts

The Foundation Engine owns three original cognitive working-state artifact types: `PROJECT_SEED`, `PROJECT_OUTCOME`, and `CONSEQUENTIAL_UNKNOWN_MAP`. The topology increment adds non-authoritative `TOPOLOGY_PLAN` and one logical `PROJECT_TOPOLOGY_BOOTSTRAP` containing a topology manifest, root project index and minimal structural shell. The latter is bootstrap/control material, not admitted downstream project payload.

They use the common artifact identity/provenance envelope and the ordinary durable-output/readback path, but they are **not** universal required common artifact types and are explicitly non-authoritative working state. Their durability preserves project-formation continuity; it does not create Owner/K0 authority, Canon truth, Research evidence, or Production authority.

## Semantic topology admission before persistent project payload

Bootstrap/control state (seed, outcome, unknowns, topology plan and topology bootstrap) may be durably recorded before topology admission. No persistent research, Canon, production, project decisions, media or long-lived runtime payload is admitted by its mere appearance in generic durable storage.

Foundation forms a project-specific semantic topology; every subsequent persistent project payload write must resolve its semantic class, project scope and canonical address from current independently read-back topology before calling the existing durable port. The shared bounded resolver is `tools/project_topology.py`; it is not a new storage engine or replacement of the #56 port. A bare pathname supplied by a worker, prompt, task or issue grants no write authority. Unsupported semantic classes/scopes require a topology change, not ad hoc directories. Root index and nested namespace indexes must support cold-start navigation without global search.

Topology extension and replacement are different authority classes. Replacement requires existing Owner architecture migration/cutover authorization, verified migration, refreshed indexes and old current topology retirement before a successor becomes current. The reference port proves logical durable bootstrap, not real-world provider-specific directory/file realization; assignments requiring GitHub/Drive physical structure must verify that separately.

The Foundation bootstrap uses the declared output identity `foundation:topology-bootstrap`, so the topology bundle itself reconciles through generic durable readback. Payload write success additionally requires exact system-of-record, identity, bytes and digest readback. Resolver payload bindings preserve project identity and semantic scope for executors to re-resolve at writing time. Repository namespace indexes distinguish scoped canonical addresses; authorized updates require the exact current artifact reference, retain superseded durable references in `history_refs`, and preserve the canonical address. This reference precondition is not Owner or Canon mutation authority.

## Identity and provenance

Every artifact has a stable `artifact_id`, `artifact_type`, `produced_by_role`, `assignment_id` where applicable (nullable for pre-assignment artifacts), `input_state_ref`, `status`, `provenance/created_from`, and `related_artifacts`.

Derived artifacts must not erase source identity. A summary cannot silently replace a primary result when the downstream decision requires the primary result.

`CAPABILITY_PROFILE` must identify the exact destination/runtime and freshness boundary. `ASSIGNMENT_ADMISSIBILITY` must bind the assignment draft, exact compiled assignment, destination, and exact capability profile used in the subset decision. An `ASSIGNMENT` must preserve those refs in its execution contract.

For durable completion, reference coverage and readback are distinct gates. `EXECUTOR_RESULT.durable_output_refs` proves only the A1 mapping. Control independently invokes the provider-neutral #56-B durable port using the assignment's exact `durable_system_of_record_ref` and each exact returned artifact ref. A resolved readback is accepted only when its system-of-record identity, artifact ref, output identity, SHA-256 content identity, and payload all correspond to that exact binding. Executor/session/local copies are not an alternative read source and cannot satisfy this gate.

The Verifier does not authenticate to storage or choose a provider. It consumes the exact independently read-back object and reports `durable_readback_proofs` identifying the exact assignment, output id, system of record, artifact ref, content digest, and `RESOLVED` status that it evaluated. Control matches those proofs against its independent readback observations before honoring `CONFIRMED`. Availability/readback proof remains separate from factual claim verification: a readable artifact can still yield `QUALIFIED`, `NOT_PROVEN`, or `BLOCKED`.

## Pre-assignment executability separation

`ASSIGNMENT_ADMISSIBILITY != VERIFICATION_RESULT`.

Admissibility establishes only that the destination can execute/prove the mandatory assignment requirements at dispatch time. It does not establish that the work succeeded, that the candidate is correct, or that acceptance is satisfied.

Known missing capability before dispatch yields `ASSIGNMENT_NOT_ADMISSIBLE` and no executable assignment. Loss of a previously proven capability after dispatch is runtime drift and may yield `BLOCKED_RUNTIME_DRIFT` from the active role.

## Execution and verification separation

`EXECUTOR_RESULT != VERIFICATION_RESULT`.

The Executor owns truthful reporting of performed work; the Verifier owns independent assessment of claims. A Verifier report must not rewrite or replace the Executor result. Where verification is required, Control Director receives **both** artifacts. For required durable outputs, the Verifier's target is the exact independently read-back payload/identity, not an Executor-provided local copy.

## Artifact versus evidence

Artifacts can contain evidence references, but artifact existence is not proof. Evidence must be evaluated against the exact claim, state, method, and trust boundary described by the evidence contract. A capability profile is evidence about the runtime surface only; it is neither authorization nor proof of task completion.

# Executability evidence and route trust boundary

`CAPABILITY_EVIDENCE` is structurally valid only when its common artifact identity, runtime, unique non-empty proven capabilities, observation/validity timestamps, observation method, provenance, and created-from lineage are complete. Structural validity is distinct from authoritative resolution: an embedded object cannot resolve itself. `EXECUTION_ROUTE` binds an assignment draft to candidate delivery, execution/verification, and durable evidence/control through capability-proven logical segments and ordered edges. Cross-surface handoffs prove export and receive sides independently; same-surface handoffs prove exact runtime equivalence and any actual internal transfer. For a known same-actor continuation in one live session, the existing route may record Director's factual assessment under `contracts/EXECUTABILITY_CONTRACT.md`; that field is not identity attestation or independent verification. Assignment and admissibility artifacts cite its exact identity, the execution segment equals their admitted execution identity, and the structured final-result reference resolves to the durable segment whose destination equals `ASSIGNMENT.result_to`.
