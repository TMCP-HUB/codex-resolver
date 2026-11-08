from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles/owner-interface/ROLE.md"
SKILL_ROOT = ROOT / "roles/owner-interface/skills"
SKILLS = {
    "owner-intent-sensemaking": SKILL_ROOT / "owner-intent-sensemaking/SKILL.md",
    "project-context-orientation": SKILL_ROOT / "project-context-orientation/SKILL.md",
    "owner-actionability": SKILL_ROOT / "owner-actionability/SKILL.md",
    "owner-decision-surface": SKILL_ROOT / "owner-decision-surface/SKILL.md",
    "owner-response-recording": SKILL_ROOT / "owner-response-recording/SKILL.md",
}
OWNER_SCHEMA = ROOT / "schemas/owner-decision-record.schema.json"


def schema_accepts(value: object, schema: dict) -> bool:
    """Execute the JSON-Schema keywords used by OWNER_DECISION_RECORD fixtures."""
    def valid(instance: object, rule: dict) -> bool:
        if "not" in rule and valid(instance, rule["not"]):
            return False
        kind = rule.get("type")
        kinds = kind if isinstance(kind, list) else [kind] if kind else []
        if kinds:
            checks = {
                "object": lambda x: isinstance(x, dict),
                "array": lambda x: isinstance(x, list),
                "string": lambda x: isinstance(x, str),
                "null": lambda x: x is None,
                "boolean": lambda x: isinstance(x, bool),
            }
            if not any(name in checks and checks[name](instance) for name in kinds):
                return False
        if "const" in rule and instance != rule["const"]:
            return False
        if isinstance(instance, str):
            if len(instance) < rule.get("minLength", 0):
                return False
            if "pattern" in rule and re.fullmatch(rule["pattern"], instance) is None:
                return False
        if isinstance(instance, list):
            if len(instance) < rule.get("minItems", 0):
                return False
            if "items" in rule and not all(valid(item, rule["items"]) for item in instance):
                return False
        if isinstance(instance, dict):
            if any(name not in instance for name in rule.get("required", [])):
                return False
            properties = rule.get("properties", {})
            if any(name in instance and not valid(instance[name], child) for name, child in properties.items()):
                return False
            for condition in rule.get("allOf", []):
                if "if" in condition and valid(instance, condition["if"]) and not valid(instance, condition.get("then", {})):
                    return False
        return True

    return valid(value, schema)


class OwnerInterfaceCoreSkillsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.role = ROLE.read_text(encoding="utf-8")
        cls.skills = {name: path.read_text(encoding="utf-8") for name, path in SKILLS.items()}
        cls.schema = json.loads(OWNER_SCHEMA.read_text(encoding="utf-8"))

    def test_role_discovers_exactly_five_core_skills_in_deterministic_order(self) -> None:
        self.assertEqual(
            sorted(path.parent.name for path in SKILL_ROOT.glob("*/SKILL.md")),
            sorted(SKILLS),
        )
        refs = [str(path.relative_to(ROOT)).replace("\\", "/") for path in SKILLS.values()]
        positions = [self.role.index(ref) for ref in refs]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Load these role-owned skills deterministically in this order", self.role)

    def test_new_skills_follow_authoring_contract(self) -> None:
        required_sections = [
            "## Purpose",
            "## Goal",
            "## When to use",
            "## Inputs",
            "## Execution contract",
            "## Required outputs",
            "## Procedure",
            "## Anti-patterns",
            "## Verification checklist",
        ]
        for name, text in self.skills.items():
            with self.subTest(skill=name):
                self.assertRegex(text, rf"(?m)^name: {re.escape(name)}$")
                for section in required_sections:
                    self.assertIn(section, text)
                self.assertIn("evidence", text.lower())
                self.assertIn("authority", text.lower())

    def test_system_owned_next_action_is_not_a_human_routing_question(self) -> None:
        text = self.skills["owner-actionability"]
        self.assertIn("`SYSTEM_OWNED_NEXT_ACTION` | false | system/control", text)
        self.assertIn("retain the baton", text.lower())
        self.assertIn("asking the Owner to choose among internal execution surfaces when Control can route", text)
        self.assertNotIn("Do you want ChatGPT, Codex Cloud, or Agent System to do this?", text)
        self.assertIn("VERIFICATION PASS != RETURN BATON TO OWNER", text)
        self.assertIn("promotion is already authorized and admitted", text)

    def test_manual_external_operation_is_one_bounded_action(self) -> None:
        text = self.skills["owner-actionability"]
        self.assertIn("`MANUAL_EXTERNAL_OPERATION_REQUIRED` | true | Owner/manual operator", text)
        self.assertIn("one precise external operation", text)
        self.assertIn("exact result to return", text)
        self.assertIn("multiple internal-agent menus", text)

    def test_genuine_owner_gate_is_humanized_and_machine_items_are_suppressed(self) -> None:
        text = self.skills["owner-decision-surface"]
        self.assertIn("machine-resolvable | no", text)
        self.assertIn("system recommendation/default requiring Owner approval | yes", text)
        self.assertIn("genuine Owner preference/authority choice | yes", text)
        self.assertIn("Every human label maps to exactly one admitted canonical option", text)
        self.assertIn("Large genuine Owner decision sets must not be dumped as one raw form", text)
        self.assertIn("Raw schemas", text)
        self.assertIn("visibly non-binding", text)

    def test_natural_unambiguous_answer_fits_exact_existing_owner_record(self) -> None:
        text = self.skills["owner-response-recording"]
        self.assertIn('"Use safer default" -> OPTION_B', text)
        self.assertIn("selected_option = OPTION_B", text)
        self.assertIn('preserve "Only for this release."', text)

        record = {
            "artifact_type": "OWNER_DECISION_RECORD",
            "artifact_id": "OWNER-DECISION-1",
            "produced_by_role": "owner-interface",
            "assignment_id": "ASSIGN-54A",
            "input_state_ref": "STATE-54A",
            "status": "RECORDED",
            "provenance": ["SURFACE-1", "OWNER-RESPONSE-1"],
            "related_artifacts": ["SURFACE-1"],
            "question_ref": "QUESTION-1",
            "options_presented": ["OPTION_A", "OPTION_B"],
            "selected_option": "OPTION_B",
            "owner_constraints": ["Only for this release."],
            "consequences_acknowledged": [],
            "qualifications": ["Only for this release."],
            "authority_role": "OWNER_K0",
        }
        self.assertTrue(schema_accepts(record, self.schema))
        self.assertEqual(record["selected_option"], "OPTION_B")
        self.assertEqual(record["owner_constraints"], ["Only for this release."])
        self.assertEqual(record["qualifications"], ["Only for this release."])

    def test_ambiguous_answer_fails_closed_without_selected_record(self) -> None:
        text = self.skills["owner-response-recording"]
        self.assertIn("return `CLARIFICATION_REQUIRED`", text)
        self.assertIn("No record may claim a selection", text)
        self.assertIn('"Either is fine" when A and B are materially distinct', text)
        self.assertIn("do not construct a selected record", text)
        self.assertIn("semantic ambiguity", text)

    def test_branching_conditional_reports_existing_schema_limit_instead_of_v2(self) -> None:
        text = self.skills["owner-response-recording"]
        self.assertIn('"B if X, otherwise A"', text)
        self.assertIn("one required `selected_option`", text)
        self.assertIn("return `SCHEMA_LIMITATION`", text)
        self.assertFalse((ROOT / "schemas/owner-decision-record-v2.schema.json").exists())
        self.assertFalse((ROOT / "schemas/owner-interface-response.schema.json").exists())
        self.assertNotIn("OWNER_DECISION_RECORD_V2", self.role.split("No `OWNER_INTERFACE_RESPONSE`", 1)[0])

    def test_liaison_cannot_self_select_owner_reserved_option(self) -> None:
        surface = self.skills["owner-decision-surface"]
        recording = self.skills["owner-response-recording"]
        self.assertIn('"use your judgment and approve for me"', surface)
        self.assertIn("leaves the Owner gate unresolved", surface)
        self.assertIn('"use your judgment and approve for me"', recording)
        self.assertIn("No `OWNER_DECISION_RECORD` with a selected option is permitted", recording)
        self.assertIn("no authority to choose an Owner-reserved option", self.role)

    def test_existing_owner_decision_record_remains_authoritative(self) -> None:
        self.assertEqual(self.schema["title"], "OWNER_DECISION_RECORD")
        required = set(self.schema["required"])
        for field in {
            "artifact_type",
            "produced_by_role",
            "status",
            "owner_constraints",
            "consequences_acknowledged",
        }:
            self.assertIn(field, required)
        self.assertEqual(self.schema["properties"]["artifact_type"]["const"], "OWNER_DECISION_RECORD")
        self.assertEqual(self.schema["properties"]["produced_by_role"]["const"], "owner-interface")
        self.assertEqual(self.schema["properties"]["status"]["const"], "RECORDED")
        legacy = {"artifact_type": "OWNER_DECISION_RECORD", "artifact_id": "D-1",
                  "produced_by_role": "owner-interface", "assignment_id": "A-1", "input_state_ref": "S-1",
                  "status": "RECORDED", "provenance": [], "related_artifacts": [],
                  "question_ref": "Q-1", "options_presented": ["A"], "selected_option": "A",
                  "owner_constraints": [], "consequences_acknowledged": []}
        self.assertTrue(schema_accepts(legacy, self.schema))
        for field in ("question_ref", "options_presented", "selected_option"):
            incomplete = dict(legacy); del incomplete[field]
            self.assertFalse(schema_accepts(incomplete, self.schema))
        self.assertIn("schemas/owner-decision-record.schema.json", self.skills["owner-response-recording"])
        self.assertIn("existing `OWNER_DECISION_RECORD`", self.role)

    def test_authority_boundaries_and_parent_failure_classes_are_explicit(self) -> None:
        for failure in [
            "E-CONTROL-PLANE-LEAKAGE",
            "E-USER-ACTIONABILITY-GAP",
            "E-OWNER-DECISION-PRESENTATION-GAP",
            "E-HUMAN-GATE-COGNITIVE-OVERLOAD",
            "E-MACHINE-FORM-LEAKAGE",
            "E-LIAISON-AUTHORITY-ESCALATION",
        ]:
            self.assertIn(failure, self.role)
        for forbidden_owner in [
            "Control routing",
            "execution-surface selection",
            "implementation",
            "independent verification",
            "promotion/merge authority",
            "Canon/domain truth",
            "the Owner's decision",
        ]:
            self.assertIn(forbidden_owner, self.role)
        self.assertIn("No K0, Canon, Control Director, Executor, verification, or promotion authority", self.skills["owner-actionability"])
        self.assertIn("authorize implementation, verification, promotion, or execution", self.skills["owner-decision-surface"])
        self.assertIn("does not itself authorize the downstream transition", self.skills["owner-response-recording"])


if __name__ == "__main__":
    unittest.main()
