# Foundation V0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize the planned `foundation` Engine so a routed raw project idea can become durable, explicitly non-authoritative working project state without prematurely creating Canon, Research, or Production authority.

**Architecture:** Add one `foundation` Engine with one `form_project_foundation` workflow, four cognitive skills, and three Foundation-owned durable artifact schemas. Reuse the existing Router, Assignment Compiler, executability/admissibility chain, durable-output/readback contract, shared Executor/Control Director roles, and common artifact envelope; do not create a Foundation-specific runtime or second control plane.

**Tech Stack:** Markdown skill/workflow contracts, YAML engine registry/manifest, JSON Schema Draft 2020-12, Python `unittest` regression tests, existing `tools/resolver_spawn.py`, GitHub Actions `Project Resolver CI`.

**Spec:** `docs/superpowers/specs/2026-10-04-foundation-v0-design.md`

## Global Constraints

- `RAW OWNER IDEA != PROJECT_SEED != CANON`.
- Foundation artifacts are durable working state and MUST be machine-checkably non-authoritative.
- Foundation V0 exposes one root semantic capability only: `form_project_foundation`.
- Required skills: `develop-project-seed`, `define-project-outcome`, `classify-consequential-unknowns`; `design-discovery` is optional and loaded only when materially useful.
- No fixed questionnaire and no mandatory minimum question count; zero clarification questions is valid.
- Skills are guidance-first; hard invariants are reserved for authority/evidence/provenance boundaries.
- Foundation MUST NOT invent Owner intent, accept/mutate Canon, auto-dispatch Research, start Production, freeze architecture, or treat model memory as external evidence.
- Foundation V0 creates exactly three Engine-owned durable artifact types: `PROJECT_SEED`, `PROJECT_OUTCOME`, `CONSEQUENTIAL_UNKNOWN_MAP`.
- Every Foundation artifact has `status: WORKING` and `authoritative: false`; no Foundation schema contains an Owner/Canon authority field.
- `FOUNDATION_READY_FOR_OWNER_GATE` is a workflow/result status, not a fourth durable artifact type and not an Owner decision.
- `FOUNDATION_READY_FOR_OWNER_GATE` is allowed only after the assignment-declared three durable outputs are materialized and satisfy the existing durable-output/reference/readback contract.
- Reuse `roles/executor/ROLE.md` and `roles/control-director/ROLE.md`; do not create a Foundation persona.
- Reuse the common artifact envelope and generic resolver/executability machinery; no Foundation-specific spawn/runtime path.
- `NO GLOBAL SKILL DISCOVERY` remains in force.
- The exact Owner Foundation Gate and handoff into Canon are a later #53 wave and are not implemented here.

## Review Focus

- A fully specified Owner idea must be able to form useful working state with **zero** clarification questions; tests must reject any fixed-question-count contract.
- A plausible model proposal must remain distinguishable from explicit Owner intent and must not become authoritative merely because it appears in a durable Foundation artifact.
- An `EXTERNAL_FACT` or `FEASIBILITY` unknown must remain a classified unknown; Foundation must not imply that Research has been dispatched or evidence obtained.
- Straightforward project formation must not load `design-discovery` unconditionally; required/optional skill composition must be explicit and testable.
- A result claiming `FOUNDATION_READY_FOR_OWNER_GATE` without all three assignment-declared durable outputs/readback requirements must be invalid under the existing generic durable completion semantics.

---

## File Structure

**Create**
- `engines/foundation/MANIFEST.yaml`
- `engines/foundation/workflows/form-project-foundation.md`
- `engines/foundation/skills/develop-project-seed/SKILL.md`
- `engines/foundation/skills/define-project-outcome/SKILL.md`
- `engines/foundation/skills/classify-consequential-unknowns/SKILL.md`
- `engines/foundation/skills/design-discovery/SKILL.md`
- `engines/foundation/schemas/project-seed.schema.json`
- `engines/foundation/schemas/project-outcome.schema.json`
- `engines/foundation/schemas/consequential-unknown-map.schema.json`
- `tests/test_foundation_materialization.py`

