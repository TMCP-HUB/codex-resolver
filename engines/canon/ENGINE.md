# Canon Engine

`engines/canon/` owns the bounded lifecycle of **accepted project Canon**: establishing a Canon Foundation, registering explicit Canon state, reconciling evidence-backed findings into proposed Canon changes, classifying production-time Canon change, validating Canon coherence, freezing authorized Canon states, and reopening frozen Canon only through explicit authority.

Canon is an explicit governed declaration about the project that downstream work must preserve until it is explicitly superseded. A statement does not become Canon merely because it appears in research, implementation, prose, code, a test, a translation, a fixture, a report, or chat history.

## Ownership boundary

Canon Engine owns:

- Canon Foundation 0.x state construction and controlled freeze;
- accepted facts, protected values, assumptions, unknowns, intended ambiguities, contradictions, canonical registries and accepted decisions as governed Canon state;
- proposed and accepted Canon change records;
- research-to-Canon reconciliation **after** Research has produced evidence/findings;
- internal Canon validation and freeze-readiness checks;
- Canon freeze/reopen transitions when the assignment carries the required authority;
- Canon lifecycle support through 0.x, 1.0, production-time changes, final reconciliation and 2.0.

Canon Engine does **not** own:

- Owner/K0 authority or protected Owner intent itself;
- substantive Research truth generation, evidence collection, source evaluation, or research sufficiency decisions;
- Production Foundation design or downstream production organization;
- software implementation, narrative/manuscript production, translation/refraction, or interactive runtime realization;
- generic independent verification or release authority;
- universal artifact ontology, K0 routing, autonomous orchestration, or permanent agent personalities.

A Canon workflow may validate its own internal preconditions. That does not replace independent Verification Engine work when independent verification is required.

## Canon maturity lifecycle

When governed Canon formation is requested, a Canon Foundation 0.x may lead to Canon 1.0 when the accepted outcome and applicable authority support it. This is not a prerequisite for every bounded task.

- Research is selected only when the outcome needs it. When applicable Research exists, reconcile its relevant evidence and findings through the existing Canon authority boundary before relying on them.
- A required but unresolved Research question or other genuine outcome-scope blocker remains a blocker. If Research is not needed, do not invent Research or reconciliation artifacts.
- Production Foundation and Production follow only when realization is requested. Final production-era reconciliation and Canon 2.0 apply to that path; Canon 1.0 may itself satisfy a Canon-only outcome.

### Canon Foundation 0.x

A 0.x Foundation captures enough explicit Owner authority to create a stable project baseline; it may support Research entry when Research is needed. It may intentionally contain assumptions, unknowns, unresolved contradictions, and explicit ambiguities. Freezing 0.x freezes the **known authority boundary and the explicit unknown state**; it does not pretend the unknowns are researched truth.

### Canon 1.0

Canon 1.0 is sufficient and authorized for the requested outcome, with applicable evidence and unresolved items dispositioned in its declared scope. Where Research is needed and produces relevant findings, current Research reconciliation is required; findings are not accepted Canon by themselves. No Research or Research reconciliation is required merely because the maturity is 1.0. Downstream Production Foundation and production are conditional on the requested outcome and its governing acceptance/freeze authority.

### Canon 2.0

Canon 2.0 is the final production-era reconciliation/freeze. It incorporates authorized production-era Canon changes and explicit final decisions. Post-2.0 change must use an explicit lifecycle mode: `ADDENDUM`, `EXPANSION`, `NEW_EDITION`, or `REOPEN`. Silent retcon is forbidden.

## Research boundary

When Research is used as input to a Canon change, its authority chain is:

```text
RESEARCH
→ EVIDENCE / FINDINGS
→ CANON RECONCILIATION
→ PROPOSED CANON CHANGE
→ EXPLICIT CANON AUTHORITY DECISION
→ ACCEPTED CANON
```

Never:

```text
RESEARCH → automatic Canon mutation
```

An implementation observation has the same boundary: it may motivate a change proposal, but `IMPLEMENTATION FACT != CANONICAL FACT`.

## Canon Foundation vs Production Foundation

Canon Foundation answers: **what is protected, accepted, assumed, unknown, ambiguous, contradictory, or decided for the project?**

Production Foundation answers: **how will a specific production be organized and built?**

The Canon Engine owns the first boundary only.

## Production-time Canon change classes

- **A — ENRICHMENT:** adds compatible detail without changing protected meaning or closing an explicitly open decision.
- **B — CLOSURE:** resolves a previously explicit unknown/open decision inside an already authorized scope.
- **C — PRODUCTION-REQUIRED CANONICAL CHANGE:** production exposes a change required for coherent realization; affected production pauses until explicit Canon authority resolves it.
- **D — CORE CHANGE / RETCON:** changes or contradicts protected/core Canon. This is a controlled stop/gate, never a silent production mutation.

These classes are Canon-specific and do not inherit the historical source repository's generic A–E change taxonomy.

## Durable artifacts

Canon workflows use durable state-bearing artifacts rather than chat memory. Core artifact types are:

- `CANON_FOUNDATION`
- `CANON_STATE`
- `CANON_CHANGE_PROPOSAL`
- `CANON_RECONCILIATION_RESULT`
- `CANON_FREEZE_RECORD`

Shared Project Resolver artifact/state/authority contracts remain normative; Canon does not create a competing universal artifact protocol.

## Roles

This migration creates no Canon personality or permanent agent role. Existing reusable roles are sufficient:

- `roles/executor/ROLE.md` performs bounded Canon work when the assignment authorizes it;
- `roles/control-director/ROLE.md` consumes results and manages gates/continuation within its authority;
- `roles/control-verifier/ROLE.md` remains owned by Verification Engine for independent claim verification.

## Progressive disclosure

Root routing selects `canon` only for semantic Canon capabilities. After selection, load `engines/canon/MANIFEST.yaml`, then only the selected workflow and required skill(s). Do not globally load this engine or recursively discover its skills.
