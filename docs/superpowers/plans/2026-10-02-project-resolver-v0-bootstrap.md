# Project Resolver V0 Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Project Resolver usable from a fresh ordinary ChatGPT Web Liaison chat without waiting for SBC Browser, PAK, provider transport, execution-ticket, or remote-dispatch implementation.

**Architecture:** Add one explicit root bootstrap entry, a minimal provider-neutral SBC runtime-context contract, and deterministic validation/fallback semantics. Preserve the existing Router, Compiler, Resolver, roles, durable-state/evidence contracts, and skill library. Treat `SPAWN_READY` as the current public control-plane boundary; later SBC/PAK transport consumes that boundary rather than blocking current main development.

**Tech Stack:** Markdown control contracts, YAML manifest, JSON Schema draft 2020-12, Python 3 stdlib validators/tests, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-02-project-resolver-v0-bootstrap-design.md`

## Global Constraints

- Owner is the human. It is not a role, chat, agent, or program.
- Project Resolver is the system in this repository; repository name `codex` is only the current GitHub repository name.
- OpenAI Codex Web is a later browser execution adapter, not this repository and not the SBC runtime.
- SBC Browser is the future private browser/runtime; PAK is only an embedded deterministic protocol/script interpreter.
- PAK, SBC transport automation, provider/browser adapters, execution tickets, claims, acknowledgement/idempotency, and private runtime creation are not V0 blockers.
- Absence of explicit SBC runtime context means valid `ORDINARY_CHAT` mode.
- SBC/provider capabilities must never be inferred from product names, repository configuration, or mere presence of a connector.
- `CONTENT CHANNEL != ACTUATION CHANNEL`; ordinary prose/examples/tests remain inert.
- Preserve progressive disclosure; no repository-wide skill scan during ordinary bootstrap or execution.
- Do not replace `CAPABILITY_PROFILE`, Assignment Compiler, Resolver, Liaison, or Control Director with parallel concepts.
- No repository rename in this wave.

## Review Focus

1. **Malformed explicit SBC context:** must fail closed as invalid context, not silently fall back to SBC mode or infer capabilities. Covered in Task 2 tests.
2. **No SBC context at all:** must remain a valid ordinary ChatGPT bootstrap path, not an executability failure. Covered in Tasks 1 and 2 tests.
3. **Unknown browser operation or provider-shaped field:** must remain opaque/non-authoritative and must not create a capability claim. Covered in Task 2 tests.
4. **Provider product name leaking into universal surface semantics:** active contracts/tests must use generic `REMOTE_CODE_EXECUTOR`; provider names may appear only as examples/adapters/history. Covered in Task 4 tests.
5. **Bootstrap accidentally causing global skill discovery or direct dispatch:** bootstrap must stop at route/context selection and never perform external actuation. Covered in Tasks 1 and 3 tests.

---

### Task 1: Add the explicit Liaison bootstrap entry point

**Files:**
- Create: `BOOTSTRAP.md`
- Modify: `SYSTEM_MANIFEST.yaml`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `tools/validate_structure.py`
- Create: `tests/test_liaison_bootstrap.py`

**Interfaces:**
- Consumes: existing `AGENTS.md`, `SYSTEM_MANIFEST.yaml`, `ROUTER.md`, `roles/owner-interface/ROLE.md`.
- Produces: stable root entry `BOOTSTRAP.md`; manifest key `bootstrap_entry: BOOTSTRAP.md`; ordinary bootstrap sequence `BOOTSTRAP.md -> AGENTS.md -> SYSTEM_MANIFEST.yaml -> ROUTER.md`.

- [ ] **Step 1: Write failing bootstrap-structure tests in `tests/test_liaison_bootstrap.py`**

Assert that:

```python
self.assertEqual(manifest_bootstrap_entry, "BOOTSTRAP.md")
self.assertIn("ORDINARY_CHAT", bootstrap)
self.assertIn("SBC_RUNTIME_CONTEXT", bootstrap)
self.assertIn("AGENTS.md", bootstrap)
self.assertIn("SYSTEM_MANIFEST.yaml", bootstrap)
self.assertIn("ROUTER.md", bootstrap)
self.assertIn("NO GLOBAL SKILL DISCOVERY", bootstrap)
self.assertNotIn("execution ticket required", bootstrap.lower())
```

Also assert that `README.md` identifies `BOOTSTRAP.md` as the fresh-Liaison entry while preserving the existing ordinary-agent intake after bootstrap.

- [ ] **Step 2: Run the focused test and confirm failure**

Run: `python -m unittest tests.test_liaison_bootstrap -v`

Expected: FAIL because `BOOTSTRAP.md` and `bootstrap_entry` do not exist.

- [ ] **Step 3: Create `BOOTSTRAP.md`**

It must define exactly this responsibility boundary:

```text
fresh Owner/Liaison entry
→ detect explicit SBC runtime context if supplied
→ otherwise ORDINARY_CHAT
→ read AGENTS.md
→ read SYSTEM_MANIFEST.yaml
→ read ROUTER.md
→ classify request
→ load only selected engine/workflow/role/skills
→ perform useful work or produce governed handoff
```

It must explicitly state that bootstrap creates no semantic authority, does not perform external dispatch, and does not globally scan skills.

- [ ] **Step 4: Register bootstrap without changing ordinary agent semantics**

Add to `SYSTEM_MANIFEST.yaml`:

```yaml
bootstrap_entry: BOOTSTRAP.md
```

Keep `root_control_files` as the post-bootstrap ordinary control set (`AGENTS.md`, `SYSTEM_MANIFEST.yaml`, `ROUTER.md`). Update `AGENTS.md` and `README.md` to distinguish fresh Liaison bootstrap from ordinary already-routed agent intake.

- [ ] **Step 5: Make structural validation require the bootstrap entry**

In `tools/validate_structure.py`, add `BOOTSTRAP.md` to `ROOT_REQUIRED` and verify `SYSTEM_MANIFEST.yaml` contains `bootstrap_entry: BOOTSTRAP.md`.

- [ ] **Step 6: Run focused and structural tests**

Run:

```bash
python -m unittest tests.test_liaison_bootstrap tests.test_structure -v
python tools/validate_structure.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add BOOTSTRAP.md SYSTEM_MANIFEST.yaml AGENTS.md README.md tools/validate_structure.py tests/test_liaison_bootstrap.py
git commit -m "feat: add Project Resolver Liaison bootstrap"
```

---

### Task 2: Materialize the minimal SBC runtime-context contract

**Files:**
- Create: `contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md`
- Create: `schemas/sbc-runtime-context.schema.json`
- Create: `tools/bootstrap_runtime.py`
- Create: `tests/test_sbc_runtime_context.py`
- Modify: `SYSTEM_MANIFEST.yaml`
- Modify: `tools/validate_structure.py`
- Modify: `schemas/README.md`

**Interfaces:**
- Consumes: optional runtime context supplied to the Liaison bootstrap.
- Produces:
  - `validate_sbc_runtime_context(value: Mapping[str, object]) -> list[str]`
  - `resolve_bootstrap_runtime_mode(value: Mapping[str, object] | None) -> tuple[str, list[str]]`
  - modes: `ORDINARY_CHAT`, `SBC_BROWSER`, `INVALID_CONTEXT`.

- [ ] **Step 1: Write failing validator tests**

Required cases:

```python
resolve_bootstrap_runtime_mode(None) == ("ORDINARY_CHAT", [])
```

A valid explicit context contains exactly the V0 fields:

```json
{
  "artifact_type": "SBC_RUNTIME_CONTEXT",
  "present": true,
  "runtime_version": "0.1",
  "pak_state": "OFF",
  "available_browser_operations": []
}
```

and returns `SBC_BROWSER`.

Test `pak_state` values `OFF`, `MANUAL`, `AUTO`. Test malformed values, `present=false`, blank `runtime_version`, duplicate/non-string operations, and unexpected authority/provider/session fields. These must return `INVALID_CONTEXT` with errors.

- [ ] **Step 2: Run focused tests and confirm failure**

Run: `python -m unittest tests.test_sbc_runtime_context -v`

Expected: FAIL because the schema/module do not exist.

- [ ] **Step 3: Create the closed JSON Schema**

`schemas/sbc-runtime-context.schema.json` must use `additionalProperties: false` and require only:

```text
artifact_type = SBC_RUNTIME_CONTEXT
present = true
runtime_version = non-empty string
pak_state = OFF | MANUAL | AUTO
available_browser_operations = unique array of non-empty strings
```

Do not add tab IDs, conversation IDs, provider IDs, DOM/CDP state, authority, execution tickets, or capability-profile fields.

- [ ] **Step 4: Implement deterministic runtime-mode validation**

Create `tools/bootstrap_runtime.py` with the exact public signatures:

```python
def validate_sbc_runtime_context(value: Mapping[str, object]) -> list[str]: ...

