from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.executability import validate_director_decision
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]
BATONS = ("WAIT", "ESCALATE", "COMPLETE")


def director_decision() -> dict[str, object]:
    return {
        "artifact_type": "DIRECTOR_DECISION",
        "artifact_id": "DIRECTOR-POST",
        "produced_by_role": "control-director",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "INPUT-1",
        "status": "PENDING",
        "provenance": ["ASSIGN-1"],
        "related_artifacts": ["ASSIGN-1", "ADM-1"],
        "executor_result_ref": "RESULT-1",
        "verification_result_ref": "VERIFY-1",
        "control_state": "WAIT",
        "decision": "Reconcile the structured post-spawn control point.",
        "next_owner": "control-director",
        "transition_authority": {
            "transition_id": "TRANSITION-1",
            "assignment_ref": "ASSIGN-1",
            "acceptance_requirements": [
                {
                    "requirement_id": "acceptance-output",
                    "claim_id": "claim-result",
                    "required_evidence_refs": ["EVIDENCE-RESULT"],
                }
            ],
            "verification_required": True,
            "verification_target_claim_ids": ["claim-result"],
            "allowed_verification_outcomes": ["CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"],
            "verification_outcome_map": {
                "CONFIRMED": "COMPLETE",
                "QUALIFIED": "WAIT",
                "NOT_PROVEN": "WAIT",
                "BLOCKED": "WAIT",
            },
            "incomplete_outcome": "WAIT",
            "next_control_intent_ref": None,
            "required_proof_refs": ["ADM-1"],
            "requires_current_executability": False,
        },
    }


def malformed_transition_bundle(decision: dict[str, object]) -> dict[str, object]:
    current = {
        "artifact_type": "STATE_OBSERVATION",
        "artifact_id": "STATE-1",
        "produced_by_role": "control-director",
        "input_state_ref": "INPUT-1",
        "status": "CURRENT",
        "provenance": ["RESULT-1"],
        "related_artifacts": ["RESULT-1"],
        "state_identity": "git:result",
        "authority_scope": "transition-result",
    }
    return {
        "refs": {
            "current_state_ref": "STATE-1",
            "prior_director_decision_ref": "DIRECTOR-POST",
            "assignment_ref": "ASSIGN-1",
            "executor_result_ref": "RESULT-1",
        },
        "artifacts": [
            current,
            decision,
            {"artifact_id": "ASSIGN-1"},
            {"artifact_id": "RESULT-1"},
        ],
    }


class VerificationAuthorityCeilingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads((ROOT / "schemas/director-decision.schema.json").read_text())
        cls.schema_map = schema["properties"]["transition_authority"]["properties"]["verification_outcome_map"]["properties"]

    def test_runtime_matches_schema_verification_outcome_ceiling(self) -> None:
        base = director_decision()
        for outcome, rule in self.schema_map.items():
            allowed = set(rule["enum"])
            for baton in BATONS:
                candidate = deepcopy(base)
                candidate["transition_authority"]["verification_outcome_map"][outcome] = baton
                errors = validate_director_decision(candidate)
                with self.subTest(outcome=outcome, baton=baton):
                    self.assertEqual(not errors, baton in allowed, errors)

    def test_non_confirmed_complete_authority_fails_closed(self) -> None:
        for outcome in ("QUALIFIED", "NOT_PROVEN", "BLOCKED"):
            decision = director_decision()
            decision["transition_authority"]["verification_outcome_map"][outcome] = "COMPLETE"
            errors = validate_director_decision(decision)
            with self.subTest(outcome=outcome):
                self.assertTrue(any("verification_outcome_map is invalid" in error for error in errors), errors)
                result = resolve_transition(malformed_transition_bundle(decision))
                self.assertEqual(
                    (result["control_state"], result["reason"]),
                    ("ESCALATE", "MALFORMED_DIRECTOR_DECISION"),
                )


if __name__ == "__main__":
    unittest.main()
