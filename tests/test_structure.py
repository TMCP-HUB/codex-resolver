from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_structure import validate_research_machine_only_gate


class ProjectResolverStructureTest(unittest.TestCase):
    def test_structural_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_structure.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_T29_structural_gate_detects_broken_machine_only_regression(self) -> None:
        errors = validate_research_machine_only_gate(
            ROOT,
            regression_runner=lambda: ["T-DELIBERATE: machine-only regression failed"],
        )
        self.assertTrue(any("T-DELIBERATE" in error for error in errors), msg=str(errors))
        source = (ROOT / "tools/validate_structure.py").read_text(encoding="utf-8")
        self.assertIn("errors.extend(validate_research_machine_only_gate(ROOT))", source)


if __name__ == "__main__":
    unittest.main()
