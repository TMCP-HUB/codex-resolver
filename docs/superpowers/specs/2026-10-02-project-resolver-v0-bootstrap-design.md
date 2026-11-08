# Project Resolver V0 bootstrap design

Date: 2026-10-02
Status: design freeze candidate
Baseline: `main` after corrective revert `2c2eaddd6029dea738793b16910550b5600d11b4`; functional architecture baseline remains `9cc81e2d2a3b7db28502a9e2270f149e28702451`.

## 1. Purpose

Make the existing Project Resolver usable now in ordinary ChatGPT Web without waiting for the future SBC Browser or PAK transport implementation.

The immediate product is a usable control/skill system, not browser automation.

A human Owner must be able to open ChatGPT Web, start a Liaison chat, point it at Project Resolver, and have that chat bootstrap the repository, select the smallest relevant existing role/workflow/skill set, and perform useful work manually.

## 2. Canonical terminology

These terms are distinct and must not be collapsed:

- **Owner**: the human using the system manually. Not a role, chat, agent, or program.
- **Project Resolver**: the system implemented by this repository.
- **repository `codex`**: the current physical GitHub repository name only. It does not mean OpenAI Codex.
- **ChatGPT Web**: the browser ChatGPT product used for Liaison/Control chats.
- **Liaison**: the first human-facing ChatGPT role instance.
- **Control Director**: a separate role that may be instantiated in a ChatGPT chat when required by the governed flow.
- **OpenAI Codex Web**: the browser-based code executor. It is a future execution transport/adapter, not this repository and not the SBC runtime.
- **SBC Browser**: the future custom browser/runtime owned by the user. It will host browser control, runtime state, logs, tabs/sessions, provider adapters, and PAK execution.
- **PAK**: a deterministic protocol/script interpreter embedded inside SBC Browser. It is not a role, agent, AI, chat, resolver, or independent runtime.

A future repository rename from `codex` to a Project Resolver-specific name may be evaluated separately. It is not required for V0.

## 3. Critical-path change

PAK, SBC transport automation, execution tickets, execution claims, provider/browser adapters, and at-most-once remote dispatch are removed from the current Project Resolver V0 critical path.

They remain valid future concerns but must not block development of:

- role contracts;
- engine/workflow completeness;
- skill library completion;
- deterministic routing/compilation;
- durable state/evidence semantics;
- manual multi-chat flows;
- scripts and validators that are useful before browser automation exists.

The current near-term critical path becomes:

```text
BOOTSTRAP
→ LIAISON
→ PROJECT RESOLVER ROUTING
→ LOAD MINIMAL EXISTING ROLE / WORKFLOW / SKILL CONTEXT
→ PERFORM USEFUL WORK IN CHAT
```

Only after that manual path is proven should automatic SBC transport become a blocking integration concern.

## 4. Missing current boundary: bootstrap

Current repository intake assumes that an agent already knows to read:

```text
AGENTS.md
→ SYSTEM_MANIFEST.yaml
→ ROUTER.md
→ selected Engine
→ selected Workflow / Role
→ bounded Skills
```

V0 requires an explicit Liaison bootstrap entry point before this sequence.

The bootstrap must:

1. identify the repository as Project Resolver;
2. detect whether an SBC runtime context was explicitly supplied;
3. read only the root control files required for progressive disclosure;
4. classify the user's request;
5. select the smallest relevant existing workflow/role/skill set;
6. continue in ordinary non-automated ChatGPT mode when SBC context is absent;
7. never invent browser automation, dispatch capability, provider sessions, or SBC state.

The bootstrap is an entry contract, not a new semantic authority owner.

## 5. SBC runtime context handshake

ChatGPT cannot infer that it is running inside SBC Browser from the web page alone. The future SBC Browser must explicitly inject a small runtime context into the conversation.

V0 should define only the minimum provider-neutral input shape required to distinguish the environment, conceptually equivalent to:

```text
SBC_PRESENT
SBC_VERSION
PAK_STATE
AVAILABLE_BROWSER_OPERATIONS
```

Rules:

