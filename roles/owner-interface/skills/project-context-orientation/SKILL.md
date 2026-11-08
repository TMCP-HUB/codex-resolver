---
name: project-context-orientation
description: Orient a Liaison to the kind of conversational/project situation a raw Owner request belongs to and choose RESPOND_IN_PLACE, CLARIFY, or ROUTE without becoming the Router or creating a new artifact ontology.
---

# Project Context Orientation

## Purpose

Determine whether the current Owner request should remain ordinary conversation, needs one bounded clarification, or should enter governed Project Resolver routing.

This skill works after or alongside `owner-intent-sensemaking`. It classifies the conversational/project situation at a lightweight reasoning level. It does not perform Engine selection, executability admission, authority creation, or assignment compilation.

## Goal

Choose the smallest useful next disposition while avoiding two opposite errors:

- forcing every question through Project Resolver machinery;
- treating real governed project work as casual chat with no authority/state boundary.

The only intake dispositions are:

```text
RESPOND_IN_PLACE
CLARIFY
ROUTE
```

These are behavioral dispositions, not a new artifact ontology and not Control Director terminal states.

## When to use

Use this skill when the Liaison has a sufficient working understanding of the Owner request and must decide whether Project Resolver machinery is actually needed.

Useful internal working frames include:

- ordinary question / conversation;
- existing-project work;
- new project / raw idea;
- continuation of already-governed work;
- genuine Owner decision;
- request to inspect external state;
- request to change external state;
- materially unclear request.

These frames are reasoning aids only. They are not durable enums, schemas, authority records, or a second routing ontology.

## Inputs

Use:

- the current Owner request;
- the bounded working understanding from `owner-intent-sensemaking`, when applicable;
- explicit known project/control state already available;
- root capability awareness from Project Resolver manifests/router only when routing is a plausible next action.

Do not inspect every Engine, workflow, repository path, or skill by default.

## Execution contract

**Required execution capabilities for mandatory steps:** none beyond native model reasoning and reads of already-supplied/root control context.

**Supported execution mode:** ordinary in-chat reasoning, including `ORDINARY_CHAT`.

**Evidence boundary:** this skill may classify the nature of the request from supplied context. It cannot prove remote/runtime/repository facts that were not observed.

**Authority boundary:** this skill does not become the Router. `ROUTE` means the request should be handed to existing Project Resolver routing/control semantics, not that the Liaison has acquired Engine-selection, assignment, or execution authority.

## Disposition guidance

### `RESPOND_IN_PLACE`

Prefer when the request can be answered or explored correctly with native LLM reasoning/current chat capabilities and no governed project transition is required.

Examples include:

- ordinary question or explanation;
- conceptual comparison;
- lightweight ideation/discussion;
- a request for general reasoning where no durable project state or external fact claim is required.

No Engine required merely because Project Resolver is loaded.

### `CLARIFY`

Use only when a material ambiguity prevents a safe useful response or faithful route.

The clarification should resolve the smallest branching uncertainty. It must not become a generic intake questionnaire.

### `ROUTE`

Use when the request requires one or more of:

- governed project state;
- an existing Engine/workflow responsibility;
- durable Canon/Foundation/Research/Production semantics;
- external inspection or mutation;
- independent verification;
- exact assignment/control/evidence semantics;
- another authority-bearing Project Resolver transition.

`ROUTE` hands a faithful bounded framing to the existing Router/control chain. It does not preselect a commercial provider or execution surface.

## Domain orientation guidance

When routing appears necessary, reason only far enough to identify the plausible owned domain before progressive disclosure continues.

Examples:

- raw idea intended to become a project -> Foundation / Project Formation ownership under #53;
- software implementation or diagnosis -> Software Engine;
- external factual uncertainty material to a project decision -> Research candidate, but Research only when the uncertainty actually requires evidence;
- independent claim checking -> Verification;
- governed project truth formation/change -> Canon, after the appropriate Foundation/authority boundary;
- genuine Owner/K0 decision -> Owner Interface decision path rather than an executor route.

Do not force all useful reasoning into one of these domains. Native reasoning remains available before and between governed transitions.

## Required outputs

Return conceptually:

- one disposition: `RESPOND_IN_PLACE`, `CLARIFY`, or `ROUTE`;
- the minimal reason for that disposition;
- when `CLARIFY`, the one bounded question needed;
- when `ROUTE`, a faithful bounded request framing and any material Owner constraints already known.

These outputs are conversational/control guidance, not new durable artifact types.

## Procedure

1. Start from the Owner's actual request and current working understanding.
2. Ask whether a correct useful response requires governed project state, external evidence/action, or an authority-bearing transition.
3. If not, choose `RESPOND_IN_PLACE` and use native model reasoning.
4. If the branch is materially ambiguous, choose `CLARIFY` and ask only the smallest resolving question.
5. Otherwise choose `ROUTE` and pass the bounded framing into existing Project Resolver routing.
6. When routing, use progressive disclosure: know capabilities from root control surfaces, inspect only the plausible Engine/workflow, and load exact skills only after the owned question is selected.

## Hard invariants

- MUST NOT create a second Router or parallel routing ontology.
- MUST NOT convert these behavioral dispositions into new mandatory artifacts merely for intake.
- MUST NOT invent Owner intent, authority, external state, or runtime capability.
- MUST NOT choose a provider/product where existing control/executability semantics own that choice.
- MUST NOT globally discover/load all skills to decide whether a route might exist.

## Anti-patterns

Avoid:

- "Project Resolver is loaded, therefore every question needs an Engine";
- "No domain skill selected, therefore the LLM cannot answer";
- routing ordinary explanation into Software/Research/Canon unnecessarily;
- launching Research for every unknown before reasoning about whether the fact matters;
- jumping directly from a raw idea to accepted Canon;
- treating repository-orientation as a prerequisite for understanding every Owner request;
- turning `RESPOND_IN_PLACE | CLARIFY | ROUTE` into a new schema family.

## Verification checklist

- [ ] Exactly one intake disposition is clear.
- [ ] Ordinary questions can remain ordinary conversation.
- [ ] Clarification is bounded to a material branch.
- [ ] Routed work is framed faithfully without Liaison acquiring Router authority.
- [ ] New-project ideas point toward Foundation before governed Canon formation.
- [ ] Research is used only where consequential external evidence is actually needed.
- [ ] Existing-project work can reach current Engine/workflow semantics through progressive disclosure.
- [ ] No new authority, provider state, runtime state, or artifact ontology was invented.
