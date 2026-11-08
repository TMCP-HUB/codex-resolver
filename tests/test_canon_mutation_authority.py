from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from engines.canon.tools.mutation_authority import (
    OWNER_MUTATION_SELECTION,
    CanonMutationAuthorityError,
    check_mutation_authority,
    guard_mutation_materialization,
)
from tests.test_executability_parity import schema_accepts
from tests.test_resource_governance_contract import schema_accepts as owner_schema_accepts

ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str) -> dict:
    return json.loads((ROOT / "engines/canon/schemas" / name).read_text(encoding="utf-8"))


def _owner_schema() -> dict:
    return json.loads((ROOT / "schemas/owner-decision-record.schema.json").read_text(encoding="utf-8"))


def _authority(
    workflow_id: str,
    target_ref: str,
    *,
    project_id: str = "PROJECT-1",
    scope: str | None = None,
    artifact_id: str = "OWNER-CANON-MUTATION-AUTH-1",
) -> dict[str, object]:
    authorized_scope = scope if scope is not None else target_ref
    return {
        "artifact_type": "OWNER_DECISION_RECORD",
        "artifact_id": artifact_id,
        "produced_by_role": "owner-interface",
        "assignment_id": "OWNER-AUTH-ASSIGN-1",
        "input_state_ref": target_ref,
        "status": "RECORDED",
        "provenance": ["OWNER/K0", target_ref],
        "related_artifacts": [target_ref],
        "question_ref": f"canon-mutation:{workflow_id}:{target_ref}",
        "options_presented": [OWNER_MUTATION_SELECTION, "DEFER"],
        "selected_option": OWNER_MUTATION_SELECTION,
        "owner_constraints": [],
        "consequences_acknowledged": ["Accepted Canon mutation is target/workflow scoped."],
        "authority_role": "OWNER_K0",
        "decision_kind": workflow_id,
        "project_id": project_id,
        "authorized_scope": authorized_scope,
    }


def _direct_authority(workflow_id: str, target_ref: str, *, scope: str | None = None) -> dict[str, object]:
    authority = _authority(workflow_id, target_ref, scope=scope)
    for field in ("question_ref", "options_presented", "selected_option"):
        del authority[field]
    authority.update(canon_input_mode="DIRECT_INSTRUCTION",
                     canon_instruction_text="Apply the specified Canon change.",
                     consequences_acknowledged=[])
    return authority


def _reconciliation(
    *,
    status: str = "ACCEPTED",
    authority_ref: str | None = "OWNER-CANON-MUTATION-AUTH-1",
    source_canon_ref: str = "CANON-SOURCE-1",
    project_id: str = "PROJECT-1",
) -> dict[str, object]:
    related = [source_canon_ref]
    if authority_ref is not None:
        related.append(authority_ref)
    return {
        "artifact_type": "CANON_RECONCILIATION_RESULT",
        "artifact_id": "CANON-RECONCILIATION-1",
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "STATE-OBS-1",
        "status": status,
        "provenance": [source_canon_ref, "RESEARCH-RELEASE-1"],
        "related_artifacts": related,
        "project_id": project_id,
        "source_canon_ref": source_canon_ref,
        "research_release_refs": ["RESEARCH-RELEASE-1"],
        "dispositions": [],
        "change_proposal_refs": [],
        "mutation_authority_ref": authority_ref,
    }


def _change(
    *,
    status: str = "ACCEPTED",
    authority_ref: str | None = "OWNER-CANON-MUTATION-AUTH-1",
    prior_canon_ref: str = "CANON-PRIOR-1",
    project_id: str = "PROJECT-1",
    scope: str = "canon/chapter-1",
) -> dict[str, object]:
    related = [prior_canon_ref]
    if authority_ref is not None:
        related.append(authority_ref)
    return {
        "artifact_type": "CANON_CHANGE_PROPOSAL",
        "artifact_id": "CANON-CHANGE-1",
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "STATE-OBS-1",
        "status": status,
        "provenance": [prior_canon_ref, "PRODUCTION-SIGNAL-1"],
        "related_artifacts": related,
        "project_id": project_id,
        "prior_canon_ref": prior_canon_ref,
        "change_id": "CHANGE-1",
        "change_class": "C_PRODUCTION_REQUIRED_CANONICAL_CHANGE",
        "statement": "Accepted bounded Canon change.",
        "scope": scope,
        "authority_required": "CANON_MUTATION_AUTHORITY",
        "authority_ref": authority_ref,
        "evidence_refs": ["PRODUCTION-SIGNAL-1"],
        "downstream_revalidation": ["affected production"],
    }


