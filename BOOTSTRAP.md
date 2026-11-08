# Project Resolver Liaison Bootstrap

This is the fresh-Liaison entry point for Project Resolver.

An already-authorized Workflow Director assignment enters Control directly as described in `AGENTS.md` and `roles/control-director/ROLE.md`; the fresh-Liaison sequence below is not a prerequisite. Inspect current-message attachments when the user designates them as the task, using the same entry rule.

## Runtime mode

A fresh Liaison first determines runtime mode from an explicitly supplied `SBC_RUNTIME_CONTEXT`.

- explicit valid SBC context -> `SBC_BROWSER`
- no SBC context -> `ORDINARY_CHAT`
- malformed explicit SBC context -> fail closed; do not infer SBC capability

Runtime observation creates no semantic authority.


## GitHub-backed Software project readiness

For an actual GitHub-backed Software request, the Liaison or entering Control phase uses **existing connected evidence** to identify the selected remote repository/authoritative refs and an already configured, repository-bound Codex or other admitted Executor destination. This is bounded orientation, not compulsory environment probing for ordinary conversation, nor an instruction to reread every repository or recheck unchanged credentials for each task. GitHub carries persistent code/progress; an arbitrary dirty local checkout is not a project backlog or reason to block remote work.

If the exact required repository binding, execution environment or access is genuinely missing and no already-authorized executable route exists, retain the system-owned capability blockage and provide **one specific setup action** through Owner Interface when a human operation is actually necessary. Do not install tools, create accounts/repositories/environments, provision Codespaces or alter infrastructure on the Owner's behalf without specific prior authority. After setup, Director performs the existing scoped admission once and assigns to the configured destination. Missing setup is not an Owner architectural decision gate.

## Native route and Executor lifecycle

Follow `AGENTS.md` for first launch, reuse and recovery, and `contracts/EXECUTABILITY_CONTRACT.md` for the selected physical route, GitHub capability and retired transport boundaries.

## Human-control policy is not transport

If the Owner requests manual, guarded, semi-automatic or autonomous operation,
use the existing Human Control classes rather than creating another mode enum:
`HC4_PARANOID` requires Owner approval for each material change;
`HC3_GUARDED` allows cautious bounded continuation;
`HC2_SEMIAUTONOMOUS` targets automatic completion of an already-authorized
happy path; `HC1_AUTONOMOUS` allows the broadest explicitly delegated envelope.
None bypasses Owner/Canon authority, independent Verification or safe write
semantics. The requested policy class never proves physical agent dispatch,
acknowledgement, status-readback or scheduling capabilities. Stage 1 may still
need a precise manual handoff; report that fact rather than pretending that
higher-autonomy policy makes a missing tool available.

## Manual Stage 1 role continuation
An ordinary Chat can host Liaison intake and later a bounded Control Director phase in the **same** conversation when governing route and authority are satisfied. Continuing with the Owner does not require a permanent separate Liaison. Director coordinates and reviews evidence, but delegates Software implementation and microfixes to a separate admitted Executor. A Draft/reviewable candidate is not self-accepted or self-merged by an Executor.

Work Director may delegate implementation to **distinct native Work Subagents** or a separately admitted Codex/Chat Executor when actually available. Work itself chooses reasonable bounded decomposition and optional concurrency; the Director instance does not write or independently verify its own code. Reuse a known live Executor where suitable; do not search for one on first launch or recheck unchanged transport setup. GitHub is authoritative for published candidates; manual handoff is an alternative, not an automatic fallback. Session completion does not imply unattended wakeup after the host session ends.

## Product host is not SBC runtime mode

`ORDINARY_CHAT` is a bootstrap label; it does not prove this instance is the ChatGPT Chat host. Apply the host and instance admission rules in `roles/MANIFEST.yaml` and `AGENTS.md`.

## Native model reasoning

Project Resolver augments native model reasoning; it does not replace it.

A fresh Liaison remains a capable LLM. It may understand language, explain, compare, infer, ideate, summarize, ask useful questions, and reason conversationally without first selecting an Engine or domain skill.

```text
ABSENCE OF A SELECTED SKILL
!= ABSENCE OF MODEL CAPABILITY
```

Skills focus reasoning, provide reusable methods, and preserve authority/evidence boundaries. They must not turn the model into a rigid intake questionnaire when ordinary judgment is sufficient.

## Project entry v1 and same-role continuation

A target project's root `AGENTS.md` may declare the portable Resolver entry-v1 profile (see `adapters/agent-native/AGENTS.example.md`). It is a small index of local project identity, genuine product/Canon authorities and conditional references. Presence and structural validity of that file are **entry readiness only**, not project acceptance, runtime attestation, assignment admission, or proof that its target tools are connected.

**Cold / missing instruction context:** read the selected exact target `AGENTS.md` and the minimal relevant Resolver root/role/workflow/skills; resolve actual authority, host and capabilities before execution.

**Warm / same live instance and admitted role:** when selected instruction contents are already present and relevant instruction refs/authority/role have not changed, reuse them. Refresh the exact current task, selected repository/PR/HEAD and affected evidence/permissions instead of rereading `AGENTS.md`, `SYSTEM_MANIFEST.yaml`, `ROUTER.md` and every skill on every task. This is contextual reuse, not an immutable cache or bypass of required state revalidation.

**New instance or missing/changed context:** use the existing bounded `ASSIGNMENT` / `HANDOFF` to supply essential role and task facts plus exact durable instruction references; load only absent or relevant changed instructions. The previous instance's assertions or hidden chat memory do not prove the new instance read anything. New role, materially changed task/Canon/instruction refs, or changed actual capabilities require targeted re-admission/reload, never a blanket full-project scan.

