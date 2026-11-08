#!/usr/bin/env python3
"""Thin, bundle-local composition of governed pre-spawn control artifacts."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.assignment_compiler import (
    ARCHITECTURE_HEALTH_RECONCILIATION_REQUIRED,
    ARCHITECTURE_HEALTH_REVIEW_REQUIRED,
    _executor_capabilities, _strings,
    compile_assignment, validate_compiled_assignment,
)
from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_assignment_execution_contract,
    validate_capability_profile,
    validate_execution_route,
    validate_state_observation,
)
from tools.github_candidate_handoff import validate_delivery_requirement
from tools.research_policy import admit_work_package
from tools.resource_admission import ResourceAdmissionError, evaluate_resource_admission
from tools.resource_ledger import ResourceLedger, ResourceLedgerError
from tools.workflow_contract import resolve_workflow_contract, requires_project_topology
from tools.project_topology import TopologyError, resolve_address, verify_bootstrap
from tools.project_topology_repository import verify_repository_shell

TERMINAL_STATES = {"WAIT", "ESCALATE", "COMPLETE"}
SEMANTIC_FIELDS = ("objective", "authority", "scope", "acceptance", "stop_conditions", "result_to")
RESEARCH_POLICY_SURFACE = "tools.research_policy.admit_work_package"
RESEARCH_CONTROL_ONLY_WORKFLOWS = {"reconcile_research_chain": "research_chain_reconciliation"}
RESEARCH_CONTROL_ONLY_CAPABILITIES = set(RESEARCH_CONTROL_ONLY_WORKFLOWS)
RESEARCH_RECONCILIATION_INPUT_FIELD = "research_reconciliation_inputs"
RESEARCH_RECONCILIATION_REQUIRED_CAPABILITY = "durable_artifact_write"
RESEARCH_RESULT_FIELDS = {"ADMISSION_STATUS", "ERROR_CODE", "REQUIRE_MACHINE_REDESIGN", "ERRORS"}
RESEARCH_ADMISSION_FIELDS = {
    "artifact_id", *RESEARCH_RESULT_FIELDS, "WORK_PACKAGE_ID", "QUESTION_ID", "POLICY_SURFACE", "PROVENANCE", "WORK_PACKAGE",
}
RESOURCE_GOVERNANCE_FIELDS = {
    "resource_admission_id", "resource_estimate_ref", "resource_grant_ref",
    "availability_evidence_refs", "unclassified_metered_side_effect_refs",
}


def _out(control_state: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": control_state, "control_state": control_state, "reason": reason, **details}


def _artifact_resolver(artifacts: object):
    if not isinstance(artifacts, list):
        return None, {}, ["artifacts must be a list"]
    by_id: dict[str, Mapping[str, object]] = {}
    errors: list[str] = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, Mapping):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            errors.append(f"artifacts[{index}].artifact_id must be a non-empty string")
            continue
        if artifact_id in by_id:
            errors.append(f"duplicate artifact_id: {artifact_id}")
            continue
        by_id[artifact_id] = item
    return by_id.get, by_id, errors


def _profile_is_only_stale(errors: list[str]) -> bool:
    """Classify freshness failures already reported by the authoritative validator."""
    return bool(errors) and all("expired" in error for error in errors)


def _valid_prerequisites(value: object) -> tuple[list[dict[str, object]], list[str]]:
    if not isinstance(value, list):
        return [], ["selected_prerequisite_actions must be a list"]
    actions, errors = [], []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"selected_prerequisite_actions[{index}] must be an object")
            continue
        action = deepcopy(dict(item))
        if not isinstance(action.get("action_id"), str) or not action["action_id"].strip():
            errors.append(f"selected_prerequisite_actions[{index}].action_id must be non-empty")
        capabilities = action.get("required_capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(cap, str) and cap.strip() for cap in capabilities):
            errors.append(f"selected_prerequisite_actions[{index}].required_capabilities must be a string list")
        evidence = action.get("evidence_path")
        if evidence is not None and (not isinstance(evidence, str) or not evidence.strip()):
            errors.append(f"selected_prerequisite_actions[{index}].evidence_path must be null or non-empty")
        responsibility = action.get("responsibility", "EXECUTOR")
        if responsibility not in ("EXECUTOR", "CONTROL", "PLATFORM"):
            errors.append(f"selected_prerequisite_actions[{index}].responsibility is invalid")
        actions.append(action)
    return actions, errors


def _same_json_value(left: object, right: object) -> bool:
    """Compare JSON values recursively without equating booleans and numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        return (isinstance(left, Mapping) and isinstance(right, Mapping)
                and left.keys() == right.keys()
                and all(_same_json_value(value, right[key]) for key, value in left.items()))
    if isinstance(left, list) or isinstance(right, list):
        return (isinstance(left, list) and isinstance(right, list) and len(left) == len(right)
                and all(_same_json_value(a, b) for a, b in zip(left, right)))
    return left == right


