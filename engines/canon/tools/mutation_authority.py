"""Canon-local deterministic gate for accepted mutation materialization."""
from __future__ import annotations

from collections.abc import Iterable, Mapping

OWNER_MUTATION_SELECTION = "AUTHORIZE_CANON_MUTATION"

_RULES: dict[str, dict[str, object]] = {
    "CANON_RECONCILIATION_RESULT": {
        "authority_field": "mutation_authority_ref",
        "target_field": "source_canon_ref",
        "scope_field": None,
        "allowed_workflows": {"reconcile_research_into_canon"},
        "nonaccepted_statuses": {"PROPOSED", "READY_FOR_AUTHORITY", "BLOCKED", "SUPERSEDED"},
    },
    "CANON_CHANGE_PROPOSAL": {
        "authority_field": "authority_ref",
        "target_field": "prior_canon_ref",
        "scope_field": "scope",
        "allowed_workflows": {"reconcile_research_into_canon", "manage_production_canon_change"},
        "nonaccepted_statuses": {"PROPOSED", "BLOCKED", "SUPERSEDED"},
    },
}


class CanonMutationAuthorityError(RuntimeError):
    """Raised when an accepted Canon mutation cannot prove governed authority."""

    def __init__(self, result: Mapping[str, object]):
        self.result = dict(result)
        super().__init__(str(result.get("reason", "CANON_MUTATION_AUTHORITY_REJECTED")))


def _reject(reason: str, **details: object) -> dict[str, object]:
    return {"status": "REJECTED", "authority_required": True, "reason": reason, **details}


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object, *, nonempty: bool = False) -> list[str] | None:
    if not isinstance(value, list) or not all(_nonempty_string(item) for item in value):
        return None
    if nonempty and not value:
        return None
    return [str(item).strip() for item in value]


def _artifact_index(
    artifacts: Iterable[Mapping[str, object]] | Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, Mapping[str, object]] | None, str | None]:
    values = artifacts.values() if isinstance(artifacts, Mapping) else artifacts
    try:
        items = list(values)
    except TypeError:
        return None, "CANON_MUTATION_ARTIFACT_SET_MALFORMED"
    index: dict[str, Mapping[str, object]] = {}
    for artifact in items:
        if not isinstance(artifact, Mapping):
            return None, "CANON_MUTATION_ARTIFACT_SET_MALFORMED"
        artifact_id = artifact.get("artifact_id")
        if not _nonempty_string(artifact_id):
            return None, "CANON_MUTATION_ARTIFACT_SET_MALFORMED"
        ref = str(artifact_id).strip()
        if ref in index:
            return None, "CANON_MUTATION_ARTIFACT_IDENTITY_CONFLICT"
        index[ref] = artifact
    return index, None


