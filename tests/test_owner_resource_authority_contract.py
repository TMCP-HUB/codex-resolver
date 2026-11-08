from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from tests.test_resource_governance_contract import schema_accepts

ROOT = Path(__file__).resolve().parents[1]
OWNER_SCHEMA = json.loads((ROOT / "schemas/owner-decision-record.schema.json").read_text(encoding="utf-8"))
GRANT_SCHEMA = json.loads((ROOT / "schemas/resource-grant.schema.json").read_text(encoding="utf-8"))
CONTRACT = (ROOT / "contracts/OWNER_RESOURCE_AUTHORITY_CONTRACT.md").read_text(encoding="utf-8")

DECISION_KIND = "OWNER_APPROVED_RESOURCE_AUTHORITY"
AFFIRMATIVE = "AUTHORIZE_RESOURCE_AUTHORITY"


def resource_limits() -> list[dict[str, object]]:
    return [
        {
            "resource_class": "MODEL_INFERENCE",
            "dimension": "TOKENS",
            "limit_mode": "RESERVABLE_LIMIT",
            "ordinary_limit": 1000,
            "finalization_reserve": 100,
        }
    ]


def finalization_policy() -> dict[str, object]:
    return {
        "protected": True,
        "allowed_purposes": ["FINAL_ACCOUNTING", "CONTROL_HANDOFF"],
    }


def owner_decision() -> dict[str, object]:
    return {
        "artifact_type": "OWNER_DECISION_RECORD",
        "artifact_id": "OWNER-RESOURCE-AUTH-1",
        "produced_by_role": "owner-interface",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "RECORDED",
        "provenance": ["owner-response:1"],
        "related_artifacts": ["RG-1"],
        "question_ref": "resource-authority:RG-1",
        "options_presented": [AFFIRMATIVE, "DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"],
        "selected_option": AFFIRMATIVE,
        "owner_constraints": [],
        "consequences_acknowledged": ["Finite resource authority applies only to RG-1."],
        "authority_role": "OWNER_K0",
        "decision_kind": DECISION_KIND,
        "authorized_resource_grant_ref": "RG-1",
        "authorized_scope": "assignment:A-1",
        "authorized_candidate_ref": "candidate:C-1",
        "authorized_route_ref": "route:R-1",
        "authorized_resource_classes": ["MODEL_INFERENCE"],
        "authorized_resource_limits": resource_limits(),
        "authorized_attempt_limit": 2,
        "authorized_valid_until": "2026-09-21T00:00:00Z",
        "authorized_finalization_policy": finalization_policy(),
        "non_transitive": True,
    }


def resource_grant() -> dict[str, object]:
    return {
        "artifact_type": "RESOURCE_GRANT",
        "artifact_id": "RG-1",
        "produced_by_role": "control-director",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "AUTHORIZED",
        "provenance": ["OWNER-RESOURCE-AUTH-1"],
        "related_artifacts": ["OWNER-RESOURCE-AUTH-1"],
        "issued_by": "control-director",
        "authority_source": {
            "authority_type": DECISION_KIND,
            "authority_ref": "OWNER-RESOURCE-AUTH-1",
        },
        "parent_grant_ref": None,
        "scope": {
            "scope_ref": "assignment:A-1",
            "candidate_ref": "candidate:C-1",
            "route_ref": "route:R-1",
            "resource_classes": ["MODEL_INFERENCE"],
        },
        "limits": resource_limits(),
        "attempt_limit": 2,
        "valid_until": "2026-09-21T00:00:00Z",
        "finalization_policy": finalization_policy(),
    }


def limit_map(items: object) -> dict[tuple[str, str], dict[str, object]] | None:
    if not isinstance(items, list):
        return None
    result: dict[tuple[str, str], dict[str, object]] = {}
    for item in items:
        if not isinstance(item, dict):
            return None
        resource_class = item.get("resource_class")
        dimension = item.get("dimension")
        if not isinstance(resource_class, str) or not isinstance(dimension, str):
            return None
        key = (resource_class, dimension)
        if key in result:
            return None
        result[key] = item
    return result


def grant_authority_shape_valid(grant: dict[str, object]) -> bool:
    scope = grant.get("scope")
    if not isinstance(scope, dict):
        return False
    resource_classes = scope.get("resource_classes")
    if not isinstance(resource_classes, list):
        return False
    limits = limit_map(grant.get("limits"))
    if limits is None:
        return False
    declared_classes = set(resource_classes)
    return all(limit.get("resource_class") in declared_classes for limit in limits.values())


