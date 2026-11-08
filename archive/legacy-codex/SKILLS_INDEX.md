# Skills Index

Use this index before loading full skill files.
The goal is progressive disclosure: choose the smallest useful skill instead of reading the whole playbook.

## Core engineering principles

These skills govern **how software work is reasoned about and executed**. They are architecture-neutral and apply across frontend, backend, data, infrastructure, CLI, mobile, ML, and other software projects.

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `anti-loop-execution` | Non-trivial execution, repeated failures, scope drift risk | Frozen-mode record, stop/resume decision, deferred findings | `implementation-planning`, `systematic-debugging` |
| `authority-mapping` | Multiple components observe/write the same conceptual state | Decision/source-of-truth ownership map | `dependency-ownership` |
| `dependency-ownership` | Multiple workstreams/providers/consumers must coordinate | Typed dependency DAG and closure rules | `implementation-planning` |
| `exact-state-verification` | Evidence depends on a specific artifact/revision | Claim-to-exact-state evidence binding | `git-branch-integrity`, `proof-loop-verification` |
| `irreversible-boundary-reasoning` | Retry/recovery crosses non-repeatable effects | Commit-boundary and pre/post recovery model | `authority-mapping`, `systematic-debugging` |
| `evidence-and-authority` | Tests/review/approval are being used to justify a claim | Claim/evidence/authority matrix | `proof-loop-verification` |
| `security-property-calibration` | Security requirement is vague or controls may protect the wrong property | Explicit asset/adversary/boundary/guarantee/non-goal/residual-risk statement | `authority-mapping`, `evidence-and-authority` |
| `async-lifetime-ownership` | Async side effects may outlive request/response/process lifetime | Side-effect lifetime/ack/loss/retry ownership map | `irreversible-boundary-reasoning`, `authority-mapping` |

## Core execution and continuity skills

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `implementation-planning` | Multi-step feature, refactor, migration, or delegated work | Frozen implementation workstream | `anti-loop-execution`, `dependency-ownership` |
| `systematic-debugging` | Build, runtime, API, UI, deploy, data, or integration bugs | Root cause and minimal correction path | `anti-loop-execution` |
| `git-branch-integrity` | Starting/finishing branch work or tracking HEAD provenance | Branch/HEAD provenance and divergence notes | `exact-state-verification` |
| `proof-loop-verification` | Claiming a task/workstream is complete | Acceptance evidence and PASS/PARTIAL/BLOCKED/FAIL verdict | `evidence-and-authority` |
| `merge-preview-check` | Before merge or ready-for-review claim | Integration drift risk verdict | `git-branch-integrity` |
| `pre-merge-review` | Before PR, merge, or deployment | Risk-focused review verdict | `proof-loop-verification` |
| `session-handoff` | Ending a work session | Tactical continuation notes | `project-chronicle` |
| `project-chronicle` | Recording durable long-term decisions | Project history entry | `session-handoff` |

## Solution Patterns — optional technical recipes

These are **not global architecture rules**. Load a pattern only after its `Assumptions`, `Use when`, and `Do not use when` match the problem. Every pattern lists alternatives and trade-offs.

### State, provenance, and concurrency

| Pattern | Problem class | Typical result | Related Core |
|---|---|---|---|
| `versioned-signed-state-envelope` | Compact trusted state must travel through an untrusted client | Versioned signed envelope with normalization, field ownership, and size budget | `authority-mapping`, `exact-state-verification` |
| `immutable-deployment-data-pinning` | Executable and external data/config can evolve incompatibly | Deployment pinned to immutable data/release and optional interpretation fingerprint | `exact-state-verification`, `dependency-ownership` |
| `single-writer-session-reconciliation` | Stale clients/tabs can overwrite newer shared state | Expected-revision mutation and authoritative reconciliation | `authority-mapping`, `irreversible-boundary-reasoning` |
| `stable-semantic-identifiers` | Logical references must survive rendering/reordering/translation/storage changes | Durable semantic IDs independent of physical position | `authority-mapping`, `dependency-ownership` |
| `legacy-schema-adoption` | Existing production DB predates trustworthy migration history | Proven legacy baseline adopted into native migrations as a finite bridge | `exact-state-verification`, `evidence-and-authority` |
| `transactional-semantic-state` | Several internal mutations form one semantic unit and partial state must not become authoritative | Draft/isolation state published only at the real semantic boundary | `authority-mapping`, `irreversible-boundary-reasoning` |

### Events, retry, and recovery

| Pattern | Problem class | Typical result | Related Core |
|---|---|---|---|
| `server-authoritative-event-journal` | Ordered accepted-event trace must survive retry/outage without breaking the product | Monotonic server events, bounded pending journal, idempotent immutable batches, explicit gaps | `authority-mapping`, `irreversible-boundary-reasoning` |
| `post-commit-recovery-cursor` | Authoritative work commits before later continuation/presentation fails | Minimal continuation cursor that resumes post-commit work without replaying the commit | `irreversible-boundary-reasoning`, `exact-state-verification` |
| `immutable-retry-snapshot` | Mutation outcome is uncertain and retry must remain the same semantic operation | Stable operation identity + immutable semantic payload across uncertain retry | `irreversible-boundary-reasoning`, `async-lifetime-ownership` |
| `capture-on-get-consume-on-post` | Automated GET/prefetch can consume one-time link intent | Safe token capture + clean redirect + explicit protected consume mutation | `security-property-calibration`, `irreversible-boundary-reasoning` |
| `plan-revalidate-apply-fence` | Consequential mutation depends on current authoritative state and a plan may go stale | Observe/plan → revalidate → explicit apply → authoritative postcondition | `irreversible-boundary-reasoning`, `exact-state-verification` |

