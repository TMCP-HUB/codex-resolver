"""Repository-backed physical realization of an admitted project topology.

Reference filesystem realization with staged initial publication, bounded
extension and exact-reference updates. It reuses the generic #56 durable port;
callers still require their existing workflow's authority for every mutation.
Local file readback alone does not prove publication to GitHub or Drive.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from tools.project_topology import (TopologyAdmission, TopologyError, _canonical_bytes,
                                   resolve_address, verify_bootstrap, materialize_project_payload,
                                   classify_topology_change, materialize_bootstrap)
from tools.durable_artifact_port import DurableArtifactPort, RESOLVED


MANIFEST_NAME = "TOPOLOGY_MANIFEST.json"


def _repository_path(root: Path, relative: str) -> Path:
    """A semantic relative address cannot delegate physical authority to symlinks."""
    current = root
    for segment in (None, *relative.split("/")):
        if segment is not None:
            current = current / segment
        if current.is_symlink():
            raise TopologyError("TOPOLOGY_PHYSICAL_PATH_INVALID")
    return current


def _publish_file(target: Path, payload: bytes) -> None:
    """Replace from a uniquely created stage owned by this operation only."""
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".topology-", delete=False) as out:
            staged = Path(out.name)
            out.write(payload)
        os.replace(staged, target)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def _root_index_bytes(admission: TopologyAdmission) -> bytes:
    return (
        "# Project Index\n\n"
        f"Project: {admission.project_id}\n\n"
        f"Topology manifest: {MANIFEST_NAME}\n\n"
        "Current Canon: NOT_SET\n\n"
        "Read the topology manifest to navigate semantic namespaces.\n"
    ).encode("utf-8")


def _read_root_index(index_data: bytes, admission: TopologyAdmission) -> str | None:
    """Read required navigation fields without freezing user-authored index text.

    The Canon field is an explicitly declared navigation reference, not proof
    that its target is accepted Canon or that an external target is reachable.
    """
    try:
        lines = index_data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise TopologyError("COLD_START_ROOT_INDEX_INVALID") from exc

    # Navigation fields belong to the opening section. Once the three fields
    # have been declared, later Markdown sections are user content, not more
    # declarations. Fenced examples are never interpreted as navigation.
    names = ("Project", "Topology manifest", "Current Canon")
    declared: set[str] = set()
    navigation_lines = []
    fence_char = None
    fence_length = 0
    for line in lines:
        # Four-space or tab indentation is Markdown code, not a declaration.
        if line.startswith("    ") or line.startswith("\t"):
            continue
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})(.*)$", stripped)
        if fence_char is not None:
            if (marker and marker.group(1)[0] == fence_char
                    and len(marker.group(1)) >= fence_length and not marker.group(2).strip()):
                fence_char = None
            continue
        if marker:
            fence_char, fence_length = marker.group(1)[0], len(marker.group(1))
            continue
        if re.match(r"^#{1,6}(?:\s|$)", stripped) and len(declared) == len(names):
            break
        navigation_lines.append(stripped)
        declared.update(name for name in names if stripped.startswith(name + ":"))

    def values(name: str) -> list[str]:
        prefix = name + ":"
        return [line[len(prefix):].strip() for line in navigation_lines if line.startswith(prefix)]

    project = values("Project")
    if project != [admission.project_id]:
        raise TopologyError("COLD_START_ROOT_INDEX_INVALID")
    manifest = values("Topology manifest")
    if manifest != [MANIFEST_NAME]:
        raise TopologyError("COLD_START_TOPOLOGY_LINK_MISSING")
    canon = values("Current Canon")
    if len(canon) != 1 or not canon[0]:
        raise TopologyError("COLD_START_ROOT_INDEX_INVALID")
    # Previously materialized shells retain the old text; it remains unset and
    # is not rewritten merely because the bootstrap format has changed.
    if canon[0] in {"NOT_SET", "NOT_SET (Owner gate not executed)"}:
        return None
    return canon[0]


def _namespace_index_bytes(entry: dict) -> bytes:
    return (
        f"# {entry['artifact_class']}\n\n"
        f"Namespace: {entry['prefix']}\n\n"
        f"Scope key: {entry['scope_key'] or 'NONE'}\n\n"
        "Current entries (JSON):\n"
        "[]\n"
    ).encode("utf-8")


def _expected_files(admission: TopologyAdmission) -> dict[str, bytes]:
    if admission.manifest.get("storage_mode") not in {"REPO_ONLY", "DRIVE_THEN_REPO"}:
        raise TopologyError("REPOSITORY_MODE_NOT_SELECTED")
    if admission.manifest["root_index"] == MANIFEST_NAME:
        raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
    files = {
        admission.manifest["root_index"]: _root_index_bytes(admission),
        MANIFEST_NAME: _canonical_bytes({
            "project_id": admission.project_id,
            "current_topology_ref": admission.bootstrap_ref,
            "content_digest": admission.digest,
            "manifest": admission.manifest,
        }),
    }
    for entry in admission.manifest["namespaces"]:
        if any(entry["prefix"] == path or entry["prefix"].startswith(path + "/")
               for path in (admission.manifest["root_index"], MANIFEST_NAME)):
            raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
        path = entry["index"]
        if path in files:
            raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
        files[path] = _namespace_index_bytes(entry)
    return files


def materialize_repository_shell(root: str | Path, admission: TopologyAdmission) -> dict:
    """Publish a *new* project root atomically; never silently rewrite an old root.

    All namespace indexes and manifest exist in the staged tree before the
    single root rename. A failed staging operation cannot admit a partial root.
    """
    root = Path(root)
    if root.exists() or root.is_symlink():
        raise TopologyError("PROJECT_ROOT_ALREADY_EXISTS")
    if not root.parent.is_dir():
        raise TopologyError("PROJECT_ROOT_PARENT_MISSING")
    files = _expected_files(admission)
    staged: Path | None = None
    try:
        staged = Path(tempfile.mkdtemp(prefix=".foundation-topology-", dir=root.parent))
        for rel, payload in files.items():
            dest = staged / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        # Validate the actual staged files before the commit boundary.
        _verify_repository_files(staged, admission)
        if root.exists() or root.is_symlink():
            raise TopologyError("PROJECT_ROOT_ALREADY_EXISTS")
        os.replace(staged, root)
        staged = None
    except (OSError, ValueError) as exc:
        if isinstance(exc, TopologyError):
            raise
        raise TopologyError("REPOSITORY_SHELL_WRITE_FAILED") from exc
    finally:
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)
    # Fresh consumer reads published files, not the writer's staged copy.
    return verify_repository_shell(root, admission)


def _verify_repository_files(root: Path, admission: TopologyAdmission) -> dict:
    expected = _expected_files(admission)
    # Cold consumer starts at the declared root entrypoint, not directory enumeration.
    index_path = _repository_path(root, admission.manifest["root_index"])
    try:
        index_data = index_path.read_bytes()
    except OSError as exc:
        raise TopologyError("COLD_START_ROOT_INDEX_MISSING") from exc
    declared_canon = _read_root_index(index_data, admission)
    try:
        manifest_data = _repository_path(root, MANIFEST_NAME).read_bytes()
        carrier = json.loads(manifest_data)
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise TopologyError("COLD_START_MANIFEST_INVALID") from exc
    if carrier != json.loads(expected[MANIFEST_NAME]):
        raise TopologyError("TOPOLOGY_CURRENT_REF_STALE")
    manifest = carrier["manifest"]
    observed_indexes = {admission.manifest["root_index"]: index_data,
                        MANIFEST_NAME: manifest_data}
    for entry in manifest["namespaces"]:
        rel = entry["index"]
        try:
            actual = _repository_path(root, rel).read_bytes()
        except OSError as exc:
            raise TopologyError("COLD_START_NAMESPACE_MISSING") from exc
        prefix = expected[rel][:-3]  # Preserve the declared navigation contract, replace only [].
        if not actual.startswith(prefix):
            raise TopologyError("COLD_START_NAMESPACE_INVALID")
        try:
            items = json.loads(actual[len(prefix):])
        except (UnicodeDecodeError, ValueError) as exc:
            raise TopologyError("COLD_START_NAMESPACE_INVALID") from exc
        if not isinstance(items, list):
            raise TopologyError("COLD_START_NAMESPACE_INVALID")
        seen = set()
        for item in items:
            required = {"artifact_id", "scope", "canonical_address", "digest", "artifact_ref"}
            if not isinstance(item, dict) or set(item) not in (required, required | {"history_refs"}):
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            history = item.get("history_refs", [])
            if (not isinstance(history, list) or not all(isinstance(ref, str) and ref.strip() for ref in history)
                    or len(set(history)) != len(history) or item["artifact_ref"] in history):
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            # The semantic address includes scope; IDs may recur across workstreams.
            if not isinstance(item["canonical_address"], str) or item["canonical_address"] in seen:
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            seen.add(item["canonical_address"])
            scope = {} if entry["scope_key"] is None else {entry["scope_key"]: item["scope"]}
            try:
                address = resolve_address(admission, entry["artifact_class"], item["artifact_id"], scope)
            except TopologyError as exc:
                raise TopologyError("COLD_START_NAMESPACE_INVALID") from exc
            if address != item["canonical_address"]:
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
            try:
                payload = _repository_path(root, address).read_bytes()
            except OSError as exc:
                raise TopologyError("COLD_START_PAYLOAD_MISSING") from exc
            if hashlib.sha256(payload).hexdigest() != item["digest"]:
                raise TopologyError("COLD_START_PAYLOAD_DIGEST_MISMATCH")
            if not isinstance(item["artifact_ref"], str) or not item["artifact_ref"].strip():
                raise TopologyError("COLD_START_NAMESPACE_INVALID")
        observed_indexes[rel] = actual
    digest = hashlib.sha256(b"".join(
        rel.encode("utf-8") + b"\x00" + observed_indexes[rel]
        for rel in sorted(expected)
    )).hexdigest()
    return {"project_id": admission.project_id,
            "topology_ref": admission.bootstrap_ref,
            "root_index": admission.manifest["root_index"],
            "manifest": MANIFEST_NAME,
            "declared_current_canon_ref": declared_canon,
            "verified_paths": sorted(expected),
            "physical_digest": digest,
            "status": "COLD_START_PROVEN"}


def verify_repository_shell(root: str | Path, admission: TopologyAdmission) -> dict:
    """Read the published repository shell; a declared Canon ref is navigation only.

    This does not grant Canon authority or establish reachability of an external
    reference. A caller changes the existing index only with its actual authority.
    """
    root = Path(root)
    if not root.is_dir():
        raise TopologyError("PROJECT_ROOT_UNRESOLVED")
    return _verify_repository_files(root, admission)


def materialize_repository_payload(
    root: str | Path,
    port: DurableArtifactPort,
    system_of_record_ref: str,
    bootstrap_ref: str,
    artifact_class: str,
    artifact_id: str,
    payload: bytes,
    *,
    scope: dict[str, str] | None = None,
    expected_artifact_ref: str | None = None,
) -> dict:
    """Materialize one project payload at its admitted physical semantic address.

    Creation never overwrites an indexed carrier. An independently authorized
    caller may update in place by binding the exact current artifact reference;
    that precondition does not itself grant Owner or Canon mutation authority.
    The namespace index is the final visibility boundary: unindexed staged bytes
    cannot be mistaken for a current, cold-start navigable project result.
    """
    admission = verify_bootstrap(port, system_of_record_ref, bootstrap_ref)
    root = Path(root)
    address = resolve_address(admission, artifact_class, artifact_id, scope)
    target = _repository_path(root, address)
    entry = next(e for e in admission.manifest["namespaces"] if e["artifact_class"] == artifact_class)
    index_path = _repository_path(root, entry["index"])
    prefix = _namespace_index_bytes(entry)[:-3]
    try:
        verify_repository_shell(root, admission)  # proves this *current* topology pointer
    except TopologyError as exc:
        if exc.code != "COLD_START_PAYLOAD_DIGEST_MISMATCH" or expected_artifact_ref is None:
            raise
        # An interrupted exact-reference update may have published new bytes but
        # not its index. Only the same authorized retry may restore the indexed
        # prior bytes, independently resolved from the existing durable port.
        try:
            prior_items = json.loads(index_path.read_bytes()[len(prefix):])
            prior = next(item for item in prior_items if item["canonical_address"] == address)
            observed = port.readback(system_of_record_ref, expected_artifact_ref)
            recoverable = (prior["artifact_ref"] == expected_artifact_ref
                and observed.status == RESOLVED and observed.system_of_record_ref == system_of_record_ref
                and observed.artifact_ref == expected_artifact_ref
                and observed.output_identity == "project-payload:" + admission.project_id + ":" + address
                and isinstance(observed.payload, bytes)
                and observed.content_digest == hashlib.sha256(observed.payload).hexdigest() == prior["digest"]
                and target.read_bytes() == payload)
        except (OSError, ValueError, TypeError, KeyError, StopIteration) as recovery_error:
            raise TopologyError("REPOSITORY_PAYLOAD_RECOVERY_NOT_PROVEN") from recovery_error
        if not recoverable:
            raise TopologyError("REPOSITORY_PAYLOAD_RECOVERY_NOT_PROVEN") from exc
        _publish_file(target, observed.payload)
        verify_repository_shell(root, admission)
    index_bytes = index_path.read_bytes()
    items = json.loads(index_bytes[len(prefix):])
    previous = next((item for item in items if item["canonical_address"] == address), None)
    if expected_artifact_ref is not None and (previous is None or previous["artifact_ref"] != expected_artifact_ref):
        raise TopologyError("PROJECT_PAYLOAD_REF_STALE")
    if previous is not None and expected_artifact_ref is None:
        raise TopologyError("CANONICAL_ADDRESS_ALREADY_EXISTS")
    if target.is_symlink() or (target.exists() and (not target.is_file()
            or (previous is None and target.read_bytes() != payload))):
        raise TopologyError("CANONICAL_ADDRESS_ALREADY_EXISTS")
    previous_bytes = target.read_bytes() if previous is not None else None
    # Use the existing system-of-record durable port, not a new artifact manager.
    materialized = materialize_project_payload(
        port, system_of_record_ref, bootstrap_ref,
        artifact_class, artifact_id, payload, scope=scope,
        current_topology_ref_reader=lambda project_id, sor: json.loads(
            _repository_path(root, MANIFEST_NAME).read_bytes()
        )["current_topology_ref"],
    )
    item = {
        "artifact_id": artifact_id,
        "scope": None if entry["scope_key"] is None else scope[entry["scope_key"]],
        "canonical_address": address,
        "digest": hashlib.sha256(payload).hexdigest(),
        "artifact_ref": materialized["artifact_ref"],
    }
    if previous is not None:
        history = previous.get("history_refs", [])
        item["history_refs"] = [ref for ref in history + [previous["artifact_ref"]]
                                if ref != item["artifact_ref"]]
    updated_items = [item if old["canonical_address"] == address else old for old in items]
    if previous is None:
        updated_items.append(item)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload_published = False
    try:
        # Publish the physical content first, then the index.
        _publish_file(target, payload)
        payload_published = True
        _publish_file(index_path, prefix + json.dumps(updated_items, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    except OSError as exc:
        # Keep the previously indexed payload coherent if an update fails before
        # the index commit. New unindexed exact bytes are safe to retry.
        if payload_published and previous_bytes is not None:
            _publish_file(target, previous_bytes)
        raise TopologyError("REPOSITORY_PAYLOAD_WRITE_FAILED") from exc
    readback = verify_repository_shell(root, admission)
    return {**materialized, "physical_readback": readback["status"],
            "physical_digest": readback["physical_digest"]}


def extend_repository_shell(
    root: str | Path,
    port: DurableArtifactPort,
    system_of_record_ref: str,
    current_ref: str,
    extended_plan: dict,
) -> dict:
    """Add semantic namespaces while preserving every previous canonical address.

    The same stable TOPOLOGY_MANIFEST.json is the only current topology carrier.
    Publishing that one file is the commit boundary; pre-staged new namespace
    indexes cannot become current through directory enumeration.
    This method does not perform replacement, even when it is authorized.
    """
    old = verify_bootstrap(port, system_of_record_ref, current_ref)
    root = Path(root)
    verify_repository_shell(root, old)  # stale caller ref is rejected
    outcome = classify_topology_change(old, extended_plan)
    if outcome == "TOPOLOGY_REPLACEMENT":
        raise TopologyError("TOPOLOGY_REPLACEMENT_NOT_SUPPORTED_BY_EXTENSION")
    if outcome == "TOPOLOGY_UNCHANGED":
        return verify_repository_shell(root, old)
    if outcome != "TOPOLOGY_EXTENSION":
        raise TopologyError("TOPOLOGY_CHANGE_INVALID")
    new_ref = materialize_bootstrap(port, system_of_record_ref, extended_plan)
    new = verify_bootstrap(port, system_of_record_ref, new_ref)
    old_classes = {entry["artifact_class"] for entry in old.manifest["namespaces"]}
    expected = _expected_files(new)
    # Added files are not authoritative until the single current-carrier replace.
    try:
        for entry in new.manifest["namespaces"]:
            if entry["artifact_class"] in old_classes:
                continue
            dest = _repository_path(root, entry["index"])
            if dest.exists() or dest.is_symlink():
                # Retry an interrupted extension only when the unadmitted index
                # is exactly this proposal's empty shell. Never replace payload.
                if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != expected[entry["index"]]:
                    raise TopologyError("TOPOLOGY_NAMESPACE_COLLISION")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            staged = dest.with_name("." + dest.name + ".staged")
            with staged.open("xb") as out:
                out.write(expected[entry["index"]])
            os.replace(staged, dest)
        manifest_path = root / MANIFEST_NAME
        staged = manifest_path.with_name("." + MANIFEST_NAME + ".staged")
        with staged.open("xb") as out:
            out.write(expected[MANIFEST_NAME])
        # Atomic current-carrier cutover. Old topology cannot remain current.
        os.replace(staged, manifest_path)
    except OSError as exc:
        raise TopologyError("TOPOLOGY_EXTENSION_WRITE_FAILED") from exc
    finally:
        # Best effort cleanup of staging files; keep unindexed namespace evidence.
        for entry in new.manifest["namespaces"]:
            if entry["artifact_class"] not in old_classes:
                (root / entry["index"]).with_name("." + Path(entry["index"]).name + ".staged").unlink(missing_ok=True)
        (root / ("." + MANIFEST_NAME + ".staged")).unlink(missing_ok=True)
    proof = verify_repository_shell(root, new)
    return {**proof, "previous_topology_ref": current_ref, "extension_status": "TOPOLOGY_EXTENSION"}