**Modify**
- `SYSTEM_MANIFEST.yaml`
- `ROUTER.md`
- `protocols/artifacts.md`
- `tools/validate_structure.py`
- `tests/test_v0_structure.py` or `tests/test_structure.py` only where the existing validator split requires it.

No Foundation-specific production Python module is planned. `tools/resolver_spawn.py` remains the generic spawn path unless a test proves a genuine generic hard-coded Engine defect.

---

### Task 1: Foundation Artifact Schemas and Non-Authority Contract

**Files:**
- Create: `engines/foundation/schemas/project-seed.schema.json`
- Create: `engines/foundation/schemas/project-outcome.schema.json`
- Create: `engines/foundation/schemas/consequential-unknown-map.schema.json`
- Create: `tests/test_foundation_materialization.py`
- Modify: `protocols/artifacts.md`

**Interfaces:**
- Consumes: common envelope fields from `protocols/artifacts.md`: `artifact_id`, `artifact_type`, `produced_by_role`, `assignment_id`, `input_state_ref`, `status`, `provenance`, `related_artifacts`.
- Produces: three closed JSON Schemas with `status: {"const": "WORKING"}` and `authoritative: {"const": false}`.

- [ ] **Step 1: Write failing schema/envelope tests**

Add `FoundationMaterializationTest` cases asserting:

```python
ENVELOPE.issubset(set(schema["required"]))
schema["properties"]["artifact_type"]["const"] == expected_type
schema["properties"]["status"]["const"] == "WORKING"
schema["properties"]["authoritative"]["const"] is False
schema_accepts(valid_artifact, schema)
not schema_accepts({**valid_artifact, "authoritative": True}, schema)
```

Assert the unknown-map classification enum is exactly:

```python
{
    "OWNER_PREFERENCE",
    "EXTERNAL_FACT",
    "FEASIBILITY",
    "ARCHITECTURE_DECISION",
    "IMPLEMENTATION_DEPENDENT",
    "NICE_TO_KNOW",
}
```

Assert all three schemas are closed with `additionalProperties: false` and expose no field named `authority`, `authority_ref`, `owner_authority`, or `canon_authority`.

- [ ] **Step 2: Run focused test to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because the three Foundation schema files do not exist.

- [ ] **Step 3: Implement the three schemas**

Use JSON Schema Draft 2020-12.

`PROJECT_SEED` requires common envelope + `authoritative`, `working_summary`; optional bounded fields may include `protected_owner_intent`, `constraints`, `non_goals`, `known_decisions`, `working_interpretations`, `model_proposals`, `material_question_refs`. Do not require empty form fields merely for completeness.

`PROJECT_OUTCOME` requires common envelope + `authoritative`, `target_outcome`, `completion_condition`, `required_deliverables`, `requires_downstream_realization`. Define `completion_condition` as either a non-empty string or `null` for explicitly open; define `requires_downstream_realization` as one of `true`, `false`, or the string `UNKNOWN`. Optional fields may include `optional_deliverables`, `audience`, `non_goals`.

`CONSEQUENTIAL_UNKNOWN_MAP` requires common envelope + `authoritative`, `items`; each closed item requires `id`, `question`, `classification`, `why_it_matters`, `state`, with `state` exactly `OPEN | DEFERRED` for V0.

- [ ] **Step 4: Document the three Engine-owned artifact types**

In `protocols/artifacts.md`, add a bounded Foundation section: the three types use the common envelope but are Engine-owned, non-authoritative working artifacts and are not added to the universal required-common-type ontology.

- [ ] **Step 5: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: schema/envelope/non-authority tests PASS.

- [ ] **Step 6: Commit**

```bash
git add engines/foundation/schemas tests/test_foundation_materialization.py protocols/artifacts.md
git commit -m "feat: define Foundation working-state artifacts"
```

---

### Task 2: Foundation Cognitive Skills

**Files:**
- Create: `engines/foundation/skills/develop-project-seed/SKILL.md`
- Create: `engines/foundation/skills/define-project-outcome/SKILL.md`
- Create: `engines/foundation/skills/classify-consequential-unknowns/SKILL.md`
- Create: `engines/foundation/skills/design-discovery/SKILL.md`
- Modify: `tests/test_foundation_materialization.py`

