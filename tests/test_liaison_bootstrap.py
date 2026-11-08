from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LiaisonBootstrapTest(unittest.TestCase):
    def test_fresh_liaison_has_explicit_bootstrap_entry(self) -> None:
        manifest = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
        bootstrap = (ROOT / "BOOTSTRAP.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        match = re.search(r"(?m)^bootstrap_entry:\s*(\S+)\s*$", manifest)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "BOOTSTRAP.md")

        for marker in [
            "ORDINARY_CHAT",
            "SBC_RUNTIME_CONTEXT",
            "AGENTS.md",
            "SYSTEM_MANIFEST.yaml",
            "ROUTER.md",
            "NO GLOBAL SKILL DISCOVERY",
        ]:
            self.assertIn(marker, bootstrap)

        self.assertNotIn("execution ticket required", bootstrap.lower())
        self.assertIn("BOOTSTRAP.md", readme)
        self.assertIn("fresh Liaison", readme)
        self.assertIn("BOOTSTRAP.md", agents)


if __name__ == "__main__":
    unittest.main()
