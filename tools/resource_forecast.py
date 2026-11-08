#!/usr/bin/env python3
"""Deterministic route-bound RESOURCE_ESTIMATE producer for RG-02."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    Context,
    Decimal,
    InvalidOperation,
    ROUND_HALF_EVEN,
    localcontext,
)
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_METERING_QUALITIES = {
    "AUTHORITATIVE_ACTUAL",
    "NORMALIZED_ACTUAL",
    "ESTIMATED",
    "UNKNOWN",
}
_USABLE_ACTUAL_QUALITIES = {"AUTHORITATIVE_ACTUAL", "NORMALIZED_ACTUAL"}
_QUANTILES: tuple[tuple[str, Decimal], ...] = (
    ("P10", Decimal("0.10")),
    ("P50", Decimal("0.50")),
    ("P90", Decimal("0.90")),
)
_TOP_LEVEL_FIELDS = {
    "artifact_id",
    "produced_by_role",
    "assignment_id",
    "input_state_ref",
    "provenance",
    "related_artifacts",
    "subject_ref",
    "route_ref",
    "estimator_revision_ref",
    "requested_resources",
    "observations",
}
_REQUESTED_RESOURCE_FIELDS = {"resource_class", "dimension"}
_OBSERVATION_FIELDS = {
    "basis_ref",
    "resource_class",
    "dimension",
    "quantity",
    "metering_quality",
    "measurement_source_ref",
}
_SHARED_ESTIMATE_FIELDS = {
    "grant_ref", "limit_id", "resource_classes", "estimate_state", "upper_bound", "basis_refs",
}
_INTERPOLATION_GUARD_DIGITS = 4


class ResourceForecastError(ValueError):
    """Raised when the implementation-local request envelope is malformed."""


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ResourceForecastError(f"{name} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ResourceForecastError(f"{name} keys must be strings")
    return value


def _require_exact_fields(value: Mapping[str, object], expected: set[str], name: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing:
        raise ResourceForecastError(f"{name} missing required fields: {', '.join(missing)}")
    if extra:
        raise ResourceForecastError(f"{name} has unexpected fields: {', '.join(extra)}")


def _nonblank_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResourceForecastError(f"{name} must be a non-empty string")
    return value


def _nullable_string(value: object, name: str, *, nonblank_when_present: bool = False) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ResourceForecastError(f"{name} must be a string or null")
    if nonblank_when_present and not value.strip():
        raise ResourceForecastError(f"{name} must be non-empty when present")
    return value


def _string_list(value: object, name: str, *, nonempty: bool) -> list[str]:
    if not isinstance(value, list):
        raise ResourceForecastError(f"{name} must be an array")
    if nonempty and not value:
        raise ResourceForecastError(f"{name} must not be empty")
    out: list[str] = []
    for index, item in enumerate(value):
        out.append(_nonblank_string(item, f"{name}[{index}]"))
    return out


def _resource_identifier(value: object, name: str) -> str:
    identifier = _nonblank_string(value, name)
    if _IDENTIFIER_RE.fullmatch(identifier) is None:
        raise ResourceForecastError(f"{name} must match ^[A-Z][A-Z0-9_]*$")
    return identifier


def _decimal_quantity(value: object, name: str, *, allow_null: bool) -> Decimal | None:
    if value is None:
        if allow_null:
            return None
        raise ResourceForecastError(f"{name} must be a non-negative number")
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ResourceForecastError(f"{name} must be a non-negative number or null")
    try:
        quantity = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ResourceForecastError(f"{name} must be a finite non-negative number") from None
    if not quantity.is_finite():
        raise ResourceForecastError(f"{name} must be finite")
    if quantity < 0:
        raise ResourceForecastError(f"{name} must not be negative")
    if quantity == 0:
        return Decimal(0)
    return quantity


def _ordinary_json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    converted = float(value)
    if not math.isfinite(converted) or (converted == 0.0 and value != 0):
        raise ResourceForecastError("computed quantity is outside supported JSON numeric range")
    return converted


def _upper_json_number(value: Decimal) -> int | float:
    """Represent a supplied bound without rounding it below its actual value."""
    converted = _ordinary_json_number(value)
    if isinstance(converted, float) and Decimal(str(converted)) < value:
        converted = math.nextafter(converted, math.inf)
        if not math.isfinite(converted):
            raise ResourceForecastError("upper estimate is outside JSON numeric range")
    return converted


def _interpolation_precision(sorted_values: Sequence[Decimal], probability: Decimal) -> int:
    """Derive precision sufficient for exact finite empirical interpolation.

    The quantity span covers every decimal position from the greatest input
    position through the least input exponent. Probability scale covers the
    extra fractional positions introduced by the fixed empirical fraction.
    Index precision separately covers ``(n - 1) * p`` for any sample count.
    A small fixed guard keeps the rule conservative without relying on the
    caller process Decimal context.
    """
    nonzero_values = [value for value in sorted_values if value != 0]
    if nonzero_values:
        highest_position = max(value.adjusted() for value in nonzero_values)
        lowest_position = min(value.as_tuple().exponent for value in nonzero_values)
        quantity_span = highest_position - lowest_position + 1
    else:
        quantity_span = 1

    probability_tuple = probability.as_tuple()
    probability_scale = max(0, -probability_tuple.exponent)
    probability_digits = max(1, len(probability_tuple.digits))
    index_digits = len(str(max(1, len(sorted_values) - 1)))

    quantity_requirement = quantity_span + probability_scale
    index_requirement = index_digits + probability_digits
    return max(quantity_requirement, index_requirement) + _INTERPOLATION_GUARD_DIGITS


def _interpolated_quantile(sorted_values: Sequence[Decimal], probability: Decimal) -> Decimal:
    explicit_context = Context(
        prec=_interpolation_precision(sorted_values, probability),
        rounding=ROUND_HALF_EVEN,
        Emin=MIN_EMIN,
        Emax=MAX_EMAX,
    )
    with localcontext(explicit_context):
        index = Decimal(len(sorted_values) - 1) * probability
        lo = int(index.to_integral_value(rounding="ROUND_FLOOR"))
        hi = int(index.to_integral_value(rounding="ROUND_CEILING"))
        if lo == hi:
            return sorted_values[lo]
        fraction = index - Decimal(lo)
        return sorted_values[lo] + fraction * (sorted_values[hi] - sorted_values[lo])


def _confidence(sample_count: int) -> str:
    if sample_count <= 4:
        return "LOW"
    if sample_count <= 19:
        return "MEDIUM"
    return "HIGH"


def _normalize_requested_resources(value: object) -> list[tuple[str, str]]:
    if not isinstance(value, list) or not value:
        raise ResourceForecastError("requested_resources must be a non-empty array")
    seen: set[tuple[str, str]] = set()
    keys: list[tuple[str, str]] = []
    for index, raw in enumerate(value):
        item = _require_mapping(raw, f"requested_resources[{index}]")
        _require_exact_fields(item, _REQUESTED_RESOURCE_FIELDS, f"requested_resources[{index}]")
        key = (
            _resource_identifier(item["resource_class"], f"requested_resources[{index}].resource_class"),
            _resource_identifier(item["dimension"], f"requested_resources[{index}].dimension"),
        )
        if key in seen:
            raise ResourceForecastError(f"duplicate requested resource key: {key[0]}/{key[1]}")
        seen.add(key)
        keys.append(key)
    return sorted(keys)


def _normalize_observations(value: object) -> dict[tuple[str, str, str], tuple[Decimal | None, str, str | None]]:
    if not isinstance(value, list):
        raise ResourceForecastError("observations must be an array")
    observations: dict[tuple[str, str, str], tuple[Decimal | None, str, str | None]] = {}
    for index, raw in enumerate(value):
        item = _require_mapping(raw, f"observations[{index}]")
        _require_exact_fields(item, _OBSERVATION_FIELDS, f"observations[{index}]")
        basis_ref = _nonblank_string(item["basis_ref"], f"observations[{index}].basis_ref")
        resource_class = _resource_identifier(item["resource_class"], f"observations[{index}].resource_class")
        dimension = _resource_identifier(item["dimension"], f"observations[{index}].dimension")
        quality = _nonblank_string(item["metering_quality"], f"observations[{index}].metering_quality")
        if quality not in _METERING_QUALITIES:
            raise ResourceForecastError(f"observations[{index}].metering_quality is not supported")
        source = _nullable_string(
            item["measurement_source_ref"],
            f"observations[{index}].measurement_source_ref",
            nonblank_when_present=True,
        )
        quantity = _decimal_quantity(
            item["quantity"],
            f"observations[{index}].quantity",
            allow_null=quality in {"ESTIMATED", "UNKNOWN"},
        )
        if quality == "UNKNOWN" and quantity is not None:
            raise ResourceForecastError(f"observations[{index}] UNKNOWN quantity must be null")
        if quality in _USABLE_ACTUAL_QUALITIES and quantity is None:
            raise ResourceForecastError(f"observations[{index}] actual quantity must be known")
        if quality == "AUTHORITATIVE_ACTUAL" and source is None:
            raise ResourceForecastError(
                f"observations[{index}] AUTHORITATIVE_ACTUAL requires measurement_source_ref"
            )
        identity = (basis_ref, resource_class, dimension)
        facts = (quantity, quality, source)
        previous = observations.get(identity)
        if previous is not None and previous != facts:
            raise ResourceForecastError(
                "conflicting duplicate historical observation: "
                f"{basis_ref}/{resource_class}/{dimension}"
            )
        observations[identity] = facts
    return observations


def canonical_shared_estimates(value: object) -> list[dict[str, object]]:
    """Normalize supplied grouped estimates; never sum overlapping components."""
    if not isinstance(value, list):
        raise ResourceForecastError("shared_estimates must be an array")
    result: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != _SHARED_ESTIMATE_FIELDS:
            raise ResourceForecastError(f"shared_estimates[{index}] has invalid fields")
        grant_ref = _nonblank_string(item["grant_ref"], "shared estimate grant_ref")
        limit_id = _nonblank_string(item["limit_id"], "shared estimate limit_id")
        if (grant_ref, limit_id) in seen:
            raise ResourceForecastError("duplicate shared estimate identity")
        seen.add((grant_ref, limit_id))
        classes = _string_list(item["resource_classes"], "shared estimate resource_classes", nonempty=True)
        if len(classes) != len(set(classes)):
            raise ResourceForecastError("duplicate shared estimate resource class")
        classes = sorted(_resource_identifier(c, "shared estimate resource_class") for c in classes)
        basis = _string_list(item["basis_refs"], "shared estimate basis_refs", nonempty=False)
        if len(basis) != len(set(basis)):
            raise ResourceForecastError("duplicate shared estimate basis ref")
        state = item["estimate_state"]
        if state not in {"ESTIMATED", "UNKNOWN"}:
            raise ResourceForecastError("shared estimate state is invalid")
        amount = _decimal_quantity(item["upper_bound"], "shared estimate upper_bound", allow_null=True)
        if state == "ESTIMATED" and (amount is None or not basis):
            raise ResourceForecastError("estimated shared total requires a bound and basis")
        if state == "UNKNOWN" and amount is not None:
            raise ResourceForecastError("unknown shared total cannot carry a bound")
        result.append({"grant_ref": grant_ref, "limit_id": limit_id, "resource_classes": classes,
                       "estimate_state": state, "upper_bound": amount, "basis_refs": sorted(basis)})
    return sorted(result, key=lambda item: (str(item["grant_ref"]), str(item["limit_id"])))


def build_resource_estimate(request: Mapping[str, object]) -> dict[str, object]:
    """Build one canonical RESOURCE_ESTIMATE from explicit route-bound evidence."""
    envelope = _require_mapping(request, "request")
    if not _TOP_LEVEL_FIELDS.issubset(envelope) or set(envelope) - (_TOP_LEVEL_FIELDS | {"shared_estimates"}):
        raise ResourceForecastError("request has invalid fields")

    artifact_id = _nonblank_string(envelope["artifact_id"], "artifact_id")
    produced_by_role = _nonblank_string(envelope["produced_by_role"], "produced_by_role")
    assignment_id = _nullable_string(envelope["assignment_id"], "assignment_id")
    input_state_ref = _nullable_string(envelope["input_state_ref"], "input_state_ref")
    subject_ref = _nonblank_string(envelope["subject_ref"], "subject_ref")
    route_ref = _nonblank_string(envelope["route_ref"], "route_ref")
    estimator_revision_ref = _nonblank_string(envelope["estimator_revision_ref"], "estimator_revision_ref")
    provenance = sorted(set(_string_list(envelope["provenance"], "provenance", nonempty=True)))
    related_artifacts = sorted(
        set(_string_list(envelope["related_artifacts"], "related_artifacts", nonempty=False))
    )
    requested_keys = _normalize_requested_resources(envelope["requested_resources"])
    observations = _normalize_observations(envelope["observations"])

    values_by_key: dict[tuple[str, str], list[tuple[str, Decimal]]] = {key: [] for key in requested_keys}
    requested_set = set(requested_keys)
    for (basis_ref, resource_class, dimension), (quantity, quality, _source) in observations.items():
        key = (resource_class, dimension)
        if key not in requested_set or quality not in _USABLE_ACTUAL_QUALITIES:
            continue
        if quantity is None:  # Guarded by validation; retained as a fail-closed invariant.
            raise ResourceForecastError("usable actual observation unexpectedly has null quantity")
        values_by_key[key].append((basis_ref, quantity))

    estimates: list[dict[str, object]] = []
    used_basis_refs: set[str] = set()
    estimated_count = 0
    for resource_class, dimension in requested_keys:
        samples = values_by_key[(resource_class, dimension)]
        if not samples:
            estimates.append(
                {
                    "resource_class": resource_class,
                    "dimension": dimension,
                    "estimate_state": "UNKNOWN",
                    "point_estimate": None,
                    "quantiles": [],
                    "upper_bound": None,
                    "confidence": "UNKNOWN",
                    "historical_sample_count": None,
                    "unknown_resource_state": "ESTIMATE_UNKNOWN",
                }
            )
            continue

        estimated_count += 1
        used_basis_refs.update(basis_ref for basis_ref, _quantity in samples)
        sorted_values = sorted(quantity for _basis_ref, quantity in samples)
        quantile_values = {
            label: _interpolated_quantile(sorted_values, probability)
            for label, probability in _QUANTILES
        }
        quantiles = [
            {
                "probability": float(probability),
                "quantity": _ordinary_json_number(quantile_values[label]),
            }
            for label, probability in _QUANTILES
        ]
        estimates.append(
            {
                "resource_class": resource_class,
                "dimension": dimension,
                "estimate_state": "ESTIMATED",
                "point_estimate": _ordinary_json_number(quantile_values["P50"]),
                "quantiles": quantiles,
                "upper_bound": _upper_json_number(sorted_values[-1]),
                "confidence": _confidence(len(sorted_values)),
                "historical_sample_count": len(sorted_values),
                "unknown_resource_state": "KNOWN",
            }
        )

    grouped = canonical_shared_estimates(envelope.get("shared_estimates", []))
    used_basis_refs.update(ref for item in grouped for ref in item["basis_refs"])
    estimated_count += sum(item["estimate_state"] == "ESTIMATED" for item in grouped)
    if estimated_count == len(estimates) + len(grouped):
        status = "ESTIMATED"
    elif estimated_count == 0:
        status = "UNKNOWN"
    else:
        status = "PARTIAL"

    result = {
        "artifact_type": "RESOURCE_ESTIMATE",
        "artifact_id": artifact_id,
        "produced_by_role": produced_by_role,
        "assignment_id": assignment_id,
        "input_state_ref": input_state_ref,
        "status": status,
        "provenance": provenance,
        "related_artifacts": related_artifacts,
        "subject_ref": subject_ref,
        "route_ref": route_ref,
        "estimator_revision_ref": estimator_revision_ref,
        "basis_refs": sorted(used_basis_refs),
        "estimates": estimates,
    }
    if "shared_estimates" in envelope:
        for item in grouped:
            amount = item["upper_bound"]
            if isinstance(amount, Decimal):
                item["upper_bound"] = _upper_json_number(amount)
        result["shared_estimates"] = grouped
    return result


def _read_request(path_arg: str | None) -> Mapping[str, object]:
    try:
        raw = Path(path_arg).read_text(encoding="utf-8") if path_arg else sys.stdin.read()
    except OSError as exc:
        raise ResourceForecastError(f"cannot read request: {exc}") from None
    try:
        parsed = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
    except json.JSONDecodeError as exc:
        raise ResourceForecastError(f"invalid JSON: line {exc.lineno} column {exc.colno}") from None
    return _require_mapping(parsed, "request")


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("resource_forecast: expected at most one REQUEST.json path", file=sys.stderr)
        return 2
    try:
        artifact = build_resource_estimate(_read_request(args[0] if args else None))
    except ResourceForecastError as exc:
        print(f"resource_forecast: {exc}", file=sys.stderr)
        return 2
    json.dump(artifact, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