def resolve_bootstrap_runtime_mode(
    value: Mapping[str, object] | None,
) -> tuple[str, list[str]]: ...
```

`None` is ordinary mode. A supplied malformed object is invalid, never silently treated as absent and never upgraded to SBC mode.

- [ ] **Step 5: Register the contract and schema**

Add to `SYSTEM_MANIFEST.yaml` under a small bootstrap/runtime-context registration section and add structural checks in `tools/validate_structure.py`. Add the schema to `schemas/README.md` as runtime observation, explicitly not semantic authority or `CAPABILITY_PROFILE` replacement.

- [ ] **Step 6: Run tests**

Run:

```bash
python -m unittest tests.test_sbc_runtime_context tests.test_liaison_bootstrap tests.test_structure -v
python tools/validate_structure.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md schemas/sbc-runtime-context.schema.json tools/bootstrap_runtime.py tests/test_sbc_runtime_context.py SYSTEM_MANIFEST.yaml tools/validate_structure.py schemas/README.md
git commit -m "feat: add explicit SBC runtime context handshake"
```

---

### Task 3: Bind bootstrap behavior to Liaison and prove the one-chat vertical slice

**Files:**
- Modify: `roles/owner-interface/ROLE.md`
- Modify: `roles/owner-interface/skills/owner-actionability/SKILL.md`
- Modify: `tests/test_owner_interface_skills.py`
- Create: `tests/test_project_resolver_v0.py`
- Modify: `BOOTSTRAP.md`

**Interfaces:**
- Consumes: bootstrap mode from Task 2 plus existing Router/engine/workflow/skill contracts.
- Produces: one-chat V0 contract where a Liaison can route a bounded request to an existing workflow/skill without automatic external dispatch.

- [ ] **Step 1: Add failing Liaison ordinary-mode tests**

Extend `tests/test_owner_interface_skills.py` to require that Owner Interface:

- accepts ordinary ChatGPT mode as a valid operating environment;
- does not treat absence of SBC as `BLOCKED_NO_ADMISSIBLE_SURFACE` by itself;
- does not claim SBC/browser automation unless supplied by runtime context;
- preserves its existing non-authority boundary.

- [ ] **Step 2: Add failing V0 vertical-slice structural test**

In `tests/test_project_resolver_v0.py`, prove that the canonical diagnosis path is resolvable from committed files:

```text
BOOTSTRAP.md
→ ROUTER.md capability diagnose_software_failure
→ production/software manifest
→ diagnosis workflow
→ executor role
→ engines/production/software/skills/systematic-debugging/SKILL.md
```

The test must assert all exact files exist and that the diagnosis workflow explicitly names `systematic-debugging`. It must also assert bootstrap does not require PAK/SBC transport to use this manual path.

- [ ] **Step 3: Run tests and confirm failure**

Run:

```bash
python -m unittest tests.test_owner_interface_skills tests.test_project_resolver_v0 -v
```

Expected: at least the new bootstrap/ordinary-mode assertions fail.

- [ ] **Step 4: Update Liaison contract and actionability skill minimally**

Add bootstrap/ordinary-chat behavior without creating a new role or skill. Replace product-specific routing examples such as `ChatGPT, Codex Cloud, Agent System` with generic execution-surface wording where the example would otherwise imply universal product classes.

- [ ] **Step 5: Update `BOOTSTRAP.md` with one representative manual path**

Document the diagnosis example only as a progressive-disclosure demonstration. Do not hard-code diagnosis as the default route and do not introduce a global skill catalog.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m unittest tests.test_owner_interface_skills tests.test_project_resolver_v0 tests.test_liaison_bootstrap tests.test_sbc_runtime_context -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add BOOTSTRAP.md roles/owner-interface/ROLE.md roles/owner-interface/skills/owner-actionability/SKILL.md tests/test_owner_interface_skills.py tests/test_project_resolver_v0.py
git commit -m "feat: prove ordinary-chat Project Resolver V0 path"
```

