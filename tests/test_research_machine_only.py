from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.research_policy import (
    FATAL_FINDINGS,
    _action_dispositions,
    _resolve_governor_scopes,
    _policy_units,
    _propositions,
    classify_text,
    machine_only_regression_results,
    validate_experiment,
    validate_human_research_authorization,
    validate_method_freeze,
    validate_question,
    validate_separate_human_work_package,
    validate_source,
    validate_work_package,
)


def base_wp() -> dict:
    return {
        "WORK_PACKAGE_ID":"WP-001","QUESTION_ID":"Q-001","NAMESPACE":"research/default",
        "EXECUTOR_ROLE":"AI_R_MASTER","VERIFIER_ROLE":"AI_R_VERIFIER","MACHINE_EXECUTABLE":True,
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_REVIEWER":False,"REQUIRES_EXTERNAL_HUMAN_REVIEW":False,
        "REQUIRES_NEW_HUMAN_DATA":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,
        "EXECUTION_SURFACE":"local machine runtime","SOURCE_ACCESS_METHOD":"public machine-accessible corpus",
        "COMPUTATION_METHOD":"deterministic structural analysis","VERIFICATION_METHOD":"automated reproducibility check",
        "LIMITATIONS":[],"PROHIBITED_OVERCLAIMS":["Do not claim direct population measurement."],"OWNER_GATE_IF_ANY":None,
    }


def base_question() -> dict:
    return {
        "QUESTION_ID":"Q-001","QUESTION":"What structural pattern is supported?","TARGET_CONSTRUCT":"structural pattern",
        "MACHINE_EXECUTABLE":True,"AVAILABLE_MACHINE_METHODS":["deterministic corpus analysis"],
        "AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE":["Published survey may be used as static evidence."],
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
        "DIRECT_MEASUREMENT_POSSIBLE":False,"PROXY_MEASUREMENT_POSSIBLE":True,
        "EXPECTED_LIMITATION":"Direct population measurement remains unavailable.","OWNER_DECISION_COMPONENT":None,
        "CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,
        "ADMISSION_STATUS":"ADMITTED_MACHINE_RESEARCH",
    }


def owner_auth_pair() -> tuple[dict, dict]:
    auth = {
        "AUTHORIZATION_ID":"HRA-001","OWNER_DECISION_RECORD_REF":"ODR-001","OWNER_AUTHORITY_ROLE":"OWNER_K0",
        "PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","SCOPE":"one bounded recognition study",
        "NAMESPACE":"human-research/P-1/Q-H1","NON_TRANSITIVE":True,
        "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM":True,"REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE":True,
        "DEFAULT_RESEARCH_MODE_UNCHANGED":True,
    }
    record = {
        "artifact_type":"OWNER_DECISION_RECORD","artifact_id":"ODR-001","produced_by_role":"owner-interface",
        "assignment_id":"A-OWNER-001","input_state_ref":"state:pre-human-research","status":"RECORDED",
        "provenance":["OWNER_K0 explicit authorization decision"],"related_artifacts":["P-1","Q-H1"],
        "question_ref":"Q-H1","options_presented":["AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","DO_NOT_AUTHORIZE"],
        "selected_option":"AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","owner_constraints":["bounded scope only"],
        "consequences_acknowledged":["default Research remains machine-only"],"authority_role":"OWNER_K0",
        "decision_kind":"CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","project_id":"P-1","authorized_question_id":"Q-H1",
        "authorized_scope":"one bounded recognition study","authorized_namespace":"human-research/P-1/Q-H1",
        "authorization_id":"HRA-001","non_transitive":True,"default_research_mode_unchanged":True,
    }
    return auth, record


def resolver_for(record: dict):
    return lambda ref: record if ref == record.get("artifact_id") else None


def base_experiment() -> dict:
    return {
        "EXPERIMENT_ID":"EXP-1","RUN_ID":"RUN-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN",
        "FREEZE_ID":"FRZ-1","INPUT_DATASET":"public machine-readable corpus","INPUT_VERSION":"1",
        "INPUT_HASH":"sha256:input","MODEL_OR_TOOL":"python","MODEL_OR_TOOL_VERSION":"3",
        "PROMPT_OR_RULESET_VERSION":"rules-1","RANDOM_SEED":1,"N_RUNS":1,"BENCHMARK_SET":[],"HOLDOUT_SET":[],
        "PERTURBATION_SET":[],"ADVERSARIAL_CASES":[],"ERROR_METRIC":"exact mismatch","AGGREGATION_METHOD":"deterministic",
        "UNCERTAINTY_METHOD":"sensitivity bounds","CROSS_METHOD_AGREEMENT":"not applicable",
        "CROSS_MODEL_DISAGREEMENT":"not applicable","OUTPUT_HASH":"sha256:output","REPRODUCTION_POINTER":"runs/RUN-1",
        "LIMITATIONS":["Proxy only."],"PROHIBITED_OVERCLAIMS":["Do not claim direct population recognition."],
    }


def base_freeze() -> dict:
    return {
        "FREEZE_ID":"FRZ-1","QUESTION_ID":"Q-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN",
        "INPUT_IDENTITY":"public corpus v1","METHOD":"deterministic computational analysis","MODEL_OR_TOOL_VERSION":"python-3",
        "PROMPT_OR_RULESET_VERSION":"rules-1","DATASET_SAMPLING":"deterministic full-corpus pass","RANDOM_SEED_POLICY":"fixed seed",
        "METRICS":["exact agreement"],"AGGREGATION":"mean","THRESHOLDS":{"minimum":0.8},"LIMITATIONS":["Proxy only."],
        "PLANNED_SENSITIVITY_ANALYSIS":"parameter sweep","METHOD_FROZEN":True,"MACHINE_EXECUTABLE":True,
        "REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,
        "REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,
    }


