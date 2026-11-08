from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tests.test_executability_parity import schema_accepts
from tests.test_resolver_transition import artifact, transition_bundle
from tools.durable_artifact_port import (
    BACKEND_FAILURE,
    MATERIALIZED,
    RESOLVED,
    LocalFileDurableReferencePort,
    ReadbackObservation,
)
from tools.durable_readback_enforcement import (
    READBACK_PROVEN,
    evaluate_required_durable_readback,
)
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]
SOR = "SOR-PRIMARY"


def _declare(value: dict, *output_ids: str, system_of_record_ref: str = SOR) -> tuple[dict, dict]:
    assignment = artifact(value, value["refs"]["assignment_ref"])
    result = artifact(value, value["refs"]["executor_result_ref"])
    assignment["required_durable_outputs"] = list(output_ids)
    if output_ids:
        assignment["durable_system_of_record_ref"] = system_of_record_ref
    return assignment, result


def _bind(result: dict, *pairs: tuple[str, str]) -> None:
    result["durable_output_refs"] = [
        {"output_id": output_id, "artifact_ref": artifact_ref}
        for output_id, artifact_ref in pairs
    ]


def _materialize_and_bind(port: LocalFileDurableReferencePort, assignment: dict, result: dict, output_id: str, payload: bytes):
    materialized = port.materialize(assignment["durable_system_of_record_ref"], output_id, payload)
    if materialized.status != MATERIALIZED or materialized.artifact_ref is None:
        raise AssertionError(materialized)
    _bind(result, (output_id, materialized.artifact_ref))
    return materialized


def _attach_exact_readback_proofs(value: dict, port) -> tuple:
    assignment = artifact(value, value["refs"]["assignment_ref"])
    result = artifact(value, value["refs"]["executor_result_ref"])
    evaluated = evaluate_required_durable_readback(assignment, result, port)
    if evaluated.status != READBACK_PROVEN:
        raise AssertionError(evaluated)
    verification = artifact(value, value["refs"]["verification_result_ref"])
    verification["durable_readback_proofs"] = [dict(proof) for proof in evaluated.proofs]
    return evaluated.observations


class IdentityMismatchPort:
    def readback(self, system_of_record_ref: str, artifact_ref: str) -> ReadbackObservation:
        return ReadbackObservation(
            RESOLVED,
            system_of_record_ref=system_of_record_ref,
            artifact_ref=artifact_ref,
            output_identity="other-output",
            content_digest="a" * 64,
            payload=b"other",
        )


class BackendFailurePort:
    def readback(self, system_of_record_ref: str, artifact_ref: str) -> ReadbackObservation:
        return ReadbackObservation(
            BACKEND_FAILURE,
            system_of_record_ref=system_of_record_ref,
            artifact_ref=artifact_ref,
            error="backend unavailable",
        )


class DurableReadbackEnforcementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verification_schema = json.loads((ROOT / "schemas/verification-result.schema.json").read_text())

    def test_valid_a1_refs_and_independent_readback_reach_normal_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            _materialize_and_bind(port, assignment, result, "report", b"authoritative-report")
            observations = _attach_exact_readback_proofs(value, port)
            self.assertEqual(observations[0].payload, b"authoritative-report")
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED"))

    def test_valid_looking_unresolved_ref_cannot_satisfy_durable_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            _bind(result, ("report", "dar:v1:" + "0" * 64))
            port = LocalFileDurableReferencePort(tempdir, SOR)
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("WAIT", "DURABLE_READBACK_NOT_PROVEN"))

    def test_wrong_system_of_record_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            materialized = _materialize_and_bind(port, assignment, result, "report", b"report")
            assignment["durable_system_of_record_ref"] = "SOR-OTHER"
            _bind(result, ("report", materialized.artifact_ref))
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("ESCALATE", "DURABLE_READBACK_INVALID"))

    def test_readback_identity_mismatch_fails_closed(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("report", "opaque-durable-ref"))
        resolved = resolve_transition(value, durable_port=IdentityMismatchPort())
        self.assertEqual((resolved["control_state"], resolved["reason"]),
                         ("ESCALATE", "DURABLE_READBACK_INVALID"))
        self.assertTrue(any("output identity mismatch" in error for error in resolved["errors"]), resolved)

    def test_local_executor_copy_cannot_substitute_for_failed_readback(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            result["local_output_copy"] = "complete local report"
            _bind(result, ("report", "dar:v1:" + "1" * 64))
            port = LocalFileDurableReferencePort(tempdir, SOR)
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("WAIT", "DURABLE_READBACK_NOT_PROVEN"))

    def test_confirmed_is_rejected_without_required_readback_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            _materialize_and_bind(port, assignment, result, "report", b"report")
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("ESCALATE", "VERIFICATION_DURABLE_READBACK_MISMATCH"))
            self.assertTrue(
                any("missing durable readback proofs" in error and "report" in error for error in resolved["errors"]),
                resolved,
            )

    def test_verifier_bound_to_exact_readback_artifact_can_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            materialized = _materialize_and_bind(port, assignment, result, "report", b"authoritative")
            observations = _attach_exact_readback_proofs(value, port)
            verification = artifact(value, "VERIFY-1")
            proof = verification["durable_readback_proofs"][0]
            self.assertEqual(proof["artifact_ref"], materialized.artifact_ref)
            self.assertEqual(proof["content_digest"], observations[0].content_digest)
            self.assertTrue(schema_accepts(verification, self.verification_schema))
            self.assertEqual(resolve_transition(value, durable_port=port)["control_state"], "COMPLETE")

    def test_control_does_not_advance_when_readback_or_verification_is_blocked(self) -> None:
        value = transition_bundle()
        assignment, result = _declare(value, "report")
        _bind(result, ("report", "opaque-durable-ref"))
        unresolved = resolve_transition(value, durable_port=BackendFailurePort())
        self.assertEqual((unresolved["control_state"], unresolved["reason"]),
                         ("WAIT", "DURABLE_READBACK_NOT_PROVEN"))

        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle(verification_status="BLOCKED")
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            _materialize_and_bind(port, assignment, result, "report", b"report")
            _attach_exact_readback_proofs(value, port)
            blocked = resolve_transition(value, durable_port=port)
            self.assertEqual((blocked["control_state"], blocked["reason"]),
                             ("WAIT", "AUTHORIZED_VERIFICATION_OUTCOME"))

    def test_zero_required_durable_outputs_preserve_existing_behavior(self) -> None:
        value = transition_bundle()
        resolved = resolve_transition(value)
        self.assertEqual((resolved["control_state"], resolved["reason"]),
                         ("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED"))

    def test_noncomplete_executor_results_do_not_fabricate_readback_proofs(self) -> None:
        for status in ("PARTIAL", "BLOCKED", "FAILED"):
            with self.subTest(status=status):
                value = transition_bundle()
                assignment, result = _declare(value, "report")
                result["status"] = status
                result.pop("durable_output_refs", None)
                resolved = resolve_transition(value)
                self.assertEqual((resolved["control_state"], resolved["reason"]),
                                 ("WAIT", "AUTHORIZED_REQUIREMENT_PENDING"))

    def test_readback_proof_does_not_automatically_confirm_factual_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle(verification_status="NOT_PROVEN", incomplete="WAIT")
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            _materialize_and_bind(port, assignment, result, "report", b"available-but-not-factually-proven")
            _attach_exact_readback_proofs(value, port)
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("WAIT", "AUTHORIZED_VERIFICATION_OUTCOME"))
            self.assertEqual(resolved["verification_outcome"], "NOT_PROVEN")

    def test_verifier_local_copy_digest_cannot_replace_authoritative_readback(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            port = LocalFileDurableReferencePort(tempdir, SOR)
            _materialize_and_bind(port, assignment, result, "report", b"authoritative")
            _attach_exact_readback_proofs(value, port)
            verification = artifact(value, "VERIFY-1")
            verification["durable_readback_proofs"][0]["content_digest"] = hashlib.sha256(b"executor-local-copy").hexdigest()
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("ESCALATE", "VERIFICATION_DURABLE_READBACK_MISMATCH"))

    def test_malformed_durable_ref_fails_closed_through_port(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            value = transition_bundle()
            assignment, result = _declare(value, "report")
            _bind(result, ("report", "not-a-56-b-ref"))
            port = LocalFileDurableReferencePort(tempdir, SOR)
            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual((resolved["control_state"], resolved["reason"]),
                             ("ESCALATE", "DURABLE_READBACK_INVALID"))


if __name__ == "__main__":
    unittest.main()