**Interfaces:**
- Consumes: Liaison bounded routing frame, explicit Owner material, native LLM reasoning, directly relevant project context.
- Produces: guidance that populates/refines the three Foundation working artifacts while preserving Owner/model/proposal/evidence distinctions; no `DESIGN_DISCOVERY_RESULT` artifact.

- [ ] **Step 1: Write failing skill-contract tests**

Assert all four skill files:
- have unique frontmatter `name` values matching directory names;
- contain `## Execution contract`, `## Thinking guidance`, `## Hard invariants`, `## Procedure`;
- explicitly preserve native model reasoning/judgment;
- explicitly state that durable output does not create Canon/Owner authority.

Assert cognitive freedom:

```python
self.assertNotRegex(all_skill_text, r"(?i)(ask|require).*(at least|minimum)\s+[1-9][0-9]*\s+(questions|fields)")
self.assertIn("zero clarification", all_skill_text.lower())
```

Assert `design-discovery` is optional and explicitly creates no `DESIGN_DISCOVERY_RESULT`.

- [ ] **Step 2: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because Foundation skill files do not exist.

- [ ] **Step 3: Implement `develop-project-seed`**

It MUST distinguish explicit Owner statement, strongly implied context, model working interpretation, model proposal, and unresolved material question. Thinking guidance should encourage inference/reframing/judgment. Hard invariants are limited to Owner intent, evidence, Canon, authority, provenance, and global-discovery boundaries.

- [ ] **Step 4: Implement `define-project-outcome`**

Guide reasoning about target outcome, completion condition, deliverables, audience/non-goals when material, and whether realization is required. Explicitly prohibit assuming software/Production by default.

- [ ] **Step 5: Implement `classify-consequential-unknowns`**

Use exactly the six V0 classes. State that classification is not resolution, Research dispatch, Owner decision, or architecture authority. Non-consequential unknowns need not be materialized.

- [ ] **Step 6: Implement optional `design-discovery`**

Allow proposal/comparison/reframing/scope simplification/trade-off exploration. Preserve proposal status, prohibit architecture freeze by plausibility, and create no fourth durable artifact.

- [ ] **Step 7: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: skill-contract and cognitive-freedom tests PASS.

- [ ] **Step 8: Commit**

```bash
git add engines/foundation/skills tests/test_foundation_materialization.py
git commit -m "feat: add Foundation cognitive skills"
```

---

### Task 3: Foundation Manifest and Formation Workflow

**Files:**
- Create: `engines/foundation/MANIFEST.yaml`
- Create: `engines/foundation/workflows/form-project-foundation.md`
- Modify: `tests/test_foundation_materialization.py`

**Interfaces:**
- Consumes: generic `exact_assignment`, destination `CAPABILITY_PROFILE`, `ASSIGNMENT_ADMISSIBILITY`, Liaison route frame, Owner material/provenance.
- Produces: capability mapping `form_project_foundation -> form_project_foundation`; exactly three required skills plus optional `design-discovery`; terminal status `FOUNDATION_READY_FOR_OWNER_GATE` only after generic durable completion/readback requirements.

- [ ] **Step 1: Write failing manifest/workflow tests**

Assert manifest/workflow:
- `engine_id: foundation`, `status: available`;
- capability set exactly `{form_project_foundation}`;
- executing role `roles/executor/ROLE.md`;
- consuming role `roles/control-director/ROLE.md`;
- required skills exactly `develop-project-seed`, `define-project-outcome`, `classify-consequential-unknowns`;
- optional skills exactly `design-discovery`;
- `does_not_own` includes Owner authority, Canon acceptance/mutation, substantive Research, Production, independent Verification, generic orchestration, transport;
- no Foundation-specific spawn/runtime tool is declared.

Add readiness assertions that the workflow requires all three declared durable outputs with exact refs/readback before `FOUNDATION_READY_FOR_OWNER_GATE`, and STOPs before Owner gate, Canon, Research dispatch, Production.

