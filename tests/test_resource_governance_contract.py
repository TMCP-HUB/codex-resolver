from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = [
    "schemas/resource-estimate.schema.json",
    "schemas/resource-grant.schema.json",
    "schemas/resource-admission.schema.json",
    "schemas/usage-event.schema.json",
    "schemas/run-accounting.schema.json",
]
RESOURCE_CLASSES = ["MODEL_INFERENCE", "REMOTE_CI", "REMOTE_BROWSER", "GPU_COMPUTE", "PAID_TOOL", "EXTERNAL_API"]
DIMENSIONS = ["USD", "RUNNER_MINUTES", "GPU_SECONDS", "TOKENS", "MODEL_CALLS", "TOOL_CALLS", "AGENT_SPAWNS"]
RESOURCE_IDENTIFIER_PATTERN = r"^[A-Z][A-Z0-9_]*$"
LIMIT_MODES = ["HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"]
METERING = ["AUTHORITATIVE_ACTUAL", "NORMALIZED_ACTUAL", "ESTIMATED", "UNKNOWN"]


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def refs(value: object):
    if isinstance(value, dict):
        if isinstance(value.get("$ref"), str):
            yield value["$ref"]
        for nested in value.values():
            yield from refs(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from refs(nested)


def resolve_local(schema: dict, ref: str) -> object:
    if not ref.startswith("#/"):
        raise AssertionError(f"non-local ref: {ref}")
    current: object = schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise AssertionError(f"unresolved ref: {ref}")
        current = current[token]
    return current


def schema_accepts(value: object, schema: dict) -> bool:
    """Execute the bounded Draft 2020-12 keyword subset used by RG-01 regressions."""

    def valid(instance: object, rule: dict) -> bool:
        if "$ref" in rule:
            target = resolve_local(schema, rule["$ref"])
            return isinstance(target, dict) and valid(instance, target)
        if "allOf" in rule and not all(valid(instance, part) for part in rule["allOf"]):
            return False
        if "not" in rule and valid(instance, rule["not"]):
            return False
        if "if" in rule and valid(instance, rule["if"]) and not valid(instance, rule.get("then", {})):
            return False
        if "const" in rule and instance != rule["const"]:
            return False
        if "enum" in rule and instance not in rule["enum"]:
            return False

        kind = rule.get("type")
        kinds = kind if isinstance(kind, list) else [kind] if kind else []
        if kinds:
            def is_number(x: object) -> bool:
                return isinstance(x, (int, float)) and not isinstance(x, bool)

            checks = {
                "object": lambda x: isinstance(x, dict),
                "array": lambda x: isinstance(x, list),
                "string": lambda x: isinstance(x, str),
                "null": lambda x: x is None,
                "boolean": lambda x: isinstance(x, bool),
                "number": is_number,
                "integer": lambda x: is_number(x) and (isinstance(x, int) or (math.isfinite(x) and x.is_integer())),
            }
            if not any(name in checks and checks[name](instance) for name in kinds):
                return False

        if isinstance(instance, str):
            if len(instance) < rule.get("minLength", 0):
                return False
            if "pattern" in rule and re.fullmatch(rule["pattern"], instance) is None:
                return False

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in rule and instance < rule["minimum"]:
                return False
            if "maximum" in rule and instance > rule["maximum"]:
                return False
            if "exclusiveMinimum" in rule and instance <= rule["exclusiveMinimum"]:
                return False

        if isinstance(instance, list):
            if len(instance) < rule.get("minItems", 0) or len(instance) > rule.get("maxItems", 10**9):
                return False
            if rule.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in instance}) != len(instance):
                return False
            if "items" in rule and not all(valid(item, rule["items"]) for item in instance):
                return False
            if "contains" in rule:
                matches = sum(valid(item, rule["contains"]) for item in instance)
                if matches < rule.get("minContains", 1) or matches > rule.get("maxContains", 10**9):
                    return False

        if isinstance(instance, dict):
            if any(name not in instance for name in rule.get("required", [])):
                return False
            properties = rule.get("properties", {})
            if rule.get("additionalProperties") is False and any(name not in properties for name in instance):
                return False
            if any(name in instance and not valid(instance[name], child) for name, child in properties.items()):
                return False

        return True

    return valid(value, schema)


