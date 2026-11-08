from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest

from tools.durable_artifact_port import (
    BACKEND_FAILURE,
    MALFORMED_INPUT,
    MATERIALIZED,
    RESOLVED,
    UNRESOLVED,
    WRONG_SYSTEM_OF_RECORD,
    DurableArtifactPort,
    LocalFileDurableReferencePort,
)
from tools.durable_output_contract import validate_executor_durable_output_refs


class FailingReferencePort(LocalFileDurableReferencePort):
    def _persist_record(self, artifact_ref: str, record_bytes: bytes) -> None:
        raise OSError("synthetic backend write failure")


class DurableArtifactPortTest(unittest.TestCase):
    def test_materialization_returns_stable_nonempty_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            first = port.materialize("SOR-PRIMARY", "report", b"exact report bytes")
            second = port.materialize("SOR-PRIMARY", "report", b"exact report bytes")
            self.assertEqual(first.status, MATERIALIZED)
            self.assertTrue(first.artifact_ref)
            self.assertEqual(first.artifact_ref, second.artifact_ref)
            self.assertEqual(first.content_digest, second.content_digest)
            self.assertNotIn(tempdir, str(first.artifact_ref))

    def test_fresh_reader_resolves_exact_materialized_object(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            writer = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            materialized = writer.materialize("SOR-PRIMARY", "manifest", b"payload-v1")
            self.assertEqual(materialized.status, MATERIALIZED)
            artifact_ref = str(materialized.artifact_ref)
            content_digest = materialized.content_digest
            del writer

            reader = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            observed = reader.readback("SOR-PRIMARY", artifact_ref)
            self.assertEqual(observed.status, RESOLVED)
            self.assertEqual(observed.artifact_ref, artifact_ref)
            self.assertEqual(observed.output_identity, "manifest")
            self.assertEqual(observed.content_digest, content_digest)
            self.assertEqual(observed.payload, b"payload-v1")

    def test_wrong_system_of_record_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            writer = LocalFileDurableReferencePort(tempdir, "SOR-A")
            materialized = writer.materialize("SOR-A", "report", b"payload")
            self.assertEqual(materialized.status, MATERIALIZED)
            artifact_ref = str(materialized.artifact_ref)

            wrong_reader = LocalFileDurableReferencePort(tempdir, "SOR-B")
            observed = wrong_reader.readback("SOR-B", artifact_ref)
            self.assertEqual(observed.status, WRONG_SYSTEM_OF_RECORD)
            self.assertIsNone(observed.payload)

            wrong_write = writer.materialize("SOR-B", "report", b"payload")
            self.assertEqual(wrong_write.status, WRONG_SYSTEM_OF_RECORD)
            self.assertIsNone(wrong_write.artifact_ref)

    def test_unknown_and_malformed_refs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            reader = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            unknown = reader.readback("SOR-PRIMARY", "dar:v1:" + "0" * 64)
            self.assertEqual(unknown.status, UNRESOLVED)
            malformed = reader.readback("SOR-PRIMARY", "/tmp/not-a-durable-ref")
            self.assertEqual(malformed.status, MALFORMED_INPUT)

    def test_failed_materialization_does_not_mint_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = FailingReferencePort(tempdir, "SOR-PRIMARY")
            result = port.materialize("SOR-PRIMARY", "report", b"payload")
            self.assertEqual(result.status, BACKEND_FAILURE)
            self.assertIsNone(result.artifact_ref)
            self.assertFalse(any(Path(tempdir).iterdir()))

    def test_corrupt_persisted_record_is_backend_read_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            writer = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            materialized = writer.materialize("SOR-PRIMARY", "report", b"payload")
            artifact_ref = str(materialized.artifact_ref)
            path = writer._record_path(artifact_ref)
            path.write_text("not-json", encoding="utf-8")

            reader = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            observed = reader.readback("SOR-PRIMARY", artifact_ref)
            self.assertEqual(observed.status, BACKEND_FAILURE)
            self.assertIsNone(observed.payload)

    def test_distinct_output_identities_do_not_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            report = port.materialize("SOR-PRIMARY", "report", b"same bytes")
            manifest = port.materialize("SOR-PRIMARY", "manifest", b"same bytes")
            self.assertEqual(report.status, MATERIALIZED)
            self.assertEqual(manifest.status, MATERIALIZED)
            self.assertNotEqual(report.artifact_ref, manifest.artifact_ref)

    def test_unencodable_output_identity_is_malformed_input(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            result = port.materialize("SOR-PRIMARY", "\ud800", b"x")
            self.assertEqual(result.status, MALFORMED_INPUT)
            self.assertIsNone(result.artifact_ref)

    def test_unencodable_materialize_system_of_record_is_malformed_input(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            result = port.materialize("\ud800", "valid", b"x")
            self.assertEqual(result.status, MALFORMED_INPUT)
            self.assertIsNone(result.artifact_ref)

    def test_unencodable_readback_system_of_record_is_malformed_input(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            port = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            observed = port.readback("\ud800", "dar:v1:" + "0" * 64)
            self.assertEqual(observed.status, MALFORMED_INPUT)

    def test_unencodable_persisted_output_identity_is_backend_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            writer = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            materialized = writer.materialize("SOR-PRIMARY", "report", b"payload")
            artifact_ref = str(materialized.artifact_ref)
            path = writer._record_path(artifact_ref)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["output_identity"] = "\ud800"
            path.write_text(json.dumps(record), encoding="utf-8")

            reader = LocalFileDurableReferencePort(tempdir, "SOR-PRIMARY")
            observed = reader.readback("SOR-PRIMARY", artifact_ref)
            self.assertEqual(observed.status, BACKEND_FAILURE)
            self.assertIsNone(observed.payload)

    def test_a1_no_durable_output_behavior_is_unchanged(self) -> None:
        assignment = {}
        result = {"status": "COMPLETE"}
        self.assertEqual(validate_executor_durable_output_refs(result, assignment), [])

    def test_universal_port_shape_requires_no_provider_identifier(self) -> None:
        materialize = inspect.signature(DurableArtifactPort.materialize)
        readback = inspect.signature(DurableArtifactPort.readback)
        self.assertEqual(
            list(materialize.parameters),
            ["self", "system_of_record_ref", "output_identity", "payload"],
        )
        self.assertEqual(
            list(readback.parameters),
            ["self", "system_of_record_ref", "artifact_ref"],
        )


if __name__ == "__main__":
    unittest.main()