def _same_prerequisite(prerequisite: Mapping[str, object], obligation: Mapping[str, object]) -> bool:
    """Only collapse a selection when every declared semantic field matches."""
    if prerequisite.get("responsibility", "EXECUTOR") != obligation.get("responsibility"):
        return False
    selected_caps = prerequisite.get("required_capabilities")
    compiled_caps = obligation.get("required_capabilities")
    if (not isinstance(selected_caps, list) or not isinstance(compiled_caps, list)
            or not all(isinstance(cap, str) and cap.strip() for cap in compiled_caps)
            or len(selected_caps) != len({cap.strip() for cap in selected_caps})
            or len(compiled_caps) != len({cap.strip() for cap in compiled_caps})
            or sorted(cap.strip() for cap in selected_caps) != sorted(cap.strip() for cap in compiled_caps)):
        return False
    selected_path, compiled_path = prerequisite.get("evidence_path"), obligation.get("evidence_path")
    if isinstance(selected_path, str): selected_path = selected_path.strip()
    if isinstance(compiled_path, str): compiled_path = compiled_path.strip()
    if selected_path != compiled_path:
        return False
    return all(field in {"responsibility", "required_capabilities", "evidence_path"}
               or (field == "context_fact_ref" and _same_json_value(obligation.get(field), value))
               or (field in obligation and _same_json_value(obligation[field], value))
               for field, value in prerequisite.items())


def _carry_compilable_prerequisites(
    draft: Mapping[str, object], prerequisites: list[dict[str, object]],
) -> Mapping[str, object]:
    """Carry only complete existing obligation shapes; leave other selections intact."""
    required = {"action_id", "operation", "obligation_class", "required_capabilities", "claim_ref"}
    original_actions = draft.get("mandatory_actions", [])
    if not isinstance(original_actions, list):
        return draft
    evidence = draft.get("evidence_requirements", [])
    existing = {
        item.get("action_id")
        for group in (original_actions, evidence) if isinstance(group, list)
        for item in group if isinstance(item, Mapping) and isinstance(item.get("action_id"), str)
    }
    additions = []
    for item in prerequisites:
        if (item.get("responsibility", "EXECUTOR") != "EXECUTOR"
                or not required.issubset(item)
                or any(not isinstance(item.get(field), str) or not item[field].strip()
                       for field in ("operation", "obligation_class", "claim_ref"))
                or item["action_id"] in existing):
            continue
        carried = deepcopy(item)
        carried.setdefault("responsibility", "EXECUTOR")
        additions.append(carried)
        existing.add(item["action_id"])
    if not additions:
        return draft

    declared = _strings(draft.get("authorized_required_capabilities"))
    if declared and declared != _executor_capabilities(original_actions, evidence):
        # Let the existing compiler report the original inconsistency; a selected
        # action must not accidentally repair or mask an invalid declaration.
        return draft
    result = deepcopy(dict(draft))
    result["mandatory_actions"] = deepcopy(original_actions) + additions
    if declared:
        selected_caps = _executor_capabilities(additions, [])
        result["authorized_required_capabilities"] = sorted(set(declared) | set(selected_caps))
    return result


def _resource_governance(value: object) -> dict[str, object]:
    if (not isinstance(value, Mapping) or not RESOURCE_GOVERNANCE_FIELDS.issubset(value)
            or set(value) - (RESOURCE_GOVERNANCE_FIELDS | {"resource_interpretation_ref", "finalization_purpose"})):
        raise ResourceAdmissionError("resource_governance must contain RG-04 fields and supported optional resource fields")
    result = dict(value)
    text_fields = ["resource_admission_id", "resource_estimate_ref", "resource_grant_ref"]
    if "resource_interpretation_ref" in result:
        text_fields.append("resource_interpretation_ref")
    if "finalization_purpose" in result:
        text_fields.append("finalization_purpose")
    for field in text_fields:
        item = result.get(field)
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise ResourceAdmissionError(f"resource_governance.{field} must be a non-empty trimmed string")
    for field in ("availability_evidence_refs", "unclassified_metered_side_effect_refs"):
        refs = result.get(field)
        if not isinstance(refs, list) or not all(isinstance(ref, str) and ref.strip() and ref == ref.strip() for ref in refs):
            raise ResourceAdmissionError(f"resource_governance.{field} must be an array of non-empty trimmed strings")
        if len(refs) != len(set(refs)):
            raise ResourceAdmissionError(f"resource_governance.{field} must contain unique refs")
        result[field] = sorted(refs)
    return result


