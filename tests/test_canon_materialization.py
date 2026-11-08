from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_assignment_compiler import action
from tests.test_executability_parity import schema_accepts
from tests.test_resolver_spawn import attach_research_admission, bundle
from tools.resolver_spawn import resolve_spawn

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE = {
    "artifact_type", "artifact_id", "produced_by_role", "assignment_id",
    "input_state_ref", "status", "provenance", "related_artifacts",
}
CAPABILITIES = {
    "establish_canon_foundation", "register_canon_fact", "register_canon_assumption",
    "register_unknown", "register_ambiguity", "register_contradiction",
    "reconcile_research_into_canon", "classify_canon_change", "validate_canon",
    "freeze_canon", "final_canon_reconciliation", "reopen_canon",
}
SCHEMA_TEMPLATE_PAIRS = {
    "canon-foundation.schema.json": "CANON_FOUNDATION.yaml",
    "canon-state.schema.json": "CANON_STATE.yaml",
    "canon-change-proposal.schema.json": "CANON_CHANGE_PROPOSAL.yaml",
    "canon-reconciliation-result.schema.json": "CANON_RECONCILIATION_RESULT.yaml",
    "canon-freeze-record.schema.json": "CANON_FREEZE_RECORD.yaml",
}
WORKFLOW_REQUIRED = {
    "establish-canon-foundation.md": ["establish-canon-foundation", "validate-canon"],
    "reconcile-research-into-canon.md": ["reconcile-research-into-canon", "validate-canon"],
    "manage-production-canon-change.md": ["classify-canon-change", "validate-canon"],
    "validate-and-freeze-canon.md": ["validate-canon", "freeze-canon"],
    "final-canon-reconciliation.md": ["validate-canon", "freeze-canon"],
    "reopen-canon.md": ["reopen-canon"],
}


def load_schema(name: str) -> dict:
    return json.loads((ROOT / "engines/canon/schemas" / name).read_text(encoding="utf-8"))


def profile_artifact(value: dict) -> dict:
    return next(item for item in value["artifacts"] if item.get("artifact_type") == "CAPABILITY_PROFILE")


