---
name: establish-canon-foundation
description: Build or update a project-neutral Canon Foundation 0.x from explicit Owner or authorized inputs without inventing truth or production design.
---

# Purpose and goal

Build a bounded 0.x candidate from the actual outcome, working material and authorized decisions while preserving what is known, proposed and unresolved.

# When to use

Use when an authorized assignment actually requests Canon Foundation; ordinary bounded work does not require full formation.

# Design basis

This skill follows the Project Resolver Canon Foundation 0.x authority contract.

# Inputs

Exact project identity, supplied Owner/authorized material, authority scope, optional existing Foundation, and relevant available `PROJECT_SEED`, `PROJECT_OUTCOME` and `CONSEQUENTIAL_UNKNOWN_MAP` with their provenance and already-recorded decisions. These working inputs are not themselves Canon or acceptance authority; do not require artifacts that do not exist when other authorized inputs suffice.

# Procedure

1. Inventory relevant supplied intent, protected values, facts, decisions, assumptions and unresolved questions. When present, use the seed's explicit Owner statements/known decisions separately from its working interpretations and model proposals; use the outcome to understand target, scope and completion, not as automatic acceptance.
2. Label each item by its actual support and authority: explicit decision, supplied fact, assumption, inference/proposal or unknown. Check the original decision/provenance before carrying an item as accepted. Reuse prior authorization within its actual scope; do not re-ask an already settled decision or present an unaccepted model proposal as Owner intent.
3. Preserve the smallest stable constraints that would materially change project identity if removed; do not force a philosophical thesis or narrative structure.
4. Create stable semantic IDs independent of file/chat location. When the accepted project outcome depends on overloaded domain terms (for example, "user" vs "customer"), distinguish meanings and aliases against actual approved Owner language; carry resolved terms with their existing semantic IDs and provenance. Represent a genuinely unresolved collision through existing unknown/contradiction handling, rather than silently inventing a meaning or reopening an already accepted decision. A project glossary, if specifically useful and authorized, is a readable projection of supported terms, **not** an independent Canon truth source or mandatory new file.
5. Initialize 0.x as `PROPOSED` unless explicit authority permits another state.
6. Carry relevant unknown-map IDs and questions into existing Canon unknown records, preserving their source/provenance. Derive scope and blocking from the actual outcome and available evidence; if their status is genuinely unresolved, report that limit rather than declaring a blocker resolved or inventing an answer. Preserve classification and reasons through existing source references; do not add unsupported schema fields or convert missing decisions into intended ambiguity.
7. Record actual input/provenance and authority refs in the existing envelope, `source_refs`, `related_artifacts` and record fields as appropriate. A proposal's source or authorization to propose is not acceptance of its content. If a required reference cannot be established, keep that material working and report the concrete limit; never invent authority.
8. Return an envelope-compatible `CANON_FOUNDATION` candidate and required follow-up registrations.

# Stop

Stop if explicit Owner authorities conflict, source evidence is too contradictory for a bounded proposal, or an existing frozen scope would be superseded without change authority.

# Invariant

Creation of a well-formed Foundation creates structure/proposal state, not acceptance authority. Existing authorized decisions can be materialized within their approved scope without repeating them; new substantive Canon acceptance still needs its actual authority.

# External reference (method only)

[Matt Pocock's `domain-modeling` at consulted commit 4ae2317d](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/domain-modeling/SKILL.md) (MIT) suggests disambiguating meaningful terminology and recording resolved language. This is **not** authority to create a parallel `GLOSSARY.md`/ADR canon, force an Owner interview, or replace Resolver's semantic IDs, provenance and frozen Canon lifecycle.

# Verification and anti-patterns

Check that source lineage, proposal/acceptance status, unknowns and authorized scope match the actual input and existing schema. Do not require Research, a new handoff artifact or a new Owner approval merely to use this skill.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound Canon reasoning over supplied or already-resolved artifacts.

**Conditional / optional capabilities:** none by default. External acquisition or repository/runtime operations must be separately declared by the exact assignment/workflow.

**Mandatory evidence path:** emit the `CANON_FOUNDATION` artifact with the common Project Resolver envelope, exact input-state binding, provenance, and related-artifact refs.

Missing mandatory durable-output capability means `ASSIGNMENT_NOT_ADMISSIBLE`.
