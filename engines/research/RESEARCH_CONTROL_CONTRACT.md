# Research Engine Control Contract

## Core separations

`Source != Evidence != Finding != Project Decision`.

Research may establish `SUPPORTED`, `CHALLENGED`, `UNKNOWN`, `CONTRADICTORY`, `INSUFFICIENT_EVIDENCE`, `PROXY_ONLY`, or `READY_FOR_OWNER_DECISION`. Only Owner/K0 can establish project acceptance where Owner authority is reserved.

## Default lifecycle

```text
OWNER / CANON INPUT
→ R0 RESEARCH FOUNDATION
→ R-WHAT
→ AUTOMATED VERIFICATION
→ OWNER_SCOPE_GATE (only when project scope authority is needed)
→ MACHINE RESEARCH WORK PACKAGES
→ SOURCE / EVIDENCE EXTRACTION
→ FINDINGS
→ AUTOMATED SYNTHESIS / ADVERSARIAL VALIDATION
→ OWNER_RESEARCH_SUFFICIENCY_ADJUDICATION (only when a project choice is genuinely needed)
→ OPTIONAL MACHINE GAP LOOP
→ RESEARCH FREEZE / VERIFIED RELEASE
→ STANDALONE COMPLETION (when this satisfies the admitted objective)
   OR AUTHORIZED CANON RECONCILIATION PACKAGE → CANON ENGINE
```

There is no ordinary transition to participant collection, surveys, interviews, focus groups, native-speaker recruitment, external reviewer approval, expert panels, or human validation.

## Question admission

Every candidate question is validated against `schemas/research-question.schema.json` and `tools/research_policy.py::validate_question` before activation. The schema is closed against undeclared fields, and every declared free-form semantic field is recursively inspected. Missing machine-executability fields or conflicting human-dependent semantics fail closed. A question that requires a non-owner human is `REJECTED_DEFAULT_RESEARCH_ARCHITECTURE`; the engine redesigns the method or records a limitation.

## Work-package admission

Every work package is validated against `schemas/research-work-package.schema.json` and `tools/research_policy.py::validate_work_package` before activation. The schema is closed against undeclared fields and all method/execution semantic values are recursively inspected. It declares an allowed AI `EXECUTOR_ROLE` and fixes `VERIFIER_ROLE=AI_R_VERIFIER`. `MACHINE_EXECUTABLE=true` and all human dependency flags must be explicit false. Owner gates, if any, must be explicit `OWNER_*` authority terms.

## Source discovery during admitted execution

The Research Executor discovers relevant pre-existing sources using admitted
machine-access methods during execution. No preliminary site matrix,
source-location gate, generic source-selection mode or fixed source whitelist
is required. The actual `SOURCE_ACCESS_METHOD` and destination capabilities
must be proven before execution, and each discovered source must pass the
existing `validate_source` provenance check before evidence admission.

An exact dataset or corpus required by a legitimate Assignment/method freeze
remains binding, without a second generic source-selection policy. A source
URI alone does not prove that the source was read or that a finding follows.

A verified Research Release can complete an admitted standalone objective.
Canon reconciliation is only routed when the authorized downstream outcome
actually requires it, without granting Canon mutation authority.

## Verifier contract

Normal Research Engine verification is automated. R-VERIFIER checks scope, provenance, source fit, reproducibility, evidence/finding separation, contradiction handling, overclaim boundaries, freeze integrity, and machine-only compliance. It never repairs and never recruits.

Verification output MUST include:

- `MACHINE_EXECUTABLE: PASS | FAIL`
- `THIRD_PARTY_HUMAN_DEPENDENCY: 0 | >0`
- `OWNER_MANUAL_RESEARCH_DEPENDENCY: 0 | >0`
- `EXTERNAL_HUMAN_REVIEW_DEPENDENCY: 0 | >0`
- `HUMAN_COLLECTION_PATH: 0 | >0`
- `AMBIGUOUS_HUMAN_GATE_TERMINOLOGY: 0 | >0`

Any prohibited value above zero is `STATUS = FAIL`.

## Repair contract

