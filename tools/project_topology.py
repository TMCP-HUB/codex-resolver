"""Project Topology admission over the existing provider-neutral durable port.

This is a semantic pre-write contract, not a storage adapter or a second
control plane. A project payload is admissible only through a topology
verified by independent durable readback.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re

from tools.durable_artifact_port import MATERIALIZED, RESOLVED, DurableArtifactPort


_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_MODES = {"DRIVE_ONLY", "REPO_ONLY", "DRIVE_THEN_REPO"}
_CLASSES = {"SOURCE", "EVIDENCE", "FINDING", "PROJECT_DECISION", "CANON", "RUNTIME", "ARCHIVE"}
_BOOTSTRAP_ID = "PROJECT_TOPOLOGY_BOOTSTRAP"
_BOOTSTRAP_OUTPUT_ID = "foundation:topology-bootstrap"


class TopologyError(ValueError):
    """A bounded fail-closed topology-admission decision."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class TopologyAdmission:
    project_id: str
    bootstrap_ref: str
    system_of_record_ref: str
    manifest: dict
    index: dict
    shell: tuple[str, ...]
    digest: str


def _segment(value: object) -> str:
    if not isinstance(value, str) or not _SEGMENT.fullmatch(value) or value in {".", ".."}:
        raise TopologyError("TOPOLOGY_SEMANTIC_ID_INVALID")
    return value


def _path(value: object) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise TopologyError("TOPOLOGY_PATH_INVALID")
    parts = value.split("/")
    if any(part in {".", ".."} or not _SEGMENT.fullmatch(part) for part in parts):
        raise TopologyError("TOPOLOGY_PATH_INVALID")
    return value


def _canonical_bytes(value: Mapping) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _validate_plan(plan: Mapping) -> tuple[str, list[dict], str]:
    if not isinstance(plan, Mapping):
        raise TopologyError("TOPOLOGY_PLAN_REQUIRED")
    if set(plan) != {"artifact_type", "artifact_id", "produced_by_role", "assignment_id",
                     "input_state_ref", "status", "provenance", "related_artifacts",
                     "authoritative", "project_id", "storage_mode", "root_index", "namespaces"}:
        raise TopologyError("TOPOLOGY_PLAN_MALFORMED")
    if plan["artifact_type"] != "TOPOLOGY_PLAN" or plan["status"] != "WORKING" or plan["authoritative"] is not False:
        raise TopologyError("TOPOLOGY_PLAN_AUTHORITY_INVALID")
    if not all(isinstance(plan[key], str) and plan[key].strip()
               for key in ("artifact_id", "produced_by_role", "input_state_ref")):
        raise TopologyError("TOPOLOGY_PLAN_IDENTITY_INVALID")
    if plan["assignment_id"] is not None and (not isinstance(plan["assignment_id"], str) or not plan["assignment_id"].strip()):
        raise TopologyError("TOPOLOGY_PLAN_IDENTITY_INVALID")
    if not isinstance(plan["related_artifacts"], list) or not all(
        isinstance(ref, str) and ref.strip() for ref in plan["related_artifacts"]
    ):
        raise TopologyError("TOPOLOGY_PLAN_IDENTITY_INVALID")
    project_id = _segment(plan["project_id"])
    if not isinstance(plan["storage_mode"], str) or plan["storage_mode"] not in _MODES:
        raise TopologyError("TOPOLOGY_STORAGE_MODE_INVALID")
    root_index = _path(plan["root_index"])
    if "/" in root_index:
        raise TopologyError("ROOT_INDEX_NOT_AT_ROOT")
    if not isinstance(plan["provenance"], list) or not plan["provenance"] or not all(
        isinstance(v, str) and v.strip() for v in plan["provenance"]
    ):
        raise TopologyError("TOPOLOGY_PROVENANCE_MISSING")
    raw = plan["namespaces"]
    if not isinstance(raw, list) or not raw:
        raise TopologyError("TOPOLOGY_NAMESPACE_REQUIRED")
    entries, classes, paths = [], set(), {root_index}
    for entry in raw:
        if not isinstance(entry, Mapping) or set(entry) != {"artifact_class", "prefix", "index", "scope_key"}:
            raise TopologyError("TOPOLOGY_NAMESPACE_MALFORMED")
        cls = _segment(entry["artifact_class"])
        prefix, index = _path(entry["prefix"]), _path(entry["index"])
        # Each node's index is a child of its own admitted namespace.
        if not index.startswith(prefix + "/") or index == prefix:
            raise TopologyError("TOPOLOGY_INDEX_OUTSIDE_NAMESPACE")
        if cls in classes or prefix in paths or index in paths:
            raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
        scope_key = entry["scope_key"]
        if scope_key is not None:
            _segment(scope_key)
        # Prefix nesting needs explicit semantic subdivision, not accidental overlap.
        if any(prefix.startswith(e["prefix"] + "/") or e["prefix"].startswith(prefix + "/") for e in entries):
            raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
        classes.add(cls)
        paths.add(prefix)
        paths.add(index)
        entries.append({"artifact_class": cls, "prefix": prefix, "index": index, "scope_key": scope_key})
    return project_id, entries, root_index