def check_mutation_authority(
    candidate: Mapping[str, object],
    workflow_id: str,
    artifacts: Iterable[Mapping[str, object]] | Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Prove governed authority for an accepted Canon mutation candidate.

    Structural schema validation remains a separate prior step. This gate
    resolves the authority reference and proves operation, target, project and
    scope semantics before an accepted artifact may be durably materialized.
    """
    if not isinstance(candidate, Mapping):
        return _reject("CANON_MUTATION_ARTIFACT_MALFORMED")
    artifact_type = candidate.get("artifact_type")
    if artifact_type not in _RULES:
        return _reject("CANON_MUTATION_ARTIFACT_UNSUPPORTED", artifact_type=artifact_type)
    rule = _RULES[str(artifact_type)]

    if not _nonempty_string(workflow_id):
        return _reject("CANON_MUTATION_WORKFLOW_INVALID")
    allowed_workflows = rule["allowed_workflows"]
    if workflow_id not in allowed_workflows:
        return _reject(
            "CANON_MUTATION_WORKFLOW_MISMATCH",
            artifact_type=artifact_type,
            workflow_id=workflow_id,
        )

    status = candidate.get("status")
    nonaccepted_statuses = rule["nonaccepted_statuses"]
    if status in nonaccepted_statuses:
        return {
            "status": "NOT_REQUIRED",
            "authority_required": False,
            "artifact_type": artifact_type,
            "workflow_id": workflow_id,
        }
    if status != "ACCEPTED":
        return _reject("CANON_MUTATION_STATUS_INVALID", artifact_type=artifact_type, status=status)

    authority_field = str(rule["authority_field"])
    target_field = str(rule["target_field"])
    authority_ref = candidate.get(authority_field)
    target_ref = candidate.get(target_field)
    project_id = candidate.get("project_id")
    if not _nonempty_string(authority_ref):
        return _reject("CANON_MUTATION_AUTHORITY_REF_REQUIRED", authority_field=authority_field)
    if not _nonempty_string(target_ref):
        return _reject("CANON_MUTATION_TARGET_INVALID", target_field=target_field)
    if not _nonempty_string(project_id):
        return _reject("CANON_MUTATION_PROJECT_INVALID")

    authority_ref = str(authority_ref).strip()
    target_ref = str(target_ref).strip()
    project_id = str(project_id).strip()

    index, index_error = _artifact_index(artifacts)
    if index_error:
        return _reject(index_error)
    assert index is not None
    authority = index.get(authority_ref)
    if authority is None:
        return _reject("CANON_MUTATION_AUTHORITY_UNRESOLVED", authority_ref=authority_ref)

    if authority.get("artifact_type") != "OWNER_DECISION_RECORD":
        return _reject("CANON_MUTATION_AUTHORITY_TYPE_MISMATCH", authority_ref=authority_ref)
    if authority.get("produced_by_role") != "owner-interface":
        return _reject("CANON_MUTATION_AUTHORITY_PRODUCER_MISMATCH", authority_ref=authority_ref)
    if authority.get("status") != "RECORDED":
        return _reject("CANON_MUTATION_AUTHORITY_STATUS_MISMATCH", authority_ref=authority_ref)
    if authority.get("authority_role") != "OWNER_K0":
        return _reject("CANON_MUTATION_AUTHORITY_ROLE_MISMATCH", authority_ref=authority_ref)

    provenance = _string_list(authority.get("provenance"), nonempty=True)
    if provenance is None:
        return _reject("CANON_MUTATION_AUTHORITY_PROVENANCE_MISSING", authority_ref=authority_ref)

    if not isinstance(authority.get("owner_constraints"), list) or not isinstance(
        authority.get("consequences_acknowledged"), list
    ):
        return _reject("CANON_MUTATION_OWNER_DECISION_MALFORMED", authority_ref=authority_ref)

    direct = "canon_input_mode" in authority
    if direct:
        if (authority.get("canon_input_mode") != "DIRECT_INSTRUCTION"
                or not _nonempty_string(authority.get("canon_instruction_text"))
                or any(field in authority for field in (
                    "question_ref", "options_presented", "selected_option",
                    "resource_input_mode", "resource_interpretation",
                ))):
            return _reject("CANON_MUTATION_OWNER_DECISION_MALFORMED", authority_ref=authority_ref)
    else:
        if ("canon_instruction_text" in authority or not _nonempty_string(authority.get("question_ref"))):
            return _reject("CANON_MUTATION_OWNER_DECISION_MALFORMED", authority_ref=authority_ref)
        options = _string_list(authority.get("options_presented"), nonempty=True)
        if options is None:
            return _reject("CANON_MUTATION_OWNER_DECISION_MALFORMED", authority_ref=authority_ref)
        if authority.get("selected_option") != OWNER_MUTATION_SELECTION or OWNER_MUTATION_SELECTION not in options:
            return _reject("CANON_MUTATION_AUTHORITY_SELECTION_MISMATCH", authority_ref=authority_ref)
    if authority.get("decision_kind") != workflow_id:
        return _reject(
            "CANON_MUTATION_AUTHORITY_WORKFLOW_MISMATCH",
            authority_ref=authority_ref,
            workflow_id=workflow_id,
        )
    if authority.get("input_state_ref") != target_ref:
        return _reject(
            "CANON_MUTATION_AUTHORITY_TARGET_MISMATCH",
            authority_ref=authority_ref,
            target_ref=target_ref,
        )
    if authority.get("project_id") != project_id:
        return _reject(
            "CANON_MUTATION_AUTHORITY_PROJECT_MISMATCH",
            authority_ref=authority_ref,
            project_id=project_id,
        )

    scope_field = rule["scope_field"]
    if scope_field is None:
        expected_scope = target_ref
    else:
        scope_value = candidate.get(str(scope_field))
        if not _nonempty_string(scope_value):
            return _reject("CANON_MUTATION_SCOPE_INVALID", scope_field=scope_field)
        expected_scope = str(scope_value).strip()
    if authority.get("authorized_scope") != expected_scope:
        return _reject(
            "CANON_MUTATION_AUTHORITY_SCOPE_MISMATCH",
            authority_ref=authority_ref,
            expected_scope=expected_scope,
        )

    candidate_related = _string_list(candidate.get("related_artifacts"))
    if candidate_related is None or target_ref not in candidate_related or authority_ref not in candidate_related:
        return _reject(
            "CANON_MUTATION_AUTHORITY_LINEAGE_MISSING",
            authority_ref=authority_ref,
            target_ref=target_ref,
        )
    authority_related = _string_list(authority.get("related_artifacts"))
    if authority_related is None or target_ref not in authority_related:
        return _reject(
            "CANON_MUTATION_AUTHORITY_TARGET_LINEAGE_MISSING",
            authority_ref=authority_ref,
            target_ref=target_ref,
        )

    result = {
        "status": "PROVEN",
        "authority_required": True,
        "artifact_type": artifact_type,
        "workflow_id": workflow_id,
        "authority_ref": authority_ref,
        "target_ref": target_ref,
        "project_id": project_id,
        "authorized_scope": expected_scope,
    }
    if direct:
        result["input_mode"] = "DIRECT_INSTRUCTION"
    else:
        result["selection"] = OWNER_MUTATION_SELECTION
    return result


def guard_mutation_materialization(
    candidate: Mapping[str, object],
    workflow_id: str,
    artifacts: Iterable[Mapping[str, object]] | Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Fail closed before durable ACCEPTED Canon mutation materialization."""
    result = check_mutation_authority(candidate, workflow_id, artifacts)
    if result.get("status") == "REJECTED":
        raise CanonMutationAuthorityError(result)
    return result