class CanonMutationAuthorityGateTest(unittest.TestCase):
    def assert_rejected(
        self,
        candidate: dict[str, object],
        workflow_id: str,
        artifacts: list[dict[str, object]],
        reason: str,
    ) -> dict[str, object]:
        result = check_mutation_authority(candidate, workflow_id, artifacts)
        self.assertEqual((result.get("status"), result.get("reason")), ("REJECTED", reason), result)
        with self.assertRaises(CanonMutationAuthorityError):
            guard_mutation_materialization(candidate, workflow_id, artifacts)
        return result

    def test_accepted_reconciliation_with_valid_governed_authority_passes(self) -> None:
        candidate = _reconciliation()
        authority = _authority("reconcile_research_into_canon", "CANON-SOURCE-1")
        self.assertTrue(schema_accepts(candidate, _schema("canon-reconciliation-result.schema.json")))
        self.assertTrue(schema_accepts(authority, _owner_schema()))
        result = guard_mutation_materialization(
            candidate, "reconcile_research_into_canon", [candidate, authority]
        )
        self.assertEqual(result["status"], "PROVEN")
        self.assertEqual(result["authority_ref"], authority["artifact_id"])
        self.assertEqual(result["target_ref"], "CANON-SOURCE-1")

    def test_accepted_change_with_valid_governed_authority_passes(self) -> None:
        candidate = _change()
        authority = _authority(
            "manage_production_canon_change",
            "CANON-PRIOR-1",
            scope="canon/chapter-1",
        )
        self.assertTrue(schema_accepts(candidate, _schema("canon-change-proposal.schema.json")))
        self.assertTrue(schema_accepts(authority, _owner_schema()))
        result = guard_mutation_materialization(
            candidate, "manage_production_canon_change", [candidate, authority]
        )
        self.assertEqual(result["status"], "PROVEN")
        self.assertEqual(result["authorized_scope"], "canon/chapter-1")

    def test_direct_instruction_can_authorize_each_supported_mutation(self) -> None:
        cases = (
            (_reconciliation(), "reconcile_research_into_canon", "CANON-SOURCE-1", None),
            (_change(), "manage_production_canon_change", "CANON-PRIOR-1", "canon/chapter-1"),
            (_change(), "reconcile_research_into_canon", "CANON-PRIOR-1", "canon/chapter-1"),
        )
        for candidate, workflow, target, scope in cases:
            with self.subTest(workflow=workflow, artifact=candidate["artifact_type"]):
                authority = _direct_authority(workflow, target, scope=scope)
                self.assertTrue(owner_schema_accepts(authority, _owner_schema()))
                result = guard_mutation_materialization(candidate, workflow, [candidate, authority])
                self.assertEqual(result["status"], "PROVEN")
                self.assertEqual(result["input_mode"], "DIRECT_INSTRUCTION")
                self.assertNotIn("selection", result)

    def test_direct_instruction_preserves_existing_authority_bindings(self) -> None:
        candidate = _change()
        base = _direct_authority("manage_production_canon_change", "CANON-PRIOR-1", scope="canon/chapter-1")
        cases = (
            ("produced_by_role", "executor", "CANON_MUTATION_AUTHORITY_PRODUCER_MISMATCH"),
            ("status", "DRAFT", "CANON_MUTATION_AUTHORITY_STATUS_MISMATCH"),
            ("authority_role", "CONTROL_DIRECTOR", "CANON_MUTATION_AUTHORITY_ROLE_MISMATCH"),
            ("provenance", [], "CANON_MUTATION_AUTHORITY_PROVENANCE_MISSING"),
            ("decision_kind", "reopen_canon", "CANON_MUTATION_AUTHORITY_WORKFLOW_MISMATCH"),
            ("input_state_ref", "CANON-OTHER", "CANON_MUTATION_AUTHORITY_TARGET_MISMATCH"),
            ("project_id", "PROJECT-OTHER", "CANON_MUTATION_AUTHORITY_PROJECT_MISMATCH"),
            ("authorized_scope", "canon/other", "CANON_MUTATION_AUTHORITY_SCOPE_MISMATCH"),
            ("related_artifacts", [], "CANON_MUTATION_AUTHORITY_TARGET_LINEAGE_MISSING"),
            ("canon_instruction_text", "  ", "CANON_MUTATION_OWNER_DECISION_MALFORMED"),
            ("selected_option", OWNER_MUTATION_SELECTION, "CANON_MUTATION_OWNER_DECISION_MALFORMED"),
            ("resource_input_mode", "DIRECT_INSTRUCTION", "CANON_MUTATION_OWNER_DECISION_MALFORMED"),
        )
        for field, value, reason in cases:
            with self.subTest(field=field):
                authority = deepcopy(base)
                authority[field] = value
                self.assert_rejected(candidate, "manage_production_canon_change", [candidate, authority], reason)

        for field, value in (("canon_instruction_text", "  "), ("selected_option", OWNER_MUTATION_SELECTION),
                             ("resource_input_mode", "DIRECT_INSTRUCTION"), ("decision_kind", "unrelated")):
            authority = deepcopy(base)
            authority[field] = value
            self.assertFalse(owner_schema_accepts(authority, _owner_schema()))

    def test_missing_authority_ref_fails_closed(self) -> None:
        candidate = _reconciliation(authority_ref=None)
        self.assertFalse(schema_accepts(candidate, _schema("canon-reconciliation-result.schema.json")))
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate],
            "CANON_MUTATION_AUTHORITY_REF_REQUIRED",
        )

    def test_unresolved_authority_ref_fails_closed(self) -> None:
        candidate = _reconciliation(authority_ref="UNKNOWN")
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate],
            "CANON_MUTATION_AUTHORITY_UNRESOLVED",
        )

    def test_ordinary_provenance_artifact_cannot_act_as_authority(self) -> None:
        candidate = _reconciliation(authority_ref="FINDING-1")
        fake = {
            "artifact_type": "RESEARCH_FINDING",
            "artifact_id": "FINDING-1",
            "provenance": ["SOURCE-1"],
        }
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate, fake],
            "CANON_MUTATION_AUTHORITY_TYPE_MISMATCH",
        )

    def test_unrelated_owner_decision_fails_closed(self) -> None:
        candidate = _reconciliation()
        authority = _authority("reconcile_research_into_canon", "CANON-SOURCE-1")
        authority["selected_option"] = "AUTHORIZE_REOPEN_CANON"
        authority["options_presented"] = ["AUTHORIZE_REOPEN_CANON", "DEFER"]
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate, authority],
            "CANON_MUTATION_AUTHORITY_SELECTION_MISMATCH",
        )

    def test_wrong_workflow_authority_fails_closed(self) -> None:
        candidate = _reconciliation()
        authority = _authority("reopen_canon", "CANON-SOURCE-1")
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate, authority],
            "CANON_MUTATION_AUTHORITY_WORKFLOW_MISMATCH",
        )

    def test_wrong_canon_target_fails_closed(self) -> None:
        candidate = _reconciliation()
        authority = _authority("reconcile_research_into_canon", "CANON-OTHER")
        authority["artifact_id"] = "OWNER-CANON-MUTATION-AUTH-1"
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate, authority],
            "CANON_MUTATION_AUTHORITY_TARGET_MISMATCH",
        )

    def test_wrong_project_and_scope_fail_closed(self) -> None:
        reconciliation = _reconciliation()
        wrong_project = _authority(
            "reconcile_research_into_canon", "CANON-SOURCE-1", project_id="PROJECT-OTHER"
        )
        self.assert_rejected(
            reconciliation,
            "reconcile_research_into_canon",
            [reconciliation, wrong_project],
            "CANON_MUTATION_AUTHORITY_PROJECT_MISMATCH",
        )

        change = _change()
        wrong_scope = _authority(
            "manage_production_canon_change", "CANON-PRIOR-1", scope="canon/other"
        )
        self.assert_rejected(
            change,
            "manage_production_canon_change",
            [change, wrong_scope],
            "CANON_MUTATION_AUTHORITY_SCOPE_MISMATCH",
        )

    def test_malformed_owner_authority_fails_closed(self) -> None:
        candidate = _reconciliation()
        base = _authority("reconcile_research_into_canon", "CANON-SOURCE-1")
        cases = (
            ("status", "AUTHORIZED", "CANON_MUTATION_AUTHORITY_STATUS_MISMATCH"),
            ("produced_by_role", "executor", "CANON_MUTATION_AUTHORITY_PRODUCER_MISMATCH"),
            ("authority_role", "CONTROL_DIRECTOR", "CANON_MUTATION_AUTHORITY_ROLE_MISMATCH"),
            ("provenance", [], "CANON_MUTATION_AUTHORITY_PROVENANCE_MISSING"),
        )
        for field, value, reason in cases:
            with self.subTest(field=field):
                authority = deepcopy(base)
                authority[field] = value
                self.assert_rejected(
                    candidate,
                    "reconcile_research_into_canon",
                    [candidate, authority],
                    reason,
                )

    def test_proposal_only_reconciliation_requires_no_mutation_authority(self) -> None:
        candidate = _reconciliation(status="PROPOSED", authority_ref=None)
        self.assertTrue(schema_accepts(candidate, _schema("canon-reconciliation-result.schema.json")))
        result = guard_mutation_materialization(
            candidate, "reconcile_research_into_canon", [candidate]
        )
        self.assertEqual((result["status"], result["authority_required"]), ("NOT_REQUIRED", False))

    def test_proposal_only_change_requires_no_mutation_authority(self) -> None:
        candidate = _change(status="PROPOSED", authority_ref=None)
        self.assertTrue(schema_accepts(candidate, _schema("canon-change-proposal.schema.json")))
        result = guard_mutation_materialization(
            candidate, "manage_production_canon_change", [candidate]
        )
        self.assertEqual((result["status"], result["authority_required"]), ("NOT_REQUIRED", False))

    def test_authority_lineage_is_mandatory_for_accepted_output(self) -> None:
        candidate = _reconciliation()
        candidate["related_artifacts"] = ["CANON-SOURCE-1"]
        authority = _authority("reconcile_research_into_canon", "CANON-SOURCE-1")
        self.assert_rejected(
            candidate,
            "reconcile_research_into_canon",
            [candidate, authority],
            "CANON_MUTATION_AUTHORITY_LINEAGE_MISSING",
        )

    def test_workflow_and_skill_contracts_make_output_gate_mandatory(self) -> None:
        paths = (
            "engines/canon/workflows/reconcile-research-into-canon.md",
            "engines/canon/workflows/manage-production-canon-change.md",
            "engines/canon/skills/reconcile-research-into-canon/SKILL.md",
            "engines/canon/skills/classify-canon-change/SKILL.md",
        )
        for rel in paths:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("guard_mutation_materialization", text, rel)
            self.assertIn("engines/canon/tools/mutation_authority.py", text, rel)
        manifest = (ROOT / "engines/canon/MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertIn("accepted_mutation_gate: engines/canon/tools/mutation_authority.py", manifest)
        authority_doc = (ROOT / "engines/canon/docs/CANON_AUTHORITY.md").read_text(encoding="utf-8")
        self.assertEqual(authority_doc.count("`AUTHORIZE_CANON_MUTATION`"), 1)


if __name__ == "__main__":
    unittest.main()
