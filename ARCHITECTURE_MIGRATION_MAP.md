# Architecture Migration Map — PR-MIG-01

Migration base: `main@49befc25b36ff7de1a582f95fe5a3a50a6a39fd6`

This map is the pre-move accounting record for the legacy Codex source corpus. `SEMANTIC_CHANGE_REQUIRED = no` means preserve content byte-for-byte where practical; path/reference reconciliation may still be required in active manifests/docs. Nothing below authorizes Wave B/C, Canon import, or new capability authoring.

Classification values are the frozen migration vocabulary from issue #25.

## Root and support files

| CURRENT_PATH | CURRENT_CLASS | CURRENT_OWNER | TARGET_CLASS | TARGET_PATH | SEMANTIC_CHANGE_REQUIRED | DEPENDENCIES | NOTES |
|---|---|---|---|---|---|---|---|
| `AGENTS.md` | root operating rules | Codex Software Playbook | SUPERSEDE | root `AGENTS.md` + `archive/legacy-codex/AGENTS.md` | yes for active root; no for archive | root control layer | Preserve legacy source; replace active function with short Project Resolver intake rules. |
| `README.md` | root overview/catalog | Codex Software Playbook | SUPERSEDE | root `README.md` + `archive/legacy-codex/README.md` | yes for active root; no for archive | system manifest/router | New README describes Project Resolver; legacy overview preserved. |
| `ARTIFACT_FLOW.md` | software artifact flow | Codex Software Playbook | SUPERSEDE | `archive/legacy-codex/ARTIFACT_FLOW.md` | no for archive | common artifact protocol | PLAN→IMPLEMENTATION→QA→REVIEW→MERGE may remain a Software workflow, not universal law. |
| `HOW_TO_APPLY.md` | software application guide | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/docs/HOW_TO_APPLY_LEGACY.md` | no | Software Engine | Keep as migrated legacy guidance; engine manifest/workflows become current routing surface. |
| `LOCALFLOW_FACTORY.md` | legacy product/factory architecture | Codex Software Playbook | ARCHIVE_AS_EVIDENCE | `archive/legacy-codex/LOCALFLOW_FACTORY.md` | no | none active | Useful historical lessons; Laravel/Filament/Cloudflare specifics are not current system architecture. |
| `PRODUCT_REPO_RULES.md` | software repository rules | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/docs/PRODUCT_REPO_RULES.md` | no | Software Engine | Software-only operational guidance. |
| `QUICKSTART.md` | software playbook quickstart | Codex Software Playbook | SUPERSEDE | `archive/legacy-codex/QUICKSTART.md` | no for archive | root router/engine manifests | Old global catalog is not an ordinary runtime entrypoint. |
| `SKILLS_INDEX.md` | global skill catalog | Codex Software Playbook | SUPERSEDE | `archive/legacy-codex/SKILLS_INDEX.md` + engine/library indexes | yes for active discovery; no for archive | progressive disclosure | Global full catalog retained only as migration evidence/maintenance reference. |
| `.codex/hooks.example.json` | provider-specific hook example | Codex runtime support | ARCHIVE_AS_EVIDENCE | `archive/legacy-codex/.codex/hooks.example.json` | no | none active | Hardcodes legacy session artifacts/provider surface; not root architecture. |
| `scripts/check_branch_integrity.py` | software git helper | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/tools/check_branch_integrity.py` | no | `git-branch-integrity` | Keep helper with Software Engine. |
| `scripts/validate_state.py` | legacy structural validator | Codex Software Playbook | SUPERSEDE | `archive/legacy-codex/scripts/validate_state.py` | no for archive | new structural validator | Old validator asserts obsolete root template topology. |
| `bundles/THREEJS_SITE_STARTER.md` | technology bundle | Codex Software Playbook | MOVE_TO_DOMAIN_PACK | `engines/production/software/domain-packs/threejs/THREEJS_SITE_STARTER.md` | no | Software Engine | Technology-specific optional bundle. |

## System-wide Core / protocol / verification / library skill owners

| CURRENT_PATH | CURRENT_CLASS | CURRENT_OWNER | TARGET_CLASS | TARGET_PATH | SEMANTIC_CHANGE_REQUIRED | DEPENDENCIES | NOTES |
|---|---|---|---|---|---|---|---|
| `.agents/skills/anti-loop-execution/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/anti-loop-execution/` | bounded terminology only if required | kernel/control | Finite execution and causal-audit law is system-wide. |
| `.agents/skills/authority-mapping/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/authority-mapping/` | bounded terminology only if required | common contracts | Authority/source/projection distinctions are system-wide. |
| `.agents/skills/dependency-ownership/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/dependency-ownership/` | bounded terminology only if required | kernel/workflow routing | Dependency ownership is system-wide. |
| `.agents/skills/exact-state-verification/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/exact-state-verification/` | bounded terminology only if required | Evidence contract | Exact identity/provenance is system-wide. |
| `.agents/skills/evidence-and-authority/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/evidence-and-authority/` | bounded terminology only if required | Evidence/Authority contracts | Evidence does not create authority. |
| `.agents/skills/irreversible-boundary-reasoning/` | Core principle | Codex Software Playbook | MOVE_TO_KERNEL | `kernel/skills/irreversible-boundary-reasoning/` | bounded terminology only if required | state mutation protocol | Irreversible boundaries are cross-engine reasoning. |
| `.agents/skills/session-handoff/` | continuity skill | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `protocols/skills/session-handoff/` | bounded terminology only if required | context/artifact protocols | Durable handoff is not Software-owned. |
| `.agents/skills/project-chronicle/` | continuity skill | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `protocols/skills/project-chronicle/` | bounded terminology only if required | durable state/artifact protocol | Long-lived decision/history record is cross-engine. |
| `.agents/skills/proof-loop-verification/` | verification skill | Codex Software Playbook | MOVE_TO_VERIFICATION_ENGINE | `engines/verification/skills/proof-loop-verification/` | bounded terminology only if required | shared evidence/exact-state skills | Verification Engine owns completion-claim proof workflow. |
| `.agents/skills/skill-authoring/` | library maintenance skill | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `library/skills/skill-authoring/` | path/ownership terminology only | library lifecycle | Maintenance capability, not Software production. #24 behavior verification remains deferred. |

## Software Engine procedural skills

All entries below remain accepted skills. Migration changes ownership/path, not their proven procedural substance.

| CURRENT_PATH | CURRENT_CLASS | CURRENT_OWNER | TARGET_CLASS | TARGET_PATH | SEMANTIC_CHANGE_REQUIRED | DEPENDENCIES | NOTES |
|---|---|---|---|---|---|---|---|
| `.agents/skills/implementation-planning/` | software workflow skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/implementation-planning/` | no except references | shared Core | Software planning remains engine-local in Wave 1. |
| `.agents/skills/systematic-debugging/` | software workflow skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/systematic-debugging/` | no except references | anti-loop | Software failure diagnosis. |
| `.agents/skills/git-branch-integrity/` | software workflow skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/git-branch-integrity/` | no except references | exact-state | Git-specific. |
| `.agents/skills/merge-preview-check/` | software workflow skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/merge-preview-check/` | no except references | git integrity | Git integration check. |
| `.agents/skills/pre-merge-review/` | software workflow skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/pre-merge-review/` | no except references | verification support | Software review. |
| `.agents/skills/design-system-authoring/` | software/design skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/design-system-authoring/` | no except references | web QA | UI/software design. |
| `.agents/skills/webapp-dogfood-qa/` | software QA skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/webapp-dogfood-qa/` | no except references | Playwright harness | Web application QA. |
| `.agents/skills/playwright-dogfood-harness/` | software QA skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/playwright-dogfood-harness/` | no except references | web QA | Software/browser tooling. |
| `.agents/skills/operational-auditing/` | software audit skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/operational-auditing/` | no except references | pre-merge review | Repository/deploy operational audit. |
| `.agents/skills/docs-assembly/` | software documentation skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/docs-assembly/` | no except references | implementation planning | Existing software docs workflow. |
| `.agents/skills/spike-prototyping/` | software experiment skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/spike-prototyping/` | no except references | implementation planning | Prototype/spike workflow remains software-owned here. |
| `.agents/skills/laravel-contract-first/` | technology/domain skill | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/laravel-contract-first/` | no except references | Software Engine | Framework-specific, never root architecture. |
| `.agents/skills/security-property-calibration/` | Core engineering principle | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/security-property-calibration/` | no except references | shared authority/evidence | Accepted Wave A engineering principle; retained as Software capability in this wave. |
| `.agents/skills/async-lifetime-ownership/` | Core engineering principle | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/skills/async-lifetime-ownership/` | no except references | irreversible boundary | Accepted Wave A engineering principle; retained as Software capability in this wave. |

## Optional Software Solution Patterns

Every entry below remains **optional**, assumption-bound, and non-authoritative at root.

| CURRENT_PATH | CURRENT_CLASS | CURRENT_OWNER | TARGET_CLASS | TARGET_PATH | SEMANTIC_CHANGE_REQUIRED | DEPENDENCIES | NOTES |
|---|---|---|---|---|---|---|---|
| `.agents/skills/versioned-signed-state-envelope/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/versioned-signed-state-envelope/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/immutable-deployment-data-pinning/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/immutable-deployment-data-pinning/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/single-writer-session-reconciliation/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/single-writer-session-reconciliation/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/stable-semantic-identifiers/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/stable-semantic-identifiers/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/legacy-schema-adoption/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/legacy-schema-adoption/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/transactional-semantic-state/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/transactional-semantic-state/` | no except references | Software Engine | Wave A pattern; optional. |
| `.agents/skills/server-authoritative-event-journal/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/server-authoritative-event-journal/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/post-commit-recovery-cursor/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/post-commit-recovery-cursor/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/immutable-retry-snapshot/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/immutable-retry-snapshot/` | no except references | Software Engine | Wave A pattern; optional. |
| `.agents/skills/capture-on-get-consume-on-post/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/capture-on-get-consume-on-post/` | no except references | Software Engine | Wave A pattern; optional. |
| `.agents/skills/plan-revalidate-apply-fence/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/plan-revalidate-apply-fence/` | no except references | Software Engine | Wave A pattern; optional. |
| `.agents/skills/publication-frontier/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/publication-frontier/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/read-only-observer-facade/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/read-only-observer-facade/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/provider-late-binding/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/provider-late-binding/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/presentation-completion-barrier/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/presentation-completion-barrier/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/accessibility-commit-announcement/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/accessibility-commit-announcement/` | no except references | Software Engine | Preserve optional classification. |
| `.agents/skills/architectural-dependency-fence/` | Optional Solution Pattern | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/patterns/architectural-dependency-fence/` | no except references | Software Engine | Wave A pattern; optional, never root mandate. |

