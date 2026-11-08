from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_UP, localcontext
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests.test_resource_governance_contract import load, schema_accepts
from tools.resource_forecast import ResourceForecastError, build_resource_estimate


ROOT = Path(__file__).resolve().parents[1]


def requested(resource_class: str = "MODEL_INFERENCE", dimension: str = "TOKENS") -> dict[str, str]:
    return {"resource_class": resource_class, "dimension": dimension}


def observation(
    basis_ref: str,
    quantity: int | float | Decimal | None,
    *,
    resource_class: str = "MODEL_INFERENCE",
    dimension: str = "TOKENS",
    quality: str = "NORMALIZED_ACTUAL",
    source: str | None = None,
) -> dict[str, object]:
    return {
        "basis_ref": basis_ref,
        "resource_class": resource_class,
        "dimension": dimension,
        "quantity": quantity,
        "metering_quality": quality,
        "measurement_source_ref": source,
    }


def request(
    *,
    requested_resources: list[dict[str, str]] | None = None,
    observations: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "artifact_id": "RESOURCE-ESTIMATE-71",
        "produced_by_role": "resource-estimator",
        "assignment_id": "A-71",
        "input_state_ref": "STATE-71",
        "provenance": ["input:71", "history:selected"],
        "related_artifacts": ["RUN-ACCOUNTING-PRIOR"],
        "subject_ref": "SUBJECT-EXACT-71",
        "route_ref": "ROUTE-EXACT-71",
        "estimator_revision_ref": "RG-02-v1",
        "requested_resources": requested_resources or [requested()],
        "observations": observations or [],
    }


def estimate_for(artifact: dict[str, object], resource_class: str, dimension: str) -> dict[str, object]:
    for item in artifact["estimates"]:  # type: ignore[index]
        if item["resource_class"] == resource_class and item["dimension"] == dimension:  # type: ignore[index]
            return item  # type: ignore[return-value]
    raise AssertionError(f"missing estimate {resource_class}/{dimension}")


