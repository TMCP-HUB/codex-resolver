from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_resolver_spawn import bundle
from tools.resolver_spawn import resolve_spawn

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "engines/research/schemas/research-chain-reconciliation.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_accepts(value: object, schema: dict) -> bool:
    root = schema

    def valid(instance: object, rule: dict) -> bool:
        ref = rule.get("$ref")
        if isinstance(ref, str):
            if not ref.startswith("#/$defs/"):
                return False
            name = ref.split("/")[-1]
            return valid(instance, root["$defs"][name])

        kind = rule.get("type")
        kinds = kind if isinstance(kind, list) else [kind] if kind else []
        checks = {
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
            "string": lambda x: isinstance(x, str),
            "null": lambda x: x is None,
            "boolean": lambda x: isinstance(x, bool),
        }
        if kinds and not any(name in checks and checks[name](instance) for name in kinds):
            return False
        if "const" in rule and instance != rule["const"]:
            return False
        if "enum" in rule and instance not in rule["enum"]:
            return False
        if isinstance(instance, str) and len(instance) < rule.get("minLength", 0):
            return False
        if isinstance(instance, list):
            if len(instance) < rule.get("minItems", 0):
                return False
            if rule.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in instance}) != len(instance):
                return False
            if "items" in rule and not all(valid(item, rule["items"]) for item in instance):
                return False
        if isinstance(instance, dict):
            if any(name not in instance for name in rule.get("required", [])):
                return False
            props = rule.get("properties", {})
            if rule.get("additionalProperties") is False and any(name not in props for name in instance):
                return False
            if any(name in instance and not valid(instance[name], child) for name, child in props.items()):
                return False
        return True

    return valid(value, schema)


def base_reconciliation() -> dict:
    return {
        "artifact_type": "RESEARCH_CHAIN_RECONCILIATION",
        "artifact_id": "RCR-1",
        "produced_by_role": "executor",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "STATE-1",
        "status": "PARTIAL",
        "provenance": ["RESEARCH-1", "RESEARCH-2"],
        "related_artifacts": ["RESEARCH-1", "RESEARCH-2"],
        "project_id": "P-1",
        "chain_id": "CHAIN-1",
        "upstream_research_refs": ["RESEARCH-1", "RESEARCH-2"],
        "requirement_evaluations": [
            {
                "requirement_ref": "REQ-A",
                "state": "SATISFIED",
                "supporting_research_refs": ["RESEARCH-1"],
                "gap_refs": [],
                "rationale": "First independent result satisfies this requirement.",
            },
            {
                "requirement_ref": "REQ-B",
                "state": "BLOCKED",
                "supporting_research_refs": ["RESEARCH-2"],
                "gap_refs": ["GAP-B"],
                "rationale": "Second requirement remains consequentially unresolved.",
            },
        ],
        "unresolved_gaps": [
            {
                "gap_id": "GAP-B",
                "requirement_ref": "REQ-B",
                "classification": "CONSEQUENTIAL_BLOCKER",
                "source_research_refs": ["RESEARCH-2"],
                "description": "A consequential external fact remains unresolved.",
                "active": True,
                "continuation": "DEFER",
            }
        ],
        "evidence_ceilings": [],
        "supersessions": [],
        "satisfied_requirement_refs": ["REQ-A"],
        "blocked_requirement_refs": ["REQ-B"],
        "next_research_frontier": [],
        "owner_input_required": False,
        "no_further_research_justified": False,
        "research_execution_authority": False,
        "direct_dispatch_authority": False,
        "canon_mutation_authority": False,
    }


