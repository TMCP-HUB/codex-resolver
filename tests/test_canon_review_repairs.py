from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_executability_parity import schema_accepts
from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn

ROOT = Path(__file__).resolve().parents[1]
RECONCILIATION_VOCABULARY = [
    "ACCEPT_ADD_PROPOSAL",
    "REJECT_PROPOSAL",
    "RETAIN",
    "SUPERSEDE_PROPOSAL",
    "CLOSE_UNKNOWN_PROPOSAL",
    "RETAIN_UNKNOWN",
    "PRESERVE_AMBIGUITY",
    "REGISTER_CONTRADICTION",
    "REQUIRE_OWNER_DECISION",
    "DEFER_OUT_OF_SCOPE",
]


def load_schema(name: str) -> dict:
    return json.loads((ROOT / "engines/canon/schemas" / name).read_text(encoding="utf-8"))


def canon_foundation() -> dict:
    return {
        "artifact_type": "CANON_FOUNDATION",
        "artifact_id": "FOUND-1",
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "STATE-0",
        "status": "PROPOSED",
        "provenance": ["AUTH-1"],
        "related_artifacts": [],
        "project_id": "P",
        "canon_version": "0.1.0",
        "authority": {"holder": "OWNER/K0", "scope": "canon", "source_ref": "AUTH-1"},
        "source_refs": [],
        "protected_values": [],
        "facts": [],
        "assumptions": [],
        "unknowns": [],
        "ambiguities": [],
        "contradictions": [],
        "decisions": [],
        "freeze": {"state": "OPEN", "scope": "canon", "freeze_record_ref": None},
    }


def canon_state() -> dict:
    return {
        "artifact_type": "CANON_STATE",
        "artifact_id": "CANON-1",
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "STATE-0",
        "status": "PROPOSED",
        "provenance": ["AUTH-1"],
        "related_artifacts": ["FOUND-1"],
        "project_id": "P",
        "canon_version": "1.0.0",
        "maturity": "CANON_1_0",
        "authority": {"holder": "OWNER/K0", "scope": "canon", "source_ref": "AUTH-1"},
        "foundation_ref": "FOUND-1",
        "research_release_ref": "REL-1",
        "reconciliation_ref": "REC-1",
        "entries": [],
        "freeze": {"state": "OPEN", "scope": "canon", "freeze_record_ref": None},
        "change_history": [],
    }


