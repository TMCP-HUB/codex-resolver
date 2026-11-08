"""Provider-neutral durable materialization/readback port for #56-B.

The universal surface uses only an opaque system-of-record reference, an opaque
output identity, exact payload bytes, and an opaque durable artifact reference.
The local-file implementation below is a reference/conformance backend only; its
filesystem mechanics are not part of the universal contract.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Protocol


MATERIALIZED = "MATERIALIZED"
RESOLVED = "RESOLVED"
UNRESOLVED = "UNRESOLVED"
WRONG_SYSTEM_OF_RECORD = "WRONG_SYSTEM_OF_RECORD"
MALFORMED_INPUT = "MALFORMED_INPUT"
BACKEND_FAILURE = "BACKEND_FAILURE"

_REF_RE = re.compile(r"^dar:v1:[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_RECORD_FIELDS = {
    "version",
    "system_of_record_ref",
    "output_identity",
    "artifact_ref",
    "content_digest",
    "payload_b64",
}


def _non_blank(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _content_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _artifact_ref(
    system_of_record_ref: str,
    output_identity: str,
    content_digest: str,
) -> str:
    identity = json.dumps(
        {
            "content_digest": content_digest,
            "output_identity": output_identity,
            "system_of_record_ref": system_of_record_ref,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"dar:v1:{hashlib.sha256(identity).hexdigest()}"


@dataclass(frozen=True)
class MaterializationResult:
    """Bounded result of one materialization attempt.

    ``artifact_ref`` is populated only for ``MATERIALIZED``. Its presence proves
    successful reference creation by this port, not claim truth or readback.
    """

    status: str
    system_of_record_ref: str | None = None
    output_identity: str | None = None
    artifact_ref: str | None = None
    content_digest: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ReadbackObservation:
    """Observation from resolving one durable artifact ref.

    ``RESOLVED`` proves exact durable-object resolution on the declared system of
    record only. It does not verify factual claims carried by the payload.
    """

    status: str
    system_of_record_ref: str | None = None
    artifact_ref: str | None = None
    output_identity: str | None = None
    content_digest: str | None = None
    payload: bytes | None = None
    error: str | None = None


class DurableArtifactPort(Protocol):
    """Provider-neutral #56-B materialization/readback boundary."""

    def materialize(
        self,
        system_of_record_ref: str,
        output_identity: str,
        payload: bytes,
    ) -> MaterializationResult: ...

    def readback(
        self,
        system_of_record_ref: str,
        artifact_ref: str,
    ) -> ReadbackObservation: ...


