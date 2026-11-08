from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProviderNeutralSurfaceNamesTest(unittest.TestCase):
    def test_active_universal_surface_names_are_provider_neutral(self) -> None:
        contract = (ROOT / "contracts/EXECUTABILITY_CONTRACT.md").read_text(encoding="utf-8")
        owner_actionability = (
            ROOT / "roles/owner-interface/skills/owner-actionability/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("REMOTE_CODE_EXECUTOR", contract)
        self.assertNotIn("CODEX_CLOUD", contract)
        self.assertNotIn("Codex Cloud", owner_actionability)
        self.assertIn("internal execution surfaces", owner_actionability)


if __name__ == "__main__":
    unittest.main()
