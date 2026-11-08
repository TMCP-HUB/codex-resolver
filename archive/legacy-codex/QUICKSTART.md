# Quickstart

## 1. Use this repo as a pattern library

Do not paste everything into one permanent prompt.
Copy only the layers you actually need.

Start with:

1. `AGENTS.md`;
2. `SKILLS_INDEX.md`;
3. the smallest useful skill for the current decision/work phase.

## 2. Minimum recommended setup in a working project

- copy/adapt `AGENTS.md`;
- copy the core skills your project actually needs;
- copy specialist skills/templates only when they will be maintained;
- copy a Solution Pattern only when its assumptions match a real problem in the project;
- adapt `.codex/hooks.example.json` into local Codex hooks when useful.

## 3. Best first skills to adopt

For almost any agent-driven repository:

- `implementation-planning`;
- `anti-loop-execution`;
- `git-branch-integrity`;
- `proof-loop-verification`.

Add these when the project has the corresponding complexity:

- `authority-mapping` — several components can disagree about state;
- `dependency-ownership` — multiple workstreams/providers/consumers;
- `exact-state-verification` — CI/review/release evidence depends on precise revisions;
- `irreversible-boundary-reasoning` — retries may cross non-repeatable effects;
- `evidence-and-authority` — machine checks, semantic review, and release decisions must stay distinct;
- `security-property-calibration` — a security requirement is broad or the adversary/trust boundary/achievable guarantee is unclear;
- `async-lifetime-ownership` — correctness-relevant async effects may outlive the initiating request, process, or user-visible response.

For debugging-heavy projects:

- `systematic-debugging`;
- `pre-merge-review`.

For UI-heavy projects:

- `design-system-authoring`;
- `webapp-dogfood-qa`.

For experimental or architecture-heavy projects:

- `spike-prototyping`;
- `implementation-planning`;
- `authority-mapping` as needed.

## 4. Recommended workflow

### Before non-trivial implementation

1. `implementation-planning` — define owner/scope/non-goals/dependencies/gates/stop conditions.
2. `dependency-ownership` or `authority-mapping` only if those boundaries are genuinely complex.
3. Freeze the workstream.
4. `anti-loop-execution` governs execution from this point.

Load `security-property-calibration` before selecting security controls when the property/adversary/boundary is still vague.
Load `async-lifetime-ownership` when required side effects can outlive the initiating request/process.

### During ordinary execution

Stay in EXECUTION MODE and implement frozen scope.
Record non-blocking adjacent findings instead of fixing them automatically.

### When execution repeats the same failure class

1. Stop point-fixing.
2. Enter CAUSAL AUDIT MODE through `anti-loop-execution`.
3. Use `systematic-debugging` for the technical diagnosis.
4. Re-check exact state and authority assumptions if relevant.
5. Resume implementation only after cause/replan is established.

### Before merge

- `git-branch-integrity`;
- `exact-state-verification` when evidence/HEAD identity matters;
- `pre-merge-review`;
- `merge-preview-check`;
- `proof-loop-verification`.

## 5. Selecting Solution Patterns

Solution Patterns are concrete optional recipes. Do not copy them as policy.

Before using one, answer:

```text
Does my problem match the pattern's Problem class?
Do its Assumptions hold?
Am I inside Use when rather than Do not use when?
Are its Trade-offs acceptable?
Why is this better here than the listed Alternatives?
```

Examples of when to look:

- compact trusted client-carried state → `versioned-signed-state-envelope`;
- code and external data must stay version-compatible → `immutable-deployment-data-pinning`;
- stale tabs/clients can overwrite shared state → `single-writer-session-reconciliation`;
- references must survive translation/rendering/reordering → `stable-semantic-identifiers`;
- production DB predates native migration history → `legacy-schema-adoption`;
- several tentative mutations form one semantic unit → `transactional-semantic-state`;
- you need an ordered server-accepted event trace under retry/outage → `server-authoritative-event-journal`;
- authoritative action commits before later continuation can fail → `post-commit-recovery-cursor`;
- uncertain mutation retry must remain the same semantic operation → `immutable-retry-snapshot`;
- one-time token link can be fetched automatically before user intent → `capture-on-get-consume-on-post`;
- a consequential live mutation is planned from state that may change before apply → `plan-revalidate-apply-fence`;
- prefetched/delivered data must not appear yet → `publication-frontier`;
- diagnostics need read-only state without control capability → `read-only-observer-facade`;
- external provider can be isolated behind a deterministic seam → `provider-late-binding`;
- domain readiness can precede presentation completion → `presentation-completion-barrier`;
- visually streaming status text should announce only committed units → `accessibility-commit-announcement`;
- an important architectural `must not depend on` rule needs executable regression evidence → `architectural-dependency-fence`.

A matching title is not enough. If assumptions differ, choose another design.

## 6. Core principles are not architecture recipes

Do not translate a core rule into an arbitrary technology mandate.

Example:

```text
Core principle:
identify authority for a shared fact.

Not implied:
"the server must always own it."
```

Example:

```text
Core principle:
identify an irreversible boundary before retry design.

Not implied:
"every workflow must use an outbox."
```

Example:

```text
Core principle:
calibrate the security property against the actual adversary and trust boundary.

Not implied:
"every protected system must use one specific security technology."
```

Specific implementations belong to optional Solution Patterns, where assumptions, trade-offs, alternatives, and failure modes are explicit.

## 7. Best first templates to adopt

- `BRANCH_STATE.md`;
- `HANDOFF.md`;
- `TASK_EVIDENCE.md`.

For UI-heavy projects:

- `DESIGN.md`;
- `QA_REPORT.md`.

For architecture experiments:

- `SPIKE_REPORT.md`.

## 8. Important rule

This repository is not the source of truth for a product codebase.
Each product repository keeps its own current contracts, authoritative state, plans, and evidence.
The playbook supplies reusable reasoning and optional recipes; the product repo decides its architecture.
