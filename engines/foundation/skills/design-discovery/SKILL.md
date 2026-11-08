---
name: design-discovery
description: Optionally explore problem and solution shapes during Foundation formation without freezing architecture, inventing Owner intent, or creating a separate design authority artifact.
---

# Design Discovery

## Purpose

Provide optional exploratory reasoning when a raw project idea benefits from comparing interpretations, boundaries, solution shapes, or trade-offs before Canon.

This skill uses native model reasoning and judgment. It is not a mandatory phase for straightforward project formation and it does not create a `DESIGN_DISCOVERY_RESULT` durable artifact.

## Execution contract

**Mandatory cognitive capability:** native model reasoning over the bounded working project context.

**Selection boundary:** this skill is optional. Load it only when exploration materially improves the project seed, outcome, or unknown classification.

**Durable output boundary:** useful discovery may be folded into the three existing Foundation durable artifacts with provenance and proposal status preserved. Durable output does not create Owner/K0 authority or Canon authority.

**Evidence boundary:** comparisons may be conceptual. External factual or feasibility claims are not evidence unless separately obtained through the proper evidence path.

**Authority boundary:** a persuasive option, architecture sketch, or recommendation remains a model proposal until the proper Owner/Canon authority accepts it.

## Thinking guidance

Use the skill when the model and Owner would benefit from exploring rather than immediately formalizing one interpretation.

Possible reasoning moves include:

- propose alternative interpretations of the problem;
- compare solution shapes and project boundaries;
- simplify scope or separate concerns;
- expose contradictions between desired outcomes and proposed mechanisms;
- test whether a feature actually serves the target outcome;
- surface trade-offs and second-order consequences;
- identify assumptions that should remain open;
- distinguish reversible exploration from decisions that would later need authority.

Prefer a few materially different options over exhaustive possibility lists. Explain trade-offs in terms of the Owner's expressed goals and constraints.

Do not load this skill merely because an architecture topic exists. Straightforward project formation can proceed without it.

## Hard invariants

- MUST NOT invent Owner intent to make one option win.
- MUST NOT freeze architecture merely because one proposal appears plausible or technically elegant.
- MUST NOT promote a model proposal into accepted Canon or Owner/K0 authority.
- MUST NOT claim external facts or feasibility evidence that was not obtained.
- MUST NOT create a separate `DESIGN_DISCOVERY_RESULT` artifact in Foundation V0.
- MUST preserve material disagreement, alternatives, or unresolved trade-offs when collapsing them would distort the working project state.

These invariants protect authority/evidence boundaries; they do not prevent creative reasoning, strong recommendations, or simplification.

## Procedure

1. Identify the specific project ambiguity, trade-off, or scope question that makes exploration useful.
2. Generate only materially distinct interpretations or solution shapes.
3. Compare them against the working outcome, Owner constraints, and protected intent.
4. State recommendations as model proposals, not settled Owner intent or Canon.
5. Preserve consequential unresolved trade-offs in the unknown map when appropriate.
6. Fold useful, still-non-authoritative discovery into `PROJECT_SEED`, `PROJECT_OUTCOME`, or `CONSEQUENTIAL_UNKNOWN_MAP` rather than creating a fourth artifact.
7. Return to the main formation workflow as soon as the exploration has made the working foundation clearer.

## Stop condition

Stop when further exploration no longer changes the current seed, outcome, consequential unknowns, or the next material Owner question.