class CanonReviewRepairTest(unittest.TestCase):
    def test_reconciliation_vocabulary_parity_and_nonempty_result(self) -> None:
        schema = load_schema("canon-reconciliation-result.schema.json")
        disposition_schema = schema["$defs"]["disposition"]
        enum = disposition_schema["properties"]["disposition"]["enum"]
        self.assertEqual(enum, RECONCILIATION_VOCABULARY)

        skill = (ROOT / "engines/canon/skills/reconcile-research-into-canon/SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / "engines/canon/workflows/reconcile-research-into-canon.md").read_text(encoding="utf-8")
        template = (ROOT / "engines/canon/templates/CANON_RECONCILIATION_RESULT.yaml").read_text(encoding="utf-8")
        for disposition in RECONCILIATION_VOCABULARY:
            with self.subTest(disposition=disposition):
                self.assertIn(disposition, skill)
                self.assertIn(disposition, workflow)
                self.assertIn(disposition, template)

        item = {
            "source_ref": "FINDING-1",
            "disposition": "RETAIN_UNKNOWN",
            "canon_entry_refs": ["UNKNOWN-1"],
            "reason": "Evidence does not close the registered unknown.",
            "authority_ref": None,
        }
        result = {
            "artifact_type": "CANON_RECONCILIATION_RESULT",
            "artifact_id": "REC-1",
            "produced_by_role": "executor",
            "assignment_id": "ASSIGN-1",
            "input_state_ref": "CANON-0",
            "status": "PROPOSED",
            "provenance": ["REL-1", "FINDING-1"],
            "related_artifacts": ["CANON-0", "REL-1"],
            "project_id": "P",
            "source_canon_ref": "CANON-0",
            "research_release_refs": ["REL-1"],
            "dispositions": [item],
            "change_proposal_refs": [],
            "mutation_authority_ref": None,
        }
        self.assertTrue(schema_accepts(result, schema))
        self.assertTrue(schema_accepts(item, disposition_schema))
        legacy = deepcopy(item)
        legacy["disposition"] = "NO_CHANGE"
        self.assertFalse(schema_accepts(legacy, disposition_schema))

    def test_foundation_and_state_freeze_status_are_bidirectionally_coherent(self) -> None:
        for schema_name, factory in (
            ("canon-foundation.schema.json", canon_foundation),
            ("canon-state.schema.json", canon_state),
        ):
            schema = load_schema(schema_name)
            with self.subTest(schema=schema_name, case="normal-open"):
                self.assertTrue(schema_accepts(factory(), schema))

            open_frozen = factory()
            open_frozen["status"] = "FROZEN"
            with self.subTest(schema=schema_name, case="frozen-status-open-freeze"):
                self.assertFalse(schema_accepts(open_frozen, schema))

            missing_record = factory()
            missing_record["status"] = "FROZEN"
            missing_record["freeze"]["state"] = "FROZEN"
            with self.subTest(schema=schema_name, case="frozen-status-null-record"):
                self.assertFalse(schema_accepts(missing_record, schema))

            valid_frozen = factory()
            valid_frozen["status"] = "FROZEN"
            valid_frozen["freeze"].update(state="FROZEN", freeze_record_ref="FREEZE-1")
            with self.subTest(schema=schema_name, case="valid-frozen"):
                self.assertTrue(schema_accepts(valid_frozen, schema))

            inverse = factory()
            inverse["status"] = "ACCEPTED"
            inverse["freeze"].update(state="FROZEN", freeze_record_ref="FREEZE-1")
            with self.subTest(schema=schema_name, case="nested-frozen-nonfrozen-status"):
                self.assertFalse(schema_accepts(inverse, schema))

    def test_validation_workflow_is_nonmutating_and_freeze_remains_authority_gated(self) -> None:
        manifest = (ROOT / "engines/canon/MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertRegex(manifest, r"(?m)^  validate_canon: validate_canon$")
        self.assertRegex(manifest, r"(?m)^  freeze_canon: validate_and_freeze_canon$")

        validation_contract = re.search(
            r"(?ms)^  validate_canon:\n(?P<body>.*?)(?=^  validate_and_freeze_canon:)", manifest
        )
        self.assertIsNotNone(validation_contract)
        validation_body = validation_contract.group("body")
        self.assertIn("engines/canon/skills/validate-canon/SKILL.md", validation_body)
        self.assertIn("exact_canon_candidate_ref", validation_body)
        self.assertNotIn("freeze-canon", validation_body)
        self.assertNotIn("explicit_freeze_authority", validation_body)

        freeze_contract = re.search(
            r"(?ms)^  validate_and_freeze_canon:\n(?P<body>.*?)(?=^  final_canon_reconciliation:)", manifest
        )
        self.assertIsNotNone(freeze_contract)
        freeze_body = freeze_contract.group("body")
        self.assertIn("engines/canon/skills/freeze-canon/SKILL.md", freeze_body)
        self.assertIn("explicit_freeze_authority", freeze_body)

        validation_workflow = (ROOT / "engines/canon/workflows/validate-canon.md").read_text(encoding="utf-8")
        self.assertIn("does not grant acceptance or freeze authority", validation_workflow)
        self.assertIn("Do not run `freeze-canon`", validation_workflow)
        self.assertIn("unchanged exact Canon candidate ref", validation_workflow)

        value = bundle("canon", "validate_canon", "validate_canon")
        value["selected_prerequisite_actions"] = [{
            "action_id": "canon-validation-durable-result",
            "required_capabilities": ["durable_artifact_write"],
            "evidence_path": "durable internal Canon validation result",
        }]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["workflow_id"], "validate_canon")
        self.assertNotIn("freeze", result["assignment"]["objective"].lower())


if __name__ == "__main__":
    unittest.main()
