---
name: pre-merge-review
description: Review a software candidate against its actual scope, risks and evidence before authorized promotion.
---

# Pre-Merge Review

## Purpose

Use this skill when a pre-merge or release review is selected or required for a product repository.

## Goal

Catch project-breaking risks relevant to the changed system and accepted behavior, including authority, security, contracts, state, configuration, dependencies, runtime and interaction where applicable.

## When to use

Use this skill when:

- a branch is ready for review
- a PR is about to merge
- a change touches API, forms, analytics, deployment, UI, or config
- the accepted change or its risks call for a review
- CI passed but product behavior may still be wrong

Select review based on the actual assignment, affected claims and risk, not file count. Honor existing project review and promotion requirements.

## Inputs

Collect:

- task goal
- changed files
- diff summary
- target branch
- verification commands and results
- preview or deployment URL if available
- known product-specific constraints


## Execution contract

- Review the exact candidate and relevant existing evidence through an authorized reader. Build, browser, runtime, deployed or provider access is required only for an actual claim or existing project gate that needs it.
- If mandatory evidence is unavailable, mark that claim `NOT_PROVEN`; source evidence cannot prove a live or rendered result. Apply the existing independent Verification boundaries below without assuming that technical observation requires a human.

## Director Control Review and separately assigned Verification
- A Director who did not implement the candidate may inspect the exact candidate, applicable authority and direct evidence and perform full V1–V4 review. Record its own claim-by-claim `DIRECTOR_REVIEW` in the Director decision, not as an Executor task or a fabricated `VERIFICATION_RESULT`.
- When a review requires implementing repairs, running unavailable tooling, or gathering additional technical QA evidence, Director delegates the work to an admissible Executor. A microfix never becomes Director implementation merely because it is small.
- When a specific requirement demands another assessor, a real separate Verifier provides its outcome-bound `VERIFICATION_RESULT` for the assigned claims. Director holds the merge/promotion decision after evidence is reconciled; Executor and Verifier do not merge.
- Role labels or a change of persona inside the same physical chat do not establish independence. Confirm current PR/HEAD and authority before promotion.

## Target-alignment review gate — Issue #10

Before reviewing a PR, classify **actual change impact**, not PR size or the author's label:

- **V1 local/technical:** microfix or bounded non-architectural change; check exact candidate, technical contract and touched regressions. Do not impose global architecture review.
- **V2 business/contract:** API, integration or business flow; independently check the governing Issue's intended business behavior and relevant contract.
- **V3 foundation/architecture:** V2 plus authoritative target architecture/Owner decisions, architectural invariants, dependency direction and verifiable progress toward the end business outcome.
- **V4 transition/migration:** V3 plus affected starting states, migration/cutover safety, legacy retirement/recovery, and any required Owner decision. Replacements distinguish preserve/migrate vs destructive cutover.

Escalate the tier if the actual diff changes dependencies, responsibility ownership, lifecycle, persisted data or an irreversible boundary. A one-line cutover may be V4.

For V2–V4, do **not** accept the PR description, self-authored tests or already-merged code as the source of business truth. Read the governing Issue and resolve its authority against current Canon/Owner decision/accepted product contract. For V3/V4, identify the exact authoritative target reference and its business outcome and protected invariants. An unapproved or contradictory target is **BLOCKED / OWNER GATE**, not technical PASS.

For V2–V4, bind `transition_authority.review_gate` to the governing outcome (V2+), architecture and progress (V3+), and migration/transition (V4) claims. Each appears in Director acceptance requirements and has a confirmed Director or specifically assigned Verifier verdict with current evidence for the exact candidate. For replacement/destructive cutover the responsible reviewer reads the existing Owner source and records why its scope authorizes the actual action. `delivery_scope=STAGED` proves a specific approved foundation/phase dependency, **not** final business-process completion. A false-green CI result cannot override a missing or failed claim.

Do not create a new verifier or control engine. Software review supplies domain-specific evaluation; Verification supplies bounded claim evidence; Control Director owns promotion and the governed target-alignment classification. Deterministic transition code can reject missing required claims, but does not infer Canon truth from prose.

## Risk checklist

| Risk area | Review question |
|---|---|
| Scope | Did the diff stay inside the requested task? |
| Secrets | Were API keys, tokens, emails, passwords, or private payloads exposed? |
| Env/config | Did relevant environment names, bindings, routes, or secrets change? |
| Dependencies | Did package manager, lockfile, or dependency set change unexpectedly? |
| API/integration | Are the affected contracts, error meanings, permissions and compatibility preserved? |
| Interaction | Are relevant states, accessibility and responsive behaviors preserved for the accepted UI claim? |
| Provider/deployment | Are the actually used provider configuration and release assumptions preserved? |
| Analytics | Are in-scope event contracts and capture paths preserved? |
| Assets | Were real assets replaced with placeholders or external hotlinks? |
| SEO | Did canonical, robots, sitemap, title, or service/location metadata regress? |
| Accessibility | Are labels, focus states, contrast, and tap targets still sane? |
| Workflow files | Were `AGENTS.md`, `.agents/skills/`, `templates/`, or scripts deleted or rewritten casually? |
| End-state closure | Are touched active docs accurate and any in-scope obsolete scaffolding, temporary scripts, adapters, or legacy paths actually retired when the approved outcome requires retirement? |

