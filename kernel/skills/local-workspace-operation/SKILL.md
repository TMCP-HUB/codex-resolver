---
name: local-workspace-operation
description: Use when an agent performs local filesystem, shell or desktop work on a user's computer and must respect that device's selected workspace, rules and installed tools.
---

# Local Workspace Operation

## Purpose
Honor the user's local workspace and instructions before work on that computer.

## Goal
Make local work repeatable across sessions without scattering project copies, duplicating common tools or mistaking a provider's launch directory for the project.

## When to use
Use only for an actually selected user computer, including Desktop Commander file or terminal operations. Remote repository/API-only work does not require a local profile or device.

## Inputs
The selected device, authorized task, known profile reference, user-selected parent and repository/agent/non-repository areas, applicable user rule file, intended destination and selected shell when specified.

## Execution contract
- **Remote-only mode:** authorized remote provider; no local device, profile, shell or human setup is required.
- **Configured local mode:** selected device and an actual supported way to read its existing profile and any configured rule source. Prefer direct file/host reads. Only when a required direct bootstrap step is unsupported by the surface, including when the provider cannot resolve the home alias and no absolute home is known, and applicable Owner/host rules permit, use an actually available selected shell for the minimum read-only bootstrap. Once a path is known, use direct profile/rule reads when available. Never use shell to bypass a file-access denial. Read applicable rules before substantive shell actions or project writes; if a user requires rules before any shell, obey that stricter rule.
- **First local setup:** actual supported profile lookup/read and an authorized way to persist it, a resolvable user home or explicit absolute profile path, and user choices only where genuinely unknown. Prefer direct file read/write. If the required direct bootstrap step is unsupported, the permitted minimal read-only shell bootstrap above may resolve home or read the profile and rule source as necessary; once a path is known, use direct reads when available; if it has no direct write, an authorized minimal shell operation may write only the profile after applicable rules are read. An access denial is not a missing surface capability and must not be bypassed. If the provider cannot resolve, persist or later supply the reference, report the exact missing capability; do not claim cross-session discovery.
- **Shell mode:** an actual permitted shell and an explicit existing/authorized task working directory. User shell selection and rules govern; no shell is universally required. A cwd, path list or instruction is not a sandbox.
- **Desktop Commander mode:** obtain the selected device's actual capabilities/configuration only when needed. Its `allowedDirectories` affects direct filesystem operations, not terminal processes; an empty list allows filesystem locations accessible to the process. Do not silently change configuration or imply shell isolation. Only configure actual approved paths after considering reads and other authorized destinations; the profile and its instruction file must remain readable by the applicable bootstrap surface.
- If mandatory local access is genuinely unavailable, report the precise local limitation; continue independent remote work where allowed.

## Required outputs
The profile and rule source actually read, selected task destination/working directory where relevant, and any real unsupported lookup, persistence or enforcement boundary. Do not expose personal paths in shared repositories.

## Procedure
1. Reuse a profile reference supplied by the selected host's persistent user instructions, current Assignment/Handoff or another already approved source. Otherwise look for `~/.config/project-resolver/local-workspace.json` on the selected device. Resolve `~` through the provider's actual home resolution or a known absolute home, not example-path placeholders. Prefer direct file/host operations. If the required direct bootstrap step is unsupported by the surface and applicable Owner/host rules permit, a real available selected shell may perform only the minimal read-only home/profile/rule lookup. An unresolved home means the provider cannot resolve the home alias and no absolute home is known; a missing profile or access denial alone does not prove that. Once home is resolved, use direct profile/rule reads when available; do not use it to bypass an access denial. If any applicable rule forbids shell before rules are read, do not launch it, even for lookup. When no permitted route exists, report the specific limitation or obtain only the necessary reference; do not invent access.
2. For genuinely first-time local setup, capture the user's chosen repository area, agent instructions/tools area, non-repository project area, existing instruction-file reference, optional common parent and preferred shell when specified. Reuse known answers and existing areas; do not move or duplicate projects. Save one small per-user/device JSON profile at the locator above using direct file operations when supported. If the surface has no direct write and applicable rules permit, an actual selected shell may write only that profile after applicable rules have been read; never bypass a denial. For the profile, use exact keys `repository_root`, `agent_root`, `project_root` and, when an existing rule source was supplied, `instruction_file`. Add `common_parent` and `preferred_shell` only when selected. Path values are absolute device paths; `preferred_shell` is the selected shell. Include no credentials. Reuse an existing compatible user/host profile instead. Keep the profile local/private. If the host cannot persist or rediscover it, say so rather than promising later automatic loading.
3. Read the `instruction_file` when supplied, and any applicable host/user instructions, before substantive shell actions or project writes; apply stricter no-shell-before-read rules when present; do not invent a rule file when no such source exists. Preserve stronger applicable project/user instructions and explicit task destinations. Pass the reference and applicable constraints through the existing Assignment/Handoff to the agent actually performing local work; that agent independently reads missing rules on its available device surface. A coordinator need not possess all delegated tools.
4. Reuse an existing authorized checkout for repository work; place any authorized new clone, worktree, snapshot or source export only in the selected repository area unless the user explicitly authorized another destination. Use the selected project area for non-repository work and the agent area for reusable agent tools. Resolve paths using actual OS semantics; do not treat a textual prefix as proof that a path is inside an area.
5. Establish the actual task directory for each terminal invocation and use the shell specified by the user's rules. Never assume the provider/server startup cwd is a workspace. Reuse installed common per-user tools and environments across projects. Ordinary application/user config, cache, log and temporary paths may be used when actually needed and authorized; do not use them to hide project copies. Avoid system-wide changes for all OS accounts unless authorized.
6. Preserve existing user files and previously authorized destinations. Clean only safely identified temporary material from the current task where authorized. Report real limits: instructions, working-directory selection and provider file-path checks do not constrain arbitrary shell subprocesses. Stronger isolation is an optional actual OS/provider capability, not a default service or new infrastructure.

## Anti-patterns
- Treating a non-empty workspace reference, provider connection or self-declared profile as evidence that local rules were read.
- Setting up a user's computer for a remote-only assignment, scanning all disks or forcing one path layout across operating systems.
- Creating duplicate repositories, hiding a checkout in an app cache or relocating user data without authorization.
- Requiring every project to have a duplicate environment or prohibiting normal per-user application data.
- Presenting Desktop Commander directory settings or a change of cwd as enforcement of all terminal writes.

## Minimal verdict format
State actual mode, selected profile/rule source read, task destination and shell if used, and any unsupported persistence or isolation claim. No screenshots, manual testing, new tests or external approval are implied by this skill.
