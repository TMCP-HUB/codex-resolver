# Foundation V0 project formation design

Date: 2026-10-04
Status: design freeze candidate
Issue owner: #53
Baseline: `main` at `65476b45d420d025506fa87b6c41ddb380ce698e` after Liaison cognitive base merge (#97).

## 1. Purpose

Materialize the planned but unavailable `foundation` Engine as the governed project-formation layer between Liaison cognitive intake and Canon.

Foundation V0 handles the case where the Owner has more than an ordinary question but less than governed project truth: a raw idea, early concept, partially understood project, or project-formation conversation that should become durable working state without silently becoming Canon.

Target path:

```text
OWNER RAW IDEA
→ Liaison (#54)
  owner-intent-sensemaking
  project-context-orientation
→ ROUTE
→ Foundation Engine (#53)
→ form_project_foundation
   ├─ develop-project-seed
   ├─ define-project-outcome
   ├─ classify-consequential-unknowns
   └─ design-discovery [only when materially useful]
→ PROJECT_SEED
→ PROJECT_OUTCOME
→ CONSEQUENTIAL_UNKNOWN_MAP
→ durable refs + exact readback of all declared outputs
→ FOUNDATION_READY_FOR_OWNER_GATE
→ STOP
```

Foundation V0 does not accept Canon, mutate Canon, start Research automatically, start Production, or decide on behalf of Owner.

## 2. Architectural position

```text
NATIVE LLM REASONING
→ Liaison cognitive intake
→ Foundation project formation
→ Owner Foundation Gate [later wave]
→ Canon Engine
→ governed Canon Foundation 0.x
```

Required distinctions:

```text
RAW OWNER IDEA
!= PROJECT_SEED
!= CANON

FOUNDATION WORKING STATE
!= OWNER-ACCEPTED PROJECT TRUTH

MODEL PROPOSAL
!= OWNER INTENT

DURABLE
!= AUTHORITATIVE
```

Foundation is not a weaker Canon Engine and not a second Liaison. It owns durable non-authoritative project-formation state.

Canon remains the sole owner of governed Canon truth lifecycle. Liaison remains the human-facing cognitive intake and Owner projection role.

## 3. Why Foundation is an Engine

The Liaison cognitive base from #97 answers:

```text
RAW OWNER REQUEST
→ RESPOND_IN_PLACE | CLARIFY | ROUTE
```

It intentionally does not own durable project formation.

After `ROUTE` selects project formation, the work needs a semantic owner with explicit outputs, workflow composition, artifact rules, Router capability ownership, and assignment/executability semantics. That owner is Foundation.

Keeping formation inside Liaison would collapse two responsibilities:

- understand what the Owner is asking;
- build durable but still non-authoritative project working state.

The same physical ChatGPT conversation may perform Liaison and Foundation as separate logical phases. Physical co-location does not merge roles or authority.

## 4. V0 scope

Foundation V0 materializes exactly one Engine workflow:

```text
form_project_foundation
```

It composes four cognitive skills:

1. `develop-project-seed` — required;
2. `define-project-outcome` — required;
3. `classify-consequential-unknowns` — required;
4. `design-discovery` — optional and loaded only when exploration materially improves the working foundation.

It produces exactly three Foundation-owned durable artifact types:

```text
PROJECT_SEED
PROJECT_OUTCOME
CONSEQUENTIAL_UNKNOWN_MAP
```

`FOUNDATION_READY_FOR_OWNER_GATE` is a workflow/result status, not a fourth durable artifact.

## 5. Engine registration

`SYSTEM_MANIFEST.yaml` currently declares Foundation under `planned_engines` with `status: not_materialized`.

Foundation V0 moves it into `engine_registry` with `status: available` and one root semantic capability:

```text
form_project_foundation
```

V0 does not expose every internal cognitive skill as a root capability. Router selects project formation; the Foundation manifest owns internal composition. This keeps root routing vocabulary smaller than the skill library.

## 6. Foundation manifest contract

Create:

```text
engines/foundation/MANIFEST.yaml
```

Foundation owns:

- raw-to-working project formation after Liaison routes into governed project formation;
- working project seed creation/refinement;
- requested outcome definition;
- consequential unknown classification;
- optional bounded design discovery before Canon;
- production of the three non-authoritative durable Foundation artifacts.

Foundation does not own:

- Owner/K0 authority;
- Liaison intent interpretation before route selection;
- accepted Canon truth;
- Canon mutation/freeze/reopen;
- substantive external Research or evidence collection;
- Production planning or implementation;
- independent Verification;
- generic routing/orchestration;
- SBC/PAK/provider transport.

V0 inputs include, as applicable:

- exact Owner request / supplied material preserved as provenance;
- Liaison bounded routing frame;
- relevant existing state when one exists;
- exact assignment;
- destination capability profile and assignment admissibility;
- declared durable output requirements/system-of-record when durable materialization is requested.

Outputs:

- `PROJECT_SEED`;
- `PROJECT_OUTCOME`;
- `CONSEQUENTIAL_UNKNOWN_MAP`;
- ordinary `EXECUTOR_RESULT` / workflow result containing terminal status or blocker.

Reuse shared roles rather than create a Foundation persona. The executing role is `roles/executor/ROLE.md`; the consuming/control role remains `roles/control-director/ROLE.md` when governed control is active.

Manual V0 may use:

```text
Liaison
→ Foundation workflow / Executor logical phase
→ Foundation result
→ Liaison projection
→ Owner
```

## 7. Workflow contract

Create:

```text
engines/foundation/workflows/form-project-foundation.md
```

Conceptual procedure:

```text
1. consume Liaison routing frame and exact supplied Owner material
2. develop PROJECT_SEED working interpretation
3. establish PROJECT_OUTCOME sufficiently for current formation stage
4. identify consequential unresolved items
5. use design-discovery only if needed for coherence/problem-space exploration
6. classify unresolved items into CONSEQUENTIAL_UNKNOWN_MAP
7. reconcile all three for contradiction and provenance loss
8. materialize all assignment-declared required Foundation outputs
9. require exact durable refs/readback under the existing durable-output contract
10. if semantically sufficient for an Owner Foundation Gate:
       return FOUNDATION_READY_FOR_OWNER_GATE
    else:
       return the smallest bounded clarification/blocker needed
11. stop; do not invoke Canon acceptance, Research execution, or Production
```

The workflow may iterate internally among the four skills. It must not create a procedural interrogation loop with the Owner.

A reasonable working interpretation the Owner can correct is preferred over exhaustive formalization.

## 8. Durability and readiness gate

Foundation artifacts are durable working state. They must use the existing Common Artifact Protocol and durable-output/readback semantics; Foundation does not invent a parallel durability model.

For a durable Foundation assignment, the three outputs are declared through the existing assignment durable-output contract. Completion must return stable output refs, and Control performs the existing provider-neutral exact readback.

Required distinction:

```text
DURABLE OUTPUT REF
+ READBACK
= proof that the working artifact exists at the declared durable identity

BUT

DURABLE OUTPUT REF
+ READBACK
!= semantic correctness
!= Owner acceptance
!= Canon authority
```

`FOUNDATION_READY_FOR_OWNER_GATE` may be emitted only when:

- the required Foundation artifacts for that formation assignment exist;
- the assignment-required durable output identities are fully covered;
- the exact durable objects are independently readable under the existing readback law;
- the working state is coherent enough to present to Owner without inventing missing intent.

It does not mean the Owner accepted the project meaning.

If durable materialization is unavailable, Foundation may still reason conversationally, but it must not claim durable Foundation completion/readiness.

## 9. Cognitive skill design law

Foundation skills guide an intelligent LLM; they do not replace intelligence with a deterministic questionnaire.

### Thinking guidance

Prefer judgment-oriented instructions such as:

- consider;
- look for;
- compare;
- infer cautiously;
- propose;
- reframe;
- simplify;
- test coherence;
- ask when material.

### Hard invariants

Strict requirements remain narrow and authority/evidence-bearing:

- do not invent Owner intent;
- do not silently promote a proposal/working interpretation into Canon;
- do not claim external factual/feasibility evidence that was not obtained;
- do not automatically start Research because an unknown exists;
- do not freeze architecture because a plausible implementation was proposed;
- do not treat a Foundation artifact as Owner/K0 authority;
- preserve explicit Owner constraints, corrections, and disagreement.

No Foundation cognitive skill may require a fixed questionnaire or arbitrary completeness score.

## 10. `develop-project-seed`

Create:

```text
engines/foundation/skills/develop-project-seed/SKILL.md
```

Purpose: turn a raw idea or incomplete concept into a coherent working interpretation useful enough to reason about and correct.

When material, look for:

- underlying objective;
- intended user/beneficiary/value;
- protected Owner intent;
- hard constraints;
- non-goals;
- explicitly known decisions;
- contradictions;
- hidden assumptions;
- important missing decisions;
- project identity candidate / useful working name when available.

Preserve distinctions among:

```text
EXPLICIT OWNER STATEMENT
STRONGLY IMPLIED CONTEXT
MODEL WORKING INTERPRETATION
MODEL PROPOSAL
UNRESOLVED MATERIAL QUESTION
```

The artifact must not erase those distinctions.

Preferred interaction style is a correctable working interpretation rather than an exhaustive form.

## 11. `define-project-outcome`

Create:

```text
engines/foundation/skills/define-project-outcome/SKILL.md
```

Purpose: establish what the Owner wants to exist at completion before Research or Production is planned.

Reason about:

- target outcome;
- completion condition;
- required deliverables;
- optional deliverables when relevant;
- audience/user where material;
- non-goals;
- whether downstream realization is required at all.

Do not assume every project ends in software or Production.

Valid outcomes include concept/Canon, evidence-backed plan, research result, document/presentation, website, software product, operating process, or multi-deliverable program.

Output remains working Foundation state until later Owner/Canon acceptance.

## 12. `classify-consequential-unknowns`

Create:

```text
engines/foundation/skills/classify-consequential-unknowns/SKILL.md
```

Purpose: keep unresolved uncertainty explicit and classify what kind of uncertainty it is without automatically resolving it.

V0 vocabulary:

```text
OWNER_PREFERENCE
EXTERNAL_FACT
FEASIBILITY
ARCHITECTURE_DECISION
IMPLEMENTATION_DEPENDENT
NICE_TO_KNOW
```

Interpretation:

- `OWNER_PREFERENCE`: belongs to Owner; Research cannot answer it for them;
- `EXTERNAL_FACT`: may later become Research candidate if consequential;
- `FEASIBILITY`: may later require evidence/prototype/research;
- `ARCHITECTURE_DECISION`: may require exploration/evidence and later authority, but is not automatically Canon;
- `IMPLEMENTATION_DEPENDENT`: defer until relevant implementation context exists;
- `NICE_TO_KNOW`: keep off critical path unless consequence changes.

Classification does not dispatch Research, create Owner authority, or authorize architecture.

Unknowns that are not consequential to the declared outcome need not be materialized for completeness.

## 13. `design-discovery`

Create:

```text
engines/foundation/skills/design-discovery/SKILL.md
```

Purpose: explore problem/solution space before Canon without prematurely freezing architecture.

It may:

- propose alternative interpretations;
- compare solution shapes;
- simplify scope;
- expose contradictions;
- test whether features serve the outcome;
- propose project boundaries;
- surface trade-offs;
- identify assumptions that should remain open.

It remains optional. Straightforward formation must not load it just because it exists.

V0 creates no `DESIGN_DISCOVERY_RESULT` artifact. Material discovery is folded into current seed/outcome/unknown map while preserving proposal vs Owner-statement provenance.

## 14. Artifact model

All three durable artifacts use the existing common artifact identity/provenance envelope (`artifact_id`, `artifact_type`, `produced_by_role`, assignment/input-state/provenance/related-artifact fields as required by the Common Artifact Protocol).

They additionally expose a machine-checkable non-authority marker. The implementation may choose the exact local field name, but all three schemas must make the equivalent of `authoritative: false` invariant.

### `PROJECT_SEED`

Schema:

```text
engines/foundation/schemas/project-seed.schema.json
```

Minimum semantic payload:

- `artifact_type: PROJECT_SEED`;
- working interpretation/project summary;
- machine-checkable non-authoritative status;
- preservation of material Owner constraints/protected intent when supplied;
- unresolved material questions or refs to unknown map;
- common-envelope provenance.

Dimensions such as intended users, constraints, non-goals, known decisions, assumptions, and identity candidate are optional/bounded, not mandatory empty form fields.

### `PROJECT_OUTCOME`

Schema:

```text
engines/foundation/schemas/project-outcome.schema.json
```

Minimum semantic payload:

- `artifact_type: PROJECT_OUTCOME`;
- working target outcome;
- completion condition or explicit unresolved completion condition;
- required deliverables known at this stage;
- optional deliverables only when meaningful;
- audience/user and non-goals when material;
- machine-checkable non-authoritative status;
- common-envelope provenance.

### `CONSEQUENTIAL_UNKNOWN_MAP`

Schema:

```text
engines/foundation/schemas/consequential-unknown-map.schema.json
```

Each materialized item contains at least:

- stable bounded item identity within the artifact;
- unknown/question statement;
- one V0 classification;
- why it matters / downstream consequence;
- current state such as open or deferred.

The map contains consequential unknowns, not every unknown thought. Its schema must not encode automatic Research dispatch authority.

## 15. Non-authority law

Required semantics:

```text
PROJECT_SEED.authoritative = false
PROJECT_OUTCOME.authoritative = false
CONSEQUENTIAL_UNKNOWN_MAP.authoritative = false
```

No Foundation artifact may satisfy a Canon mutation/freeze authority requirement merely because it is durable, read back successfully, or produced by a valid assignment.

A later Owner Foundation Gate may authorize selected Foundation meaning to enter Canon. That gate is outside this wave.

## 16. Clarification policy

Liaison and Foundation share this law:

```text
ASK ONLY WHEN DIFFERENT PLAUSIBLE ANSWERS
WOULD MATERIALLY CHANGE
THE PROJECT, ROUTE, AUTHORITY, OUTPUT, OR NEXT ACTION.
```

Foundation V0 has no mandatory minimum question count.

Zero clarification questions is valid when supplied material is sufficient for useful working Foundation state.

This resolves older bootstrap guidance mentioning an adaptive `3–20` question range: it is not a protocol requirement or minimum. The newer Liaison/Foundation cognitive law governs V0.

When interaction is required, ask the smallest bounded material question. A model may instead state a working interpretation and allow correction when that is safer and more efficient.

## 17. External facts and Research boundary

Foundation may use general model reasoning for ideation/explanation, but it must distinguish reasoning from evidence-backed external project facts.

When formation depends on a current/external factual or feasibility claim, Foundation classifies the uncertainty but does not treat model memory as evidence.

Later chain:

```text
CONSEQUENTIAL_UNKNOWN_MAP
→ later Research admission/planning where justified
→ evidence/findings
→ later Canon reconciliation / Owner authority
```

Foundation V0 stops before Research dispatch.

## 18. Canon boundary

The existing Canon Engine owns `CANON_FOUNDATION`, Canon state registration, reconciliation/change classification, validation, freeze, and reopen.

Foundation V0 duplicates none of those artifacts or skills.

The workflow ends at:

```text
FOUNDATION_READY_FOR_OWNER_GATE
```

not:

```text
CANON_FOUNDATION_CREATED
```

A later #53 wave defines the exact Owner Foundation Gate and handoff from accepted Foundation meaning into existing `establish_canon_foundation`.

Until then, readiness is an explicit stop boundary.

## 19. Router changes

`ROUTER.md` currently has a non-materialized Foundation gate. V0 replaces only that Foundation path.

Add:

```text
form_project_foundation → foundation
```

Routing behavior:

1. Liaison has selected `ROUTE` because governed project formation is intended.
2. Router selects Foundation by semantic capability/authority boundary.
3. Load only `engines/foundation/MANIFEST.yaml`.
4. Select `form_project_foundation`.
5. Load three required skills plus `design-discovery` only when selected/needed.
6. Apply existing compiler/executability/admissibility and durable-output laws.
7. Activate declared role without granting Owner or Canon authority.

Do not route raw project formation straight to Canon because `establish_canon_foundation` exists.

Do not borrow Software skills to simulate Foundation.

## 20. Progressive disclosure

#97 law remains:

```text
AWARE
→ INSPECT
→ LOAD
→ APPLY
→ MATERIALIZE
```

For raw project formation:

- `AWARE`: root manifest says Foundation exists;
- `INSPECT`: after Liaison `ROUTE`, inspect only Foundation manifest/workflow;
- `LOAD`: load required skills and optional discovery only when relevant;
- `APPLY`: skills guide native reasoning;
- `MATERIALIZE`: create durable Foundation outputs only under valid assignment/durable-output conditions.

No global skill discovery.

## 21. Error and stop conditions

Foundation stops or reports bounded blockers rather than fabricating certainty for:

- material Owner-intent ambiguity that cannot be preserved faithfully;
- contradictory Owner constraints that materially change the project;
- insufficient information to define even a working outcome;
- external fact/feasibility dependency presented as established evidence without proof;
- attempt to treat Foundation output as accepted Canon;
- attempt to auto-dispatch Research;
- attempt to auto-enter Production;
- missing assignment/executability/durable-write/readback prerequisites for claimed durable completion.

Where a useful non-authoritative working interpretation is possible, explicit uncertainty is preferred over unnecessary blocking.

## 22. Expected implementation surfaces

The implementation plan may refine exact test filenames, but the architecture expects approximately:

```text
SYSTEM_MANIFEST.yaml
ROUTER.md
engines/foundation/MANIFEST.yaml
engines/foundation/workflows/form-project-foundation.md
engines/foundation/skills/develop-project-seed/SKILL.md
engines/foundation/skills/define-project-outcome/SKILL.md
engines/foundation/skills/classify-consequential-unknowns/SKILL.md
engines/foundation/skills/design-discovery/SKILL.md
engines/foundation/schemas/project-seed.schema.json
engines/foundation/schemas/project-outcome.schema.json
engines/foundation/schemas/consequential-unknown-map.schema.json
schemas/README.md [only if shared index requires it]
tools/validate_structure.py [only enough to register/protect new Engine surfaces]
tests/... Foundation behavioral/structure/schema/route coverage
```

No unrelated Canon, Research, Software, Verification, SBC, PAK, provider, or resource-governance rewrite belongs in this wave.

## 23. Testing strategy

Implementation uses TDD and proves semantics plus boundaries.

Minimum cases:

1. raw project idea routed from Liaison reaches Foundation, not Canon/Software;
2. sufficient description may produce working state with zero forced clarification questions;
3. material ambiguity produces bounded clarification rather than invented Owner intent;
4. `design-discovery` remains optional;
5. Foundation outputs are durable and machine-checkably non-authoritative;
6. all three artifacts validate against their schemas/common envelope;
7. durable assignment declares and covers required Foundation output identities;
8. exact readback is required before `FOUNDATION_READY_FOR_OWNER_GATE`;
9. unknown classification accepts exactly V0 vocabulary and rejects undeclared classes;
10. `OWNER_PREFERENCE` is not converted into Research work;
11. `EXTERNAL_FACT`/`FEASIBILITY` may remain Research candidates/unknowns but do not dispatch Research;
12. no Foundation output satisfies Canon mutation/freeze authority by itself;
13. workflow stops at readiness and does not create `CANON_FOUNDATION`;
14. existing Software/Research/Verification/Canon representative routes remain unchanged;
15. structural validator recognizes Foundation as materialized;
16. global skill discovery remains forbidden.

Full repository suite and `tools/validate_structure.py` must pass on exact PR head/merge ref before merge.

## 24. Acceptance criteria

Foundation V0 is accepted when:

1. `foundation` is `available` in root engine registry.
2. Router selects `form_project_foundation` from Liaison `ROUTE`.
3. One Foundation workflow composes four approved cognitive skills with discovery optional.
4. Raw Owner idea can become durable `PROJECT_SEED`, `PROJECT_OUTCOME`, and `CONSEQUENTIAL_UNKNOWN_MAP` without becoming Canon.
5. The three artifacts preserve provenance and machine-checkable non-authority.
6. Required durable outputs use existing assignment/readback law.
7. Model may use working interpretations rather than fixed intake form.
8. No mandatory minimum Owner-question count exists.
9. Consequential unknowns are classified without automatic Research dispatch.
10. Foundation stops at `FOUNDATION_READY_FOR_OWNER_GATE`.
11. Canon remains sole owner of governed Canon Foundation/truth lifecycle.
12. Existing Router/compiler/executability/durable-state laws are reused, not duplicated.
13. Existing Engines retain regression behavior.

## 25. Explicit non-goals

This wave does not implement:

- Owner Foundation Gate artifact/decision semantics;
- automatic Foundation → `CANON_FOUNDATION` conversion;
- Canon carrier creation/migration;
- Research dispatch or broad Research Need orchestration beyond unknown classification;
- Production Foundation or implementation;
- storage-topology provisioning (`DRIVE_ONLY`, `REPO_ONLY`, `DRIVE_THEN_REPO`);
- account/connectors provisioning;
- automation activation gate;
- SBC Browser or PAK transport;
- physical multi-chat session orchestration;
- a new Liaison, Control Director, Executor, or Foundation persona;
- a new common artifact envelope or durability protocol;
- a second Router;
- completion of all remaining #53 lifecycle sections.

## 26. Sequencing

```text
#97 MERGED: Liaison Cognitive Base
→ THIS WAVE: Foundation V0
→ NEXT #53 WAVE: Owner Foundation Gate + exact handoff into existing Canon Engine
→ later #53 lifecycle extensions as needed
→ #58/#54 manual multi-chat conformance where physical handoff is useful
```

This is an architecture addition: it materializes an already-planned Engine and does not replace an existing Engine. The architecture-replacement preserve/destructive Owner gate is therefore not invoked.