class LocalFileDurableReferencePort:
    """Deliberately simple local persistence backend for port conformance tests.

    ``storage_root`` is backend configuration only. It never enters the universal
    operation shape, the durable artifact ref, or readback identity semantics.
    """

    def __init__(self, storage_root: str | Path, system_of_record_ref: str) -> None:
        raw_root = str(storage_root)
        if not raw_root.strip():
            raise ValueError("storage_root must be non-empty")
        if not _non_blank(system_of_record_ref):
            raise ValueError("system_of_record_ref must be a non-blank string")
        self._storage_root = Path(storage_root)
        self._system_of_record_ref = system_of_record_ref

    @property
    def system_of_record_ref(self) -> str:
        return self._system_of_record_ref

    def materialize(
        self,
        system_of_record_ref: str,
        output_identity: str,
        payload: bytes,
    ) -> MaterializationResult:
        if not _non_blank(system_of_record_ref):
            return MaterializationResult(
                MALFORMED_INPUT,
                error="system_of_record_ref must be a non-blank string",
            )
        if not _non_blank(output_identity):
            return MaterializationResult(
                MALFORMED_INPUT,
                system_of_record_ref=system_of_record_ref,
                error="output_identity must be a non-blank string",
            )
        if not isinstance(payload, bytes):
            return MaterializationResult(
                MALFORMED_INPUT,
                system_of_record_ref=system_of_record_ref,
                output_identity=output_identity,
                error="payload must be exact bytes",
            )
        if system_of_record_ref != self._system_of_record_ref:
            return MaterializationResult(
                WRONG_SYSTEM_OF_RECORD,
                system_of_record_ref=system_of_record_ref,
                output_identity=output_identity,
                error="system_of_record_ref does not match this backend binding",
            )

        digest = _content_digest(payload)
        artifact_ref = _artifact_ref(system_of_record_ref, output_identity, digest)
        record = {
            "version": 1,
            "system_of_record_ref": system_of_record_ref,
            "output_identity": output_identity,
            "artifact_ref": artifact_ref,
            "content_digest": digest,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
        }
        record_bytes = json.dumps(
            record,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        try:
            self._persist_record(artifact_ref, record_bytes)
        except OSError as exc:
            return MaterializationResult(
                BACKEND_FAILURE,
                system_of_record_ref=system_of_record_ref,
                output_identity=output_identity,
                error=str(exc),
            )

        return MaterializationResult(
            MATERIALIZED,
            system_of_record_ref=system_of_record_ref,
            output_identity=output_identity,
            artifact_ref=artifact_ref,
            content_digest=digest,
        )

    def readback(
        self,
        system_of_record_ref: str,
        artifact_ref: str,
    ) -> ReadbackObservation:
        if not _non_blank(system_of_record_ref):
            return ReadbackObservation(
                MALFORMED_INPUT,
                error="system_of_record_ref must be a non-blank string",
            )
        if not isinstance(artifact_ref, str) or _REF_RE.fullmatch(artifact_ref) is None:
            return ReadbackObservation(
                MALFORMED_INPUT,
                system_of_record_ref=system_of_record_ref,
                error="artifact_ref is malformed",
            )
        if system_of_record_ref != self._system_of_record_ref:
            return ReadbackObservation(
                WRONG_SYSTEM_OF_RECORD,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error="system_of_record_ref does not match this backend binding",
            )

        path = self._record_path(artifact_ref)
        try:
            record_bytes = path.read_bytes()
        except FileNotFoundError:
            return ReadbackObservation(
                UNRESOLVED,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
            )
        except OSError as exc:
            return ReadbackObservation(
                BACKEND_FAILURE,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error=str(exc),
            )

        try:
            record = json.loads(record_bytes.decode("utf-8"))
            if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
                raise ValueError("durable record has invalid shape")
            if record.get("version") != 1:
                raise ValueError("durable record version is unsupported")
            if record.get("artifact_ref") != artifact_ref:
                raise ValueError("durable record artifact_ref mismatch")
            if not _non_blank(record.get("output_identity")):
                raise ValueError("durable record output_identity is invalid")
            digest = record.get("content_digest")
            if not isinstance(digest, str) or _DIGEST_RE.fullmatch(digest) is None:
                raise ValueError("durable record content_digest is invalid")
            encoded = record.get("payload_b64")
            if not isinstance(encoded, str):
                raise ValueError("durable record payload is invalid")
            payload = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (UnicodeDecodeError, UnicodeEncodeError, json.JSONDecodeError, ValueError, binascii.Error) as exc:
            return ReadbackObservation(
                BACKEND_FAILURE,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error=str(exc),
            )

        if record.get("system_of_record_ref") != system_of_record_ref:
            return ReadbackObservation(
                WRONG_SYSTEM_OF_RECORD,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error="durable record is bound to a different system of record",
            )

        output_identity = str(record["output_identity"])
        if _content_digest(payload) != digest:
            return ReadbackObservation(
                BACKEND_FAILURE,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error="durable record content digest mismatch",
            )
        if _artifact_ref(system_of_record_ref, output_identity, digest) != artifact_ref:
            return ReadbackObservation(
                BACKEND_FAILURE,
                system_of_record_ref=system_of_record_ref,
                artifact_ref=artifact_ref,
                error="durable record identity mismatch",
            )

        return ReadbackObservation(
            RESOLVED,
            system_of_record_ref=system_of_record_ref,
            artifact_ref=artifact_ref,
            output_identity=output_identity,
            content_digest=digest,
            payload=payload,
        )

    def _record_path(self, artifact_ref: str) -> Path:
        filename = hashlib.sha256(artifact_ref.encode("utf-8")).hexdigest() + ".json"
        return self._storage_root / filename

    def _persist_record(self, artifact_ref: str, record_bytes: bytes) -> None:
        self._storage_root.mkdir(parents=True, exist_ok=True)
        path = self._record_path(artifact_ref)
        if path.exists():
            if path.read_bytes() != record_bytes:
                raise OSError("existing durable record conflicts with deterministic identity")
            return

        temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            temp_path.write_bytes(record_bytes)
            os.replace(temp_path, path)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