## Procedure

1. Read the task goal and acceptance criteria.
2. List changed files and classify the change: docs, UI, API, config, deployment, analytics, data, or mixed.
3. Inspect the diff for unrelated changes.
   - Compare touched governing documents and in-scope transitional mechanisms against the approved end state, not against the PR author's implementation narrative.
   - Require replacement/removal of newly stale governing statements. If the authorized outcome retires a temporary aid or legacy path, require actual in-scope removal in this PR rather than mere disabling or a new cleanup follow-up.
   - Record affected docs or `NO_DOCUMENTATION_IMPACT`, and any in-scope retirements or `NOT_APPLICABLE`. Do not audit unrelated debt, remove still-required recovery mechanisms, create parallel current documents, or infer new Owner/Canon authority from code.
4. Reuse the evidence and existing checks required by the accepted claim and authorized scope; commands are not automatic when source review suffices.
5. Apply the risk checklist to areas actually affected by the change and accepted claims.
6. Record blockers, warnings, and non-blocking suggestions separately.
7. Produce a final verdict.

## Claim-specific evidence by change type

| Change type | Evidence when relevant |
|---|---|
| Docs/playbook | diff review and relevant link/path sanity |
| UI | evidence appropriate to the accepted claim; bounded browser/visual observation for actual visual, responsive or interaction claims that source/CI cannot prove |
| API/contract | relevant service contract, response/error behavior and client mapping evidence; runtime or actual request evidence only for claims requiring it |
| Backend/runtime | appropriate source or focused runtime evidence for the accepted claim |
| Provider/deployment | relevant configuration/source evidence; actual provider or deployed evidence only for a claim requiring it |
| Analytics/integration | affected event/payload contract and capture/compatibility evidence |
| Dependency/config | relevant dependency/configuration evidence and rationale; install/build only when required by the claim or active project gate |

Select existing QA methods by the accepted claim: HTTP/API contract, backend/runtime, web/browser, or mixed. Use `api-error-contract-handling` for in-scope API error-to-client semantics and web QA only for actual web claims. If genuinely necessary evidence is ambiguous, request bounded clarification from the existing Control Director, not another Owner decision. A change alone does not require a build, Preview, provider call, screenshots, manual human inspection, another Playwright QA pass, broad suites, new tests, or a separate QA report. Reuse current exact-candidate CI and relevant existing checks. For an accepted rendered geometry, responsive, conversion, or browser-specific auth or interaction claim that source/CI cannot prove, require the smallest appropriate browser/visual check of the affected route, viewport, and state. Screenshots are needed only if they are the chosen necessary evidence for an explicit visual claim or diagnosis; an available capable agent can perform independent technical observation when independence is required. If mandatory evidence is unavailable, record NOT_PROVEN and the limitation; nonvisual evidence cannot establish a visual claim. Existing baseline gates, V1–V4 classification, and independent promotion boundaries remain in force.

## Blockers

Treat a finding as blocking when it violates the actual accepted scope, security boundary, applicable contract or existing required gate. Examples when relevant:

- exposed secrets or protected data;
- removing an active required workflow, contract or protection without an authorized replacement;
- a relevant required build/check failing, or evidence required for acceptance unavailable or contradictory;
- incompatible integration, configuration, permissions or data changes without the required compatibility/recovery plan;
- a required user interaction, asset or event path broken for the affected product;
- an unjustified dependency or unrelated refactor outside the approved scope.

## Warnings

Warnings should be called out but may not block:

- minor visual inconsistency outside touched scope
- optional evidence unavailable in the current environment, with the affected claim marked `NOT_PROVEN`
- an optional lint script unavailable
- pre-existing failures not caused by the branch

## Anti-patterns

Avoid:

- saying green CI means safe to merge
- reviewing only code style while ignoring product contracts
- hiding warnings in a positive summary
- merging after only local verification when target branch moved
- accepting unrelated cleanup because it looks harmless

## Output format

```md
## Pre-merge review

- Status: pass / partial / fail
- Change type:
- Files reviewed:
- Verification:
- Blockers:
- Warnings:
- Documentation delta: updated paths / NO_DOCUMENTATION_IMPACT / BLOCKED (reason)
- In-scope retirement: removed paths / NOT_APPLICABLE / BLOCKED (reason)
- Product-specific risks:
- Recommended next action:
```

## Pair with

- `merge-preview-check` for integration drift
- `proof-loop-verification` for final evidence
- `systematic-debugging` if a blocker is a real bug
