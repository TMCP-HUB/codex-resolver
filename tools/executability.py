#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.assignment_compiler import (
    EnvelopeResolver, director_decision_envelope_errors, valid_architecture_health, validate_compiled_assignment,
)
from tools.durable_output_contract import validate_assignment_durable_outputs

CapabilityEvidenceResolver = Callable[[str], Mapping[str, object] | None]

CAPABILITY_PROFILE_READINESS = {
    "READY",
    "DEGRADED",
    "PROVISIONING_REQUIRED",
    "AUTH_REQUIRED",
    "UNAVAILABLE",
}
EXECUTION_USABLE_READINESS = {"READY", "DEGRADED"}


def validate_state_observation(artifact: Mapping[str, object]) -> list[str]:
    """Validate the bounded Control-owned relevant-state observation contract."""
    errors: list[str] = []
    if artifact.get("artifact_type") != "STATE_OBSERVATION": errors.append("artifact_type must be STATE_OBSERVATION")
    if artifact.get("produced_by_role") != "control-director": errors.append("produced_by_role must be control-director")
    if artifact.get("status") != "CURRENT": errors.append("status must be CURRENT")
    for field in ("artifact_id", "state_identity", "authority_scope"):
        if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip(): errors.append(f"{field} must be a non-empty string")
    value = artifact.get("input_state_ref")
    if "input_state_ref" not in artifact or (value is not None and (not isinstance(value, str) or not value.strip())): errors.append("input_state_ref must be null or a non-empty string")
    for field in ("provenance", "related_artifacts"): _string_list(artifact.get(field), field, errors)
    context = artifact.get("project_topology_context")
    if context is not None:
        expected = {"project_id", "current_topology_ref", "system_of_record_ref", "storage_mode"}
        if not isinstance(context, Mapping) or set(context) != expected:
            errors.append("project_topology_context must contain exact governed identity fields")
        else:
            for field in ("project_id", "current_topology_ref", "system_of_record_ref"):
                if not isinstance(context[field], str) or not context[field].strip():
                    errors.append(f"project_topology_context.{field} must be non-blank")
            if context["storage_mode"] not in {"DRIVE_ONLY", "REPO_ONLY", "DRIVE_THEN_REPO"}:
                errors.append("project_topology_context.storage_mode is invalid")
    allowed = {"artifact_type", "artifact_id", "produced_by_role", "input_state_ref", "status", "provenance", "related_artifacts", "state_identity", "authority_scope", "project_topology_context"}
    if extra := sorted(set(artifact) - allowed): errors.append(f"unexpected fields: {extra}")
    return errors


def validate_executor_result(result: Mapping[str, object]) -> list[str]:
    """Validate the canonical factual EXECUTOR_RESULT contract."""
    errors: list[str] = []
    if result.get("artifact_type") != "EXECUTOR_RESULT": errors.append("artifact_type must be EXECUTOR_RESULT")
    if result.get("produced_by_role") != "executor": errors.append("produced_by_role must be executor")
    for field in ("artifact_id", "assignment_id"):
        if not isinstance(result.get(field), str) or not str(result[field]).strip(): errors.append(f"{field} must be a non-empty string")
    value = result.get("input_state_ref")
    if "input_state_ref" not in result or (value is not None and (not isinstance(value, str) or not value.strip())): errors.append("input_state_ref must be null or a non-empty string")
    if result.get("status") not in {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}: errors.append("status is invalid")
    for field in ("provenance", "related_artifacts", "resulting_state_refs", "evidence_refs", "deferred_findings", "limitations"):
        _string_list(result.get(field), field, errors)
    claims = result.get("claims")
    if not isinstance(claims, list): errors.append("claims must be a list"); return errors
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping): errors.append(f"claims[{index}] must be an object"); continue
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip(): errors.append(f"claims[{index}].claim_id must be non-empty")
        elif claim_id in seen: errors.append(f"duplicate claim_id: {claim_id}")
        else: seen.add(claim_id)
        if not isinstance(claim.get("claim"), str): errors.append(f"claims[{index}].claim must be a string")
        _string_list(claim.get("evidence_refs"), f"claims[{index}].evidence_refs", errors)
    return errors


def validate_verification_result(result: Mapping[str, object]) -> list[str]:
    """Validate the canonical VERIFICATION_RESULT contract."""
    errors: list[str] = []
    if result.get("artifact_type") != "VERIFICATION_RESULT": errors.append("artifact_type must be VERIFICATION_RESULT")
    if result.get("produced_by_role") != "control-verifier": errors.append("produced_by_role must be control-verifier")
    for field in ("artifact_id", "assignment_id", "executor_result_ref"):
        if not isinstance(result.get(field), str) or not str(result[field]).strip(): errors.append(f"{field} must be a non-empty string")
    value = result.get("input_state_ref")
    if "input_state_ref" not in result or (value is not None and (not isinstance(value, str) or not value.strip())): errors.append("input_state_ref must be null or a non-empty string")
    if result.get("status") not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"}: errors.append("status is invalid")
    for field in ("provenance", "related_artifacts", "additional_findings", "evidence_gaps"): _string_list(result.get(field), field, errors)
    verdicts = result.get("claim_verdicts")
    if not isinstance(verdicts, list): errors.append("claim_verdicts must be a list"); return errors
    seen: set[str] = set()
    for index, verdict in enumerate(verdicts):
        if not isinstance(verdict, Mapping): errors.append(f"claim_verdicts[{index}] must be an object"); continue
        claim_id = verdict.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip(): errors.append(f"claim_verdicts[{index}].claim_id must be non-empty")
        elif claim_id in seen: errors.append(f"duplicate claim verdict: {claim_id}")
        else: seen.add(claim_id)
        if verdict.get("verdict") not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN"}: errors.append(f"claim_verdicts[{index}].verdict is invalid")
        if "evidence_refs" in verdict: _string_list(verdict.get("evidence_refs"), f"claim_verdicts[{index}].evidence_refs", errors)
        if "note" in verdict and not isinstance(verdict.get("note"), str): errors.append(f"claim_verdicts[{index}].note must be a string")
    return errors