def build_bootstrap(plan: Mapping) -> dict:
    """Construct a single logical transaction; no payload is admitted yet."""
    project_id, namespaces, root_index = _validate_plan(plan)
    manifest = {
        "artifact_type": "TOPOLOGY_MANIFEST",
        "project_id": project_id,
        "storage_mode": plan["storage_mode"],
        "root_index": root_index,
        "namespaces": namespaces,
        "authoritative": False,  # Owner/Canon authority is not created.
    }
    index = {
        "artifact_type": "PROJECT_INDEX",
        "project_id": project_id,
        "topology_entry": "TOPOLOGY_MANIFEST",
        "current_canon_ref": None,
        "nodes": [
            {"artifact_class": entry["artifact_class"], "index": entry["index"],
             "namespace": entry["prefix"], "current_ref": None, "history_refs": []}
            for entry in namespaces
        ],
    }
    # Structural shell is a semantic index/namespace plan. Physical provider
    # adapters realize these addresses, never use agent-proposed paths.
    shell = sorted({root_index, *(entry["index"] for entry in namespaces)})
    return {"kind": _BOOTSTRAP_ID, "version": 1, "plan": dict(plan),
            "manifest": manifest, "index": index, "shell": shell}


def materialize_bootstrap(port: DurableArtifactPort, system_of_record_ref: str, plan: Mapping) -> str:
    """Persist all bootstrap state in one durable object; a ref is not admission."""
    if not isinstance(system_of_record_ref, str) or not system_of_record_ref.strip():
        raise TopologyError("TOPOLOGY_SYSTEM_OF_RECORD_REQUIRED")
    _validate_plan(plan)
    bundle = build_bootstrap(plan)
    # Match the workflow's required output identity so generic readback can
    # reconcile the very same bundle. Project identity remains in its payload.
    result = port.materialize(system_of_record_ref, _BOOTSTRAP_OUTPUT_ID, _canonical_bytes(bundle))
    if result.status != MATERIALIZED or not result.artifact_ref:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_WRITE_FAILED")
    return result.artifact_ref


