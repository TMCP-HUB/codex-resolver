from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_executability_parity import schema_accepts


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_DIR = ROOT / "engines/foundation"
SCHEMA_DIR = FOUNDATION_DIR / "schemas"
SKILL_DIR = FOUNDATION_DIR / "skills"
MANIFEST_PATH = FOUNDATION_DIR / "MANIFEST.yaml"
WORKFLOW_PATH = FOUNDATION_DIR / "workflows/form-project-foundation.md"
ENVELOPE = {
    "artifact_type",
    "artifact_id",
    "produced_by_role",
    "assignment_id",
    "input_state_ref",
    "status",
    "provenance",
    "related_artifacts",
}
UNKNOWN_CLASSES = {
    "OWNER_PREFERENCE",
    "EXTERNAL_FACT",
    "FEASIBILITY",
    "ARCHITECTURE_DECISION",
    "IMPLEMENTATION_DEPENDENT",
    "NICE_TO_KNOW",
}
FOUNDATION_SKILLS = (
    "develop-project-seed",
    "define-project-outcome",
    "classify-consequential-unknowns",
    "plan-project-topology",
    "design-discovery",
)
REQUIRED_FOUNDATION_SKILLS = FOUNDATION_SKILLS[:4]


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    if not path.is_file():
        raise AssertionError(f"missing Foundation schema: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_skill(name: str) -> str:
    path = SKILL_DIR / name / "SKILL.md"
    if not path.is_file():
        raise AssertionError(f"missing Foundation skill: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_text(path: Path, label: str) -> str:
    if not path.is_file():
        raise AssertionError(f"missing {label}: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def common(artifact_type: str, artifact_id: str) -> dict:
    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-FOUNDATION-1",
        "input_state_ref": "OWNER-REQUEST-1",
        "status": "WORKING",
        "provenance": ["OWNER-REQUEST-1"],
        "related_artifacts": [],
        "authoritative": False,
    }


class FoundationMaterializationTest(unittest.TestCase):
    def test_foundation_schemas_use_common_envelope_and_are_non_authoritative(self) -> None:
        cases = {
            "project-seed.schema.json": {
                **common("PROJECT_SEED", "SEED-1"),
                "working_summary": "A working interpretation of the project.",
            },
            "project-outcome.schema.json": {
                **common("PROJECT_OUTCOME", "OUTCOME-1"),
                "target_outcome": "A governed project concept.",
                "completion_condition": None,
                "required_deliverables": [],
                "requires_downstream_realization": "UNKNOWN",
            },
            "consequential-unknown-map.schema.json": {
                **common("CONSEQUENTIAL_UNKNOWN_MAP", "UNKNOWN-MAP-1"),
                "items": [],
            },
        }

        for name, value in cases.items():
            with self.subTest(schema=name):
                schema = load_schema(name)
                self.assertTrue(ENVELOPE.issubset(set(schema["required"])))
                self.assertIn("authoritative", schema["required"])
                self.assertEqual(schema["properties"]["artifact_type"]["const"], value["artifact_type"])
                self.assertEqual(schema["properties"]["status"]["const"], "WORKING")
                self.assertEqual(schema["properties"]["authoritative"]["const"], False)
                self.assertFalse(schema.get("additionalProperties", True))
                self.assertTrue(schema_accepts(value, schema), name)

                authoritative = deepcopy(value)
                authoritative["authoritative"] = True
                self.assertFalse(schema_accepts(authoritative, schema), name)

    def test_consequential_unknown_map_has_exact_v0_classification_vocabulary(self) -> None:
        schema = load_schema("consequential-unknown-map.schema.json")
        item_schema = schema["properties"]["items"]["items"]
        self.assertFalse(item_schema.get("additionalProperties", True))
        self.assertEqual(set(item_schema["properties"]["classification"]["enum"]), UNKNOWN_CLASSES)
        self.assertEqual(set(item_schema["properties"]["state"]["enum"]), {"OPEN", "DEFERRED"})

        for classification in UNKNOWN_CLASSES:
            value = {
                **common("CONSEQUENTIAL_UNKNOWN_MAP", f"MAP-{classification}"),
                "items": [
                    {
                        "id": "U-1",
                        "question": "A material unresolved question?",
                        "classification": classification,
                        "why_it_matters": "It may change the project or next action.",
                        "state": "OPEN",
                    }
                ],
            }
            self.assertTrue(schema_accepts(value, schema), classification)

    def test_foundation_artifact_protocol_does_not_promote_working_state_to_common_authority(self) -> None:
        protocol = (ROOT / "protocols/artifacts.md").read_text(encoding="utf-8")
        self.assertIn("PROJECT_SEED", protocol)
        self.assertIn("PROJECT_OUTCOME", protocol)
        self.assertIn("CONSEQUENTIAL_UNKNOWN_MAP", protocol)
        self.assertIn("non-authoritative", protocol.lower())
        common_types = protocol.split("## Required common artifact types", 1)[1].split(
            "## Engine-owned Foundation working artifacts", 1
        )[0]
        for artifact_type in ("PROJECT_SEED", "PROJECT_OUTCOME", "CONSEQUENTIAL_UNKNOWN_MAP"):
            self.assertNotIn(f"`{artifact_type}`", common_types)

    def test_foundation_cognitive_skills_follow_guidance_first_contract(self) -> None:
        names = []
        all_text = []
        for skill_name in FOUNDATION_SKILLS:
            text = load_skill(skill_name)
            all_text.append(text)
            match = re.search(r"^name:\s*(\S+)\s*$", text, re.M)
            self.assertIsNotNone(match, skill_name)
            names.append(match.group(1))
            self.assertEqual(match.group(1), skill_name)
            for heading in ("## Execution contract", "## Thinking guidance", "## Hard invariants", "## Procedure"):
                self.assertIn(heading, text, f"{skill_name}: {heading}")
            lower = text.lower()
            self.assertIn("native", lower, skill_name)
            self.assertTrue("reasoning" in lower or "judgment" in lower, skill_name)
            self.assertIn("durable", lower, skill_name)
            self.assertIn("canon", lower, skill_name)
            self.assertIn("owner", lower, skill_name)

        self.assertEqual(len(names), len(set(names)))
        combined = "\n".join(all_text)
        self.assertNotRegex(combined, r"(?is)(ask|require).{0,80}(at least|minimum)\s+[1-9][0-9]*\s+(questions|fields)")

    def test_develop_project_seed_preserves_source_interpretation_boundaries_and_zero_question_path(self) -> None:
        text = load_skill("develop-project-seed")
        for phrase in (
            "explicit Owner statement",
            "strongly implied context",
            "model working interpretation",
            "model proposal",
            "unresolved material question",
        ):
            self.assertIn(phrase, text)
        self.assertIn("zero clarification questions", text.lower())
        self.assertIn("working interpretation", text.lower())

    def test_project_outcome_does_not_assume_software_or_production(self) -> None:
        text = load_skill("define-project-outcome")
        lower = text.lower()
        for phrase in ("target outcome", "completion condition", "required deliverables", "non-goals"):
            self.assertIn(phrase, lower)
        self.assertIn("software", lower)
        self.assertIn("production", lower)
        self.assertTrue("must not assume" in lower or "do not assume" in lower)

    def test_unknown_classification_is_not_resolution_or_dispatch(self) -> None:
        text = load_skill("classify-consequential-unknowns")
        for classification in UNKNOWN_CLASSES:
            self.assertIn(classification, text)
        lower = text.lower()
        self.assertIn("classification is not resolution", lower)
        self.assertIn("research dispatch", lower)
        self.assertIn("owner decision", lower)
        self.assertIn("architecture authority", lower)
        self.assertIn("non-consequential", lower)

    def test_design_discovery_is_optional_and_creates_no_fourth_artifact(self) -> None:
        text = load_skill("design-discovery")
        lower = text.lower()
        self.assertIn("optional", lower)
        self.assertIn("proposal", lower)
        self.assertIn("architecture", lower)
        self.assertIn("does not create a `design_discovery_result`", lower)
        self.assertNotIn("artifact_type: DESIGN_DISCOVERY_RESULT", text)

    def test_foundation_manifest_declares_one_workflow_and_bounded_ownership(self) -> None:
        manifest = load_text(MANIFEST_PATH, "Foundation manifest")
        self.assertIn("engine_id: foundation", manifest)
        self.assertIn("status: available", manifest)
        capability_block = manifest.split("capabilities:\n", 1)[1].split("execution_contract:\n", 1)[0]
        mapped = re.findall(r"^  ([a-z0-9_]+):\s+([a-z0-9_]+)$", capability_block, re.M)
        self.assertEqual(mapped, [("form_project_foundation", "form_project_foundation")])
        self.assertIn("form_project_foundation: engines/foundation/workflows/form-project-foundation.md", manifest)

        for boundary in (
            "owner_authority",
            "canon_acceptance",
            "canon_mutation",
            "substantive_research",
            "production_planning",
            "production_implementation",
            "generic_independent_verification",
            "generic_orchestration",
            "physical_transport",
        ):
            self.assertIn(f"  - {boundary}", manifest)

    def test_foundation_workflow_skill_composition_and_roles_are_explicit(self) -> None:
        manifest = load_text(MANIFEST_PATH, "Foundation manifest")
        workflow = load_text(WORKFLOW_PATH, "Foundation formation workflow")
        self.assertIn("executing_role: `roles/executor/ROLE.md`", workflow)
        self.assertIn("consuming_role: `roles/control-director/ROLE.md`", workflow)

        required_block = manifest.split("required_skills:\n", 1)[1].split("optional_skills:\n", 1)[0]
        optional_block = manifest.split("optional_skills:\n", 1)[1].split("upstream_requirements:\n", 1)[0]
        for skill_name in REQUIRED_FOUNDATION_SKILLS:
            path = f"engines/foundation/skills/{skill_name}/SKILL.md"
            self.assertIn(path, required_block)
            self.assertIn(path, workflow)
        design_path = "engines/foundation/skills/design-discovery/SKILL.md"
        self.assertNotIn(design_path, required_block)
        self.assertIn(design_path, optional_block)
        self.assertIn(design_path, workflow)
        self.assertIn("optional", workflow.lower())
        self.assertIn("global_skill_discovery: forbidden", manifest)

    def test_foundation_workflow_readiness_requires_generic_durable_completion_and_stops_before_authority(self) -> None:
        workflow = load_text(WORKFLOW_PATH, "Foundation formation workflow")
        lower = workflow.lower()
        for artifact_type in ("PROJECT_SEED", "PROJECT_OUTCOME", "CONSEQUENTIAL_UNKNOWN_MAP",
                              "TOPOLOGY_PLAN", "PROJECT_TOPOLOGY_BOOTSTRAP",
                              "PROJECT_INDEX", "TOPOLOGY_MANIFEST"):
            self.assertIn(artifact_type, workflow)
        self.assertIn("TOPOLOGY_ADMITTED", workflow)
        self.assertIn("cold-start", workflow.lower())
        self.assertIn("FOUNDATION_READY_FOR_OWNER_GATE", workflow)
        self.assertIn("required_durable_outputs", workflow)
        self.assertIn("durable_output_refs", workflow)
        self.assertIn("independent readback", lower)
        self.assertIn("zero clarification questions is valid", lower)
        self.assertIn("stop", lower)
        for forbidden_transition in ("owner foundation gate", "canon acceptance", "research dispatch", "production"):
            self.assertIn(forbidden_transition, lower)
        self.assertIn("does not create owner/k0 authority", lower)
        self.assertIn("does not create canon authority", lower)

    def test_root_registry_and_router_activate_foundation_without_global_discovery(self) -> None:
        system = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")

        registry = re.search(
            r"^  - engine_id: foundation\n(?P<body>.*?)(?=^  - engine_id: |^planned_engines:)",
            system,
            re.M | re.S,
        )
        self.assertIsNotNone(registry)
        body = registry.group("body")
        self.assertIn("manifest_path: engines/foundation/MANIFEST.yaml", body)
        self.assertIn("status: available", body)
        capabilities = re.findall(r"^      - ([a-z0-9_]+)$", body, re.M)
        self.assertIn("form_project_foundation", capabilities)
        self.assertEqual(capabilities.count("form_project_foundation"), 1)

        planned = system.split("planned_engines:\n", 1)[1]
        self.assertNotIn("engine_id: foundation", planned)

        self.assertIn("## Foundation progressive disclosure", router)
        foundation_section = router.split("## Foundation progressive disclosure", 1)[1].split("## Canon progressive disclosure", 1)[0]
        self.assertIn("engines/foundation/MANIFEST.yaml", foundation_section)
        self.assertIn("workflow_contracts.<workflow>.required_skills", foundation_section)
        self.assertIn("design-discovery", foundation_section)
        self.assertIn("optional", foundation_section.lower())
        self.assertIn("no global skill discovery", foundation_section.lower())
        self.assertIn("| `form_project_foundation` | `foundation` |", router)

        non_materialized = router.split("## Non-materialized engine gate", 1)[1].split("## Role activation", 1)[0]
        self.assertNotIn("Foundation", non_materialized)
        self.assertNotIn("foundation", non_materialized)


if __name__ == "__main__":
    unittest.main()
