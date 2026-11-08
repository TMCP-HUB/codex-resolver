---
name: owner-decision-surface
description: Transform a genuine Owner/K0 control gate into a usable Owner decision surface without changing option semantics or creating authority.
---

# Owner Decision Surface

## Purpose

Use this skill only after `owner-actionability` has established that a genuine Owner/K0 decision is required.

## Goal

Convert the authoritative machine/control gate into a cognitively usable Owner decision surface while preserving the exact decision semantics, admissible options, material consequences, and authority boundary.

```text
HUMAN-FRIENDLY PRESENTATION != NEW DECISION SEMANTICS
```

## When to use

Use this skill when:

- an existing control gate is explicitly Owner/K0-reserved;
- the Owner must approve a system recommendation because authority remains Owner-reserved;
- the Owner must choose among materially distinct admissible options;
- a large genuine Owner decision set needs batching or natural labels.

Do not use this skill when:

- a machine role can resolve the item under existing authority;
- the system already has an authorized/admitted next action;
- the problem is only execution-surface routing;
- the required action is a manual external operation rather than an Owner preference/authority choice;
- options, consequences, or authority are too incomplete to present faithfully.

## Inputs

Require the authoritative decision gate or an exact equivalent containing enough information to preserve:

- exact question semantics and question/control reference;
- which authority owns the decision;
- complete admissible option set;
- option consequences and material constraints/qualifications;
- machine-resolvable items already distinguished from Owner-reserved items;
- system recommendation/default when evidence supports one;
- what control will do after a valid Owner decision.

Do not invent missing options or consequences. Request bounded upstream clarification from the responsible control role when they are material.

## Execution contract

**Required execution capabilities for mandatory steps:** none beyond model reasoning and reads of the supplied authoritative gate/control artifacts.

**Supported execution modes:**

| Mode | Required capabilities | Claim/evidence boundary |
|---|---|---|
| assignment-bound reasoning | supplied decision gate | May transform presentation only; cannot prove missing option admissibility or consequences. |
| artifact-backed reasoning | readable authoritative gate/result refs | Same presentation transformation with durable provenance refs. |

**Conditional / optional capabilities:** artifact reads when gate details are referenced rather than supplied inline.

**Mandatory evidence path and equivalent fallbacks:** every human option must map one-to-one to an exact underlying machine option from the authoritative gate. Recommendation and consequence statements must be traceable to supplied evidence/control facts. There is no equivalent fallback for missing material gate semantics.

**Unsupported environment behavior:** if the gate cannot be read or a deterministic mapping cannot be established, return a bounded upstream clarification requirement. Do not improvise a new Owner question.

## Required outputs

Produce a decision surface that contains:

- a plain-language decision question;
- why Owner/K0 authority is genuinely required;
- only the genuine Owner decision dimension(s);
- human-readable labels for every admissible option;
- an internal deterministic mapping from each label to the exact canonical/machine option;
- material consequences and constraints for each option;
- system recommendation/default when supported, visibly non-binding;
- what happens after the Owner decides;
- question/control provenance needed by `owner-response-recording`;
- batching metadata or ordering when the decision set is large.

The mapping/provenance layer is for deterministic compilation and need not be exposed as raw machine form in the default Owner view.

## Gate classification

Before presenting any choice, classify each unresolved item:

| Item class | Present as Owner choice? | Handling |
|---|---:|---|
| machine-resolvable | no | return to the responsible machine/control path; never ask Owner to decide it as preference |
| system recommendation/default requiring Owner approval | yes | show the recommendation and why, but require explicit Owner selection/approval |
| genuine Owner preference/authority choice | yes | present the admissible options and consequences |
| recovery/escalation condition | not by default | present only if the Owner truly owns a required recovery decision; otherwise keep it in control |

Only the second and third rows enter the Owner decision set, and only when authority is actually Owner-reserved.

## Procedure