def reconciliation_bundle() -> dict:
    value = bundle("research", "reconcile_research_chain", "research_chain_reconciliation")
    value["artifacts"].extend([
        {"artifact_id": "RESEARCH-1", "artifact_type": "RESEARCH_FINDING", "provenance": ["RESEARCH-RELEASE-1"]},
        {"artifact_id": "RESEARCH-2", "artifact_type": "RESEARCH_FINDING", "provenance": ["RESEARCH-RELEASE-2"]},
    ])
    value["assignment_draft_semantics"]["research_reconciliation_inputs"] = {
        "upstream_research_refs": ["RESEARCH-1", "RESEARCH-2"],
        "downstream_requirement_refs": ["REQ-A", "REQ-B"],
    }
    value["selected_prerequisite_actions"] = [{
        "action_id": "research-chain-reconciliation-durable-output",
        "required_capabilities": ["durable_artifact_write"],
        "evidence_path": "RESEARCH_CHAIN_RECONCILIATION",
    }]
    return value


class ResearchChainReconcilerMaterializationTest(unittest.TestCase):
    def test_capability_is_research_owned_and_deterministically_bound(self) -> None:
        manifest = (ROOT / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
        system = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        self.assertRegex(manifest, r"(?m)^  reconcile_research_chain: research_chain_reconciliation$")
        self.assertRegex(manifest, r"(?m)^  research_chain_reconciliation: engines/research/workflows/research-chain-reconciliation\.md$")
        self.assertIn("- reconcile_research_chain", system)
        self.assertIn("| `reconcile_research_chain` | `research` |", router)
        self.assertNotIn("engine_id: research-reconciler", system)

    def test_artifact_uses_common_envelope_and_required_control_fields(self) -> None:
        schema = load_schema()
        envelope = {
            "artifact_type", "artifact_id", "produced_by_role", "assignment_id",
            "input_state_ref", "status", "provenance", "related_artifacts",
        }
        self.assertTrue(envelope.issubset(set(schema["required"])))
        self.assertTrue(schema_accepts(base_reconciliation(), schema))
        malformed = base_reconciliation()
        malformed.pop("provenance")
        self.assertFalse(schema_accepts(malformed, schema))

    def test_requirement_specific_readiness_and_multiple_independent_results(self) -> None:
        artifact = base_reconciliation()
        states = {item["requirement_ref"]: item["state"] for item in artifact["requirement_evaluations"]}
        self.assertEqual(states, {"REQ-A": "SATISFIED", "REQ-B": "BLOCKED"})
        supports = {item["requirement_ref"]: item["supporting_research_refs"] for item in artifact["requirement_evaluations"]}
        self.assertEqual(supports["REQ-A"], ["RESEARCH-1"])
        self.assertEqual(supports["REQ-B"], ["RESEARCH-2"])
        self.assertNotIn("complete", {key.lower() for key in artifact})
        self.assertTrue(schema_accepts(artifact, load_schema()))

    def test_partial_satisfaction_does_not_become_global_complete(self) -> None:
        artifact = base_reconciliation()
        self.assertEqual(artifact["satisfied_requirement_refs"], ["REQ-A"])
        self.assertEqual(artifact["blocked_requirement_refs"], ["REQ-B"])
        self.assertEqual(artifact["status"], "PARTIAL")

    def test_acceptable_unknown_stops_repeat(self) -> None:
        artifact = base_reconciliation()
        artifact["requirement_evaluations"][1]["state"] = "ACCEPTABLE_UNKNOWN"
        artifact["unresolved_gaps"][0]["classification"] = "ACCEPTABLE_UNKNOWN"
        artifact["unresolved_gaps"][0]["continuation"] = "NO_RESEARCH"
        artifact["blocked_requirement_refs"] = []
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertEqual(artifact["next_research_frontier"], [])

    def test_evidence_ceiling_blocks_new_frontier(self) -> None:
        artifact = base_reconciliation()
        artifact["requirement_evaluations"][1]["state"] = "EVIDENCE_CEILING"
        artifact["unresolved_gaps"][0]["classification"] = "EVIDENCE_CEILING"
        artifact["unresolved_gaps"][0]["continuation"] = "DEFER"
        artifact["evidence_ceilings"] = [{
            "ceiling_id": "CEIL-1",
            "requirement_ref": "REQ-B",
            "supporting_research_refs": ["RESEARCH-2"],
            "reason": "Bounded available sources cannot materially improve the claim.",
            "disposition": "ACCEPT_BOUNDED_UNCERTAINTY",
            "further_research_justified": False,
        }]
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertFalse(artifact["evidence_ceilings"][0]["further_research_justified"])
        self.assertEqual(artifact["next_research_frontier"], [])

    def test_superseded_blocker_is_historical_not_active(self) -> None:
        artifact = base_reconciliation()
        artifact["requirement_evaluations"][1]["state"] = "SUPERSEDED"
        artifact["unresolved_gaps"][0]["classification"] = "SUPERSEDED_REQUIREMENT"
        artifact["unresolved_gaps"][0]["active"] = False
        artifact["unresolved_gaps"][0]["continuation"] = "NO_RESEARCH"
        artifact["supersessions"] = [{
            "superseded_ref": "RESEARCH-2",
            "superseded_by_ref": "RESEARCH-3",
            "reason": "Newer authoritative output resolved the old blocker.",
            "active_authority": False,
        }]
        artifact["blocked_requirement_refs"] = []
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertFalse(artifact["supersessions"][0]["active_authority"])

    def test_owner_preference_is_not_research_continuation(self) -> None:
        artifact = base_reconciliation()
        artifact["status"] = "OWNER_DECISION_REQUIRED"
        artifact["owner_input_required"] = True
        artifact["requirement_evaluations"][1]["state"] = "OWNER_DECISION_REQUIRED"
        artifact["unresolved_gaps"][0]["classification"] = "OWNER_PREFERENCE_OR_AUTHORITY"
        artifact["unresolved_gaps"][0]["continuation"] = "OWNER_GATE"
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertEqual(artifact["next_research_frontier"], [])

    def test_bounded_new_research_candidate_is_candidate_only(self) -> None:
        artifact = base_reconciliation()
        artifact["unresolved_gaps"][0]["classification"] = "BOUNDED_NEW_RESEARCH_CANDIDATE"
        artifact["unresolved_gaps"][0]["continuation"] = "BOUNDED_NEW_RESEARCH_CANDIDATE"
        artifact["next_research_frontier"] = [{
            "candidate_id": "NEXT-1",
            "requirement_ref": "REQ-B",
            "question": "Which bounded external source resolves the remaining exact fact?",
            "justification": "The remaining dependency is consequential and useful bounded methods remain.",
            "prior_gap_ref": "GAP-B",
            "narrowed_by_evidence_refs": ["RESEARCH-2"],
            "method_available": True,
            "evidence_ceiling_absent": True,
            "owner_preference_absent": True,
            "dispatch_status": "CANDIDATE_ONLY",
        }]
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertEqual(artifact["next_research_frontier"][0]["dispatch_status"], "CANDIDATE_ONLY")

    def test_method_or_artifact_defect_is_not_more_research(self) -> None:
        artifact = base_reconciliation()
        artifact["unresolved_gaps"][0]["classification"] = "METHOD_OR_ARTIFACT_DEFECT"
        artifact["unresolved_gaps"][0]["continuation"] = "NO_RESEARCH"
        self.assertTrue(schema_accepts(artifact, load_schema()))
        self.assertEqual(artifact["next_research_frontier"], [])

    def test_missing_or_duplicate_upstream_ref_fails_closed_structurally(self) -> None:
        schema = load_schema()
        missing = base_reconciliation()
        missing["upstream_research_refs"] = []
        self.assertFalse(schema_accepts(missing, schema))
        duplicate = base_reconciliation()
        duplicate["upstream_research_refs"] = ["RESEARCH-1", "RESEARCH-1"]
        self.assertFalse(schema_accepts(duplicate, schema))

    def test_gap_classes_are_closed_and_no_generic_repeat_state_exists(self) -> None:
        schema = load_schema()
        gap_classes = set(schema["$defs"]["gap"]["properties"]["classification"]["enum"])
        self.assertEqual(gap_classes, {
            "CONSEQUENTIAL_BLOCKER", "ACCEPTABLE_UNKNOWN", "EVIDENCE_CEILING",
            "SUPERSEDED_REQUIREMENT", "OWNER_PREFERENCE_OR_AUTHORITY",
            "METHOD_OR_ARTIFACT_DEFECT", "OUTSIDE_CURRENT_SCOPE",
            "BOUNDED_NEW_RESEARCH_CANDIDATE",
        })
        self.assertNotIn("REPEAT_RESEARCH", gap_classes)

    def test_authority_flags_block_direct_execution_dispatch_and_canon_mutation(self) -> None:
        props = load_schema()["properties"]
        self.assertEqual(props["research_execution_authority"]["const"], False)
        self.assertEqual(props["direct_dispatch_authority"]["const"], False)
        self.assertEqual(props["canon_mutation_authority"]["const"], False)

    def test_workflow_and_skill_encode_fail_closed_and_no_auto_repeat(self) -> None:
        workflow = (ROOT / "engines/research/workflows/research-chain-reconciliation.md").read_text(encoding="utf-8")
        skill = (ROOT / "engines/research/skills/reconcile-research-chain/SKILL.md").read_text(encoding="utf-8")
        for token in (
            "Fail closed", "GAP != REPEAT_RESEARCH", "EVIDENCE_CEILING",
            "OWNER_PREFERENCE_OR_AUTHORITY", "CANDIDATE_ONLY",
            "never calls spawn/dispatch", "never calls a Canon mutation gate",
        ):
            self.assertIn(token, workflow + "\n" + skill)

    def test_reconciler_does_not_require_research_work_package_admission(self) -> None:
        value = reconciliation_bundle()
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertNotIn("research_admission", result)
        self.assertEqual(
            result["assignment"]["research_reconciliation_inputs"],
            value["assignment_draft_semantics"]["research_reconciliation_inputs"],
        )
        self.assertIn("durable_artifact_write", result["assignment_admissibility"]["required_capabilities"])
        self.assertIn("RESEARCH-1", result["assignment"]["related_artifacts"])
        self.assertIn("RESEARCH-2", result["assignment"]["related_artifacts"])

    def test_reconciler_missing_exact_inputs_fails_closed(self) -> None:
        value = bundle("research", "reconcile_research_chain", "research_chain_reconciliation")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "RESEARCH_RECONCILIATION_INPUT_REQUIRED"), result)

    def test_reconciler_unresolved_upstream_ref_fails_closed(self) -> None:
        value = reconciliation_bundle()
        value["assignment_draft_semantics"]["research_reconciliation_inputs"]["upstream_research_refs"] = ["RESEARCH-MISSING"]
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "RESEARCH_RECONCILIATION_UPSTREAM_UNRESOLVED"), result)

    def test_reconciler_missing_upstream_provenance_fails_closed(self) -> None:
        value = reconciliation_bundle()
        next(item for item in value["artifacts"] if item.get("artifact_id") == "RESEARCH-1")["provenance"] = []
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "RESEARCH_RECONCILIATION_UPSTREAM_PROVENANCE_MISSING"), result)

    def test_reconciler_requires_durable_output_mechanic(self) -> None:
        value = reconciliation_bundle()
        value["selected_prerequisite_actions"] = []
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "RESEARCH_RECONCILIATION_DURABLE_OUTPUT_REQUIRED"), result)

    def test_reconciler_workflow_identity_cannot_bypass_research_admission(self) -> None:
        value = reconciliation_bundle()
        value["decision"]["workflow_id"] = "machine-only-execution"
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]),
                         ("ESCALATE", "RESEARCH_CONTROL_WORKFLOW_IDENTITY_MISMATCH"), result)

    def test_default_research_execution_admission_regression(self) -> None:
        value = bundle("research", "execute_research_work", "machine-only-execution")
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "RESEARCH_ADMISSION_REQUIRED"), result)
        default_workflow = (ROOT / "engines/research/workflows/default-machine-research.md").read_text(encoding="utf-8")
        self.assertIn("validate_work_package", default_workflow)
        self.assertIn("admit_work_package", (ROOT / "tools/resolver_spawn.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