- absence of the context means ordinary ChatGPT Web mode;
- presence is runtime observation, not semantic authority;
- no SBC capability may be inferred when not explicitly advertised;
- V0 may validate fixtures for this context before the SBC Browser exists;
- exact DOM/CDP/tab/provider-session mechanics remain outside Project Resolver V0.

## 6. SBC Browser and PAK boundary

The future private runtime is **SBC Browser**, not PAK.

SBC Browser may own physical runtime concerns such as:

- browser control lease;
- UI controls;
- OFF / MANUAL / AUTO state;
- pause/step controls;
- tabs/windows;
- provider sessions;
- queues/events;
- logs;
- DOM/CDP mechanics;
- provider adapters;
- runtime recovery;
- local attempt/transport bookkeeping;
- the PAK interpreter.

PAK owns only deterministic protocol execution such as:

```text
parse allowed command
→ validate syntax/mechanical preconditions
→ perform declared browser operation
→ capture declared observation/result
→ serialize result
```

PAK must not be modeled as a role, agent, control authority, routing authority, or reasoning component.

## 7. Inert content versus actuation

Natural-language or repository text must not become an external side effect merely because it contains text that resembles a provider trigger.

Required separation:

```text
CONTENT CHANNEL
!= ACTUATION CHANNEL
```

Future PAK execution must require an explicit machine-recognized command envelope plus an enabled SBC execution mode. Ordinary model prose, issue text, task documentation, examples, tests, and quoted provider commands remain inert content.

Tests must validate the actuation boundary rather than globally banning trigger-like strings from arbitrary text.

## 8. Capability profiles before SBC exists

`CAPABILITY_PROFILE` remains useful as a provider-neutral representation of observed runtime capability. It must not be deleted or replaced merely because SBC is not implemented.

However, V0 must not pretend that dynamic SBC/provider reality can already be advertised in production.

Until a real SBC runtime exists:

- capability profiles may describe currently provable/manual/reference surfaces;
- SBC/provider-specific profiles may be fixtures/reference advertisements only;
- no profile may invent browser state, authentication, remote task state, or provider capabilities;
- runtime advertisement and drift/revalidation automation remain downstream work.

Provider product names should not define universal surface semantics. OpenAI Codex Web is one future adapter for a generic remote code-execution/browser surface.

## 9. Manual vertical slices

### V0-A: one-chat useful work

Required first proof:

```text
OWNER
→ LIAISON CHAT
→ BOOTSTRAP PROJECT RESOLVER
→ SELECT EXISTING SKILL/ROLE/WORKFLOW
→ LOAD ONLY REQUIRED CONTEXT
→ PERFORM USEFUL WORK
→ RETURN RESULT TO OWNER
```

No automatic external dispatch is required.

A representative acceptance scenario should use an already-materialized skill, for example systematic debugging, exact-state verification, or another bounded skill that can operate with the available chat/connectors.

### V0-B: manual multi-chat control

After V0-A works:

```text
OWNER
→ LIAISON
→ bounded Control Director assignment
→ human manually opens/uses second ChatGPT chat
→ result returned manually
→ Liaison/Control reconciles result
```

This manually emulates the future transport boundary without requiring PAK.

### Later: OpenAI Codex Web transport

Only after the manual flow is proven should the system automate a coding executor path through OpenAI Codex Web.

The browser transport must be based on observed web behavior, not assumptions about a desktop client, CLI, or inaccessible provider internals.

## 10. Existing architecture retained

The following current architecture remains on the development path and should not be rewritten merely because transport is deferred:

- engine registry and engine boundaries;
- Liaison role;
- Control Director role;
- Assignment Compiler;
- Resolver semantic routing;
- durable artifact/readback law;
- exact-state verification;
- existing skill library;
- `CAPABILITY_PROFILE` as a data contract;
- current `resolve_spawn()` behavior up to `SPAWN_READY`.

For V0, `SPAWN_READY` means the internal control plane has produced an executable candidate for a known/manual destination. It does not require an execution-ticket/claim/PAK chain to exist yet.

## 11. Deferred from the current critical path

The following are explicitly non-blocking for Project Resolver V0 unless a concrete current feature independently requires them:

