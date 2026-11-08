# Common Project Resolver Contracts

These contracts define shared meanings. Engines may extend them but may not silently redefine them.

## STATE
**Definition:** durable accepted or candidate facts relevant to the project. **Authority:** the authority named for that state domain. **Required fields:** identity/version, status, provenance, authority, affected scope. **Invariants:** chat history is not state; state mutations are explicit. **Do not confuse with:** context, evidence, or an implementation observation.

## AUTHORITY
**Definition:** the right to accept, reject, or mutate a governed state/decision. **Owner:** the declared governing role or Owner/K0 boundary. **Required fields:** authority scope, holder/source, permitted actions, escalation path. **Invariants:** writing/carrying/observing information does not create authority. **Do not confuse with:** information access, verification ability, implementation ownership, or runtime capability.

## ENGINE
**Definition:** bounded owner of a class of transformations. **Authority:** system manifest + engine manifest. **Required fields:** `engine_id`, owns, does_not_own, inputs, outputs, entry/exit conditions, dependencies, workflows/capabilities. **Invariant:** conceptual separation does not require a separate repository; semantic engine capability does not prove that a destination runtime can execute a routed assignment. **Do not confuse with:** role, workflow, or destination runtime.

## WORKFLOW
**Definition:** a declared transformation path inside an engine or shared control layer. **Authority:** owning engine/protocol. **Required fields:** workflow id, entry condition, roles, transitions, outputs, stop conditions. **Invariant:** workflow selects role/skills; it does not acquire new authority or execution surfaces. Mandatory workflow actions contribute to assignment required capabilities. **Do not confuse with:** lifecycle state graph as a whole.

## ROLE
**Definition:** durable responsibility and authority contract instantiated by disposable agents. **Authority:** shared/engine role registry. **Required fields:** purpose, authority, context contract, inputs, procedure, outputs, handoff, stop/escalation. **Invariant:** ROLE != AGENT INSTANCE. A role contract does not guarantee that every instance has every tool/runtime mentioned by its procedures. **Do not confuse with:** personality, a permanent worker, or a capability profile.

## SKILL
**Definition:** bounded reusable procedure for how to perform one recurring decision/work method. **Authority:** owning namespace/library lifecycle. **Required fields:** id/name, trigger/use boundary, inputs, procedure, outputs, failure/stop rules; every new or substantively edited skill also declares required/conditional execution capabilities, supported execution modes, and evidence/fallback rules; Solution Patterns additionally need assumptions/rejection conditions/alternatives/trade-offs. **Migration compatibility:** a pre-existing migration-preserved skill without explicit execution metadata is not capability-free; its prerequisites are `UNKNOWN` and MUST be derived from the selected skill's mandatory steps under `contracts/EXECUTABILITY_CONTRACT.md` before assignment. **Invariant:** a skill does not expand role/engine authority or destination runtime capability. **Do not confuse with:** engine, role, universal architecture, or proof that the current destination can execute it.

## CAPABILITY PROFILE
**Definition:** freshness-bounded observation of concrete execution surfaces available to one exact destination instance. **Authority:** it is runtime evidence, not permission to use a capability. **Required fields:** artifact identity/provenance, destination/runtime identity, available capabilities, unavailable capabilities, evidence for every claimed available capability, freshness boundary, limitations. **Invariant:** broad semantic claims such as `can code` are insufficient; capabilities identify concrete surfaces such as repository connector access, local checkout, shell, language runtime, browser, database, deployment, or CI access. **Do not confuse with:** role, engine capability, or authority.

## ASSIGNMENT ADMISSIBILITY
**Definition:** pre-assignment proof that one exact destination can perform and prove all mandatory work authorized by an exact compiled assignment. **Authority:** Control Director applies the compiled requirements; the deterministic subset rule is defined in `contracts/EXECUTABILITY_CONTRACT.md`. **Required fields:** assignment draft id, compiled assignment ref, destination id, capability profile ref, mandatory actions, required capabilities, available capabilities, unsatisfied required capabilities, mandatory evidence paths, execution mode, status. **Invariant:** the union of capabilities required by all final mandatory actions/evidence gates MUST equal the declared required-capability set and MUST contain every compiled authorized capability; additional capabilities require mandatory workflow/skill action accounting. `ADMISSIBLE` requires `REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES` and therefore an empty unsatisfied set. Missing capability is resolved before `ASSIGN`, not intentionally delegated to the Executor/Verifier to discover. **Do not confuse with:** semantic compilation, completion verification, or engine semantic routing.

## ASSIGNMENT
**Definition:** exact instruction for what must happen now. **Authority:** issuer within declared scope. **Required fields:** id, objective, authority, input state ref, allowed/forbidden scope, acceptance, required outputs, stop conditions, result recipient, exact destination, capability profile ref, admissibility ref, required capabilities, mandatory evidence paths, and `execution_contract.proof_status=PROVEN`. **Invariants:** assignment is bounded; missing authority is not inferred; **NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF**. If destination executability is not proven, the artifact remains an assignment draft/control decision and must not be issued as executable work. When `required_durable_outputs` is non-empty, each entry is an opaque assignment-local output identity and the assignment MUST also declare one non-blank opaque `durable_system_of_record_ref` naming the durable authority surface from which those outputs must later be independently read back. `EXECUTOR_RESULT.status=COMPLETE` is structurally valid only when every required output identity has exactly one non-blank binding in `EXECUTOR_RESULT.durable_output_refs`. Those bindings establish reference coverage only. Durable completion is not accepted until Control independently resolves each exact returned ref through the #56 durable port against the assignment's exact system-of-record target and the Verifier binds its verification to that same exact read-back identity/content digest. **DURABLE REF PRESENT != DURABLE READBACK PROVEN**. **Do not confuse with:** role contract, project Canon, or an `ASSIGNMENT_NOT_ADMISSIBLE` control outcome.

