---
name: cloudflare-workers-delivery
description: Configure or review Git-owned Cloudflare Workers build, deploy, Preview, route and binding delivery using existing project scripts and provider settings.
---

# Cloudflare Workers Delivery

## Purpose and selection

Use for an authorized change or review of Workers Builds, Git linkage, Wrangler Worker/asset/route/binding configuration, build/deploy/Preview commands, or related deployment drift. Do not load solely because a repository uses Cloudflare. This is a Software delivery skill under existing implementation and review workflows; it grants no deployment, provider mutation or infrastructure authority.

## Inputs and execution contract

Inputs: exact project repository/ref, selected Worker(s), approved deployment and Preview policy, relevant current documentation, and the claims requested by the assignment. Inspect actual Wrangler config, named configs/environments, scripts and lockfile; determine the current Preview model. Mandatory capabilities below apply only to selected actions and evidence. The existing compiler/admission contract derives the exact destination's required set; this skill grants no authority.

- **Remote source review:** requires `repository_remote_read` for exact repository/ref and access to the relevant configuration, scripts, lockfile and active docs. Evidence: identified commit and source paths/content. This establishes source state only.
- **Local-worktree review or validation, when selected:** requires `repository_local_checkout`, `git_local_worktree` and `shell`, plus the project's actual runtime/package-manager capabilities (for example `node_runtime`) and dependencies. Require `package_install` and `outbound_network` only if dependency installation is needed and authorized. Evidence: exact local revision/worktree state and command output; separately publish/read the remote candidate if required.
- **Source implementation and publication:** requires `repository_remote_read` and `repository_remote_write` for the authorized target branch/PR, plus a permitted edit/publish method and remote readback of exact HEAD and diff. A local edit path additionally requires the local-worktree capabilities above; a repository API may perform the same source edits without a local checkout. Required build or validation adds the relevant runtime capabilities or an admitted CI execution/evidence path as appropriate.
- **Provider observation:** when dashboard/build/deployed configuration evidence is mandatory, requires authorized provider read access scoped to the exact account, Worker and settings or deployment, through a capable connector/API or an authorized interactive surface (including `interactive_browser` when that is the selected method). Evidence: provider readback identifying Worker, branch/build or deployment and relevant non-secret effective settings/bindings. Source configuration alone cannot establish those facts.
- **Provider mutation or deployment:** only when separately authorized and in scope, requires the relevant scoped provider write or `deployment_access` for the actual target, and provider read access for exact non-secret result readback. A CLI path additionally needs `shell`, the required runtime/Wrangler and network access; a dashboard path needs the admitted interactive surface. Evidence: provider operation result and subsequent exact Worker/configuration or deployment readback, with source/build identity when applicable. A repository write or provider read does not imply write/deploy capability.
- **Build/Preview/runtime evidence, when required by the claim:** existing exact-state CI/build evidence may be reused with `ci_read` or the relevant provider build-log read capability. Triggering a new run requires `ci_trigger` or the actual provider trigger capability; local build requires the selected local runtime and dependencies. An authorized live HTTP or browser check requires access to the exact deployed endpoint, network or interactive browser as applicable, and a safe permitted operation. Bind evidence to source/build, deployment or Preview identifier, and relevant effective configuration. No test, new build, live request or provider mutation is mandatory merely because the skill is selected.

**Equivalent paths and limits:** Direct repository connector/API and authorized native Git are equivalent only for the same remote ref, operation and evidence; remote source is not evidence of unpushed local state. Provider API/connector and an explicitly authorized visible dashboard may substitute only when they expose the same exact effective state and preserve the selected physical route. Local build and CI are equivalent only if their actual inputs, environment and required claim are proven equivalent. Static review, a successful build or a Preview URL cannot replace a required live/deployed observation; a runtime response cannot alone prove effective bindings or production activation. Do not weaken a mandatory claim silently.

**Unsupported environments:** Before assignment, when required action or evidence capabilities are missing or unproven, use the existing `ASSIGNMENT_NOT_ADMISSIBLE` path or an already-authorized equivalent mode; preserve exact missing capabilities and evidence paths. After valid admission, loss of a required capability is `BLOCKED_RUNTIME_DRIFT`; retain the candidate and report the affected action. Optional unavailable observations are unknown/not proven and do not create a new gate. Never claim an unobserved provider state or substitute a weaker mode without explicit acceptance.

## Configuration ownership and commands