def limits_equal(left: object, right: object) -> bool:
    left_map = limit_map(left)
    right_map = limit_map(right)
    if left_map is None or right_map is None or left_map.keys() != right_map.keys():
        return False
    fields = ("resource_class", "dimension", "limit_mode", "ordinary_limit", "finalization_reserve")
    return all(
        all(left_map[key].get(field) == right_map[key].get(field) for field in fields)
        for key in left_map
    )


def finalization_equal(left: object, right: object) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    if left.get("protected") is not True or right.get("protected") is not True:
        return False
    left_purposes = left.get("allowed_purposes")
    right_purposes = right.get("allowed_purposes")
    if not isinstance(left_purposes, list) or not isinstance(right_purposes, list):
        return False
    return set(left_purposes) == set(right_purposes)


def preserved_value_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(preserved_value_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(preserved_value_equal(a, b) for a, b in zip(left, right))
    return left == right


def same_instant(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is right
    try:
        a = datetime.fromisoformat(left.replace("Z", "+00:00"))
        b = datetime.fromisoformat(right.replace("Z", "+00:00"))
        return a.utcoffset() is not None and b.utcoffset() is not None and a.astimezone(timezone.utc) == b.astimezone(timezone.utc)
    except (AttributeError, ValueError, OverflowError):
        return False


def owner_resource_authority_proven(grant: dict[str, object], artifacts: list[dict[str, object]],
                                    resource_interpretation_ref: str | None = None) -> bool:
    """Reference predicate for the frozen cross-artifact contract, not runtime RG-04 code."""
    if not schema_accepts(grant, GRANT_SCHEMA):
        return False
    if not grant_authority_shape_valid(grant):
        return False
    source = grant.get("authority_source")
    if not isinstance(source, dict) or source.get("authority_type") != DECISION_KIND:
        return False
    if grant.get("parent_grant_ref") is not None:
        return False
    authority_ref = source.get("authority_ref")
    matches = [artifact for artifact in artifacts if artifact.get("artifact_id") == authority_ref]
    if len(matches) != 1:
        return False
    authority = matches[0]
    if not schema_accepts(authority, OWNER_SCHEMA):
        return False
    original = authority
    if grant.get("artifact_id") not in original.get("related_artifacts", []):
        return False
    if resource_interpretation_ref is not None:
        normalized = [item for item in artifacts if item.get("artifact_id") == resource_interpretation_ref]
        if (resource_interpretation_ref == authority_ref or len(normalized) != 1
                or not schema_accepts(normalized[0], OWNER_SCHEMA)):
            return False
        authority = normalized[0]
        if authority_ref not in authority.get("related_artifacts", []) or "resource_interpretation" not in authority:
            return False
        metadata = {"artifact_id", "provenance", "related_artifacts", "resource_interpretation", "qualifications"}
        original_fields = set(original) - metadata
        unordered = {"authorized_resource_classes", "authorized_resource_limits", "authorized_finalization_policy", "authorized_valid_until"}
        if (original_fields != set(authority) - metadata
                or any(not preserved_value_equal(original[field], authority[field]) for field in original_fields - unordered)
                or set(original["authorized_resource_classes"]) != set(authority["authorized_resource_classes"])
                or not limits_equal(original["authorized_resource_limits"], authority["authorized_resource_limits"])
                or not finalization_equal(original["authorized_finalization_policy"], authority["authorized_finalization_policy"])
                or not same_instant(original["authorized_valid_until"], authority["authorized_valid_until"])
                or original.get("qualifications", []) != authority.get("qualifications", [])):
            return False
        if "resource_interpretation" in original:
            prior = original["resource_interpretation"]
            if (prior["source_text"] != authority["resource_interpretation"]["source_text"]
                    or prior["unresolved_constraints"] or prior["unresolved_qualifications"]):
                return False
    if authority.get("artifact_type") != "OWNER_DECISION_RECORD":
        return False
    if authority.get("produced_by_role") != "owner-interface":
        return False
    if authority.get("status") != "RECORDED":
        return False
    if authority.get("authority_role") != "OWNER_K0":
        return False
    if authority.get("decision_kind") != DECISION_KIND:
        return False
    if authority.get("resource_input_mode") != "DIRECT_INSTRUCTION":
        if authority.get("selected_option") != AFFIRMATIVE:
            return False
        options = authority.get("options_presented")
        if not isinstance(options, list) or AFFIRMATIVE not in options:
            return False
    if authority.get("non_transitive") is not True:
        return False
    if authority.get("authorized_resource_grant_ref") != grant.get("artifact_id"):
        return False
    if authority.get("assignment_id") != grant.get("assignment_id"):
        return False
    if authority.get("input_state_ref") != grant.get("input_state_ref"):
        return False
    scope = grant.get("scope")
    if not isinstance(scope, dict):
        return False
    if authority.get("authorized_scope") != scope.get("scope_ref"):
        return False
    if authority.get("authorized_candidate_ref") != scope.get("candidate_ref"):
        return False
    if authority.get("authorized_route_ref") != scope.get("route_ref"):
        return False
    resource_classes = scope.get("resource_classes")
    authorized_classes = authority.get("authorized_resource_classes")
    if not isinstance(resource_classes, list) or not isinstance(authorized_classes, list):
        return False
    if set(authorized_classes) != set(resource_classes):
        return False
    if not limits_equal(authority.get("authorized_resource_limits"), grant.get("limits")):
        return False
    if authority.get("authorized_attempt_limit") != grant.get("attempt_limit"):
        return False
    if not same_instant(authority.get("authorized_valid_until"), grant.get("valid_until")):
        return False
    if not finalization_equal(authority.get("authorized_finalization_policy"), grant.get("finalization_policy")):
        return False
    related = authority.get("related_artifacts")
    if not isinstance(related, list) or grant.get("artifact_id") not in related:
        return False
    interpretation = authority.get("resource_interpretation")
    if interpretation is None:
        if authority.get("owner_constraints") or authority.get("qualifications", []):
            return False
    elif interpretation["unresolved_constraints"] or interpretation["unresolved_qualifications"]:
        return False
    return source.get("authority_ref") == original.get("artifact_id")


class OwnerResourceAuthorityContractTest(unittest.TestCase):
    def assert_not_authorized(self, grant: dict[str, object], authority: dict[str, object] | None) -> None:
        artifacts = [] if authority is None else [authority]
        self.assertFalse(owner_resource_authority_proven(grant, artifacts))

    def test_fully_valid_resource_authorizing_owner_decision_is_accepted(self) -> None:
        grant = resource_grant()
        authority = owner_decision()
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assertTrue(owner_resource_authority_proven(grant, [authority]))

    def test_direct_instruction_has_no_fabricated_option_and_keeps_real_constraints(self) -> None:
        grant = resource_grant(); authority = owner_decision()
        for field in ("question_ref", "options_presented", "selected_option"):
            del authority[field]
        authority.update(resource_input_mode="DIRECT_INSTRUCTION", owner_constraints=["Use at most the specified amount."],
                         resource_interpretation={"source_text": "Use at most the specified amount.",
                             "unresolved_constraints": [], "unresolved_qualifications": []})
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assertTrue(owner_resource_authority_proven(grant, [authority]))
        authority["resource_interpretation"]["unresolved_constraints"] = ["Wait for the audit."]
        self.assertFalse(owner_resource_authority_proven(grant, [authority]))

    def test_old_option_decision_is_preserved_and_linked_to_normalized_view(self) -> None:
        grant = resource_grant(); original = owner_decision()
        original["owner_constraints"] = ["Use at most the specified amount."]
        view = deepcopy(original); view["artifact_id"] = "INTERPRETATION-1"
        view["related_artifacts"].append(original["artifact_id"])
        view["resource_interpretation"] = {"source_text": "Use at most the specified amount.",
                                           "unresolved_constraints": [], "unresolved_qualifications": []}
        self.assertFalse(owner_resource_authority_proven(grant, [original, view]))
        self.assertTrue(owner_resource_authority_proven(grant, [original, view], "INTERPRETATION-1"))
        view["authorized_valid_until"] = "2026-09-21T03:00:00+03:00"
        self.assertTrue(owner_resource_authority_proven(grant, [original, view], "INTERPRETATION-1"))
        view["authorized_valid_until"] = "2026-09-21T03:00:01+03:00"
        self.assertFalse(owner_resource_authority_proven(grant, [original, view], "INTERPRETATION-1"))
        view["authorized_valid_until"] = original["authorized_valid_until"]
        view["owner_constraints"] = []
        self.assertFalse(owner_resource_authority_proven(grant, [original, view], "INTERPRETATION-1"))

    def test_schema_invalid_owner_decision_is_rejected(self) -> None:
        authority = owner_decision()
        authority.pop("owner_constraints")
        self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_wrong_authority_role_is_rejected(self) -> None:
        authority = owner_decision()
        authority["authority_role"] = "CONTROL_DIRECTOR"
        self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_wrong_producer_is_rejected(self) -> None:
        authority = owner_decision()
        authority["produced_by_role"] = "control-director"
        self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_non_recorded_status_is_rejected(self) -> None:
        authority = owner_decision()
        authority["status"] = "PROPOSED"
        self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_unrelated_but_valid_owner_decision_is_rejected(self) -> None:
        authority = owner_decision()
        authority["decision_kind"] = "DEPLOYMENT_DECISION"
        authority["options_presented"] = ["APPROVE_DEPLOYMENT", "DEFER"]
        authority["selected_option"] = "APPROVE_DEPLOYMENT"
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_non_affirmative_resource_selection_is_valid_record_but_not_authority(self) -> None:
        authority = owner_decision()
        authority["selected_option"] = "DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY"
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_resource_decision_without_affirmative_option_is_schema_invalid(self) -> None:
        authority = owner_decision()
        authority["options_presented"] = ["DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"]
        authority["selected_option"] = "DEFER"
        self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_target_grant_mismatch_is_rejected(self) -> None:
        authority = owner_decision()
        authority["authorized_resource_grant_ref"] = "RG-OTHER"
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_assignment_mismatch_is_rejected(self) -> None:
        authority = owner_decision()
        authority["assignment_id"] = "A-OTHER"
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_input_state_mismatch_is_rejected(self) -> None:
        authority = owner_decision()
        authority["input_state_ref"] = "STATE-OTHER"
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_scope_candidate_and_route_mismatch_are_rejected(self) -> None:
        mutations = (
            ("authorized_scope", "assignment:OTHER"),
            ("authorized_candidate_ref", "candidate:OTHER"),
            ("authorized_route_ref", "route:OTHER"),
            ("authorized_candidate_ref", None),
            ("authorized_route_ref", None),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                authority = owner_decision()
                authority[field] = value
                self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
                self.assert_not_authorized(resource_grant(), authority)

    def test_finite_authority_term_mismatches_are_rejected(self) -> None:
        cases: list[tuple[str, object]] = [
            ("authorized_resource_classes", ["REMOTE_CI"]),
            ("authorized_attempt_limit", 3),
            ("authorized_valid_until", "2026-09-22T00:00:00Z"),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                authority = owner_decision()
                authority[field] = value
                self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
                self.assert_not_authorized(resource_grant(), authority)

        authority = owner_decision()
        authority["authorized_resource_limits"][0]["ordinary_limit"] = 1001
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

        authority = owner_decision()
        authority["authorized_finalization_policy"]["allowed_purposes"] = ["FINAL_ACCOUNTING"]
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_limit_resource_class_outside_scope_fails_closed(self) -> None:
        remote_ci_limit = {
            "resource_class": "REMOTE_CI",
            "dimension": "RUNNER_MINUTES",
            "limit_mode": "HARD_LIMIT",
            "ordinary_limit": 10,
            "finalization_reserve": 1,
        }
        grant = resource_grant()
        grant["limits"] = [deepcopy(remote_ci_limit)]
        authority = owner_decision()
        authority["authorized_resource_limits"] = [deepcopy(remote_ci_limit)]
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(grant, authority)

    def test_declared_multi_class_scope_does_not_require_limit_for_every_class(self) -> None:
        grant = resource_grant()
        authority = owner_decision()
        grant["scope"]["resource_classes"] = ["MODEL_INFERENCE", "REMOTE_CI"]
        authority["authorized_resource_classes"] = ["REMOTE_CI", "MODEL_INFERENCE"]
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assertTrue(owner_resource_authority_proven(grant, [authority]))

    def test_limit_and_finalization_reordering_preserves_same_authority(self) -> None:
        grant = resource_grant()
        authority = owner_decision()
        second = {
            "resource_class": "REMOTE_CI",
            "dimension": "RUNNER_MINUTES",
            "limit_mode": "HARD_LIMIT",
            "ordinary_limit": 10,
            "finalization_reserve": 1,
        }
        grant["scope"]["resource_classes"].append("REMOTE_CI")
        grant["limits"].append(second)
        authority["authorized_resource_classes"] = ["REMOTE_CI", "MODEL_INFERENCE"]
        authority["authorized_resource_limits"] = [deepcopy(second), resource_limits()[0]]
        authority["authorized_finalization_policy"]["allowed_purposes"] = ["CONTROL_HANDOFF", "FINAL_ACCOUNTING"]
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assertTrue(owner_resource_authority_proven(grant, [authority]))

    def test_duplicate_limit_keys_fail_closed(self) -> None:
        authority = owner_decision()
        authority["authorized_resource_limits"].append(deepcopy(authority["authorized_resource_limits"][0]))
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

        grant = resource_grant()
        grant["limits"].append(deepcopy(grant["limits"][0]))
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertFalse(owner_resource_authority_proven(grant, [owner_decision()]))

    def test_owner_constraints_or_qualifications_do_not_become_hidden_authority(self) -> None:
        authority = owner_decision()
        authority["owner_constraints"] = ["Only after audit passes."]
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

        authority = owner_decision()
        authority["qualifications"] = ["Only for a later candidate."]
        self.assertTrue(schema_accepts(authority, OWNER_SCHEMA))
        self.assert_not_authorized(resource_grant(), authority)

    def test_fake_or_nonexistent_authority_ref_is_rejected(self) -> None:
        grant = resource_grant()
        grant["authority_source"]["authority_ref"] = "OWNER-NOT-FOUND"
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertFalse(owner_resource_authority_proven(grant, [owner_decision()]))
        self.assertFalse(owner_resource_authority_proven(grant, []))

    def test_resource_grant_cannot_self_authorize(self) -> None:
        grant = resource_grant()
        grant["authority_source"]["authority_ref"] = grant["artifact_id"]
        self.assertTrue(schema_accepts(grant, GRANT_SCHEMA))
        self.assertFalse(owner_resource_authority_proven(grant, [grant]))

    def test_existing_non_resource_owner_decision_remains_valid(self) -> None:
        decision = {
            "artifact_type": "OWNER_DECISION_RECORD",
            "artifact_id": "OWNER-OTHER-1",
            "produced_by_role": "owner-interface",
            "assignment_id": "A-OTHER",
            "input_state_ref": "STATE-OTHER",
            "status": "RECORDED",
            "provenance": ["owner-response:other"],
            "related_artifacts": [],
            "question_ref": "architecture:choice",
            "options_presented": ["OPTION_A", "OPTION_B"],
            "selected_option": "OPTION_A",
            "owner_constraints": [],
            "consequences_acknowledged": [],
            "authority_role": "OWNER_K0",
            "decision_kind": "ARCHITECTURE_DECISION",
        }
        self.assertTrue(schema_accepts(decision, OWNER_SCHEMA))

    def test_resource_specialization_requires_exact_binding_fields(self) -> None:
        for field in (
            "authority_role",
            "authorized_resource_grant_ref",
            "authorized_scope",
            "authorized_candidate_ref",
            "authorized_route_ref",
            "authorized_resource_classes",
            "authorized_resource_limits",
            "authorized_attempt_limit",
            "authorized_valid_until",
            "authorized_finalization_policy",
            "non_transitive",
        ):
            with self.subTest(field=field):
                authority = owner_decision()
                authority.pop(field)
                self.assertFalse(schema_accepts(authority, OWNER_SCHEMA))

    def test_contract_freezes_owner_authority_without_rg04_runtime(self) -> None:
        for required in (
            "OWNER IDENTITY",
            "OWNER_DECISION_RECORD EXISTS",
            "RESOURCE_GRANT MAY REFERENCE AUTHORITY",
            "decision_kind = OWNER_APPROVED_RESOURCE_AUTHORITY",
            "selected_option = AUTHORIZE_RESOURCE_AUTHORITY",
            "authorized_resource_grant_ref",
            "authorized_resource_classes",
            "authorized_resource_limits",
            "authorized_attempt_limit",
            "authorized_valid_until",
            "authorized_finalization_policy",
            "every limit resource_class belongs to scope.resource_classes",
            "assignment_id",
            "input_state_ref",
            "authorized_candidate_ref",
            "authorized_route_ref",
            "tools/resource_admission.py",
            "tools/resolver_spawn.py",
        ):
            self.assertIn(required, CONTRACT)


if __name__ == "__main__":
    unittest.main()
