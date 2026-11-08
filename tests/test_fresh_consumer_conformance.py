from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_resolver_transition import artifact, transition_bundle
from tools.durable_artifact_port import (
    BACKEND_FAILURE,
    MATERIALIZED,
    RESOLVED,
    UNRESOLVED,
    WRONG_SYSTEM_OF_RECORD,
    LocalFileDurableReferencePort,
)
from tools.durable_readback_enforcement import (
    READBACK_PROVEN,
    evaluate_required_durable_readback,
)
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]
SOR = "SOR-PRIMARY"
OUTPUT_ID = "report"

_FRESH_CONSUMER = r"""
import base64
import json
import os
from pathlib import Path
import sys

from tools.durable_artifact_port import LocalFileDurableReferencePort, RESOLVED

durable_root = Path(sys.argv[1])
handoff = json.loads(sys.stdin.read())
port = LocalFileDurableReferencePort(durable_root, handoff["system_of_record_ref"])
observation = port.readback(handoff["system_of_record_ref"], handoff["artifact_ref"])
accepted = (
    handoff.get("role_contract") == "fresh-independent-consumer"
    and observation.status == RESOLVED
    and observation.artifact_ref == handoff["artifact_ref"]
    and observation.output_identity == handoff["output_id"]
    and observation.content_digest == handoff.get("content_digest")
)
print(json.dumps({
    "pid": os.getpid(),
    "status": observation.status,
    "accepted": accepted,
    "artifact_ref": observation.artifact_ref,
    "output_identity": observation.output_identity,
    "content_digest": observation.content_digest,
    "payload_b64": (
        base64.b64encode(observation.payload).decode("ascii")
        if isinstance(observation.payload, bytes)
        else None
    ),
}, sort_keys=True))
"""


def _durable_handoff(
    *,
    assignment_id: str,
    artifact_ref: str,
    content_digest: str,
    system_of_record_ref: str = SOR,
    output_id: str = OUTPUT_ID,
) -> dict[str, str]:
    return {
        "assignment_id": assignment_id,
        "role_contract": "fresh-independent-consumer",
        "system_of_record_ref": system_of_record_ref,
        "output_id": output_id,
        "artifact_ref": artifact_ref,
        "content_digest": content_digest,
    }


