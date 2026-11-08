from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.agent_native_preflight import observe


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=directory, text=True).strip()


def setup_repo(path: Path, remote: str) -> str:
    path.mkdir()
    git(path, "init", "-q")
    git(path, "config", "user.name", "Test User")
    git(path, "config", "user.email", "test@example.invalid")
    (path / "README.md").write_text("Fixture\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-qm", "fixture")
    git(path, "remote", "add", "origin", remote)
    return git(path, "rev-parse", "HEAD")


class AgentNativePreflightTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.target = root / "target"
        self.resolver = root / "codex"
        self.target_sha = setup_repo(self.target, "https://github.com/example/target.git")
        self.resolver_sha = setup_repo(self.resolver, "https://github.com/example/codex.git")

    def check(self, **kwargs: str) -> dict:
        inputs = dict(
            target=self.target,
            resolver=self.resolver,
            target_sha=self.target_sha,
            resolver_sha=self.resolver_sha,
        )
        inputs.update(kwargs)
        return observe(**inputs)

    def test_clean_exact_heads_match_but_cannot_claim_remote_freshness(self) -> None:
        result = self.check()
        self.assertEqual(result["status"], "LOCAL_STATE_MATCH")
        self.assertEqual(result["target"]["head_sha"], self.target_sha)
        self.assertIn("REMOTE_HEAD_FRESHNESS_NOT_PROVEN", result["limitations"])
        self.assertIn("ASSIGNMENT_AUTHORITY_NOT_PROVEN", result["limitations"])

    def test_wrong_expected_sha_fails_closed(self) -> None:
        result = self.check(target_sha="0" * 40)
        self.assertEqual(result["status"], "NOT_PROVEN")
        self.assertIn("TARGET_HEAD_SHA_MISMATCH", result["errors"])

    def test_dirty_worktree_fails_closed(self) -> None:
        (self.target / "README.md").write_text("mutated\n", encoding="utf-8")
        result = self.check()
        self.assertIn("TARGET_DIRTY_CHECKOUT", result["errors"])

    def test_unexpected_branch_fails_closed(self) -> None:
        result = self.check(target_branch="not-current")
        self.assertIn("TARGET_BRANCH_MISMATCH", result["errors"])

    def test_repository_identity_must_be_distinct(self) -> None:
        result = observe(self.target, self.target, self.target_sha, self.target_sha)
        self.assertIn("TARGET_AND_RESOLVER_MUST_BE_DISTINCT", result["errors"])

    def test_invalid_expected_sha_fails_closed(self) -> None:
        result = self.check(target_sha="main")
        self.assertIn("TARGET_EXPECTED_SHA_MUST_BE_FULL", result["errors"])


if __name__ == "__main__":
    unittest.main()