def _research_admission(
    decision: Mapping[str, object],
    artifacts: Mapping[str, Mapping[str, object]],
) -> tuple[Mapping[str, object] | None, dict[str, object] | None]:
    """Revalidate exact Research work through the existing Research policy surface."""
    admission_ref = decision.get("research_admission_ref")
    if not isinstance(admission_ref, str) or not admission_ref.strip():
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_REQUIRED", engine_id="research")
    selected_work_id = decision.get("research_work_package_id")
    selected_question_id = decision.get("research_question_id")
    if not isinstance(selected_work_id, str) or not selected_work_id.strip() or not isinstance(selected_question_id, str) or not selected_question_id.strip():
        return None, _out("ESCALATE", "RESEARCH_WORK_IDENTITY_REQUIRED", engine_id="research")

    admission = artifacts.get(admission_ref)
    if not isinstance(admission, Mapping):
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_UNRESOLVED", engine_id="research", research_admission_ref=admission_ref)
    if set(admission) != RESEARCH_ADMISSION_FIELDS:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("artifact_id") != admission_ref or admission.get("POLICY_SURFACE") != RESEARCH_POLICY_SURFACE:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)

    work_package = admission.get("WORK_PACKAGE")
    if not isinstance(work_package, Mapping):
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    work_id = work_package.get("WORK_PACKAGE_ID")
    question_id = work_package.get("QUESTION_ID")
    if not isinstance(work_id, str) or not work_id.strip() or not isinstance(question_id, str) or not question_id.strip():
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("WORK_PACKAGE_ID") != work_id or admission.get("QUESTION_ID") != question_id:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_IDENTITY_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if selected_work_id != work_id or selected_question_id != question_id:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_IDENTITY_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if admission.get("PROVENANCE") != [RESEARCH_POLICY_SURFACE, work_id, question_id]:
        return None, _out("ESCALATE", "MALFORMED_RESEARCH_ADMISSION", engine_id="research", research_admission_ref=admission_ref)

    authoritative_result = admit_work_package(dict(work_package))
    carried_result = {field: admission.get(field) for field in RESEARCH_RESULT_FIELDS}
    if carried_result != authoritative_result:
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_RESULT_MISMATCH", engine_id="research", research_admission_ref=admission_ref)
    if authoritative_result.get("ADMISSION_STATUS") != "ADMITTED_MACHINE_RESEARCH":
        return None, _out("ESCALATE", "RESEARCH_ADMISSION_NOT_ADMITTED", engine_id="research", research_admission_ref=admission_ref)
    return admission, None


def _research_reconciliation_inputs(
    semantics: Mapping[str, object],
    artifacts: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, list[str]] | None, dict[str, object] | None]:
    """Fail closed unless reconciliation receives exact durable Research refs and requirement refs."""
    value = semantics.get(RESEARCH_RECONCILIATION_INPUT_FIELD)
    if not isinstance(value, Mapping):
        return None, _out("ESCALATE", "RESEARCH_RECONCILIATION_INPUT_REQUIRED", engine_id="research")
    expected = {"upstream_research_refs", "downstream_requirement_refs"}
    if set(value) != expected:
        return None, _out("ESCALATE", "RESEARCH_RECONCILIATION_INPUT_MALFORMED", engine_id="research")

    normalized: dict[str, list[str]] = {}
    for field in ("upstream_research_refs", "downstream_requirement_refs"):
        refs = value.get(field)
        if (not isinstance(refs, list) or not refs
                or not all(isinstance(ref, str) and ref.strip() and ref == ref.strip() for ref in refs)
                or len(refs) != len(set(refs))):
            return None, _out("ESCALATE", "RESEARCH_RECONCILIATION_INPUT_MALFORMED",
                              engine_id="research", field=field)
        normalized[field] = list(refs)

    for ref in normalized["upstream_research_refs"]:
        artifact = artifacts.get(ref)
        if not isinstance(artifact, Mapping):
            return None, _out("ESCALATE", "RESEARCH_RECONCILIATION_UPSTREAM_UNRESOLVED",
                              engine_id="research", upstream_ref=ref)
        provenance = artifact.get("provenance")
        if (not isinstance(provenance, list) or not provenance
                or not all(isinstance(item, str) and item.strip() for item in provenance)):
            return None, _out("ESCALATE", "RESEARCH_RECONCILIATION_UPSTREAM_PROVENANCE_MISSING",
                              engine_id="research", upstream_ref=ref)
    return normalized, None