def verify_bootstrap(port: DurableArtifactPort, system_of_record_ref: str, bootstrap_ref: str) -> TopologyAdmission:
    """Independent cold-start readback: never trust a local draft or bare ref."""
    if not isinstance(system_of_record_ref, str) or not system_of_record_ref.strip():
        raise TopologyError("TOPOLOGY_SYSTEM_OF_RECORD_REQUIRED")
    if not isinstance(bootstrap_ref, str) or not bootstrap_ref.strip():
        raise TopologyError("TOPOLOGY_BOOTSTRAP_REF_REQUIRED")
    try:
        observed = port.readback(system_of_record_ref, bootstrap_ref)
    except Exception as exc:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_READBACK_NOT_PROVEN") from exc
    if (observed.status != RESOLVED or observed.system_of_record_ref != system_of_record_ref
            or observed.artifact_ref != bootstrap_ref or not isinstance(observed.payload, bytes)
            or not isinstance(observed.content_digest, str)):
        raise TopologyError("TOPOLOGY_BOOTSTRAP_READBACK_NOT_PROVEN")
    if hashlib.sha256(observed.payload).hexdigest() != observed.content_digest:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_DIGEST_MISMATCH")
    try:
        bundle = json.loads(observed.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TopologyError("TOPOLOGY_BOOTSTRAP_INVALID")
    if not isinstance(bundle, dict) or set(bundle) != {"kind", "version", "plan", "manifest", "index", "shell"}:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_INVALID")
    if bundle["kind"] != _BOOTSTRAP_ID or bundle["version"] != 1:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_INVALID")
    try:
        expected = build_bootstrap(bundle["plan"])
    except (TypeError, TopologyError):
        raise TopologyError("TOPOLOGY_BOOTSTRAP_INVALID")
    if bundle != expected:
        raise TopologyError("COLD_START_NAVIGATION_INVALID")
    project_id = bundle["manifest"]["project_id"]
    if observed.output_identity != _BOOTSTRAP_OUTPUT_ID:
        raise TopologyError("TOPOLOGY_BOOTSTRAP_IDENTITY_MISMATCH")
    return TopologyAdmission(project_id, bootstrap_ref, system_of_record_ref,
                             bundle["manifest"], bundle["index"], tuple(bundle["shell"]),
                             observed.content_digest)


def resolve_address(admission: TopologyAdmission, artifact_class: str, artifact_id: str,
                    scope: Mapping[str, str] | None = None) -> str:
    """Derive canonical semantic address from admitted topology, not a proposed path."""
    _segment(artifact_class)
    _segment(artifact_id)
    matches = [entry for entry in admission.manifest["namespaces"] if entry["artifact_class"] == artifact_class]
    if len(matches) != 1:
        raise TopologyError("TOPOLOGY_CHANGE_REQUIRED")
    entry = matches[0]
    scope = {} if scope is None else scope
    if not isinstance(scope, Mapping):
        raise TopologyError("TOPOLOGY_SCOPE_INVALID")
    key = entry["scope_key"]
    if set(scope) != ({key} if key else set()):
        raise TopologyError("TOPOLOGY_SCOPE_INVALID")
    scoped = [_segment(scope[key])] if key else []
    address = "/".join([entry["prefix"], *scoped, artifact_id])
    # Navigation/control carriers are not payload addresses, including ancestors.
    if any(address == path or address.startswith(path + "/") or path.startswith(address + "/")
           for path in admission.shell):
        raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
    return address


def materialize_project_payload(port: DurableArtifactPort, system_of_record_ref: str,
                                bootstrap_ref: str, artifact_class: str, artifact_id: str,
                                payload: bytes, *, scope: Mapping[str, str] | None = None,
                                proposed_address: str | None = None,
                                current_topology_ref_reader=None):
    """Mandatory semantic admission front door for permanent project payload writers."""
    admission = verify_bootstrap(port, system_of_record_ref, bootstrap_ref)
    # A readable historic bootstrap is not proof that it remains CURRENT.
    # Control/provider supplies the independent stable-current-carrier reader.
    if not callable(current_topology_ref_reader):
        raise TopologyError("TOPOLOGY_CURRENT_REF_READBACK_REQUIRED")
    try:
        current_ref = current_topology_ref_reader(admission.project_id, system_of_record_ref)
    except Exception as exc:
        raise TopologyError("TOPOLOGY_CURRENT_REF_READBACK_REQUIRED") from exc
    if current_ref != bootstrap_ref:
        raise TopologyError("TOPOLOGY_CURRENT_REF_STALE")
    address = resolve_address(admission, artifact_class, artifact_id, scope)
    if proposed_address is not None and proposed_address != address:
        raise TopologyError("TOPOLOGY_ADDRESS_MISMATCH")
    if not isinstance(payload, bytes):
        raise TopologyError("TOPOLOGY_PAYLOAD_INVALID")
    identity = "project-payload:" + admission.project_id + ":" + address
    result = port.materialize(system_of_record_ref, identity, payload)
    if result.status != MATERIALIZED or not result.artifact_ref:
        raise TopologyError("TOPOLOGY_PAYLOAD_WRITE_FAILED")
    try:
        observed = port.readback(system_of_record_ref, result.artifact_ref)
    except Exception as exc:
        raise TopologyError("TOPOLOGY_PAYLOAD_READBACK_NOT_PROVEN") from exc
    digest = hashlib.sha256(payload).hexdigest()
    if (observed.status != RESOLVED or observed.system_of_record_ref != system_of_record_ref
            or observed.artifact_ref != result.artifact_ref or observed.output_identity != identity
            or observed.payload != payload or observed.content_digest != digest):
        raise TopologyError("TOPOLOGY_PAYLOAD_READBACK_NOT_PROVEN")
    return {"canonical_address": address, "artifact_ref": result.artifact_ref,
            "system_of_record_ref": system_of_record_ref, "topology_ref": bootstrap_ref,
            "content_digest": digest, "readback_status": RESOLVED}


def classify_topology_change(old: TopologyAdmission, new_plan: Mapping) -> str:
    """Classify only. Existing Owner/architecture machinery decides replacement.

    A replacement classification does not determine whether an applicable
    Owner decision already exists.
    A ref or boolean supplied by a worker is not a verified Owner decision.
    No second authority gate or replacement materializer is created here.
    """
    project_id, proposed, new_root = _validate_plan(new_plan)
    if project_id != old.project_id:
        raise TopologyError("TOPOLOGY_PROJECT_IDENTITY_MISMATCH")
    previous = {entry["artifact_class"]: entry for entry in old.manifest["namespaces"]}
    updated = {entry["artifact_class"]: entry for entry in proposed}
    replacement = (old.manifest["root_index"] != new_root
                   or old.manifest["storage_mode"] != new_plan["storage_mode"]) or any(
        cls not in updated or updated[cls] != entry for cls, entry in previous.items()
    )
    if replacement:
        return "TOPOLOGY_REPLACEMENT"
    return "TOPOLOGY_EXTENSION" if previous != updated else "TOPOLOGY_UNCHANGED"