def _fresh_consume(durable_root: Path, handoff: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-c", _FRESH_CONSUMER, str(durable_root)],
        cwd=ROOT,
        input=json.dumps(handoff),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _declare_required_output(value: dict, *, system_of_record_ref: str = SOR) -> tuple[dict, dict]:
    assignment = artifact(value, value["refs"]["assignment_ref"])
    result = artifact(value, value["refs"]["executor_result_ref"])
    assignment["required_durable_outputs"] = [OUTPUT_ID]
    assignment["durable_system_of_record_ref"] = system_of_record_ref
    return assignment, result


def _bind(result: dict, artifact_ref: str) -> None:
    result["durable_output_refs"] = [
        {"output_id": OUTPUT_ID, "artifact_ref": artifact_ref}
    ]


def _attach_56c_readback_proof(
    value: dict,
    port: LocalFileDurableReferencePort,
) -> tuple[dict[str, str], ...]:
    assignment = artifact(value, value["refs"]["assignment_ref"])
    result = artifact(value, value["refs"]["executor_result_ref"])
    evaluated = evaluate_required_durable_readback(assignment, result, port)
    if evaluated.status != READBACK_PROVEN:
        raise AssertionError(evaluated)
    verification = artifact(value, value["refs"]["verification_result_ref"])
    verification["durable_readback_proofs"] = [
        dict(proof) for proof in evaluated.proofs
    ]
    return evaluated.proofs


class FreshConsumerConformanceTest(unittest.TestCase):
    def test_materialized_output_survives_destroyed_predecessor_workspace_and_fresh_process(self) -> None:
        payload = b"authoritative durable report"
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            durable_root = root_path / "durable-store"
            predecessor_workspace = root_path / "predecessor-workspace"
            predecessor_workspace.mkdir()
            local_output = predecessor_workspace / "report.bin"
            local_output.write_bytes(payload)

            value = transition_bundle()
            assignment, result = _declare_required_output(value)
            producer_port = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = producer_port.materialize(
                SOR, OUTPUT_ID, local_output.read_bytes()
            )
            self.assertEqual(materialized.status, MATERIALIZED)
            self.assertIsNotNone(materialized.artifact_ref)
            self.assertIsNotNone(materialized.content_digest)
            _bind(result, str(materialized.artifact_ref))

            proofs = _attach_56c_readback_proof(value, producer_port)
            resolved = resolve_transition(value, durable_port=producer_port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED"),
            )
            accepted_proof = dict(proofs[0])
            handoff = _durable_handoff(
                assignment_id=str(assignment["assignment_id"]),
                artifact_ref=accepted_proof["artifact_ref"],
                content_digest=accepted_proof["content_digest"],
            )

            self.assertEqual(
                set(handoff),
                {
                    "assignment_id",
                    "role_contract",
                    "system_of_record_ref",
                    "output_id",
                    "artifact_ref",
                    "content_digest",
                },
            )
            self.assertFalse(
                any("chat" in key or "session" in key or "workspace" in key for key in handoff)
            )

            shutil.rmtree(predecessor_workspace)
            self.assertFalse(local_output.exists())
            del producer_port, value, assignment, result

            consumed = _fresh_consume(durable_root, handoff)
            self.assertNotEqual(consumed["pid"], os.getpid())
            self.assertEqual(consumed["status"], RESOLVED)
            self.assertTrue(consumed["accepted"])
            self.assertEqual(consumed["artifact_ref"], accepted_proof["artifact_ref"])
            self.assertEqual(consumed["output_identity"], accepted_proof["output_id"])
            self.assertEqual(consumed["content_digest"], accepted_proof["content_digest"])
            self.assertEqual(
                base64.b64decode(str(consumed["payload_b64"]).encode("ascii")),
                payload,
            )

    def test_local_only_output_cannot_complete_or_feed_fresh_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            durable_root = root_path / "durable-store"
            predecessor_workspace = root_path / "predecessor-workspace"
            predecessor_workspace.mkdir()
            local_output = predecessor_workspace / "report.bin"
            local_output.write_bytes(b"local-only report")

            value = transition_bundle()
            assignment, result = _declare_required_output(value)
            missing_ref = "dar:v1:" + "0" * 64
            _bind(result, missing_ref)
            port = LocalFileDurableReferencePort(durable_root, SOR)

            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("WAIT", "DURABLE_READBACK_NOT_PROVEN"),
            )
            self.assertTrue(local_output.exists())

            handoff = _durable_handoff(
                assignment_id=str(assignment["assignment_id"]),
                artifact_ref=missing_ref,
                content_digest="0" * 64,
            )
            shutil.rmtree(predecessor_workspace)
            consumed = _fresh_consume(durable_root, handoff)
            self.assertEqual(consumed["status"], UNRESOLVED)
            self.assertFalse(consumed["accepted"])

    def test_stale_or_wrong_output_ref_is_not_rescued_by_predecessor_local_state(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            durable_root = root_path / "durable-store"
            predecessor_workspace = root_path / "predecessor-workspace"
            predecessor_workspace.mkdir()
            (predecessor_workspace / "report.bin").write_bytes(b"current local report")

            value = transition_bundle()
            assignment, result = _declare_required_output(value)
            port = LocalFileDurableReferencePort(durable_root, SOR)
            stale = port.materialize(SOR, "other-output", b"stale durable bytes")
            self.assertEqual(stale.status, MATERIALIZED)
            _bind(result, str(stale.artifact_ref))

            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("ESCALATE", "DURABLE_READBACK_INVALID"),
            )
            handoff = _durable_handoff(
                assignment_id=str(assignment["assignment_id"]),
                artifact_ref=str(stale.artifact_ref),
                content_digest=str(stale.content_digest),
            )
            consumed = _fresh_consume(durable_root, handoff)
            self.assertEqual(consumed["status"], RESOLVED)
            self.assertEqual(consumed["output_identity"], "other-output")
            self.assertFalse(consumed["accepted"])

    def test_wrong_system_of_record_fails_even_with_similarly_named_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            durable_root = root_path / "durable-store"
            local_output = root_path / "report.bin"
            local_output.write_bytes(b"same-looking local report")

            value = transition_bundle()
            assignment, result = _declare_required_output(
                value, system_of_record_ref="SOR-WRONG"
            )
            producer_port = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = producer_port.materialize(
                SOR, OUTPUT_ID, b"authoritative report"
            )
            self.assertEqual(materialized.status, MATERIALIZED)
            _bind(result, str(materialized.artifact_ref))

            wrong_port = LocalFileDurableReferencePort(durable_root, "SOR-WRONG")
            resolved = resolve_transition(value, durable_port=wrong_port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("ESCALATE", "DURABLE_READBACK_INVALID"),
            )
            self.assertTrue(local_output.exists())

            handoff = _durable_handoff(
                assignment_id=str(assignment["assignment_id"]),
                artifact_ref=str(materialized.artifact_ref),
                content_digest=str(materialized.content_digest),
                system_of_record_ref="SOR-WRONG",
            )
            consumed = _fresh_consume(durable_root, handoff)
            self.assertEqual(consumed["status"], WRONG_SYSTEM_OF_RECORD)
            self.assertFalse(consumed["accepted"])

    def test_changed_durable_object_fails_closed_against_bound_identity(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            durable_root = Path(root) / "durable-store"
            value = transition_bundle()
            assignment, result = _declare_required_output(value)
            producer_port = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = producer_port.materialize(
                SOR, OUTPUT_ID, b"original durable report"
            )
            self.assertEqual(materialized.status, MATERIALIZED)
            _bind(result, str(materialized.artifact_ref))

            record_path = producer_port._record_path(str(materialized.artifact_ref))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["payload_b64"] = base64.b64encode(b"tampered report").decode("ascii")
            record_path.write_text(
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )

            fresh_port = LocalFileDurableReferencePort(durable_root, SOR)
            resolved = resolve_transition(value, durable_port=fresh_port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("WAIT", "DURABLE_READBACK_NOT_PROVEN"),
            )

            handoff = _durable_handoff(
                assignment_id=str(assignment["assignment_id"]),
                artifact_ref=str(materialized.artifact_ref),
                content_digest=str(materialized.content_digest),
            )
            consumed = _fresh_consume(durable_root, handoff)
            self.assertEqual(consumed["status"], BACKEND_FAILURE)
            self.assertFalse(consumed["accepted"])

    def test_fresh_subprocess_requires_no_predecessor_globals_or_session_metadata(self) -> None:
        payload = b"no hidden cache needed"
        with tempfile.TemporaryDirectory() as root:
            durable_root = Path(root) / "durable-store"
            writer = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = writer.materialize(SOR, OUTPUT_ID, payload)
            self.assertEqual(materialized.status, MATERIALIZED)
            handoff = _durable_handoff(
                assignment_id="ASSIGN-FRESH",
                artifact_ref=str(materialized.artifact_ref),
                content_digest=str(materialized.content_digest),
            )
            del writer

            consumed = _fresh_consume(durable_root, handoff)
            self.assertNotEqual(consumed["pid"], os.getpid())
            self.assertTrue(consumed["accepted"])
            self.assertEqual(
                base64.b64decode(str(consumed["payload_b64"]).encode("ascii")),
                payload,
            )

    def test_zero_required_durable_outputs_preserve_legacy_completion(self) -> None:
        resolved = resolve_transition(transition_bundle())
        self.assertEqual(
            (resolved["control_state"], resolved["reason"]),
            ("COMPLETE", "DIRECTOR_ACCEPTANCE_CONDITION_SATISFIED"),
        )

    def test_artifact_availability_does_not_override_factual_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            durable_root = Path(root) / "durable-store"
            value = transition_bundle(
                verification_status="NOT_PROVEN",
                incomplete="WAIT",
            )
            assignment, result = _declare_required_output(value)
            port = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = port.materialize(
                SOR, OUTPUT_ID, b"available but not factually proven"
            )
            self.assertEqual(materialized.status, MATERIALIZED)
            _bind(result, str(materialized.artifact_ref))
            _attach_56c_readback_proof(value, port)

            resolved = resolve_transition(value, durable_port=port)
            self.assertEqual(
                (resolved["control_state"], resolved["reason"]),
                ("WAIT", "AUTHORIZED_VERIFICATION_OUTCOME"),
            )
            self.assertEqual(resolved["verification_outcome"], "NOT_PROVEN")

    def test_fresh_consumer_matches_exact_identity_accepted_by_56c(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            durable_root = Path(root) / "durable-store"
            value = transition_bundle()
            assignment, result = _declare_required_output(value)
            port = LocalFileDurableReferencePort(durable_root, SOR)
            materialized = port.materialize(SOR, OUTPUT_ID, b"identity-bound")
            self.assertEqual(materialized.status, MATERIALIZED)
            _bind(result, str(materialized.artifact_ref))
            proofs = _attach_56c_readback_proof(value, port)
            proof = dict(proofs[0])

            consumed = _fresh_consume(
                durable_root,
                _durable_handoff(
                    assignment_id=str(assignment["assignment_id"]),
                    artifact_ref=proof["artifact_ref"],
                    content_digest=proof["content_digest"],
                    system_of_record_ref=proof["system_of_record_ref"],
                    output_id=proof["output_id"],
                ),
            )
            self.assertTrue(consumed["accepted"])
            self.assertEqual(consumed["artifact_ref"], proof["artifact_ref"])
            self.assertEqual(consumed["output_identity"], proof["output_id"])
            self.assertEqual(consumed["content_digest"], proof["content_digest"])


if __name__ == "__main__":
    unittest.main()
