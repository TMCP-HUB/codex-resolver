"""Provider-neutral durable readback enforcement for #56-C.

This layer composes the merged A1 declaration/reference contract with the merged
56-B readback port. It proves durable availability/identity only; claim truth
continues to belong to the existing Verifier/Control path.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re

from tools.durable_artifact_port import (
    BACKEND_FAILURE,
    RESOLVED,
    UNRESOLVED,
    DurableArtifactPort,
    ReadbackObservation,
)
from tools.durable_output_contract import (
    DURABLE_OUTPUT_REFS_FIELD,
    DURABLE_SYSTEM_OF_RECORD_REF_FIELD,
    REQUIRED_DURABLE_OUTPUTS_FIELD,
    validate_executor_durable_output_refs,
)


READBACK_PROVEN = "PROVEN"
READBACK_NOT_PROVEN = "NOT_PROVEN"
READBACK_INVALID = "INVALID"
READBACK_NOT_REQUIRED = "NOT_REQUIRED"

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PROOF_FIELDS = {
    "assignment_id",
    "output_id",
    "system_of_record_ref",
    "artifact_ref",
    "content_digest",
    "readback_status",
}


@dataclass(frozen=True)
class DurableReadbackEvaluation:
    """Exact independent readback observations for one Executor result."""

    status: str
    proofs: tuple[dict[str, str], ...] = ()
    observations: tuple[ReadbackObservation, ...] = ()
    errors: tuple[str, ...] = ()


def _non_blank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _invalid(*errors: str) -> DurableReadbackEvaluation:
    return DurableReadbackEvaluation(READBACK_INVALID, errors=tuple(errors))


def _not_proven(*errors: str) -> DurableReadbackEvaluation:
    return DurableReadbackEvaluation(READBACK_NOT_PROVEN, errors=tuple(errors))


def evaluate_required_durable_readback(
    assignment: Mapping[str, object],
    result: Mapping[str, object],
    durable_port: DurableArtifactPort | None,
) -> DurableReadbackEvaluation:
    """Resolve every required COMPLETE output through the merged 56-B port.

    PARTIAL/BLOCKED/FAILED results are not required to fabricate references or
    readback proof. A COMPLETE result with no required durable outputs preserves
    legacy behavior. For governed durable outputs, only independently resolved
    exact observations can yield PROVEN.
    """
    structural_errors = validate_executor_durable_output_refs(result, assignment)
    if structural_errors:
        return DurableReadbackEvaluation(
            READBACK_INVALID,
            errors=tuple(structural_errors),
        )

    required_value = assignment.get(REQUIRED_DURABLE_OUTPUTS_FIELD, [])
    required = list(required_value) if isinstance(required_value, list) else []
    if result.get("status") != "COMPLETE" or not required:
        return DurableReadbackEvaluation(READBACK_NOT_REQUIRED)

    assignment_id = assignment.get("assignment_id")
    system_of_record_ref = assignment.get(DURABLE_SYSTEM_OF_RECORD_REF_FIELD)
    if not _non_blank(assignment_id):
        return _invalid("assignment.assignment_id must be a non-blank string for durable readback")
    if not _non_blank(system_of_record_ref):
        return _invalid("assignment durable system-of-record binding is invalid")
    if durable_port is None:
        return _not_proven("durable readback port is unavailable")

    bindings_value = result.get(DURABLE_OUTPUT_REFS_FIELD, [])
    bindings = {
        str(binding["output_id"]): str(binding["artifact_ref"])
        for binding in bindings_value
        if isinstance(binding, Mapping)
        and _non_blank(binding.get("output_id"))
        and _non_blank(binding.get("artifact_ref"))
    }

    proofs: list[dict[str, str]] = []
    observations: list[ReadbackObservation] = []
    assert isinstance(assignment_id, str)
    assert isinstance(system_of_record_ref, str)
    for output_id in required:
        artifact_ref = bindings[str(output_id)]
        try:
            observation = durable_port.readback(system_of_record_ref, artifact_ref)
        except Exception as exc:  # adapter/backend failure must fail closed at Control.
            return _not_proven(
                f"durable readback failed for output {output_id}: {type(exc).__name__}: {exc}"
            )

        observations.append(observation)
        if observation.status in {UNRESOLVED, BACKEND_FAILURE}:
            return DurableReadbackEvaluation(
                READBACK_NOT_PROVEN,
                observations=tuple(observations),
                errors=(f"durable readback is not proven for output {output_id}: {observation.status}",),
            )
        if observation.status != RESOLVED:
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback is invalid for output {output_id}: {observation.status}",),
            )
        if observation.system_of_record_ref != system_of_record_ref:
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback system-of-record mismatch for output {output_id}",),
            )
        if observation.artifact_ref != artifact_ref:
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback artifact_ref mismatch for output {output_id}",),
            )
        if observation.output_identity != output_id:
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback output identity mismatch for output {output_id}",),
            )
        if not isinstance(observation.content_digest, str) or _DIGEST_RE.fullmatch(observation.content_digest) is None:
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback content identity is invalid for output {output_id}",),
            )
        if not isinstance(observation.payload, bytes):
            return DurableReadbackEvaluation(
                READBACK_INVALID,
                observations=tuple(observations),
                errors=(f"durable readback payload is unavailable for output {output_id}",),
            )

        proofs.append(
            {
                "assignment_id": assignment_id,
                "output_id": str(output_id),
                "system_of_record_ref": system_of_record_ref,
                "artifact_ref": artifact_ref,
                "content_digest": observation.content_digest,
                "readback_status": RESOLVED,
            }
        )

    return DurableReadbackEvaluation(
        READBACK_PROVEN,
        proofs=tuple(proofs),
        observations=tuple(observations),
    )


def validate_verification_durable_readback_proofs(
    verification: Mapping[str, object],
    assignment: Mapping[str, object],
    expected_proofs: Sequence[Mapping[str, str]] | None,
) -> list[str]:
    """Bind Verifier durable evidence to independently observed readback exactly.

    This does not verify factual claims. It only prevents CONFIRMED from being
    accepted when the Verifier's durable target differs from Control's exact
    independent readback observation.
    """
    errors: list[str] = []
    required_value = assignment.get(REQUIRED_DURABLE_OUTPUTS_FIELD, [])
    required = set(required_value) if isinstance(required_value, list) else set()
    assignment_id = assignment.get("assignment_id")

    provided = verification.get("durable_readback_proofs", [])
    if not isinstance(provided, list):
        return ["verification_result.durable_readback_proofs must be a list"]

    expected_by_output: dict[str, dict[str, str]] | None = None
    if expected_proofs is not None:
        expected_by_output = {
            str(proof.get("output_id")): dict(proof)
            for proof in expected_proofs
            if isinstance(proof, Mapping) and _non_blank(proof.get("output_id"))
        }

    seen: set[str] = set()
    for index, proof in enumerate(provided):
        prefix = f"verification_result.durable_readback_proofs[{index}]"
        if not isinstance(proof, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if set(proof) != _PROOF_FIELDS:
            errors.append(f"{prefix} has invalid fields")
            continue
        for field in ("assignment_id", "output_id", "system_of_record_ref", "artifact_ref", "content_digest"):
            if not _non_blank(proof.get(field)):
                errors.append(f"{prefix}.{field} must be a non-blank string")
        if proof.get("readback_status") != RESOLVED:
            errors.append(f"{prefix}.readback_status must be RESOLVED")
        digest = proof.get("content_digest")
        if isinstance(digest, str) and _DIGEST_RE.fullmatch(digest) is None:
            errors.append(f"{prefix}.content_digest must be a lowercase SHA-256 digest")
        if proof.get("assignment_id") != assignment_id:
            errors.append(f"{prefix}.assignment_id does not match the exact assignment")
        output_id = proof.get("output_id")
        if isinstance(output_id, str):
            if output_id not in required:
                errors.append(f"{prefix}.output_id is not a required durable output")
            if output_id in seen:
                errors.append(f"duplicate durable readback proof for output {output_id}")
            seen.add(output_id)
            if expected_by_output is None:
                errors.append(f"{prefix} is not backed by an independent durable readback observation")
            else:
                expected = expected_by_output.get(output_id)
                if expected is None or dict(proof) != expected:
                    errors.append(f"{prefix} does not match the exact independent readback observation")

    if required and expected_by_output is not None:
        missing = sorted(required - seen)
        if missing:
            errors.append(f"verification result is missing durable readback proofs: {missing}")

    if verification.get("status") == "CONFIRMED" and required:
        if expected_by_output is None or set(expected_by_output) != required:
            errors.append("CONFIRMED requires proven independent readback for every required durable output")
    return errors