- final PAK grammar;
- SBC Browser implementation;
- OpenAI Codex Web automation;
- generic provider/browser adapter implementation;
- `EXECUTION_TICKET` as a separate artifact;
- claim/reservation dispatch protocol;
- remote acknowledgement/idempotency machinery;
- automatic session/tab recovery;
- full autonomy/scheduler implementation;
- provider usage normalization;
- private runtime repository creation.

Deferral means "not a V0 blocker", not "rejected forever".

## 12. Issue architecture corrections

The active issue set must be reconciled to this design.

### #77

Rewrite the tracker so that:

- private **SBC Browser** owns physical browser/runtime mechanics;
- PAK is only the embedded deterministic protocol/script layer;
- PAK/SBC transport completion is not a prerequisite for continuing current main development;
- `PAC_READY` is no longer the gate for all useful Project Resolver progress;
- bootstrap/manual-use readiness becomes the immediate milestone;
- future automated transport receives its own later gate after manual flows are proven.

### #57

Retain execution-surface/capability semantics, but:

- remove any implication that an OpenAI product name is a universal runtime class;
- do not require live SBC advertisement before SBC exists;
- treat provider/browser runtime integration as a downstream adapter concern;
- prioritize currently provable/manual/reference surfaces.

### #54

Retain the current Liaison authority boundary. Extend the workstream only as required for explicit bootstrap and ordinary-chat fallback behavior.

### #55

Retain Assignment Compiler semantics. Durable task materialization remains useful, but future transport/ticket mechanics must not block compiler or skill development.

### #58

Keep durable context/role continuity work, but physical tab/session mapping is a future SBC concern and must not block V0 manual continuation.

### #59

Keep autonomy semantics as future control work. Full automation is not required for manual V0 use.

### #61

Keep bounded anti-loop/Architecture Health improvements that protect current work. Do not make a large future automation-health subsystem a prerequisite for bootstrap/skill usability.

### #62

Re-prioritize repository orientation, delegated-workflow helpers, test/regression skills, and other reusable capabilities that make Project Resolver useful before automatic transport exists.

### #68

Retain resource-governance semantics where relevant to current metered operations, but claim-time browser/provider reservation integration is downstream of SBC transport.

## 13. Development priority after design freeze

The next implementation wave should optimize for immediate utility:

1. explicit Liaison bootstrap entry point;
2. minimal SBC runtime-context contract/fixture with ordinary-chat fallback;
3. route/bootstrap tests that prove no invented SBC capability;
4. one-chat vertical-slice conformance using existing roles/skills;
5. audit current role/workflow/skill completeness and fill bounded gaps;
6. manual multi-chat vertical slice;
7. continue main development in independent engines, roles, skills, validators, scripts, and durable-control features;
8. only later freeze the physical PAK/SBC transport protocol from observed runtime needs.

## 14. V0 acceptance

Project Resolver V0 bootstrap is accepted when all of the following are true:

1. A fresh ordinary ChatGPT Web chat can identify and bootstrap Project Resolver from an explicit entry point.
2. The bootstrap uses progressive disclosure and does not scan the full repository by default.
3. Absence of SBC context produces a valid ordinary-chat mode rather than a false blocker.
4. Presence of an SBC fixture is recognized only from explicit supplied runtime context.
5. No SBC/PAK/provider capability is invented from repository configuration or product naming.
6. Liaison can route at least one real Owner request to an existing role/workflow/skill and complete useful work without automatic dispatch.
7. The same architecture can represent a later manual multi-chat handoff without requiring final PAK syntax.
8. Existing Resolver, Compiler, durable-state, evidence, and skill architecture remains usable and is not rewritten around an unimplemented transport.
9. PAK is nowhere modeled as an AI role or reasoning authority.
10. Active architecture issues reflect the SBC Browser / PAK distinction and no longer make final transport implementation the blocker for current Project Resolver development.

## 15. Non-goals

This wave does not implement:

- SBC Browser;
- PAK browser automation;
- OpenAI Codex Web automation;
- CLI/desktop Codex integration;
- remote task correlation;
- automatic PR/branch promotion;
- generic provider API adapters;
- a new Resolver;
- a second capability ontology;
- a second Liaison or Control Director;
- repository rename.
