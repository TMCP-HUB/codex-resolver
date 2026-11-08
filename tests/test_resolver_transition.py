from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_assignment_compiler import action, claim
from tests.test_executability_parity import schema_accepts
from tests.test_resolver_spawn import bundle as spawn_bundle
from tools.resolver_spawn import resolve_spawn
from tools.resolver_transition import resolve_transition

ROOT = Path(__file__).resolve().parents[1]


def transition_bundle(*, verification=True, incomplete="WAIT", verification_status="CONFIRMED",
                      software=False, branch_capability=False):
    # Generic transition tests are not code-mutation Software assignments.
    capability = "implement_software_change" if software else "plan_software_work"
    pre_spawn = spawn_bundle("production/software", capability, "implementation")
    if software and branch_capability:
        pre_spawn["assignment_draft_semantics"]["github_candidate_delivery"]["allowed_kinds"] = [
            "PULL_REQUEST", "BRANCH"
        ]
        profile = pre_spawn["artifacts"][2]
        evidence = profile["evidence_artifacts"][0]
        route = pre_spawn["artifacts"][3]
        profile["available_capabilities"].append("remote_branch_write")
        profile["capability_evidence"].append({"capability": "remote_branch_write", "evidence_ref": "EVIDENCE-1"})
        evidence["capabilities"].append("remote_branch_write")
        route["segments"][0]["required_capabilities"].append("remote_branch_write")
    spawned = resolve_spawn(pre_spawn)
    if spawned.get("status") != "SPAWN_READY":
        raise AssertionError(spawned)
    assignment = spawned["assignment"]
    admission = spawned["assignment_admissibility"]
    result = {
        "artifact_type": "EXECUTOR_RESULT", "artifact_id": "RESULT-1", "produced_by_role": "executor",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"], "status": "COMPLETE",
        "provenance": [assignment["artifact_id"]], "related_artifacts": [assignment["artifact_id"]],
        "resulting_state_refs": ["STATE-RESULT"], "evidence_refs": ["EVIDENCE-RESULT"],
        "deferred_findings": [], "limitations": [],
        "claims": [{"claim_id": "claim-result", "claim": "The required output was produced.",
                    "evidence_refs": ["EVIDENCE-RESULT"]}],
    }
    verification_result = {
        "artifact_type": "VERIFICATION_RESULT", "artifact_id": "VERIFY-1", "produced_by_role": "control-verifier",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"],
        "status": verification_status, "provenance": [result["artifact_id"]],
        "related_artifacts": [result["artifact_id"]], "executor_result_ref": result["artifact_id"],
        "claim_verdicts": [{"claim_id": "claim-result", "verdict": verification_status if verification_status != "BLOCKED" else "NOT_PROVEN",
                            "evidence_refs": ["EVIDENCE-RESULT"]}], "additional_findings": [], "evidence_gaps": [],
    }
    outcome_map = {"CONFIRMED": "COMPLETE", "QUALIFIED": "WAIT", "NOT_PROVEN": incomplete, "BLOCKED": "WAIT"}
    director = {
        "artifact_type": "DIRECTOR_DECISION", "artifact_id": "DIRECTOR-POST", "produced_by_role": "control-director",
        "assignment_id": assignment["assignment_id"], "input_state_ref": assignment["input_state_ref"], "status": "PENDING",
        "provenance": [assignment["artifact_id"]], "related_artifacts": [assignment["artifact_id"], admission["artifact_id"]],
        "executor_result_ref": result["artifact_id"], "verification_result_ref": verification_result["artifact_id"] if verification else None,
        "control_state": "WAIT", "decision": "Reconcile the structured post-spawn control point.", "next_owner": "control-director",
        "transition_authority": {
            "transition_id": "TRANSITION-1", "assignment_ref": assignment["artifact_id"],
            "acceptance_requirements": [{"requirement_id": "tests-pass", "claim_id": "claim-result",
                                         "required_evidence_refs": ["EVIDENCE-RESULT"]}],
            "verification_required": verification,
            "verification_target_claim_ids": ["claim-result"] if verification else [],
            "allowed_verification_outcomes": ["CONFIRMED", "QUALIFIED", "NOT_PROVEN", "BLOCKED"] if verification else [],
            "verification_outcome_map": outcome_map if verification else {},
            "incomplete_outcome": incomplete, "next_control_intent_ref": None,
            "required_proof_refs": [admission["artifact_id"]], "requires_current_executability": False,
        },
    }
    current = {"artifact_type": "STATE_OBSERVATION", "artifact_id": "STATE-RESULT", "produced_by_role": "control-director",
               "input_state_ref": assignment["input_state_ref"], "status": "CURRENT", "provenance": [result["artifact_id"]],
               "related_artifacts": [result["artifact_id"]], "state_identity": "git:result", "authority_scope": "transition-result"}
    artifacts = deepcopy(pre_spawn["artifacts"]) + [spawned["compiled_assignment"], admission, assignment, result, director, current]
    if verification:
        artifacts.append(verification_result)
    return {"refs": {"current_state_ref": current["artifact_id"], "prior_director_decision_ref": director["artifact_id"],
                     "assignment_ref": assignment["artifact_id"], "executor_result_ref": result["artifact_id"],
                     "verification_result_ref": verification_result["artifact_id"] if verification else None,
                     "current_capability_profile_ref": spawned["capability_profile_ref"]},
            "artifacts": artifacts, "spawned": spawned}