- [ ] **Step 2: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: FAIL because manifest/workflow do not exist.

- [ ] **Step 3: Implement `engines/foundation/MANIFEST.yaml`**

Follow existing Engine manifest conventions. Reuse the generic executability contract; set `global_skill_discovery: forbidden`; list the three Foundation artifacts plus ordinary executor/workflow result as outputs; bind required and optional skills exactly as above.

- [ ] **Step 4: Implement `form-project-foundation.md`**

Encode:

```text
Liaison route frame
→ develop project seed
→ define project outcome
→ classify consequential unknowns
→ optional design discovery only when useful
→ reconcile three working artifacts
→ generic durable materialization/readback
→ FOUNDATION_READY_FOR_OWNER_GATE | bounded clarification/blocker
→ STOP
```

Zero clarification questions MUST remain valid. No Canon/Research/Production transition occurs here.

- [ ] **Step 5: Run focused tests to prove GREEN**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: manifest/workflow composition and boundary tests PASS.

- [ ] **Step 6: Commit**

```bash
git add engines/foundation/MANIFEST.yaml engines/foundation/workflows tests/test_foundation_materialization.py
git commit -m "feat: materialize Foundation formation workflow"
```

---

### Task 4: Root Registry, Router Activation, and Generic Spawn Proof

**Files:**
- Modify: `SYSTEM_MANIFEST.yaml`
- Modify: `ROUTER.md`
- Modify: `tests/test_foundation_materialization.py`
- Modify only if proven necessary: `tools/resolver_spawn.py`

**Interfaces:**
- Consumes: `form_project_foundation` selected after Liaison `ROUTE`, generic test helper `bundle(engine_id, capability, workflow)`, `durable_artifact_write`, assignment `required_durable_outputs`, `durable_system_of_record_ref`.
- Produces: active Foundation root registration and proof that the existing generic resolver can reach `SPAWN_READY` for Foundation without a Foundation-specific runtime.

- [ ] **Step 1: Write failing root registry/router tests**

Assert Foundation:
- exists once in `engine_registry`;
- has `status: available`;
- points to `engines/foundation/MANIFEST.yaml`;
- advertises only `form_project_foundation`;
- no longer appears under `planned_engines`;
- has a Router current-route row for `form_project_foundation | foundation`;
- is excluded from the `ENGINE_NOT_MATERIALIZED` Foundation wording;
- uses progressive disclosure and optional `design-discovery`, not global skill discovery.

- [ ] **Step 2: Write representative generic-spawn RED test before activation**

Create:

```python
value = bundle("foundation", "form_project_foundation", "form_project_foundation")
```

Declare the mandatory `durable_artifact_write` prerequisite and the three required durable output identities. Assert the eventual target:

```python
(result["control_state"], result["status"]) == ("ASSIGN", "SPAWN_READY")
result["engine_id"] == "foundation"
result["assignment_admissibility"]["status"] == "ADMISSIBLE"
"durable_artifact_write" in result["assignment_admissibility"]["required_capabilities"]
```

- [ ] **Step 3: Run focused tests to prove RED**

Run: `python -m unittest tests.test_foundation_materialization.FoundationMaterializationTest -v`

Expected: root tests fail because Foundation is still `not_materialized`; representative spawn fails with `ENGINE_NOT_MATERIALIZED` or the corresponding old-route state.

- [ ] **Step 4: Update `SYSTEM_MANIFEST.yaml`**

Move Foundation from `planned_engines` into `engine_registry` with only `form_project_foundation`. Preserve generic authority/state/assignment/executability entry conditions; do not invent Canon authority.

- [ ] **Step 5: Update `ROUTER.md`**

Add Foundation progressive-disclosure guidance and current route. Preserve the generic compiler, destination preflight, assignment admissibility and role activation chain. The non-materialized gate now refers only to still-unmaterialized engines such as `production/other-domains`.

- [ ] **Step 6: Run Foundation + generic durable regression tests**

Run:

