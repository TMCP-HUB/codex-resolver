from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExecutabilityStructureTest(unittest.TestCase):
    def test_post_spawn_authority_and_lifecycle_are_schema_backed(self) -> None:
        director = json.loads((ROOT / "schemas/director-decision.schema.json").read_text(encoding="utf-8"))
        executor = json.loads((ROOT / "schemas/executor-result.schema.json").read_text(encoding="utf-8"))
        admissibility = json.loads((ROOT / "schemas/assignment-admissibility.schema.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / "schemas/state-observation.schema.json").read_text(encoding="utf-8"))
        self.assertNotIn("transition_authority", director["required"])
        self.assertIn("transition_authority", director["properties"])
        self.assertFalse(director["properties"]["transition_authority"]["additionalProperties"])
        self.assertNotIn("acceptance_status", executor["properties"]["claims"]["items"]["properties"])
        self.assertIn("transition_proof", admissibility["required"])
        self.assertEqual(admissibility["properties"]["transition_proof"]["properties"]["proof_class"]["const"], "ASSIGNMENT_ADMISSION")
        self.assertEqual(state["properties"]["produced_by_role"]["const"], "control-director")

    def test_assignment_requires_proven_execution_contract(self) -> None:
        schema = json.loads((ROOT / "schemas/assignment.schema.json").read_text(encoding="utf-8"))
        self.assertIn("execution_contract", schema["required"])
        contract = schema["properties"]["execution_contract"]
        self.assertEqual(contract["properties"]["proof_status"]["const"], "PROVEN")
        self.assertEqual(contract["properties"]["unsatisfied_required_capabilities"]["maxItems"], 0)
        for required in [
            "assignment_draft_ref",
            "compiled_assignment_ref",
            "destination_id",
            "runtime_identity",
            "capability_profile_ref",
            "admissibility_ref",
            "required_capabilities",
            "mandatory_evidence_paths",
            "execution_mode",
        ]:
            self.assertIn(required, contract["required"])

    def test_capability_profile_requires_evidence(self) -> None:
        schema = json.loads((ROOT / "schemas/capability-profile.schema.json").read_text(encoding="utf-8"))
        self.assertIn("capability_evidence", schema["required"])
        self.assertIn("available_capabilities", schema["required"])
        self.assertIn("unavailable_capabilities", schema["required"])
        self.assertIn("freshness_boundary", schema["required"])
        self.assertIn("evidence_artifacts", schema["required"])
        boundary = schema["properties"]["freshness_boundary"]
        self.assertEqual(boundary["type"], "object")
        self.assertEqual(boundary["required"], ["observed_at", "valid_until"])

    def test_admissibility_schema_fails_closed(self) -> None:
        schema = json.loads((ROOT / "schemas/assignment-admissibility.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["status"]["enum"], ["ADMISSIBLE", "NOT_ADMISSIBLE"])
        self.assertIn("mandatory_actions", schema["required"])
        self.assertIn("runtime_identity", schema["required"])
        self.assertIn("compiled_assignment_ref", schema["required"])
        self.assertEqual(schema["properties"]["mandatory_actions"]["minItems"], 1)
        serialized = json.dumps(schema)
        self.assertIn('"maxItems": 0', serialized)
        self.assertIn('"minItems": 1', serialized)

    def test_route_and_evidence_schema_parity_surface(self) -> None:
        route = json.loads((ROOT / "schemas/execution-route.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(route["properties"]["status"]["const"], "ADMISSIBLE")
        self.assertEqual(route["properties"]["segments"]["minItems"], 3)
        self.assertEqual(route["properties"]["handoffs"]["minItems"], 2)
        self.assertIn("final_result", route["required"])
        handoff = route["properties"]["handoffs"]["items"]
        for field in ["source_required_capabilities", "target_required_capabilities", "internal_required_capabilities"]:
            self.assertIn(field, handoff["required"])
        profile = json.loads((ROOT / "schemas/capability-profile.schema.json").read_text(encoding="utf-8"))
        evidence = profile["properties"]["evidence_artifacts"]["items"]
        for field in ["observation_method", "created_from", "provenance", "related_artifacts"]:
            self.assertIn(field, evidence["required"])
        assignment = json.loads((ROOT / "schemas/assignment.schema.json").read_text(encoding="utf-8"))
        admissibility = json.loads((ROOT / "schemas/assignment-admissibility.schema.json").read_text(encoding="utf-8"))
        self.assertIn("route_ref", assignment["properties"]["execution_contract"]["required"])
        self.assertIn("route_ref", admissibility["required"])

    def test_root_router_and_director_require_preflight_before_assign(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
        for text in [agents, router, director]:
            self.assertIn("ASSIGNMENT_NOT_ADMISSIBLE", text)
            self.assertIn("REQUIRED_CAPABILITIES", text)
        self.assertIn("NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF", agents)
        self.assertIn("REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES", director)
        self.assertIn("UNKNOWN prerequisites, not zero prerequisites", router)
        self.assertLess(router.index("compile structured assignment semantics"), router.index("derive REQUIRED_CAPABILITIES"))
        self.assertLess(director.index("COMPILED_ASSIGNMENT"), director.index("destination executability preflight"))

    def test_compiled_assignment_schema_and_enum_parity(self) -> None:
        schema = json.loads((ROOT / "schemas/compiled-assignment.schema.json").read_text(encoding="utf-8"))
        from tools.assignment_compiler import AUTHORITY_CLASSES, CONTEXT_AUTHORITIES, INVALID_EXECUTION_HINT
        self.assertEqual(schema["properties"]["authority_class"]["enum"], list(AUTHORITY_CLASSES))
        context = schema["properties"]["context_facts"]["items"]["properties"]["authority_source"]["enum"]
        self.assertEqual(context, list(CONTEXT_AUTHORITIES))
        for field in ["authorized_claims", "authorized_evidence_requirements", "supported_execution_envelope_ref"]:
            self.assertIn(field, schema["required"])
        self.assertIn("execution_hints", schema["properties"])
        hints = schema["properties"]["execution_hints"]
        self.assertIn("non-authoritative", hints["description"].lower())
        hint = schema["$defs"]["executionHint"]
        self.assertEqual(hint["required"], ["hint_id", "hint_kind", "description"])
        self.assertFalse(hint["additionalProperties"])
        error_codes = schema["properties"]["compilation_errors"]["items"]["properties"]["code"]["enum"]
        self.assertIn(INVALID_EXECUTION_HINT, error_codes)
        envelope = json.loads((ROOT / "schemas/execution-envelope.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(envelope["properties"]["artifact_type"]["const"], "EXECUTION_ENVELOPE")
        serialized = json.dumps(schema)
        for forbidden in ["CODEX_CLOUD", "ChatGPT", "Cloudflare", "Google Drive"]:
            self.assertNotIn(forbidden, serialized)

    def test_engine_manifests_require_destination_preflight(self) -> None:
        software = (ROOT / "engines/production/software/MANIFEST.yaml").read_text(encoding="utf-8")
        verification = (ROOT / "engines/verification/MANIFEST.yaml").read_text(encoding="utf-8")
        research = (ROOT / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertIn("destination_executability_preflight_passes", software)
        self.assertIn("destination_executability_preflight_passes_for_mandatory_evidence", verification)
        self.assertIn("method_level_machine_only_admission_not_destination_proof", research)

    def test_skill_authoring_requires_execution_contract(self) -> None:
        authoring = (ROOT / "library/skills/skill-authoring/SKILL.md").read_text(encoding="utf-8")
        template = (ROOT / "library/templates/SKILL_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("Execution contract", authoring)
        self.assertIn("Required execution capabilities", template)
        self.assertIn("Supported execution modes", template)
        self.assertIn("ASSIGNMENT_NOT_ADMISSIBLE", template)


if __name__ == "__main__":
    unittest.main()