1. Bind the surface to the exact decision gate and question/control ref.
2. Separate machine-resolvable, recommended-with-approval, genuine Owner choice, and recovery/escalation items.
3. Remove machine-resolvable/internal-routing items from the Owner choice set without deleting them from the underlying control state.
4. For each genuine Owner decision, preserve the complete admissible canonical option set.
5. Assign concise natural-language labels. Each label must map deterministically to exactly one canonical option, and each presented canonical option must have exactly one unambiguous label within that decision.
6. Translate consequences and constraints into plain language without weakening, adding, or normalizing away material qualifications.
7. Show a system recommendation only when supported by supplied evidence. Label it as a recommendation, never as the selected option or as authority.
8. State what happens after a valid choice.
9. If the set is large, split it into cognitively manageable groups while preserving a stable decision/question identity and complete option mapping across batches.
10. Provide the decision surface and its hidden/internal mapping to `owner-response-recording` for exact compilation after the Owner replies.

## Progressive disclosure

Default Owner view should contain only what is needed to decide:

1. the decision in human terms;
2. why the Owner is needed;
3. options and meaningful consequences;
4. recommendation, if any;
5. what happens next.

Raw schemas, machine disposition vocabulary, internal IDs, capability profiles, control packets, and repetitive row-level mechanics remain hidden by default. They may be exposed on explicit audit request or when genuinely necessary to distinguish options.

## Batching law

Large genuine Owner decision sets must not be dumped as one raw form. Batch by a stable decision dimension, dependency boundary, or manageable group. Batching may change presentation order, but must not:

- omit an admissible option;
- merge materially distinct options;
- split one option into new semantic variants;
- change the canonical mapping between batches;
- imply that a recommendation is already approved.

## Natural-label mapping

A valid decision surface retains an internal mapping such as:

```text
"Use the safer default" -> OPTION_B
"Keep the current behavior" -> OPTION_A
```

The Owner may answer with the human label, the canonical option, or an unambiguous natural equivalent. `owner-response-recording` must compile only through this mapping and the actual Owner words; the Liaison does not infer an omitted choice.

## Authority boundary

The decision surface can explain and recommend, but it cannot:

- select an Owner-reserved option;
- turn a machine recommendation into Owner consent;
- add an option that was not admitted by the upstream gate;
- change Canon truth;
- authorize implementation, verification, promotion, or execution;
- create K0 authority through persona or prompt wording.

A request such as "use your judgment and approve for me" leaves the Owner gate unresolved. The Liaison may restate the recommendation but must not produce a selected Owner decision.

## Anti-patterns

Avoid:

- asking Owner to resolve a machine-resolvable uncertainty;
- asking Owner to choose ChatGPT/Codex/Agent System when topology is a control problem;
- dumping raw disposition codes or internal IDs as the default UI;
- presenting dozens of repetitive rows without batching;
- hiding a material option qualification for brevity;
- phrasing a recommendation as "we chose" or "approved";
- creating a synthetic option such as "Liaison decides";
- silently dropping options that are inconvenient to explain.

These guard `E-OWNER-DECISION-PRESENTATION-GAP`, `E-HUMAN-GATE-COGNITIVE-OVERLOAD`, `E-MACHINE-FORM-LEAKAGE`, `E-CONTROL-PLANE-LEAKAGE`, and `E-LIAISON-AUTHORITY-ESCALATION` without creating a new global error ontology.

## Verification checklist

- [ ] The gate is genuinely Owner/K0-reserved.
- [ ] Machine-resolvable items are absent from the Owner choice set.
- [ ] Every human label maps to exactly one admitted canonical option.
- [ ] Every presented option preserves its material consequences and constraints.
- [ ] Recommendation is supported and visibly non-binding.
- [ ] No raw schema/control form is required for the default Owner interaction.
- [ ] Large sets are batched without semantic drift.
- [ ] The surface states what happens after the decision.
- [ ] Authority attack cannot result in Liaison self-selection.
- [ ] The resulting surface contains enough provenance/mapping for exact response recording.

## Minimal verdict format

- Decision gate ref
- Genuine Owner decisions presented
- Machine-resolvable items suppressed from Owner choice set
- Human labels -> canonical option mapping
- Recommendation, if any
- Consequences/constraints preserved
- Batch/group, if any
- Next system action after decision
- Status: READY_FOR_OWNER / NEEDS_UPSTREAM_CLARIFICATION
