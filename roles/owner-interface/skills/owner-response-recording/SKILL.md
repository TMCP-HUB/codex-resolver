---
name: owner-response-recording
description: Record an actual Owner answer or direct resource or Canon instruction in the existing OWNER_DECISION_RECORD without inventing intent.
---

# Owner Response Recording

## Purpose

Use this skill after the Owner has answered a genuine decision surface produced by `owner-decision-surface`, or has directly given an unambiguous resource or Canon instruction that needs a durable record.

## Goal

Normalize only what the Owner actually said, map an answer to the already-presented canonical option set when one exists, preserve explicit qualifications, and materialize the existing `OWNER_DECISION_RECORD` contract only when the decision is unambiguous.

```text
LIAISON NORMALIZATION != LIAISON DECISION
```

## When to use

Use this skill when:

- an exact Owner decision surface and its canonical option mapping are available;
- an unambiguous direct resource or Canon instruction must be recorded without a fabricated decision surface;
- the Owner replies with a compact human label, canonical option, or unambiguous natural equivalent;
- the Owner adds bounded qualifications, constraints, or a condition that qualifies one selected option;
- a durable Owner decision must be returned to Control Director.

Do not use this skill when:

- neither a genuine Owner gate nor a direct Owner resource or Canon instruction exists;
- the answer could map to multiple materially distinct options;
- the Owner omitted the selection and only repeated a recommendation/rationale;
- the Owner delegates authority to Liaison instead of choosing;
- the answer requires a branching conditional choice that the existing single-`selected_option` schema cannot faithfully represent.

## Inputs

For an answer to presented options, require:

- exact decision/question ref;
- exact option set that was presented;
- deterministic human-label -> canonical-option mapping;
- the Owner's actual response text or durable response ref;
- relevant assignment/input-state/provenance refs needed by the existing record contract;
- consequences/constraints that were presented, only as needed to preserve explicit acknowledgements or qualifications.

The existing authoritative schema is `schemas/owner-decision-record.schema.json`. Do not create a replacement or parallel decision artifact family.

For a direct resource or Canon instruction, use the Owner's exact original words and the actual authorized scope; resource instructions also retain the actual limits. No earlier question or option set is implied.

## Execution contract

**Required execution capabilities for mandatory reasoning/compilation steps:** model reasoning plus reads of the actual Owner instruction or supplied decision surface and response, and the authoritative `OWNER_DECISION_RECORD` contract.

**Required capability for a durable-materialization claim:** `durable_artifact_write`.

**Supported execution modes:**

| Mode | Required capabilities | Claim/evidence boundary |
|---|---|---|
| compile-only | supplied/readable direct instruction or gate + response, and schema | May emit a schema-shaped candidate and clarification/schema-limit verdicts; must not claim a durable decision was recorded. |
| durable record | compile-only prerequisites + `durable_artifact_write` | May materialize and return an `OWNER_DECISION_RECORD` bound to the exact Owner instruction or response and any actual decision surface. |

**Conditional / optional capabilities:** schema validator when available. Validation strengthens structural evidence but never authorizes semantic inference.

**Mandatory evidence paths and equivalent fallbacks:** when options were presented, the selected option must be one member of that exact set and traceable through the decision-surface mapping or exact canonical wording in the Owner response. A direct resource or Canon instruction and any resource-specific normalization retain the exact original words inline. Material qualifications must be traceable to those words. There is no equivalent fallback for semantic ambiguity.

**Unsupported environment behavior:** if durable recording is mandatory but `durable_artifact_write` is unavailable, return `ASSIGNMENT_NOT_ADMISSIBLE` for the durable claim. If the response is ambiguous, return a bounded clarification requirement. Never weaken either failure into inferred consent.

## Required outputs

On an unambiguous answer to presented options, produce the repository's existing `OWNER_DECISION_RECORD` semantics with:

- `artifact_type: OWNER_DECISION_RECORD`;
- `produced_by_role: owner-interface`;
- `status: RECORDED` only for an actually materialized durable record;
- exact `question_ref`;
- exact canonical `options_presented`;
- exact canonical `selected_option`;
- explicit `owner_constraints` stated by Owner, without additions;
- explicit `qualifications` when present;
- `consequences_acknowledged` only to the extent actually acknowledged; an empty array is preferable to invented acknowledgement;
- required envelope/provenance/related-artifact fields from the current contract;
- optional authority/specialized fields only when the underlying authorized gate actually supplies their semantics.

On ambiguity or authority attack, produce no selected Owner decision record. Return only the bounded clarification/refusal result needed to preserve the original gate.

