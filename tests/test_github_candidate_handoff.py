from __future__ import annotations

import unittest

from tests.test_resolver_transition import artifact, transition_bundle
from tests.test_resolver_spawn import bundle as spawn_bundle
from tools.resolver_spawn import resolve_spawn
from tools.github_candidate_handoff import check_github_candidate, validate_delivery_requirement
from tools.resolver_transition import resolve_transition

REPO = "example-org/example"
SHA = "a" * 40
TASK = "ASSIGN-RESOLVED"
REQ = {"repository": REPO, "base_branch": "main", "allowed_kinds": ["PULL_REQUEST", "BRANCH"]}


def valid_pr() -> dict:
    return {
        "number": 17, "state": "open", "merged": False, "draft": False,
        "head": {"sha": SHA, "repo": {"full_name": REPO}},
        "base": {"ref": "main", "repo": {"full_name": REPO}},
        "body": "Implementation details\nResolver-Assignment: ASSIGN-RESOLVED\n",
    }


def enabled_bundle(kind="PULL_REQUEST", reference=17):
    bundle = transition_bundle(software=True, branch_capability=(kind == "BRANCH"))
    result = artifact(bundle, "RESULT-1")
    result["published_candidate"] = {
        "kind": kind, "repository": REPO, "ref": reference, "head_sha": SHA,
    }
    return bundle


