from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tests.test_resolver_spawn import bundle
from tests.test_resource_governance_contract import schema_accepts
from tools.resolver_spawn import resolve_spawn
from tools.workflow_contract import resolve_workflow_contract


def _candidate(artifact_id: str = "CANON-CANDIDATE-1") -> dict[str, object]:
    return {
        "artifact_type": "CANON_STATE",
        "artifact_id": artifact_id,
        "provenance": ["OWNER/K0"],
    }


def _freeze_authority(candidate_id: str = "CANON-CANDIDATE-1", *, artifact_id: str = "FREEZE-AUTH-1") -> dict[str, object]:
    return {
        "artifact_type": "FREEZE_AUTHORITY",
        "artifact_id": artifact_id,
        "produced_by_role": "owner-interface",
        "status": "AUTHORIZED",
        "provenance": ["OWNER-DECISION-1"],
        "authority_role": "OWNER_K0",
        "target_ref": candidate_id,
        "candidate_identity": candidate_id,
        "workflow_id": "validate_and_freeze_canon",
        "authorizes_exact_candidate_freeze": True,
    }


def freeze_bundle(*, authority: dict[str, object] | None = None) -> dict:
    value = bundle("canon", "freeze_canon", "validate_and_freeze_canon")
    candidate = _candidate()
    value["artifacts"].append(candidate)
    bindings: dict[str, object] = {"exact_canon_candidate_ref": candidate["artifact_id"]}
    if authority is not None:
        value["artifacts"].append(authority)
        bindings["explicit_freeze_authority"] = authority["artifact_id"]
    value["workflow_prerequisite_bindings"] = bindings
    return value


class WorkflowContractUnitTest(unittest.TestCase):
    def test_engine_neutral_required_input_omission_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "engines/demo/MANIFEST.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "engine_id: demo\n"
                "status: available\n"
                "workflow_contracts:\n"
                "  execute:\n"
                "    upstream_requirements:\n"
                "      - {\"requirement_id\":\"required_input\",\"proof_class\":\"ARTIFACT_REF\"}\n"
                "capabilities:\n"
                "  do_work: execute\n",
                encoding="utf-8",
            )
            decision = {
                "engine_id": "demo", "engine_status": "available",
                "semantic_capability": "do_work", "workflow_id": "execute",
            }
            result = resolve_workflow_contract(decision, {}, {}.get, root=root)
            self.assertEqual((result["status"], result["reason"]), ("ERROR", "WORKFLOW_PREREQUISITE_REQUIRED"))
            self.assertEqual(result["missing_requirement"], "required_input")

    def test_engine_neutral_capability_workflow_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "engines/demo/MANIFEST.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "engine_id: demo\n"
                "status: available\n"
                "workflow_contracts:\n"
                "  execute:\n"
                "    upstream_requirements: []\n"
                "  other:\n"
                "    upstream_requirements: []\n"
                "capabilities:\n"
                "  do_work: execute\n",
                encoding="utf-8",
            )
            decision = {
                "engine_id": "demo", "engine_status": "available",
                "semantic_capability": "do_work", "workflow_id": "other",
            }
            result = resolve_workflow_contract(decision, {}, {}.get, root=root)
            self.assertEqual((result["status"], result["reason"]), ("ERROR", "CAPABILITY_WORKFLOW_IDENTITY_MISMATCH"))


