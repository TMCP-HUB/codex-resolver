# Canon Authority

This document defines reusable Canon authority semantics for Project Resolver, consistent with the active Canon contracts and skills.

## Definition

Canon is an **explicit governed project declaration** that downstream work must preserve until it is explicitly superseded through authorized change.

A proposition is not Canon merely because it appears in research notes, evidence, a finding, implementation, source code, prose, translation, test, fixture, report, or remembered/chat intent. Those surfaces may provide information or evidence. They do not silently create authority.

## Item authority states

Canon records may use:

- `PROPOSED` — candidate state; not downstream authority;
- `ACCEPTED` — explicitly accepted within stated authority/scope;
- `FROZEN` — accepted and protected against incidental mutation for a declared lifecycle scope;
- `SUPERSEDED` — retained as history/provenance, no longer current authority.

These item states are distinct from Canon maturity/version (`0.x`, `1.0`, `2.0`).

## Core rules

1. **Explicit beats inferred.** Plausibility, implementation convenience, or repeated wording does not grant acceptance.
2. **Upstream authority beats downstream realization.** Production may expose a Canon defect or gap; it may not repair Canon silently.
3. **Implementation fact is not Canonical fact.** Runtime/software behavior may trigger a proposal but cannot make itself law.
4. **Research evidence/finding is not an accepted project decision.** Findings enter Canon through reconciliation plus explicit Canon authority.
5. **Translation is realization.** Language-specific solutions do not automatically mutate source Canon.
6. **Validation derives from authority.** A validator/test can show inconsistency; passing cannot grant Owner acceptance.
7. **Scope is part of meaning.** Apparently opposite declarations can coexist when their time, audience, condition, or scope differs.
8. **Equal-authority conflict has no implicit winner.** Do not resolve by last-read/newest/convenient carrier; register the smallest conflict and gate mutation.
9. **Reuse applicable decisions.** An already-authorized Owner decision remains valid for its actual scope; do not seek the same decision again. Working materials and new substantive interpretations do not inherit acceptance from it.

## Facts, assumptions, unknowns, ambiguity, contradictions

### Fact

A Canon fact is an accepted proposition supported by declared authority/provenance. An inference remains proposed until accepted.

### Assumption

An assumption is an explicitly tracked proposition the project is temporarily relying on **as an assumption**, not as established truth. Accepting an assumption record means accepting its use/status, not asserting factual certainty.

### Unknown

An unknown records a question/state the project has not resolved. Canon Foundation 0.x may freeze with explicit unknowns. Freezing an unknown means preserving that it is unknown; it does not turn the missing answer into truth.

### Intended ambiguity

Intended ambiguity is a positive protected decision not to collapse a distinction or reading within a stated scope. It requires explicit authority and preservation requirements. Creator/project indecision is not intended ambiguity.

### Contradiction

A contradiction record describes incompatible or apparently incompatible claims and their scope/status. Blocking accepted conflicts cannot be auto-fixed by the Canon Engine; they require controlled authority/change handling. Intentional tension or scoped apparent conflict may be nonblocking when explicitly declared.

## Canon registries

Canon may maintain stable registries required by a project, but core Canon defines no mandatory literary/product ontology. Characters, motifs, reveals, objects, chapters, APIs, legal sections, stakeholders, or other domain entities are project/domain schemas or optional patterns. The universal Canon requirement is only that canonical identities are stable, scoped, provenance-bearing, and governed by explicit authority.

## Freeze semantics by maturity

### Foundation 0.x freeze

A 0.x freeze establishes a stable project authority boundary, including Research entry only where Research is needed. It may include explicit assumptions, unknowns, unresolved contradictions and protected ambiguity; it must not present them as researched truth.

Required minimum:

- Owner-authorized scope/protected values are explicit;
- known facts vs assumptions vs unknowns are distinguishable;
- known blocking ambiguity/contradiction is visible;
- stable identity/provenance exist;
- the freeze record states what remains unresolved and, only where relevant, what Research is expected to reduce.

### Canon 1.0 freeze

A 1.0 freeze requires authority disposition of accepted claims and of any genuine blockers for the declared outcome and freeze scope. Relevant Research that was needed or performed for that outcome must be considered and reconciled through the existing authority boundary; a required but unresolved finding remains a blocker. When no Research was needed and none applicable exists, do not require a Research release or reconciliation. Nonblocking unknowns may remain with their disposition covered by existing authority; a protected ambiguity must be explicitly authorized. Production authorization is relevant only when realization is requested.

### Canon 2.0 freeze

A 2.0 freeze follows final production-era reconciliation. It records all accepted production-time Canon changes and remaining explicit decisions/ambiguities. Post-2.0 change cannot be an ordinary silent edit.

## Reopen rule

A frozen Canon scope may reopen only under explicit authority and a new state/version lineage. After Canon 2.0, the change must declare one of:

- `ADDENDUM`
- `EXPANSION`
- `NEW_EDITION`
- `REOPEN`

No mode authorizes retroactive mutation without provenance or impact handling.

## Current Canon carrier continuity

When an already-authorized ordinary revision or freeze actually designates a
resulting Canon state as current and the project already has a declared current
carrier, update that carrier in place. Keep its stable address distinct from
the new semantic state/version reference, and retain the preceding state in the
existing history or provenance surface. A proposal, draft, or freeze record is
not by itself a designation of current Canon. A normal revision or freeze does
not authorize a different carrier or a transfer of semantic authority.