class GitHubCandidateHandoffTest(unittest.TestCase):
    def test_valid_pr_readback_advances_control(self) -> None:
        bundle = enabled_bundle()
        reader = lambda kind, repo, ref: valid_pr()
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=reader)["control_state"], "COMPLETE")

    def test_executor_self_report_without_independent_readback_waits(self) -> None:
        bundle = enabled_bundle()
        result = resolve_transition(bundle)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "GITHUB_CANDIDATE_READBACK_NOT_PROVEN"))

    def test_no_candidate_ref_waits(self) -> None:
        for executor_status in ("COMPLETE", "PARTIAL", "BLOCKED"):
            with self.subTest(executor_status=executor_status):
                bundle = enabled_bundle()
                executor = artifact(bundle, "RESULT-1")
                executor.pop("published_candidate")
                executor["status"] = executor_status
                result = resolve_transition(bundle, github_candidate_reader=lambda *args: valid_pr())
                self.assertEqual(
                    (result["control_state"], result["reason"], result["candidate_reason"]),
                    ("WAIT", "SOFTWARE_GITHUB_PUBLICATION_PENDING", "GITHUB_CANDIDATE_NOT_PUBLISHED"),
                )

    def test_draft_is_verifiable_but_merged_or_closed_requires_reconciliation(self) -> None:
        for field, value, status in (("merged", True, "NOT_PROVEN"), ("draft", True, "PROVEN"),
                                     ("state", "closed", "NOT_PROVEN")):
            with self.subTest(field=field):
                pr = valid_pr()
                pr[field] = value
                bundle = enabled_bundle()
                verdict = check_github_candidate(artifact(bundle, TASK),
                    artifact(bundle, "RESULT-1"), lambda *args: pr)
                self.assertEqual(verdict["status"], status)

    def test_merged_pr_waits_for_control_promotion_reconciliation(self) -> None:
        bundle = enabled_bundle()
        pr = valid_pr()
        pr["merged"] = True
        transition = resolve_transition(bundle, github_candidate_reader=lambda *args: pr)
        self.assertEqual((transition["control_state"], transition["reason"]),
                         ("WAIT", "GITHUB_CANDIDATE_READBACK_NOT_PROVEN"))
        self.assertEqual(transition["candidate_reason"],
                         "GITHUB_PR_MERGED_REQUIRES_PROMOTION_RECONCILIATION")

    def test_malformed_kind_list_fails_closed_without_exception(self) -> None:
        invalid = dict(REQ, allowed_kinds=[{"unexpected": "object"}])
        self.assertTrue(validate_delivery_requirement(invalid))

    def test_mismatched_head_and_base_and_assignment_marker_fail(self) -> None:
        for path, new in (("sha", "b" * 40), ("base", "other"), ("body", "Different task")):
            with self.subTest(path=path):
                pr = valid_pr()
                if path == "sha": pr["head"]["sha"] = new
                if path == "base": pr["base"]["ref"] = new
                if path == "body": pr["body"] = new
                bundle = enabled_bundle()
                verdict = check_github_candidate(artifact(bundle, TASK), artifact(bundle, "RESULT-1"), lambda *args: pr)
                self.assertEqual(verdict["status"], "NOT_PROVEN")

    def test_cross_repo_candidate_rejected(self) -> None:
        bundle = enabled_bundle()
        artifact(bundle, "RESULT-1")["published_candidate"]["repository"] = "example-org/other"
        result = resolve_transition(bundle, github_candidate_reader=lambda *args: valid_pr())
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", "GITHUB_CANDIDATE_READBACK_INVALID"))

    def test_branch_mode_requires_exact_assignment_namespace_and_sha(self) -> None:
        branch = f"resolver/{TASK}/implementation"
        bundle = enabled_bundle("BRANCH", branch)
        reader = lambda kind, repo, ref: {"name": branch, "commit": {"sha": SHA}}
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=reader)["control_state"], "COMPLETE")
        artifact(bundle, "RESULT-1")["published_candidate"]["ref"] = "feature/unrelated"
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=reader)["control_state"], "ESCALATE")

    def test_branch_absence_and_read_failure_cannot_pass(self) -> None:
        bundle = enabled_bundle("BRANCH", f"resolver/{TASK}/implementation")
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=lambda *args: None)["control_state"], "WAIT")
        def failed(*args): raise RuntimeError("network unavailable")
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=failed)["control_state"], "WAIT")

    def test_non_code_report_needs_no_code_candidate(self) -> None:
        bundle = transition_bundle()
        assignment = artifact(bundle, TASK)
        self.assertNotIn("github_candidate_delivery", assignment)
        self.assertNotIn("published_candidate", artifact(bundle, "RESULT-1"))
        self.assertEqual(resolve_transition(bundle)["control_state"], "COMPLETE")

    def test_pr_readback_uses_the_reported_target(self) -> None:
        bundle = enabled_bundle()
        def reader(kind, repository, reference):
            self.assertEqual((kind, repository, reference), ("PULL_REQUEST", REPO, 17))
            return valid_pr()
        self.assertEqual(resolve_transition(bundle, github_candidate_reader=reader)["control_state"], "COMPLETE")

    def test_wrong_or_missing_remote_pr_head_waits(self) -> None:
        for head in ({"repo": {"full_name": REPO}},
                     {"sha": "b" * 40, "repo": {"full_name": REPO}}):
            with self.subTest(head=head):
                pr = valid_pr()
                pr["head"] = head
                result = resolve_transition(enabled_bundle(), github_candidate_reader=lambda *args: pr)
                self.assertEqual((result["control_state"], result["reason"]),
                                 ("WAIT", "GITHUB_CANDIDATE_READBACK_NOT_PROVEN"))

    def test_unadmitted_branch_cannot_replace_proven_pr_route(self) -> None:
        bundle = enabled_bundle()
        assignment = artifact(bundle, TASK)
        assignment["github_candidate_delivery"]["allowed_kinds"].append("BRANCH")
        artifact(bundle, "RESULT-1")["published_candidate"]["kind"] = "BRANCH"
        artifact(bundle, "RESULT-1")["published_candidate"]["ref"] = f"resolver/{TASK}/implementation"
        result = resolve_transition(bundle, github_candidate_reader=lambda *args: {"name": f"resolver/{TASK}/implementation", "commit": {"sha": SHA}})
        self.assertEqual(result["reason"], "GITHUB_CANDIDATE_PUBLISH_ROUTE_NOT_ADMITTED")

    def test_invalid_requirement_fails_closed(self) -> None:
        self.assertTrue(validate_delivery_requirement({"repository": REPO}))
        bundle = enabled_bundle()
        artifact(bundle, TASK)["github_candidate_delivery"]["allowed_kinds"] = []
        self.assertEqual(resolve_transition(bundle)["control_state"], "ESCALATE")

    def test_code_change_without_proven_github_publish_route_is_not_assigned(self) -> None:
        request = spawn_bundle()
        delivery = request["artifacts"][3]["segments"][0]
        delivery["required_capabilities"].remove("pull_request_create")
        blocked = resolve_spawn(request)
        self.assertEqual((blocked["control_state"], blocked["reason"]),
                         ("WAIT", "SOFTWARE_GITHUB_PUBLISH_CAPABILITY_REQUIRED"))
        self.assertNotIn("assignment", blocked)

    def test_one_proven_publication_alternative_is_sufficient(self) -> None:
        request = spawn_bundle()
        request["assignment_draft_semantics"]["github_candidate_delivery"]["allowed_kinds"] = [
            "PULL_REQUEST", "BRANCH"
        ]
        ready = resolve_spawn(request)
        self.assertEqual(ready["status"], "SPAWN_READY")
        self.assertEqual(ready["assignment"]["github_candidate_delivery"]["allowed_kinds"],
                         ["PULL_REQUEST", "BRANCH"])

    def test_missing_actual_publisher_capability_fails_route_validation(self) -> None:
        request = spawn_bundle()
        profile = request["artifacts"][2]
        profile["available_capabilities"].remove("pull_request_create")
        profile["capability_evidence"] = [entry for entry in profile["capability_evidence"]
                                           if entry["capability"] != "pull_request_create"]
        profile["evidence_artifacts"][0]["capabilities"].remove("pull_request_create")
        blocked = resolve_spawn(request)
        self.assertNotEqual(blocked.get("status"), "SPAWN_READY")
        self.assertNotIn("assignment", blocked)

    def test_code_change_assignment_without_publication_contract_is_rejected(self) -> None:
        request = spawn_bundle()
        request["assignment_draft_semantics"].pop("github_candidate_delivery")
        rejected = resolve_spawn(request)
        self.assertEqual(rejected["reason"], "SOFTWARE_GITHUB_CANDIDATE_DELIVERY_REQUIRED")
        self.assertNotIn("assignment", rejected)

    def test_malformed_delivery_assignment_is_rejected_before_executor(self) -> None:
        request = spawn_bundle()
        request["assignment_draft_semantics"]["github_candidate_delivery"]["allowed_kinds"] = []
        rejected = resolve_spawn(request)
        self.assertEqual(rejected["reason"], "SOFTWARE_GITHUB_CANDIDATE_DELIVERY_INVALID")

    def test_legacy_non_code_result_does_not_need_git_candidate(self) -> None:
        self.assertEqual(resolve_transition(transition_bundle())["control_state"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