class ResourceForecastTest(unittest.TestCase):
    def test_estimator_carries_a_normalized_shared_forecast_with_its_basis(self) -> None:
        payload = request(
            requested_resources=[requested("MODEL_INFERENCE", "USD"), requested("REMOTE_CI", "USD")],
            observations=[observation("MODEL-1", 6, dimension="USD"),
                          observation("CI-1", 6, resource_class="REMOTE_CI", dimension="USD")],
        )
        payload["shared_estimates"] = [{
            "grant_ref": "G-ROOT", "limit_id": "TOTAL", "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
            "estimate_state": "ESTIMATED", "upper_bound": 9, "basis_refs": ["NORMALIZED-TOTAL-1"],
        }]
        artifact = build_resource_estimate(payload)
        self.assertEqual(artifact["route_ref"], "ROUTE-EXACT-71")
        self.assertEqual(artifact["shared_estimates"][0]["upper_bound"], 9)
        self.assertIn("NORMALIZED-TOTAL-1", artifact["basis_refs"])
        self.assertEqual(artifact["status"], "ESTIMATED")
        self.assertTrue(schema_accepts(artifact, load("schemas/resource-estimate.schema.json")))

    def test_unknown_shared_forecast_stays_unknown_and_is_not_summed(self) -> None:
        payload = request(
            requested_resources=[requested("MODEL_INFERENCE", "USD"), requested("REMOTE_CI", "USD")],
            observations=[observation("MODEL-1", 6, dimension="USD"),
                          observation("CI-1", 6, resource_class="REMOTE_CI", dimension="USD")],
        )
        payload["shared_estimates"] = [{
            "grant_ref": "G-ROOT", "limit_id": "TOTAL", "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
            "estimate_state": "UNKNOWN", "upper_bound": None, "basis_refs": [],
        }]
        artifact = build_resource_estimate(payload)
        self.assertEqual(artifact["status"], "PARTIAL")
        self.assertIsNone(artifact["shared_estimates"][0]["upper_bound"])
        self.assertTrue(schema_accepts(artifact, load("schemas/resource-estimate.schema.json")))

    def test_group_bound_is_not_rounded_below_supplied_decimal(self) -> None:
        amount = Decimal("0.100000000000000000000000001")
        payload = request(observations=[observation("B-1", 1)])
        payload["shared_estimates"] = [{
            "grant_ref": "G-ROOT", "limit_id": "TOTAL", "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
            "estimate_state": "ESTIMATED", "upper_bound": amount, "basis_refs": ["TOTAL-BASIS"],
        }]
        artifact = build_resource_estimate(payload)
        self.assertGreaterEqual(Decimal(str(artifact["shared_estimates"][0]["upper_bound"])), amount)

    def test_component_upper_bound_is_not_rounded_below_known_historical_maximum(self) -> None:
        amount = Decimal("1.0000000000000000000000000001")
        artifact = build_resource_estimate(request(observations=[observation("B-1", amount)]))
        bound = estimate_for(artifact, "MODEL_INFERENCE", "TOKENS")["upper_bound"]
        self.assertGreaterEqual(Decimal(str(bound)), amount)

    def test_group_bound_rejects_boolean_and_nonfinite_quantities(self) -> None:
        payload = request()
        payload["shared_estimates"] = [{
            "grant_ref": "G-ROOT", "limit_id": "TOTAL", "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
            "estimate_state": "ESTIMATED", "upper_bound": True, "basis_refs": ["TOTAL-BASIS"],
        }]
        for invalid in (True, float("inf"), float("nan"), Decimal("-1")):
            with self.subTest(invalid=invalid), self.assertRaises(ResourceForecastError):
                payload["shared_estimates"][0]["upper_bound"] = invalid
                build_resource_estimate(payload)

    def test_exact_route_ref_is_preserved(self) -> None:
        artifact = build_resource_estimate(request())
        self.assertEqual(artifact["route_ref"], "ROUTE-EXACT-71")

    def test_exact_subject_ref_is_preserved(self) -> None:
        artifact = build_resource_estimate(request())
        self.assertEqual(artifact["subject_ref"], "SUBJECT-EXACT-71")

    def test_same_normalized_inputs_produce_identical_artifact(self) -> None:
        first = request(observations=[observation("B-1", 1), observation("B-2", 2)])
        second = copy.deepcopy(first)
        second["provenance"] = ["history:selected", "input:71", "input:71"]
        second["related_artifacts"] = ["RUN-ACCOUNTING-PRIOR", "RUN-ACCOUNTING-PRIOR"]
        self.assertEqual(build_resource_estimate(first), build_resource_estimate(second))

    def test_ambient_decimal_context_does_not_change_forecast(self) -> None:
        payload = request(
            observations=[
                observation("B-1", Decimal("1.111111111111111")),
                observation("B-2", Decimal("9.999999999999999")),
            ]
        )
        with localcontext() as context:
            context.prec = 10
            context.rounding = ROUND_DOWN
            low_precision = build_resource_estimate(payload)
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_UP
            high_precision = build_resource_estimate(payload)

        self.assertEqual(low_precision, high_precision)
        item = estimate_for(low_precision, "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(item["point_estimate"], 5.555555555555555)

    def test_ambient_decimal_context_does_not_change_mixed_scale_forecast(self) -> None:
        payload = request(
            observations=[
                observation("B-1", Decimal("0.0000001234567890123456789012345")),
                observation("B-2", Decimal("98765.432109876543210987654321")),
            ]
        )
        with localcontext() as context:
            context.prec = 7
            context.rounding = ROUND_UP
            narrow = build_resource_estimate(payload)
        with localcontext() as context:
            context.prec = 80
            context.rounding = ROUND_DOWN
            wide = build_resource_estimate(payload)

        self.assertEqual(narrow, wide)

    def test_observation_order_does_not_change_artifact(self) -> None:
        observations = [observation("B-1", 1), observation("B-2", 10), observation("B-3", 5)]
        forward = build_resource_estimate(request(observations=observations))
        reverse = build_resource_estimate(request(observations=list(reversed(observations))))
        self.assertEqual(forward, reverse)

    def test_requested_resource_order_does_not_change_artifact(self) -> None:
        resources = [requested("REMOTE_CI", "RUNNER_MINUTES"), requested("MODEL_INFERENCE", "TOKENS")]
        observations = [
            observation("B-1", 2),
            observation("B-2", 7, resource_class="REMOTE_CI", dimension="RUNNER_MINUTES"),
        ]
        forward = build_resource_estimate(request(requested_resources=resources, observations=observations))
        reverse = build_resource_estimate(request(requested_resources=list(reversed(resources)), observations=observations))
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [(x["resource_class"], x["dimension"]) for x in forward["estimates"]],  # type: ignore[index]
            [("MODEL_INFERENCE", "TOKENS"), ("REMOTE_CI", "RUNNER_MINUTES")],
        )

    def test_p10_p50_p90_exact_linear_interpolation(self) -> None:
        observations = [observation(f"B-{i}", value) for i, value in enumerate([0, 10, 20, 30], 1)]
        item = estimate_for(build_resource_estimate(request(observations=observations)), "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(
            item["quantiles"],
            [
                {"probability": 0.1, "quantity": 3},
                {"probability": 0.5, "quantity": 15},
                {"probability": 0.9, "quantity": 27},
            ],
        )

    def test_point_estimate_equals_p50(self) -> None:
        item = estimate_for(
            build_resource_estimate(request(observations=[observation("B-1", 1), observation("B-2", 9)])),
            "MODEL_INFERENCE",
            "TOKENS",
        )
        p50 = next(q["quantity"] for q in item["quantiles"] if q["probability"] == 0.5)  # type: ignore[index]
        self.assertEqual(item["point_estimate"], p50)

    def test_upper_bound_is_maximum_actual(self) -> None:
        item = estimate_for(
            build_resource_estimate(request(observations=[observation("B-1", 99), observation("B-2", 3)])),
            "MODEL_INFERENCE",
            "TOKENS",
        )
        self.assertEqual(item["upper_bound"], 99)

    def test_n1_behaves_correctly(self) -> None:
        item = estimate_for(build_resource_estimate(request(observations=[observation("B-1", 7)])), "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(item["point_estimate"], 7)
        self.assertEqual(item["upper_bound"], 7)
        self.assertEqual(item["historical_sample_count"], 1)
        self.assertEqual([q["quantity"] for q in item["quantiles"]], [7, 7, 7])  # type: ignore[index]

    def test_confidence_low_for_n1_through_4(self) -> None:
        for n in range(1, 5):
            with self.subTest(n=n):
                observations = [observation(f"B-{i}", i) for i in range(n)]
                item = estimate_for(build_resource_estimate(request(observations=observations)), "MODEL_INFERENCE", "TOKENS")
                self.assertEqual(item["confidence"], "LOW")

    def test_confidence_medium_for_n5_through_19(self) -> None:
        for n in (5, 19):
            with self.subTest(n=n):
                observations = [observation(f"B-{i}", i) for i in range(n)]
                item = estimate_for(build_resource_estimate(request(observations=observations)), "MODEL_INFERENCE", "TOKENS")
                self.assertEqual(item["confidence"], "MEDIUM")

    def test_confidence_high_for_n20_or_more(self) -> None:
        observations = [observation(f"B-{i}", i) for i in range(20)]
        item = estimate_for(build_resource_estimate(request(observations=observations)), "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(item["confidence"], "HIGH")

    def test_identical_duplicate_observation_is_counted_once(self) -> None:
        duplicate = observation("B-1", 5)
        item = estimate_for(
            build_resource_estimate(request(observations=[duplicate, copy.deepcopy(duplicate)])),
            "MODEL_INFERENCE",
            "TOKENS",
        )
        self.assertEqual(item["historical_sample_count"], 1)
        self.assertEqual(item["point_estimate"], 5)

    def test_conflicting_duplicate_durable_observation_fails_closed(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(observations=[observation("B-1", 5), observation("B-1", 6)]))

    def test_one_basis_may_contribute_separate_dimensions(self) -> None:
        artifact = build_resource_estimate(
            request(
                requested_resources=[requested("MODEL_INFERENCE", "TOKENS"), requested("MODEL_INFERENCE", "MODEL_CALLS")],
                observations=[
                    observation("RUN-1", 100, dimension="TOKENS"),
                    observation("RUN-1", 2, dimension="MODEL_CALLS"),
                ],
            )
        )
        self.assertEqual(estimate_for(artifact, "MODEL_INFERENCE", "TOKENS")["point_estimate"], 100)
        self.assertEqual(estimate_for(artifact, "MODEL_INFERENCE", "MODEL_CALLS")["point_estimate"], 2)
        self.assertEqual(artifact["basis_refs"], ["RUN-1"])

    def test_different_dimensions_never_mix_arithmetic(self) -> None:
        artifact = build_resource_estimate(
            request(
                requested_resources=[requested("MODEL_INFERENCE", "TOKENS"), requested("MODEL_INFERENCE", "MODEL_CALLS")],
                observations=[
                    observation("T-1", 1000, dimension="TOKENS"),
                    observation("C-1", 3, dimension="MODEL_CALLS"),
                ],
            )
        )
        self.assertEqual(estimate_for(artifact, "MODEL_INFERENCE", "TOKENS")["point_estimate"], 1000)
        self.assertEqual(estimate_for(artifact, "MODEL_INFERENCE", "MODEL_CALLS")["point_estimate"], 3)

    def test_authoritative_actual_requires_measurement_source(self) -> None:
        good = build_resource_estimate(
            request(observations=[observation("B-1", 4, quality="AUTHORITATIVE_ACTUAL", source="meter:1")])
        )
        self.assertEqual(estimate_for(good, "MODEL_INFERENCE", "TOKENS")["point_estimate"], 4)
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(
                request(observations=[observation("B-1", 4, quality="AUTHORITATIVE_ACTUAL", source=None)])
            )

    def test_normalized_actual_contributes(self) -> None:
        item = estimate_for(
            build_resource_estimate(request(observations=[observation("B-1", 4, quality="NORMALIZED_ACTUAL")])),
            "MODEL_INFERENCE",
            "TOKENS",
        )
        self.assertEqual(item["historical_sample_count"], 1)

    def test_estimated_history_does_not_contribute(self) -> None:
        artifact = build_resource_estimate(
            request(observations=[observation("B-1", 100, quality="ESTIMATED")])
        )
        item = estimate_for(artifact, "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(item["estimate_state"], "UNKNOWN")
        self.assertIsNone(item["historical_sample_count"])
        self.assertEqual(artifact["basis_refs"], [])

    def test_unknown_history_does_not_contribute(self) -> None:
        artifact = build_resource_estimate(
            request(observations=[observation("B-1", None, quality="UNKNOWN")])
        )
        item = estimate_for(artifact, "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(item["estimate_state"], "UNKNOWN")
        self.assertIsNone(item["historical_sample_count"])

    def test_unknown_never_becomes_numeric_zero(self) -> None:
        item = estimate_for(build_resource_estimate(request()), "MODEL_INFERENCE", "TOKENS")
        self.assertIsNone(item["point_estimate"])
        self.assertIsNone(item["upper_bound"])
        self.assertEqual(item["quantiles"], [])

    def test_negative_quantity_fails(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(observations=[observation("B-1", -1)]))

    def test_bool_quantity_fails(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(observations=[observation("B-1", True)]))

    def test_nan_and_infinity_fail(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ResourceForecastError):
                build_resource_estimate(request(observations=[observation("B-1", value)]))

    def test_unknown_with_numeric_quantity_fails(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(observations=[observation("B-1", 0, quality="UNKNOWN")]))

    def test_duplicate_requested_key_fails(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(requested_resources=[requested(), requested()]))

    def test_malformed_resource_identifier_fails(self) -> None:
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(request(requested_resources=[requested("provider-specific", "TOKENS")]))

    def test_blank_required_identity_fails(self) -> None:
        for field in ("artifact_id", "produced_by_role", "subject_ref", "route_ref", "estimator_revision_ref"):
            with self.subTest(field=field):
                req = request()
                req[field] = "   "
                with self.assertRaises(ResourceForecastError):
                    build_resource_estimate(req)

    def test_empty_provenance_and_requested_resources_fail(self) -> None:
        req = request()
        req["provenance"] = []
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(req)
        req = request()
        req["requested_resources"] = []
        with self.assertRaises(ResourceForecastError):
            build_resource_estimate(req)

    def test_all_known_requested_keys_status_estimated(self) -> None:
        artifact = build_resource_estimate(
            request(
                requested_resources=[requested(), requested("REMOTE_CI", "RUNNER_MINUTES")],
                observations=[
                    observation("B-1", 5),
                    observation("B-2", 10, resource_class="REMOTE_CI", dimension="RUNNER_MINUTES"),
                ],
            )
        )
        self.assertEqual(artifact["status"], "ESTIMATED")

    def test_mixed_known_unknown_status_partial(self) -> None:
        artifact = build_resource_estimate(
            request(
                requested_resources=[requested(), requested("REMOTE_CI", "RUNNER_MINUTES")],
                observations=[observation("B-1", 5)],
            )
        )
        self.assertEqual(artifact["status"], "PARTIAL")

    def test_all_unknown_status_unknown(self) -> None:
        artifact = build_resource_estimate(
            request(requested_resources=[requested(), requested("REMOTE_CI", "RUNNER_MINUTES")])
        )
        self.assertEqual(artifact["status"], "UNKNOWN")

    def test_basis_refs_include_only_actually_used_evidence(self) -> None:
        artifact = build_resource_estimate(
            request(
                observations=[
                    observation("USED", 5),
                    observation("ESTIMATE-ONLY", 50, quality="ESTIMATED"),
                    observation("UNKNOWN-ONLY", None, quality="UNKNOWN"),
                    observation("UNREQUESTED", 8, dimension="MODEL_CALLS"),
                ]
            )
        )
        self.assertEqual(artifact["basis_refs"], ["USED"])

    def test_no_random_or_time_dependent_artifact_identity(self) -> None:
        req = request(observations=[observation("B-1", 1)])
        first = build_resource_estimate(req)
        second = build_resource_estimate(req)
        self.assertEqual(first["artifact_id"], "RESOURCE-ESTIMATE-71")
        self.assertEqual(first, second)
        source = (ROOT / "tools/resource_forecast.py").read_text(encoding="utf-8")
        for forbidden in ("import random", "import time", "import datetime", "import uuid"):
            self.assertNotIn(forbidden, source)

    def test_output_validates_against_frozen_resource_estimate_schema(self) -> None:
        artifact = build_resource_estimate(
            request(
                requested_resources=[requested(), requested("REMOTE_CI", "RUNNER_MINUTES")],
                observations=[observation("B-1", 2)],
            )
        )
        self.assertTrue(schema_accepts(artifact, load("schemas/resource-estimate.schema.json")))

    def test_production_module_has_no_authority_or_external_runtime_behavior(self) -> None:
        source = (ROOT / "tools/resource_forecast.py").read_text(encoding="utf-8")
        for forbidden in (
            "RESOURCE_GRANT",
            "RESOURCE_ADMISSION",
            "sqlite3",
            "requests",
            "urllib",
            "http.client",
            "subprocess",
        ):
            self.assertNotIn(forbidden, source)

    def test_cli_reads_stdin_and_emits_canonical_json(self) -> None:
        payload = request(observations=[observation("B-1", 4)])
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/resource_forecast.py")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), build_resource_estimate(payload))
        self.assertTrue(proc.stdout.endswith("\n"))
        self.assertEqual(proc.stdout, json.dumps(json.loads(proc.stdout), indent=2, sort_keys=True) + "\n")

    def test_cli_malformed_input_fails_without_estimate(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/resource_forecast.py")],
            input="{not-json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        self.assertIn("resource_forecast: invalid JSON:", proc.stderr)

    def test_cli_reads_request_path(self) -> None:
        payload = request(observations=[observation("B-1", 6)])
        request_path = ROOT / "request-rg02-test.json"
        try:
            request_path.write_text(json.dumps(payload), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools/resource_forecast.py"), str(request_path)],
                text=True,
                capture_output=True,
                check=False,
            )
        finally:
            request_path.unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), build_resource_estimate(payload))

    def test_caller_supplied_top_level_identity_is_preserved(self) -> None:
        req = request()
        req["assignment_id"] = None
        req["input_state_ref"] = "STATE-EXACT"
        artifact = build_resource_estimate(req)
        self.assertEqual(artifact["artifact_id"], req["artifact_id"])
        self.assertEqual(artifact["produced_by_role"], req["produced_by_role"])
        self.assertIsNone(artifact["assignment_id"])
        self.assertEqual(artifact["input_state_ref"], "STATE-EXACT")
        self.assertEqual(artifact["estimator_revision_ref"], req["estimator_revision_ref"])


if __name__ == "__main__":
    unittest.main()

