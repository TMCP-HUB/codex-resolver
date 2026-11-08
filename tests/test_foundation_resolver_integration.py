from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn
from tests.test_foundation_materialization import common
from tests.test_executability_parity import schema_accepts
from tests.test_project_topology import plan
from tools.durable_artifact_port import LocalFileDurableReferencePort
from tools.durable_readback_enforcement import evaluate_required_durable_readback
from tools.project_topology import materialize_bootstrap, verify_bootstrap
from tools.project_topology_repository import materialize_repository_shell, verify_repository_shell


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_OUTPUTS = [
    "foundation:project-seed",
    "foundation:project-outcome",
    "foundation:consequential-unknown-map",
    "foundation:topology-plan",
    "foundation:topology-bootstrap",
]


def foundation_bundle() -> dict:
    value = bundle("foundation", "form_project_foundation", "form_project_foundation")
    owner_material = {
        "artifact_type": "OWNER_SUPPLIED_PROJECT_MATERIAL",
        "artifact_id": "OWNER-MATERIAL-1",
        "provenance": ["OWNER/K0"],
    }
    value["artifacts"].append(owner_material)
    value["workflow_prerequisite_bindings"] = {
        "exact_owner_or_supplied_project_material": owner_material["artifact_id"]
    }
    return value


class FoundationResolverIntegrationTest(unittest.TestCase):
    def test_all_five_outputs_reconcile_through_the_existing_durable_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            port = LocalFileDurableReferencePort(root / "durable", "SOR-FOUNDATION-V0")
            value = foundation_bundle()
            semantics = value["assignment_draft_semantics"]
            semantics["required_durable_outputs"] = FOUNDATION_OUTPUTS
            semantics["durable_system_of_record_ref"] = "SOR-FOUNDATION-V0"
            value["selected_prerequisite_actions"] = [{"action_id": "persist-foundation",
                "required_capabilities": ["durable_artifact_write"], "evidence_path": "exact output readback"}]
            spawned = resolve_spawn(value)
            self.assertEqual(spawned["status"], "SPAWN_READY", spawned)
            outputs = [
                {**common("PROJECT_SEED", "SEED-1"), "working_summary": "Owner requests a bounded evidence project."},
                {**common("PROJECT_OUTCOME", "OUTCOME-1"), "target_outcome": "A reviewed evidence summary.",
                 "completion_condition": "Owner review", "required_deliverables": ["Evidence summary"],
                 "requires_downstream_realization": True},
                {**common("CONSEQUENTIAL_UNKNOWN_MAP", "UNKNOWNS-1"), "items": []},
                plan(),
            ]
            schemas = ("project-seed", "project-outcome", "consequential-unknown-map", "topology-plan")
            refs = []
            for output_id, payload, schema_name in zip(FOUNDATION_OUTPUTS, outputs, schemas):
                payload.update(assignment_id=spawned["assignment"]["assignment_id"],
                    input_state_ref=spawned["assignment"]["input_state_ref"], provenance=["OWNER-MATERIAL-1"])
                schema = json.loads((ROOT / "engines/foundation/schemas" / (schema_name + ".schema.json")).read_text())
                self.assertTrue(schema_accepts(payload, schema), schema_name)
                persisted = port.materialize("SOR-FOUNDATION-V0", output_id, json.dumps(payload).encode())
                refs.append({"output_id": output_id, "artifact_ref": persisted.artifact_ref})
            ref = materialize_bootstrap(port, "SOR-FOUNDATION-V0", outputs[-1])
            refs.append({"output_id": FOUNDATION_OUTPUTS[-1], "artifact_ref": ref})
            result = {"status": "COMPLETE", "durable_output_refs": refs}
            fresh_port = LocalFileDurableReferencePort(root / "durable", "SOR-FOUNDATION-V0")
            readback = evaluate_required_durable_readback(spawned["assignment"], result, fresh_port)
            self.assertEqual(readback.status, "PROVEN", readback.errors)
            incomplete = {"status": "COMPLETE", "durable_output_refs": refs[:-1]}
            self.assertEqual(evaluate_required_durable_readback(spawned["assignment"], incomplete, fresh_port).status, "INVALID")
            admission = verify_bootstrap(fresh_port, "SOR-FOUNDATION-V0", ref)
            materialize_repository_shell(root / "project", admission)
            self.assertEqual(verify_repository_shell(root / "project", admission)["status"], "COLD_START_PROVEN")
            self.assertIsNone(admission.index["current_canon_ref"])
            self.assertFalse(admission.manifest["authoritative"])

    def test_foundation_uses_generic_spawn_with_topology_outputs(self) -> None:
        value = foundation_bundle()
        value["selected_prerequisite_actions"] = [
            {
                "action_id": "foundation-durable-working-state",
                "required_capabilities": ["durable_artifact_write"],
                "evidence_path": "Foundation working state and one logical topology bootstrap via declared durable system of record",
            }
        ]
        value["assignment_draft_semantics"]["required_durable_outputs"] = list(FOUNDATION_OUTPUTS)
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-FOUNDATION-V0"

        result = resolve_spawn(value)

        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["engine_id"], "foundation")
        self.assertEqual(result["workflow_id"], "form_project_foundation")
        self.assertEqual(result["workflow_prerequisite_refs"], ["OWNER-MATERIAL-1"])
        self.assertEqual(result["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertIn("OWNER-MATERIAL-1", result["assignment_admissibility"]["related_artifacts"])
        self.assertIn("durable_artifact_write", result["assignment_admissibility"]["required_capabilities"])
        self.assertEqual(result["assignment"]["required_durable_outputs"], FOUNDATION_OUTPUTS)
        self.assertEqual(result["assignment"]["durable_system_of_record_ref"], "SOR-FOUNDATION-V0")

    def test_topology_bootstrap_cannot_be_omitted_from_generic_spawn(self) -> None:
        value = foundation_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = FOUNDATION_OUTPUTS[:3]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-FOUNDATION-V0"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "WORKFLOW_REQUIRED_OUTPUTS_MISMATCH"), result)
        self.assertNotIn("assignment", result)

    def test_foundation_prerequisite_is_real_and_cannot_be_masked_by_durable_action(self) -> None:
        value = bundle("foundation", "form_project_foundation", "form_project_foundation")
        value["selected_prerequisite_actions"] = [
            {
                "action_id": "foundation-durable-working-state",
                "required_capabilities": ["durable_artifact_write"],
                "evidence_path": "three Foundation working artifacts via declared durable system of record",
            }
        ]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "WORKFLOW_PREREQUISITE_REQUIRED"))
        self.assertEqual(result["workflow_contract_details"]["missing_requirement"], "exact_owner_or_supplied_project_material")
        self.assertNotIn("assignment", result)

    def test_foundation_has_no_special_spawn_runtime(self) -> None:
        source = (ROOT / "tools/resolver_spawn.py").read_text(encoding="utf-8")
        self.assertNotIn("resolve_foundation_spawn", source)
        self.assertNotIn("foundation_spawn", source)

    def test_generic_durable_contract_is_the_readiness_boundary(self) -> None:
        workflow = (ROOT / "engines/foundation/workflows/form-project-foundation.md").read_text(encoding="utf-8")
        protocol = (ROOT / "protocols/artifacts.md").read_text(encoding="utf-8")
        self.assertIn("required_durable_outputs", workflow)
        self.assertIn("durable_output_refs", workflow)
        self.assertIn("independent readback", workflow.lower())
        self.assertIn("reference coverage and readback are distinct gates", protocol.lower())
        self.assertIn("local/session copy", workflow.lower())


if __name__ == "__main__":
    unittest.main()
