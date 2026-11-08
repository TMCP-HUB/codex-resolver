from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "engines/production/software/tools/check_branch_integrity.py"
SPEC = importlib.util.spec_from_file_location("check_branch_integrity", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def populated_state(**overrides: str) -> str:
    values = {
        "Current branch:": "repair/example",
        "Target branch:": "main",
        "Base SHA:": "a" * 40,
        "Merge base SHA:": "b" * 40,
        "Working HEAD:": "c" * 40,
        "Intended HEAD:": "c" * 40,
        "PR HEAD:": "N/A",
        "Reviewed HEAD:": "N/A",
        "Tested HEAD:": "c" * 40,
        "Target HEAD at last integration check:": "d" * 40,
        "Risk level:": "LOW",
    }
    values.update(overrides)
    return "# Branch State\n\n" + "\n".join(f"- {label} {value}" for label, value in values.items()) + "\n"


class BranchIntegrityCheckerTest(unittest.TestCase):
    def test_current_template_identity_shape_passes_when_populated(self) -> None:
        self.assertEqual(checker.validate_branch_state_text(populated_state()), [])

    def test_missing_required_identity_fails(self) -> None:
        text = populated_state().replace(f"- Reviewed HEAD: N/A\n", "")
        self.assertIn("missing required label: Reviewed HEAD:", checker.validate_branch_state_text(text))

    def test_blank_required_identity_fails(self) -> None:
        errors = checker.validate_branch_state_text(populated_state(**{"Tested HEAD:": ""}))
        self.assertIn("blank required identity: Tested HEAD:", errors)

    def test_blank_required_non_identity_fields_fail(self) -> None:
        for label in ("Current branch:", "Target branch:", "Risk level:"):
            with self.subTest(label=label):
                errors = checker.validate_branch_state_text(populated_state(**{label: ""}))
                self.assertIn(f"blank required field: {label}", errors)

    def test_multiline_value_does_not_fill_blank_identity(self) -> None:
        text = populated_state(**{"Base SHA:": "\n  " + "a" * 40})
        self.assertIn("blank required identity: Base SHA:", checker.validate_branch_state_text(text))

    def test_duplicate_label_with_blank_first_does_not_bypass(self) -> None:
        text = populated_state(**{"Base SHA:": ""}) + f"- Base SHA: {'a' * 40}\n"
        self.assertIn("blank required identity: Base SHA:", checker.validate_branch_state_text(text))

    def test_permitted_na_passes(self) -> None:
        self.assertEqual(
            checker.validate_branch_state_text(
                populated_state(**{"PR HEAD:": "N/A", "Reviewed HEAD:": "N/A", "Tested HEAD:": "N/A"})
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