def validate_director_decision(decision: Mapping[str, object]) -> list[str]:
    """Validate canonical Director fields and bounded declarative transition authority."""
    errors: list[str] = director_decision_envelope_errors(decision)
    if "architecture_health" in decision and not valid_architecture_health(decision["architecture_health"]):
        errors.append("architecture_health must identify the affected boundary, observed state and disposition")
    authority = decision.get("transition_authority")
    if not isinstance(authority, Mapping): errors.append("transition_authority must be an object"); return errors
    expected = {"transition_id", "assignment_ref", "acceptance_requirements", "verification_required", "verification_target_claim_ids", "allowed_verification_outcomes", "verification_outcome_map", "incomplete_outcome", "next_control_intent_ref", "required_proof_refs", "requires_current_executability", "review_gate"}
    optional = {"review_gate"}
    if extra := sorted(set(authority) - expected): errors.append(f"transition_authority unexpected fields: {extra}")
    if missing := sorted((expected - optional) - set(authority)): errors.append(f"transition_authority missing fields: {missing}")
    for field in ("transition_id", "assignment_ref"):
        if not isinstance(authority.get(field), str) or not str(authority[field]).strip(): errors.append(f"transition_authority.{field} must be non-empty")
    if not isinstance(authority.get("verification_required"), bool): errors.append("transition_authority.verification_required must be boolean")
    if not isinstance(authority.get("requires_current_executability"), bool): errors.append("transition_authority.requires_current_executability must be boolean")
    for field in ("verification_target_claim_ids", "allowed_verification_outcomes", "required_proof_refs"): _string_list(authority.get(field), f"transition_authority.{field}", errors, unique=True, min_items=1 if field == "required_proof_refs" else 0)
    allowed_outcomes = {"CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"}
    if isinstance(authority.get("allowed_verification_outcomes"), list) and any(item not in allowed_outcomes for item in authority["allowed_verification_outcomes"]): errors.append("transition_authority.allowed_verification_outcomes is invalid")
    if authority.get("incomplete_outcome") not in {"ASSIGN", "WAIT", "ESCALATE"}: errors.append("transition_authority.incomplete_outcome is invalid")
    next_ref = authority.get("next_control_intent_ref")
    if next_ref is not None and (not isinstance(next_ref, str) or not next_ref.strip()): errors.append("transition_authority.next_control_intent_ref must be null or non-empty")
    requirements = authority.get("acceptance_requirements")
    if not isinstance(requirements, list) or not requirements: errors.append("transition_authority.acceptance_requirements must be non-empty")
    else:
        seen: set[str] = set()
        for index, item in enumerate(requirements):
            required_fields = {"requirement_id", "claim_id", "required_evidence_refs"}
            if not isinstance(item, Mapping) or not required_fields.issubset(item) or set(item) - (required_fields | {"evidence_source"}): errors.append(f"acceptance_requirements[{index}] has invalid shape"); continue
            for field in ("requirement_id", "claim_id"):
                if not isinstance(item.get(field), str) or not item[field].strip(): errors.append(f"acceptance_requirements[{index}].{field} must be non-empty")
            if isinstance(item.get("requirement_id"), str) and item["requirement_id"] in seen: errors.append("duplicate acceptance requirement")
            else: seen.add(str(item.get("requirement_id")))
            _string_list(item.get("required_evidence_refs"), f"acceptance_requirements[{index}].required_evidence_refs", errors)
            source = item.get("evidence_source", "EXECUTOR")
            if not isinstance(source, str) or source not in {"EXECUTOR", "VERIFIER", "DIRECTOR"}: errors.append(f"acceptance_requirements[{index}].evidence_source is invalid")
            if source == "VERIFIER":
                targets = authority.get("verification_target_claim_ids")
                if authority.get("verification_required") is not True or not isinstance(targets, list) or item.get("claim_id") not in targets:
                    errors.append(f"acceptance_requirements[{index}] requires an assigned verification target")
                if not item.get("required_evidence_refs"):
                    errors.append(f"acceptance_requirements[{index}] requires verifier evidence")
            if source == "DIRECTOR":
                if not isinstance(decision.get("director_review"), Mapping):
                    errors.append(f"acceptance_requirements[{index}] requires a Director review")
                if not item.get("required_evidence_refs"):
                    errors.append(f"acceptance_requirements[{index}] requires Director evidence")
    outcome_map = authority.get("verification_outcome_map")
    allowed_batons_by_outcome = {
        "CONFIRMED": {"WAIT", "ESCALATE", "COMPLETE"},
        "QUALIFIED": {"WAIT", "ESCALATE"},
        "NOT_PROVEN": {"WAIT", "ESCALATE"},
        "BLOCKED": {"WAIT", "ESCALATE"},
    }
    if not isinstance(outcome_map, Mapping) or any(key not in allowed_outcomes or value not in allowed_batons_by_outcome[key] for key, value in outcome_map.items()): errors.append("transition_authority.verification_outcome_map is invalid")

    gate = authority.get("review_gate")
    if gate is not None:
        if not isinstance(gate, Mapping):
            errors.append("transition_authority.review_gate must be an object")
        else:
            permitted = {"tier", "issue_ref", "target_ref", "outcome_claim_id",
                         "architecture_claim_id", "progress_claim_id",
                         "transition_claim_id", "transition_mode", "owner_decision_ref", "delivery_scope"}
            if extra := sorted(set(gate) - permitted):
                errors.append(f"review_gate unexpected fields: {extra}")
            tier = gate.get("tier")
            if not isinstance(tier, str) or tier not in {"V2", "V3", "V4"}:
                errors.append("review_gate.tier must be V2, V3 or V4")
            required = {"issue_ref", "outcome_claim_id", "delivery_scope"}
            if tier in {"V3", "V4"}:
                required |= {"target_ref", "architecture_claim_id", "progress_claim_id"}
            if tier == "V4":
                required |= {"transition_claim_id", "transition_mode"}
            if isinstance(gate.get("transition_mode"), str) and gate["transition_mode"] in {"REPLACEMENT_PRESERVE", "DESTRUCTIVE_CUTOVER"}:
                required.add("owner_decision_ref")
                if tier != "V4":
                    errors.append("review_gate replacement or destructive cutover requires V4")
            for field in required:
                if not isinstance(gate.get(field), str) or not gate[field].strip():
                    errors.append(f"review_gate.{field} must be non-empty")
            if gate.get("delivery_scope") not in {"FULL", "STAGED"}:
                errors.append("review_gate.delivery_scope is invalid")
            if "transition_mode" in gate and (not isinstance(gate["transition_mode"], str) or gate["transition_mode"] not in {
                "MIGRATION", "REPLACEMENT_PRESERVE", "DESTRUCTIVE_CUTOVER"
            }):
                errors.append("review_gate.transition_mode is invalid")
            if not authority.get("verification_required") and not isinstance(decision.get("director_review"), Mapping):
                errors.append("review_gate requires Director review or independent verification")
            claim_fields = ["outcome_claim_id"]
            if tier in {"V3", "V4"}:
                claim_fields += ["architecture_claim_id", "progress_claim_id"]
            if tier == "V4":
                claim_fields.append("transition_claim_id")
            claim_ids = [gate.get(field) for field in claim_fields]
            if len(claim_ids) != len(set(str(item) for item in claim_ids)):
                errors.append("review_gate claim identities must be distinct")
    review = decision.get("director_review")
    if review is not None:
        fields = {"review_type", "assignment_id", "executor_result_ref", "input_state_ref",
                  "verified_state_identity", "status", "claim_verdicts"}
        if not isinstance(review, Mapping) or not fields.issubset(review) or set(review) - (fields | {"verified_candidate"}):
            errors.append("director_review has invalid shape")
        else:
            if review.get("review_type") != "DIRECTOR_REVIEW": errors.append("director_review.review_type is invalid")
            for field in ("assignment_id", "executor_result_ref", "verified_state_identity"):
                if not isinstance(review.get(field), str) or not review[field].strip():
                    errors.append(f"director_review.{field} must be non-empty")
            if review.get("input_state_ref") is not None and (not isinstance(review.get("input_state_ref"), str) or not review["input_state_ref"].strip()):
                errors.append("director_review.input_state_ref must be null or non-empty")
            if not isinstance(review.get("status"), str) or review["status"] not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"}:
                errors.append("director_review.status is invalid")
            candidate = review.get("verified_candidate")
            if "verified_candidate" in review and (not isinstance(candidate, Mapping)
                    or set(candidate) != {"kind", "repository", "ref", "head_sha"}
                    or not isinstance(candidate.get("kind"), str) or candidate["kind"] not in {"PULL_REQUEST", "BRANCH"}
                    or not isinstance(candidate.get("repository"), str) or not candidate["repository"].strip()
                    or not isinstance(candidate.get("head_sha"), str)
                    or re.fullmatch(r"[0-9a-f]{40}", candidate["head_sha"]) is None
                    or isinstance(candidate.get("ref"), bool)
                    or not (isinstance(candidate.get("ref"), int) and candidate["ref"] >= 1
                            or isinstance(candidate.get("ref"), str) and candidate["ref"].strip())):
                errors.append("director_review.verified_candidate is invalid")
            verdicts = review.get("claim_verdicts")
            if not isinstance(verdicts, list):
                errors.append("director_review.claim_verdicts must be a list")
            else:
                seen_review_claims: set[str] = set()
                for index, verdict in enumerate(verdicts):
                    required_verdict = {"claim_id", "verdict", "evidence_refs"}
                    if (not isinstance(verdict, Mapping) or not required_verdict.issubset(verdict)
                            or set(verdict) - (required_verdict | {"note"})):
                        errors.append(f"director_review.claim_verdicts[{index}] has invalid shape")
                        continue
                    claim_id = verdict.get("claim_id")
                    if not isinstance(claim_id, str) or not claim_id.strip():
                        errors.append(f"director_review.claim_verdicts[{index}].claim_id must be non-empty")
                    elif claim_id in seen_review_claims:
                        errors.append(f"duplicate Director claim verdict: {claim_id}")
                    else:
                        seen_review_claims.add(claim_id)
                    if not isinstance(verdict.get("verdict"), str) or verdict["verdict"] not in {"CONFIRMED", "QUALIFIED", "NOT_PROVEN"}:
                        errors.append(f"director_review.claim_verdicts[{index}].verdict is invalid")
                    _string_list(verdict.get("evidence_refs"), f"director_review.claim_verdicts[{index}].evidence_refs", errors)
                    if "note" in verdict and not isinstance(verdict.get("note"), str):
                        errors.append(f"director_review.claim_verdicts[{index}].note must be a string")
                    if verdict.get("verdict") == "CONFIRMED" and not verdict.get("evidence_refs"):
                        errors.append(f"director_review.claim_verdicts[{index}] requires evidence")
    return errors