---

### Task 4: Remove OpenAI-product naming from universal active surface classes

**Files:**
- Modify: `contracts/EXECUTABILITY_CONTRACT.md`
- Modify: `tests/test_execution_surface_profile.py`
- Modify: `ROUTER.md` only where active universal examples require correction
- Modify: `roles/owner-interface/skills/owner-actionability/SKILL.md` if not already handled in Task 3
- Modify: `tools/validate_structure.py` only if structural assertions need the generic class

**Interfaces:**
- Consumes: existing `CAPABILITY_PROFILE.surface_class: string` contract.
- Produces: generic reference class `REMOTE_CODE_EXECUTOR` in active universal examples; OpenAI Codex Web remains only a future adapter/example, not a universal class.

- [ ] **Step 1: Change the reference-surface test first**

In `tests/test_execution_surface_profile.py`, replace the reference `CODEX_CLOUD` case with:

```python
("REMOTE_CODE_EXECUTOR", ["repository_local_checkout", "shell", "python_runtime"], [...])
```

Add an assertion that the active universal contract does not list `CODEX_CLOUD` as a reference class.

Historical immutable task packets under `tasks/` are not rewritten merely to rename old evidence.

- [ ] **Step 2: Run focused test and confirm failure**

Run: `python -m unittest tests.test_execution_surface_profile -v`