For an unambiguous direct resource instruction, use the same record with `resource_input_mode: DIRECT_INSTRUCTION`, the exact words in `resource_interpretation.source_text`, the actual resource-authority fields and no invented `question_ref`, `options_presented`, or `selected_option`. A bare amount, question or ambiguous discussion is not itself permission to spend. Preserve the original material constraints/qualifications; put only conditions not yet represented or actually resolved into `unresolved_constraints` and `unresolved_qualifications`. Do not attribute an unmentioned attempt limit, expiry or route restriction to the Owner. Any narrower task selection must follow the actual authorized work, not a fabricated Owner constraint.

For a genuinely authorized total spanning resource classes in one dimension, record one `resource_interpretation.shared_limits` entry with the Owner's total and the covered classes. If the Owner described the whole task budget, include every actually authorized class in that dimension, including relevant delegated operations; use a subset only when the Owner's scope actually limits it. An unmentioned protected finalization reserve is zero; any specified reserve is inside the total. Do not turn the total into independently spendable copies. The existing ledger can bind this entry to the original grant; ordinary decisions without a shared total need no new field or step.

When a previously selected complete shared view is mistaken or incomplete, the
responsible actor checks the same real Owner source and prepares a corrected
complete linked interpretation, retaining actual conditions and evidence. Use
the existing ledger selection snapshot and source fingerprint for explicit
replacement; do not merge alternative interpretations or ask the Owner to
repeat an already recorded decision. An actually corrected empty set is valid.
The assessment of the source remains the actor's responsibility.

If an existing grant's per-class limits misstate the recorded Owner decision,
check the same actual source and choose the complete corrected interpretation.
Use the existing ledger's explicit correction and reviewed snapshot; preserve
the original Owner record, grant, conditions, shared groups and consumption
history. A linked interpretation can correct the structured Owner limits too
when the original source actually supports it. Do not infer the corrected
amount or ask the Owner to repeat an existing decision.

For an unambiguous direct instruction authorizing an actual Canon operation, use `canon_input_mode: DIRECT_INSTRUCTION` and retain the Owner's exact words in `canon_instruction_text`, the real source in provenance, and actual constraints and qualifications. Bind the existing fields required by the applicable Canon workflow to the authorized operation and scope. Do not invent a question, options, selected option, acknowledgement or new Owner decision. A question, discussion, recommendation or mere mention does not itself authorize a mutation or transition; interpret the actual source and context before recording. The code checks record shape and bindings; it does not authenticate the speaker or understand arbitrary language.

When a previously recorded decision needs normalization, leave it intact and create a separate derived `OWNER_DECISION_RECORD` with a different ID, a `related_artifacts` link to the original decision, identical Owner response and authority-bearing terms, and the resource interpretation. Pass its ref through the existing resource admission; retain the original grant and its original authority reference. This is an interpretation of the earlier decision, not a new approval or budget. After actually establishing a condition from applicable, sufficiently fresh sources, record its original kind/index and real evidence refs in `condition_resolutions`; an explanatory note is optional. If an existing Director or Verifier review is used, also bind its ref and confirmed claim. A reference, entry, empty unresolved set, or role label alone does not prove the source was read, the Owner language understood, or the condition satisfied. Keep other unresolved conditions in force, honor any existing fact-specific readback or Verifier requirement, and do not invent a new Owner question, Executor result or Verifier when the actual evidence suffices.

## Deterministic normalization rules

### 1. Compact natural answer

If the response maps to exactly one presented label/canonical option, compile that exact option.

Example:

```text
Presented mapping:
"Keep current behavior" -> OPTION_A
"Use safer default" -> OPTION_B

Owner: "Safer default. Only for this release."
selected_option = OPTION_B
owner_constraints/qualifications preserve "Only for this release."
```

Do not store the human paraphrase as a new semantic option when a canonical option already exists.

### 2. Canonical answer

If Owner states `OPTION_B` exactly and it was presented, use `OPTION_B` without reinterpretation.

### 3. Bounded qualifications and constraints

Preserve every material Owner qualification. Do not:

- broaden "only for staging" into production authority;
- drop "not before audit";
- convert "prefer" into a binding constraint;
- convert a binding "only if" into optional prose.

Use `owner_constraints` for explicit binding limits and `qualifications` for other explicit decision qualifications. If the distinction is materially unclear, request clarification rather than silently classifying it.

### 4. Conditional choices

A condition that qualifies one selected option can be preserved when the existing record faithfully represents it, for example: "Choose B, but only after audit passes." -> `selected_option = B` plus the explicit condition in constraints/qualifications.

A branching choice such as "B if X, otherwise A" does not have one unconditional `selected_option`. Because the current schema exposes one required `selected_option`, do not manufacture either A or B. Return `SCHEMA_LIMITATION` with the exact representational gap unless the Owner resolves the branch into one current selection.