```bash
python -m unittest \
  tests.test_foundation_materialization \
  tests.test_durable_output_contract \
  tests.test_durable_readback_enforcement -v
```

Expected: PASS. Existing generic tests prove that missing/wrong/duplicate durable output identities, unresolved readback, or local/session copies cannot satisfy durable completion/readback.

- [ ] **Step 7: Fix generic resolver only if Step 6 proves a genuine hard-coded Engine defect**

If and only if `tools/resolver_spawn.py` rejects the now-valid manifest/route because of a hard-coded old Engine set, make the smallest generic fix and add the exact regression. Do NOT create `resolve_foundation_spawn()`.

- [ ] **Step 8: Commit**

```bash
git add SYSTEM_MANIFEST.yaml ROUTER.md tests/test_foundation_materialization.py
git commit -m "feat: activate Foundation Engine routing"
```

If Step 7 required a generic fix, add only the exact affected generic file.

---

### Task 5: Structural Registration Gate

**Files:**
- Modify: `tools/validate_structure.py`
- Modify: `tests/test_v0_structure.py` or `tests/test_structure.py` according to the existing validator split.

**Interfaces:**
- Consumes: active Foundation registration from Tasks 1-4.
- Produces: structural validation that fails if active Foundation manifest/workflow/schemas or root registration disappear.

- [ ] **Step 1: Write failing structural tests**

Require at least:
- `engines/foundation/MANIFEST.yaml`;
- `engines/foundation/workflows/form-project-foundation.md`;
- all three Foundation schema paths;
- root manifest registration `manifest_path: engines/foundation/MANIFEST.yaml` and `form_project_foundation`.

Validate declared required/optional skill paths through bounded Foundation-specific checks; do not introduce repository-wide skill scanning.

- [ ] **Step 2: Run structural tests to prove RED**

Run the exact existing structural test modules that own `tools/validate_structure.py` (currently `tests.test_v0_structure` and `tests.test_structure`).

Expected: FAIL because the validator does not yet protect Foundation registration.

- [ ] **Step 3: Extend `tools/validate_structure.py` minimally**

Add Foundation active-surface/path/registration checks while preserving every existing validator rule.

- [ ] **Step 4: Run structural tests to prove GREEN**

Run: `python -m unittest tests.test_v0_structure tests.test_structure -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit only the validator and structural test files actually changed with message:

```text
test: protect Foundation structural registration
```

---

### Task 6: Full Regression, Diff Audit, and PR

**Files:**
- No planned new product files.
- PR body only after verification evidence exists.

**Interfaces:**
- Consumes: Tasks 1-5.
- Produces: one reviewable Foundation V0 PR against exact current `main`, with full CI evidence and no Owner Foundation Gate/Canon/Research/Production scope creep.

- [ ] **Step 1: Run Foundation-focused suite**

Run: `python -m unittest tests.test_foundation_materialization -v`

Expected: PASS.

- [ ] **Step 2: Run full repository suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 3: Run structural validator directly**

Run: `python tools/validate_structure.py`

Expected: `Project Resolver structural validation: PASS`.

- [ ] **Step 4: Audit branch diff against exact base**

Verify there is no Owner Foundation Gate implementation, Canon mutation/acceptance change, automatic Research dispatch, Production work, PAK/SBC/provider transport work, Foundation-specific resolver/runtime fork, or fourth Foundation durable artifact.

- [ ] **Step 5: Open a draft PR against `main`**

Title: `Foundation V0: materialize pre-Canon project formation`

Body includes issue #53, spec/plan paths, exact base/head SHA, three durable artifact types, four skills with `design-discovery` optional, non-authority/STOP boundary, TDD evidence, full suite + structural validator evidence, and explicit statement that Owner Foundation Gate → Canon is a later wave.

- [ ] **Step 6: Verify GitHub Actions on exact PR HEAD/merge ref**

Require `Project Resolver CI` success for the exact head being proposed; if HEAD moves, only the latest exact run counts.

- [ ] **Step 7: Do not merge without separate Owner/K0 authorization**

Return exact PR/head/CI status to Owner. Merge only after explicit Owner/K0 instruction.