Expected: FAIL until active contract text is updated.

- [ ] **Step 3: Update active universal docs only**

In `contracts/EXECUTABILITY_CONTRACT.md`, use reference families equivalent to:

```text
CHATGPT_CHAT
REMOTE_DEV_ENV
REMOTE_CODE_EXECUTOR
BROWSER_CONSOLE
DEPLOYMENT_RUNTIME
MANUAL_OPERATOR
```

Clarify that provider adapters may map a concrete provider product to one of these classes. Do not encode OpenAI Codex Web mechanics here.

- [ ] **Step 4: Run relevant executability tests**

Run:

```bash
python -m unittest tests.test_execution_surface_profile tests.test_executability tests.test_executability_structure -v
python tools/validate_structure.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add contracts/EXECUTABILITY_CONTRACT.md tests/test_execution_surface_profile.py ROUTER.md roles/owner-interface/skills/owner-actionability/SKILL.md tools/validate_structure.py
git commit -m "refactor: make remote code execution surface provider neutral"
```

---

### Task 5: Reconcile active architecture issues with the V0 critical path

**Files / external records:**
- Update issue body: `#77`
- Update issue body: `#57`
- Update issue bodies with bounded V0 alignment sections: `#54`, `#55`, `#58`, `#59`, `#61`, `#62`, `#68`

**Interfaces:**
- Consumes: approved design spec and Tasks 1-4 implementation state.
- Produces: issue set that no longer makes final SBC/PAK transport a prerequisite for ordinary Project Resolver development.

- [ ] **Step 1: Rewrite #77 as a program tracker around two separate milestones**

The body must make these distinct:

```text
PROJECT_RESOLVER_V0
= bootstrap + manual useful operation

AUTOMATED_SBC_TRANSPORT (later)
= SBC Browser + embedded PAK + observed provider adapters
```

