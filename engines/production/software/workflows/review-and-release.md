# Software Workflow — Review and Release Support

**Entry:** exact software candidate/result that needs integration review, technical QA, or release preparation, plus destination executability proof for the mandatory review/release actions and evidence paths selected for this assignment.

Software-owned review skills may include `pre-merge-review`, `merge-preview-check`, `git-branch-integrity`, `operational-auditing`, browser QA, and deployment/data engineering support as applicable.

Before assignment, derive concrete capabilities from the selected mandatory review surface. Examples:

- local branch/worktree assertions require `repository_local_checkout` / `git_local_worktree` and any required shell/git execution surface;
- build/install/test minima require the matching checkout, package/runtime, and command execution capabilities;
- browser QA requires `interactive_browser` or a fully provisioned declared browser-automation mode such as `playwright_runtime` plus its own checkout/runtime/package/browser prerequisites;
- deployed/runtime/database assertions require the exact deployed/network/database access needed by the claim;
- remote PR/branch state may use a declared repository connector/API mode, but cannot prove local-only state.

Known missing mandatory capability before dispatch is `ASSIGNMENT_NOT_ADMISSIBLE`. Do not reinterpret a mandatory full review as `PASS` merely because only static/remote evidence is available. A supported partial review is valid only when the assignment explicitly scopes/accepts partial evidence.

**Review boundary:** A Director who did not implement the candidate can review the exact candidate and all applicable V1–V4 claims directly. Use an actual separate Verifier when specifically required or selected. Delegate implementation/repair to an admitted Executor; gather required evidence with an actor that can actually access it. Director/Control alone owns authorized merge/promotion. Executor and Verifier never merge.

Shared exact-state/evidence rules bind all claims to the actual candidate/environment. A production mutation is an explicit authority boundary, not an incidental worker feedback loop.

Before any PR merge-ready claim, run risk-tier classification from `skills/pre-merge-review`. For V2–V4 independently bind Issue/Owner/Canon target references and require the corresponding `transition_authority.review_gate` plus outcome/architecture/progress/transition claim proof. Do not treat a technical-only CONFIRMED as architectural PASS; an intentionally staged V3 dependency is not final end-to-end business completion. If the target is missing or contradicts current authority, return BLOCKED / Owner Gate, not a fabricated PASS.

For implementation that changes the truth of active governing operational documentation, affected documentation must be reconciled in the same candidate PR. Software pre-merge review reports the bounded documentation delta (updated paths, `NO_DOCUMENTATION_IMPACT`, or `BLOCKED`); an unresolved change-caused contradiction is not merge-ready. This does not impose documentation edits on unrelated microfixes or authorize a new Canon decision. Control Director consumes the documentation result as part of the original acceptance claims; Verification independently proves it when it is a required claim, without a separate documentation engine or Owner gate.

**Post-merge workstream continuation:** After an already-authorized PR promotion, Control independently reads the merged remote main, updates the existing Issue cursor with exact PR/merge refs, and continues the next separately admitted stage when the Owner's frozen final outcome remains open. Do not hand it back to Owner after every successful child PR or invent an additional acceptance gate. Reuse exact-state CI/Preview evidence appropriate to actual claims. Merge conflicts and mandatory gate failures remain bounded WAIT/repair/ESCALATE, never permission to skip steps.

When a separate Verifier is specifically required or selected, hand the exact assignment, Executor Result and candidate/evidence refs to `engines/verification/` and preflight that destination. Preserve the distinct Verifier result for Control Director. A Director's own review is recorded in its decision instead.
