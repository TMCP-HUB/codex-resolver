"""PR target-alignment negative controls for Issue #61."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_resolver_transition import transition_bundle, artifact
from tools.executability import validate_director_decision
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def reviewed_bundle(tier="V3", *, software=False):
    value = transition_bundle(software=software)
    director = artifact(value, "DIRECTOR-POST")
    authority = director["transition_authority"]
    gate = {
        "tier": tier,
        "issue_ref": "github:example-org/example/issues/42",
        "outcome_claim_id": "business-outcome",
        "delivery_scope": "STAGED" if tier == "V3" else "FULL",
    }
    if tier in {"V3", "V4"}:
        gate.update({
            "target_ref": "canon:approved-target-v2",
            "architecture_claim_id": "architecture-alignment",
            "progress_claim_id": "progress-to-target",
        })
    if tier == "V4":
        gate.update({
            "transition_claim_id": "migration-safety",
            "transition_mode": "DESTRUCTIVE_CUTOVER",
            "owner_decision_ref": "owner:authorized-cutover",
        })
    authority["review_gate"] = gate
    executor = artifact(value, "RESULT-1")
    verifier = artifact(value, "VERIFY-1")
    verifier["verified_state_identity"] = artifact(value, "STATE-RESULT")["state_identity"]
    if tier == "V4":
        value["artifacts"].append({"artifact_type": "OWNER_DECISION_RECORD", "artifact_id": gate["owner_decision_ref"],
                                   "produced_by_role": "owner-interface", "status": "RECORDED",
                                   "selected_option": "Approve the specified cutover"})
    claim_ids = [gate["outcome_claim_id"]]
    if tier in {"V3", "V4"}:
        claim_ids += [gate["architecture_claim_id"], gate["progress_claim_id"]]
    if tier == "V4":
        claim_ids.append(gate["transition_claim_id"])
    for claim_id in claim_ids:
        executor["claims"].append({"claim_id": claim_id, "claim": f"Confirmed {claim_id}.",
                                   "evidence_refs": ["EVIDENCE-RESULT"]})
        verifier["claim_verdicts"].append({"claim_id": claim_id, "verdict": "CONFIRMED",
                                           "evidence_refs": ["EVIDENCE-RESULT"] +
                                           ([gate["owner_decision_ref"]] if claim_id == gate.get("transition_claim_id") else [])})
        if claim_id == gate.get("transition_claim_id"):
            verifier["claim_verdicts"][-1]["note"] = "The referenced Owner decision authorizes this scoped cutover."
        authority["verification_target_claim_ids"].append(claim_id)
        authority["acceptance_requirements"].append({
            "requirement_id": "acceptance-" + claim_id,
            "claim_id": claim_id,
            "required_evidence_refs": ["EVIDENCE-RESULT"],
        })
    return value


def director_reviewed_bundle(tier="V3", *, software=False):
    value = reviewed_bundle(tier, software=software)
    director = artifact(value, "DIRECTOR-POST")
    authority = director["transition_authority"]
    original = artifact(value, "VERIFY-1")
    director["verification_result_ref"] = None
    value["refs"]["verification_result_ref"] = None
    authority["verification_required"] = False
    authority["verification_target_claim_ids"] = []
    authority["allowed_verification_outcomes"] = []
    authority["verification_outcome_map"] = {}
    gate_claims = {authority["review_gate"][field] for field in
                   ("outcome_claim_id", "architecture_claim_id", "progress_claim_id", "transition_claim_id")
                   if field in authority["review_gate"]}
    director["director_review"] = {
        "review_type": "DIRECTOR_REVIEW", "assignment_id": director["assignment_id"],
        "executor_result_ref": director["executor_result_ref"], "input_state_ref": director["input_state_ref"],
        "verified_state_identity": artifact(value, "STATE-RESULT")["state_identity"], "status": "CONFIRMED",
        "claim_verdicts": deepcopy([item for item in original["claim_verdicts"] if item["claim_id"] in gate_claims]),
    }
    return value


class TargetAlignmentReviewTest(unittest.TestCase):
    def assert_reason(self, value, reason):
        actual = resolve_transition(value)
        self.assertEqual(actual["reason"], reason, actual)
        self.assertNotEqual(actual["control_state"], "COMPLETE", actual)

    def test_unaffected_technical_v1_does_not_invent_architecture_gate(self):
        self.assertEqual(resolve_transition(transition_bundle())["control_state"], "COMPLETE")

    def test_business_v2_requires_outcome_claim(self):
        value = reviewed_bundle("V2")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["verification_target_claim_ids"].remove("business-outcome")
        self.assert_reason(value, "TARGET_ALIGNMENT_CONTRACT_MISSING")

    def test_architecture_v3_all_required_claims_prove_stage_only(self):
        value = reviewed_bundle()
        self.assertEqual(validate_director_decision(artifact(value, "DIRECTOR-POST")), [])
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["delivery_scope"]), ("COMPLETE", "STAGED"))

    def test_ci_green_cannot_replace_architecture_claim(self):
        value = reviewed_bundle()
        verifier = artifact(value, "VERIFY-1")
        next(v for v in verifier["claim_verdicts"] if v["claim_id"] == "architecture-alignment")["verdict"] = "NOT_PROVEN"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_progress_to_target_must_be_proven(self):
        value = reviewed_bundle()
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "progress-to-target")["verdict"] = "QUALIFIED"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_claim_must_be_in_director_acceptance_not_just_tests(self):
        value = reviewed_bundle()
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["acceptance_requirements"] = [
            r for r in authority["acceptance_requirements"] if r["claim_id"] != "progress-to-target"
        ]
        self.assert_reason(value, "TARGET_ALIGNMENT_CONTRACT_MISSING")

    def test_target_evidence_missing_is_not_pass(self):
        value = reviewed_bundle()
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "architecture-alignment")["evidence_refs"] = []
        self.assert_reason(value, "TARGET_ALIGNMENT_EVIDENCE_MISSING")

    def test_review_gate_accepts_verifier_owned_claim_for_exact_state(self):
        value = reviewed_bundle("V2")
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        requirement = next(r for r in authority["acceptance_requirements"] if r["claim_id"] == "business-outcome")
        requirement.update(evidence_source="VERIFIER", required_evidence_refs=["VERIFIER-OBSERVATION"])
        executor = artifact(value, "RESULT-1")
        executor["claims"] = [c for c in executor["claims"] if c["claim_id"] != "business-outcome"]
        verifier = artifact(value, "VERIFY-1")
        verifier["verified_state_identity"] = artifact(value, "STATE-RESULT")["state_identity"]
        next(v for v in verifier["claim_verdicts"] if v["claim_id"] == "business-outcome")["evidence_refs"] = ["VERIFIER-OBSERVATION"]
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_target_ref_absent_fails_closed(self):
        value = reviewed_bundle()
        del artifact(value, "DIRECTOR-POST")["transition_authority"]["review_gate"]["target_ref"]
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")

    def test_review_gate_cannot_turn_off_independent_verification(self):
        value = reviewed_bundle("V2")
        artifact(value, "DIRECTOR-POST")["transition_authority"]["verification_required"] = False
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")

    def test_v4_destructive_requires_owner_authority_and_transition_evidence(self):
        value = reviewed_bundle("V4")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        gate = artifact(value, "DIRECTOR-POST")["transition_authority"]["review_gate"]
        del gate["owner_decision_ref"]
        self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")
        gate["owner_decision_ref"] = "owner:authorized-cutover"
        next(v for v in artifact(value, "VERIFY-1")["claim_verdicts"]
             if v["claim_id"] == "migration-safety")["verdict"] = "NOT_PROVEN"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_director_can_review_v2_v3_and_v4_without_a_verifier(self):
        for tier in ("V2", "V3", "V4"):
            with self.subTest(tier=tier):
                value = director_reviewed_bundle(tier)
                result = resolve_transition(value)
                self.assertEqual(result["control_state"], "COMPLETE", result)

    def test_director_review_is_bound_to_exact_result_and_state(self):
        value = director_reviewed_bundle()
        review = artifact(value, "DIRECTOR-POST")["director_review"]
        review["verified_state_identity"] = "git:old-result"
        self.assert_reason(value, "DIRECTOR_REVIEW_CANDIDATE_NOT_PROVEN")
        review["verified_state_identity"] = artifact(value, "STATE-RESULT")["state_identity"]
        review["executor_result_ref"] = "RESULT-OTHER"
        self.assert_reason(value, "DIRECTOR_REVIEW_CANDIDATE_NOT_PROVEN")

    def test_director_review_uses_exact_independently_read_github_candidate(self):
        value = director_reviewed_bundle("V2", software=True)
        candidate = {"kind": "PULL_REQUEST", "repository": "example-org/example", "ref": 23, "head_sha": "a" * 40}
        artifact(value, "RESULT-1")["published_candidate"] = deepcopy(candidate)
        review = artifact(value, "DIRECTOR-POST")["director_review"]
        review["verified_candidate"] = deepcopy(candidate)
        def reader(kind, repository, ref):
            return {"number": 23, "state": "open", "draft": True, "merged": False,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": candidate["head_sha"], "repo": {"full_name": repository}},
                    "body": "Resolver-Assignment: ASSIGN-RESOLVED"}
        self.assertEqual(resolve_transition(value, github_candidate_reader=reader)["control_state"], "COMPLETE")
        review["verified_candidate"]["head_sha"] = "b" * 40
        self.assertEqual(resolve_transition(value, github_candidate_reader=reader)["reason"], "DIRECTOR_REVIEW_CANDIDATE_NOT_PROVEN")

    def test_mixed_director_and_verifier_check_only_their_assigned_claims(self):
        value = director_reviewed_bundle()
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["verification_required"] = True
        authority["verification_target_claim_ids"] = ["architecture-alignment"]
        authority["allowed_verification_outcomes"] = ["CONFIRMED", "NOT_PROVEN"]
        authority["verification_outcome_map"] = {"CONFIRMED": "COMPLETE", "NOT_PROVEN": "WAIT"}
        director = artifact(value, "DIRECTOR-POST")
        director["verification_result_ref"] = "VERIFY-1"
        value["refs"]["verification_result_ref"] = "VERIFY-1"
        verifier = artifact(value, "VERIFY-1")
        verifier["claim_verdicts"] = [v for v in verifier["claim_verdicts"] if v["claim_id"] == "architecture-alignment"]
        director["director_review"]["claim_verdicts"] = [v for v in director["director_review"]["claim_verdicts"]
                                                         if v["claim_id"] != "architecture-alignment"]
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        value["refs"]["verification_result_ref"] = None
        self.assert_reason(value, "VERIFICATION_RESULT_PENDING")

    def test_director_owned_evidence_needs_no_future_executor_claim(self):
        value = director_reviewed_bundle("V2")
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        req = next(r for r in authority["acceptance_requirements"] if r["claim_id"] == "business-outcome")
        req.update(evidence_source="DIRECTOR", required_evidence_refs=["DIRECT-OBSERVATION"])
        executor = artifact(value, "RESULT-1")
        executor["claims"] = [c for c in executor["claims"] if c["claim_id"] != "business-outcome"]
        review = artifact(value, "DIRECTOR-POST")["director_review"]
        next(v for v in review["claim_verdicts"] if v["claim_id"] == "business-outcome")["evidence_refs"] = ["DIRECT-OBSERVATION"]
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_destructive_authority_source_must_be_read_and_scope_reviewed(self):
        value = director_reviewed_bundle("V4")
        value["artifacts"] = [item for item in value["artifacts"] if item.get("artifact_id") != "owner:authorized-cutover"]
        self.assert_reason(value, "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: True)["reason"], "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda ref: ref)["reason"], "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        for key in ("body", "content", "text", "source_text", "decision"):
            with self.subTest(echo_field=key):
                echo = {"ref": "owner:authorized-cutover", key: "owner:authorized-cutover"}
                self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: echo)["reason"], "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: "Owner approved this cutover scope.")["control_state"], "COMPLETE")
        source = {"url": "https://api.example.invalid/decision", "body": "Owner approved this cutover scope."}
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: source)["control_state"], "COMPLETE")
        structured = {"artifact_type": "OWNER_DECISION_RECORD", "artifact_id": "D-1",
                      "produced_by_role": "owner-interface", "status": "RECORDED",
                      "selected_option": "Approve the scoped cutover"}
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: structured)["control_state"], "COMPLETE")
        direct = {"artifact_type": "OWNER_DECISION_RECORD", "artifact_id": "D-2",
                  "produced_by_role": "owner-interface", "status": "RECORDED",
                  "canon_input_mode": "DIRECT_INSTRUCTION", "canon_instruction_text": "Proceed with this scoped Canon transition."}
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: direct)["control_state"], "COMPLETE")
        direct["canon_instruction_text"] = "  "
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: direct)["reason"], "OWNER_AUTHORITY_SOURCE_NOT_PROVEN")
        review = artifact(value, "DIRECTOR-POST")["director_review"]
        transition = next(v for v in review["claim_verdicts"] if v["claim_id"] == "migration-safety")
        transition["evidence_refs"] = ["EVIDENCE-RESULT"]
        self.assertEqual(resolve_transition(value, owner_decision_reader=lambda _: "Owner approved this cutover scope.")["reason"], "OWNER_AUTHORITY_REVIEW_NOT_PROVEN")

    def test_replacement_and_destructive_modes_use_v4_transition_review(self):
        for tier in ("V2", "V3"):
            for mode in ("REPLACEMENT_PRESERVE", "DESTRUCTIVE_CUTOVER"):
                with self.subTest(tier=tier, mode=mode):
                    value = director_reviewed_bundle(tier)
                    gate = artifact(value, "DIRECTOR-POST")["transition_authority"]["review_gate"]
                    gate.update(transition_mode=mode, owner_decision_ref="owner:authorized-cutover")
                    self.assert_reason(value, "MALFORMED_DIRECTOR_DECISION")

    def test_director_review_cannot_use_unconfirmed_claims(self):
        value = director_reviewed_bundle()
        review = artifact(value, "DIRECTOR-POST")["director_review"]
        next(v for v in review["claim_verdicts"] if v["claim_id"] == "progress-to-target")["verdict"] = "NOT_PROVEN"
        self.assert_reason(value, "TARGET_ALIGNMENT_NOT_PROVEN")

    def test_existing_v1_review_cannot_discard_negative_required_findings(self):
        value = transition_bundle(verification=False)
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        director = artifact(value, "DIRECTOR-POST")
        director["director_review"] = {
            "review_type": "DIRECTOR_REVIEW", "assignment_id": director["assignment_id"],
            "executor_result_ref": director["executor_result_ref"], "input_state_ref": director["input_state_ref"],
            "verified_state_identity": artifact(value, "STATE-RESULT")["state_identity"], "status": "NOT_PROVEN",
            "claim_verdicts": [{"claim_id": "claim-result", "verdict": "NOT_PROVEN", "evidence_refs": []}],
        }
        review = director["director_review"]
        self.assert_reason(value, "DIRECTOR_REVIEW_NOT_PROVEN")
        review["status"] = "CONFIRMED"
        self.assert_reason(value, "DIRECTOR_REVIEW_NOT_PROVEN")
        review["claim_verdicts"][0].update(verdict="CONFIRMED", evidence_refs=["DIRECT-OBSERVATION"])
        review["status"] = "NOT_PROVEN"
        self.assert_reason(value, "DIRECTOR_REVIEW_NOT_PROVEN")
        review["claim_verdicts"] = []
        self.assert_reason(value, "DIRECTOR_REVIEW_NOT_PROVEN")
        review["claim_verdicts"] = [{"claim_id": "unrelated-optional", "verdict": "NOT_PROVEN", "evidence_refs": []}]
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        review["status"] = "CONFIRMED"
        review["claim_verdicts"].append({"claim_id": "claim-result", "verdict": "CONFIRMED", "evidence_refs": ["DIRECT-OBSERVATION"]})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_exact_state_drift_still_blocks_promoted_claims(self):
        value = reviewed_bundle()
        artifact(value, "STATE-OBS-1")["state_identity"] = "git:changed-head"
        self.assert_reason(value, "RELEVANT_PROOF_STALE")

    def test_schema_declares_same_elevated_contract(self):
        schema = json.loads((ROOT / "schemas/director-decision.schema.json").read_text())
        gate = schema["properties"]["transition_authority"]["properties"]["review_gate"]
        self.assertEqual(set(gate["properties"]["tier"]["enum"]), {"V2", "V3", "V4"})
        self.assertIn("outcome_claim_id", gate["required"])
        self.assertEqual(len(gate["allOf"]), 3)
        self.assertEqual(gate["allOf"][2]["then"]["properties"]["tier"]["const"], "V4")


if __name__ == "__main__":
    unittest.main()