## Templates

| CURRENT_PATH | CURRENT_CLASS | CURRENT_OWNER | TARGET_CLASS | TARGET_PATH | SEMANTIC_CHANGE_REQUIRED | DEPENDENCIES | NOTES |
|---|---|---|---|---|---|---|---|
| `templates/BRANCH_STATE.md` | software template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/BRANCH_STATE.md` | no | git integrity | Software/git artifact. |
| `templates/DESIGN.md` | software design template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/DESIGN.md` | no | design-system-authoring | Software design artifact. |
| `templates/DOGFOOD_GITHUB_ACTION.yml` | software CI template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/DOGFOOD_GITHUB_ACTION.yml` | no | Playwright harness | GitHub-specific optional template. |
| `templates/HANDOFF.md` | continuity template | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `protocols/templates/HANDOFF.md` | bounded terminology later if needed | handoff protocol | Cross-engine durable handoff. |
| `templates/MERGE_PREVIEW.md` | software template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/MERGE_PREVIEW.md` | no | merge-preview-check | Software/git artifact. |
| `templates/PLAN.md` | software template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/PLAN.md` | no | implementation-planning | Software workflow artifact, not universal assignment schema. |
| `templates/PLAYWRIGHT_DOGFOOD_SETUP.md` | software template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/PLAYWRIGHT_DOGFOOD_SETUP.md` | no | Playwright harness | Software/browser setup. |
| `templates/PROJECT_CHRONICLE.md` | continuity template | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `protocols/templates/PROJECT_CHRONICLE.md` | bounded terminology later if needed | project-chronicle | Cross-engine durable history. |
| `templates/PR_REVIEW.md` | software template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/PR_REVIEW.md` | no | pre-merge-review | Software review artifact. |
| `templates/QA_REPORT.md` | software QA template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/QA_REPORT.md` | no | QA skills | Software QA artifact. |
| `templates/REVIEW.md` | software review template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/REVIEW.md` | no | review workflows | Software review artifact. |
| `templates/RUNBOOK.md` | software operations template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/RUNBOOK.md` | no | docs/operations | Software operations artifact. |
| `templates/SKILL_TEMPLATE.md` | library maintenance template | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `library/templates/SKILL_TEMPLATE.md` | path/ownership references only if required | skill-authoring | System-wide library maintenance. |
| `templates/SPIKE_REPORT.md` | software experiment template | Codex Software Playbook | MOVE_TO_SOFTWARE_ENGINE | `engines/production/software/templates/SPIKE_REPORT.md` | no | spike-prototyping | Software experiment artifact. |
| `templates/TASK_EVIDENCE.md` | evidence template | Codex Software Playbook | MOVE_TO_COMMON_PROTOCOL | `protocols/templates/TASK_EVIDENCE.md` | bounded terminology later if needed | Evidence contract | Generic evidence carrier; artifact is not evidence by identity alone. |