class ResearchMachineOnlyPolicyTest(unittest.TestCase):
    @staticmethod
    def classification_classes(text: str) -> set[str]:
        return {finding.classification for finding in classify_text(text)}

    def test_T01_T42_bounded_regression_matrix(self) -> None:
        results = machine_only_regression_results()
        self.assertEqual(set(results), {f"T{i:02d}" for i in range(1,43)})
        self.assertEqual({k:v for k,v in results.items() if v != "PASS"}, {}, msg=str(results))

    def test_clause_action_classifier_preserves_mixed_findings(self) -> None:
        classes = {f.classification for f in classify_text("Human recruitment is prohibited; nevertheless recruit 20 speakers.")}
        self.assertIn("EXPLICIT_PROHIBITION", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)
        classes = {f.classification for f in classify_text("Use a published survey, then recruit 20 respondents.")}
        self.assertIn("STATIC_EXTERNAL_SOURCE", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)
        classes = {f.classification for f in classify_text("Analyze archived interviews and interview five new speakers.")}
        self.assertIn("STATIC_EXTERNAL_SOURCE", classes); self.assertIn("ACTIVE_DEPENDENCY", classes)

    def test_owner_user_control_and_prohibition_text_are_non_fatal(self) -> None:
        cases = (
            "Ask the user again if required project authority is missing.",
            "Contact the user for the missing repository identifier.",
            "Consult Owner/K0 before accepting the project decision.",
            "Never recruit human participants.",
            "This workflow never creates authority to recruit humans.",
            "Human annotation is prohibited.",
            "Never recruit human participants and survey them.",
            "No third-party human research is allowed.",
            "The legacy workflow used human annotation before retirement.",
            "Historically, human annotation was mandatory before retirement.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(any(f.classification in FATAL_FINDINGS for f in classify_text(text)), msg=str(classify_text(text)))

    def test_live_repository_control_history_and_authority_clauses_are_non_fatal(self) -> None:
        cases = (
            "Generic reviewer, expert reviewer, participant coordinator, recruitment/survey operator, human coder/annotator/rater/validator, community solicitation liaison, or panel coordinator are invalid default Research Engine roles.",
            "Already-collected historical project-generated human data remains historical lineage and is classified accurately.",
            "Cancel or retire unexecuted project-generated human collection runs without executing them.",
            "Migration passes only when required non-owner humans, Owner manual research labor, external human review, active human collection paths, and ambiguous generic human authority gates must be zero.",
            "Retire the historical human review gate during migration remediation.",
            "Do not require human approval for every trivial change.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(any(f.classification in FATAL_FINDINGS for f in classify_text(text)), msg=str(classify_text(text)))

    def test_third_party_annotation_rating_coding_and_crowd_labor_are_fatal(self) -> None:
        cases = (
            "Hire five human annotators to label the dataset.",
            "Assign human annotators to label the dataset.",
            "Use three human raters to score the outputs.",
            "Use human raters to score the responses.",
            "Employ coders to code the interview responses.",
            "Employ human coders to code the samples.",
            "Contract crowdworkers to classify the samples.",
            "Contract crowdworkers to classify the dataset.",
            "Use crowd workers to classify samples.",
            "Use crowdworkers to classify samples.",
            "Use crowd-workers to classify samples.",
            "Hire human labelers to label the research dataset.",
            "Have panelists score the research outputs.",
            "Have external reviewers rate every generated item.",
            "The legacy pipeline requires human annotation for every new sample.",
            "In the legacy pipeline, human annotation remains mandatory.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), msg=str(classify_text(text)))

    def test_mixed_prohibition_or_history_does_not_hide_active_requirement(self) -> None:
        cases = (
            "Human annotation is prohibited; nevertheless hire human labelers to label the dataset.",
            "Historically human review was retired; the current method requires human review as research labor.",
            "The legacy workflow is inactive, but human rating remains mandatory for every new output.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), msg=str(classify_text(text)))

    def test_action_scoped_history_and_negation_adversarial_matrix(self) -> None:
        active = (
            "Already-collected historical project-generated human data remains historical lineage and human reviewers score every new output.",
            "Already-collected historical human data remains preserved, and human reviewers score every new output.",
            "Recruit 20 participants, and missing responses must be zero.",
            "Retire the old participant collection without executing it and recruit 20 new participants.",
            "Historical human review was retired but human rating remains mandatory for every new output.",
            "Human annotation is prohibited; nevertheless hire human labelers to label the new dataset.",
        )
        inactive = (
            "Already-collected historical human data remains historical lineage.",
            "Retire the historical participant collection without executing it.",
            "Never recruit human participants.",
            "Human annotation is prohibited.",
            "This workflow never creates authority to recruit humans.",
            "Use a published survey as static external evidence.",
        )
        for text in active:
            with self.subTest(active=text):
                self.assertTrue(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), classify_text(text))
        for text in inactive:
            with self.subTest(inactive=text):
                self.assertFalse(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), classify_text(text))

    def test_clause_global_negation_cannot_swallow_independent_action_family(self) -> None:
        mixed = (
            "There is no ordinary transition to participant recruitment, but recruit human participants under the alternate path.",
            "Human recruitment is prohibited, but recruit 20 participants under the exception path.",
            "Human annotation is forbidden; however hire human labelers for the new dataset.",
            "Never recruit human participants by default, but the exception requires recruiting 10 participants.",
            "There is no ordinary transition to human review, yet human reviewers score every new output on the alternate path.",
            "Retire the old participant collection without executing it, but recruit 20 new participants.",
            "Already-collected historical human data remains historical lineage, but human reviewers rate every new output.",
            "Recruit 20 participants, but participant recruitment is prohibited for future runs.",
            "Recruit 20 participants and never recruit human participants in the fallback path.",
            "Historical human review was retired, but human rating remains mandatory.",
            "Human annotation is forbidden; nevertheless hire human labelers for the new dataset.",
        )
        for text in mixed:
            with self.subTest(text=text):
                classes = {finding.classification for finding in classify_text(text)}
                self.assertIn("ACTIVE_DEPENDENCY", classes, classify_text(text))

        mixed_prohibition = mixed[:3]
        for text in mixed_prohibition:
            with self.subTest(mixed_findings=text):
                classes = {finding.classification for finding in classify_text(text)}
                self.assertIn("EXPLICIT_PROHIBITION", classes, classify_text(text))
                self.assertIn("ACTIVE_DEPENDENCY", classes, classify_text(text))

    def test_direct_shared_governor_cases(self) -> None:
        cases = (
            "There is no ordinary transition to recruit human participants and survey respondents.",
            "There is no ordinary transition to recruit human participants or survey respondents.",
            "Prohibited: recruit human participants and survey respondents.",
            "Forbidden: recruit human participants and survey respondents.",
            "Default-deny controls: recruit human participants and survey respondents.",
            "Never recruit human participants and survey respondents.",
            "Do not recruit human participants and survey respondents.",
            "Must not recruit human participants and survey respondents.",
            "Should not recruit human participants and survey respondents.",
            "Cannot recruit human participants and survey respondents.",
            "No authority to recruit human participants and survey respondents.",
            "Prohibited: recruit human participants, survey respondents, and interview speakers.",
            "Never recruit human participants, survey respondents, and interview speakers.",
            "There is no ordinary transition to recruit human participants, survey respondents, or interview speakers.",
        )
        for text in cases:
            with self.subTest(text=text):
                classes = {f.classification for f in classify_text(text)}
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertNotIn("ACTIVE_DEPENDENCY", classes)

    def test_generated_shared_governor_action_coordination_matrix(self) -> None:
        governors = ("Never ", "Do not ", "Must not ", "Should not ", "Cannot ", "Prohibited: ", "Forbidden: ", "Default-deny controls: ", "There is no ordinary transition to ", "There is no authority to ")
        actions = ("recruit human participants", "survey respondents", "interview speakers", "hire human annotators", "use human raters to score outputs", "contact external experts")
        coordinators = (" and ", " or ", ", ", ", and ", ", or ")
        for governor in governors:
            for index, action in enumerate(actions):
                other = actions[(index + 1) % len(actions)]
                for coordinator in coordinators:
                    text = governor + action + coordinator + other + "."
                    with self.subTest(text=text):
                        classes = {f.classification for f in classify_text(text)}
                        self.assertIn("EXPLICIT_PROHIBITION", classes)
                        self.assertNotIn("ACTIVE_DEPENDENCY", classes)

    def test_trailing_authority_denial_direct_mixed_cases(self) -> None:
        cases = (
            "Recruit human participants and this workflow never creates authority to recruit humans.",
            "Survey respondents and this process does not grant permission to recruit human participants.",
            "Interview speakers and the method cannot provide authority to recruit participants.",
            "Hire human annotators and this workflow can't confer permission to recruit respondents.",
            "Use human raters to score outputs and this workflow never creates authority to recruit humans.",
        )
        for text in cases:
            with self.subTest(text=text):
                decisions = _action_dispositions(_propositions(_policy_units(text)[0])[0], 0)
                classes = self.classification_classes(text)
                self.assertIn("ACTIVE_DEPENDENCY", classes)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertEqual({d.disposition for d in decisions if d.source_item_index == 0}, {"ACTIVE"})
                self.assertEqual({d.disposition for d in decisions if d.source_item_index == 1}, {"NON_ACTIVE"})

    def test_subject_led_prefix_authority_denials_remain_safe(self) -> None:
        cases = (
            "This workflow never creates authority to recruit humans.",
            "Unavailable direct measurement never creates authority to recruit humans.",
            "This process does not grant permission to survey respondents.",
            "The method cannot provide authority to interview speakers.",
            "This workflow can't confer permission to contact external experts.",
        )
        for text in cases:
            with self.subTest(text=text):
                classes = self.classification_classes(text)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertNotIn("ACTIVE_DEPENDENCY", classes)

    def test_generated_trailing_authority_denial_matrix(self) -> None:
        actions = ("recruit human participants", "survey respondents", "interview speakers", "hire human annotators", "use human raters to score outputs", "contact external experts")
        denials = (
            "this workflow never creates authority to {}",
            "this process does not grant permission to {}",
            "the method cannot provide authority to {}",
            "this workflow can't confer permission to {}",
        )
        layouts = (" and ", ", and ", "\nand ")
        for index, action_a in enumerate(actions):
            action_b = actions[(index + 1) % len(actions)]
            for denial in denials:
                for layout in layouts:
                    text = action_a + layout + denial.format(action_b) + "."
                    with self.subTest(text=text):
                        proposition = _propositions(_policy_units(text)[0])[0]
                        decisions = _action_dispositions(proposition, 0)
                        classes = self.classification_classes(text)
                        left = [d for d in decisions if d.source_item_index == 0]
                        trailing = [d for d in decisions if d.source_item_index == 1]
                        self.assertTrue(left, decisions)
                        self.assertTrue(trailing, decisions)
                        self.assertEqual({d.source_item_text for d in left}, {action_a})
                        self.assertEqual({d.disposition for d in left}, {"ACTIVE"})
                        self.assertEqual({d.disposition for d in trailing}, {"NON_ACTIVE"})
                        self.assertIn("ACTIVE_DEPENDENCY", classes)
                        self.assertIn("EXPLICIT_PROHIBITION", classes)

    def test_trailing_denial_after_multiple_actions_and_prefix_control(self) -> None:
        trailing = "Recruit human participants, survey respondents, and this workflow never creates authority to interview speakers."
        decisions = _action_dispositions(_propositions(_policy_units(trailing)[0])[0], 0)
        self.assertEqual({d.disposition for d in decisions if d.source_item_index in (0, 1)}, {"ACTIVE"})
        self.assertEqual({d.disposition for d in decisions if d.source_item_index == 2}, {"NON_ACTIVE"})
        self.assertTrue({"ACTIVE_DEPENDENCY", "EXPLICIT_PROHIBITION"}.issubset(self.classification_classes(trailing)))

        prefix = "This workflow never creates authority to recruit human participants or survey respondents."
        decisions = _action_dispositions(_propositions(_policy_units(prefix)[0])[0], 0)
        self.assertEqual({d.source_item_index for d in decisions}, {0, 1})
        self.assertEqual({d.disposition for d in decisions}, {"NON_ACTIVE"})
        self.assertNotIn("ACTIVE_DEPENDENCY", self.classification_classes(prefix))

    def test_bounded_governor_scope_required_cases_and_provenance(self) -> None:
        cases = (
            ("Never recruit human participants or survey respondents.", {0: 0, 1: 0}, set()),
            ("There is no ordinary transition to recruit human participants, survey respondents, or interview speakers.", {0: 0, 1: 0, 2: 0}, set()),
            ("This workflow never creates authority to recruit human participants or survey respondents.", {0: 0, 1: 0}, set()),
            ("Prohibited: recruit human participants and survey respondents.", {0: 0, 1: 0}, set()),
            ("Recruit human participants and this workflow never creates authority to recruit humans.", {1: 0}, {0}),
            ("This workflow never creates authority to recruit humans and under the alternate path recruit human participants.", {0: 0}, {1}),
            ("Never recruit human participants and under the alternate path survey respondents.", {0: 0}, {1}),
            ("There is no ordinary transition to recruit human participants and under the exception interview speakers.", {0: 0}, {1}),
            ("Prohibited: recruit human participants and under the alternate method interview speakers.", {0: 0}, {1}),
            ("Recruit human participants and this workflow never creates authority to survey respondents or interview speakers.", {1: 0, 2: 0}, {0}),
        )
        for text, expected_membership, active_items in cases:
            with self.subTest(text=text):
                proposition = _propositions(_policy_units(text)[0])[0]
                items, occurrences, scopes, membership = _resolve_governor_scopes(proposition)
                decisions = _action_dispositions(proposition, 0)
                self.assertEqual(membership, {(index, 0): scope for index, scope in expected_membership.items()})
                self.assertEqual({d.source_item_index for d in decisions if d.disposition == "ACTIVE"}, active_items)
                for item in items:
                    self.assertEqual(proposition[item.source_item_start:item.source_item_end], item.source_item_text)
                for occurrence in occurrences:
                    self.assertEqual(proposition[occurrence.action_start:occurrence.action_end], occurrence.action)
                for scope in scopes:
                    self.assertEqual(proposition[scope.governor_start:scope.governor_end].strip(), scope.governor_text)
                    self.assertLessEqual(scope.governor_end, scope.governed_start)
                    self.assertLess(scope.governed_start, scope.governed_end)
                for decision in decisions:
                    self.assertEqual(decision.governor_scope_id, membership.get((decision.source_item_index, decision.semantic_action_index)))
                    if decision.disposition == "NON_ACTIVE" and decision.governor is not None:
                        self.assertIsNotNone(decision.governor_scope_id)

    def test_scope_no_reentry_and_multiple_governor_non_overlap(self) -> None:
        no_reentry = "Never recruit human participants and under the alternate path survey respondents or interview speakers."
        proposition = _propositions(_policy_units(no_reentry)[0])[0]
        _, _, scopes, membership = _resolve_governor_scopes(proposition)
        self.assertEqual(membership, {(0, 0): 0})
        self.assertEqual(len(scopes), 1)
        decisions = _action_dispositions(proposition, 0)
        self.assertEqual({d.source_item_index for d in decisions if d.disposition == "ACTIVE"}, {1, 2})

        multiple = "Never recruit human participants and do not survey respondents or interview speakers."
        proposition = _propositions(_policy_units(multiple)[0])[0]
        _, _, scopes, membership = _resolve_governor_scopes(proposition)
        self.assertEqual(membership, {(0, 0): 0, (1, 0): 1, (2, 0): 1})
        self.assertEqual(len(scopes), 2)
        self.assertLessEqual(scopes[0].governed_end, scopes[1].governor_start)
        self.assertNotIn("ACTIVE_DEPENDENCY", self.classification_classes(multiple))

    def test_unsupported_continuation_prefixes_fail_active(self) -> None:
        for prefix, action in (("under the alternate path ", "recruit participants"), ("separately ", "survey respondents"), ("instead ", "interview speakers")):
            text = f"Never recruit human participants and {prefix}{action}."
            with self.subTest(text=text):
                proposition = _propositions(_policy_units(text)[0])[0]
                _, _, _, membership = _resolve_governor_scopes(proposition)
                decisions = _action_dispositions(proposition, 0)
                self.assertEqual(membership, {(0, 0): 0})
                self.assertEqual({d.disposition for d in decisions if d.source_item_index == 1}, {"ACTIVE"})
                self.assertTrue({"ACTIVE_DEPENDENCY", "EXPLICIT_PROHIBITION"}.issubset(self.classification_classes(text)))

    def test_same_item_distinct_occurrence_scope(self) -> None:
        cases = (
            ("Recruit human participants while this workflow never creates authority to recruit humans.", {0: None, 1: 0}),
            ("This workflow never creates authority to recruit humans while recruit human participants.", {0: 0, 1: None}),
        )
        for text, expected_scope in cases:
            with self.subTest(text=text):
                proposition = _propositions(_policy_units(text)[0])[0]
                items, occurrences, scopes, membership = _resolve_governor_scopes(proposition)
                decisions = _action_dispositions(proposition, 0)
                self.assertEqual(len(items), 1)
                self.assertGreaterEqual(len(occurrences), 2)
                self.assertEqual({occurrence.semantic_action_index for occurrence in occurrences}, {0, 1})
                self.assertEqual({occurrence.semantic_action_index: occurrence.governor_scope_id for occurrence in occurrences}, expected_scope)
                self.assertEqual({occurrence.semantic_action_index: membership.get((0, occurrence.semantic_action_index)) for occurrence in occurrences}, expected_scope)
                self.assertEqual({d.semantic_action_index: d.disposition for d in decisions}, {index: "NON_ACTIVE" if scope_id is not None else "ACTIVE" for index, scope_id in expected_scope.items()})
                self.assertLess(occurrences[0].action_end, occurrences[1].action_start)
                self.assertEqual(len(scopes), 1)
                self.assertTrue({"ACTIVE_DEPENDENCY", "EXPLICIT_PROHIBITION"}.issubset(self.classification_classes(text)))

    def test_non_action_gap_terminates_governor_scope(self) -> None:
        cases = (
            "Never recruit human participants and retain existing documentation or survey respondents.",
            "There is no ordinary transition to recruit human participants and preserve the existing files or interview speakers.",
            "Prohibited: recruit human participants and retain the existing dataset or survey respondents.",
        )
        for text in cases:
            with self.subTest(text=text):
                proposition = _propositions(_policy_units(text)[0])[0]
                items, occurrences, scopes, membership = _resolve_governor_scopes(proposition)
                decisions = _action_dispositions(proposition, 0)
                self.assertEqual(len(items), 3)
                self.assertFalse([occurrence for occurrence in occurrences if occurrence.source_item_index == 1])
                self.assertEqual(membership, {(0, 0): 0})
                self.assertEqual({d.disposition for d in decisions if d.source_item_index == 0}, {"NON_ACTIVE"})
                self.assertEqual({d.disposition for d in decisions if d.source_item_index == 2}, {"ACTIVE"})
                self.assertEqual(len(scopes), 1)
                self.assertTrue({"ACTIVE_DEPENDENCY", "EXPLICIT_PROHIBITION"}.issubset(self.classification_classes(text)))

    def test_governor_scope_soft_wrap_semantic_equivalence(self) -> None:
        pairs = (
            ("Never recruit human participants or survey respondents.", "Never recruit human participants\nor survey respondents."),
            ("This workflow never creates authority to recruit humans and under the alternate path recruit participants.", "This workflow never creates authority to recruit humans\nand under the alternate path recruit participants."),
            ("Recruit participants and this workflow never creates authority to survey respondents or interview speakers.", "Recruit participants\nand this workflow never creates authority to survey respondents\nor interview speakers."),
            ("Never recruit participants and do not survey respondents or interview speakers.", "Never recruit participants\nand do not survey respondents\nor interview speakers."),
        )
        for single, wrapped in pairs:
            with self.subTest(wrapped=wrapped):
                def signature(text: str) -> tuple[list[tuple[int, int | None]], list[str]]:
                    proposition = _propositions(_policy_units(text)[0])[0]
                    _, _, _, membership = _resolve_governor_scopes(proposition)
                    decisions = _action_dispositions(proposition, 0)
                    return ([(d.source_item_index, membership.get((d.source_item_index, d.semantic_action_index))) for d in decisions], sorted(self.classification_classes(text)))
                self.assertEqual(signature(single), signature(wrapped))

    def test_generated_bounded_governor_scope_matrix(self) -> None:
        actions = ("recruit human participants", "survey respondents", "interview speakers", "hire human annotators", "use human raters to score outputs", "contact external experts")
        governors = (
            lambda action: f"Never {action}",
            lambda action: f"There is no ordinary transition to {action}",
            lambda action: f"This workflow never creates authority to {action}",
            lambda action: f"Prohibited: {action}",
        )
        separators = ((" and ", "\nand "), (" or ", "\nor "), (", and ", ",\nand "))
        for governor_index, governor in enumerate(governors):
            for action_index, action_a in enumerate(actions):
                action_b = actions[(action_index + 1) % len(actions)]
                action_c = actions[(action_index + 2) % len(actions)]
                separator_pair = separators[(governor_index + action_index) % len(separators)]
                for wrapped, separator in enumerate(separator_pair):
                    forward = "\nor " if wrapped else " or "
                    shapes = (
                        (governor(action_a) + separator + action_b + ".", {0: 0, 1: 0}, set()),
                        (governor(action_a) + separator + "under an alternate path " + action_b + ".", {0: 0}, {1}),
                        (action_a + separator + governor(action_b) + ".", {1: 0}, {0}),
                        (action_a + separator + governor(action_b) + forward + action_c + ".", {1: 0, 2: 0}, {0}),
                    )
                    for text, expected_membership, active_items in shapes:
                        with self.subTest(text=text):
                            proposition = _propositions(_policy_units(text)[0])[0]
                            items, occurrences, scopes, membership = _resolve_governor_scopes(proposition)
                            decisions = _action_dispositions(proposition, 0)
                            self.assertEqual(membership, {(index, 0): scope for index, scope in expected_membership.items()})
                            self.assertEqual({d.source_item_index for d in decisions if d.disposition == "ACTIVE"}, active_items)
                            self.assertEqual({d.source_item_index for d in decisions}, set(range(len(items))))
                            self.assertTrue(scopes)
                            for occurrence_key, scope_id in membership.items():
                                item_index, semantic_action_index = occurrence_key
                                item_decisions = [d for d in decisions if d.source_item_index == item_index and d.semantic_action_index == semantic_action_index]
                                self.assertEqual({d.governor_scope_id for d in item_decisions}, {scope_id})
                            classes = self.classification_classes(text)
                            self.assertIn("EXPLICIT_PROHIBITION", classes)
                            if active_items:
                                self.assertIn("ACTIVE_DEPENDENCY", classes)
                            else:
                                self.assertNotIn("ACTIVE_DEPENDENCY", classes)

    def test_generated_soft_wrap_matrix_and_action_observability(self) -> None:
        governors = ("Never ", "Do not ", "Must not ", "Should not ", "Cannot ", "Prohibited: ", "Forbidden: ", "Default-deny controls: ", "There is no ordinary transition to ", "There is no authority to ")
        actions = ("recruit human participants", "survey respondents", "interview speakers", "hire human annotators", "use human raters to score outputs", "contact external experts")
        coordinators = ((" and ", "\nand "), (" or ", "\nor "), (", ", ",\n"), (", and ", ",\nand "), (", or ", ",\nor "))
        for action in actions:
            with self.subTest(standalone=action):
                self.assertIn("ACTIVE_DEPENDENCY", self.classification_classes(action + "."))
        for governor in governors:
            for index, action in enumerate(actions):
                other = actions[(index + 1) % len(actions)]
                for single_joiner, wrapped_joiner in coordinators:
                    single = governor + action + single_joiner + other + "."
                    wrapped = governor + action + wrapped_joiner + other + "."
                    with self.subTest(wrapped=wrapped):
                        self.assertEqual(self.classification_classes(single), self.classification_classes(wrapped))
                        self.assertIn("EXPLICIT_PROHIBITION", self.classification_classes(wrapped))
                        self.assertNotIn("ACTIVE_DEPENDENCY", self.classification_classes(wrapped))
                        units = _policy_units(wrapped)
                        propositions = [part for unit in units for part in _propositions(unit)]
                        decisions = [decision for number, proposition in enumerate(propositions) for decision in _action_dispositions(proposition, number)]
                        self.assertEqual({decision.source_item_index for decision in decisions}, {0, 1}, decisions)
                        for source_item_index in (0, 1):
                            item_decisions = [decision for decision in decisions if decision.source_item_index == source_item_index]
                            self.assertTrue(item_decisions, decisions)
                            self.assertEqual(len({decision.source_item_text for decision in item_decisions}), 1, item_decisions)
                            self.assertTrue(all(decision.disposition == "NON_ACTIVE" for decision in item_decisions), item_decisions)
                        self.assertTrue(all(decision.disposition == "NON_ACTIVE" for decision in decisions), decisions)

    def test_source_action_identity_for_governed_ungoverned_and_wrapped_pairs(self) -> None:
        cases = (
            ("Prohibited: recruit human participants and survey respondents.", "NON_ACTIVE"),
            ("recruit human participants and survey respondents.", "ACTIVE"),
            ("Prohibited: recruit human participants\nand survey respondents.", "NON_ACTIVE"),
            ("Prohibited: use human raters to score outputs\nand contact external experts.", "NON_ACTIVE"),
        )
        for text, disposition in cases:
            units = _policy_units(text)
            propositions = [part for unit in units for part in _propositions(unit)]
            decisions = [decision for number, proposition in enumerate(propositions) for decision in _action_dispositions(proposition, number)]
            with self.subTest(text=text):
                self.assertEqual({decision.source_item_index for decision in decisions}, {0, 1}, decisions)
                for source_item_index in (0, 1):
                    item_decisions = [decision for decision in decisions if decision.source_item_index == source_item_index]
                    self.assertTrue(item_decisions, decisions)
                    self.assertEqual({decision.disposition for decision in item_decisions}, {disposition})
                    self.assertEqual(len({decision.source_item_text for decision in item_decisions}), 1)

    def test_overlapping_matches_preserve_source_action_identity(self) -> None:
        text = "Prohibited: use human raters to score outputs and contact external experts."
        proposition = _propositions(_policy_units(text)[0])[0]
        decisions = _action_dispositions(proposition, 0)
        first = [decision for decision in decisions if decision.source_item_index == 0]
        second = [decision for decision in decisions if decision.source_item_index == 1]
        self.assertGreater(len(first), 1, decisions)
        self.assertTrue(second, decisions)
        self.assertEqual({decision.source_item_index for decision in first}, {0})
        self.assertEqual({decision.source_item_text for decision in first}, {"Prohibited: use human raters to score outputs"})
        self.assertEqual({(decision.source_item_start, decision.source_item_end) for decision in first}, {(0, len("Prohibited: use human raters to score outputs"))})
        self.assertEqual({decision.semantic_action_index for decision in first}, {0})
        self.assertEqual(len({(decision.semantic_action_start, decision.semantic_action_end) for decision in first}), 1)
        self.assertEqual({decision.governor_scope_id for decision in first}, {0})
        self.assertEqual({decision.source_item_index for decision in second}, {1})
        self.assertEqual({decision.source_item_text for decision in second}, {"contact external experts."})
        self.assertTrue(all(decision.disposition == "NON_ACTIVE" for decision in decisions))

        cases = (
            ("use human raters to score outputs and Never recruit participants.", 0, None, "ACTIVE"),
            ("Never recruit participants or use human raters to score outputs.", 1, 0, "NON_ACTIVE"),
        )
        for text, item_index, scope_id, disposition in cases:
            with self.subTest(text=text):
                proposition = _propositions(_policy_units(text)[0])[0]
                item_decisions = [d for d in _action_dispositions(proposition, 0) if d.source_item_index == item_index]
                self.assertGreater(len(item_decisions), 1)
                self.assertEqual(len({d.semantic_action_index for d in item_decisions}), 1)
                self.assertEqual(len({(d.source_item_start, d.source_item_end) for d in item_decisions}), 1)
                self.assertEqual({d.governor_scope_id for d in item_decisions}, {scope_id})
                self.assertEqual({d.disposition for d in item_decisions}, {disposition})

    def test_generated_bidirectional_contrast_matrix(self) -> None:
        markers = ("but", "however", "yet", "nevertheless", "nonetheless")
        pairs = (("recruit human participants", "survey respondents"), ("hire human annotators", "contact external experts"), ("interview speakers", "use human raters to score outputs"))
        for marker in markers:
            for first, second in pairs:
                for text in (f"Prohibited: {first}, {marker} {second}.", f"{first}, {marker} never {second}."):
                    with self.subTest(text=text):
                        self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text(text)})

    def test_generated_contrast_wrap_matrix(self) -> None:
        markers = ("but", "however", "yet", "nevertheless", "nonetheless")
        pairs = (("recruit human participants", "survey respondents"), ("hire human annotators", "contact external experts"), ("interview speakers", "use human raters to score outputs"))
        for marker in markers:
            for first, second in pairs:
                layouts = (
                    (f"Prohibited: {first}, {marker} {second}.", f"Prohibited: {first},\n{marker} {second}."),
                    (f"{first}, {marker} never {second}.", f"{first},\n{marker} never {second}."),
                )
                for single, wrapped in layouts:
                    with self.subTest(wrapped=wrapped):
                        self.assertEqual(self.classification_classes(single), self.classification_classes(wrapped))
                        self.assertIn("ACTIVE_DEPENDENCY", self.classification_classes(wrapped))

    def test_direct_active_and_mixed_cases(self) -> None:
        cases = (
            "There is no ordinary transition to participant recruitment, but recruit human participants under the alternate path.",
            "Prohibited: recruit human participants, but recruit respondents under the exception path.",
            "Never recruit human participants by default, but recruit 20 participants under the alternate path.",
            "Human annotation is forbidden; however hire human labelers for the new dataset.",
            "There is no ordinary transition to human review, yet human reviewers score every new output on the alternate path.",
            "Already-collected historical project-generated human data remains historical lineage and human reviewers score every new output.",
            "Already-collected historical human data remains preserved, and human reviewers score every new output.",
            "Retire the old participant collection without executing it and recruit 20 new participants.",
            "Recruit 20 participants and never recruit human participants in the fallback path.",
            "Use a published survey and recruit 20 new respondents.",
            "Analyze archived interviews and interview five new speakers.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text(text)})
        for text in cases[:5]:
            with self.subTest(coexisting=text):
                self.assertIn("EXPLICIT_PROHIBITION", {f.classification for f in classify_text(text)})

    def test_direct_multiline_safe_and_active_layout_invariance(self) -> None:
        safe = (
            "There is no ordinary transition to recruit human participants\nand survey respondents.",
            "There is no ordinary transition to\nrecruit human participants and survey respondents.",
            "There is no ordinary transition to recruit\nhuman participants and survey respondents.",
            "There is no ordinary transition to recruit human participants\nor survey respondents.",
            "Prohibited: recruit human participants\nand survey respondents.",
            "Forbidden: recruit human participants\nand survey respondents.",
            "Default-deny controls: recruit human participants\nand survey respondents.",
            "Never recruit human participants\nand survey respondents.",
            "Do not recruit human participants\nand survey respondents.",
            "Must not recruit human participants\nand survey respondents.",
            "Cannot recruit human participants\nand survey respondents.",
            "There is no authority to recruit human participants\nand survey respondents.",
            "Prohibited: recruit human participants,\nsurvey respondents,\nand interview speakers.",
            "There is no ordinary transition to recruit human participants,\nsurvey respondents,\nor interview speakers.",
        )
        active = (
            "There is no ordinary transition to participant recruitment,\nbut recruit human participants under the alternate path.",
            "Prohibited: recruit human participants,\nbut recruit respondents under the exception path.",
            "Never recruit human participants by default,\nbut recruit 20 participants under the alternate path.",
            "Already-collected historical project-generated human data\nremains historical lineage and human reviewers score every new output.",
            "Already-collected historical human data remains preserved,\nand human reviewers score every new output.",
            "Retire the old participant collection without executing it\nand recruit 20 new participants.",
            "Recruit 20 participants\nand never recruit human participants in the fallback path.",
            "Use a published survey\nand recruit 20 new respondents.",
            "Analyze archived interviews\nand interview five new speakers.",
        )
        for text in safe:
            with self.subTest(safe=text):
                classes = self.classification_classes(text)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertNotIn("ACTIVE_DEPENDENCY", classes)
                self.assertEqual(classes, self.classification_classes(text.replace("\n", " ")))
        for text in active:
            with self.subTest(active=text):
                classes = self.classification_classes(text)
                self.assertIn("ACTIVE_DEPENDENCY", classes)
                self.assertEqual(classes, self.classification_classes(text.replace("\n", " ")))

    def test_paragraph_and_markdown_structural_boundaries(self) -> None:
        paragraphs = (
            "Prohibited: recruit human participants.\n\nRecruit external experts under the alternate method.",
            "There is no ordinary transition to recruit human participants\nand survey respondents.\n\nRecruit external experts under the alternate method.",
            "Never recruit human participants.\n\nSurvey respondents for the new study.",
        )
        for text in paragraphs:
            with self.subTest(paragraph=text):
                classes = self.classification_classes(text)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertIn("ACTIVE_DEPENDENCY", classes)
        governed = "Prohibited:\n\n- recruit human participants\n  and survey respondents\n- interview speakers"
        governed_action = "Prohibited:\n\n- use human raters\n  to score outputs\n- contact external experts"
        for text in (governed, governed_action):
            with self.subTest(governed=text):
                classes = self.classification_classes(text)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertNotIn("ACTIVE_DEPENDENCY", classes)
        self.assertIn("ACTIVE_DEPENDENCY", self.classification_classes("- recruit human participants\n  and survey respondents"))
        stopped = "Prohibited:\n\n- recruit human participants\n- survey respondents\n\nRecruit external experts under the exception path."
        self.assertIn("ACTIVE_DEPENDENCY", self.classification_classes(stopped))

    def test_atx_headings_are_structural_policy_boundaries(self) -> None:
        safe = (
            "# Research transition policy\nThere is no ordinary transition to recruit human participants\nand survey respondents.",
            "### Policy\nThere is no ordinary transition to\nrecruit human participants\nand survey respondents.",
            "###### Policy\nProhibited: recruit human participants\nand survey respondents.",
            "# Research policy\nProhibited:\n\n- recruit human participants\n- survey respondents",
            "   ## Research policy\nProhibited:\n\n- recruit human participants\n- survey respondents",
        )
        for text in safe:
            with self.subTest(safe=text):
                classes = self.classification_classes(text)
                self.assertIn("EXPLICIT_PROHIBITION", classes)
                self.assertNotIn("ACTIVE_DEPENDENCY", classes)
        active = "## Policy\nRecruit human participants\nand survey respondents."
        self.assertIn("ACTIVE_DEPENDENCY", self.classification_classes(active))
        terminated = "There is no ordinary transition to recruit human participants.\n## Alternate method\nRecruit external experts for the new study."
        classes = self.classification_classes(terminated)
        self.assertIn("EXPLICIT_PROHIBITION", classes)
        self.assertIn("ACTIVE_DEPENDENCY", classes)
        self.assertEqual(_policy_units("# Heading with recruit participants\nMachine-only prose."), ["Machine-only prose."])

    def test_atx_heading_grammar_is_bounded(self) -> None:
        self.assertEqual(_policy_units("# Heading\ntext"), ["text"])
        self.assertEqual(_policy_units("   ###### Heading\ntext"), ["text"])
        self.assertEqual(_policy_units("#not-a-heading\ntext"), ["#not-a-heading text"])
        self.assertEqual(_policy_units("foo # bar\ntext"), ["foo # bar text"])
        self.assertEqual(_policy_units("    # four-leading-spaces-is-not-an-ATX-heading\ntext"), ["# four-leading-spaces-is-not-an-ATX-heading text"])
        self.assertEqual(_policy_units("####### not-a-heading\ntext"), ["####### not-a-heading text"])

    def test_metamorphic_scope_invariants(self) -> None:
        actions = ("recruit human participants", "survey respondents", "interview speakers")
        for joiner in (" and ", " or ", ", ", ", and ", ", or "):
            governed = "Prohibited: " + joiner.join(actions) + "."
            self.assertNotIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text(governed)})  # M1
            self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text(joiner.join(actions) + ".")})  # M2/M6
        self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text("Prohibited: recruit human participants, but survey respondents.")})  # M3
        self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text("Published survey evidence is historical, and recruit human participants.")})  # M4
        self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text("Recruit human participants, but never survey respondents.")})  # M5
        layouts = (
            ("Prohibited: recruit human participants and survey respondents.", "Prohibited: recruit human participants\nand survey respondents."),
            ("Recruit human participants and survey respondents.", "Recruit human participants\nand survey respondents."),
            ("Prohibited: recruit human participants, but survey respondents.", "Prohibited: recruit human participants,\nbut survey respondents."),
            ("Historical human data is preserved, and recruit human participants.", "Historical human data is preserved,\nand recruit human participants."),
            ("Use a published survey and recruit human participants.", "Use a published survey\nand recruit human participants."),
        )
        for single, wrapped in layouts:
            self.assertEqual(self.classification_classes(single), self.classification_classes(wrapped))  # M7

    def test_markdown_governed_list_scope(self) -> None:
        governed = "Prohibited:\n\n- recruit human participants\n- survey respondents\n- interview speakers"
        classes = {f.classification for f in classify_text(governed)}
        self.assertIn("EXPLICIT_PROHIBITION", classes)
        self.assertNotIn("ACTIVE_DEPENDENCY", classes)
        mixed = "Prohibited:\n\n- recruit human participants\n- survey respondents\n\nHowever, recruit external experts under the exception path."
        self.assertIn("ACTIVE_DEPENDENCY", {f.classification for f in classify_text(mixed)})

    def test_pure_and_genuinely_list_wide_prohibitions_remain_non_active(self) -> None:
        cases = (
            "Human review is prohibited and human reviewers must not score outputs.",
            "Never recruit human participants.",
            "Retire the historical participant collection without executing it.",
            "Already-collected historical human data remains historical lineage.",
            "Human annotation is prohibited.",
            "Generic reviewer, expert reviewer, participant coordinator, recruitment/survey operator, human coder/annotator/rater/validator, community solicitation liaison, or panel coordinator are invalid default Research Engine roles.",
            "Migration passes only when required non-owner humans, Owner manual research labor, external human review, active human collection paths, and ambiguous generic human authority gates must be zero.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(any(f.classification == "ACTIVE_DEPENDENCY" for f in classify_text(text)), classify_text(text))

    def test_question_recursively_checks_semantic_fields(self) -> None:
        q = base_question(); q["AVAILABLE_MACHINE_METHODS"] = ["deterministic pass", ["Recruit native speakers"]]
        self.assertTrue(validate_question(q))
        q = base_question(); q["AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE"] = ["Published survey; then recruit new respondents."]
        self.assertTrue(validate_question(q))

    def test_default_objects_reject_undeclared_payloads(self) -> None:
        wp = base_wp(); wp["PARTICIPANT_PLAN"] = "Recruit 50 speakers."; self.assertTrue(validate_work_package(wp))
        wp = base_wp(); wp["METADATA"] = {"execution":{"reviewers":"external experts"}}; self.assertTrue(validate_work_package(wp))

    def test_authorization_requires_governed_owner_resolver(self) -> None:
        auth, record = owner_auth_pair()
        self.assertTrue(validate_human_research_authorization(auth))
        self.assertEqual(validate_human_research_authorization(auth, resolver_for(record)), [])
        fake = copy.deepcopy(auth); fake["OWNER_DECISION_RECORD_REF"] = "ODR-NOT-FOUND"
        self.assertTrue(validate_human_research_authorization(fake, resolver_for(record)))
        for field,value in (("project_id","P-OTHER"),("authorized_question_id","Q-OTHER"),("authorized_scope","broader scope"),("authorized_namespace","human-research/P-1/OTHER")):
            bad = copy.deepcopy(record); bad[field] = value
            self.assertTrue(validate_human_research_authorization(auth, resolver_for(bad)), msg=field)

    def test_genuine_owner_authorization_passes_only_separate_namespace(self) -> None:
        auth, record = owner_auth_pair(); resolver = resolver_for(record)
        human_wp = {"PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","NAMESPACE":"human-research/P-1/Q-H1"}
        self.assertEqual(validate_separate_human_work_package(human_wp, auth, resolver), [])
        default = base_wp(); default["NAMESPACE"] = human_wp["NAMESPACE"]
        self.assertTrue(validate_work_package(default))

    def test_source_provenance_fails_closed(self) -> None:
        source = {"SOURCE_ID":"SRC-1","PROVENANCE_CLASS":"EXTERNAL_PREEXISTING_HUMAN_DATA","ORIGIN":"EXTERNAL_PREEXISTING","HUMAN_ORIGIN":True,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Published survey dataset."}
        self.assertTrue(validate_source(source))
        source = {"SOURCE_ID":"SRC-2","PROVENANCE_CLASS":"OTHER","ORIGIN":"PROJECT_MACHINE_GENERATED","HUMAN_ORIGIN":False,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Recruit participants and collect new human responses."}
        self.assertTrue(validate_source(source))

    def test_experiment_semantics_ignore_keys_but_not_values(self) -> None:
        e = base_experiment(); e["INPUT_DATASET"] = "Recruit 20 participants and collect responses."; self.assertTrue(validate_experiment(e))
        e = base_experiment(); e["INPUT_DATASET"] = {"metadata":{"collection_plan":{"participants":"Recruit 20 participants."}}}; self.assertTrue(validate_experiment(e))
        e = base_experiment(); e["INPUT_DATASET"] = "Archived public interview corpus."; self.assertEqual(validate_experiment(e), [])

    def test_method_freeze_requires_machine_only_semantics(self) -> None:
        f = base_freeze(); f["METHOD"] = "Recruit 50 speakers and survey them."; self.assertTrue(validate_method_freeze(f))
        f = base_freeze(); f["INPUT_IDENTITY"] = {"metadata":{"collection_plan":"Recruit 20 participants."}}; self.assertTrue(validate_method_freeze(f))
        self.assertEqual(validate_method_freeze(base_freeze()), [])


if __name__ == "__main__": unittest.main()
