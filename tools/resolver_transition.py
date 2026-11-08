#!/usr/bin/env python3
"""Bundle-local composition of governed post-spawn Control Director artifacts."""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.github_candidate_handoff import check_github_candidate
from tools.assignment_compiler import (
    ARCHITECTURE_HEALTH_CONTEXT_INVALID,
    architecture_health_problem,
)
from tools.durable_artifact_port import DurableArtifactPort
from tools.durable_output_contract import (
    validate_assignment_durable_outputs,
    validate_executor_durable_output_refs,
)
from tools.durable_readback_enforcement import (
    READBACK_INVALID,
    READBACK_NOT_PROVEN,
    READBACK_PROVEN,
    evaluate_required_durable_readback,
    validate_verification_durable_readback_proofs,
)
from tools.executability import (
    validate_assignment_execution_contract,
    validate_capability_profile,
    validate_director_decision,
    validate_execution_route,
    validate_executor_result,
    validate_state_observation,
    validate_verification_result,
)

BATONS = {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"}
VERIFICATION_SEVERITY = {"CONFIRMED": 0, "QUALIFIED": 1, "NOT_PROVEN": 2, "BLOCKED": 3}


def _out(state: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": state, "control_state": state, "reason": reason, **details}


def _artifacts(value: object) -> tuple[dict[str, Mapping[str, object]], list[str]]:
    if not isinstance(value, list):
        return {}, ["artifacts must be a list"]
    found: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for index, artifact in enumerate(value):
        if not isinstance(artifact, Mapping):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"artifacts[{index}].artifact_id must be non-empty")
        elif artifact_id in found:
            errors.append(f"duplicate artifact_id: {artifact_id}")
        else:
            found[artifact_id] = artifact
    return found, errors


def _proof_problem(
    proof: Mapping[str, object],
    assignment: Mapping[str, object],
    artifacts: Mapping[str, Mapping[str, object]],
) -> tuple[str, str] | None:
    if proof.get("artifact_type") != "ASSIGNMENT_ADMISSIBILITY" or proof.get("status") != "ADMISSIBLE":
        return "ESCALATE", "INVALID_PROOF_CLASS"
    contract = assignment.get("execution_contract")
    lifecycle = proof.get("transition_proof")
    if not isinstance(contract, Mapping) or not isinstance(lifecycle, Mapping):
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    expected = {
        "proof_class": "ASSIGNMENT_ADMISSION",
        "proof_status": "PROVEN",
        "assignment_ref": assignment.get("artifact_id"),
        "admissibility_ref": proof.get("artifact_id"),
        "destination_id": contract.get("destination_id"),
        "runtime_identity": contract.get("runtime_identity"),
    }
    if any(lifecycle.get(field) != value for field, value in expected.items()):
        return "ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH"
    if contract.get("admissibility_ref") != proof.get("artifact_id"):
        return "ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH"
    bindings = lifecycle.get("dependency_bindings")
    if not isinstance(bindings, list) or not bindings:
        return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
    for binding in bindings:
        if not isinstance(binding, Mapping):
            return "ESCALATE", "MALFORMED_PROOF_LIFECYCLE"
        ref, identity = binding.get("dependency_ref"), binding.get("proven_identity")
        current = artifacts.get(ref) if isinstance(ref, str) else None
        if not isinstance(current, Mapping) or validate_state_observation(current):
            return "ESCALATE", "UNAUTHORIZED_PROOF_DEPENDENCY"
        if current.get("state_identity") != identity:
            return "WAIT", "RELEVANT_PROOF_STALE"
    return None


def _incomplete(authority: Mapping[str, object], artifacts: Mapping[str, Mapping[str, object]], assignment_id: object, current_state_ref: str | None = None) -> dict[str, object]:
    outcome = authority.get("incomplete_outcome")
    if outcome == "ASSIGN":
        ref = authority.get("next_control_intent_ref")
        intent = artifacts.get(ref) if isinstance(ref, str) else None
        if not isinstance(intent, Mapping) or intent.get("artifact_type") != "CONTROL_INTENT" or intent.get("assignment_id") != assignment_id:
            return _out("ESCALATE", "NEXT_ASSIGN_AUTHORITY_MISSING")
        if any(field in intent for field in ("assignment", "assignment_id_to_issue", "spawn_ready")):
            return _out("ESCALATE", "DIRECT_SPAWN_BYPASS_FORBIDDEN")
        if problem := architecture_health_problem(intent.get("architecture_context"), artifacts.get, current_state_ref=current_state_ref):
            state = "ESCALATE" if problem["code"] == ARCHITECTURE_HEALTH_CONTEXT_INVALID else "WAIT"
            return _out(state, problem["code"], detail=problem["detail"])
        return _out("ASSIGN", "AUTHORIZED_MORE_WORK", next_control_intent_ref=ref,
                    next_entrypoint="tools.resolver_spawn.resolve_spawn")
    if outcome == "WAIT":
        return _out("WAIT", "AUTHORIZED_REQUIREMENT_PENDING")
    return _out("ESCALATE", "AUTHORIZED_MATERIAL_CONFLICT")


def _effective_verification_outcome(
    aggregate_status: str,
    target_claim_ids: set[str],
    verdicts: Mapping[str, str],
) -> str:
    """Return the weakest governed verification outcome across aggregate and required claims."""
    outcomes = [aggregate_status, *(verdicts[claim_id] for claim_id in target_claim_ids)]
    return max(outcomes, key=VERIFICATION_SEVERITY.__getitem__)


def _owner_source_resolves(
    ref: str,
    artifacts: Mapping[str, Mapping[str, object]],
    reader: Callable[[str], object] | None,
) -> bool:
    """Read an existing Owner source; claim truth remains the reviewer's responsibility.

    The bundle may contain a structured Owner record or an actual text source.
    An external reader may return that same source as text or a mapping. A ref
    or boolean alone does not establish that the source was read.
    """
    def has_content(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip()) and value.strip() != ref.strip()

    source: object = artifacts.get(ref)
    if source is None and reader is not None:
        try:
            source = reader(ref)
        except Exception:
            return False
    if isinstance(source, str):
        return has_content(source)
    if not isinstance(source, Mapping):
        return False
    # Bundle lookup uses the artifact's key. An external trusted reader must
    # resolve the requested reference; its returned record may have a distinct
    # internal artifact_id or provider URL.
    if source.get("artifact_type") == "OWNER_DECISION_RECORD":
        if source.get("status") != "RECORDED" or source.get("produced_by_role") != "owner-interface":
            return False
        interpretation = source.get("resource_interpretation")
        constraints = source.get("owner_constraints")
        return bool(has_content(source.get("selected_option"))
                    or (isinstance(constraints, list) and any(has_content(item) for item in constraints))
                    or (source.get("canon_input_mode") == "DIRECT_INSTRUCTION"
                        and has_content(source.get("canon_instruction_text")))
                    or (isinstance(interpretation, Mapping) and has_content(interpretation.get("source_text"))))
    return any(has_content(source.get(key))
               for key in ("body", "content", "text", "source_text", "decision"))


def resolve_transition(
    control_bundle: Mapping[str, object],
    *,
    durable_port: DurableArtifactPort | None = None,
    github_candidate_reader: Callable[[str, str, str | int], Mapping[str, object] | None] | None = None,
    owner_decision_reader: Callable[[str], object] | None = None,
) -> dict[str, object]:
    """Reconcile one structured local post-spawn bundle to exactly one baton."""
    if not isinstance(control_bundle, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    artifacts, errors = _artifacts(control_bundle.get("artifacts"))
    if errors:
        reason = "CONTRADICTORY_CONTROL_ARTIFACTS" if any("duplicate artifact_id" in error for error in errors) else "MALFORMED_CONTROL_ARTIFACT"
        return _out("ESCALATE", reason, errors=errors)
    refs = control_bundle.get("refs")
    if not isinstance(refs, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    for field in ("current_state_ref", "prior_director_decision_ref", "assignment_ref", "executor_result_ref"):
        if not isinstance(refs.get(field), str) or not refs[field]:
            return _out("WAIT", "EXECUTOR_RESULT_PENDING") if field == "executor_result_ref" else _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")

    current = artifacts.get(refs["current_state_ref"])
    director = artifacts.get(refs["prior_director_decision_ref"])
    assignment = artifacts.get(refs["assignment_ref"])
    executor = artifacts.get(refs["executor_result_ref"])
    if not isinstance(current, Mapping) or validate_state_observation(current):
        return _out("ESCALATE", "MALFORMED_STATE_OBSERVATION")
    if not isinstance(director, Mapping) or (errors := validate_director_decision(director)):
        return _out("ESCALATE", "MALFORMED_DIRECTOR_DECISION", errors=errors if isinstance(director, Mapping) else [])
    if not isinstance(executor, Mapping):
        return _out("WAIT", "EXECUTOR_RESULT_PENDING")
    if errors := validate_executor_result(executor):
        return _out("ESCALATE", "MALFORMED_EXECUTOR_RESULT", errors=errors)

    authority = director["transition_authority"]
    assignment_id = assignment.get("assignment_id") if isinstance(assignment, Mapping) else None
    if (not isinstance(assignment, Mapping) or authority.get("assignment_ref") != assignment.get("artifact_id")
            or director.get("assignment_id") != assignment_id or executor.get("assignment_id") != assignment_id
            or executor.get("input_state_ref") != assignment.get("input_state_ref")
            or director.get("executor_result_ref") != executor.get("artifact_id")):
        return _out("ESCALATE", "CONTROL_POINT_IDENTITY_MISMATCH")

    durable_assignment_errors = validate_assignment_durable_outputs(assignment)
    if durable_assignment_errors:
        return _out("ESCALATE", "INVALID_GOVERNED_ASSIGNMENT", errors=durable_assignment_errors)
    if errors := validate_executor_durable_output_refs(executor, assignment):
        return _out("ESCALATE", "MALFORMED_EXECUTOR_RESULT", errors=errors)

    if current.get("artifact_id") not in executor.get("resulting_state_refs", []):
        return _out("ESCALATE", "CURRENT_STATE_IDENTITY_MISMATCH")

    contract = assignment.get("execution_contract")
    proof_ref = contract.get("admissibility_ref") if isinstance(contract, Mapping) else None
    profile_ref = contract.get("capability_profile_ref") if isinstance(contract, Mapping) else None
    route_ref = contract.get("route_ref") if isinstance(contract, Mapping) else None
    compiled_ref = contract.get("compiled_assignment_ref") if isinstance(contract, Mapping) else None
    proof, profile, route, compiled = (artifacts.get(ref) for ref in (proof_ref, profile_ref, route_ref, compiled_ref))
    if not all(isinstance(item, Mapping) for item in (proof, profile, route, compiled)):
        return _out("ESCALATE", "ASSIGNMENT_PROOF_CHAIN_UNRESOLVED")
    profiles = {key: value for key, value in artifacts.items() if value.get("artifact_type") == "CAPABILITY_PROFILE"}
    route_errors = validate_execution_route(route, profiles, artifacts.get)
    chain_errors = validate_assignment_execution_contract(
        assignment, proof, profile, artifacts.get, route, profiles, compiled, artifacts.get,
    )
    if route_errors or chain_errors:
        return _out("ESCALATE", "INVALID_GOVERNED_ASSIGNMENT", errors=route_errors + chain_errors)

    required_proofs = authority.get("required_proof_refs", [])
    if required_proofs != [proof_ref]:
        return _out("ESCALATE", "PROOF_CHAIN_IDENTITY_MISMATCH")
    if problem := _proof_problem(proof, assignment, artifacts):
        return _out(*problem, proof_ref=proof_ref)

    if authority.get("requires_current_executability"):
        current_profile_ref = refs.get("current_capability_profile_ref")
        current_profile = artifacts.get(current_profile_ref) if isinstance(current_profile_ref, str) else None
        if not isinstance(current_profile, Mapping) or (errors := validate_capability_profile(current_profile, artifacts.get, require_usable=True)):
            return _out("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED", errors=errors if isinstance(current_profile, Mapping) else [])
        if (current_profile.get("destination_id") != contract.get("destination_id")
                or current_profile.get("runtime_identity") != contract.get("runtime_identity")):
            return _out("ESCALATE", "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH")
        missing = sorted(set(contract.get("required_capabilities", [])) - set(current_profile.get("available_capabilities", [])))
        if missing:
            return _out("WAIT", "BLOCKED_RUNTIME_DRIFT", missing_capabilities=missing)

    durable_readback = evaluate_required_durable_readback(assignment, executor, durable_port)
    if durable_readback.status == READBACK_INVALID:
        return _out("ESCALATE", "DURABLE_READBACK_INVALID", errors=list(durable_readback.errors))
    if durable_readback.status == READBACK_NOT_PROVEN:
        return _out("WAIT", "DURABLE_READBACK_NOT_PROVEN", errors=list(durable_readback.errors))

    # The actual candidate kind must be supported by the admitted publisher route.
    if assignment.get("github_candidate_delivery") is not None:
        published = executor.get("published_candidate")
        if isinstance(published, Mapping) and published.get("kind") in {"PULL_REQUEST", "BRANCH"}:
            segments = route.get("segments", [])
            publishers = [item for item in segments if isinstance(item, Mapping)
                          and item.get("route_role") == "CANDIDATE_DELIVERY"]
            capabilities = set(publishers[0].get("required_capabilities", [])) if len(publishers) == 1 else set()
            required_cap = {"PULL_REQUEST": "pull_request_create",
                            "BRANCH": "remote_branch_write"}[published["kind"]]
            if required_cap not in capabilities:
                return _out("ESCALATE", "GITHUB_CANDIDATE_PUBLISH_ROUTE_NOT_ADMITTED")

    candidate_readback = check_github_candidate(assignment, executor, github_candidate_reader)
    if candidate_readback["status"] == "INVALID":
        return _out("ESCALATE", "GITHUB_CANDIDATE_READBACK_INVALID",
                    candidate_reason=candidate_readback["reason"])
    if candidate_readback["status"] == "NOT_PROVEN":
        if candidate_readback["reason"] == "GITHUB_CANDIDATE_NOT_PUBLISHED":
            # A local-only Executor result must never close Software delivery.
            # Preserve Control ownership of the original publishing attempt.
            return _out("WAIT", "SOFTWARE_GITHUB_PUBLICATION_PENDING",
                        candidate_reason=candidate_readback["reason"])
        return _out("WAIT", "GITHUB_CANDIDATE_READBACK_NOT_PROVEN",
                    candidate_reason=candidate_readback["reason"])

    director_review = director.get("director_review")
    director_verdicts = {}
    if isinstance(director_review, Mapping):
        if (director_review.get("assignment_id") != assignment_id
                or director_review.get("executor_result_ref") != executor.get("artifact_id")
                or director_review.get("input_state_ref") != executor.get("input_state_ref")
                or director_review.get("verified_state_identity") != current.get("state_identity")):
            return _out("WAIT", "DIRECTOR_REVIEW_CANDIDATE_NOT_PROVEN")
        if assignment.get("github_candidate_delivery") is not None:
            observed = director_review.get("verified_candidate")
            published = executor.get("published_candidate")
            if (not isinstance(observed, Mapping) or not isinstance(published, Mapping)
                    or set(observed) != set(published)
                    or any(type(observed[key]) is not type(value) or observed[key] != value
                           for key, value in published.items())):
                return _out("WAIT", "DIRECTOR_REVIEW_CANDIDATE_NOT_PROVEN")
        director_verdicts = {item["claim_id"]: item for item in director_review["claim_verdicts"]}

    verification = None
    if authority.get("verification_required"):
        verification_ref = refs.get("verification_result_ref")
        if not isinstance(verification_ref, str) or verification_ref not in artifacts:
            return _out("WAIT", "VERIFICATION_RESULT_PENDING")
        verification = artifacts[verification_ref]
        if errors := validate_verification_result(verification):
            return _out("ESCALATE", "MALFORMED_VERIFICATION_RESULT", errors=errors)
        if (director.get("verification_result_ref") != verification_ref
                or verification.get("assignment_id") != assignment_id
                or verification.get("executor_result_ref") != executor.get("artifact_id")
                or verification.get("input_state_ref") != executor.get("input_state_ref")):
            return _out("ESCALATE", "VERIFICATION_RESULT_IDENTITY_MISMATCH")
        if durable_readback.status == READBACK_PROVEN:
            if errors := validate_verification_durable_readback_proofs(
                verification,
                assignment,
                durable_readback.proofs,
            ):
                return _out("ESCALATE", "VERIFICATION_DURABLE_READBACK_MISMATCH", errors=errors)

    claims = {claim["claim_id"]: claim for claim in executor["claims"]}
    requirements = authority["acceptance_requirements"]
    verifier_requirements = [item for item in requirements if item.get("evidence_source", "EXECUTOR") == "VERIFIER"]
    verifier_claim_ids = {item["claim_id"] for item in verifier_requirements}
    director_requirements = [item for item in requirements if item.get("evidence_source", "EXECUTOR") == "DIRECTOR"]
    director_claim_ids = {item["claim_id"] for item in director_requirements}
    # Preserve the compiled acceptance requirements which actually
    # authorize mandatory Executor work. A claim authorizes an obligation;
    # it does not by itself mandate a separate Executor Result claim.
    compiled_claims = {item["claim_id"]: item for item in compiled.get("authorized_claims", [])
                       if isinstance(item, Mapping) and isinstance(item.get("claim_id"), str)}
    mandatory_acceptance = set()
    for obligation in compiled["authorized_mandatory_actions"] + compiled["authorized_evidence_requirements"]:
        if not isinstance(obligation, Mapping) or obligation.get("responsibility") != "EXECUTOR":
            continue
        claim = compiled_claims.get(str(obligation.get("claim_ref", "")))
        target = claim.get("target_ref") if isinstance(claim, Mapping) and claim.get("claim_kind") == "TASK_OUTCOME" else None
        if isinstance(target, str) and target.startswith("acceptance:"):
            mandatory_acceptance.add(target[len("acceptance:"):])
    missing = mandatory_acceptance - {item["requirement_id"] for item in requirements}
    if missing:
        return _out("ESCALATE", "COMPILED_ACCEPTANCE_REQUIREMENT_MISSING", requirement_ids=sorted(missing))
    # The existing verifier result is scoped to the same Executor Result;
    # additionally bind observations used as acceptance evidence to the
    # exact resulting state and, when applicable, published candidate.
    if verifier_requirements and (verification is None or verification.get("verified_state_identity") != current.get("state_identity")):
        return _out("WAIT", "VERIFICATION_CANDIDATE_NOT_PROVEN")
    if verifier_requirements and assignment.get("github_candidate_delivery") is not None:
        verified_candidate = verification.get("verified_candidate")
        published_candidate = executor.get("published_candidate")
        if (not isinstance(verified_candidate, Mapping) or not isinstance(published_candidate, Mapping)
                or set(verified_candidate) != set(published_candidate)
                or any(type(verified_candidate[key]) is not type(value) or verified_candidate[key] != value
                       for key, value in published_candidate.items())):
            return _out("WAIT", "VERIFICATION_CANDIDATE_NOT_PROVEN")
    factual_requirements_met = True

    review_gate = authority.get("review_gate")
    if isinstance(review_gate, Mapping):
        required_claim_ids = {review_gate["outcome_claim_id"]}
        if review_gate["tier"] in {"V3", "V4"}:
            required_claim_ids.update({review_gate["architecture_claim_id"],
                                       review_gate["progress_claim_id"]})
        if review_gate["tier"] == "V4":
            required_claim_ids.add(review_gate["transition_claim_id"])
        accepted_claim_ids = {item["claim_id"] for item in authority["acceptance_requirements"]}
        governed_targets = set(authority["verification_target_claim_ids"] if verification is not None else []) | set(director_verdicts)
        if not required_claim_ids.issubset(accepted_claim_ids & governed_targets):
            return _out("ESCALATE", "TARGET_ALIGNMENT_CONTRACT_MISSING",
                        missing_claim_ids=sorted(required_claim_ids - (accepted_claim_ids & governed_targets)))
        verifier_targets = set(authority["verification_target_claim_ids"]) if verification is not None else set()
        if required_claim_ids & verifier_targets:
            if verification.get("verified_state_identity") != current.get("state_identity"):
                return _out("WAIT", "VERIFICATION_CANDIDATE_NOT_PROVEN")
            if assignment.get("github_candidate_delivery") is not None:
                checked = verification.get("verified_candidate")
                published = executor.get("published_candidate")
                if (not isinstance(checked, Mapping) or not isinstance(published, Mapping)
                        or set(checked) != set(published)
                        or any(type(checked[key]) is not type(value) or checked[key] != value
                               for key, value in published.items())):
                    return _out("WAIT", "VERIFICATION_CANDIDATE_NOT_PROVEN")
        verdict_map = {item["claim_id"]: item for item in verification["claim_verdicts"]} if verification else {}
        owner_ref = review_gate.get("owner_decision_ref")
        destructive = review_gate.get("transition_mode") in {"REPLACEMENT_PRESERVE", "DESTRUCTIVE_CUTOVER"}
        if destructive and (not isinstance(owner_ref, str)
                            or not _owner_source_resolves(owner_ref, artifacts, owner_decision_reader)):
            return _out("WAIT", "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        for claim_id in sorted(required_claim_ids):
            by_verifier = claim_id in verifier_targets
            verdict = verdict_map.get(claim_id) if by_verifier else director_verdicts.get(claim_id)
            factual = claims.get(claim_id)
            requires_executor = any(item["claim_id"] == claim_id and item.get("evidence_source", "EXECUTOR") == "EXECUTOR" for item in requirements)
            if not isinstance(verdict, Mapping) or (requires_executor and not isinstance(factual, Mapping)):
                return _out("WAIT", "TARGET_ALIGNMENT_NOT_PROVEN", claim_id=claim_id)
            if verdict.get("verdict") != "CONFIRMED":
                return _out("WAIT", "TARGET_ALIGNMENT_NOT_PROVEN", claim_id=claim_id)
            if not verdict.get("evidence_refs") or (requires_executor and not factual.get("evidence_refs")):
                return _out("WAIT", "TARGET_ALIGNMENT_EVIDENCE_MISSING", claim_id=claim_id)
            if destructive and claim_id == review_gate.get("transition_claim_id"):
                note = verdict.get("note")
                if (owner_ref not in verdict["evidence_refs"] or not isinstance(note, str) or not note.strip()):
                    return _out("WAIT", "OWNER_AUTHORITY_REVIEW_NOT_PROVEN", claim_id=claim_id)

    # A submitted review is evidence, even for V1 or Executor-owned claims.
    # A review scoped solely to unrelated optional claims is not a new gate.
    if isinstance(director_review, Mapping):
        required_ids = {item["claim_id"] for item in requirements}
        covered = {key: value for key, value in director_verdicts.items() if key in required_ids}
        if any(value.get("verdict") != "CONFIRMED" for value in covered.values()):
            return _out("WAIT", "DIRECTOR_REVIEW_NOT_PROVEN")
        status = director_review["status"]
        if status != "CONFIRMED" and (covered or not director_verdicts):
            return _out("WAIT", "DIRECTOR_REVIEW_NOT_PROVEN")

    for requirement in requirements:
        required_evidence = set(requirement["required_evidence_refs"])
        if requirement.get("evidence_source", "EXECUTOR") == "VERIFIER":
            verdict = next((item for item in verification["claim_verdicts"] if item["claim_id"] == requirement["claim_id"]), None)
            if not isinstance(verdict, Mapping) or verdict.get("verdict") != "CONFIRMED" \
                    or not required_evidence.issubset(set(verdict.get("evidence_refs", []))):
                factual_requirements_met = False
        elif requirement.get("evidence_source", "EXECUTOR") == "DIRECTOR":
            verdict = director_verdicts.get(requirement["claim_id"])
            if (not isinstance(director_review, Mapping)
                    or not isinstance(verdict, Mapping) or verdict.get("verdict") != "CONFIRMED"
                    or not required_evidence.issubset(set(verdict.get("evidence_refs", [])))):
                factual_requirements_met = False
        else:
            claim = claims.get(requirement["claim_id"])
            if not isinstance(claim, Mapping) or not required_evidence.issubset(set(claim.get("evidence_refs", []))) \
                    or not required_evidence.issubset(set(executor.get("evidence_refs", []))):
                factual_requirements_met = False

    if verification is not None:
        target_ids = set(authority["verification_target_claim_ids"])
        verdicts = {item["claim_id"]: item["verdict"] for item in verification["claim_verdicts"]}
        if target_ids - (set(claims) | verifier_claim_ids | director_claim_ids) or target_ids - set(verdicts):
            return _out("ESCALATE", "VERIFICATION_TARGET_IDENTITY_MISMATCH")
        effective_outcome = _effective_verification_outcome(verification["status"], target_ids, verdicts)
        mapped = authority["verification_outcome_map"].get(effective_outcome)
        if mapped not in BATONS or effective_outcome not in authority["allowed_verification_outcomes"]:
            return _incomplete(authority, artifacts, assignment_id, str(current["artifact_id"]))
        if mapped != "COMPLETE":
            return _out(mapped, "AUTHORIZED_VERIFICATION_OUTCOME", verification_outcome=effective_outcome)

    if factual_requirements_met and executor.get("status") == "COMPLETE":
        scope = review_gate.get("delivery_scope") if isinstance(review_gate, Mapping) else None
        return _out("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED", **({"delivery_scope": scope} if scope else {}))
    return _incomplete(authority, artifacts, assignment_id, str(current["artifact_id"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one local structured post-spawn control bundle")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; stdin when omitted")
    args = parser.parse_args()
    try:
        with (open(args.bundle, encoding="utf-8") if args.bundle else sys.stdin) as source:
            result = resolve_transition(json.load(source))
    except (OSError, json.JSONDecodeError) as exc:
        result = _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[str(exc)])
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("control_state") in BATONS else 1


if __name__ == "__main__":
    raise SystemExit(main())