def resolve_spawn(
    control_bundle: Mapping[str, object],
    *,
    resource_state_reader: object | None = None,
    now: object | None = None,
    topology_port: object | None = None,
    topology_root: object | None = None,
) -> dict[str, object]:
    """Resolve one already-selected local control bundle to a baton outcome."""
    if not isinstance(control_bundle, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    resource_governed = "resource_governance" in control_bundle
    decision = control_bundle.get("decision")
    if not isinstance(decision, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["decision must be an object"])
    state = decision.get("control_state")
    if state in TERMINAL_STATES:
        return _out(str(state), "INPUT_CONTROL_STATE_PRESERVED")
    if state != "ASSIGN":
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["control_state is invalid"])
    for field in ("engine_id", "engine_status", "semantic_capability", "workflow_id"):
        if not isinstance(decision.get(field), str) or not str(decision[field]).strip():
            return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[f"decision.{field} is required"])
    if decision["engine_status"] != "available":
        reason = "ENGINE_NOT_MATERIALIZED" if decision["engine_status"] == "not_materialized" else "ENGINE_UNAVAILABLE"
        return _out("ESCALATE", reason, engine_id=decision["engine_id"])
    if "additional_required_capabilities" in control_bundle or "final_required_capabilities" in control_bundle:
        return _out("ESCALATE", "UNACCOUNTED_CAPABILITY_EXPANSION")

    resolver, artifacts, artifact_errors = _artifact_resolver(control_bundle.get("artifacts", []))
    if artifact_errors:
        reason = "CONTRADICTORY_CONTROL_ARTIFACTS" if any(error.startswith("duplicate artifact_id:") for error in artifact_errors) else "MALFORMED_CONTROL_ARTIFACT"
        return _out("ESCALATE", reason, errors=artifact_errors)

    workflow_proof = resolve_workflow_contract(
        decision,
        control_bundle.get("workflow_prerequisite_bindings"),
        resolver,
    )
    if workflow_proof.get("status") == "ERROR":
        return _out("ESCALATE", str(workflow_proof.get("reason")),
                    engine_id=decision["engine_id"], workflow_id=decision["workflow_id"],
                    workflow_contract_source=workflow_proof.get("contract_source"),
                    workflow_contract_details={key: value for key, value in workflow_proof.items()
                                               if key not in {"status", "reason", "contract_source"}})
    workflow_refs = workflow_proof.get("proof_refs", []) if workflow_proof.get("status") == "PROVEN" else []
    if not isinstance(workflow_refs, list):
        return _out("ESCALATE", "WORKFLOW_CONTRACT_MALFORMED")

    research_admission = None
    reconciliation_selected = (
        decision["engine_id"] == "research"
        and decision["semantic_capability"] in RESEARCH_CONTROL_ONLY_CAPABILITIES
    )
    if reconciliation_selected:
        expected_workflow = RESEARCH_CONTROL_ONLY_WORKFLOWS[str(decision["semantic_capability"])]
        if decision["workflow_id"] != expected_workflow:
            return _out("ESCALATE", "RESEARCH_CONTROL_WORKFLOW_IDENTITY_MISMATCH",
                        engine_id="research", semantic_capability=decision["semantic_capability"],
                        workflow_id=decision["workflow_id"], expected_workflow_id=expected_workflow)
    elif decision["engine_id"] == "research":
        research_admission, research_error = _research_admission(decision, artifacts)
        if research_error is not None:
            return research_error

    state_observation_ref = control_bundle.get("input_state_observation_ref")
    state_observation = artifacts.get(state_observation_ref) if isinstance(state_observation_ref, str) else None
    if not isinstance(state_observation, Mapping):
        return _out("ESCALATE", "INPUT_STATE_OBSERVATION_REQUIRED")
    state_errors = validate_state_observation(state_observation)
    if state_errors:
        return _out("ESCALATE", "MALFORMED_STATE_OBSERVATION", errors=state_errors)
    draft = control_bundle.get("assignment_compilation_draft")
    semantics = control_bundle.get("assignment_draft_semantics")
    if not isinstance(draft, Mapping) or not isinstance(semantics, Mapping):
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT")
    draft_context, semantic_context = draft.get("architecture_context"), semantics.get("architecture_context")
    if draft_context is not None and semantic_context is not None and draft_context != semantic_context:
        return _out("ESCALATE", "ARCHITECTURE_CONTEXT_MISMATCH")
    if draft_context is None and semantic_context is not None:
        draft = {**draft, "architecture_context": deepcopy(semantic_context)}
    missing_semantics = [field for field in SEMANTIC_FIELDS if field not in semantics]
    if missing_semantics:
        return _out("ESCALATE", "MISSING_ASSIGNMENT_SEMANTICS", errors=missing_semantics)

    software_code_change = (decision["engine_id"] == "production/software"
                            and decision["semantic_capability"] == "implement_software_change")
    if software_code_change and "github_candidate_delivery" not in semantics:
        return _out("ESCALATE", "SOFTWARE_GITHUB_CANDIDATE_DELIVERY_REQUIRED")
    if "github_candidate_delivery" in semantics:
        candidate_errors = validate_delivery_requirement(semantics["github_candidate_delivery"])
        if candidate_errors:
            return _out("ESCALATE", "SOFTWARE_GITHUB_CANDIDATE_DELIVERY_INVALID",
                        errors=candidate_errors)

    topology_bindings = None
    topology_context = state_observation.get("project_topology_context")
    try:
        writes_payload = requires_project_topology(str(decision["engine_id"]), str(decision["semantic_capability"]))
    except (ValueError, OSError) as exc:
        return _out("ESCALATE", "TOPOLOGY_WRITE_POLICY_INVALID", errors=[str(exc)])
    supplied_intents = semantics.get("project_payload_intents")
    if topology_context is not None and (writes_payload or supplied_intents is not None):
        if topology_port is None:
            return _out("WAIT", "CURRENT_TOPOLOGY_READBACK_REQUIRED")
        try:
            current = verify_bootstrap(topology_port, topology_context["system_of_record_ref"],
                                       topology_context["current_topology_ref"])
            if current.project_id != topology_context["project_id"] or current.manifest["storage_mode"] != topology_context["storage_mode"]:
                raise TopologyError("TOPOLOGY_STATE_IDENTITY_MISMATCH")
            if current.manifest["storage_mode"] in {"REPO_ONLY", "DRIVE_THEN_REPO"}:
                if topology_root is None:
                    return _out("WAIT", "TOPOLOGY_PHYSICAL_READBACK_REQUIRED")
                verify_repository_shell(topology_root, current)
            else:
                return _out("WAIT", "TOPOLOGY_PROVIDER_READBACK_REQUIRED")
            if not isinstance(supplied_intents, list) or not supplied_intents:
                return _out("ESCALATE", "PROJECT_PAYLOAD_INTENTS_REQUIRED")
            topology_bindings = []
            for item in supplied_intents:
                if not isinstance(item, Mapping) or set(item) != {"artifact_class", "artifact_id", "scope"}:
                    raise TopologyError("PROJECT_PAYLOAD_INTENT_MALFORMED")
                address = resolve_address(current, item["artifact_class"], item["artifact_id"], item["scope"])
                topology_bindings.append({"artifact_class": item["artifact_class"],
                    "artifact_id": item["artifact_id"], "canonical_address": address,
                    "project_id": current.project_id, "scope": deepcopy(item["scope"]),
                    "topology_ref": current.bootstrap_ref,
                    "system_of_record_ref": current.system_of_record_ref})
            if len({item["canonical_address"] for item in topology_bindings}) != len(topology_bindings):
                raise TopologyError("PROJECT_PAYLOAD_INTENT_DUPLICATE")
        except (KeyError, TypeError, TopologyError) as exc:
            return _out("ESCALATE", getattr(exc, "code", "TOPOLOGY_STATE_INVALID"), errors=[str(exc)])
    elif supplied_intents is not None and topology_context is None:
        return _out("ESCALATE", "PROJECT_TOPOLOGY_CONTEXT_REQUIRED")
    required_workflow_outputs = workflow_proof.get("required_durable_output_ids", [])
    if required_workflow_outputs:
        declared_outputs = semantics.get("required_durable_outputs")
        if (not isinstance(declared_outputs, list)
                or len(declared_outputs) != len(required_workflow_outputs)
                or not all(isinstance(item, str) for item in declared_outputs)
                or set(declared_outputs) != set(required_workflow_outputs)):
            return _out("ESCALATE", "WORKFLOW_REQUIRED_OUTPUTS_MISMATCH",
                        engine_id=decision["engine_id"], workflow_id=decision["workflow_id"])

    reconciliation_inputs = None
    if reconciliation_selected:
        reconciliation_inputs, reconciliation_error = _research_reconciliation_inputs(semantics, artifacts)
        if reconciliation_error is not None:
            return reconciliation_error

    prerequisites, prerequisite_errors = _valid_prerequisites(control_bundle.get("selected_prerequisite_actions", []))
    prerequisite_ids = [item.get("action_id") for item in prerequisites]
    if not prerequisite_errors and len(prerequisite_ids) == len(set(prerequisite_ids)):
        draft = _carry_compilable_prerequisites(draft, prerequisites)

    envelope_ref = control_bundle.get("execution_envelope_ref")
    compiled = compile_assignment(draft, envelope_ref, resolver, resolver, current_state_ref=state_observation_ref) if isinstance(envelope_ref, str) and envelope_ref.strip() else None
    if compiled is None:
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=["execution_envelope_ref is required"])
    if compiled.get("compilation_status") != "COMPILED":
        errors = compiled.get("compilation_errors", [])
        health_codes = {ARCHITECTURE_HEALTH_REVIEW_REQUIRED, ARCHITECTURE_HEALTH_RECONCILIATION_REQUIRED}
        codes = {item.get("code") for item in errors if isinstance(item, Mapping)}
        if codes and codes.issubset(health_codes):
            reason = ARCHITECTURE_HEALTH_RECONCILIATION_REQUIRED if ARCHITECTURE_HEALTH_RECONCILIATION_REQUIRED in codes else ARCHITECTURE_HEALTH_REVIEW_REQUIRED
            return _out("WAIT", reason, compilation_errors=errors)
        return _out("ESCALATE", "COMPILE_REJECTED", compilation_errors=compiled.get("compilation_errors", []))
    compiled_errors = validate_compiled_assignment(compiled, resolver, resolver)
    if compiled_errors:
        return _out("ESCALATE", "COMPILED_ASSIGNMENT_INVALID", errors=compiled_errors)
    if prerequisite_errors:
        return _out("ESCALATE", "MALFORMED_PREREQUISITE_ACTION", errors=prerequisite_errors)
    compiled_actions = [
        deepcopy(item) for item in compiled["authorized_mandatory_actions"]
        if isinstance(item, Mapping) and item.get("responsibility") == "EXECUTOR"
    ]
    compiled_evidence = [
        deepcopy(item) for item in compiled["authorized_evidence_requirements"]
        if isinstance(item, Mapping) and item.get("responsibility") == "EXECUTOR"
    ]
    # An explicitly non-Executor prerequisite must already be an authorized
    # compiled obligation for that responsibility. It remains in the compiled
    # assignment for the responsible actor; merely naming a role neither proves
    # that actor's capabilities nor completes its later evidence obligation.
    authorized = compiled["authorized_mandatory_actions"] + compiled["authorized_evidence_requirements"]
    executor_prerequisites = []
    selected_ids = set()
    for prerequisite in prerequisites:
        action_id = prerequisite["action_id"]
        if action_id in selected_ids:
            return _out("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS",
                        errors=["duplicate selected prerequisite action id"])
        selected_ids.add(action_id)
        responsibility = prerequisite.get("responsibility", "EXECUTOR")
        matches = [item for item in authorized if isinstance(item, Mapping)
                   and item.get("action_id") == action_id]
        if matches:
            if len(matches) != 1 or not _same_prerequisite(prerequisite, matches[0]):
                reason = ("CONTRADICTORY_CONTROL_ARTIFACTS" if responsibility == "EXECUTOR"
                          else "PREREQUISITE_ACTOR_BINDING_INVALID")
                return _out("ESCALATE", reason, action_id=action_id)
            # The compiled obligation already carries this exact action and its
            # authority/evidence; adding it again would create a false duplicate.
            continue
        if responsibility != "EXECUTOR":
            return _out("ESCALATE", "PREREQUISITE_ACTOR_BINDING_INVALID", action_id=action_id)
        executor_prerequisites.append(prerequisite)
    final_actions = compiled_actions + compiled_evidence + executor_prerequisites
    capability_errors = []
    for index, action in enumerate(final_actions):
        capabilities = action.get("required_capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(cap, str) and cap.strip() for cap in capabilities):
            capability_errors.append(f"final mandatory action[{index}].required_capabilities must be a string list")
    if capability_errors:
        return _out("ESCALATE", "MALFORMED_MANDATORY_ACTION", errors=capability_errors)
    action_ids = [item.get("action_id") for item in final_actions if isinstance(item, Mapping)]
    if len(action_ids) != len(set(action_ids)):
        return _out("ESCALATE", "CONTRADICTORY_CONTROL_ARTIFACTS", errors=["duplicate final mandatory action id"])
    required = sorted({cap.strip() for action in final_actions for cap in action.get("required_capabilities", [])})
    if reconciliation_selected and RESEARCH_RECONCILIATION_REQUIRED_CAPABILITY not in required:
        return _out("ESCALATE", "RESEARCH_RECONCILIATION_DURABLE_OUTPUT_REQUIRED",
                    engine_id="research", required_capability=RESEARCH_RECONCILIATION_REQUIRED_CAPABILITY)
    if topology_bindings is not None and "durable_artifact_write" not in required:
        return _out("ESCALATE", "TOPOLOGY_PAYLOAD_DURABLE_ACTION_REQUIRED")
    paths = sorted({path for action in final_actions if isinstance((path := action.get("evidence_path")), str) and path.strip()})

    profile_ref, route_ref = control_bundle.get("capability_profile_ref"), control_bundle.get("route_ref")
    invalid_refs = [
        field for field, value in (("capability_profile_ref", profile_ref), ("route_ref", route_ref))
        if not isinstance(value, str) or not value.strip()
    ]
    if invalid_refs:
        return _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[f"{field} must be a non-empty string" for field in invalid_refs])
    profile, route = artifacts.get(profile_ref), artifacts.get(route_ref)
    if not isinstance(profile, Mapping) or not isinstance(route, Mapping):
        return _out("ESCALATE", "REFERENCE_IDENTITY_MISMATCH")
    profile_errors = validate_capability_profile(profile, resolver)
    if profile_errors:
        state = "WAIT" if _profile_is_only_stale(profile_errors) else "ESCALATE"
        reason = "CAPABILITY_PROFILE_STALE" if state == "WAIT" else "MALFORMED_CAPABILITY_PROFILE"
        return _out(state, reason, errors=profile_errors, capability_profile_ref=profile_ref)
    route_profiles = {key: value for key, value in artifacts.items() if isinstance(value, Mapping) and value.get("artifact_type") == "CAPABILITY_PROFILE"}
    route_errors = validate_execution_route(route, route_profiles, resolver)
    if route_errors:
        return _out("ESCALATE", "EXECUTION_ROUTE_INVALID", errors=route_errors)

    if software_code_change:
        # Publication is a mandatory route capability on the *publisher*
        # segment, which need not be the code Executor's destination.
        delivery_segments = [segment for segment in route.get("segments", [])
                             if isinstance(segment, Mapping)
                             and segment.get("route_role") == "CANDIDATE_DELIVERY"]
        delivery = delivery_segments[0] if len(delivery_segments) == 1 else None
        allowed = set(semantics["github_candidate_delivery"]["allowed_kinds"])
        publish_modes = {"PULL_REQUEST": "pull_request_create", "BRANCH": "remote_branch_write"}
        allowed_publish = {publish_modes[kind] for kind in allowed}
        declared_publish = set(delivery.get("required_capabilities", [])) if isinstance(delivery, Mapping) else set()
        if not allowed_publish.intersection(declared_publish):
            return _out("WAIT", "SOFTWARE_GITHUB_PUBLISH_CAPABILITY_REQUIRED",
                        missing_publish_capabilities=sorted(allowed_publish))
        # allowed_kinds are alternatives; the selected route must prove the actual kind.
        # validate_execution_route already proves the delivery segment's
        # capabilities against its own exact profile and evidence.

    subset = evaluate_assignment_admissibility(required, profile.get("available_capabilities", []))
    research_refs = [str(research_admission["artifact_id"])] if isinstance(research_admission, Mapping) else []
    reconciliation_refs = reconciliation_inputs["upstream_research_refs"] if isinstance(reconciliation_inputs, Mapping) else []
    proof_refs = list(dict.fromkeys([*research_refs, *(str(ref) for ref in workflow_refs), *reconciliation_refs]))
    admissibility = {
        "artifact_type": "ASSIGNMENT_ADMISSIBILITY", "artifact_id": control_bundle.get("admissibility_id"),
        "produced_by_role": "control-director", "assignment_id": control_bundle.get("assignment_id"), "input_state_ref": draft.get("input_state_ref"),
        "status": subset["status"], "provenance": [str(profile_ref)], "related_artifacts": [str(profile_ref), str(route_ref), *proof_refs],
        "assignment_draft_id": draft.get("assignment_draft_ref"), "compiled_assignment_ref": compiled.get("artifact_id"),
        "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"),
        "capability_profile_ref": profile_ref, "route_ref": route_ref, "mandatory_actions": final_actions,
        "required_capabilities": required, "available_capabilities": subset["available_capabilities"],
        "unsatisfied_required_capabilities": subset["unsatisfied_required_capabilities"], "mandatory_evidence_paths": paths,
        "execution_mode": decision.get("execution_mode"),
        "transition_proof": {"proof_class": "ASSIGNMENT_ADMISSION", "proof_status": "PROVEN",
            "assignment_ref": control_bundle.get("assignment_id"), "admissibility_ref": control_bundle.get("admissibility_id"),
            "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"),
            "dependency_bindings": [{"dependency_ref": state_observation.get("artifact_id"),
                                     "proven_identity": state_observation.get("state_identity")}]},
    }
    admission_errors = validate_admissibility_against_profile(admissibility, profile, resolver)
    if admission_errors:
        return _out("ESCALATE", "ASSIGNMENT_ADMISSIBILITY_INVALID", errors=admission_errors)
    if subset["status"] != "ADMISSIBLE":
        return _out("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE", required_capabilities=required,
                    available_capabilities=subset["available_capabilities"], missing_capabilities=subset["unsatisfied_required_capabilities"],
                    destination_id=profile.get("destination_id"), capability_profile_ref=profile_ref)

    resource_admission = None
    governance = None
    if resource_governed:
        try:
            governance = _resource_governance(control_bundle.get("resource_governance"))
            if resource_state_reader is None:
                raise ResourceAdmissionError("resource_state_reader is required for resource-governed resolution")
            estimate_ref = str(governance["resource_estimate_ref"])
            grant_ref = str(governance["resource_grant_ref"])
            estimate = artifacts.get(estimate_ref)
            grant = artifacts.get(grant_ref)
            resource_arguments = dict(
                artifact_id=str(governance["resource_admission_id"]),
                assignment_id=str(control_bundle.get("assignment_id")),
                input_state_ref=draft.get("input_state_ref") if isinstance(draft.get("input_state_ref"), str) else None,
                compiled_assignment=compiled,
                assignment_admissibility=admissibility,
                route_ref=str(route_ref),
                state_identity=str(state_observation.get("state_identity")),
                resource_estimate_ref=estimate_ref,
                resource_estimate=estimate,
                resource_grant_ref=grant_ref,
                resource_grant=grant,
                resource_state_reader=resource_state_reader,
                authority_resolver=resolver,
                resource_interpretation_ref=governance.get("resource_interpretation_ref"),
                finalization_purpose=governance.get("finalization_purpose"),
                availability_evidence_refs=governance["availability_evidence_refs"],
                unclassified_metered_side_effect_refs=governance["unclassified_metered_side_effect_refs"],
                now=now,
            )
            resource_admission = evaluate_resource_admission(**resource_arguments)
            # RG-04 admission remains read-only. When its only missing input is
            # an explicitly authorized shared total, the existing ledger owner
            # may idempotently bind that total, then admission reads it again.
            # Ordinary grants and unrelated resource failures do not invoke it.
            if (resource_admission.get("blocking_reasons") == ["SHARED_LIMIT_REGISTRATION_REQUIRED"]
                    and callable(getattr(resource_state_reader, "register_owner_shared_limits", None))):
                try:
                    source_ref = resource_admission.get("resource_interpretation_ref")
                    resource_state_reader.register_owner_shared_limits(grant_ref, resolver, source_ref)
                except Exception as exc:
                    return _out("WAIT", "RESOURCE_SHARED_LIMIT_PREPARATION_FAILED",
                                errors=[str(exc)], assignment_admissibility=admissibility,
                                resource_admission=resource_admission)
                resource_admission = evaluate_resource_admission(**resource_arguments)
        except ResourceAdmissionError as exc:
            return _out("ESCALATE", "RESOURCE_ADMISSION_INVALID", errors=[str(exc)], assignment_admissibility=admissibility)
        if resource_admission.get("status") != "ADMISSIBLE":
            return _out("WAIT", "RESOURCE_NOT_ADMISSIBLE", assignment_admissibility=admissibility,
                        resource_admission=resource_admission)

    assignment = deepcopy(dict(semantics))
    if compiled.get("architecture_context") is not None:
        assignment["architecture_context"] = deepcopy(compiled["architecture_context"])
    if topology_bindings is not None:
        # Derived from independently read-back topology; never worker-supplied paths.
        assignment.pop("project_payload_intents", None)
        assignment["project_payload_bindings"] = topology_bindings
    assignment_provenance = [str(admissibility["artifact_id"])]
    assignment_related = [str(admissibility["artifact_id"]), str(profile_ref), str(route_ref), *proof_refs]
    execution_contract = {
        "assignment_draft_ref": draft.get("assignment_draft_ref"), "compiled_assignment_ref": compiled.get("artifact_id"),
        "destination_id": profile.get("destination_id"), "runtime_identity": profile.get("runtime_identity"), "capability_profile_ref": profile_ref,
        "admissibility_ref": admissibility.get("artifact_id"), "route_ref": route_ref, "proof_status": "PROVEN",
        "required_capabilities": required, "unsatisfied_required_capabilities": [], "mandatory_evidence_paths": paths,
        "execution_mode": decision.get("execution_mode")}
    if resource_admission is not None and governance is not None:
        resource_admission_ref = str(resource_admission["artifact_id"])
        estimate_ref = str(governance["resource_estimate_ref"])
        grant_ref = str(governance["resource_grant_ref"])
        execution_contract.update({
            "resource_admission_ref": resource_admission_ref,
            "resource_estimate_ref": estimate_ref,
            "resource_grant_ref": grant_ref,
        })
        if governance.get("finalization_purpose") is not None:
            execution_contract["resource_finalization_purpose"] = governance["finalization_purpose"]
        assignment_provenance = sorted({str(admissibility["artifact_id"]), resource_admission_ref})
        assignment_related = sorted(set([*assignment_related, resource_admission_ref, estimate_ref, grant_ref]))
    assignment.update({
        "artifact_type": "ASSIGNMENT", "artifact_id": control_bundle.get("assignment_id"), "produced_by_role": "control-director",
        "assignment_id": control_bundle.get("assignment_id"), "input_state_ref": draft.get("input_state_ref"), "status": "ISSUED",
        "provenance": assignment_provenance, "related_artifacts": assignment_related,
        "execution_contract": execution_contract,
    })
    proof_errors = validate_assignment_execution_contract(assignment, admissibility, profile, resolver, route, route_profiles,
                                                           compiled, resolver)
    if proof_errors:
        return _out("ESCALATE", "FINAL_ASSIGNMENT_PROOF_FAILED", errors=proof_errors)
    result = {"status": "SPAWN_READY", "control_state": "ASSIGN", "engine_id": decision["engine_id"],
              "workflow_id": decision["workflow_id"], "compiled_assignment_ref": compiled["artifact_id"],
              "capability_profile_ref": profile_ref, "route_ref": route_ref, "admissibility_ref": admissibility["artifact_id"],
              "assignment_ref": assignment["artifact_id"], "compiled_assignment": compiled,
              "assignment_admissibility": admissibility, "assignment": assignment,
              "capability_profile": profile, "execution_route": route,
              "input_state_observation": state_observation}
    if resource_admission is not None and governance is not None:
        result.update({
            "resource_admission_ref": resource_admission["artifact_id"],
            "resource_admission": resource_admission,
            "resource_estimate_ref": governance["resource_estimate_ref"],
            "resource_grant_ref": governance["resource_grant_ref"],
        })
    if workflow_proof.get("status") == "PROVEN":
        result["workflow_contract_source"] = workflow_proof.get("contract_source")
        result["workflow_prerequisite_refs"] = workflow_refs
    if isinstance(research_admission, Mapping):
        result["research_admission_ref"] = research_admission["artifact_id"]
        result["research_admission"] = research_admission
    return result


