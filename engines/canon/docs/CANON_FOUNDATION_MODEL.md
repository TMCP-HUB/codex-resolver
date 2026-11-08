# Canon Foundation Model

This model preserves the useful general semantics of the source `SEED_CANON_MODEL.md` while removing book-only assumptions and aligning the state model to Project Resolver.

## Purpose

Canon Foundation 0.x is the smallest durable governed state needed for the actual project outcome; it can support Research when needed without pretending that Research has already happened.

It captures:

- explicit Owner intent and authority boundaries;
- protected values/invariants that must not be casually optimized away;
- currently accepted supplied facts;
- explicit assumptions;
- explicit unknowns;
- explicitly protected ambiguities;
- known contradictions/conflicts;
- accepted decisions already made;
- provenance/source references;
- applicable Research-entry scope and freeze record, where those are needed.

It is not a Production Foundation and does not define how the downstream production will be staffed, structured, written, coded, translated, or released.

## Evidence and inference

Every substantive Foundation claim must be distinguishable as one of:

- explicit Owner/authorized decision;
- supplied fact accepted within the current authority scope;
- assumption;
- inference/proposal;
- unknown;
- intended ambiguity;
- contradiction/conflict.

Inference never becomes accepted merely because it is plausible. A structured registry entry never becomes Canon merely because it has an ID.

## Stable identity

Addressable Canon records use stable semantic IDs independent of file path, prose line, database row, chat turn, or temporary agent instance. IDs must be unique in the relevant namespace and preserve version/provenance lineage.

## Protected values

Protected values express meanings, constraints, rights, invariants, exclusions, or other Owner-authorized project commitments that should not be flattened for convenience. The Engine may record or propose them; it may not invent or accept protected Owner intent without authority.

## Facts

Facts are atomic scoped propositions. Registration should separate statements that can change independently, retain provenance, and detect existing semantic identity before creating a duplicate.

## Assumptions

Assumptions make temporary reliance explicit. Each assumption should state:

- proposition;
- why it is being assumed;
- scope;
- risk if false;
- what evidence/decision could resolve it;
- downstream surfaces that must revalidate when it changes.

An assumption can be accepted **as an assumption** while still not being accepted as factual truth.

## Unknowns

Unknowns are first-class state, not omissions. Each unknown should identify the unresolved question, why it matters, affected scope, whether it blocks the current gate, and the expected resolution path where known.

A Foundation 0.x freeze may include unknowns. Canon 1.0 may retain nonblocking unknowns outside the declared outcome/freeze scope or where their disposition is covered by the governing authority. Unresolved blockers inside the actual outcome scope remain blockers; reuse already-authorized dispositions rather than asking again. Unknown is never silently relabeled as ambiguity.

## Intended ambiguity

Intended ambiguity is an explicit protected decision. Record:

- unresolved proposition/dimension;
- audience/scope to which ambiguity applies;
- allowed readings where authority supports naming them;
- forbidden collapses;
- downstream preservation requirements.

Do not make the allowed set artificially exhaustive when doing so would narrow the intended ambiguity.

## Contradictions

Contradiction registration should classify the smallest conflicting proposition set where possible. Useful classes retained from the source model include:

- direct semantic conflict;
- temporal/ordering conflict;
- identity conflict;
- terminology/definition conflict;
- dependency conflict;
- intentional tension;
- scoped apparent conflict;
- nonblocking duplication;
- unresolved authority conflict.

Blocking conflicts between equal accepted authorities require explicit resolution/change control; no carrier wins because it was read last.

## Canon State when Research is used

Research is conditional on the actual outcome. When used, Research produces evidence/findings, not project acceptance. Reconciliation compares Research outputs to Foundation/current Canon and produces a `CANON_RECONCILIATION_RESULT` containing explicit proposed actions such as:

- ACCEPT / ADD a supported Canon proposition;
- REJECT a proposed proposition;
- RETAIN an existing Canon proposition;
- SUPERSEDE an existing proposition;
- CLOSE an unknown;
- RETAIN an unknown;
- REGISTER / PRESERVE ambiguity;
- REGISTER / RESOLVE contradiction;
- REQUIRE OWNER DECISION;
- DEFER outside scope.

Only the authority governing the affected Canon state can convert those proposals into accepted mutation.

## Minimal completeness

Canon is not improved by maximal specification. A scope is sufficiently explicit when downstream consumers can distinguish:

- what is protected/required;
- what is accepted fact;
- what is assumption;
- what is unknown;
- what must remain ambiguous;
- what conflicts are known;
- what has been decided;
- what may vary;
- what evidence/authority supports each governed claim.

Over-specification is a defect when it removes freedom not required by project authority.