Replace the old model where PAC itself owns browser backend/tabs/DOM/provider sessions. State that SBC Browser owns physical runtime mechanics and PAK is only its deterministic embedded command interpreter.

Remove execution-ticket/claim/private-runtime completion from the gate for continuing ordinary main development. Keep future transport concerns explicitly deferred rather than rejected.

- [ ] **Step 2: Correct #57 execution-surface terminology and sequencing**

Preserve `CAPABILITY_PROFILE` and executability semantics. Replace universal OpenAI-product surface naming with generic remote-code-executor terminology. State that live SBC advertisement is not required before SBC exists and reference/test/manual surfaces are valid current development targets.

- [ ] **Step 3: Add bounded V0 alignment to #54/#55/#58/#59/#61/#62/#68**

Each issue should receive only the minimum correction owned by that issue:

- `#54`: explicit Liaison bootstrap + ordinary-chat fallback; no authority expansion.
- `#55`: compiler/task materialization continues independently of future transport/tickets.
- `#58`: logical/durable context work may continue; physical tab/session mapping is SBC runtime work later.
- `#59`: autonomy remains useful but full automation is not a manual V0 prerequisite.
- `#61`: current anti-loop/architecture-health work may proceed where useful; future automation-health closure is not bootstrap blocking.
- `#62`: prioritize reusable skill/repository-orientation/test/delegation capabilities that improve manual utility.
- `#68`: retain resource-governance core; browser/provider claim-time reservation integration is later transport work.

Do not create new issues merely to mirror these corrections unless a later bounded implementation task actually needs one.

- [ ] **Step 4: Read back every changed issue**

Verify:

- no issue models PAK as an AI/role/runtime;
- no issue says final SBC/PAK transport is required before skills/roles/engines can advance;
- #77 and #57 agree on the generic execution-surface model;
- current ownership boundaries remain intact.

- [ ] **Step 5: Record exact issue URLs/numbers in the PR description, not in a new ontology artifact**

No repository code change is required for issue-body mutation itself.

---

### Task 6: Full V0 verification and pull request

**Files:**
- All files changed by Tasks 1-4
- Existing spec and this plan

**Interfaces:**
- Consumes: completed Tasks 1-5.
- Produces: one reviewable PR against `main` with bootstrap/runtime-context/provider-neutral surface changes and aligned issues.

- [ ] **Step 1: Run the complete repository test suite**

Run:

```bash
python -m unittest discover -s tests -v
python tools/validate_structure.py
```

Expected: all tests PASS and structural validator prints `Project Resolver structural validation: PASS`.

- [ ] **Step 2: Search the active tree for architectural regressions**

Check active code/contracts/docs for:

```text
PAK modeled as role/agent/runtime authority
SBC inferred when context absent
CODEX_CLOUD used as active universal surface class
bootstrap requiring execution ticket/claim
bootstrap requiring global skill discovery
```

Historical/archive/task evidence may retain old wording when immutability/history requires it; active control surfaces may not.

- [ ] **Step 3: Compare branch to `main`**

Confirm only intended V0/spec/plan/bootstrap/runtime-context/surface-neutrality files changed. Do not include unrelated cleanup.

- [ ] **Step 4: Open one PR**

Title:

```text
Project Resolver V0: bootstrap ordinary ChatGPT before SBC transport
```

PR body must summarize:

- explicit `BOOTSTRAP.md` entry;
- ordinary ChatGPT fallback;
- explicit SBC runtime-context handshake;
- one-chat vertical-slice conformance;
- provider-neutral `REMOTE_CODE_EXECUTOR` reference class;
- PAK/SBC automation removed from current critical path;
- linked issue reconciliations;
- exact test commands/results.

- [ ] **Step 5: Do not merge as part of implementation**

Leave the PR for independent review/Owner decision. No automatic Codex trigger text, no external executor invocation, and no branch-protection/ruleset mutation belongs to this plan.