def _load_bundle(source: object) -> object:
    text = source.read()  # type: ignore[attr-defined]
    probe = json.loads(text)
    if isinstance(probe, Mapping) and "resource_governance" in probe:
        return json.loads(text, parse_float=Decimal)
    return probe


def _json_exact(value: object, *, level: int = 0, indent: int = 2) -> str:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ResourceAdmissionError("non-finite Decimal cannot be serialized as JSON")
        return str(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ResourceAdmissionError("JSON object keys must be strings")
        keys = sorted(value)
        if not keys:
            return "{}"
        pad = " " * (indent * (level + 1))
        close = " " * (indent * level)
        body = ",\n".join(f"{pad}{json.dumps(key, ensure_ascii=False)}: {_json_exact(value[key], level=level + 1, indent=indent)}" for key in keys)
        return "{\n" + body + "\n" + close + "}"
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        pad = " " * (indent * (level + 1))
        close = " " * (indent * level)
        body = ",\n".join(f"{pad}{_json_exact(item, level=level + 1, indent=indent)}" for item in value)
        return "[\n" + body + "\n" + close + "]"
    raise ResourceAdmissionError(f"unsupported JSON value type: {type(value).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one local structured control bundle to a pre-spawn outcome")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; stdin when omitted")
    parser.add_argument("--resource-ledger", help="Existing RG authority SQLite file for resource-governed resolution")
    args = parser.parse_args()
    try:
        with (open(args.bundle, encoding="utf-8") if args.bundle else sys.stdin) as source:
            bundle = _load_bundle(source)
        reader = None
        if isinstance(bundle, Mapping) and "resource_governance" in bundle:
            if not args.resource_ledger:
                result = _out("ESCALATE", "RESOURCE_ADMISSION_INVALID", errors=["--resource-ledger is required for resource-governed input"])
            else:
                ledger_path = Path(args.resource_ledger)
                if not ledger_path.exists() or not ledger_path.is_file():
                    result = _out("ESCALATE", "RESOURCE_ADMISSION_INVALID", errors=["resource ledger path must already exist and be a regular file"])
                else:
                    reader = ResourceLedger(ledger_path)
                    result = resolve_spawn(bundle, resource_state_reader=reader)
        else:
            result = resolve_spawn(bundle)  # type: ignore[arg-type]
    except (OSError, json.JSONDecodeError, ResourceLedgerError, ResourceAdmissionError) as exc:
        result = _out("ESCALATE", "MALFORMED_CONTROL_ARTIFACT", errors=[str(exc)])
    sys.stdout.write(_json_exact(result, indent=2))
    sys.stdout.write("\n")
    return 0 if result.get("control_state") in {"ASSIGN", "WAIT", "ESCALATE", "COMPLETE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