class CanonMaterializationTest(unittest.TestCase):
    def test_registry_manifest_router_and_capability_uniqueness(self) -> None:
        system = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
        manifest = (ROOT / "engines/canon/MANIFEST.yaml").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")

        registry = re.search(r"^  - engine_id: canon\n(?P<body>.*?)(?=^  - engine_id: |^planned_engines:)", system, re.M | re.S)
        self.assertIsNotNone(registry)
        body = registry.group("body")
        self.assertIn("manifest_path: engines/canon/MANIFEST.yaml", body)
        self.assertIn("status: available", body)
        registered = set(re.findall(r"^      - ([a-z0-9_]+)$", body, re.M)) & CAPABILITIES
        self.assertEqual(registered, CAPABILITIES)
        self.assertNotIn("engine_id: canon", system.split("planned_engines:", 1)[1])

        capability_block = manifest.split("capabilities:\n", 1)[1].split("execution_contract:\n", 1)[0]
        mapped = re.findall(r"^  ([a-z0-9_]+):\s+[a-z0-9_]+$", capability_block, re.M)
        self.assertEqual(set(mapped), CAPABILITIES)
        self.assertEqual(len(mapped), len(set(mapped)))
        for capability in CAPABILITIES:
            self.assertIn(f"| `{capability}` | `canon` |", router)
        self.assertIn("workflow_contracts.<workflow>.required_skills", router)
        non_materialized = router.split("## Non-materialized engine gate", 1)[1].split("## Role activation", 1)[0]
        self.assertNotIn("belongs to Canon", non_materialized)
        self.assertNotIn("resolve_canon_spawn", (ROOT / "tools/resolver_spawn.py").read_text(encoding="utf-8"))

    def test_workflow_roles_and_mandatory_skill_composition_are_explicit(self) -> None:
        manifest = (ROOT / "engines/canon/MANIFEST.yaml").read_text(encoding="utf-8")
        for workflow_name, skill_names in WORKFLOW_REQUIRED.items():
            workflow = (ROOT / "engines/canon/workflows" / workflow_name).read_text(encoding="utf-8")
            self.assertIn("executing_role: `roles/executor/ROLE.md`", workflow)
            self.assertIn("consuming_role: `roles/control-director/ROLE.md`", workflow)
            for skill_name in skill_names:
                rel = f"engines/canon/skills/{skill_name}/SKILL.md"
                self.assertIn(rel, workflow)
                self.assertIn(rel, manifest)
                self.assertTrue((ROOT / rel).is_file())
        self.assertIn("workflow_required_skills_are_mandatory_prerequisites: true", manifest)
        self.assertIn("global_skill_discovery: forbidden", manifest)

    def test_all_active_canon_skills_have_execution_contract_and_unique_names(self) -> None:
        files = sorted((ROOT / "engines/canon/skills").glob("*/SKILL.md"))
        self.assertEqual(len(files), 11)
        names = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*(\S+)\s*$", text, re.M)
            self.assertIsNotNone(match, path)
            names.append(match.group(1))
            self.assertIn("## Execution contract", text, path)
            self.assertIn("durable_artifact_write", text, path)
            self.assertIn("ASSIGNMENT_NOT_ADMISSIBLE", text, path)
        self.assertEqual(len(names), len(set(names)))

    def test_durable_canon_schemas_and_templates_use_common_envelope(self) -> None:
        for schema_name, template_name in SCHEMA_TEMPLATE_PAIRS.items():
            schema = load_schema(schema_name)
            with self.subTest(schema=schema_name):
                self.assertTrue(ENVELOPE.issubset(set(schema["required"])))
                template = (ROOT / "engines/canon/templates" / template_name).read_text(encoding="utf-8")
                for field in ENVELOPE:
                    self.assertRegex(template, rf"(?m)^{re.escape(field)}:")

    def test_malformed_accepted_canon_state_cannot_masquerade_as_valid(self) -> None:
        schema = load_schema("canon-state.schema.json")
        state = {
            "artifact_type": "CANON_STATE", "artifact_id": "CANON-1", "produced_by_role": "executor",
            "assignment_id": "ASSIGN-1", "input_state_ref": "STATE-0", "status": "ACCEPTED",
            "provenance": ["AUTH-1"], "related_artifacts": ["FOUND-1"], "project_id": "P",
            "canon_version": "1.0.0", "maturity": "CANON_1_0",
            "authority": {"holder": "OWNER/K0", "scope": "canon", "source_ref": "AUTH-1"},
            "foundation_ref": "FOUND-1", "research_release_ref": "REL-1", "reconciliation_ref": "REC-1",
            "entries": [], "freeze": {"state": "OPEN", "scope": "canon", "freeze_record_ref": None},
            "change_history": [],
        }
        self.assertTrue(schema_accepts(state, schema))
        for field in ("artifact_id", "authority", "provenance"):
            malformed = deepcopy(state)
            malformed.pop(field)
            self.assertFalse(schema_accepts(malformed, schema), field)
        entry_schema = schema["$defs"]["entry"]
        malformed_entry = {"id": "F-1", "type": "FACT", "statement": "x", "status": "ACCEPTED", "scope": "s", "provenance": ["E-1"]}
        self.assertFalse(schema_accepts(malformed_entry, entry_schema))

    def test_canon_authority_transitions_fail_closed(self) -> None:
        proposal_schema = load_schema("canon-change-proposal.schema.json")
        proposal = {
            "artifact_type": "CANON_CHANGE_PROPOSAL", "artifact_id": "CP-1", "produced_by_role": "executor",
            "assignment_id": "A-1", "input_state_ref": "C-0", "status": "ACCEPTED", "provenance": ["E-1"],
            "related_artifacts": ["C-0"], "project_id": "P", "prior_canon_ref": "C-0", "change_id": "CH-1",
            "change_class": "A_ENRICHMENT", "statement": "x", "scope": "s", "authority_required": "canon",
            "authority_ref": None, "evidence_refs": ["E-1"], "downstream_revalidation": [],
        }
        self.assertFalse(schema_accepts(proposal, proposal_schema))
        proposal["authority_ref"] = "AUTH-1"
        self.assertTrue(schema_accepts(proposal, proposal_schema))

        reconciliation_schema = load_schema("canon-reconciliation-result.schema.json")
        reconciliation = {
            "artifact_type": "CANON_RECONCILIATION_RESULT", "artifact_id": "R-1", "produced_by_role": "executor",
            "assignment_id": "A-1", "input_state_ref": "C-0", "status": "ACCEPTED", "provenance": ["REL-1"],
            "related_artifacts": ["C-0", "REL-1"], "project_id": "P", "source_canon_ref": "C-0",
            "research_release_refs": ["REL-1"], "dispositions": [], "change_proposal_refs": [], "mutation_authority_ref": None,
        }
        self.assertFalse(schema_accepts(reconciliation, reconciliation_schema))
        reconciliation["mutation_authority_ref"] = "AUTH-1"
        self.assertTrue(schema_accepts(reconciliation, reconciliation_schema))

        freeze_schema = load_schema("canon-freeze-record.schema.json")
        freeze = {
            "artifact_type": "CANON_FREEZE_RECORD", "artifact_id": "FZ-1", "produced_by_role": "executor",
            "assignment_id": "A-1", "input_state_ref": "C-1", "status": "FROZEN", "provenance": ["C-1"],
            "related_artifacts": ["C-1"], "project_id": "P", "state_ref": "C-1", "maturity": "CANON_1_0",
            "scope": "s", "authority_ref": None, "unresolved_permitted_refs": [], "downstream_authorization": [],
        }
        self.assertFalse(schema_accepts(freeze, freeze_schema))
        freeze["authority_ref"] = "AUTH-1"
        self.assertTrue(schema_accepts(freeze, freeze_schema))

    def test_representative_canon_resolver_path_reaches_spawn_ready(self) -> None:
        value = bundle("canon", "establish_canon_foundation", "establish_canon_foundation")
        value["selected_prerequisite_actions"] = [{
            "action_id": "canon-foundation-durable-output",
            "required_capabilities": ["durable_artifact_write"],
            "evidence_path": "CANON_FOUNDATION common-envelope artifact",
        }]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["engine_id"], "canon")
        self.assertEqual(result["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertIn("durable_artifact_write", result["assignment_admissibility"]["required_capabilities"])
        self.assertEqual(result["assignment"]["execution_contract"]["proof_status"], "PROVEN")

    def test_canon_spawn_fail_closed_conditions(self) -> None:
        unavailable = bundle("canon", "establish_canon_foundation", "establish_canon_foundation")
        unavailable["decision"]["engine_status"] = "not_materialized"
        result = resolve_spawn(unavailable)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "ENGINE_NOT_MATERIALIZED"))

        no_authority = bundle("canon", "establish_canon_foundation", "establish_canon_foundation")
        del no_authority["assignment_draft_semantics"]["authority"]
        result = resolve_spawn(no_authority)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MISSING_ASSIGNMENT_SEMANTICS"))
        self.assertNotIn("assignment", result)

        malformed_profile = bundle("canon", "establish_canon_foundation", "establish_canon_foundation")
        del profile_artifact(malformed_profile)["destination_id"]
        result = resolve_spawn(malformed_profile)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "MALFORMED_CAPABILITY_PROFILE"))

        unresolved_dependency = bundle("canon", "reconcile_research_into_canon", "reconcile_research_into_canon")
        unresolved_dependency["selected_prerequisite_actions"] = [{
            "action_id": "resolve-required-upstream-canon-input",
            "required_capabilities": ["outbound_network"],
            "evidence_path": "exact mandatory upstream artifact",
        }]
        result = resolve_spawn(unresolved_dependency)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"))
        self.assertIn("outbound_network", result["missing_capabilities"])

    def test_forbidden_ownership_and_cross_engine_mutation_boundaries(self) -> None:
        manifest = (ROOT / "engines/canon/MANIFEST.yaml").read_text(encoding="utf-8")
        for boundary in (
            "owner_authority", "substantive_research", "evidence_collection", "research_sufficiency",
            "production_foundation", "software_implementation", "generic_independent_verification",
            "release_authority", "generic_orchestration", "universal_artifact_ontology", "k0_routing",
        ):
            self.assertIn(f"  - {boundary}", manifest)
        reconcile = (ROOT / "engines/canon/workflows/reconcile-research-into-canon.md").read_text(encoding="utf-8")
        production = (ROOT / "engines/canon/workflows/manage-production-canon-change.md").read_text(encoding="utf-8")
        freeze = (ROOT / "engines/canon/workflows/validate-and-freeze-canon.md").read_text(encoding="utf-8")
        self.assertIn("never accepted Canon", reconcile)
        self.assertIn("cannot self-certify Canon truth", production)
        self.assertIn("Verification cannot mutate Canon state", freeze)

    def test_non_canon_resolver_regression_paths(self) -> None:
        software = bundle()
        research = bundle("research", "execute_research_work", "machine-only-execution")
        attach_research_admission(research)
        verification = bundle("verification", "verify_completion_claim", "exact-evidence-verification")
        verification["assignment_compilation_draft"]["evidence_requirements"] = [
            action("verification-evidence", capabilities=["python_runtime"], obligation_class="local_evidence")
        ]
        for label, value in (("software", software), ("research", research), ("verification", verification)):
            with self.subTest(engine=label):
                result = resolve_spawn(value)
                self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)


if __name__ == "__main__":
    unittest.main()
