---
name: setup
description: Set up the Project Resolver workflow for an existing project using already configured repositories, tools, and agent environments, including first or resumed local-computer setup. Use on initial installation or when a user asks how to start.
---

# Project Resolver setup

## Purpose
Set up the user's selected Resolver workflow and, only when needed, its local-computer workspace.

## Goal
Use existing authorized tools and preserve the user's chosen workspace and rules across sessions.

## When to use
For initial or resumed setup of a Resolver workflow; local setup applies only to a selected computer.

## Inputs
The user's actual task, chosen project or local device, known paths and applicable instructions.

## Execution contract
Remote-only mode requires the selected provider access only. Authorized local-only setup needs no GitHub or network access. It uses the packaged procedure, applicable user/project instructions, actual supported profile read/persistence capabilities, a supported home-directory lookup or supplied absolute profile path, and user input only for missing choices. Prefer direct file operations. Where a required direct bootstrap step is unsupported by the surface, including genuinely unresolved home, applicable Owner/host policy permits, and a selected shell really exists, that shell may perform minimal read-only home/profile/rule lookup. Once the path is known, use direct reads when available; never bypass a file-access denial. A user rule requiring instructions before any shell remains binding. Any shell write to create only the authorized profile requires applicable rules to have been read and direct writing to be unsupported by the surface. If the chosen host cannot persist, resolve, or read the reference, report that limitation without inventing automatic loading or blocking independent remote work. Creating a profile does not prove OS-level enforcement.

## Required outputs
Configured reference and chosen locations for local mode, or the exact missing capability; ordinary remote setup reports only its actual route.

## Procedure

Use existing capabilities; this skill does not install tools or create project infrastructure.

1. Identify the user's **selected target** and applicable user/project authority. For local-only setup no repository or network connection is required. When the question is general, explain the workflow without forcing a project-specific setup.
2. If the task is GitHub-backed, prefer an already connected GitHub provider or native Git with the user's existing permissions. Read the target project's current `AGENTS.md` and its declared Resolver reference (if present) at the selected remote ref. Never infer that a local sibling checkout, browser tab, plugin installation or remote desktop connection grants access.
3. For a GitHub-backed task or another genuine need for canonical source, use `https://github.com/TMCP-HUB/codex-resolver` at an accessible, verified ref; read its `AGENTS.md`, `SYSTEM_MANIFEST.yaml`, `ROUTER.md`, then only the relevant role/workflow/skills. An authorized local-only setup may use the packaged local procedure without that network access, while preserving applicable Owner, host and project instructions; do not claim an unread source was read or replace repository evidence when the actual task requires it.
4. Determine whether an already configured execution destination can perform the **required** action when an actual assignment is being prepared. Work Director may launch distinct native Work Subagents for implementation and separate verification, or use Codex/Chat/other admitted agents. Reuse known-current capabilities and environments rather than checking the same setup for every new child. Never assume a subscription/model/tier implies a capability. Do not create accounts, projects, environments or services unless separately authorized.
5. If an essential missing connection/setup action truly requires the human, specify that **one** action and its purpose; do not turn machine routing into a questionnaire or Owner gate. If the work can proceed through another already-admitted path, use that path.
6. Use the `project-resolver` skill when appropriate to continue the current task with applicable role separation, proportional verification and Owner/Canon decisions. GitHub-first durable state applies to GitHub-backed work; local-only setup can finish using the packaged procedure.

**Local computer, first use only:** Reuse the user's previously selected device profile and rules when known. Otherwise use an existing globally loaded host/user instruction or Assignment reference; if absent, try the portable per-user locator `~/.config/project-resolver/local-workspace.json` on the selected device, resolving `~` only through a real supported home lookup or known absolute home (not example values). Prefer direct file/host reads. If a required direct bootstrap step is unsupported by the surface and applicable Owner/host rules permit, use an actually available selected shell only for the minimum read-only home/profile/rule lookup. This includes when the provider cannot resolve the home alias and no absolute home is known; a missing profile or access denial alone does not prove that. Once home is known, use direct profile/rule reads when available. Never bypass a file-access denial or violate a user rule requiring rules before any shell. When the profile is missing, ask only for genuinely unknown choices: common parent if applicable, repository area, agent instructions/tools area, non-repository project area, existing rule-file reference and preferred shell if specified. Preserve existing selected locations, even outside a common parent.

