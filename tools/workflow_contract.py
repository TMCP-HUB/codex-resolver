"""Thin engine-local workflow-contract resolution for pre-spawn composition."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ArtifactResolver = Callable[[str], Mapping[str, object] | None]


def _scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^\n#]+?)\s*$", text)
    return match.group(1).strip() if match else None


def _top_level_section(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*$", text)
    if not match:
        return None
    start = match.end()
    next_key = re.search(r"(?m)^[a-z0-9_]+:\s*(?:[^\n]*)$", text[start:])
    end = start + next_key.start() if next_key else len(text)
    return text[start:end]


def _simple_mapping(section: str | None) -> dict[str, str] | None:
    if section is None:
        return None
    result: dict[str, str] = {}
    for line in section.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"  ([a-z0-9_]+):\s*([a-z0-9_/-]+)\s*", line)
        if not match or match.group(1) in result:
            return None
        result[match.group(1)] = match.group(2)
    return result


def _workflow_requirements(section: str | None) -> dict[str, dict[str, object]] | None:
    """Read the bounded machine-readable subset of workflow_contracts.

    The manifest remains YAML. Only the workflow identity and inline JSON
    upstream-requirement records are consumed here; Resolver does not parse
    Router prose or duplicate engine policy.
    """
    if section is None:
        return None
    workflows: dict[str, dict[str, object]] = {}
    current: str | None = None
    in_requirements = False
    for raw in section.splitlines():
        if not raw.strip():
            continue
        workflow = re.fullmatch(r"  ([a-z0-9_]+):\s*", raw)
        if workflow:
            current = workflow.group(1)
            if current in workflows:
                return None
            workflows[current] = {"upstream_requirements": []}
            in_requirements = False
            continue
        if current is None:
            return None
        if re.fullmatch(r"    upstream_requirements:\s*", raw):
            in_requirements = True
            continue
        durable = re.fullmatch(r"    required_durable_output_ids:\s*(\[.*\])\s*", raw)
        if durable:
            if "required_durable_output_ids" in workflows[current]:
                return None
            try:
                ids = json.loads(durable.group(1))
            except json.JSONDecodeError:
                return None
            if (not isinstance(ids, list) or not ids
                    or not all(isinstance(item, str) and item.strip() for item in ids)
                    or len(ids) != len(set(ids))):
                return None
            workflows[current]["required_durable_output_ids"] = ids
            in_requirements = False
            continue
        if re.fullmatch(r"    [a-z0-9_]+:.*", raw):
            in_requirements = False
            continue
        if raw.startswith("      - "):
            if not in_requirements:
                continue
            encoded = raw[len("      - "):].strip()
            if not encoded.startswith("{"):
                return None
            try:
                requirement = json.loads(encoded)
            except json.JSONDecodeError:
                return None
            if not isinstance(requirement, Mapping):
                return None
            workflows[current]["upstream_requirements"].append(dict(requirement))
            continue
        if raw.startswith("      "):
            # Other nested workflow data (skills) is not part of this runtime seam.
            continue
        return None
    return workflows


def load_engine_workflow_contract(engine_id: str, *, root: Path = ROOT) -> tuple[dict[str, object] | None, str | None]:
    """Load one engine's runtime workflow contract from its own manifest.

    Legacy manifests without ``workflow_contracts`` intentionally return
    ``(None, None)`` so pre-contract engines preserve their existing resolver
    path. A manifest that opts into workflow contracts must use the bounded
    machine-readable requirement form or fails closed.
    """
    if not re.fullmatch(r"[a-z0-9_/-]+", engine_id) or ".." in engine_id.split("/"):
        return None, "ENGINE_CONTRACT_IDENTITY_INVALID"
    path = root / "engines" / engine_id / "MANIFEST.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, "ENGINE_CONTRACT_UNRESOLVED"
    declared_engine = _scalar(text, "engine_id")
    status = _scalar(text, "status")
    workflow_section = _top_level_section(text, "workflow_contracts")
    if workflow_section is None:
        return None, None
    workflow_contracts = _workflow_requirements(workflow_section)
    capabilities = _simple_mapping(_top_level_section(text, "capabilities"))
    if declared_engine != engine_id or not isinstance(status, str) or workflow_contracts is None or capabilities is None:
        return None, "ENGINE_CONTRACT_MALFORMED"
    return {
        "engine_id": declared_engine,
        "status": status,
        "capabilities": capabilities,
        "workflow_contracts": workflow_contracts,
        "source": str(path.relative_to(root)),
    }, None


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        return None
    return [item.strip() for item in value]


def _binding_refs(value: object, *, multiple: bool) -> list[str] | None:
    if multiple:
        refs = _string_list(value)
        return refs if refs else None
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return None


def _resolved_artifact(resolver: ArtifactResolver, ref: str) -> Mapping[str, object] | None:
    try:
        artifact = resolver(ref)
    except Exception:
        return None
    return artifact if isinstance(artifact, Mapping) and artifact.get("artifact_id") == ref else None


def _prove_artifact_requirement(
    requirement: Mapping[str, object], refs: list[str], resolver: ArtifactResolver,
) -> tuple[list[Mapping[str, object]], str | None]:
    allowed_types = requirement.get("allowed_artifact_types")
    if allowed_types is not None:
        allowed_types = _string_list(allowed_types)
        if allowed_types is None or not allowed_types:
            return [], "WORKFLOW_CONTRACT_MALFORMED"
    artifacts: list[Mapping[str, object]] = []
    for ref in refs:
        artifact = _resolved_artifact(resolver, ref)
        if artifact is None:
            return [], "WORKFLOW_PREREQUISITE_UNRESOLVED"
        if allowed_types is not None and artifact.get("artifact_type") not in set(allowed_types):
            return [], "WORKFLOW_PREREQUISITE_TYPE_MISMATCH"
        if requirement.get("require_provenance") is True:
            provenance = artifact.get("provenance")
            if not isinstance(provenance, list) or not provenance or not all(isinstance(item, str) and item.strip() for item in provenance):
                return [], "WORKFLOW_PREREQUISITE_PROVENANCE_MISSING"
        artifacts.append(artifact)
    return artifacts, None


def _prove_authority_requirement(
    requirement: Mapping[str, object], refs: list[str], resolver: ArtifactResolver,
    proven: Mapping[str, list[Mapping[str, object]]], workflow_id: str,
) -> tuple[list[Mapping[str, object]], str | None]:
    if len(refs) != 1:
        return [], "WORKFLOW_CONTRACT_MALFORMED"
    artifact = _resolved_artifact(resolver, refs[0])
    if artifact is None:
        return [], "WORKFLOW_PREREQUISITE_UNRESOLVED"
    authority = requirement.get("authority_contract")
    if not isinstance(authority, Mapping):
        return [], "WORKFLOW_CONTRACT_MALFORMED"

    for field, artifact_field, error in (
        ("artifact_types", "artifact_type", "WORKFLOW_AUTHORITY_TYPE_MISMATCH"),
        ("statuses", "status", "WORKFLOW_AUTHORITY_STATUS_MISMATCH"),
        ("produced_by_roles", "produced_by_role", "WORKFLOW_AUTHORITY_PRODUCER_MISMATCH"),
        ("authority_roles", "authority_role", "WORKFLOW_AUTHORITY_ROLE_MISMATCH"),
    ):
        if field not in authority:
            continue
        allowed = _string_list(authority.get(field))
        if allowed is None or not allowed:
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        if artifact.get(artifact_field) not in set(allowed):
            return [], error

    if authority.get("require_provenance") is True:
        provenance = artifact.get("provenance")
        if not isinstance(provenance, list) or not provenance or not all(isinstance(item, str) and item.strip() for item in provenance):
            return [], "WORKFLOW_AUTHORITY_PROVENANCE_MISSING"
    constants = authority.get("constant_checks", {})
    if not isinstance(constants, Mapping):
        return [], "WORKFLOW_CONTRACT_MALFORMED"
    alternative = authority.get("constant_checks_alternative")
    use_alternative = False
    if "constant_checks_alternative" in authority:
        if (not constants or not isinstance(alternative, Mapping)
                or set(alternative) != {"mode_field", "mode_value", "required_nonempty_fields", "forbidden_fields"}):
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        mode_field = alternative.get("mode_field")
        mode_value = alternative.get("mode_value")
        required = _string_list(alternative.get("required_nonempty_fields"))
        forbidden = _string_list(alternative.get("forbidden_fields"))
        if (not isinstance(mode_field, str) or not mode_field.strip()
                or not isinstance(mode_value, str) or not mode_value.strip()
                or required is None or not required or forbidden is None):
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        if mode_field in artifact:
            use_alternative = True
            if (artifact.get(mode_field) != mode_value
                    or any(not isinstance(artifact.get(field), str) or not artifact[field].strip() for field in required)
                    or any(field in artifact for field in forbidden)):
                return [], "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"
    if not use_alternative:
        for field, expected in constants.items():
            if artifact.get(field) != expected:
                return [], "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"
    workflow_field = authority.get("workflow_field")
    if workflow_field is not None:
        if not isinstance(workflow_field, str) or not workflow_field.strip():
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        if artifact.get(workflow_field) != workflow_id:
            return [], "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"
    bindings = authority.get("binding_checks", [])
    if not isinstance(bindings, list):
        return [], "WORKFLOW_CONTRACT_MALFORMED"
    for check in bindings:
        if not isinstance(check, Mapping):
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        authority_field = check.get("authority_field")
        requirement_id = check.get("requirement_id")
        artifact_field = check.get("artifact_field", "artifact_id")
        if not all(isinstance(item, str) and item.strip() for item in (authority_field, requirement_id, artifact_field)):
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        targets = proven.get(str(requirement_id))
        if not targets or len(targets) != 1:
            return [], "WORKFLOW_CONTRACT_MALFORMED"
        expected = targets[0].get(str(artifact_field))
        if expected is None or artifact.get(str(authority_field)) != expected:
            return [], "WORKFLOW_AUTHORITY_SCOPE_MISMATCH"
    return [artifact], None


def resolve_workflow_contract(
    decision: Mapping[str, object],
    bindings: object,
    artifact_resolver: ArtifactResolver,
    *,
    root: Path = ROOT,
) -> dict[str, object]:
    """Resolve authoritative workflow identity and prove its complete upstream set."""
    engine_id = decision.get("engine_id")
    capability = decision.get("semantic_capability")
    workflow_id = decision.get("workflow_id")
    if not all(isinstance(item, str) and item.strip() for item in (engine_id, capability, workflow_id)):
        return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_IDENTITY_INVALID"}
    contract, error = load_engine_workflow_contract(str(engine_id), root=root)
    if error:
        return {"status": "ERROR", "reason": error}
    if contract is None:
        return {"status": "LEGACY_NO_WORKFLOW_CONTRACT"}
    if contract.get("status") != decision.get("engine_status"):
        return {"status": "ERROR", "reason": "ENGINE_CONTRACT_STATUS_MISMATCH", "contract_source": contract.get("source")}
    capabilities = contract.get("capabilities")
    workflows = contract.get("workflow_contracts")
    if not isinstance(capabilities, Mapping) or not isinstance(workflows, Mapping):
        return {"status": "ERROR", "reason": "ENGINE_CONTRACT_MALFORMED", "contract_source": contract.get("source")}
    selected = capabilities.get(capability)
    if selected != workflow_id:
        return {"status": "ERROR", "reason": "CAPABILITY_WORKFLOW_IDENTITY_MISMATCH", "contract_source": contract.get("source")}
    workflow = workflows.get(workflow_id)
    if not isinstance(workflow, Mapping):
        return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_UNRESOLVED", "contract_source": contract.get("source")}
    requirements = workflow.get("upstream_requirements", [])
    if not isinstance(requirements, list):
        return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_MALFORMED", "contract_source": contract.get("source")}
    if not isinstance(bindings, Mapping):
        bindings = {} if bindings is None else None
    if bindings is None:
        return {"status": "ERROR", "reason": "WORKFLOW_PREREQUISITE_BINDINGS_MALFORMED", "contract_source": contract.get("source")}
    requirement_ids: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, Mapping) or not isinstance(requirement.get("requirement_id"), str) or not requirement["requirement_id"].strip():
            return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_MALFORMED", "contract_source": contract.get("source")}
        requirement_ids.append(requirement["requirement_id"].strip())
    if len(requirement_ids) != len(set(requirement_ids)):
        return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_MALFORMED", "contract_source": contract.get("source")}
    unknown = sorted(set(bindings) - set(requirement_ids))
    if unknown:
        return {"status": "ERROR", "reason": "WORKFLOW_PREREQUISITE_BINDING_MISMATCH", "unknown_bindings": unknown, "contract_source": contract.get("source")}
    proven: dict[str, list[Mapping[str, object]]] = {}
    proof_refs: list[str] = []
    for requirement in requirements:
        requirement_id = str(requirement["requirement_id"])
        multiple = requirement.get("multiple") is True
        refs = _binding_refs(bindings.get(requirement_id), multiple=multiple)
        if refs is None:
            return {"status": "ERROR", "reason": "WORKFLOW_PREREQUISITE_REQUIRED", "missing_requirement": requirement_id, "contract_source": contract.get("source")}
        proof_class = requirement.get("proof_class")
        if proof_class == "ARTIFACT_REF":
            artifacts, proof_error = _prove_artifact_requirement(requirement, refs, artifact_resolver)
        elif proof_class == "AUTHORITY_REF":
            artifacts, proof_error = _prove_authority_requirement(requirement, refs, artifact_resolver, proven, str(workflow_id))
        else:
            return {"status": "ERROR", "reason": "WORKFLOW_CONTRACT_MALFORMED", "contract_source": contract.get("source")}
        if proof_error:
            return {"status": "ERROR", "reason": proof_error, "failed_requirement": requirement_id, "contract_source": contract.get("source")}
        proven[requirement_id] = artifacts
        proof_refs.extend(str(item["artifact_id"]) for item in artifacts)
    return {
        "status": "PROVEN",
        "engine_id": engine_id,
        "semantic_capability": capability,
        "workflow_id": workflow_id,
        "contract_source": contract.get("source"),
        "requirement_ids": requirement_ids,
        "proof_refs": list(dict.fromkeys(proof_refs)),
        "required_durable_output_ids": workflow.get("required_durable_output_ids", []),
    }


def requires_project_topology(engine_id: str, capability: str, *, root: Path = ROOT) -> bool:
    """Read the Engine's own explicitly declared persistent-payload capabilities.

    This is scope metadata, not new workflow authority. A read-only capability
    does not acquire a write obligation merely because its Engine can write.
    """
    if not re.fullmatch(r"[a-z0-9_/-]+", engine_id) or ".." in engine_id.split("/"):
        raise ValueError("ENGINE_CONTRACT_IDENTITY_INVALID")
    path = root / "engines" / engine_id / "MANIFEST.yaml"
    section = _top_level_section(path.read_text(encoding="utf-8"), "persistent_payload_capabilities")
    if section is None:
        return False
    values = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"  - ([a-z0-9_]+)\s*", line)
        if match is None:
            raise ValueError("TOPOLOGY_WRITE_POLICY_MALFORMED")
        values.append(match.group(1))
    if len(values) != len(set(values)):
        raise ValueError("TOPOLOGY_WRITE_POLICY_MALFORMED")
    known = _simple_mapping(_top_level_section(path.read_text(encoding="utf-8"), "capabilities"))
    if known is None or any(item not in known for item in values):
        raise ValueError("TOPOLOGY_WRITE_POLICY_MALFORMED")
    return capability in values
