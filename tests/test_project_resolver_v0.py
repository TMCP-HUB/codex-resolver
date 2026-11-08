from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectResolverV0Test(unittest.TestCase):
    def test_ordinary_chat_is_valid_liaison_mode_without_sbc(self) -> None:
        role = (ROOT / "roles/owner-interface/ROLE.md").read_text(encoding="utf-8")
        actionability = (ROOT / "roles/owner-interface/skills/owner-actionability/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ORDINARY_CHAT", role)
        self.assertIn("Absence of SBC context", actionability)
        self.assertIn("does not itself create `BLOCKED_NO_ADMISSIBLE_SURFACE`", actionability)
        self.assertIn("Never invent SBC Browser", actionability)

    def test_role_mobility_respects_director_executor_and_verifier_boundaries(self) -> None:
        roles = (ROOT / "roles/MANIFEST.yaml").read_text(encoding="utf-8")
        liaison = (ROOT / "roles/owner-interface/ROLE.md").read_text(encoding="utf-8")
        director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
        executor = (ROOT / "roles/executor/ROLE.md").read_text(encoding="utf-8")
        verifier = (ROOT / "roles/control-verifier/ROLE.md").read_text(encoding="utf-8")
        adapter = (ROOT / "adapters/agent-native/README.md").read_text(encoding="utf-8")
        self.assertIn("Role != agent instance", roles)
        self.assertIn("Liaison -> Director -> Liaison", director)
        self.assertIn("Director never executes its own Software Assignment", director)
        self.assertIn("Executor never merges", director)
        self.assertIn("two distinct governed Assignments", executor)
        self.assertIn("separate instance from its Executor", verifier)
        self.assertIn("genuinely separate instance", liaison)
        self.assertIn("manual Chat coordination", adapter)

    def test_audit_to_executor_workflow_preserves_independent_acceptance(self) -> None:
        diagnosis = (ROOT / "engines/production/software/workflows/diagnosis.md").read_text(encoding="utf-8")
        audit = (ROOT / "engines/production/software/skills/operational-auditing/SKILL.md").read_text(encoding="utf-8")
        review = (ROOT / "engines/production/software/skills/pre-merge-review/SKILL.md").read_text(encoding="utf-8")
        verification = (ROOT / "engines/verification/skills/proof-loop-verification/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("different Assignments", diagnosis)
        self.assertIn("Findings alone do not authorize", audit)
        self.assertIn("Director Control Review", review)
        self.assertIn("distinct instance", verification)

    def test_stage1_host_role_profiles_are_explicit_and_bounded(self) -> None:
        manifest = (ROOT / "roles/MANIFEST.yaml").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        bootstrap = (ROOT / "BOOTSTRAP.md").read_text(encoding="utf-8")
        codex = (ROOT / "roles/executor/ROLE.md").read_text(encoding="utf-8")
        director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
        verifier = (ROOT / "roles/control-verifier/ROLE.md").read_text(encoding="utf-8")
        self.assertIn("codex_cloud: [executor]", manifest)
        self.assertIn("chatgpt_work: [owner-interface, control-director, control-verifier]", manifest)
        self.assertIn("chatgpt_work_native_subagent: [executor, control-verifier]", manifest)
        self.assertIn("chatgpt_chat: [owner-interface, control-director, control-verifier, executor]", manifest)
        self.assertIn("stage1_physical_host_gate_implemented: false", manifest)
        self.assertIn("Codex Cloud", agents)
        self.assertIn("ChatGPT Work", agents)
        self.assertIn("ChatGPT Chat", agents)
        self.assertIn("does **not** attest", router)
        self.assertIn("does not prove this instance", bootstrap)
        self.assertIn("Work Director parent instance never executes its own Software assignment", codex)
        self.assertIn("native Work Subagent", codex)
        self.assertIn("distinct Work Subagent", agents)
        self.assertIn("Work Subagent", verifier)
        self.assertIn("not Codex Cloud", director)
        self.assertIn("not Codex Cloud", verifier)

    def test_diagnosis_vertical_slice_resolves_to_existing_skill(self) -> None:
        bootstrap = (ROOT / "BOOTSTRAP.md").read_text(encoding="utf-8")
        router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
        manifest = (ROOT / "engines/production/software/MANIFEST.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / "engines/production/software/workflows/diagnosis.md").read_text(encoding="utf-8")
        skill = ROOT / "engines/production/software/skills/systematic-debugging/SKILL.md"

        self.assertIn("diagnose_software_failure", router)
        self.assertIn("diagnose_software_failure: diagnosis", manifest)
        self.assertIn("systematic-debugging", workflow)
        self.assertTrue(skill.is_file())
        self.assertIn("does not require PAK", bootstrap)
        self.assertIn("does not make diagnosis the default route", bootstrap)


if __name__ == "__main__":
    unittest.main()