With the user's selected local setup, persist one small per-user/device JSON file at that locator using direct file operations when supported. If the surface lacks direct writing, a permitted selected shell may write only that profile after applicable rules are read; never bypass a denial. Use exact keys `repository_root`, `agent_root`, `project_root`, and `instruction_file` when an existing local rules file is supplied; use `common_parent` and `preferred_shell` only when selected. Values are the selected absolute paths (or selected shell for `preferred_shell`); include no credentials. Reuse an already configured user/host profile instead when present. Carry the profile reference to future local actors through the host's supported persistent user instructions and Assignment/Handoff. On later local use, read the profile and any configured rule file, together with applicable host/user instructions, before substantive shell actions or project writes. Obey any stricter instruction that requires rules before any shell. If the provider cannot resolve the home alias, read the profile or persist/receive its reference, report the exact limitation and obtain only the missing absolute path; do not pretend a profile or auto-loading exists. If a provider's direct-file path allowlist is used, ensure it permits reading the selected profile and rules as well as the other already authorized destinations; never bypass a resulting denial through shell; do not silently narrow those destinations. The locator is per-user configuration, not a project checkout or a required new daemon. Do not put personal paths in a project repository.

**Local operations without network:** After reading any configured rule file and applicable host/user instructions, reuse the selected areas: keep authorized repository clones, worktrees and source copies in the repository area unless an explicit task authorizes another destination; put non-repository work and reusable agent tools in their selected areas. Establish the actual task directory for each terminal invocation and honor the user's selected shell. Reuse existing common per-user tools and necessary application configuration/caches; do not duplicate checkouts or move/delete pre-existing user data. Desktop Commander `allowedDirectories` controls direct file operations, not shell commands; an empty list allows the process's OS-accessible filesystem. If configuring an allowlist, preserve profile, rule-file and other authorized access. Neither it nor a working-directory change is a shell sandbox. This in-package procedure is sufficient for authorized local-only setup; no source-repository fetch or extra approval is implied.

**Cold start is normal:** When the Owner starts a new governed workflow, the absence of any prior Executor is not an execution error. Use the already configured/verified native agent launch action to create the first admitted Executor. Search/reuse a chat only if this workstream previously created and bound one. If a dispatched task has unknown acknowledgement, reconcile its existing task/session and available result or handoff before launching another, using GitHub state only for GitHub-backed work; a proven terminal/absent task may be replaced through the approved native route. Do not retest unchanged transport setup or require a new Owner decision just because the first worker has not yet been created.

**Selected transport is binding:** A new GitHub-backed Work-hosted assignment may choose a distinct native Work Subagent or Codex Cloud Executor with real GitHub publication capability. Local-only work uses the selected admitted destination and capabilities actually needed without implying GitHub publication; a specifically frozen in-flight route remains binding. Do not redirect either through legacy Linear `@codex`, PR-comment coding or detached old environments. If Owner selected visible Desktop-integrated MCP control, do not open an independent hidden browser. Report the actual unavailable tool instead of changing the route.

**Git-first publication readiness:** For GitHub-backed Software code changes, verify an actual remote GitHub branch/PR publisher for the selected repository before admitting local work; a connector that only reads Issues or a writable disposable directory is not enough. Reuse existing target PRs. Unfinished code must be checkpointed to its authorized remote candidate before a substantive handoff/session exit when safe; missing publication remains an exact scoped blocker, not an invitation to create another environment or let temporary work disappear.

No always-on monitor, MCP, credentials, custom host attestation, model-effort control or background dispatch is installed by this skill. Plugin installation is entry readiness, not permission to mutate any project.

## Anti-patterns
Do not make remote-only work depend on local paths, silently move existing projects, assume a default shell, duplicate common environments, or claim folder settings sandbox shell commands.

## Minimal verdict format
Report configured or reused profile reference, which local rules were actually read, and any real lookup/persistence limitation; distinguish source instructions from live provider enforcement.