class CanonWorkflowAdmissionIntegrationTest(unittest.TestCase):
    def assert_fail_closed(self, value: dict, reason: str | None = None) -> dict:
        result = resolve_spawn(value)
        self.assertNotEqual(result.get("status"), "SPAWN_READY", result)
        self.assertNotIn("assignment", result)
        if reason is not None:
            self.assertEqual(result.get("reason"), reason, result)
        return result

    def test_validate_with_exact_candidate_reaches_spawn_ready_without_freeze_authority(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["workflow_contract_source"], "engines/canon/MANIFEST.yaml")
        self.assertEqual(result["workflow_prerequisite_refs"], ["CANON-CANDIDATE-1"])
        self.assertNotIn("FREEZE-AUTH-1", result["assignment_admissibility"]["related_artifacts"])

    def test_validate_without_exact_candidate_fails_closed(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["workflow_prerequisite_bindings"] = {}
        self.assert_fail_closed(value, "WORKFLOW_PREREQUISITE_REQUIRED")

    def test_freeze_with_valid_scoped_authority_reaches_spawn_ready_and_binds_proof_refs(self) -> None:
        value = freeze_bundle(authority=_freeze_authority())
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        for artifact_id in ("CANON-CANDIDATE-1", "FREEZE-AUTH-1"):
            self.assertIn(artifact_id, result["workflow_prerequisite_refs"])
            self.assertIn(artifact_id, result["assignment_admissibility"]["related_artifacts"])
            self.assertIn(artifact_id, result["assignment"]["related_artifacts"])
        self.assertEqual(result["assignment"]["execution_contract"]["proof_status"], "PROVEN")

    def test_freeze_without_authority_fails_closed(self) -> None:
        self.assert_fail_closed(freeze_bundle(), "WORKFLOW_PREREQUISITE_REQUIRED")

    def test_freeze_wrong_or_fake_authority_fails_closed(self) -> None:
        wrong = _freeze_authority()
        wrong["target_ref"] = "OTHER-CANDIDATE"
        self.assert_fail_closed(freeze_bundle(authority=wrong), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

        fake = _freeze_authority()
        fake["artifact_type"] = "OWNER_DECISION_RECORD"
        self.assert_fail_closed(freeze_bundle(authority=fake), "WORKFLOW_AUTHORITY_TYPE_MISMATCH")

    def test_selected_prerequisite_actions_cannot_mask_missing_workflow_requirement(self) -> None:
        value = freeze_bundle()
        value["selected_prerequisite_actions"] = [{
            "action_id": "pretend-freeze-authority",
            "required_capabilities": ["shell"],
            "evidence_path": "caller says freeze authority exists",
        }]
        result = self.assert_fail_closed(value, "WORKFLOW_PREREQUISITE_REQUIRED")
        self.assertEqual(result["workflow_contract_details"]["missing_requirement"], "explicit_freeze_authority")

    def test_capability_workflow_identity_mix_fails_closed(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["decision"]["workflow_id"] = "validate_and_freeze_canon"
        self.assert_fail_closed(value, "CAPABILITY_WORKFLOW_IDENTITY_MISMATCH")

    def test_missing_destination_capability_preserves_assignment_not_admissible(self) -> None:
        value = bundle("canon", "validate_canon", "validate_canon")
        value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"), result)
        self.assertEqual(result["missing_capabilities"], ["database_access"])
        self.assertNotIn("assignment", result)



def _owner_decision_authority(
    workflow_id: str,
    target_ref: str,
    selected_option: str,
    *,
    artifact_id: str = "OWNER-CANON-AUTH-1",
) -> dict[str, object]:
    return {
        "artifact_type": "OWNER_DECISION_RECORD",
        "artifact_id": artifact_id,
        "produced_by_role": "owner-interface",
        "assignment_id": "OWNER-ASSIGN-1",
        "input_state_ref": target_ref,
        "status": "RECORDED",
        "provenance": ["OWNER/K0", target_ref],
        "related_artifacts": [target_ref],
        "question_ref": f"{workflow_id}:{target_ref}",
        "options_presented": [selected_option, "DEFER"],
        "selected_option": selected_option,
        "owner_constraints": [],
        "consequences_acknowledged": ["Canon authority is scoped and non-transitive."],
        "authority_role": "OWNER_K0",
        "decision_kind": workflow_id,
        "authorized_scope": target_ref,
    }


def _final_bundle(authority: dict[str, object] | None = None) -> dict:
    value = bundle("canon", "final_canon_reconciliation", "final_canon_reconciliation")
    canon = {"artifact_type": "CANON_STATE", "artifact_id": "CANON-1X-1", "provenance": ["OWNER/K0"]}
    record = {"artifact_type": "PRODUCTION_CHANGE", "artifact_id": "PROD-CHANGE-1", "provenance": ["PRODUCTION-1"]}
    value["artifacts"].extend([canon, record])
    bindings: dict[str, object] = {
        "exact_canon_1x_ref": canon["artifact_id"],
        "exact_production_change_records": [record["artifact_id"]],
    }
    if authority is not None:
        value["artifacts"].append(authority)
        bindings["explicit_final_canon_authority"] = authority["artifact_id"]
    value["workflow_prerequisite_bindings"] = bindings
    return value


def _reopen_bundle(authority: dict[str, object] | None = None) -> dict:
    value = bundle("canon", "reopen_canon", "reopen_canon")
    canon = {"artifact_type": "CANON_STATE", "artifact_id": "CANON-FROZEN-1", "provenance": ["FREEZE-1"]}
    value["artifacts"].append(canon)
    bindings: dict[str, object] = {"exact_frozen_canon_ref": canon["artifact_id"]}
    if authority is not None:
        value["artifacts"].append(authority)
        bindings["explicit_reopen_authority"] = authority["artifact_id"]
    value["workflow_prerequisite_bindings"] = bindings
    return value


class CanonAuthoritySemanticsR3Test(unittest.TestCase):
    def assert_fail_closed(self, value: dict, reason: str) -> dict:
        result = resolve_spawn(value)
        self.assertNotEqual(result.get("status"), "SPAWN_READY", result)
        self.assertNotIn("assignment", result)
        self.assertEqual(result.get("reason"), reason, result)
        return result

    def test_final_authority_is_governed_and_target_workflow_bound(self) -> None:
        authority = _owner_decision_authority(
            "final_canon_reconciliation", "CANON-1X-1", "AUTHORIZE_FINAL_CANON_RECONCILIATION"
        )
        result = resolve_spawn(_final_bundle(authority))
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertIn(authority["artifact_id"], result["workflow_prerequisite_refs"])

        wrong_target = dict(authority)
        wrong_target["artifact_id"] = "OWNER-FINAL-WRONG-TARGET"
        wrong_target["authorized_scope"] = "CANON-OTHER"
        self.assert_fail_closed(_final_bundle(wrong_target), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

        wrong_workflow = dict(authority)
        wrong_workflow["artifact_id"] = "OWNER-FINAL-WRONG-WORKFLOW"
        wrong_workflow["decision_kind"] = "reopen_canon"
        self.assert_fail_closed(_final_bundle(wrong_workflow), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

    def test_final_missing_or_fake_authority_fails_closed(self) -> None:
        self.assert_fail_closed(_final_bundle(), "WORKFLOW_PREREQUISITE_REQUIRED")
        fake = {"artifact_type": "RESEARCH_FINDING", "artifact_id": "FAKE-FINAL-AUTH", "provenance": ["OWNER/K0"]}
        self.assert_fail_closed(_final_bundle(fake), "WORKFLOW_AUTHORITY_TYPE_MISMATCH")

    def test_reopen_authority_is_governed_and_target_workflow_bound(self) -> None:
        authority = _owner_decision_authority(
            "reopen_canon", "CANON-FROZEN-1", "AUTHORIZE_REOPEN_CANON"
        )
        result = resolve_spawn(_reopen_bundle(authority))
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertIn(authority["artifact_id"], result["workflow_prerequisite_refs"])

        wrong_target = dict(authority)
        wrong_target["artifact_id"] = "OWNER-REOPEN-WRONG-TARGET"
        wrong_target["authorized_scope"] = "CANON-OTHER"
        self.assert_fail_closed(_reopen_bundle(wrong_target), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

        wrong_workflow = dict(authority)
        wrong_workflow["artifact_id"] = "OWNER-REOPEN-WRONG-WORKFLOW"
        wrong_workflow["decision_kind"] = "final_canon_reconciliation"
        self.assert_fail_closed(_reopen_bundle(wrong_workflow), "WORKFLOW_AUTHORITY_SCOPE_MISMATCH")

    def test_direct_instructions_admit_final_and_reopen_with_existing_bindings(self) -> None:
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/owner-decision-record.schema.json").read_text())
        cases = (
            ("final_canon_reconciliation", "CANON-1X-1", "AUTHORIZE_FINAL_CANON_RECONCILIATION", _final_bundle),
            ("reopen_canon", "CANON-FROZEN-1", "AUTHORIZE_REOPEN_CANON", _reopen_bundle),
        )
        for workflow, target, selection, build in cases:
            with self.subTest(workflow=workflow):
                authority = _owner_decision_authority(workflow, target, selection)
                for field in ("question_ref", "options_presented", "selected_option"):
                    del authority[field]
                authority.update(canon_input_mode="DIRECT_INSTRUCTION",
                                 canon_instruction_text="Proceed with this Canon transition.",
                                 consequences_acknowledged=[])
                self.assertTrue(schema_accepts(authority, schema))
                self.assertNotIn("project_id", authority)  # The existing contract does not require it here.
                self.assertEqual(resolve_spawn(build(authority))["status"], "SPAWN_READY")

                for field, value, reason in (
                    ("authorized_scope", "CANON-OTHER", "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"),
                    ("decision_kind", "manage_production_canon_change", "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"),
                    ("produced_by_role", "executor", "WORKFLOW_AUTHORITY_PRODUCER_MISMATCH"),
                    ("provenance", [], "WORKFLOW_AUTHORITY_PROVENANCE_MISSING"),
                    ("canon_instruction_text", "  ", "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"),
                    ("canon_input_mode", "OTHER", "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"),
                    ("selected_option", selection, "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"),
                ):
                    with self.subTest(workflow=workflow, field=field):
                        invalid = deepcopy(authority)
                        invalid[field] = value
                        self.assert_fail_closed(build(invalid), reason)

    def test_reopen_missing_or_fake_authority_fails_closed(self) -> None:
        self.assert_fail_closed(_reopen_bundle(), "WORKFLOW_PREREQUISITE_REQUIRED")
        fake = {"artifact_type": "PRODUCTION_CHANGE", "artifact_id": "FAKE-REOPEN-AUTH", "provenance": ["PRODUCTION-1"]}
        self.assert_fail_closed(_reopen_bundle(fake), "WORKFLOW_AUTHORITY_TYPE_MISMATCH")

    def test_reconciliation_proposal_only_does_not_require_mutation_authority(self) -> None:
        value = bundle("canon", "reconcile_research_into_canon", "reconcile_research_into_canon")
        self.assertNotIn("canon_mutation_authority_for_any_accepted_change", value["workflow_prerequisite_bindings"])
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)

    def test_production_classification_does_not_require_mutation_authority(self) -> None:
        value = bundle("canon", "classify_canon_change", "manage_production_canon_change")
        self.assertNotIn("canon_mutation_authority_for_any_accepted_change", value["workflow_prerequisite_bindings"])
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)

    def test_arbitrary_mutation_authority_binding_cannot_become_entry_authority(self) -> None:
        value = bundle("canon", "reconcile_research_into_canon", "reconcile_research_into_canon")
        fake = {"artifact_type": "OWNER_DECISION_RECORD", "artifact_id": "FAKE-MUTATION-AUTH", "provenance": ["OWNER/K0"]}
        value["artifacts"].append(fake)
        value["workflow_prerequisite_bindings"]["canon_mutation_authority_for_any_accepted_change"] = fake["artifact_id"]
        self.assert_fail_closed(value, "WORKFLOW_PREREQUISITE_BINDING_MISMATCH")


if __name__ == "__main__":
    unittest.main()