## ARTIFACT
**Definition:** durable carrier of a result, claim, decision, or state proposal. **Authority:** source role produces it; downstream authority decides acceptance where required. **Required fields:** stable identity, type, producer role, assignment/state refs, status, provenance, related artifacts. **Invariant:** ARTIFACT != EVIDENCE. A durable-output reference naming an artifact does not by itself prove that the artifact is resolvable, readable, fresh, or independently consumed. Successful exact readback proves availability/content identity at the declared durable authority surface; it does not prove factual claims carried by the payload. **Do not confuse with:** proof simply because it exists.

## EVIDENCE
**Definition:** observations/data that support a specific claim about an exact relevant state. **Authority:** evidence has information value; acceptance authority remains separate. **Required fields:** claim, exact target identity, method/source, result, freshness/trust boundary. **Invariants:** evidence cannot prove a stronger claim than it observes; stale affected evidence is not current proof; availability of an evidence source must not be assumed from semantic capability. **Do not confuse with:** approval, authority, artifact presence, or capability profile.

## GATE
**Definition:** explicit condition that controls an admissible state/workflow transition. **Authority:** declared by governing workflow/authority. **Required fields:** gate id, required conditions/evidence/authority, PASS/BLOCKED outcome, next transition. **Invariants:** gates fail closed when required proof/authority is absent; a mandatory evidence gate contributes its execution/evidence capabilities to pre-assignment admissibility. In Research Engine flows, any authority gate reserved to the only default human actor must be named explicitly as an `OWNER_*` gate; generic `HUMAN_*` authority gates are invalid. **Do not confuse with:** arbitrary ceremony or a permanent manual approval bottleneck.

## HANDOFF
**Definition:** durable transfer of bounded continuation state between role instances. **Authority:** producing role owns accuracy of its handoff; receiving role revalidates affected assumptions. **Required fields:** source/recipient role, state/assignment refs, completed work, unresolved/blockers, evidence refs, exact next owner/action. **Invariant:** hidden chat memory is not a handoff. **Do not confuse with:** verification or acceptance.

## OWNER QUESTION
**Definition:** a human-readable request for a decision that only Owner/K0 may make. **Authority:** Owner/K0. **Required fields:** why decision is needed, options, consequences, recommendation, unresolved uncertainty, what follows. **Invariant:** do not manufacture Owner questions for decisions already delegated. **Do not confuse with:** an implementation clarification the active role can resolve within authority.

## STATE MUTATION
**Definition:** proposed or accepted change to governed durable state. **Authority:** mutation requires the authority of the affected state domain. **Required fields:** mutation id/proposal artifact, prior state ref, proposed change, reason/evidence, authority decision, resulting state ref. **Invariant:** no silent mutation. **Do not confuse with:** editing a carrier file when the edit has not been accepted as state.

## Mandatory distinctions

- `IMPLEMENTATION FACT != CANONICAL FACT`: software observations cannot silently become Canon truth.
- `ARTIFACT != EVIDENCE`: a report may point to proof but does not prove itself.
- `DURABLE REF PRESENT != DURABLE READBACK PROVEN`: A1 reference completeness is not materialization/readback evidence.
- `DURABLE READBACK PROVEN != FACTUAL CLAIM VERIFIED`: exact availability/content identity does not establish truth of claims inside the artifact.
- `ROLE != AGENT INSTANCE`: agents are replaceable executions of durable contracts.
- `ENGINE CAPABILITY != DESTINATION CAPABILITY`: semantic ownership does not imply an executable runtime.
- `MACHINE_EXECUTABLE METHOD != DESTINATION EXECUTABILITY`: machine-only Research admission is not runtime capability proof.
- `ASSIGNMENT DRAFT != EXECUTABLE ASSIGNMENT`: only an admissible destination-bound assignment may be issued.
- `STATE != CHAT CONTEXT`: durable state survives independently of conversation history.
- `VERIFICATION AUTHORITY != INFORMATION AUTHORITY`: a verifier may establish whether claims are supported; it does not thereby own product/Canon/Owner decisions.

## Minimal protected-proof lifecycle

A governed `ASSIGNMENT_ADMISSIBILITY` reused at a post-spawn protected transition identifies only its relevant
dependencies as exact `dependency_ref` / `proven_identity` bindings under
`transition_proof.dependency_bindings`. Reuse compares those bindings with the
current locally supplied Control Director `STATE_OBSERVATION` identities. A changed relevant dependency
invalidates that proof; an unrelated state change does not. Reuse of assignment
admission for a transition explicitly requiring current executability also
requires a current governed capability profile for the same runtime whose
destination and runtime identities match and whose available capabilities still
cover the assignment execution contract. `resolve_spawn()` produces this binding;
`resolve_transition()` consumes it and rejects every other proof class. This
bounded representation is not a proof registry, dependency graph, state engine,
or authorization to recompute unrelated proofs.