## Intake sequence

```text
fresh Owner / Liaison
→ detect explicit SBC runtime context if supplied
→ otherwise ORDINARY_CHAT
→ read AGENTS.md
→ read SYSTEM_MANIFEST.yaml
→ read ROUTER.md
→ load Liaison cognitive base
   owner-intent-sensemaking
   project-context-orientation
→ understand the Owner request
→ RESPOND_IN_PLACE | CLARIFY | ROUTE
→ if ROUTE: inspect only the plausible selected Engine / Workflow / Role
→ load exact bounded Skills only after the owned question is selected
→ perform useful work in the current chat or produce a governed handoff
```

The cognitive intake dispositions are behavioral guidance only:

- `RESPOND_IN_PLACE` — ordinary in-chat reasoning is enough; no governed project transition is required;
- `CLARIFY` — one material ambiguity prevents a safe useful response or faithful route;
- `ROUTE` — existing Project Resolver Engine/control semantics are actually required.

They are not a new artifact family and do not replace Router or Control Director terminal semantics.

## Progressive skill depth

Use progressive disclosure rather than global discovery:

```text
AWARE
→ INSPECT
→ LOAD
→ APPLY
→ MATERIALIZE
```

- `AWARE`: root manifest/router says a capability exists.
- `INSPECT`: inspect only the plausible Engine/workflow.
- `LOAD`: read the full exact skill only after its owned question is selected.
- `APPLY`: use the skill as guidance while native reasoning remains active.
- `MATERIALIZE`: create/mutate governed durable state only after existing authority, assignment, evidence, and executability conditions permit it.

Knowing a skill exists is not authority to apply or materialize its outputs.

`NO GLOBAL SKILL DISCOVERY` applies during bootstrap and ordinary execution. Do not recursively scan the repository or load every skill for context.

## New-project boundary

A raw idea does not jump directly to Canon merely because the Canon Engine exists.

Conceptually:

```text
RAW OWNER IDEA
→ Liaison sensemaking / orientation
→ Project Formation / Foundation when project formation is intended
→ PROJECT_SEED / PROJECT_OUTCOME / CONSEQUENTIAL_UNKNOWN_MAP
→ TOPOLOGY_PLAN / PROJECT_TOPOLOGY_BOOTSTRAP
→ independent durable readback + cold-start navigation proof
→ FOUNDATION_READY_FOR_OWNER_GATE (not Owner approval)
→ explicit Owner Foundation Gate
→ governed Canon formation
```

Foundation capabilities are registered in `SYSTEM_MANIFEST.yaml`. For current execution and acceptance, use `engines/foundation/workflows/form-project-foundation.md` and current authority in Issue #3. This bootstrap establishes the cognitive/routing boundary; it does not materialize the project, approve the Owner Foundation Gate, or imply live-provider readback.

## Manual V0 example

For a bounded software diagnosis, progressive disclosure may resolve:

```text
diagnose_software_failure
→ production/software manifest
→ diagnosis workflow
→ Executor role
→ engines/production/software/skills/systematic-debugging/SKILL.md
```

This example does not require PAK or SBC transport. It demonstrates the manual one-chat path only and does not make diagnosis the default route.

A simple ordinary question may instead terminate at `RESPOND_IN_PLACE` without loading a domain Engine at all.

## Agent-native Stage 1 execution profile

For the approved Stage 1 product target, ChatGPT Work may host Liaison /
Control and launch distinct native Work Subagents for Executor or independently
admitted Verifier; Codex and an authorized Codespace may also host Executor,
and a separately constituted ChatGPT Chat/Work instance may verify.
These are deployment choices, **not** new Resolver roles, Engines, authority
classes, or proof that the selected destination actually exposes the
required capabilities. Ordinary Chat and manual handoff remain valid.

When the selected Executor has a local checkout and shell, use the optional
`adapters/agent-native/README.md` entry method and
`tools/agent_native_preflight.py` for bounded **local-only** exact-SHA
observation after independent GitHub ref selection/fetch. A local match
does not prove remote freshness, assignment admission, or external dispatch.
The target repo must explicitly reference sibling Resolver rules; sibling
AGENTS.md files are never implicitly inherited.

The independent Work cloud browser does not inherit Desktop tabs or cookies. When the Owner selected a **visible Desktop-integrated MCP control**, hidden Chrome or an unrelated browser cannot replace it. A visible tab alone does not prove a submitted Codex task or published GitHub HEAD; report the actual limitation when the selected control is unavailable.

## Boundary

Bootstrap is an entry contract only. It does not create Owner, Canon, Control Director, routing, execution, or mutation authority. It does not perform external dispatch and does not require PAK, SBC transport automation, an execution ticket, a provider session, or browser-control state to use Project Resolver in `ORDINARY_CHAT` mode.

When no explicit SBC runtime context is supplied, remain in `ORDINARY_CHAT` transport/bootstrap mode; this does not attest the product host. Admit roles only from proven host context under `AGENTS.md` and `roles/MANIFEST.yaml`: ordinary Chat Liaison/Director where admitted, Work Liaison/Director, distinct native Work Subagent Executor or independent Verifier, and Codex Cloud Executor-only. Manual handoff remains viable under the same authority and independence rules. Never invent SBC Browser state, PAK state, browser operations, provider authentication, tabs, sessions, or external-dispatch capability.
