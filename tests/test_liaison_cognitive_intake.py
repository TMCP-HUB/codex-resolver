from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles/owner-interface/ROLE.md"
BOOTSTRAP = ROOT / "BOOTSTRAP.md"
INTENT = ROOT / "roles/owner-interface/skills/owner-intent-sensemaking/SKILL.md"
CONTEXT = ROOT / "roles/owner-interface/skills/project-context-orientation/SKILL.md"


class LiaisonCognitiveIntakeTest(unittest.TestCase):
    def test_cognitive_base_skills_exist(self) -> None:
        self.assertTrue(INTENT.is_file())
        self.assertTrue(CONTEXT.is_file())

    def test_intent_skill_preserves_native_reasoning_without_inventing_authority(self) -> None:
        text = INTENT.read_text(encoding="utf-8")
        self.assertIn("PROJECT RESOLVER AUGMENTS NATIVE MODEL REASONING", text)
        self.assertIn("SKILLS DO NOT REPLACE INTELLIGENCE", text)
        self.assertIn("explicit Owner statements", text)
        self.assertIn("working interpretations", text)
        self.assertIn("MUST NOT invent Owner intent", text)
        self.assertIn("materially change the project, route, authority, output, or next action", text)
        self.assertIn("prefer stating a safe working interpretation", text)
        self.assertIn("must not become Canon", text)

    def test_context_orientation_has_only_behavioral_intake_dispositions(self) -> None:
        text = CONTEXT.read_text(encoding="utf-8")
        for disposition in ("RESPOND_IN_PLACE", "CLARIFY", "ROUTE"):
            self.assertIn(disposition, text)
        self.assertIn("ordinary question", text)
        self.assertIn("new project / raw idea", text)
        self.assertIn("existing-project work", text)
        self.assertIn("genuine Owner decision", text)
        self.assertIn("behavioral dispositions", text)
        self.assertIn("not a new artifact ontology", text)
        self.assertIn("does not become the Router", text)

    def test_progressive_skill_depth_is_explicit(self) -> None:
        role = ROLE.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        for stage in ("AWARE", "INSPECT", "LOAD", "APPLY", "MATERIALIZE"):
            self.assertIn(stage, role)
        self.assertIn("ABSENCE OF A SELECTED SKILL", role)
        self.assertIn("owner-intent-sensemaking", role)
        self.assertIn("project-context-orientation", role)
        self.assertIn("RESPOND_IN_PLACE", bootstrap)
        self.assertIn("CLARIFY", bootstrap)
        self.assertIn("ROUTE", bootstrap)
        self.assertIn("native model reasoning", bootstrap.lower())

    def test_intake_does_not_force_every_request_through_an_engine(self) -> None:
        role = ROLE.read_text(encoding="utf-8")
        self.assertIn("ordinary question", role)
        self.assertIn("no Engine required", role)
        self.assertIn("Research only", role)
        self.assertIn("Foundation", role)
        self.assertIn("Canon", role)


if __name__ == "__main__":
    unittest.main()