## Open issue ownership remap — migration inputs only

No candidate below is implemented by this wave.

- **#21** → mainly Software data/release guidance; retain `E-ASSURANCE-COMPLEXITY`, explicit promotion boundary, and prohibition on universal DB mechanisms.
- **#22** → shared state-stability/provenance/revalidation invariant; exclusive lease remains an optional Software pattern only when assumptions require it.
- **#23** → `CTRL-01` Kernel/orchestration; `CTRL-02` Kernel/planning/orchestration; `CTRL-03` Software release + Verification; `CTRL-04` shared verification/anti-loop; `CTRL-05` shared authority/change protocol; `CTRL-06` K0/Owner Interface; `DATA-01` common state lifecycle plus optional Software/data realization.
- **#24** → `design-discovery` future Foundation/common workflow; `test-design-and-regression` Software + Verification; `delegated-workstream-execution` Kernel/orchestration; `parallel-agent-dispatch` Kernel/orchestration; `repository-orientation` Software Engine; Skill Behavior Verification → shared Skill Library lifecycle.

## Accounting summary

- pre-migration skill owners accounted for: **41 / 41**;
- accepted Optional Solution Patterns accounted for: **17 / 17**;
- root/support files accounted for: **12** (8 root docs + hook + 2 scripts + 1 bundle);
- templates accounted for: **15 / 15**;
- no accepted skill/pattern/template is classified for deletion;
- planned Canon/Research/Foundation engines are not migration sources in this wave.