### Delivery, observation, providers, and presentation

| Pattern | Problem class | Typical result | Related Core |
|---|---|---|---|
| `publication-frontier` | Data may be delivered before it is allowed to become observable/published | Explicit publication lease/frontier and future-surface audit | `authority-mapping`, `irreversible-boundary-reasoning` |
| `read-only-observer-facade` | Diagnostics need state visibility without mutation/control authority | Detached allowlisted observer snapshots | `authority-mapping`, `evidence-and-authority` |
| `provider-late-binding` | External provider complexity can be isolated behind an application contract | Provider-neutral seam + deterministic fake + later live-provider certification | `dependency-ownership`, `evidence-and-authority` |
| `presentation-completion-barrier` | Domain readiness can precede user-visible/application presentation completion | Explicit presentation lease/barrier before dependent commands drain | `authority-mapping`, `irreversible-boundary-reasoning` |
| `accessibility-commit-announcement` | Visually streaming text should not be announced mutation-by-mutation | Separate semantic commit signal and single live-region announcement | `authority-mapping`, `evidence-and-authority` |

### Architecture enforcement

| Pattern | Problem class | Typical result | Related Core |
|---|---|---|---|
| `architectural-dependency-fence` | A high-value architectural prohibition must not remain prose-only | Narrow executable negative guard over a declared dependency/capability universe | `authority-mapping`, `dependency-ownership`, `evidence-and-authority` |

## Design, QA, audit, and documentation

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `design-system-authoring` | UI work or DESIGN.md creation | Design contract and visual QA note | `webapp-dogfood-qa` |
| `webapp-dogfood-qa` | Checking a web app, landing page, admin, menu, or calculator | QA report with evidence and severity | `design-system-authoring` |
| `playwright-dogfood-harness` | Repository needs reproducible browser QA | Screenshots, traces, reports, browser evidence | `webapp-dogfood-qa` |
| `operational-auditing` | Auditing repo, deploy, workflows, or AI-generated systems | Operational risk audit | `pre-merge-review` |
| `docs-assembly` | Generating/updating operational docs | Structured documentation set | `implementation-planning` |

## Planning, experimentation, and authoring

| Skill | Use when | Main output | Pair with |
|---|---|---|---|
| `spike-prototyping` | Testing an uncertain architecture/UX idea before production work | Spike report with validated/partial/invalidated verdict | `implementation-planning` when promoted |
| `skill-authoring` | Creating/editing reusable playbook skills | Well-structured SKILL.md | `proof-loop-verification` |
| `laravel-contract-first` | Laravel work where request/domain/persistence contracts should be fixed before implementation | Contract-first Laravel implementation plan/artifacts | Core principles as needed |

## Selection rules

1. For a non-trivial new workstream, use `implementation-planning`; once scope is frozen, `anti-loop-execution` governs execution.
2. For a bug, use `systematic-debugging`; repeated same-class failed corrections hand control back to `anti-loop-execution` for Causal Audit.
3. When several components can disagree about state, use `authority-mapping` before inventing another coordinator, cache rule, or writer.
4. When several issues/workstreams depend on one another, use `dependency-ownership` and type the edges instead of creating mutual blockers.
5. When a security request is phrased broadly, use `security-property-calibration` before choosing controls or claiming a guarantee.
6. When async work can outlive the initiating request/process, use `async-lifetime-ownership` to classify required vs degradable work and name the real lifetime/acknowledgement owner.
7. When a retry may cross a payment/send/delete/commit/cutover or other non-repeatable effect, use `irreversible-boundary-reasoning` before choosing retry mechanics.
8. Before quoting tests/review as proof, use `exact-state-verification` and `evidence-and-authority` at the level warranted by the risk.
9. **Do not select a Solution Pattern by name alone.** Open it, check `Assumptions`, `Use when`, `Do not use when`, `Trade-offs`, and `Alternatives`; reject it when the problem differs.
10. A Core Principle may guide selection of a pattern, but no Solution Pattern becomes mandatory merely because it worked in a prior project.
11. For UI tasks, load `design-system-authoring` first, then `webapp-dogfood-qa` before sign-off.
12. For uncertain architecture or UX ideas, run a spike before production implementation.
13. Before merge, use `pre-merge-review`, `merge-preview-check`, then `proof-loop-verification`.
14. When browser access is limited, use `playwright-dogfood-harness` instead of relying on environment-specific screenshot capability.
15. For inherited or AI-heavy repositories, run `operational-auditing` before major refactors.
16. When adding a new reusable workflow, use `skill-authoring` and check this index for overlap first.

## Core principle vs solution pattern

A **core engineering principle** constrains reasoning/execution broadly and should remain technology-neutral.

A **solution pattern** is an optional, proven way to solve a narrower technical problem. A pattern must state assumptions, trade-offs, alternatives, and when **not** to use it. Never promote a successful implementation pattern into a universal rule merely because it worked in one project.

## Do not load everything

Load only the skills needed for the current phase of work.
A complex task may use several skills over time, but avoid loading one skill per technology simultaneously. Prefer the smallest owner for the current decision:

- planning / ownership;
- execution or causal audit;
- implementation/debugging;
- optional solution pattern only if assumptions match;
- review/QA;
- proof/merge;
- handoff.
