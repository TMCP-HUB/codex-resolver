from pathlib import Path
import unittest

from tools.validate_structure import ROOT_REQUIRED

ROOT = Path(__file__).resolve().parents[1]


class V0StructuralRegistrationTest(unittest.TestCase):
    def test_v0_bootstrap_surfaces_are_structurally_required(self) -> None:
        for rel in [
            "BOOTSTRAP.md",
            "contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md",
            "schemas/sbc-runtime-context.schema.json",
            "tools/bootstrap_runtime.py",
        ]:
            self.assertIn(rel, ROOT_REQUIRED)

    def test_structural_validator_checks_v0_manifest_registration(self) -> None:
        source = (ROOT / "tools/validate_structure.py").read_text(encoding="utf-8")
        for marker in [
            "bootstrap_entry: BOOTSTRAP.md",
            "contract: contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md",
            "schema: schemas/sbc-runtime-context.schema.json",
            "validator: tools/bootstrap_runtime.py",
        ]:
            self.assertIn(marker, source)

    def test_active_foundation_surfaces_are_structurally_required(self) -> None:
        for rel in [
            "engines/foundation/MANIFEST.yaml",
            "engines/foundation/workflows/form-project-foundation.md",
            "engines/foundation/schemas/project-seed.schema.json",
            "engines/foundation/schemas/project-outcome.schema.json",
            "engines/foundation/schemas/consequential-unknown-map.schema.json",
        ]:
            self.assertIn(rel, ROOT_REQUIRED)

    def test_structural_validator_checks_foundation_registration_and_declared_paths(self) -> None:
        source = (ROOT / "tools/validate_structure.py").read_text(encoding="utf-8")
        for marker in [
            "manifest_path: engines/foundation/MANIFEST.yaml",
            "form_project_foundation",
            "engines/foundation/MANIFEST.yaml",
            "engines/foundation/skills",
            "foundation schema is not closed",
        ]:
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
