from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.test_resolver_spawn import bundle, attach_research_admission
from tests.test_workflow_contract import freeze_bundle, _freeze_authority
from tests.test_project_topology import plan
from tools.durable_artifact_port import LocalFileDurableReferencePort
from tools.project_topology import materialize_bootstrap, verify_bootstrap
from tools.project_topology_repository import materialize_repository_shell, materialize_repository_payload
from tools.resolver_spawn import resolve_spawn

from tests.test_resolver_spawn import _attach_default_canon_prerequisites


class TopologyAssignmentAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.port = LocalFileDurableReferencePort(self.root / "durable", "SOR-1")
        self.ref = materialize_bootstrap(self.port, "SOR-1", plan())
        self.admission = verify_bootstrap(self.port, "SOR-1", self.ref)
        self.project = self.root / "project"
        materialize_repository_shell(self.project, self.admission)

    def governed(self):
        value = bundle()
        state = next(item for item in value["artifacts"] if item.get("artifact_type") == "STATE_OBSERVATION")
        state["project_topology_context"] = {
            "project_id": "project-1",
            "current_topology_ref": self.ref,
            "system_of_record_ref": "SOR-1",
            "storage_mode": "DRIVE_THEN_REPO",
        }
        value["assignment_draft_semantics"]["project_payload_intents"] = [
            {"artifact_class": "FINDING", "artifact_id": "F-9", "scope": {"workstream_id": "R-017"}}
        ]
        value["selected_prerequisite_actions"] = [{
            "action_id": "persist-project-payload",
            "required_capabilities": ["durable_artifact_write"],
            "evidence_path": "provider-backed project artifact and index readback",
        }]
        return value

    def test_governed_payload_requires_verified_topology_and_derives_address(self):
        value = self.governed()
        outcome = resolve_spawn(value, topology_port=self.port, topology_root=self.project)
        self.assertEqual(outcome["status"], "SPAWN_READY", outcome)
        payload = outcome["assignment"]["project_payload_bindings"][0]
        self.assertEqual(payload["canonical_address"], "research/findings/R-017/F-9")
        self.assertEqual(payload["topology_ref"], self.ref)

    def test_engine_executor_can_write_using_only_derived_assignment_binding(self):
        for engine, capability, workflow in (
            ("production/software", "implement_software_change", "implementation"),
            ("research", "execute_research_work", "machine-only-execution"),
            ("canon", "register_canon_fact", "establish_canon_foundation"),
        ):
            with self.subTest(engine=engine):
                value = bundle(engine, capability, workflow)
                governed = self.governed()
                value["assignment_draft_semantics"].update(governed["assignment_draft_semantics"])
                value["selected_prerequisite_actions"] = governed["selected_prerequisite_actions"]
                state = next(item for item in value["artifacts"] if item.get("artifact_type") == "STATE_OBSERVATION")
                state["project_topology_context"] = next(item for item in governed["artifacts"]
                    if item.get("artifact_type") == "STATE_OBSERVATION")["project_topology_context"]
                value["assignment_draft_semantics"]["project_payload_intents"][0]["artifact_id"] = engine.replace("/", "-")
                if engine == "research":
                    attach_research_admission(value)
                spawned = resolve_spawn(value, topology_port=self.port, topology_root=self.project)
                self.assertEqual(spawned["status"], "SPAWN_READY", spawned.get("reason"))
                binding = spawned["assignment"]["project_payload_bindings"][0]
                self.assertEqual(binding["project_id"], "project-1")
                written = materialize_repository_payload(self.project, self.port,
                    binding["system_of_record_ref"], binding["topology_ref"], binding["artifact_class"],
                    binding["artifact_id"], b"working project payload", scope=binding["scope"])
                self.assertEqual(written["physical_readback"], "COLD_START_PROVEN")
                self.assertEqual(self.port.readback("SOR-1", written["artifact_ref"]).payload, b"working project payload")

    def test_absent_port_or_physical_root_is_not_admitted(self):
        value = self.governed()
        self.assertEqual(resolve_spawn(value)["reason"], "CURRENT_TOPOLOGY_READBACK_REQUIRED")
        self.assertEqual(resolve_spawn(value, topology_port=self.port)["reason"],
                         "TOPOLOGY_PHYSICAL_READBACK_REQUIRED")

    def test_undeclared_payload_class_is_rejected_before_spawn(self):
        value = self.governed()
        value["assignment_draft_semantics"]["project_payload_intents"][0]["artifact_class"] = "UNADMITTED"
        result = resolve_spawn(value, topology_port=self.port, topology_root=self.project)
        self.assertEqual(result["reason"], "TOPOLOGY_CHANGE_REQUIRED")
        self.assertNotIn("assignment", result)

    def test_no_intent_or_durable_action_stops_protected_write(self):
        value = self.governed()
        value["assignment_draft_semantics"].pop("project_payload_intents")
        self.assertEqual(resolve_spawn(value, topology_port=self.port, topology_root=self.project)["reason"],
                         "PROJECT_PAYLOAD_INTENTS_REQUIRED")
        value = self.governed()
        value["selected_prerequisite_actions"] = []
        self.assertEqual(resolve_spawn(value, topology_port=self.port, topology_root=self.project)["reason"],
                         "TOPOLOGY_PAYLOAD_DURABLE_ACTION_REQUIRED")

    def test_stale_current_carrier_cannot_admit_write(self):
        value = self.governed()
        (self.project / "TOPOLOGY_MANIFEST.json").write_text('{"current_topology_ref":"superseded"}')
        result = resolve_spawn(value, topology_port=self.port, topology_root=self.project)
        self.assertEqual(result["reason"], "TOPOLOGY_CURRENT_REF_STALE")

    def test_legacy_without_formation_state_keeps_previous_contract(self):
        value = bundle()
        self.assertEqual(resolve_spawn(value)["status"], "SPAWN_READY")

    def test_canon_registration_routes_cannot_omit_payload_intents(self):
        # These skills mandate durable Canon records; aliases must not evade
        # the selected workflow's existing topology admission requirement.
        for capability in ("register_canon_fact", "register_canon_assumption", "register_unknown",
                           "register_ambiguity", "register_contradiction", "classify_canon_change"):
            with self.subTest(capability=capability):
                workflow = "manage_production_canon_change" if capability == "classify_canon_change" else "establish_canon_foundation"
                value = bundle("canon", capability, workflow)
                state = next(item for item in value["artifacts"] if item.get("artifact_type") == "STATE_OBSERVATION")
                state["project_topology_context"] = {
                    "project_id": "project-1", "current_topology_ref": self.ref,
                    "system_of_record_ref": "SOR-1", "storage_mode": "DRIVE_THEN_REPO"}
                result = resolve_spawn(value, topology_port=self.port, topology_root=self.project)
                self.assertEqual(result.get("reason"), "PROJECT_PAYLOAD_INTENTS_REQUIRED")
                self.assertNotIn("assignment", result)

    def test_freeze_write_requires_topology_but_validation_stays_read_only(self):
        context = next(item for item in self.governed()["artifacts"]
            if item.get("artifact_type") == "STATE_OBSERVATION")["project_topology_context"]
        freeze = freeze_bundle(authority=_freeze_authority())
        validate = bundle("canon", "validate_canon", "validate_canon")
        for value in (freeze, validate):
            next(item for item in value["artifacts"] if item.get("artifact_type") == "STATE_OBSERVATION")["project_topology_context"] = context
        self.assertEqual(resolve_spawn(freeze, topology_port=self.port, topology_root=self.project)["reason"],
                         "PROJECT_PAYLOAD_INTENTS_REQUIRED")
        self.assertEqual(resolve_spawn(validate)["status"], "SPAWN_READY")


if __name__ == "__main__":
    unittest.main()
