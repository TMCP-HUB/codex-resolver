---
name: owner-intent-sensemaking
description: Help a capable Liaison understand a raw Owner request using native LLM reasoning while preserving the boundary between Owner intent, model interpretation, proposal, evidence, and authority.
---

# Owner Intent Sensemaking

## Purpose

Guide the Liaison when a human request arrives before formal routing, assignment, or admitted control state exists.

This skill does not supply intelligence to the model. It focuses the model's existing language understanding and reasoning so Project Resolver can understand the Owner without prematurely turning conversation into governance machinery.

Core laws:

```text
PROJECT RESOLVER AUGMENTS NATIVE MODEL REASONING.
IT DOES NOT REPLACE IT.

SKILLS DO NOT REPLACE INTELLIGENCE.
SKILLS FOCUS INTELLIGENCE,
PRESERVE AUTHORITY,
AND PROVIDE REUSABLE METHODS.
```

## Goal

Reach the smallest useful understanding of what the Owner is trying to accomplish while keeping four things distinguishable:

- explicit Owner statements;
- strong implications supported by the current conversation;
- working interpretations proposed by the Liaison;
- material uncertainty that can change what should happen next.

Help the Owner think when useful. Do not merely paraphrase an underspecified idea and do not interrogate for completeness.

## When to use

Use this skill when:

- a fresh Owner request arrives before a governed route exists;
- the Owner expresses a raw or partially formed idea;
- ordinary language must be translated into a bounded working understanding;
- several plausible interpretations could lead to materially different work;
- the Liaison needs to decide whether it can safely continue, should ask one bounded question, or should frame the request for Project Resolver routing.

Do not use this skill to replace an already-authoritative Control decision, to reinterpret an exact assignment, or to reopen an already resolved Owner decision without evidence of changed intent/state.

## Inputs

Use only the bounded information relevant to the current request:

- the Owner's current words;
- directly relevant conversational context already available to the Liaison;
- current project identity/state only when explicitly supplied or already admitted;
- current authority/evidence facts only when actually known.

Do not require a repository, Canon, Research packet, execution profile, or full project history merely to understand ordinary human language.

## Execution contract

**Required execution capabilities for mandatory steps:** none beyond native model reasoning and the supplied conversational/context inputs.

**Supported execution mode:** ordinary in-chat reasoning, including `ORDINARY_CHAT`.

**Evidence boundary:** this skill may reason about what the Owner said and may form clearly labeled working interpretations. It may not claim unsupplied repository, browser, provider, research, production, or runtime facts as evidence.

**Authority boundary:** understanding, suggesting, reframing, or recommending does not create Owner/K0, Canon, Control Director, implementation, verification, or mutation authority.

External reads or tools are optional only when the request itself requires external facts; their need is decided downstream rather than assumed by this skill.

## Thinking guidance

Use judgment rather than a rigid questionnaire.

Consider, when useful:

- the underlying objective, not only the literal wording;
- the desired outcome or decision;
- protected intent or constraints the Owner appears to care about;
- assumptions that the Owner may not have stated explicitly;
- contradictions between requested outcomes and stated constraints;
- whether the Owner is exploring, asking for an answer, asking for project work, or authorizing a governed change;
- whether a proposed interpretation would make the next action substantially clearer.

You may improve the framing of an idea, propose alternatives, point out consequences, and test interpretations conversationally.

A model proposal remains a proposal. It must not become Canon, accepted Owner intent, or project authority merely because it is plausible or helpful.

## Clarification threshold

Ask only when different plausible answers would materially change the project, route, authority, output, or next action.

When the ambiguity is low-risk and a safe working interpretation is available, prefer stating a safe working interpretation and allowing the Owner to correct it over asking an exhaustive series of questions.

When clarification is required, ask the smallest question that resolves the material branch. Do not ask for fields simply because a downstream artifact might eventually contain them.

## Hard invariants

- MUST NOT invent Owner intent.
- MUST NOT silently convert a working interpretation or recommendation into an Owner decision.
- MUST NOT silently create Canon truth.
- MUST NOT claim external/runtime/project state without evidence.
- MUST NOT bypass Owner/K0 authority or another existing authority owner.
- MUST NOT globally load the repository or every skill merely to understand the request.

These invariants constrain authority and factual claims. They do not prohibit normal reasoning, ideation, explanation, inference, or useful proposals.

## Required outputs

Produce only what the current conversation needs, conceptually:

- a concise working understanding of the Owner's goal when useful;
- material constraints or protected intent already expressed;
- explicit uncertainty only where it matters;
- a bounded clarification question when required; or
- a sufficiently faithful framing for `project-context-orientation` / downstream routing.

No new durable artifact type is created by this skill.

## Procedure

1. Read the Owner's actual request as ordinary language before applying project machinery.
2. Identify the likely objective and desired outcome using normal LLM reasoning.
3. Separate explicit statements from working interpretations and proposals.
4. Notice only uncertainties that materially affect the next branch.
5. Where useful, improve or extend the idea with clearly non-authoritative suggestions.
6. If one bounded question is necessary, ask it; otherwise continue with the safest useful interpretation.
7. Hand the resulting working understanding to `project-context-orientation` when a routing/disposition decision is needed.

## Anti-patterns

Avoid:

- turning the Owner's first message into accepted Canon;
- converting brainstorming into a formal intake form;
- asking WHAT / WHY / FOR WHOM / CONSTRAINTS / NON-GOALS mechanically when the answer is already clear enough;
- treating every unknown as a Research request;
- treating every technical statement as a Software assignment;
- pretending that no skill means the model has no ability to reason;
- hiding a model-authored proposal inside language that sounds like settled Owner intent;
- loading all skills "for context".

## Verification checklist

- [ ] Explicit Owner statements remain distinguishable from model interpretation.
- [ ] Working interpretations and proposals are visibly non-authoritative.
- [ ] Any clarification is materially necessary and bounded.
- [ ] Native reasoning was used where safe rather than replaced by a checklist.
- [ ] No external fact/state was claimed without evidence.
- [ ] No Owner/K0, Canon, routing, implementation, verification, or mutation authority was created.
- [ ] The result is sufficient either to continue conversationally or to orient/rout the request without global skill discovery.
