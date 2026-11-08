---
name: classify-consequential-unknowns
description: Classify unresolved project uncertainty by consequence and ownership without automatically resolving it, dispatching Research, or turning architecture questions into authority.
---

# Classify Consequential Unknowns

## Purpose

Keep material uncertainty explicit while helping the model decide what kind of unknown it is and why it matters.

This skill uses native reasoning and judgment to create or refine the non-authoritative `CONSEQUENTIAL_UNKNOWN_MAP`. Classification is not resolution.

## Execution contract

**Mandatory cognitive capability:** native model reasoning over the working seed, working outcome, explicit Owner material, and bounded relevant context.

**Durable output boundary:** the Foundation workflow may require `CONSEQUENTIAL_UNKNOWN_MAP` to be materialized through the generic durable-output path. Durable output does not create Owner/K0 authority or Canon authority.

**Evidence boundary:** the model may recognize that an item needs evidence. It may not claim that external evidence, feasibility proof, repository proof, or current-world verification exists when it has not been obtained.

**Authority boundary:** classification may identify a likely next owner or later evidence need. It is not Research dispatch, an Owner decision, architecture authority, Canon acceptance, or Production authorization.

## Thinking guidance

Materialize only unknowns whose resolution or continued uncertainty can affect the project, route, authority, output, scope, risk, or next action.

Use exactly these V0 classes:

- `OWNER_PREFERENCE` — a value/trade-off the Owner must choose or accept; evidence may inform it but cannot choose it for the Owner.
- `EXTERNAL_FACT` — a consequential factual claim that may later need an evidence-backed Research path.
- `FEASIBILITY` — whether something can actually be done under relevant conditions; may later require evidence, experiment, or prototype.
- `ARCHITECTURE_DECISION` — a consequential design choice that may need exploration/evidence and proper authority before it becomes protected project truth.
- `IMPLEMENTATION_DEPENDENT` — cannot be usefully resolved until relevant implementation context exists.
- `NICE_TO_KNOW` — potentially interesting but not currently consequential enough for the critical path.

Use judgment when an item touches several categories. Classify it by the next meaningful ownership/evidence question rather than multiplying duplicate unknowns.

Non-consequential unknowns need not be materialized merely for completeness.

## Hard invariants

- MUST NOT convert `OWNER_PREFERENCE` into a machine-selected Owner decision.
- MUST NOT treat `EXTERNAL_FACT` or `FEASIBILITY` as proven without evidence.
- MUST NOT treat `ARCHITECTURE_DECISION` as architecture authority or accepted Canon merely because one option looks best.
- MUST NOT automatically dispatch Research because a researchable unknown exists.
- MUST NOT promote the durable unknown map into Owner/K0 or Canon authority.
- MUST preserve why each materialized unknown matters so downstream work can decide whether it remains consequential.

## Procedure

1. Read the working seed and outcome and identify unresolved items that can materially affect the project.
2. Drop or defer uncertainty that is not consequential at the current stage.
3. Classify each retained item using exactly one V0 class that best expresses the next ownership/evidence problem.
4. State why the item matters downstream.
5. Mark it `OPEN` or `DEFERRED` according to current relevance, without pretending deferred means resolved.
6. Preserve provenance and references to the seed/outcome where useful.
7. Return the non-authoritative classification map to the Foundation workflow; do not dispatch or decide the next subsystem from this skill alone.

## Boundary reminders

Classification is not resolution. A Research candidate is not Research dispatch. An Owner preference is not an Owner decision. An architecture question is not architecture authority. A durable unknown map is not Canon.
