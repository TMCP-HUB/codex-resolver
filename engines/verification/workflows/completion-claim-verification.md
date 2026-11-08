# Verification Workflow — Completion Claim

**Entry:** exact assignment, exact `EXECUTOR_RESULT`, explicit claims/acceptance targets, and destination executability proof covering every mandatory verification/evidence action required from the selected verifier instance.

**Reviewer:** A Director who did not implement the candidate can review V1–V4 claims directly and record `DIRECTOR_REVIEW` in its decision. When a specific requirement needs a further assessor, use a Verifier instance distinct from the Executor and Director; an Executor's in-chat role switch is not independence. A separate Verifier may be reused for unrelated candidates but not to certify its own implementation. Instance independence is established from actual runtime/handoff evidence, not role strings. The following steps describe the separately selected Verifier path.

1. Load exact assignment, exact `EXECUTOR_RESULT`, Control Verifier role, and the verifier destination capability/admissibility refs.
2. Extract asserted claims and required acceptance criteria **before assignment** when deriving verifier requirements; map each mandatory claim to its exact evidence path and concrete execution capabilities.
3. Require `REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES` for the verifier destination under `contracts/EXECUTABILITY_CONTRACT.md`. If a mandatory evidence path is known unavailable, return `ASSIGNMENT_NOT_ADMISSIBLE`; do not intentionally launch verification to obtain a predictable `BLOCKED`.
4. Bind candidate/evidence identity using shared exact-state rules. Distinguish remote repository state, local worktree state, runtime/deployed state, browser state, database state, and other trust boundaries.
5. Use `skills/proof-loop-verification` plus shared evidence/authority rules. For V2–V4 PR review require governed `transition_authority.review_gate`, inspect its independent Issue/target authority references, and verify each mandatory outcome/architecture/progress/transition claim with exact evidence; do not accept the PR itself as target authority.
6. Inspect direct state/evidence where required; do not accept Executor narrative as proof and do not silently substitute weaker evidence because the destination lacks the stronger surface.
7. If a capability that was proven at assignment time disappears, mark affected claims `NOT_PROVEN`/blocked with `BLOCKED_RUNTIME_DRIFT` evidence.
8. Emit `VERIFICATION_RESULT` with `CONFIRMED`, `QUALIFIED`, or `NOT_PROVEN` per claim and separate additional findings.
9. Hand the result to Control Director **alongside the unchanged Executor Result**.

No repair or scope expansion occurs inside this workflow. Verification blockage remains a truthful runtime outcome only for unavailable/stale evidence that was not already known to make the assignment inadmissible before dispatch.
