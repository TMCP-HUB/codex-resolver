# Project Resolver — Machine-Only Research Constitution

Status: KERNEL INVARIANT  
Authority: OWNER / K0  
Default research mode: `MACHINE_ONLY`

## Constitutional invariant

The default Project Resolver Research Engine performs research end-to-end by machine.

`OWNER / K0` is the only default human actor. Owner/K0 supplies project authority and project decisions; Owner/K0 is not ordinary research labor.

**PROHIBITED:** recruiting, surveying, interviewing, testing, consulting, annotating, rating, reviewing, coding, panel work, field work, or otherwise introducing non-owner humans into ordinary Research Engine execution.

Pre-existing public or otherwise lawfully machine-accessible human-generated material may be analyzed as source provenance. Such people are not project actors.

Computational, corpus, structural, typological, simulation, model, and multi-model proxies are permitted when explicitly labeled. `UNKNOWN`, `INSUFFICIENT_EVIDENCE`, `PROXY_ONLY`, and `UNMEASURED_HUMAN_CONSTRUCT` are valid outcomes.

Unavailable direct measurement never creates authority to recruit humans.

Human research is reachable only through a separate, explicitly OWNER/K0-authorized human-research workstream. Authorization is bounded to one exact project and exact research question and never changes this default constitution.

## Default-deny controls

Every admitted default research question and work package MUST prove all of the following:

- `MACHINE_EXECUTABLE = true`
- `REQUIRES_THIRD_PARTY_HUMAN = false`
- `REQUIRES_OWNER_MANUAL_RESEARCH = false`
- `REQUIRES_EXTERNAL_HUMAN_REVIEW = false`
- `REQUIRES_HUMAN_DATA_COLLECTION = false`
- `CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS = true`
- `OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS = true`

A missing field is a denial, not an implicit pass.

These booleans establish **method-level machine-only admissibility**. They do not prove that the exact destination agent/runtime currently has the concrete execution surfaces required by the method. A machine-only work package can still require a local checkout, shell, Python/Node/PHP runtime, browser, network, database, deployment access, or a specific connector that is absent from a particular destination.

Therefore every Research execution/verification assignment is also subject to `contracts/EXECUTABILITY_CONTRACT.md`: the Control Director must derive concrete required capabilities from the work package's `EXECUTION_SURFACE`, source access, computation, verification method, and mandatory validators, bind an exact destination `CAPABILITY_PROFILE`, and prove `REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES` before `ASSIGN`. Known missing runtime capability is `ASSIGNMENT_NOT_ADMISSIBLE`, not a valid plan to discover `BLOCKED` downstream.

An object that requires a prohibited human dependency is invalid at admission and MUST return `METHOD_NOT_MACHINE_EXECUTABLE` or `REJECTED_DEFAULT_RESEARCH_ARCHITECTURE`. It MUST NOT enter normal execution as `BLOCKED_PENDING_HUMANS`.

## Allowed pre-existing human-derived evidence

Allowed provenance may include published papers, books, dictionaries, public corpora, archived interviews, recorded speech corpora, externally conducted surveys or experiments, census/statistical datasets, existing annotations, public reviews/posts/forums where methodologically appropriate, and existing expert judgments.

The engine MUST distinguish:

- `EXTERNAL_PREEXISTING_HUMAN_DATA` — allowed as source provenance.
- `PROJECT_GENERATED_HUMAN_RESEARCH` — prohibited by default.

Legacy `HUMAN_TEST`-like classes may exist only as compatibility/history and MUST carry `PROJECT_GENERATION_PROHIBITED = true`.

## Owner authority terminology

Generic human authority terms are not valid Research Engine transition names. Use explicit Owner/K0 terms, including:

- `OWNER_AUTHORITY_GATE`
- `OWNER_SCOPE_GATE`
- `OWNER_ADJUDICATION`
- `OWNER_DECISION`
- `OWNER_RESEARCH_RELEASE_GATE`
- `OWNER_CANON_RECONCILIATION_GATE`
- `OWNER_ACCEPTANCE`

Owner judgment is a project decision, not sampled human evidence.

## Human-construct gap handling

When a construct cannot be measured directly without new human participation, ordinary research MUST choose one or more of:

`EXTERNAL_PREEXISTING_EVIDENCE`, `CORPUS_PROXY`, `COMPUTATIONAL_PROXY`, `MODEL_PROXY`, `MULTI_MODEL_PROXY`, `SIMULATION`, `STRUCTURAL_ANALYSIS`, `TYPOLOGICAL_ANALYSIS`, `SENSITIVITY_ANALYSIS`, `UNKNOWN`, `INSUFFICIENT_PUBLIC_EVIDENCE`, `UNMEASURED_HUMAN_CONSTRUCT`, `OWNER_JUDGMENT_REQUIRED`.

No proxy may be described as direct human measurement or as human responses.

## Precedence

For Research Engine execution, authority order is:

1. OWNER / K0 constitutional decision
2. this kernel constitution
3. universal destination executability contract
4. Research Engine manifest/contracts
5. project-specific research architecture
6. research work package
7. method / experiment freeze
8. executor prompt

A weaker downstream instruction that requests prohibited human participation is an invalid method instruction. Stop that method, not the research project; return a machine-executable remediation or an explicit evidence limitation.

## Separate opt-in human-research boundary

No ordinary Research Engine transition may create a human-research workstream.

A separate workstream is valid only if an explicit Owner/K0 authorization object states all of:

- `CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM = true`
- exact `PROJECT_ID`
- exact `QUESTION_ID`
- `REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE = true`
- bounded `SCOPE`
- separate `NAMESPACE` beginning with `human-research/`

Authorization is non-transitive, non-reusable, and does not modify the default Research Engine.

## Enforcement requirement

This constitution is enforceable, not advisory. Research question admission, work-package admission, experiment validation, static policy linting, and automated regression tests MUST reject active prohibited human dependencies before normal Research Engine execution. Destination executability remains a separate universal pre-assignment gate and must not be inferred from the machine-only admission booleans.