1. Keep supported Worker identity, entry point, assets, routes, bindings and environment-specific references in the project's versioned Wrangler configuration (`wrangler.jsonc`, TOML or its existing named config). When a selected claim or action requires effective deployed settings or dashboard-managed values, reuse valid exact-state evidence or observe them only when needed, authorized and supported by proven provider-read capability; repository config alone is not proof of the live state. Never commit secret values.
2. Put the real build, deploy and Preview commands, including necessary `--config` arguments and project build pipeline, in versioned `package.json` scripts or the established equivalent. For a new compatible project, `build`, `deploy`, `deploy:preview` are a useful convention; preserve existing package managers, script names, multi-Worker layout and approved routes when present. Do not create redundant scripts.
3. Workers Builds retains the Git connection, production branch, branch/build controls, working/root directory, build token/credentials, build variables and platform-side settings. When these Builds settings are in scope, use short commands such as `npm run build`, `npm run deploy`, and `npm run deploy:preview` where they match the project's scripts. Do not claim Wrangler config controls all dashboard settings. Build variables/secrets are available to the build; runtime variables and secrets are configured separately. Do not expose secret values or tokens in docs, logs or results.
4. Inspect the command chain relevant to the selected scope. When build evidence is required, reuse valid exact-state build or CI evidence when it satisfies the claim. Run a build at the appropriate layer only when required by the selected scope, authorized and supported by proven capability. Workers Builds runs its optional build step, then deploy or Preview; Cloudflare says Workers Builds does not honor Wrangler Custom Builds configuration. Other Wrangler invocations can run their own custom build, so inspect script and invocation behavior to avoid accidental duplication rather than assuming the contexts are identical.
5. Follow the project's actual Wrangler/package version and framework requirements. For current Worker Previews, Cloudflare requires the project Wrangler dependency `>=4.135.0`, a source-owned `previews` block, and `wrangler preview` (with appropriate existing config/arguments). A Preview build uses its Preview command instead of the production deploy command. `wrangler versions upload` produces a version/Version URL, not the same Preview model; `wrangler deploy --env ...` is an environment Worker deployment, not a substitute for Worker Previews. An older model remains valid if it is the approved current setup; any cutover is separately scoped and safe, never a blanket migration.

## Preview boundaries and effective state

- Inspect source configuration and available evidence for production and Preview branch selection, commands, bindings, route/trigger behavior and resource identities as relevant to the selected claims. When a selected claim or action requires effective live Preview or resource state, reuse valid exact-state evidence or observe it only when needed, authorized and supported by proven provider-read capability. A Preview URL is not proof that its runtime bindings are complete, isolated or safe to exercise.
- For D1, KV, R2 and other account-level resources, the same ID/name can mean shared data between Previews or production; use appropriate non-production bindings or an expressly approved reason for sharing. Evaluate access and side effects before any live request, including external APIs, emails, queues, webhooks or writes.
- Cloudflare documents automatic per-Preview Durable Object namespaces/storage for supported Worker Previews, but verify the mode and `env` binding declaration relevant to the scoped claim, distinguishing source configuration from effective live state; do not extend that guarantee to other bindings or existing environments. Current Preview service bindings can target the bound Worker's production deployment: inspect the complete downstream effects and require an approved safe arrangement before exercising it. Queues, workflows and other integrations may also target shared live resources.
- Wrangler named environments are distinct from the `previews` block. Bindings, variables and secrets for named environments are non-inheritable and need environment-specific configuration; assess configured behavior from the selected configuration, without claiming effective live behavior from source alone. Assets and other top-level-only Preview settings must stay where current Cloudflare documentation specifies. Preserve approved project decisions; do not automatically enable/disable Preview, create staging resources, change domains, or provision/migrate anything.

## Project documentation and evidence

When an authorized config change makes an existing active deployment document stale, update it in the same PR using `docs-assembly`: replace superseded claims, link to actual versioned config/scripts as the source, and explain the supported commands, production branch, Preview policy, resource isolation or approved sharing, exceptional dashboard settings, rationale and recovery where relevant. Use an existing `DEPLOYMENT.md`, `RUNBOOK.md` or equivalent; no new document or documentation rebuild for an unaffected microfix.

Use `operational-auditing` for broader operational findings, `pre-merge-review` for applicable delivery review, and `kernel/skills/exact-state-verification/SKILL.md` for binding claims to actual state; do not duplicate their general procedures. Reuse valid existing checks.

Report separately, as applicable: exact source candidate/HEAD and config paths; static review or build result; Workers Builds run and source commit; effective Worker/branch, Preview or deployment identifier and relevant non-secret binding state; and any authorized live observation. A build, URL or checked-in config is not proof of runtime behavior or production activation. If access or evidence is missing, mark that specific claim not proven. Do not run live checks or mutate provider state beyond the assignment.

## Minimal verdict format

- **Status:** PASS / PARTIAL / BLOCKED / FAIL for the selected scope and claims.
- **Evidence:** exact source and, when applicable, build, Preview or deployment identity and relevant observed settings.
- **Unproven or blocked:** missing evidence, limitations and next action; use `NOT_APPLICABLE` when none.

Use existing evidence and checks appropriate to the assignment; this format does not require additional tests, live actions or gates.

## Official references

Recheck current provider documentation and project-supported versions when applying this skill:

- Workers Builds configuration: https://developers.cloudflare.com/workers/ci-cd/builds/configuration/
- Worker Previews setup and requirements: https://developers.cloudflare.com/workers/previews/get-started/
- Preview configuration: https://developers.cloudflare.com/workers/previews/configuration/
- Preview resources and isolation: https://developers.cloudflare.com/workers/previews/resources/
- Wrangler environments: https://developers.cloudflare.com/workers/wrangler/environments/
