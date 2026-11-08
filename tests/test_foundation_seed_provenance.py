from __future__ import annotations

import json
from pathlib import Path
import unittest

from tests.test_executability_parity import schema_accepts


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "engines/foundation/schemas/project-seed.schema.json"


class FoundationSeedProvenanceTest(unittest.TestCase):
    def test_seed_schema_preserves_owner_and_inference_classes_without_making_them_required(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema["properties"]
        self.assertIn("explicit_owner_statements", props)
        self.assertIn("strongly_implied_context", props)
        self.assertNotIn("explicit_owner_statements", schema["required"])
        self.assertNotIn("strongly_implied_context", schema["required"])

        value = {
            "artifact_type": "PROJECT_SEED",
            "artifact_id": "SEED-PROVENANCE-1",
            "produced_by_role": "executor",
            "assignment_id": "ASSIGN-FOUNDATION-1",
            "input_state_ref": "OWNER-REQUEST-1",
            "status": "WORKING",
            "provenance": ["OWNER-REQUEST-1"],
            "related_artifacts": [],
            "authoritative": False,
            "working_summary": "Working interpretation.",
            "explicit_owner_statements": ["Owner wants a project control system."],
            "strongly_implied_context": ["The project should remain usable in ordinary chat."],
            "working_interpretations": ["A Foundation phase is useful before Canon."],
            "model_proposals": ["Keep design discovery optional."],
        }
        self.assertTrue(schema_accepts(value, schema))


if __name__ == "__main__":
    unittest.main()
