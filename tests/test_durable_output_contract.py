from __future__ import annotations

import json
from pathlib import Path
import unittest

from tests.test_executability_parity import schema_accepts
from tests.test_resolver_spawn import bundle as spawn_bundle
from tests.test_resolver_transition import artifact, transition_bundle
from tools.durable_output_contract import (
    validate_assignment_durable_outputs,
    validate_executor_durable_output_refs,
)
from tools.resolver_spawn import resolve_spawn
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def _declare(value: dict, *output_ids: str) -> tuple[dict, dict]:
    assignment = artifact(value, value["refs"]["assignment_ref"])
    result = artifact(value, value["refs"]["executor_result_ref"])
    assignment["required_durable_outputs"] = list(output_ids)
    if output_ids:
        assignment["durable_system_of_record_ref"] = "SOR-PRIMARY"
    return assignment, result


def _bind(result: dict, *pairs: tuple[str, str]) -> None:
    result["durable_output_refs"] = [
        {"output_id": output_id, "artifact_ref": artifact_ref}
        for output_id, artifact_ref in pairs
    ]


class DurableOutputContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assignment_schema = json.loads((ROOT / "schemas/assignment.schema.json").read_text())
        cls.result_schema = json.loads((ROOT / "schemas/executor-result.schema.json").read_text())

    def test_spawn_carries_required_durable_output_declaration(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["report"]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-PRIMARY"
        spawned = resolve_spawn(value)
        self.assertEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["assignment"]["required_durable_outputs"], ["report"])
        self.assertEqual(spawned["assignment"]["durable_system_of_record_ref"], "SOR-PRIMARY")

    def test_spawn_rejects_required_durable_output_without_system_of_record(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["report"]
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(any("durable_system_of_record_ref" in error for error in spawned["errors"]), spawned)

    def test_spawn_rejects_duplicate_required_durable_output_ids(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["report", "report"]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-PRIMARY"
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(any("duplicate required durable output id" in error for error in spawned["errors"]), spawned)

    def test_spawn_rejects_blank_required_durable_output_id(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["   "]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-PRIMARY"
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(any("must be a non-blank string" in error for error in spawned["errors"]), spawned)

    def test_spawn_rejects_unencodable_required_durable_output_id(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["\ud800"]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-PRIMARY"
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(
            any("required_durable_outputs[0] must be UTF-8 encodable" in error for error in spawned["errors"]),
            spawned,
        )

    def test_spawn_rejects_unencodable_durable_system_of_record_ref(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["report"]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "\ud800"
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(
            any("durable_system_of_record_ref must be UTF-8 encodable" in error for error in spawned["errors"]),
            spawned,
        )

    def test_spawn_accepts_ordinary_utf8_durable_identities(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = ["отчёт-✓"]
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-основной-✓"
        spawned = resolve_spawn(value)
        self.assertEqual(spawned["status"], "SPAWN_READY", spawned)
        self.assertEqual(spawned["assignment"]["required_durable_outputs"], ["отчёт-✓"])
        self.assertEqual(spawned["assignment"]["durable_system_of_record_ref"], "SOR-основной-✓")

    def test_spawn_rejects_non_list_required_durable_outputs(self) -> None:
        value = spawn_bundle()
        value["assignment_draft_semantics"]["required_durable_outputs"] = "report"
        value["assignment_draft_semantics"]["durable_system_of_record_ref"] = "SOR-PRIMARY"
        spawned = resolve_spawn(value)
        self.assertNotEqual(spawned["status"], "SPAWN_READY")
        self.assertEqual(spawned["reason"], "FINAL_ASSIGNMENT_PROOF_FAILED")
        self.assertTrue(any("required_durable_outputs must be a list" in error for error in spawned["errors"]), spawned)

    def test_legacy_assignment_without_durable_outputs_preserves_complete(self) -> None:
        value = transition_bundle()
        assignment = artifact(value, value["refs"]["assignment_ref"])
        result = artifact(value, value["refs"]["executor_result_ref"])
        self.assertEqual(validate_assignment_durable_outputs(assignment), [])
        self.assertEqual(validate_executor_durable_output_refs(result, assignment), [])
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_one_required_output_with_exact_binding_is_structurally_valid_but_not_readback_proven(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "deliverable")
        _bind(result, ("deliverable", "ARTIFACT-1"))
        self.assertEqual(validate_executor_durable_output_refs(result, assignment), [])
        self.assertTrue(schema_accepts(assignment, self.assignment_schema))
        self.assertTrue(schema_accepts(result, self.result_schema))
        resolved = resolve_transition(value)
        self.assertEqual((resolved["control_state"], resolved["reason"]), ("WAIT", "DURABLE_READBACK_NOT_PROVEN"))

    def test_complete_without_binding_fails_closed(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "deliverable")
        errors = validate_executor_durable_output_refs(result, assignment)
        self.assertTrue(any("missing durable output refs" in error for error in errors), errors)
        resolved = resolve_transition(value)
        self.assertEqual((resolved["control_state"], resolved["reason"]), ("ESCALATE", "MALFORMED_EXECUTOR_RESULT"))

    def test_complete_requires_every_declared_output(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report", "manifest")
        _bind(result, ("report", "ARTIFACT-REPORT"))
        errors = validate_executor_durable_output_refs(result, assignment)
        self.assertTrue(any("manifest" in error for error in errors), errors)
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_EXECUTOR_RESULT")

    def test_blank_artifact_ref_cannot_satisfy_requirement(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("report", "   "))
        errors = validate_executor_durable_output_refs(result, assignment)
        self.assertTrue(any("artifact_ref must be a non-blank string" in error for error in errors), errors)
        self.assertFalse(schema_accepts(result, self.result_schema))

    def test_wrong_output_identity_cannot_cover_declared_requirement(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("other", "ARTIFACT-OTHER"))
        errors = validate_executor_durable_output_refs(result, assignment)
        self.assertTrue(any("not declared by the assignment" in error for error in errors), errors)
        self.assertTrue(any("report" in error and "missing durable output refs" in error for error in errors), errors)

    def test_duplicate_requirement_and_binding_identity_fail_closed(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report", "report")
        self.assertTrue(validate_assignment_durable_outputs(assignment))
        self.assertFalse(schema_accepts(assignment, self.assignment_schema))

        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("report", "ARTIFACT-1"), ("report", "ARTIFACT-2"))
        errors = validate_executor_durable_output_refs(result, assignment)
        self.assertTrue(any("duplicate durable output binding id" in error for error in errors), errors)
        self.assertTrue(schema_accepts(result, self.result_schema))
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_EXECUTOR_RESULT")

    def test_partial_may_report_only_materialized_subset(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report", "manifest")
        result["status"] = "PARTIAL"
        _bind(result, ("report", "ARTIFACT-REPORT"))
        self.assertEqual(validate_executor_durable_output_refs(result, assignment), [])
        resolved = resolve_transition(value)
        self.assertEqual((resolved["control_state"], resolved["reason"]), ("WAIT", "AUTHORIZED_REQUIREMENT_PENDING"))

    def test_binding_shape_and_blank_ids_match_schema_structure(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        self.assertTrue(schema_accepts(assignment, self.assignment_schema))

        assignment["required_durable_outputs"] = ["   "]
        self.assertFalse(schema_accepts(assignment, self.assignment_schema))
        self.assertTrue(validate_assignment_durable_outputs(assignment))

        value = transition_bundle()
        assignment, result = _declare(value, "report")
        result["durable_output_refs"] = [{"output_id": "report", "artifact_ref": "ARTIFACT-1", "path": "/tmp/x"}]
        self.assertFalse(schema_accepts(result, self.result_schema))
        self.assertTrue(validate_executor_durable_output_refs(result, assignment))

    def test_reference_presence_does_not_claim_readback(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("report", "opaque:durable-ref"))
        self.assertEqual(validate_executor_durable_output_refs(result, assignment), [])
        self.assertNotIn("readback", result)
        self.assertNotIn("freshness", result)


if __name__ == "__main__":
    unittest.main()