def _normalize(values: Iterable[str]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def _timestamp(value: object, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO-8601 timestamp")
        return None
    if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ) is None:
        errors.append(f"{field} must be an RFC3339 date-time")
        return None
    offset = re.search(r"([+-])(\d{2}):(\d{2})$", value)
    if offset and (int(offset.group(2)) > 23 or int(offset.group(3)) > 59):
        errors.append(f"{field} has an invalid timezone offset")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        normalized = parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        errors.append(f"{field} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return normalized


def _string_list(
    value: object,
    field: str,
    errors: list[str],
    *,
    unique: bool = False,
    min_items: int = 0,
    non_empty: bool = True,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return None
    if len(value) < min_items:
        errors.append(f"{field} must contain at least {min_items} item(s)")
    if not all(isinstance(item, str) and (item.strip() if non_empty else True) for item in value):
        errors.append(f"{field} must be a list of {'non-empty ' if non_empty else ''}strings")
        return None
    normalized = [item.strip() if non_empty else item for item in value]
    if unique and len(set(normalized)) != len(normalized):
        errors.append(f"{field} must not contain duplicates")
    return normalized


def evaluate_assignment_admissibility(
    required_capabilities: Iterable[str],
    available_capabilities: Iterable[str],
) -> dict[str, object]:
    """Return the deterministic subset result for one destination capability profile."""
    required = _normalize(required_capabilities)
    available = _normalize(available_capabilities)
    missing = sorted(set(required) - set(available))
    return {
        "status": "ADMISSIBLE" if not missing else "NOT_ADMISSIBLE",
        "required_capabilities": required,
        "available_capabilities": available,
        "unsatisfied_required_capabilities": missing,
    }


def validate_capability_evidence_artifact(artifact: Mapping[str, object]) -> list[str]:
    """Validate the schema-backed structural surface of CAPABILITY_EVIDENCE."""
    errors: list[str] = []
    if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE": errors.append("artifact_type must be CAPABILITY_EVIDENCE")
    if artifact.get("status") != "RESOLVED": errors.append("status must be RESOLVED")
    for field in ["artifact_id", "produced_by_role", "runtime_identity", "observation_method", "created_from"]:
        if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip(): errors.append(f"{field} must be a non-empty string")
    for field in ["assignment_id", "input_state_ref"]:
        value = artifact.get(field)
        if field not in artifact: errors.append(f"{field} is required")
        elif value is not None and (not isinstance(value, str) or not value.strip()): errors.append(f"{field} must be null or a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(artifact.get(field), field, errors, min_items=1)
    _string_list(artifact.get("capabilities"), "capabilities", errors, unique=True, min_items=1)
    _timestamp(artifact.get("observed_at"), "observed_at", errors)
    _timestamp(artifact.get("valid_until"), "valid_until", errors)
    return errors


def validate_capability_profile(
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
    *,
    require_usable: bool = False,
) -> list[str]:
    """Validate one canonical, freshness-bounded execution-surface advertisement."""
    errors: list[str] = []
    if profile.get("artifact_type") != "CAPABILITY_PROFILE":
        errors.append("artifact_type must be CAPABILITY_PROFILE")
    if profile.get("status") != "CURRENT":
        errors.append("capability profile status must be CURRENT")
    for field in [
        "artifact_id",
        "produced_by_role",
        "status",
        "destination_id",
        "runtime_identity",
        "surface_class",
        "workspace_scope_ref",
    ]:
        if not isinstance(profile.get(field), str) or not str(profile[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    readiness = profile.get("readiness")
    if not isinstance(readiness, str) or readiness not in CAPABILITY_PROFILE_READINESS:
        errors.append("readiness is invalid")
    elif require_usable and readiness not in EXECUTION_USABLE_READINESS:
        errors.append(f"capability profile readiness does not permit current execution: {readiness}")
    for field in ["provenance", "related_artifacts", "limitations"]:
        _string_list(profile.get(field), field, errors, non_empty=False)
    _string_list(profile.get("evidence_channels"), "evidence_channels", errors, unique=True, min_items=1)
    for field in ["assignment_id", "input_state_ref"]:
        if field not in profile:
            errors.append(f"{field} is required")
            continue
        value = profile.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")

    boundary = profile.get("freshness_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("freshness_boundary must be an object")
        observed_at = valid_until = None
    else:
        extra_boundary_fields = sorted(set(boundary) - {"observed_at", "valid_until"})
        if extra_boundary_fields:
            errors.append(f"freshness_boundary has unexpected fields: {extra_boundary_fields}")
        observed_at = _timestamp(boundary.get("observed_at"), "freshness_boundary.observed_at", errors)
        valid_until = _timestamp(boundary.get("valid_until"), "freshness_boundary.valid_until", errors)
        if observed_at and valid_until and observed_at > valid_until:
            errors.append("freshness_boundary observed_at must not be after valid_until")
        now = datetime.now(timezone.utc)
        if observed_at and observed_at > now:
            errors.append("capability profile freshness boundary starts in the future")
        if valid_until and valid_until <= now:
            errors.append("capability profile freshness boundary is expired")

    available = _string_list(
        profile.get("available_capabilities"),
        "available_capabilities",
        errors,
        unique=True,
    )
    unavailable = _string_list(
        profile.get("unavailable_capabilities"),
        "unavailable_capabilities",
        errors,
        unique=True,
    )
    evidence = profile.get("capability_evidence")
    if not isinstance(evidence, list):
        errors.append("capability_evidence must be a list")
        evidence = []

    normalized_available = _normalize(available or [])
    normalized_unavailable = _normalize(unavailable or [])
    overlap = sorted(set(normalized_available) & set(normalized_unavailable))
    if overlap:
        errors.append(f"capabilities cannot be both available and unavailable: {overlap}")

    runtime_identity = profile.get("runtime_identity")
    related_artifacts = profile.get("related_artifacts")
    evidence_artifacts = profile.get("evidence_artifacts")
    if not isinstance(evidence_artifacts, list):
        errors.append("evidence_artifacts must be a list")
        evidence_artifacts = []

    embedded_by_id: dict[str, Mapping[str, object]] = {}
    now = datetime.now(timezone.utc)
    for index, artifact in enumerate(evidence_artifacts):
        prefix = f"evidence_artifacts[{index}]"
        if not isinstance(artifact, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        errors.extend(f"{prefix}.{error}" for error in validate_capability_evidence_artifact(artifact))
        artifact_id = artifact.get("artifact_id")
        if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE":
            errors.append(f"{prefix}.artifact_type must be CAPABILITY_EVIDENCE")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"{prefix}.artifact_id must be a non-empty string")
            artifact_id = None
        elif artifact_id in embedded_by_id:
            errors.append(f"duplicate evidence artifact id: {artifact_id}")
        if artifact.get("status") != "RESOLVED":
            errors.append(f"{prefix}.status must be RESOLVED")
        if not isinstance(artifact.get("runtime_identity"), str) or not str(artifact["runtime_identity"]).strip():
            errors.append(f"{prefix}.runtime_identity must be a non-empty string")
        elif artifact.get("runtime_identity") != runtime_identity:
            errors.append(f"{prefix}.runtime_identity mismatch")
        _string_list(
            artifact.get("capabilities"),
            f"{prefix}.capabilities",
            errors,
            unique=True,
            min_items=1,
        )
        for field in ["produced_by_role", "observation_method", "created_from"]:
            if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ["provenance", "related_artifacts"]:
            _string_list(artifact.get(field), f"{prefix}.{field}", errors, min_items=1)
        for field in ["assignment_id", "input_state_ref"]:
            value = artifact.get(field)
            if field not in artifact:
                errors.append(f"{prefix}.{field} is required")
            elif value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"{prefix}.{field} must be null or a non-empty string")
        evidence_observed = _timestamp(artifact.get("observed_at"), f"{prefix}.observed_at", errors)
        evidence_valid = _timestamp(artifact.get("valid_until"), f"{prefix}.valid_until", errors)
        if evidence_observed and evidence_observed > now:
            errors.append(f"{prefix}.observed_at starts in the future")
        if evidence_valid and evidence_valid <= now:
            errors.append(f"{prefix}.valid_until is expired")
        if evidence_observed and evidence_valid and evidence_observed > evidence_valid:
            errors.append(f"{prefix}.observed_at is after valid_until")
        if observed_at and evidence_observed and evidence_observed > observed_at:
            errors.append(f"{prefix} begins after the profile freshness boundary")
        if valid_until and evidence_valid and evidence_valid < valid_until:
            errors.append(f"{prefix} expires before the profile")
        if artifact_id:
            embedded_by_id[artifact_id] = artifact

    evidence_caps: list[str] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            errors.append(f"capability_evidence[{index}] must be an object")
            continue
        capability = item.get("capability")
        evidence_ref = item.get("evidence_ref")
        if not isinstance(capability, str) or not capability.strip():
            errors.append(f"capability_evidence[{index}].capability must be a non-empty string")
            continue
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            errors.append(f"capability_evidence[{index}].evidence_ref must be a non-empty string")
            continue
        if evidence_resolver is None:
            errors.append(f"capability_evidence[{index}].evidence_ref requires governed resolution: {evidence_ref!r}")
            continue
        try:
            artifact = evidence_resolver(evidence_ref)
        except Exception as exc:
            errors.append(f"capability evidence resolver failed closed for {evidence_ref!r}: {type(exc).__name__}")
            continue
        if not isinstance(artifact, Mapping):
            errors.append(f"capability_evidence[{index}].evidence_ref is unresolved: {evidence_ref!r}")
            continue
        if artifact.get("artifact_id") != evidence_ref:
            errors.append(f"resolved evidence artifact identity mismatch for {evidence_ref!r}")
            continue
        embedded = embedded_by_id.get(evidence_ref)
        if embedded is not None and dict(embedded) != dict(artifact):
            errors.append(f"embedded evidence disagrees with authoritative evidence {evidence_ref!r}")
        errors.extend(f"resolved evidence {evidence_ref!r}.{error}" for error in validate_capability_evidence_artifact(artifact))
        # Validate the authoritative object with the same structural surface.
        for field in ["produced_by_role", "observation_method", "created_from"]:
            if not isinstance(artifact.get(field), str) or not str(artifact[field]).strip():
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be a non-empty string")
        for field in ["provenance", "related_artifacts"]:
            value = artifact.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(v, str) and v.strip() for v in value):
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be a non-empty string list")
        for field in ["assignment_id", "input_state_ref"]:
            value = artifact.get(field)
            if field not in artifact:
                errors.append(f"resolved evidence {evidence_ref!r}.{field} is required")
            elif value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"resolved evidence {evidence_ref!r}.{field} must be null or a non-empty string")
        if artifact.get("artifact_type") != "CAPABILITY_EVIDENCE" or artifact.get("status") != "RESOLVED":
            errors.append(f"resolved evidence {evidence_ref!r} is not a RESOLVED CAPABILITY_EVIDENCE")
        if artifact.get("runtime_identity") != runtime_identity:
            errors.append(f"resolved evidence {evidence_ref!r}.runtime_identity mismatch")
        resolved_observed = _timestamp(artifact.get("observed_at"), f"resolved evidence {evidence_ref!r}.observed_at", errors)
        resolved_valid = _timestamp(artifact.get("valid_until"), f"resolved evidence {evidence_ref!r}.valid_until", errors)
        if resolved_observed and resolved_observed > now: errors.append(f"resolved evidence {evidence_ref!r}.observed_at starts in the future")
        if resolved_valid and resolved_valid <= now: errors.append(f"resolved evidence {evidence_ref!r}.valid_until is expired")
        if resolved_observed and resolved_valid and resolved_observed > resolved_valid: errors.append(f"resolved evidence {evidence_ref!r}.observed_at is after valid_until")
        if observed_at and resolved_observed and resolved_observed > observed_at: errors.append(f"resolved evidence {evidence_ref!r} begins after the profile freshness boundary")
        if valid_until and resolved_valid and resolved_valid < valid_until: errors.append(f"resolved evidence {evidence_ref!r} expires before the profile")
        capabilities = _string_list(artifact.get("capabilities"), f"resolved evidence {evidence_ref!r}.capabilities", errors, unique=True, min_items=1)
        if capabilities is None or capability.strip() not in _normalize(capabilities):
            errors.append(f"evidence artifact {evidence_ref!r} does not prove {capability.strip()!r}")
        evidence_caps.append(capability.strip())
        if isinstance(related_artifacts, list) and evidence_ref not in related_artifacts:
            errors.append(f"evidence artifact {evidence_ref!r} is absent from related_artifacts")

    missing_evidence = sorted(set(normalized_available) - set(evidence_caps))
    if missing_evidence:
        errors.append(f"available capabilities missing evidence: {missing_evidence}")

    undeclared_evidence = sorted(set(evidence_caps) - set(normalized_available))
    if undeclared_evidence:
        errors.append(f"capability evidence references non-available capabilities: {undeclared_evidence}")

    return errors


def validate_admissibility_record(record: Mapping[str, object]) -> list[str]:
    """Validate subset result and complete mandatory-action capability accounting."""
    errors: list[str] = []
    required = record.get("required_capabilities")
    available = record.get("available_capabilities")
    missing = record.get("unsatisfied_required_capabilities")
    actions = record.get("mandatory_actions")
    evidence_paths = record.get("mandatory_evidence_paths")
    status = record.get("status")

    proof = record.get("transition_proof")
    if not isinstance(proof, Mapping):
        errors.append("transition_proof must be an object")
    else:
        expected = {"proof_class", "proof_status", "assignment_ref", "admissibility_ref", "destination_id", "runtime_identity", "dependency_bindings"}
        if set(proof) != expected: errors.append("transition_proof has invalid fields")
        if proof.get("proof_class") != "ASSIGNMENT_ADMISSION": errors.append("transition_proof.proof_class must be ASSIGNMENT_ADMISSION")
        if proof.get("proof_status") != "PROVEN": errors.append("transition_proof.proof_status must be PROVEN")
        for field in ("assignment_ref", "admissibility_ref", "destination_id", "runtime_identity"):
            if not isinstance(proof.get(field), str) or not str(proof[field]).strip(): errors.append(f"transition_proof.{field} must be non-empty")
        bindings = proof.get("dependency_bindings")
        if not isinstance(bindings, list) or not bindings: errors.append("transition_proof.dependency_bindings must be non-empty")
        else:
            refs: set[str] = set()
            for index, binding in enumerate(bindings):
                if not isinstance(binding, Mapping) or set(binding) != {"dependency_ref", "proven_identity"}: errors.append(f"transition_proof.dependency_bindings[{index}] has invalid shape"); continue
                for field in ("dependency_ref", "proven_identity"):
                    if not isinstance(binding.get(field), str) or not binding[field].strip(): errors.append(f"transition_proof.dependency_bindings[{index}].{field} must be non-empty")
                if binding.get("dependency_ref") in refs: errors.append("transition_proof has duplicate dependency_ref")
                refs.add(str(binding.get("dependency_ref")))

    if record.get("artifact_type") != "ASSIGNMENT_ADMISSIBILITY":
        errors.append("artifact_type must be ASSIGNMENT_ADMISSIBILITY")
    for field in [
        "artifact_id",
        "produced_by_role",
        "assignment_draft_id",
        "compiled_assignment_ref",
        "destination_id",
        "runtime_identity",
        "capability_profile_ref",
        "route_ref",
        "execution_mode",
    ]:
        if not isinstance(record.get(field), str) or not str(record[field]).strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(record.get(field), field, errors, non_empty=False)
    for field in ["assignment_id", "input_state_ref"]:
        if field not in record:
            errors.append(f"{field} is required")
            continue
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be null or a non-empty string")
    for field in ["fallback_mode", "reason"]:
        if field in record and record.get(field) is not None and not isinstance(record.get(field), str):
            errors.append(f"{field} must be null or a string")

    required_list = _string_list(required, "required_capabilities", errors, unique=True)
    available_list = _string_list(available, "available_capabilities", errors, unique=True)
    missing_list = _string_list(missing, "unsatisfied_required_capabilities", errors, unique=True)
    if not isinstance(actions, list) or not actions:
        errors.append("mandatory_actions must be a non-empty list")
        actions = []
    evidence_paths_list = _string_list(
        evidence_paths,
        "mandatory_evidence_paths",
        errors,
    )

    derived_required: set[str] = set()
    derived_evidence_paths: set[str] = set()
    seen_action_ids: set[str] = set()
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            errors.append(f"mandatory_actions[{index}] must be an object")
            continue
        action_id = action.get("action_id")
        action_required = action.get("required_capabilities")
        evidence_path = action.get("evidence_path")
        if not isinstance(action_id, str) or not action_id.strip():
            errors.append(f"mandatory_actions[{index}].action_id must be a non-empty string")
        elif action_id in seen_action_ids:
            errors.append(f"duplicate mandatory action id: {action_id}")
        else:
            seen_action_ids.add(action_id)
        action_required_list = _string_list(
            action_required,
            f"mandatory_actions[{index}].required_capabilities",
            errors,
            unique=True,
        )
        if action_required_list is not None:
            derived_required.update(_normalize(action_required_list))
        if evidence_path is not None:
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                errors.append(f"mandatory_actions[{index}].evidence_path must be null or a non-empty string")
            else:
                derived_evidence_paths.add(evidence_path.strip())

    normalized_required = _normalize(required_list or [])
    if sorted(derived_required) != normalized_required:
        errors.append(
            "required_capabilities do not equal union of mandatory action requirements: "
            f"derived {sorted(derived_required)}, declared {normalized_required}"
        )

    normalized_paths = _normalize(evidence_paths_list or [])
    if sorted(derived_evidence_paths) != normalized_paths:
        errors.append(
            "mandatory_evidence_paths do not equal action evidence paths: "
            f"derived {sorted(derived_evidence_paths)}, declared {normalized_paths}"
        )

    if required_list is not None and available_list is not None and missing_list is not None:
        expected = evaluate_assignment_admissibility(required_list, available_list)
        if status != expected["status"]:
            errors.append(f"status drift: expected {expected['status']}, got {status}")
        if _normalize(missing_list) != expected["unsatisfied_required_capabilities"]:
            errors.append(
                "unsatisfied_required_capabilities drift: "
                f"expected {expected['unsatisfied_required_capabilities']}, got {_normalize(missing_list)}"
            )
    return errors


def validate_admissibility_against_profile(
    record: Mapping[str, object],
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
) -> list[str]:
    """Bind an admissibility record to the exact, currently usable capability profile it cites."""
    errors = validate_capability_profile(profile, evidence_resolver, require_usable=True) + validate_admissibility_record(record)

    profile_id = profile.get("artifact_id")
    record_profile_ref = record.get("capability_profile_ref")
    if not isinstance(profile_id, str) or not profile_id.strip():
        errors.append("capability profile artifact_id must be a non-empty string")
    elif record_profile_ref != profile_id:
        errors.append(
            f"capability_profile_ref mismatch: record cites {record_profile_ref!r}, profile is {profile_id!r}"
        )

    profile_destination = profile.get("destination_id")
    record_destination = record.get("destination_id")
    if profile_destination != record_destination:
        errors.append(
            f"destination mismatch: record {record_destination!r}, profile {profile_destination!r}"
        )

    if profile.get("runtime_identity") != record.get("runtime_identity"):
        errors.append(
            "runtime identity mismatch: "
            f"record {record.get('runtime_identity')!r}, profile {profile.get('runtime_identity')!r}"
        )

    profile_available = profile.get("available_capabilities")
    record_available = record.get("available_capabilities")
    if isinstance(profile_available, list) and isinstance(record_available, list):
        if _normalize(profile_available) != _normalize(record_available):
            errors.append(
                "available_capabilities do not match cited capability profile: "
                f"record {_normalize(record_available)}, profile {_normalize(profile_available)}"
            )

    return errors


def validate_execution_route(
    route: Mapping[str, object],
    profiles: Mapping[str, Mapping[str, object]],
    evidence_resolver: CapabilityEvidenceResolver | None,
) -> list[str]:
    """Prove every delivery/execution/durable-control segment and handoff."""
    errors: list[str] = []
    if route.get("artifact_type") != "EXECUTION_ROUTE" or route.get("status") != "ADMISSIBLE":
        errors.append("execution route must be an ADMISSIBLE EXECUTION_ROUTE")
    for field in ["artifact_id", "produced_by_role", "assignment_draft_id"]:
        if not isinstance(route.get(field), str) or not str(route[field]).strip():
            errors.append(f"execution_route.{field} must be a non-empty string")
    for field in ["assignment_id", "input_state_ref"]:
        value = route.get(field)
        if field not in route: errors.append(f"execution_route.{field} is required")
        elif value is not None and (not isinstance(value, str) or not value.strip()): errors.append(f"execution_route.{field} must be null or a non-empty string")
    for field in ["provenance", "related_artifacts"]:
        _string_list(route.get(field), f"execution_route.{field}", errors)
    segments = route.get("segments")
    if not isinstance(segments, list) or not segments:
        return errors + ["execution_route.segments must be a non-empty list"]
    roles: set[str] = set()
    ids: set[str] = set()
    segment_caps: dict[str, set[str]] = {}
    segment_by_id: dict[str, Mapping[str, object]] = {}
    for index, segment in enumerate(segments):
        prefix = f"execution_route.segments[{index}]"
        if not isinstance(segment, Mapping): errors.append(f"{prefix} must be an object"); continue
        sid, role = segment.get("segment_id"), segment.get("route_role")
        for field in ["segment_id", "route_role", "destination_id", "runtime_identity", "capability_profile_ref", "execution_mode"]:
            if not isinstance(segment.get(field), str) or not str(segment[field]).strip(): errors.append(f"{prefix}.{field} must be a non-empty string")
        if role not in {"CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"}: errors.append(f"{prefix}.route_role is invalid")
        elif role in roles: errors.append(f"duplicate execution route role: {role}")
        else: roles.add(str(role))
        if isinstance(sid, str):
            if sid in ids: errors.append(f"duplicate route segment id: {sid}")
            ids.add(sid)
        required = _string_list(segment.get("required_capabilities"), f"{prefix}.required_capabilities", errors, unique=True) or []
        profile_ref = segment.get("capability_profile_ref")
        profile = profiles.get(str(profile_ref))
        if profile is None:
            errors.append(f"{prefix}.capability_profile_ref is unresolved: {profile_ref!r}"); continue
        errors.extend(validate_capability_profile(profile, evidence_resolver, require_usable=True))
        if profile.get("destination_id") != segment.get("destination_id"): errors.append(f"{prefix}.destination_id mismatch")
        if profile.get("runtime_identity") != segment.get("runtime_identity"): errors.append(f"{prefix}.runtime_identity mismatch")
        available = set(_normalize(profile.get("available_capabilities", [])))
        missing = sorted(set(_normalize(required)) - available)
        if missing: errors.append(f"{prefix} has unproven capabilities: {missing}")
        if isinstance(sid, str):
            segment_caps[sid] = available
            segment_by_id[sid] = segment
    expected_roles = {"CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"}
    if roles != expected_roles: errors.append(f"execution route roles incomplete: {sorted(expected_roles - roles)}")
    edges = route.get("handoffs")
    if not isinstance(edges, list) or len(edges) < 2: errors.append("execution_route.handoffs must prove both mandatory handoffs"); edges = []
    seen_pairs: set[tuple[object, object]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping): errors.append(f"execution_route.handoffs[{index}] must be an object"); continue
        source, target = edge.get("from_segment"), edge.get("to_segment")
        same_surface = edge.get("same_surface")
        if "same_surface" not in edge:
            errors.append(f"execution_route.handoffs[{index}].same_surface is required")
            continue
        if not isinstance(same_surface, bool):
            errors.append(f"execution_route.handoffs[{index}].same_surface must be a boolean")
            continue
        same_actor = edge.get("same_actor_continuation", False)
        if not isinstance(same_actor, bool):
            errors.append(f"execution_route.handoffs[{index}].same_actor_continuation must be a boolean")
            same_actor = False
        if same_actor and not same_surface:
            errors.append(f"execution_route.handoffs[{index}] same-actor continuation requires the same surface")
        source_required = _string_list(edge.get("source_required_capabilities"), f"execution_route.handoffs[{index}].source_required_capabilities", errors, unique=True) or []
        target_required = _string_list(edge.get("target_required_capabilities"), f"execution_route.handoffs[{index}].target_required_capabilities", errors, unique=True) or []
        internal_required = _string_list(edge.get("internal_required_capabilities"), f"execution_route.handoffs[{index}].internal_required_capabilities", errors, unique=True) or []
        if source not in ids or target not in ids: errors.append(f"execution_route.handoffs[{index}] cites an unknown segment")
        seen_pairs.add((source, target))
        source_available = segment_caps.get(str(source), set())
        target_available = segment_caps.get(str(target), set())
        if same_surface:
            source_seg = segment_by_id.get(str(source), {})
            target_seg = segment_by_id.get(str(target), {})
            if (source_seg.get("destination_id"), source_seg.get("runtime_identity")) != (target_seg.get("destination_id"), target_seg.get("runtime_identity")):
                errors.append(f"execution_route.handoffs[{index}] claims false same-surface equivalence")
            if not internal_required and not same_actor:
                errors.append(f"execution_route.handoffs[{index}] same-surface handoff requires internal capabilities")
            missing = sorted(set(internal_required) - source_available)
            if missing: errors.append(f"execution_route.handoffs[{index}] has unproven internal capabilities: {missing}")
        else:
            if not source_required or not target_required:
                errors.append(f"execution_route.handoffs[{index}] cross-surface handoff requires source export and target receive capabilities")
            source_missing = sorted(set(source_required) - source_available)
            target_missing = sorted(set(target_required) - target_available)
            if source_missing: errors.append(f"execution_route.handoffs[{index}] has unproven source capabilities: {source_missing}")
            if target_missing: errors.append(f"execution_route.handoffs[{index}] has unproven target capabilities: {target_missing}")
    ordered = [next((s.get("segment_id") for s in segments if isinstance(s, Mapping) and s.get("route_role") == r), None) for r in ["CANDIDATE_DELIVERY", "EXECUTION_VERIFICATION", "DURABLE_EVIDENCE_CONTROL"]]
    if (ordered[0], ordered[1]) not in seen_pairs or (ordered[1], ordered[2]) not in seen_pairs: errors.append("execution route is missing a mandatory ordered handoff")
    final_result = route.get("final_result")
    if not isinstance(final_result, Mapping):
        errors.append("execution_route.final_result must be an object")
    else:
        segment_ref = final_result.get("segment_ref")
        destination_id = final_result.get("destination_id")
        if not isinstance(segment_ref, str) or segment_ref not in segment_by_id:
            errors.append("execution_route.final_result.segment_ref is unresolved")
        else:
            endpoint = segment_by_id[segment_ref]
            if endpoint.get("route_role") != "DURABLE_EVIDENCE_CONTROL": errors.append("execution_route.final_result must reference the durable segment")
            if destination_id != endpoint.get("destination_id"): errors.append("execution_route.final_result.destination_id does not match durable segment")
        if not isinstance(destination_id, str) or not destination_id.strip(): errors.append("execution_route.final_result.destination_id must be a non-empty string")
    return errors


def validate_assignment_artifact(assignment: Mapping[str, object]) -> list[str]:
    """Validate the schema-required ASSIGNMENT surface used by the complete-chain CLI."""
    errors: list[str] = []
    if assignment.get("artifact_type") != "ASSIGNMENT":
        errors.append("assignment artifact_type must be ASSIGNMENT")
    for field in [
        "artifact_id",
        "produced_by_role",
        "assignment_id",
        "status",
        "objective",
        "result_to",
    ]:
        if not isinstance(assignment.get(field), str) or not str(assignment[field]).strip():
            errors.append(f"assignment.{field} must be a non-empty string")
    if "input_state_ref" not in assignment:
        errors.append("assignment.input_state_ref is required")
    else:
        input_state_ref = assignment.get("input_state_ref")
        if input_state_ref is not None and (
            not isinstance(input_state_ref, str) or not input_state_ref.strip()
        ):
            errors.append("assignment.input_state_ref must be null or a non-empty string")
    for field in ["provenance", "related_artifacts", "acceptance", "stop_conditions"]:
        _string_list(assignment.get(field), f"assignment.{field}", errors, non_empty=False)
    _string_list(
        assignment.get("authority"),
        "assignment.authority",
        errors,
        min_items=1,
        non_empty=False,
    )
    required_outputs = assignment.get("required_outputs")
    if required_outputs is not None:
        _string_list(required_outputs, "assignment.required_outputs", errors, non_empty=False)
    errors.extend(validate_assignment_durable_outputs(assignment))

    scope = assignment.get("scope")
    if not isinstance(scope, Mapping):
        errors.append("assignment.scope must be an object")
    else:
        _string_list(scope.get("allowed"), "assignment.scope.allowed", errors, non_empty=False)
        _string_list(scope.get("forbidden"), "assignment.scope.forbidden", errors, non_empty=False)

    contract = assignment.get("execution_contract")
    if not isinstance(contract, Mapping):
        errors.append("assignment.execution_contract must be an object")
        return errors

    for field in [
        "assignment_draft_ref",
        "compiled_assignment_ref",
        "destination_id",
        "runtime_identity",
        "capability_profile_ref",
        "admissibility_ref",
        "route_ref",
        "execution_mode",
    ]:
        if not isinstance(contract.get(field), str) or not str(contract[field]).strip():
            errors.append(f"assignment.execution_contract.{field} must be a non-empty string")
    if contract.get("proof_status") != "PROVEN":
        errors.append("assignment execution proof_status must be PROVEN")
    _string_list(
        contract.get("required_capabilities"),
        "assignment.execution_contract.required_capabilities",
        errors,
        unique=True,
    )
    unsatisfied = _string_list(
        contract.get("unsatisfied_required_capabilities"),
        "assignment.execution_contract.unsatisfied_required_capabilities",
        errors,
        unique=True,
    )
    if unsatisfied:
        errors.append("assignment.execution_contract.unsatisfied_required_capabilities must be empty")
    _string_list(
        contract.get("mandatory_evidence_paths"),
        "assignment.execution_contract.mandatory_evidence_paths",
        errors,
    )
    fallback = contract.get("fallback_mode")
    if fallback is not None and not isinstance(fallback, str):
        errors.append("assignment.execution_contract.fallback_mode must be null or a string")
    return errors


def validate_assignment_execution_contract(
    assignment: Mapping[str, object],
    record: Mapping[str, object],
    profile: Mapping[str, object],
    evidence_resolver: CapabilityEvidenceResolver | None = None,
    route: Mapping[str, object] | None = None,
    route_profiles: Mapping[str, Mapping[str, object]] | None = None,
    compiled_assignment: Mapping[str, object] | None = None,
    execution_envelope_resolver: EnvelopeResolver | None = None,
) -> list[str]:
    """Validate the complete executable-assignment proof chain."""
    errors = (
        validate_admissibility_against_profile(record, profile, evidence_resolver)
        + validate_assignment_artifact(assignment)
    )
    contract = assignment.get("execution_contract")
    if not isinstance(contract, Mapping):
        return errors

    if compiled_assignment is None:
        errors.append("complete executable assignment requires an exact COMPILED_ASSIGNMENT")
    else:
        errors.extend(f"compiled assignment: {error}" for error in validate_compiled_assignment(compiled_assignment, execution_envelope_resolver))
        compiled_id = compiled_assignment.get("artifact_id")
        if compiled_assignment.get("compilation_status") != "COMPILED":
            errors.append("executable assignment cites a non-COMPILED artifact")
        if contract.get("compiled_assignment_ref") != compiled_id:
            errors.append("assignment compiled_assignment_ref mismatch")
        if record.get("compiled_assignment_ref") != compiled_id:
            errors.append("admissibility compiled_assignment_ref mismatch")
        if compiled_assignment.get("assignment_draft_ref") != record.get("assignment_draft_id"):
            errors.append("compiled assignment draft binding mismatch")
        if assignment.get("architecture_context") != compiled_assignment.get("architecture_context"):
            errors.append("assignment architecture context does not match compiled assignment")
        compiled_required = set(_normalize(compiled_assignment.get("authorized_required_capabilities", [])))
        final_required = set(_normalize(record.get("required_capabilities", [])))
        missing_compiled = sorted(compiled_required - final_required)
        if missing_compiled:
            errors.append(f"admissibility drops compiled assignment capabilities: {missing_compiled}")

    if record.get("status") != "ADMISSIBLE":
        errors.append("executable assignment cites a non-ADMISSIBLE record")

    draft_id = record.get("assignment_draft_id")
    draft_ref = contract.get("assignment_draft_ref")
    if not isinstance(draft_ref, str) or not draft_ref.strip():
        errors.append("assignment execution contract requires a non-empty assignment_draft_ref")
    elif draft_ref != draft_id:
        errors.append(f"assignment_draft_ref mismatch: assignment {draft_ref!r}, proof {draft_id!r}")

    record_id = record.get("artifact_id")
    if contract.get("admissibility_ref") != record_id:
        errors.append(
            f"admissibility_ref mismatch: assignment {contract.get('admissibility_ref')!r}, record {record_id!r}"
        )
    proof = record.get("transition_proof")
    if isinstance(proof, Mapping):
        if proof.get("assignment_ref") != assignment.get("artifact_id"): errors.append("transition proof assignment_ref mismatch")
        if proof.get("admissibility_ref") != record_id: errors.append("transition proof admissibility_ref mismatch")
        if proof.get("destination_id") != contract.get("destination_id"): errors.append("transition proof destination_id mismatch")
        if proof.get("runtime_identity") != contract.get("runtime_identity"): errors.append("transition proof runtime_identity mismatch")

    profile_id = profile.get("artifact_id")
    if contract.get("capability_profile_ref") != profile_id:
        errors.append(
            "assignment capability_profile_ref mismatch: "
            f"assignment {contract.get('capability_profile_ref')!r}, profile {profile_id!r}"
        )

    destination = record.get("destination_id")
    if contract.get("destination_id") != destination:
        errors.append(
            f"assignment destination mismatch: assignment {contract.get('destination_id')!r}, proof {destination!r}"
        )

    runtime_identity = record.get("runtime_identity")
    if contract.get("runtime_identity") != runtime_identity:
        errors.append(
            "assignment runtime_identity mismatch: "
            f"assignment {contract.get('runtime_identity')!r}, proof {runtime_identity!r}"
        )

    if contract.get("proof_status") != "PROVEN":
        errors.append("assignment execution proof_status must be PROVEN")

    record_required = record.get("required_capabilities")
    assignment_required = contract.get("required_capabilities")
    if isinstance(record_required, list) and isinstance(assignment_required, list):
        if _normalize(record_required) != _normalize(assignment_required):
            errors.append(
                "assignment required_capabilities do not match admissibility record: "
                f"assignment {_normalize(assignment_required)}, proof {_normalize(record_required)}"
            )
    else:
        errors.append("assignment/proof required_capabilities must be lists")

    record_missing = record.get("unsatisfied_required_capabilities")
    assignment_missing = contract.get("unsatisfied_required_capabilities")
    if isinstance(record_missing, list) and isinstance(assignment_missing, list):
        if _normalize(record_missing) != _normalize(assignment_missing):
            errors.append("assignment unsatisfied_required_capabilities do not match admissibility record")
        if _normalize(assignment_missing):
            errors.append("executable assignment contains unsatisfied required capabilities")
    else:
        errors.append("assignment/proof unsatisfied_required_capabilities must be lists")

    record_paths = record.get("mandatory_evidence_paths")
    assignment_paths = contract.get("mandatory_evidence_paths")
    if isinstance(record_paths, list) and isinstance(assignment_paths, list):
        if _normalize(record_paths) != _normalize(assignment_paths):
            errors.append(
                "assignment mandatory_evidence_paths do not match admissibility record: "
                f"assignment {_normalize(assignment_paths)}, proof {_normalize(record_paths)}"
            )
    else:
        errors.append("assignment/proof mandatory_evidence_paths must be lists")

    if contract.get("execution_mode") != record.get("execution_mode"):
        errors.append(
            "assignment execution_mode does not match admissibility record: "
            f"assignment {contract.get('execution_mode')!r}, proof {record.get('execution_mode')!r}"
        )

    if route is None:
        errors.append("complete executable assignment requires an authoritative execution route")
    else:
        errors.extend(validate_execution_route(route, route_profiles or {str(profile.get("artifact_id")): profile}, evidence_resolver))
        if contract.get("route_ref") != route.get("artifact_id"):
            errors.append("assignment route_ref does not match execution route identity")
        if record.get("route_ref") != route.get("artifact_id"):
            errors.append("admissibility route_ref does not match execution route identity")
        if route.get("assignment_draft_id") != record.get("assignment_draft_id"):
            errors.append("execution route assignment_draft_id mismatch")
        final_result = route.get("final_result")
        if not isinstance(final_result, Mapping) or assignment.get("result_to") != final_result.get("destination_id"):
            errors.append("assignment result_to does not match bound final durable route destination")
        route_segments = route.get("segments")
        execution_segment = next((segment for segment in route_segments if isinstance(segment, Mapping) and segment.get("route_role") == "EXECUTION_VERIFICATION"), None) if isinstance(route_segments, list) else None
        if not isinstance(execution_segment, Mapping):
            errors.append("execution route has no bound execution segment")
        else:
            for field in ["destination_id", "runtime_identity", "capability_profile_ref"]:
                if execution_segment.get(field) != contract.get(field):
                    errors.append(f"execution route execution segment {field} mismatch")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Project Resolver destination executability")
    parser.add_argument("--required", nargs="*", default=[])
    parser.add_argument("--available", nargs="*", default=[])
    parser.add_argument("--record", help="Validate an ASSIGNMENT_ADMISSIBILITY JSON file")
    parser.add_argument("--profile", help="Validate against an exact CAPABILITY_PROFILE JSON file")
    parser.add_argument("--assignment", help="Validate the complete ASSIGNMENT proof chain")
    parser.add_argument("--evidence-bundle", help="Governed offline CAPABILITY_EVIDENCE JSON array")
    parser.add_argument("--route", help="Validate the cited EXECUTION_ROUTE JSON file")
    parser.add_argument("--route-profiles", help="Offline JSON array of route CAPABILITY_PROFILE artifacts")
    parser.add_argument("--compiled-assignment", help="Exact authorized COMPILED_ASSIGNMENT JSON file")
    parser.add_argument("--execution-envelope", help="Governed EXECUTION_ENVELOPE JSON artifact")
    args = parser.parse_args()

    if args.profile and not args.record:
        parser.error("--profile requires --record")
    if args.assignment and (not args.record or not args.profile):
        parser.error("--assignment requires --record and --profile")
    if args.assignment and (not args.evidence_bundle or not args.route or not args.compiled_assignment or not args.execution_envelope):
        parser.error("--assignment requires --evidence-bundle, --route, --compiled-assignment, and --execution-envelope")

    if args.record:
        with open(args.record, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        if args.profile:
            with open(args.profile, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
            if args.assignment:
                with open(args.assignment, "r", encoding="utf-8") as handle:
                    assignment = json.load(handle)
                with open(args.evidence_bundle, "r", encoding="utf-8") as handle:
                    bundle = json.load(handle)
                evidence_by_id = {item.get("artifact_id"): item for item in bundle if isinstance(item, Mapping)} if isinstance(bundle, list) else {}
                with open(args.route, "r", encoding="utf-8") as handle:
                    route = json.load(handle)
                with open(args.compiled_assignment, "r", encoding="utf-8") as handle:
                    compiled_assignment = json.load(handle)
                with open(args.execution_envelope, "r", encoding="utf-8") as handle:
                    execution_envelope = json.load(handle)
                profiles = {str(profile.get("artifact_id")): profile}
                if args.route_profiles:
                    with open(args.route_profiles, "r", encoding="utf-8") as handle:
                        for item in json.load(handle):
                            if isinstance(item, Mapping): profiles[str(item.get("artifact_id"))] = item
                envelope_resolver = lambda ref: execution_envelope if execution_envelope.get("artifact_id") == ref else None
                errors = validate_assignment_execution_contract(assignment, record, profile, evidence_by_id.get, route, profiles, compiled_assignment, envelope_resolver)
            else:
                errors = validate_admissibility_against_profile(record, profile)
        else:
            errors = validate_admissibility_record(record)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    result = evaluate_assignment_admissibility(args.required, args.available)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ADMISSIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