def limit_map(grant: dict) -> dict[tuple[str, str], dict]:
    out = {}
    for item in grant["limits"]:
        key = (item["resource_class"], item["dimension"])
        if key in out:
            raise AssertionError(f"duplicate limit key: {key}")
        out[key] = item
    return out


def narrows(
    parent: dict,
    child: dict,
    proven_scope_relations: set[tuple[str, str]] | None = None,
) -> bool:
    """Reference-only RG-01 narrowing predicate; not a runtime ledger implementation."""
    mode_order = {
        "HARD_LIMIT": {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
        "RESERVABLE_LIMIT": {"RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
        "OBSERVATION_ONLY": {"OBSERVATION_ONLY"},
    }
    relations = proven_scope_relations or set()
    parent_scope = parent["scope"]["scope_ref"]
    child_scope = child["scope"]["scope_ref"]
    if child_scope != parent_scope and (child_scope, parent_scope) not in relations:
        return False
    if not set(child["scope"]["resource_classes"]).issubset(parent["scope"]["resource_classes"]):
        return False
    for binding in ("candidate_ref", "route_ref"):
        if parent["scope"].get(binding) is not None and child["scope"].get(binding) != parent["scope"].get(binding):
            return False
    if parent.get("attempt_limit") is not None and (
        child.get("attempt_limit") is None or child["attempt_limit"] > parent["attempt_limit"]
    ):
        return False
    if parent.get("valid_until") is not None:
        p = datetime.fromisoformat(parent["valid_until"].replace("Z", "+00:00"))
        c = datetime.fromisoformat(child["valid_until"].replace("Z", "+00:00")) if child.get("valid_until") else None
        if c is None or c > p:
            return False
    try:
        parents, children = limit_map(parent), limit_map(child)
    except AssertionError:
        return False
    for key, child_limit in children.items():
        parent_limit = parents.get(key)
        if parent_limit is None or child_limit["limit_mode"] not in mode_order[parent_limit["limit_mode"]]:
            return False
        if child_limit["limit_mode"] == "OBSERVATION_ONLY":
            continue
        if parent_limit["limit_mode"] == "OBSERVATION_ONLY":
            return False
        if float(child_limit["ordinary_limit"]) > float(parent_limit["ordinary_limit"]):
            return False
        if float(child_limit["finalization_reserve"]) > float(parent_limit["finalization_reserve"]):
            return False
    return True


def valid_admission(evaluation: dict) -> dict:
    return {
        "artifact_type": "RESOURCE_ADMISSION",
        "artifact_id": "RA-1",
        "produced_by_role": "control-director",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "ADMISSIBLE",
        "provenance": ["proof:1"],
        "related_artifacts": [],
        "compiled_assignment_ref": "CA-1",
        "assignment_admissibility_ref": "AA-1",
        "route_ref": "ROUTE-1",
        "resource_estimate_ref": "RE-1",
        "resource_grant_ref": "RG-1",
        "availability_evidence_refs": [],
        "evaluations": [evaluation],
        "blocking_reasons": [],
        "unknown_resource_state": "KNOWN",
    }


def valid_usage_event() -> dict:
    return {
        "artifact_type": "USAGE_EVENT",
        "artifact_id": "UE-1",
        "produced_by_role": "executor",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "RECORDED",
        "provenance": ["provider-usage:1"],
        "related_artifacts": [],
        "run_id": "RUN-1",
        "operation_ref": "OP-1",
        "agent_id": "AGENT-1",
        "parent_agent_id": None,
        "resource_class": "MODEL_INFERENCE",
        "dimension": "TOKENS",
        "quantity": 100,
        "metering_quality": "AUTHORITATIVE_ACTUAL",
        "unknown_resource_state": "KNOWN",
        "measurement_source_ref": "meter:provider-usage-1",
        "rate_or_quota_revision_ref": None,
        "started_at": None,
        "finished_at": None,
    }


def timing_measurement(seconds: float | None, quality: str, unknown_state: str, source: str | None) -> dict:
    return {
        "seconds": seconds,
        "metering_quality": quality,
        "unknown_resource_state": unknown_state,
        "measurement_source_ref": source,
    }


def valid_run_accounting(wall: dict, aggregate_machine: dict) -> dict:
    return {
        "artifact_type": "RUN_ACCOUNTING",
        "artifact_id": "RUN-ACCOUNTING-1",
        "produced_by_role": "executor",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "COMPLETE",
        "provenance": ["run:1"],
        "related_artifacts": [],
        "run_id": "RUN-1",
        "resource_estimate_ref": "RE-1",
        "resource_grant_ref": "RG-1",
        "resource_admission_ref": "RA-1",
        "usage_event_refs": [],
        "totals": [],
        "timing": {"wall": wall, "aggregate_machine": aggregate_machine},
        "estimate_comparisons": [],
        "exhaustion_state": "NOT_EXHAUSTED",
        "unknown_resource_state": "KNOWN",
        "finalization_reserve_used": False,
        "termination_reason": "COMPLETED",
    }


class ResourceGovernanceContractTest(unittest.TestCase):
    def test_core_schemas_are_structurally_self_contained(self) -> None:
        for rel in SCHEMAS:
            schema = load(rel)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])
            for ref in refs(schema):
                resolve_local(schema, ref)

    def test_common_vocabulary_is_consistent_and_provider_neutral(self) -> None:
        for rel in SCHEMAS:
            defs = load(rel)["$defs"]
            for key, baseline in [("resourceClass", RESOURCE_CLASSES), ("dimension", DIMENSIONS)]:
                namespace = defs[key]
                self.assertEqual(namespace["type"], "string")
                self.assertEqual(namespace["pattern"], RESOURCE_IDENTIFIER_PATTERN)
                self.assertEqual(namespace["examples"], baseline)
                self.assertNotIn("enum", namespace)
            if "limitMode" in defs:
                self.assertEqual(defs["limitMode"]["enum"], LIMIT_MODES)
            if "meteringQuality" in defs:
                self.assertEqual(defs["meteringQuality"]["enum"], METERING)
        combined = (
            (ROOT / "contracts/RESOURCE_GOVERNANCE_CONTRACT.md").read_text(encoding="utf-8")
            + (ROOT / "protocols/resource-accounting.md").read_text(encoding="utf-8")
            + "".join(json.dumps(load(rel)) for rel in SCHEMAS)
        )
        for forbidden in ["LiteLLM", "OpenAI", "Anthropic", "Gemini", "Playwright", "Monte Carlo", "SQLite", "Postgres", "Redis"]:
            self.assertNotIn(forbidden, combined)

    def test_resource_identifier_namespaces_are_extensible(self) -> None:
        for rel in SCHEMAS:
            defs = load(rel)["$defs"]
            resource_class = defs["resourceClass"]
            dimension = defs["dimension"]
            self.assertNotIn("LOCAL_COMPUTE", resource_class["examples"])
            self.assertNotIn("CPU_SECONDS", dimension["examples"])
            self.assertIsNotNone(re.fullmatch(resource_class["pattern"], "LOCAL_COMPUTE"))
            self.assertIsNotNone(re.fullmatch(dimension["pattern"], "CPU_SECONDS"))
            self.assertIsNone(re.fullmatch(resource_class["pattern"], "provider-specific"))

    def test_estimate_requires_route_binding(self) -> None:
        self.assertIn("route_ref", load("schemas/resource-estimate.schema.json")["required"])

    def test_grant_separates_issuer_authority_and_parent_binding(self) -> None:
        schema = load("schemas/resource-grant.schema.json")
        self.assertEqual(schema["properties"]["issued_by"]["const"], "control-director")
        self.assertEqual(schema["$defs"]["authoritySource"]["required"], ["authority_type", "authority_ref"])
        self.assertIn("parent_grant_ref", schema["required"])
        self.assertEqual(len(schema["allOf"]), 2)

    def test_parent_child_authority_is_monotonic(self) -> None:
        parent = {
            "scope": {"scope_ref": "project:p", "candidate_ref": None, "route_ref": None, "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"]},
            "limits": [
                {"resource_class": "MODEL_INFERENCE", "dimension": "USD", "limit_mode": "HARD_LIMIT", "ordinary_limit": 5.0, "finalization_reserve": 1.0},
                {"resource_class": "REMOTE_CI", "dimension": "RUNNER_MINUTES", "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 20.0, "finalization_reserve": 2.0},
            ],
            "attempt_limit": 4,
            "valid_until": "2026-12-31T00:00:00Z",
        }
        child = {
            "scope": {"scope_ref": "assignment:a", "candidate_ref": "candidate:c", "route_ref": "route:r", "resource_classes": ["MODEL_INFERENCE"]},
            "limits": [{"resource_class": "MODEL_INFERENCE", "dimension": "USD", "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 3.0, "finalization_reserve": 0.5}],
            "attempt_limit": 2,
            "valid_until": "2026-11-30T00:00:00Z",
        }
        scope_proof = {("assignment:a", "project:p")}
        self.assertTrue(narrows(parent, child, scope_proof))
        expanded = json.loads(json.dumps(child))
        expanded["limits"][0]["ordinary_limit"] = 7.0
        self.assertFalse(narrows(parent, expanded, scope_proof))

    def test_finalization_reserve_cannot_be_repurposed_as_ordinary_capacity(self) -> None:
        parent = {
            "scope": {"scope_ref": "scope:s", "candidate_ref": None, "route_ref": None, "resource_classes": ["MODEL_INFERENCE"]},
            "limits": [{"resource_class": "MODEL_INFERENCE", "dimension": "USD", "limit_mode": "HARD_LIMIT", "ordinary_limit": 5.0, "finalization_reserve": 1.0}],
            "attempt_limit": 3,
            "valid_until": None,
        }
        child = json.loads(json.dumps(parent))
        child["limits"][0]["ordinary_limit"] = 5.5
        child["limits"][0]["finalization_reserve"] = 0.5
        self.assertFalse(narrows(parent, child))

    def test_scope_expansion_or_unknown_scope_relation_fails_closed(self) -> None:
        parent = {
            "scope": {"scope_ref": "assignment:a", "candidate_ref": None, "route_ref": None, "resource_classes": ["MODEL_INFERENCE"]},
            "limits": [{"resource_class": "MODEL_INFERENCE", "dimension": "USD", "limit_mode": "HARD_LIMIT", "ordinary_limit": 5.0, "finalization_reserve": 1.0}],
            "attempt_limit": 3,
            "valid_until": None,
        }
        child = json.loads(json.dumps(parent))
        child["scope"]["scope_ref"] = "project:ALL"
        child["limits"][0]["ordinary_limit"] = 1.0
        self.assertFalse(narrows(parent, child))
        self.assertFalse(narrows(parent, child, {("assignment:a", "project:ALL")}))
        proven_narrower = json.loads(json.dumps(parent))
        proven_narrower["scope"]["scope_ref"] = "task:1"
        self.assertTrue(narrows(parent, proven_narrower, {("task:1", "assignment:a")}))

    def test_limit_modes_multidimensional_and_finalization_are_explicit(self) -> None:
        schema = load("schemas/resource-grant.schema.json")
        self.assertEqual(schema["$defs"]["limitMode"]["enum"], LIMIT_MODES)
        limit = schema["$defs"]["limit"]
        self.assertIn("ordinary_limit", limit["required"])
        self.assertIn("finalization_reserve", limit["required"])
        policy = schema["properties"]["finalization_policy"]
        self.assertTrue(policy["properties"]["protected"]["const"])

    def test_unknown_is_not_zero(self) -> None:
        estimate = load("schemas/resource-estimate.schema.json")
        unknown_estimate = estimate["$defs"]["estimateItem"]["allOf"][1]["then"]["properties"]
        self.assertEqual(unknown_estimate["point_estimate"]["type"], "null")
        usage = load("schemas/usage-event.schema.json")
        unknown_usage = usage["allOf"][2]["then"]["properties"]
        self.assertEqual(unknown_usage["quantity"]["type"], "null")
        run = load("schemas/run-accounting.schema.json")
        unknown_timing = run["$defs"]["timingMeasurement"]["allOf"][2]["then"]["properties"]
        self.assertEqual(unknown_timing["seconds"]["type"], "null")
        self.assertNotIn('"default": 0', json.dumps([estimate, usage, run]))

    def test_observation_only_unknown_telemetry_is_non_blocking(self) -> None:
        schema = load("schemas/resource-admission.schema.json")
        observation = {
            "resource_class": "MODEL_INFERENCE",
            "dimension": "TOKENS",
            "limit_mode": "OBSERVATION_ONLY",
            "estimated_requirement": None,
            "available_amount": None,
            "verdict": "ADMISSIBLE",
            "reason": "OBSERVATION_ONLY_NON_BLOCKING",
            "unknown_resource_state": "METERING_UNAVAILABLE",
        }
        self.assertTrue(schema_accepts(valid_admission(observation), schema))
        reversed_semantics = json.loads(json.dumps(observation))
        reversed_semantics.update(verdict="NOT_ADMISSIBLE", reason="UNKNOWN_REQUIRED_RESOURCE")
        self.assertFalse(schema_accepts(valid_admission(reversed_semantics), schema))

    def test_blocking_admission_still_fails_closed(self) -> None:
        schema = load("schemas/resource-admission.schema.json")
        blocking_unknown = {
            "resource_class": "REMOTE_CI",
            "dimension": "RUNNER_MINUTES",
            "limit_mode": "RESERVABLE_LIMIT",
            "estimated_requirement": 8,
            "available_amount": None,
            "verdict": "ADMISSIBLE",
            "reason": "AUTHORIZED_AND_AVAILABLE",
            "unknown_resource_state": "AVAILABILITY_UNKNOWN",
        }
        self.assertFalse(schema_accepts(valid_admission(blocking_unknown), schema))

    def test_admission_can_represent_missing_inputs_fail_closed(self) -> None:
        schema = load("schemas/resource-admission.schema.json")
        self.assertEqual(set(schema["properties"]["resource_estimate_ref"]["type"]), {"string", "null"})
        self.assertEqual(set(schema["properties"]["resource_grant_ref"]["type"]), {"string", "null"})
        reasons = schema["$defs"]["blockingReason"]["enum"]
        self.assertIn("GRANT_MISSING", reasons)
        self.assertIn("ESTIMATE_MISSING", reasons)
        self.assertIn("UNCLASSIFIED_METERED_SIDE_EFFECT", reasons)

    def test_authoritative_actual_requires_measurement_source(self) -> None:
        schema = load("schemas/usage-event.schema.json")
        event = valid_usage_event()
        self.assertTrue(schema_accepts(event, schema))
        missing_source = json.loads(json.dumps(event))
        missing_source["measurement_source_ref"] = None
        self.assertFalse(schema_accepts(missing_source, schema))

    def test_run_accounting_timing_supports_asymmetric_evidence_quality(self) -> None:
        schema = load("schemas/run-accounting.schema.json")
        authoritative = timing_measurement(41.7, "AUTHORITATIVE_ACTUAL", "KNOWN", "clock:run-1")
        unknown = timing_measurement(None, "UNKNOWN", "METERING_UNAVAILABLE", None)
        estimated = timing_measurement(37.2, "ESTIMATED", "KNOWN", None)
        self.assertTrue(schema_accepts(valid_run_accounting(authoritative, unknown), schema))
        self.assertTrue(schema_accepts(valid_run_accounting(unknown, estimated), schema))

    def test_unknown_timing_never_uses_numeric_sentinel(self) -> None:
        schema = load("schemas/run-accounting.schema.json")
        valid_unknown = timing_measurement(None, "UNKNOWN", "ACTUAL_UNKNOWN", None)
        for side in ("wall", "aggregate_machine"):
            for seconds in (0, 3.5):
                with self.subTest(side=side, seconds=seconds):
                    invalid = timing_measurement(seconds, "UNKNOWN", "ACTUAL_UNKNOWN", None)
                    timing = {"wall": valid_unknown, "aggregate_machine": valid_unknown}
                    timing[side] = invalid
                    self.assertFalse(schema_accepts(valid_run_accounting(timing["wall"], timing["aggregate_machine"]), schema))

    def test_authoritative_timing_requires_numeric_known_sourced_measurement(self) -> None:
        schema = load("schemas/run-accounting.schema.json")
        other = timing_measurement(None, "UNKNOWN", "METERING_UNAVAILABLE", None)
        valid = timing_measurement(1.0, "AUTHORITATIVE_ACTUAL", "KNOWN", "clock:1")
        self.assertTrue(schema_accepts(valid_run_accounting(valid, other), schema))
        invalids = [
            timing_measurement(None, "AUTHORITATIVE_ACTUAL", "KNOWN", "clock:1"),
            timing_measurement(1.0, "AUTHORITATIVE_ACTUAL", "KNOWN", None),
            timing_measurement(1.0, "AUTHORITATIVE_ACTUAL", "ACTUAL_UNKNOWN", "clock:1"),
        ]
        for side in ("wall", "aggregate_machine"):
            for invalid in invalids:
                with self.subTest(side=side, invalid=invalid):
                    timing = {"wall": valid, "aggregate_machine": valid}
                    timing[side] = invalid
                    self.assertFalse(schema_accepts(valid_run_accounting(timing["wall"], timing["aggregate_machine"]), schema))

    def test_estimated_timing_numeric_known_is_valid_independently(self) -> None:
        schema = load("schemas/run-accounting.schema.json")
        estimated = timing_measurement(9.25, "ESTIMATED", "KNOWN", None)
        unknown = timing_measurement(None, "UNKNOWN", "METERING_UNAVAILABLE", None)
        self.assertTrue(schema_accepts(valid_run_accounting(estimated, unknown), schema))
        self.assertTrue(schema_accepts(valid_run_accounting(unknown, estimated), schema))

    def test_run_accounting_timing_has_no_shared_quality_or_default_zero(self) -> None:
        schema = load("schemas/run-accounting.schema.json")
        timing = schema["properties"]["timing"]
        self.assertEqual(timing["required"], ["wall", "aggregate_machine"])
        self.assertNotIn("metering_quality", timing["properties"])
        measurement = schema["$defs"]["timingMeasurement"]
        for field in ["seconds", "metering_quality", "unknown_resource_state", "measurement_source_ref"]:
            self.assertIn(field, measurement["required"])
        self.assertNotIn('"default"', json.dumps(schema))

    def test_usage_and_run_accounting_preserve_required_distinctions(self) -> None:
        usage = load("schemas/usage-event.schema.json")
        for field in ["quantity", "metering_quality", "measurement_source_ref", "rate_or_quota_revision_ref", "provenance"]:
            self.assertIn(field, usage["required"])
        run = load("schemas/run-accounting.schema.json")
        for field in ["resource_estimate_ref", "totals", "estimate_comparisons"]:
            self.assertIn(field, run["required"])
        timing = run["properties"]["timing"]
        self.assertIn("wall", timing["required"])
        self.assertIn("aggregate_machine", timing["required"])

    def test_contract_gap_path_is_frozen_without_runtime_mechanism(self) -> None:
        contract = (ROOT / "contracts/RESOURCE_GOVERNANCE_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("IMPLEMENTATION CONVENIENCE", contract)
        self.assertIn("CONTRACT DEFECT", contract)
        self.assertIn("CONTRACT_GAP_FOUND", contract)
        self.assertIn("CHILD_SCOPE ⊆ PARENT_SCOPE", contract)
        self.assertIn("CHILD_FINALIZATION_RESERVE <= PARENT_FINALIZATION_RESERVE", contract)

    def test_system_manifest_registers_resource_governance_contract(self) -> None:
        manifest = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertIn("resource_governance: contracts/RESOURCE_GOVERNANCE_CONTRACT.md", manifest)


if __name__ == "__main__":
    unittest.main()