For an existing repository-indexed Canon payload, resolve the declared current
address to its existing namespace entry. Use that entry's carrier `artifact_id`,
scope and exact current `artifact_ref` as `expected_artifact_ref` with
`tools.project_topology_repository.materialize_repository_payload`; the existing
update preserves the address and records prior refs in `history_refs`. For a
scoped namespace, form the scope mapping from its `scope_key` and the entry's
stored scope value; for an unscoped namespace, omit scope. This
precondition does not itself confer Canon authority. For another actual carrier,
use its existing authorized update/readback capability when available. If the
assignment or destination cannot perform the authorized carrier update, return
the bounded result and the specific outstanding update to Control for an
existing capable route. Do not create a new carrier or repeat an already
applicable Owner decision. Local repository readback alone does not prove
publication to another system.

### Multiple already-declared current representations

When a project actually declares multiple current representations of the same
Canon, use its existing project state or authority map to identify each real
carrier, system of record, current address and state ref, authority source,
authority or presentation/mirror role, and synchronization direction. The
existing `kernel/skills/authority-mapping/SKILL.md` method may be used when
needed; do not create another registry or infer roles from storage location or
read order.

When the authorized work requires synchronization, update the declared
representations using the available existing operations and only the already
authorized meaning. Reuse applicable Owner decisions; a new semantic choice or
scope change is not implied by copying or formatting content. Keep any genuinely
unresolved new meaning or scope proposed and route it through existing Canon
authority. For each affected carrier, use actual readback of its result and
assess whether its meaning matches the authorized Canon for the relevant scope.
Reuse applicable readback and semantic assessments that remain valid for the
exact states. Exact bytes, a digest or a successful readback alone do not
establish semantic equivalence across formats.

An out-of-date mirror is not automatically a competing authority: use its
declared direction and update it within the existing authority when appropriate.
If equally authoritative accepted states actually conflict, do not choose the
last-read or newest; route the real conflict through the existing
`register-contradiction` method with exact refs and authority. Do not manufacture
a new Owner question when an applicable decision already resolves it.

### Explicit carrier or semantic-authority cutover

Treat a requested and authorized carrier change as a distinct operation from an
ordinary revision; transferring semantic authority is a distinct decision from
copying or moving a carrier. Reuse the actual applicable authority and project
state; neither edit access nor a changed navigation pointer confers authority.
If a required existing decision record cannot represent this operation, retain
the real source and report that exact limitation; do not relabel the cutover as
an unrelated workflow or invent a selection.

Materialize the selected successor carrier if needed, use actual readback of its
content, and establish semantic equivalence to the governing Canon or the exact
already-authorized difference. Reuse applicable evidence that remains valid for
the exact states. Then apply only the selected current-carrier
designation and/or semantic-authority change through the existing state and
decision mechanisms. A review result or a reference to authority does not itself
perform that change. An authority transfer between already-current
representations need not replace either carrier. If a carrier's role changes,
record its actual resulting role as historical, mirror or presentation,
preserving its link when it remains a current presentation. Reconcile the
existing project map and affected current references; do not rewrite historical
evidence or silently transfer authority back during later synchronization.

For a material Canon or authority change, pass the actually known affected refs,
assignments and evidence to Control for the existing bounded revalidation and
current-frontier reconciliation. Do not invalidate unrelated evidence or require
a global scan. If an assigned actor cannot perform an actual required
read, update, comparison or cutover, return the completed bounded work and exact
outstanding operation to Control for an existing capable route; do not claim the
unperformed operation or provider synchronization succeeded.

## Accepted mutation materialization gate

For an answer to presented options, the Owner decision selection for accepted
Canon mutation is exactly `AUTHORIZE_CANON_MUTATION`. An already-authorized,
unambiguous direct Owner instruction may instead be recorded using
`canon_input_mode: DIRECT_INSTRUCTION` and the exact Owner words in
`canon_instruction_text`, with the real source and qualifications preserved.
Do not invent a prior question, options, or selection. The same direct record
form applies to actual final reconciliation and reopen authority; each workflow
keeps its existing authority bindings. The responsible Owner Interface actor
must read the source and determine whether it authorizes the scoped operation;
discussion or a question alone is not authority. The record and code do not
authenticate the speaker or establish the meaning of arbitrary language.

This selection is conditional on an actual accepted mutation. Proposal,
classification, retain, defer, blocked and superseded outputs do not require
mutation authority merely to execute.

Before durable materialization of an accepted `CANON_RECONCILIATION_RESULT` or
`CANON_CHANGE_PROPOSAL`, the active Canon workflow must call
`guard_mutation_materialization()` from
`engines/canon/tools/mutation_authority.py`.

The resolved authority must be an existing governed `OWNER_DECISION_RECORD`
with `produced_by_role = owner-interface`, `status = RECORDED`,
`authority_role = OWNER_K0`, non-empty provenance, either the actual selection
or the direct instruction form above, and `decision_kind` equal to the active
mutation workflow.

Target and scope are non-transitive. `input_state_ref` on the authority binds
the exact `source_canon_ref` / `prior_canon_ref`; `project_id` must match. For
`CANON_CHANGE_PROPOSAL`, `authorized_scope` must equal the proposal `scope`.
For `CANON_RECONCILIATION_RESULT`, which has no separate scope field,
`authorized_scope` must equal the exact `source_canon_ref`.

Only gate status `PROVEN` permits durable `ACCEPTED` materialization or
application into resulting Canon state. The accepted artifact must retain the
validated authority ref in its authority field and include both the authority
and exact Canon target in `related_artifacts`. A missing, unresolved, fake,
unrelated, wrong-workflow, wrong-target, wrong-project or wrong-scope authority
fails closed.