### 5. Ambiguous response

If multiple materially distinct options remain plausible, return `CLARIFICATION_REQUIRED` and ask only the smallest question needed to distinguish them. No record may claim a selection.

Examples that fail closed:

- "Either is fine" when A and B are materially distinct;
- "Go with that" when multiple referents are plausible;
- "yes" when the surface was not framed as one unambiguous yes/no mapping;
- response that selects one label but adds a qualification that materially conflicts with the option semantics.

### 6. Authority delegation attack

Owner input such as "use your judgment and approve for me" does not select a presented Owner-reserved option. Liaison may restate its prior recommendation but must return the unresolved Owner gate. No `OWNER_DECISION_RECORD` with a selected option is permitted.

## Procedure

For a direct resource or Canon instruction, first preserve the exact words and source, normalize only the actually authorized terms, and retain real conditions in the corresponding fields above. Do not invent a presented question, options, approval or a second budget. Validate and materialize the existing record as applicable. The steps below apply to a response to presented options.

1. Bind the response to the exact previously presented question and mapping.
2. Confirm that `options_presented` are the exact canonical options from that surface.
3. Extract only explicit selection language, constraints, qualifications, and acknowledgements from the Owner response.
4. Resolve the selection through the canonical option or deterministic human-label mapping.
5. If zero or multiple canonical options remain materially possible, return `CLARIFICATION_REQUIRED`; do not construct a selected record.
6. If the response attempts to delegate Owner authority to Liaison, refuse self-selection and preserve the gate.
7. If the response is an explicit conditional, determine whether it qualifies one selected option or encodes multiple future selections. For a multi-branch selection not faithfully representable by the current schema, return `SCHEMA_LIMITATION` rather than widening the schema.
8. Populate only fields supported by the existing schema and exact source semantics. Do not add authority scope that the Owner did not decide.
9. Validate structure when a validator is available. Structural validity does not cure semantic ambiguity.
10. Materialize `status: RECORDED` only when durable write capability is available and the semantic mapping is exact.
11. Return the durable record and affected state/control refs to Control Director. Liaison does not itself authorize the downstream transition.

## Existing schema authority

`schemas/owner-decision-record.schema.json` remains authoritative. This skill must not create:

- `OWNER_DECISION_RECORD_V2`;
- `LIAISON_DECISION`;
- `OWNER_AUTHORITY_PROXY`;
- any second Owner-decision artifact family.

If an essential bounded Owner answer cannot be represented without changing its meaning, stop with `SCHEMA_LIMITATION` and identify the exact missing representational capability. Do not redesign the schema inside this skill/workstream.

## Anti-patterns

Avoid:

- choosing the system recommendation because Owner did not object;
- treating silence, politeness, or "looks good" as a selection when the mapping is not exact;
- selecting an omitted option;
- dropping constraints to make the record fit;
- turning ambiguous reference words into consent;
- adding broader scope/authority than the question and response contain;
- creating a record after Liaison self-delegation language;
- treating schema-valid output as proof that the human actually made that decision.

These guard `E-OWNER-DECISION-PRESENTATION-GAP`, `E-MACHINE-FORM-LEAKAGE`, and `E-LIAISON-AUTHORITY-ESCALATION` while preserving the existing authority model.

## Verification checklist

- [ ] For an option response, the exact question and presented option set are bound.
- [ ] For an option response, the selected option maps to exactly one presented canonical option.
- [ ] For a direct resource or Canon instruction, exact Owner words, real source and only actually authorized terms are retained.
- [ ] No omitted option was inferred.
- [ ] Material Owner constraints and qualifications survive normalization.
- [ ] Consequence acknowledgement is not invented.
- [ ] Ambiguity returns clarification without a selected record.
- [ ] Authority delegation cannot become Liaison selection.
- [ ] Unsupported branching conditional choices fail with exact schema limitation.
- [ ] Existing `OWNER_DECISION_RECORD` remains the only decision record contract.
- [ ] Liaison creates no Canon, Control Director, Executor, verification, or promotion authority.

## Minimal verdict format

- Status: RECORDED / CANDIDATE_ONLY / CLARIFICATION_REQUIRED / SCHEMA_LIMITATION / ASSIGNMENT_NOT_ADMISSIBLE
- Question ref, options and selected canonical option, only for an actual option response
- Exact source words and unresolved resource conditions, for a direct instruction or resource interpretation
- Owner constraints
- Qualifications
- Consequences acknowledged
- Provenance refs
- Durable record ref, only when actually written
- Clarification or exact schema limitation, when applicable

