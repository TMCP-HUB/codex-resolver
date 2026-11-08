---
name: reconcile-research-chain
description: Reconcile exact durable Research outputs into requirement-specific dependency state, explicit gap classes, evidence ceilings, supersession, and a bounded candidate research frontier without executing Research, dispatching workers, or mutating Canon.
---

# Inputs

- exact durable upstream Research artifact refs for one bounded chain or dependency frontier;
- the downstream requirement refs those Research requests were intended to support;
- exact current outcome/requirement identity when supersession depends on it;
- no caller prose may substitute for a missing or identity-inconsistent upstream artifact.

Use existing Research artifacts as evidence/findings. Do not invent a second Research result ontology.

# Procedure

1. Resolve every selected upstream Research ref and verify exact `artifact_id` identity plus non-empty provenance. Missing or contradictory identity fails closed.
2. Establish only the bounded downstream requirement set relevant to this reconciliation.
3. Preserve raw Research result/status separately from reconciliation control state.
4. Determine supersession before evaluating the active frontier. Preserve superseded history, but set it inactive.
5. Evaluate evidence sufficiency independently for each downstream requirement.
6. Classify each material remaining gap as exactly one of:
   `CONSEQUENTIAL_BLOCKER`, `ACCEPTABLE_UNKNOWN`, `EVIDENCE_CEILING`,
   `SUPERSEDED_REQUIREMENT`, `OWNER_PREFERENCE_OR_AUTHORITY`,
   `METHOD_OR_ARTIFACT_DEFECT`, `OUTSIDE_CURRENT_SCOPE`,
   `BOUNDED_NEW_RESEARCH_CANDIDATE`.
7. When bounded methods/sources cannot materially improve a governed claim within current scope, record `EVIDENCE_CEILING` and choose only:
   `ACCEPT_BOUNDED_UNCERTAINTY`, `DEFER`, `OWNER_GATE`,
   `REDESIGN_DOWNSTREAM_REQUIREMENT`, or `STOP_RESEARCH_LANE`.
8. Assign each downstream requirement one state:
   `SATISFIED`, `BLOCKED`, `ACCEPTABLE_UNKNOWN`, `EVIDENCE_CEILING`,
   `OWNER_DECISION_REQUIRED`, `SUPERSEDED`, `DEFERRED`, or `OUT_OF_SCOPE`.
9. Emit a next Research frontier candidate only for an active consequential external-fact gap where useful bounded methods remain, no evidence ceiling applies, the question is not Owner preference/authority, and the candidate is narrower than the unresolved prior question. Mark it `CANDIDATE_ONLY`.
10. Emit one common-envelope `RESEARCH_CHAIN_RECONCILIATION` artifact preserving every exact upstream Research ref and requirement-specific rationale.

# Invariants

- `RAW_RESEARCH_RESULT_STATUS != RECONCILIATION_CONTROL_STATE`.
- `GAP != REPEAT_RESEARCH`.
- `RESEARCH_RECONCILER != RESEARCH_EXECUTOR != CANON_AUTHORITY != CONTROL_DIRECTOR`.
- A complete result for one requirement never makes another requirement complete.
- `EVIDENCE_CEILING` never creates a retry candidate.
- `OWNER_PREFERENCE_OR_AUTHORITY` goes to Owner Interface / Control as an Owner authority gate, not to Research continuation.
- `METHOD_OR_ARTIFACT_DEFECT` is a defect classification, not evidence that more substantive Research is needed.
- Superseded blockers/requests stay historical and leave the active frontier.
- This skill never calls `tools.research_policy.admit_work_package()` because it does not execute Research. Any later admitted frontier candidate still uses the normal Research execution admission path.
- This skill never calls spawn/dispatch, never executes a candidate frontier, never creates `OWNER_DECISION_RECORD`, never calls a Canon mutation gate, and never emits accepted Canon state.

# Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution mode:** read-only interpretation of exact already-durable Research artifacts plus durable emission of the reconciliation artifact.

**Mandatory evidence path:** one schema-conforming `RESEARCH_CHAIN_RECONCILIATION` with exact upstream refs, per-requirement states, explicit gaps/ceilings/supersessions, and candidate-only frontier entries.

If an exact upstream Research ref cannot be resolved or has contradictory identity, fail closed and do not emit a success reconciliation. When the Assignment requires durable-output readback, use the existing system-of-record readback and applicable Control/Verifier checks. If the accepted task requires downstream consumption, verify that specific use through an available capable consumer; a fresh agent or live-provider exercise is required only when needed to prove the actual claim.