def artifact(value, artifact_id):
    return next(item for item in value["artifacts"] if item.get("artifact_id") == artifact_id)


def add_verifier_requirement(value):
    authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
    authority["acceptance_requirements"].append({"requirement_id": "acceptance-observation",
        "claim_id": "verified-observation", "required_evidence_refs": ["VERIFIER-EVIDENCE"],
        "evidence_source": "VERIFIER"})
    authority["verification_target_claim_ids"].append("verified-observation")
    verifier = artifact(value, "VERIFY-1")
    verifier["verified_state_identity"] = artifact(value, "STATE-RESULT")["state_identity"]
    verifier["claim_verdicts"].append({"claim_id": "verified-observation", "verdict": "CONFIRMED",
                                       "evidence_refs": ["VERIFIER-EVIDENCE"]})


class ResolverTransitionTest(unittest.TestCase):
    def test_real_spawn_output_flows_into_transition(self):
        value = transition_bundle()
        self.assertEqual(value["spawned"]["status"], "SPAWN_READY")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_spawn_materializes_deterministic_selective_lifecycle(self):
        first, second = resolve_spawn(spawn_bundle()), resolve_spawn(spawn_bundle())
        self.assertEqual(first["assignment_admissibility"]["transition_proof"], second["assignment_admissibility"]["transition_proof"])
        proof = first["assignment_admissibility"]["transition_proof"]
        self.assertEqual(proof["assignment_ref"], first["assignment"]["artifact_id"])
        self.assertEqual(proof["admissibility_ref"], first["assignment_admissibility"]["artifact_id"])
        self.assertEqual(proof["dependency_bindings"], [{"dependency_ref": "STATE-OBS-1", "proven_identity": "git:input-state"}])

    def test_l1_real_proof_relevant_change(self):
        value = transition_bundle(); artifact(value, "STATE-OBS-1")["state_identity"] = "git:changed"
        self.assertEqual(resolve_transition(value)["reason"], "RELEVANT_PROOF_STALE")

    def test_l2_real_proof_unrelated_change(self):
        value = transition_bundle(); value["artifacts"].append({"artifact_type": "STATE_OBSERVATION", "artifact_id": "UNRELATED",
            "produced_by_role": "control-director", "input_state_ref": None, "status": "CURRENT", "provenance": [],
            "related_artifacts": [], "state_identity": "other", "authority_scope": "unrelated"})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def _current_profile(self, value, *, destination=None, remove_capability=None):
        old = artifact(value, value["spawned"]["capability_profile_ref"])
        profile = deepcopy(old); profile["artifact_id"] = "PROFILE-NOW"
        evidence = deepcopy(profile["evidence_artifacts"][0]); evidence["artifact_id"] = "EVIDENCE-NOW"
        profile["evidence_artifacts"] = [evidence]; profile["related_artifacts"] = [evidence["artifact_id"]]
        for item in profile["capability_evidence"]: item["evidence_ref"] = evidence["artifact_id"]
        if destination is not None: profile["destination_id"] = destination
        if remove_capability:
            profile["available_capabilities"].remove(remove_capability); profile["unavailable_capabilities"].append(remove_capability)
            profile["capability_evidence"] = [item for item in profile["capability_evidence"] if item["capability"] != remove_capability]
            evidence["capabilities"].remove(remove_capability)
        value["artifacts"].extend([profile, evidence]); value["refs"]["current_capability_profile_ref"] = profile["artifact_id"]
        artifact(value, "DIRECTOR-POST")["transition_authority"]["requires_current_executability"] = True

    def test_l3_real_proof_runtime_drift(self):
        value = transition_bundle(); self._current_profile(value, remove_capability="shell")
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "BLOCKED_RUNTIME_DRIFT"))

    def test_l4_wrong_destination_profile(self):
        value = transition_bundle(); self._current_profile(value, destination="other-destination")
        self.assertEqual(resolve_transition(value)["reason"], "CURRENT_PROFILE_EXECUTION_SURFACE_MISMATCH")

    def test_executor_cannot_self_certify_acceptance(self):
        value = transition_bundle(verification=False, incomplete="WAIT")
        result = artifact(value, "RESULT-1"); result["acceptance_status"] = "SATISFIED"
        result["claims"][0]["evidence_refs"] = []
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")

    def test_verifier_evidence_satisfies_its_claim_without_future_executor_evidence(self):
        value = transition_bundle(); add_verifier_requirement(value)
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
        verdict = artifact(value, "VERIFY-1")["claim_verdicts"][-1]
        verdict["evidence_refs"] = ["OTHER-EVIDENCE"]
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")
        verdict["evidence_refs"] = ["VERIFIER-EVIDENCE"]
        verdict["claim_id"] = "different-claim"
        self.assertNotEqual(resolve_transition(value)["control_state"], "COMPLETE")
        verdict["claim_id"] = "verified-observation"
        verdict["verdict"] = "NOT_PROVEN"
        self.assertNotEqual(resolve_transition(value)["control_state"], "COMPLETE")
        artifact(value, "DIRECTOR-POST")["transition_authority"]["verification_required"] = False
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_DIRECTOR_DECISION")

    def test_verifier_evidence_cannot_replace_executor_evidence_or_stale_scope(self):
        value = transition_bundle(); add_verifier_requirement(value)
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = []
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = ["EVIDENCE-RESULT"]
        artifact(value, "VERIFY-1")["verified_state_identity"] = "git:stale-result"
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_CANDIDATE_NOT_PROVEN")
        artifact(value, "VERIFY-1")["verified_state_identity"] = "git:result"
        artifact(value, "VERIFY-1")["executor_result_ref"] = "OTHER-RESULT"
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_IDENTITY_MISMATCH")

    def test_unused_compiled_claim_does_not_create_an_evidence_obligation(self):
        value = transition_bundle(); add_verifier_requirement(value)
        compiled = artifact(value, "COMPILED-1")
        unused = deepcopy(compiled["authorized_claims"][0]); unused["claim_id"] = "verified-observation"
        compiled["authorized_claims"].append(unused)
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_executor_evidence_cannot_drop_compiled_acceptance(self):
        for verification in (False, True):
            with self.subTest(verification_required=verification):
                value = transition_bundle(verification=verification)
                self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")
                authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
                authority["acceptance_requirements"] = [{"requirement_id": "report-only",
                    "claim_id": "report-result", "required_evidence_refs": ["REPORT-EVIDENCE"]}]
                executor = artifact(value, "RESULT-1")
                executor["claims"] = [{"claim_id": "report-result", "claim": "A report was produced.",
                    "evidence_refs": ["REPORT-EVIDENCE"]}]
                executor["evidence_refs"] = ["REPORT-EVIDENCE"]
                if verification:
                    authority["verification_target_claim_ids"] = ["report-result"]
                    verifier = artifact(value, "VERIFY-1")
                    verifier["claim_verdicts"] = [{"claim_id": "report-result", "verdict": "CONFIRMED",
                        "evidence_refs": ["REPORT-EVIDENCE"]}]
                self.assertEqual(resolve_transition(value)["reason"], "COMPILED_ACCEPTANCE_REQUIREMENT_MISSING")

    def test_selected_executor_outcome_survives_compilation_and_transition(self):
        make_bundle = spawn_bundle

        def with_selected(*args, **kwargs):
            value = make_bundle(*args, **kwargs)
            draft = value["assignment_compilation_draft"]
            draft["authorized_claims"].append(claim("impact-outcome", target="acceptance:impact-reviewed"))
            draft["acceptance_requirements"].append({"requirement_id": "impact-reviewed"})
            value["selected_prerequisite_actions"] = [action("inspect-impact", claim_ref="impact-outcome",
                operation="INSPECT_SOURCE", obligation_class="remote_observation", capabilities=["repository_remote_read"])]
            return value

        with patch(f"{__name__}.spawn_bundle", with_selected):
            value = transition_bundle(verification=False)
        compiled = artifact(value, "COMPILED-1")
        self.assertEqual(sum(item["action_id"] == "inspect-impact" for item in compiled["authorized_mandatory_actions"]), 1)
        missing = resolve_transition(value)
        self.assertEqual(missing["reason"], "COMPILED_ACCEPTANCE_REQUIREMENT_MISSING")
        self.assertIn("impact-reviewed", missing["requirement_ids"])

        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["acceptance_requirements"].append({"requirement_id": "impact-reviewed",
            "claim_id": "impact-result", "required_evidence_refs": ["EVIDENCE-IMPACT"]})
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")
        executor = artifact(value, "RESULT-1")
        executor["claims"].append({"claim_id": "impact-result", "claim": "Impact was reviewed.",
                                   "evidence_refs": ["EVIDENCE-IMPACT"]})
        executor["evidence_refs"].append("EVIDENCE-IMPACT")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_extended_selected_outcome_and_fields_reach_executor_and_transition(self):
        make_bundle = spawn_bundle
        selected = action("inspect-impact", claim_ref="impact-outcome", operation="INSPECT_SOURCE",
                          obligation_class="remote_observation", capabilities=["repository_remote_read"])
        selected.update(source_ref="existing:source", context={"scope": ["one", "two"]},
                        evidence_path="requested:location")

        def with_selected(*args, **kwargs):
            value = make_bundle(*args, **kwargs)
            draft = value["assignment_compilation_draft"]
            draft["authorized_claims"].append(claim("impact-outcome", target="acceptance:impact-reviewed"))
            draft["acceptance_requirements"].append({"requirement_id": "impact-reviewed"})
            value["selected_prerequisite_actions"] = [deepcopy(selected)]
            return value

        with patch(f"{__name__}.spawn_bundle", with_selected):
            value = transition_bundle(verification=False)
        compiled = artifact(value, "COMPILED-1")
        self.assertIn(selected, compiled["authorized_mandatory_actions"])
        self.assertIn(selected, compiled["executor_responsibilities"])
        self.assertIn(selected, value["spawned"]["assignment_admissibility"]["mandatory_actions"])
        schema = json.loads((ROOT / "schemas/compiled-assignment.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(schema_accepts(selected, schema["$defs"]["obligation"]))

        missing = resolve_transition(value)
        self.assertEqual(missing["reason"], "COMPILED_ACCEPTANCE_REQUIREMENT_MISSING")
        self.assertIn("impact-reviewed", missing["requirement_ids"])
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["acceptance_requirements"].append({"requirement_id": "impact-reviewed",
            "claim_id": "impact-result", "required_evidence_refs": ["EVIDENCE-IMPACT"]})
        self.assertEqual(resolve_transition(value)["control_state"], "WAIT")
        executor = artifact(value, "RESULT-1")
        executor["claims"].append({"claim_id": "impact-result", "claim": "Impact was reviewed.",
                                   "evidence_refs": ["EVIDENCE-IMPACT"]})
        executor["evidence_refs"].append("EVIDENCE-IMPACT")
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_verifier_cannot_drop_compiled_acceptance_but_can_directly_prove_it(self):
        value = transition_bundle(); add_verifier_requirement(value)
        authority = artifact(value, "DIRECTOR-POST")["transition_authority"]
        authority["acceptance_requirements"] = [authority["acceptance_requirements"][-1]]
        authority["verification_target_claim_ids"] = ["verified-observation"]
        result = artifact(value, "RESULT-1"); result["claims"] = []; result["evidence_refs"] = []
        self.assertEqual(resolve_transition(value)["reason"], "COMPILED_ACCEPTANCE_REQUIREMENT_MISSING")
        authority["acceptance_requirements"][0]["requirement_id"] = "tests-pass"
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_unused_malformed_compiled_claim_does_not_crash_transition(self):
        value = transition_bundle(); add_verifier_requirement(value)
        artifact(value, "COMPILED-1")["authorized_claims"].append({"claim_id": [], "responsibility": "EXECUTOR"})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_compiled_claim_lookup_matches_existing_runtime_normalization(self):
        value = transition_bundle(); add_verifier_requirement(value)
        compiled = artifact(value, "COMPILED-1")
        compiled["authorized_claims"][0]["claim_id"] = "['existing']"
        for field in ("authorized_mandatory_actions", "executor_responsibilities"):
            compiled[field][0]["claim_ref"] = ["existing"]
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_verifier_evidence_binds_exact_github_candidate(self):
        value = transition_bundle(software=True); add_verifier_requirement(value)
        candidate = {"kind": "PULL_REQUEST", "repository": "example-org/example", "ref": 23,
                     "head_sha": "a" * 40}
        artifact(value, "RESULT-1")["published_candidate"] = candidate
        verifier = artifact(value, "VERIFY-1"); verifier["verified_candidate"] = deepcopy(candidate)
        def reader(kind, repository, ref):
            return {"number": 23, "state": "open", "draft": True, "merged": False,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": candidate["head_sha"], "repo": {"full_name": repository}},
                    "body": "Resolver-Assignment: ASSIGN-RESOLVED"}
        self.assertEqual(resolve_transition(value, github_candidate_reader=reader)["control_state"], "COMPLETE")
        verifier["verified_candidate"]["head_sha"] = "b" * 40
        self.assertEqual(resolve_transition(value, github_candidate_reader=reader)["reason"], "VERIFICATION_CANDIDATE_NOT_PROVEN")

    def test_missing_required_verification_waits(self):
        value = transition_bundle(); value["refs"]["verification_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_PENDING")

    def test_same_actor_route_does_not_replace_required_verifier(self):
        value = transition_bundle()
        for edge in artifact(value, "ROUTE-1")["handoffs"]:
            edge.update(same_actor_continuation=True, internal_required_capabilities=[])
        value["refs"]["verification_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "VERIFICATION_RESULT_PENDING")

    def test_verifier_cannot_replace_executor(self):
        value = transition_bundle(); value["refs"]["executor_result_ref"] = None
        self.assertEqual(resolve_transition(value)["reason"], "EXECUTOR_RESULT_PENDING")

    def test_not_proven_baton_is_director_owned(self):
        waiting = transition_bundle(verification_status="NOT_PROVEN", incomplete="WAIT")
        self.assertEqual(resolve_transition(waiting)["control_state"], "WAIT")
        escalating = transition_bundle(verification_status="NOT_PROVEN", incomplete="ESCALATE")
        self.assertEqual(resolve_transition(escalating)["control_state"], "ESCALATE")

    def test_aggregate_verification_cannot_elevate_required_claim(self):
        value = transition_bundle(verification_status="CONFIRMED", incomplete="WAIT")
        artifact(value, "VERIFY-1")["claim_verdicts"][0]["verdict"] = "NOT_PROVEN"
        result = resolve_transition(value)
        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "AUTHORIZED_VERIFICATION_OUTCOME"))
        self.assertEqual(result["verification_outcome"], "NOT_PROVEN")

    def test_malformed_director_and_non_proven_assignment_fail(self):
        value = transition_bundle(); del artifact(value, "DIRECTOR-POST")["decision"]
        self.assertEqual(resolve_transition(value)["reason"], "MALFORMED_DIRECTOR_DECISION")
        value = transition_bundle(); artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["proof_status"] = "UNPROVEN"
        self.assertEqual(resolve_transition(value)["reason"], "INVALID_GOVERNED_ASSIGNMENT")

    def test_arbitrary_proof_and_wrong_admission_ref_fail(self):
        value = transition_bundle(); admission = artifact(value, "ADM-RESOLVED"); admission["artifact_type"] = "OTHER_PROOF"
        self.assertIn(resolve_transition(value)["reason"], {"INVALID_GOVERNED_ASSIGNMENT", "INVALID_PROOF_CLASS"})
        value = transition_bundle(); artifact(value, "ASSIGN-RESOLVED")["execution_contract"]["admissibility_ref"] = "OTHER"
        self.assertEqual(resolve_transition(value)["reason"], "ASSIGNMENT_PROOF_CHAIN_UNRESOLVED")

    def test_assign_fence(self):
        value = transition_bundle(verification=False, incomplete="ASSIGN")
        intent = {"artifact_type": "CONTROL_INTENT", "artifact_id": "INTENT-1",
                  "assignment_id": "ASSIGN-RESOLVED", "next_action": "run pre-spawn composition"}
        value["artifacts"].append(intent); artifact(value, "DIRECTOR-POST")["transition_authority"]["next_control_intent_ref"] = "INTENT-1"
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = []
        result = resolve_transition(value)
        self.assertEqual(result["next_entrypoint"], "tools.resolver_spawn.resolve_spawn")
        self.assertNotIn("assignment", result)

    def test_health_decision_governs_only_the_next_implicated_repair(self):
        value = transition_bundle(verification=False, incomplete="ASSIGN")
        current = artifact(value, "STATE-RESULT")
        health = {"artifact_type": "DIRECTOR_DECISION", "artifact_id": "HEALTH-1",
                  "produced_by_role": "control-director", "assignment_id": None, "input_state_ref": None,
                  "status": "RECORDED", "provenance": ["target:accepted"], "related_artifacts": ["evidence:repair"],
                  "executor_result_ref": None, "verification_result_ref": None, "control_state": "WAIT",
                  "decision": "Hold this repair while the cause is reconciled.", "next_owner": "control-director",
                  "architecture_health": {"affected_boundary_ref": "boundary:repair",
                      "observed_state_identity": current["state_identity"], "disposition": "ARCHITECTURE_REVIEW_REQUIRED",
                      "target_ref": "target:accepted", "evidence_refs": ["evidence:repair"]}}
        context = {"decision_ref": "HEALTH-1", "boundary_ref": "boundary:repair", "action_mode": "MUTATING_REPAIR",
                   "state_observation_ref": current["artifact_id"]}
        intent = {"artifact_type": "CONTROL_INTENT", "artifact_id": "INTENT-1",
                  "assignment_id": "ASSIGN-RESOLVED", "architecture_context": context}
        value["artifacts"].extend([health, intent])
        artifact(value, "DIRECTOR-POST")["transition_authority"]["next_control_intent_ref"] = "INTENT-1"
        artifact(value, "RESULT-1")["claims"][0]["evidence_refs"] = []
        self.assertEqual(resolve_transition(value)["reason"], "ARCHITECTURE_HEALTH_REVIEW_REQUIRED")
        context["action_mode"] = "CAUSAL_ANALYSIS"
        self.assertEqual(resolve_transition(value)["control_state"], "ASSIGN")
        context.update(action_mode="MUTATING_REPAIR", boundary_ref="boundary:unrelated")
        self.assertEqual(resolve_transition(value)["control_state"], "ASSIGN")
        context["boundary_ref"] = "boundary:repair"; current["state_identity"] = "git:changed"
        self.assertEqual(resolve_transition(value)["reason"], "ARCHITECTURE_HEALTH_RECONCILIATION_REQUIRED")

    def test_health_stop_does_not_block_acceptance_of_already_finished_work(self):
        value = transition_bundle(verification=False)
        value["artifacts"].append({"artifact_type": "DIRECTOR_DECISION", "artifact_id": "HEALTH-1",
            "produced_by_role": "control-director", "assignment_id": None, "input_state_ref": None,
            "status": "RECORDED", "provenance": ["target:accepted"], "related_artifacts": ["evidence:repair"],
            "executor_result_ref": None, "verification_result_ref": None, "control_state": "WAIT",
            "decision": "Hold this repair while the cause is reconciled.", "next_owner": "control-director", "architecture_health": {
                "affected_boundary_ref": "boundary:repair", "observed_state_identity": "git:result",
                "disposition": "ARCHITECTURE_REVIEW_REQUIRED", "target_ref": "target:accepted",
                "evidence_refs": ["evidence:repair"]}})
        self.assertEqual(resolve_transition(value)["control_state"], "COMPLETE")

    def test_cli_reads_local_json(self):
        value = transition_bundle(); value.pop("spawned")
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(value, handle); handle.flush()
            completed = subprocess.run([sys.executable, str(ROOT / "tools/resolver_transition.py"), handle.name], check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(completed.stdout)["control_state"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