R-REPAIR repairs only a bounded verifier finding. Human-dependent methods are replaced, when feasible, by pre-existing datasets, public corpora, deterministic computation, model/ensemble annotation, structural analysis, published literature, official standards, or explicit proxies. If no valid machine method exists, record `UNKNOWN`, `INSUFFICIENT_PUBLIC_EVIDENCE`, or `UNMEASURED_HUMAN_CONSTRUCT`. Never introduce a new human dependency.

## Clause/action policy classification

Machine-only semantic classification operates at clause/action level and can return multiple findings for one input. A prohibition binds only to the human action it actually negates. A static-source cue identifies only the pre-existing evidence it describes. Neither an `EXPLICIT_PROHIBITION` nor a `STATIC_EXTERNAL_SOURCE` finding can erase a separate `ACTIVE_DEPENDENCY`; any active prohibited human action is fatal to default Research admission.

## Source provenance

Active provenance classes include `PRIMARY_EXTERNAL_DATA`, `PUBLIC_DATASET`, `CORPUS`, `SCHOLARLY_ANALYSIS`, `DICTIONARY_REFERENCE`, `OFFICIAL_REFERENCE`, `COMMUNITY_ARCHIVE`, `EXTERNAL_PREEXISTING_HUMAN_DATA`, `SOFTWARE_DATASET`, `PROXY`, and `OTHER`.

Every source must pass `tools/research_policy.py::validate_source` before admission. `LEGACY_HUMAN_TEST` is compatibility-only and requires `PROJECT_GENERATION_PROHIBITED=true`, `HUMAN_ORIGIN=true`, and legacy-preserved origin. `EXTERNAL_PREEXISTING_HUMAN_DATA` requires `PROJECT_GENERATION_PROHIBITED=true`, `HUMAN_ORIGIN=true`, and external-pre-existing origin. `OTHER` cannot hide project-generated human evidence: human-origin `OTHER` sources must be provably external/legacy and project-generation-prohibited, while ambiguous `UNKNOWN` origin fails closed.

## Machine experiments and freeze

Default experiments conform to `schemas/machine-experiment.schema.json` and must pass `tools/research_policy.py::validate_experiment`. Forbidden human-research keys are inspected recursively. Semantic classification applies recursively to value leaves only; schema/property names such as `PROHIBITED_OVERCLAIMS` have no semantic masking effect on unrelated values.

Method freeze conforms to `schemas/research-method-freeze.schema.json` and must pass `tools/research_policy.py::validate_method_freeze` before `METHOD_FROZEN=true` can become authoritative. The freeze is closed against undeclared fields, carries explicit machine-only declarations, recursively rejects human-research keys/semantics, and freezes question, input identity, method/tool versions, prompt/rules, sampling, seed policy, metrics, aggregation, thresholds, limitations, and planned sensitivity analysis before substantive result inspection.

## Gap rule and overclaim guard

Direct human constructs may remain unmeasured. Machine proxies must be labeled as proxies and must not be called human responses, direct listener measurement, direct preference measurement, native-speaker validation, or population validation.

## Separate human-research compatibility boundary

The default engine cannot create or enter a `human-research/` namespace. A separate authorization object is not authority by itself. `tools/research_policy.py::validate_human_research_authorization` must receive or resolve the exact durable `OWNER_DECISION_RECORD` referenced by `OWNER_DECISION_RECORD_REF` and revalidate that the record is a genuine `RECORDED` Owner Interface artifact with `OWNER_K0` authority that explicitly created the same authorization identity, project, question, exact bounded scope, and namespace. Both record and authorization must be non-transitive and must preserve default Research mode unchanged. Missing, fabricated, mismatched, or agent-constructed provenance fails closed. `validate_separate_human_work_package` additionally checks exact project/question/namespace equality. This is a separate workstream, not a Research Engine fallback and not a reusable authorization.

## Normal regression gate

`python tools/validate_structure.py` is the ordinary deterministic structural gate. It validates active Research enforcement-surface reachability, schema closure and schema/policy required-field consistency, active runtime/config/document semantic lint, and the bounded machine-only negative regression matrix. Test fixtures and policy implementation source are executed/structurally checked rather than naively treated as executable Research instructions. Archives remain historical and outside runtime semantic lint.
