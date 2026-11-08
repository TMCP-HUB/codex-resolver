from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.assignment_compiler import (
    AUTHORITY_CLASSES, CONTEXT_AUTHORITIES, COMPILED_CAPABILITY_MISMATCH,
    INVALID_EXECUTION_HINT, INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,
    OBLIGATION_NOT_AUTHORIZED, PLATFORM_FACT_REAUTHENTICATION,
    UNSUPPORTED_EXECUTION_ENVELOPE, compile_assignment,
    validate_compiled_assignment,
)
from tools.executability import evaluate_assignment_admissibility


ROOT = Path(__file__).resolve().parents[1]


def envelope(classes=None, artifact_id="ENVELOPE-1"):
    return {"artifact_type":"EXECUTION_ENVELOPE","artifact_id":artifact_id,"produced_by_role":"control-director","assignment_id":None,"input_state_ref":"state-1","status":"CURRENT","provenance":["portfolio"],"related_artifacts":[],"supported_obligation_classes":classes or ["local_execution","local_evidence","remote_observation","provided_context","control_adjudication"]}


def resolver_for(*artifacts):
    by_id={item["artifact_id"]:item for item in artifacts}
    return by_id.get


def claim(claim_id="local-outcome", *, kind="TASK_OUTCOME", source="RESOLVER_BOUND", target="acceptance:tests-pass", responsibility="EXECUTOR", verification=False, classification="runtime_resolved"):
    return {"claim_id":claim_id,"claim_kind":kind,"authority_source":source,"target_ref":target,"responsibility":responsibility,"independent_verification_required":verification,"classification":classification}


def action(action_id="test", *, claim_ref="local-outcome", responsibility="EXECUTOR", operation="RUN_TESTS", obligation_class="local_execution", fact_ref=None, capabilities=None):
    return {"action_id":action_id,"claim_ref":claim_ref,"responsibility":responsibility,"operation":operation,"obligation_class":obligation_class,"context_fact_ref":fact_ref,"required_capabilities":capabilities or ["shell"],"evidence_path":None}


def draft(authority_class="MOVING_PR"):
    return {
      "compiled_artifact_id":"COMPILED-1","assignment_draft_ref":"DRAFT-1","input_state_ref":"state-1","provenance":["OWNER-1"],"related_artifacts":["DRAFT-1"],"authority_class":authority_class,
      "context_facts":[{"fact_id":"workspace","fact_kind":"repository_checkout","authority_source":"PLATFORM_PROVIDED","value_or_ref":"provided:workspace","mutable":True,"required_for":["execution"]},{"fact_id":"local-result","fact_kind":"test_result","authority_source":"EXECUTOR_RESOLVED","value_or_ref":"runtime","mutable":True,"required_for":["acceptance"]}],
      "authorized_claims":[claim()],"invariants":[],"mandatory_actions":[action()],"evidence_requirements":[],"acceptance_requirements":[{"requirement_id":"tests-pass"}],"stop_conditions":[]}


def compile_ok(value, env=None, authority_resolver=None):
    env=env or envelope(); return compile_assignment(value,env["artifact_id"],resolver_for(env),authority_resolver)

def codes(result): return {error["code"] for error in result["compilation_errors"]}


class AssignmentCompilerTest(unittest.TestCase):
    def test_enum_contract(self):
        self.assertEqual(AUTHORITY_CLASSES,("FROZEN_CANDIDATE","MOVING_PR","MOVING_BRANCH","POST_MERGE_STATE","LIVE_REMOTE_STATE")); self.assertEqual(CONTEXT_AUTHORITIES,("PLATFORM_PROVIDED","RESOLVER_BOUND","EXECUTOR_RESOLVED","REMOTE_LIVE"))

    def test_compiler_consumes_a_selected_director_health_decision(self):
        value = draft(); value["architecture_context"] = {
            "decision_ref": "HEALTH-1", "boundary_ref": "boundary:one", "action_mode": "MUTATING_REPAIR",
            "state_observation_ref": "STATE-1"}
        decision = {"artifact_id": "HEALTH-1", "artifact_type": "DIRECTOR_DECISION",
                    "produced_by_role": "control-director", "assignment_id": None, "input_state_ref": None,
                    "status": "RECORDED", "provenance": ["target:accepted"], "related_artifacts": ["evidence:repair"],
                    "executor_result_ref": None, "verification_result_ref": None, "control_state": "WAIT",
                    "decision": "Reconcile the cause before further repair.", "next_owner": "control-director", "architecture_health": {
                        "affected_boundary_ref": "boundary:one", "observed_state_identity": "git:head",
                        "disposition": "ARCHITECTURE_REVIEW_REQUIRED", "target_ref": "target:accepted",
                        "evidence_refs": ["evidence:repair"]}}
        state = {"artifact_id": "STATE-1", "artifact_type": "STATE_OBSERVATION",
                 "produced_by_role": "control-director", "status": "CURRENT", "state_identity": "git:head"}
        result = compile_ok(value, authority_resolver=resolver_for(decision, state))
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("ARCHITECTURE_HEALTH_REVIEW_REQUIRED", codes(result))
        value["architecture_context"]["action_mode"] = "CAUSAL_ANALYSIS"
        self.assertEqual(compile_ok(value, authority_resolver=resolver_for(decision, state))["status"], "COMPILED")

    def test_every_obligation_requires_authorized_claim(self):
        value=draft(); value["mandatory_actions"].append(action("generic-remote",claim_ref="missing",operation="VERIFY_REMOTE_PR_HEAD",obligation_class="remote_observation",capabilities=["repository_remote_read","outbound_network"]))
        result=compile_ok(value)
        self.assertEqual(result["status"],"REJECTED"); self.assertIn(OBLIGATION_NOT_AUTHORIZED,codes(result)); self.assertNotIn("repository_remote_read",result["authorized_required_capabilities"])

    def test_operation_encoding_cannot_bypass_platform_authority(self):
        value=draft(); value["authorized_claims"].append(claim("workspace-use",kind="CONTEXT_FACT",source="PLATFORM_PROVIDED",target="workspace",responsibility="EXECUTOR",classification="platform_provided")); value["mandatory_actions"].append(action("generic-remote",claim_ref="workspace-use",operation="VERIFY_REMOTE_PR_HEAD",obligation_class="remote_observation",fact_ref="workspace",capabilities=["repository_remote_read","outbound_network"]))
        result=compile_ok(value); self.assertIn(PLATFORM_FACT_REAUTHENTICATION,codes(result)); self.assertEqual(result["authorized_required_capabilities"],[])

    def test_unbacked_immutable_claim_cannot_bypass_platform_authority(self):
        value=draft(); value["authorized_claims"].append(claim("forged",kind="IMMUTABLE_INVARIANT",target="workspace-identity",classification="immutable")); value["mandatory_actions"].append(action("generic-remote",claim_ref="forged",operation="VERIFY_REMOTE_PR_HEAD",obligation_class="remote_observation",capabilities=["repository_remote_read","outbound_network"]))
        result=compile_ok(value); self.assertIn(OBLIGATION_NOT_AUTHORIZED,codes(result)); self.assertEqual(result["authorized_required_capabilities"],[])

    def test_immutable_claim_requires_exact_invariant_semantics(self):
        base=draft("FROZEN_CANDIDATE"); base["invariants"]=[{"invariant_id":"candidate","identity_kind":"CANDIDATE_HEAD","classification":"immutable","responsibility":"EXECUTOR","target_ref":"candidate:release","value_or_ref":"sha:abc"}]
        base["authorized_claims"]=[claim("candidate-claim",kind="IMMUTABLE_INVARIANT",target="missing",classification="immutable")]; base["mandatory_actions"]=[action("verify",claim_ref="candidate-claim",operation="VERIFY_CANDIDATE",fact_ref=None)]
        self.assertIn(OBLIGATION_NOT_AUTHORIZED,codes(compile_ok(base)))
        classification=deepcopy(base); classification["authorized_claims"][0].update(target_ref="candidate:release",classification="runtime_resolved"); self.assertIn(OBLIGATION_NOT_AUTHORIZED,codes(compile_ok(classification)))
        responsibility=deepcopy(base); responsibility["authorized_claims"][0].update(target_ref="candidate:release",responsibility="CONTROL"); responsibility["mandatory_actions"][0]["responsibility"]="CONTROL"; self.assertIn(OBLIGATION_NOT_AUTHORIZED,codes(compile_ok(responsibility)))
        valid=deepcopy(base); valid["authorized_claims"][0]["target_ref"]="candidate:release"; result=compile_ok(valid); self.assertEqual(result["status"],"COMPILED"); self.assertEqual(validate_compiled_assignment(result,resolver_for(envelope())),[])

    def test_resolver_bound_independent_platform_verification_remains_valid(self):
        value=draft(); value["authorized_claims"].append(claim("independent",kind="INDEPENDENT_VERIFICATION",source="RESOLVER_BOUND",target="workspace",responsibility="EXECUTOR",verification=True,classification="platform_provided")); value["mandatory_actions"].append(action("independent-check",claim_ref="independent",operation="VERIFY_CONTEXT",obligation_class="remote_observation",fact_ref="workspace",capabilities=["repository_remote_read"]))
        result=compile_ok(value); self.assertEqual(result["status"],"COMPILED"); self.assertIn("repository_remote_read",result["authorized_required_capabilities"])

    def test_live_remote_authorized_claim_compiles(self):
        value=draft("LIVE_REMOTE_STATE"); value["context_facts"].append({"fact_id":"remote-release","fact_kind":"published_release","authority_source":"REMOTE_LIVE","value_or_ref":"remote:current","mutable":True,"required_for":["objective"]}); value["authorized_claims"]=[claim("remote-state",kind="RUNTIME_FACT",source="REMOTE_LIVE",target="remote-release",classification="remote_live")]; value["mandatory_actions"]=[action("read-remote",claim_ref="remote-state",operation="READ_REMOTE_STATE",obligation_class="remote_observation",fact_ref="remote-release",capabilities=["repository_remote_read","outbound_network"])]
        result=compile_ok(value); self.assertEqual(result["status"],"COMPILED"); self.assertEqual(result["authorized_required_capabilities"],["outbound_network","repository_remote_read"])

    def test_freeze_authority_must_resolve_and_match(self):
        base=draft(); base["invariants"]=[{"invariant_id":"head","identity_kind":"CANDIDATE_HEAD","classification":"immutable","responsibility":"CONTROL","target_ref":"workstream:39","value_or_ref":"sha:abc","independent_freeze_authority_ref":"FREEZE-1"}]
        self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(compile_ok(base)))
        no_ref=deepcopy(base); no_ref["invariants"][0]["independent_freeze_authority_ref"]=None; self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(compile_ok(no_ref)))
        branch=deepcopy(no_ref); branch["authority_class"]="MOVING_BRANCH"; self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(compile_ok(branch)))
        unrelated={"artifact_type":"OWNER_DECISION_RECORD","artifact_id":"FREEZE-1","status":"RECORDED"}; self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(compile_ok(base,authority_resolver=resolver_for(unrelated))))
        wrong={"artifact_type":"FREEZE_AUTHORITY","artifact_id":"FREEZE-1","produced_by_role":"owner-interface","status":"AUTHORIZED","provenance":["OWNER-DECISION-1"],"authority_role":"OWNER_K0","target_ref":"other","authority_class":"MOVING_PR","authorizes_exact_candidate_freeze":True,"candidate_identity":"sha:wrong"}; self.assertIn(INVALID_FROZEN_IDENTITY_FOR_MOVING_TARGET,codes(compile_ok(base,authority_resolver=resolver_for(wrong))))
        valid=dict(wrong,target_ref="workstream:39",candidate_identity="sha:abc"); result=compile_ok(base,authority_resolver=resolver_for(valid)); self.assertEqual(result["status"],"COMPILED"); self.assertEqual(validate_compiled_assignment(result,resolver_for(envelope()),resolver_for(valid)),[])

    def test_frozen_candidate_needs_no_moving_exception(self):
        value=draft("FROZEN_CANDIDATE"); value["invariants"]=[{"invariant_id":"head","identity_kind":"CANDIDATE_HEAD","classification":"immutable","responsibility":"CONTROL","target_ref":"candidate","value_or_ref":"sha:abc"}]
        self.assertEqual(compile_ok(value)["status"],"COMPILED")

    def test_non_frozen_authority_classes_preserve_local_work(self):
        for authority in ("MOVING_PR","MOVING_BRANCH","POST_MERGE_STATE"):
            with self.subTest(authority=authority): self.assertEqual(compile_ok(draft(authority))["status"],"COMPILED")

    def test_control_and_platform_obligations_remain_partitioned(self):
        value=draft(); value["authorized_claims"].extend([
          claim("platform-context",kind="CONTEXT_FACT",source="PLATFORM_PROVIDED",target="workspace",responsibility="PLATFORM",classification="platform_provided"),
          claim("control-context",kind="TASK_OUTCOME",source="RESOLVER_BOUND",target="acceptance:tests-pass",responsibility="CONTROL",classification="immutable")])
        value["mandatory_actions"].extend([
          action("provide",claim_ref="platform-context",responsibility="PLATFORM",operation="PROVIDE_CONTEXT",obligation_class="provided_context",fact_ref="workspace",capabilities=["platform_binding"]),
          action("adjudicate",claim_ref="control-context",responsibility="CONTROL",operation="ADJUDICATE",obligation_class="control_adjudication",capabilities=["owner_authority"])])
        result=compile_ok(value); self.assertEqual(result["status"],"COMPILED"); self.assertEqual(result["authorized_required_capabilities"],["shell"]); self.assertEqual(len(result["platform_responsibilities"]),1); self.assertEqual(len(result["control_responsibilities"]),1)

    def test_action_and_evidence_share_one_capability_closure(self):
        value=draft(); value["evidence_requirements"]=[action("checkout-proof",claim_ref="local-outcome",operation="OBSERVE_LOCAL",obligation_class="local_evidence",capabilities=["repository_local_checkout"])]
        result=compile_ok(value); self.assertEqual(result["authorized_required_capabilities"],["repository_local_checkout","shell"]); self.assertEqual(validate_compiled_assignment(result,resolver_for(envelope())),[])
        value["mandatory_actions"].append(action("again",capabilities=["shell"])); value["evidence_requirements"][0]["required_capabilities"]=["python_runtime"]; self.assertEqual(compile_ok(value)["authorized_required_capabilities"],["python_runtime","shell"])

    def test_control_evidence_does_not_contaminate_executor(self):
        value=draft(); value["authorized_claims"].append(claim("control-proof",kind="INDEPENDENT_VERIFICATION",source="RESOLVER_BOUND",target="control:acceptance",responsibility="CONTROL",verification=True)); value["evidence_requirements"]=[action("control-evidence",claim_ref="control-proof",responsibility="CONTROL",operation="VERIFY_CONTROL",obligation_class="control_adjudication",capabilities=["repository_remote_read"])]
        self.assertEqual(compile_ok(value)["authorized_required_capabilities"],["shell"])

    def test_validator_rejects_extra_capability_and_bad_envelope_claim(self):
        env=envelope(); result=compile_ok(draft(),env); result["authorized_required_capabilities"].append("outbound_network"); self.assertIn(COMPILED_CAPABILITY_MISMATCH,validate_compiled_assignment(result,resolver_for(env)))
        result=compile_ok(draft(),env); narrow=envelope(["remote_observation"]); self.assertIn(UNSUPPORTED_EXECUTION_ENVELOPE,validate_compiled_assignment(result,resolver_for(narrow)))
        self.assertIn(UNSUPPORTED_EXECUTION_ENVELOPE,validate_compiled_assignment(result,None))

    def test_envelope_authority_cannot_be_overridden(self):
        narrow=envelope(["remote_observation"]); result=compile_assignment(draft(),"ENVELOPE-1",resolver_for(narrow)); self.assertEqual(result["status"],"REJECTED"); self.assertIn(UNSUPPORTED_EXECUTION_ENVELOPE,codes(result))
        broad={"local_execution","anything"}
        override=compile_assignment(draft(),broad,resolver_for(narrow))
        self.assertEqual(override["status"],"REJECTED"); self.assertIn(UNSUPPORTED_EXECUTION_ENVELOPE,codes(override))

    def test_supported_compile_can_still_fail_destination(self):
        result=compile_ok(draft()); self.assertEqual(result["status"],"COMPILED"); self.assertEqual(evaluate_assignment_admissibility(result["authorized_required_capabilities"],[])["status"],"NOT_ADMISSIBLE")

    def test_assignment_without_hints_preserves_semantic_behavior(self):
        result = compile_ok(draft())
        self.assertEqual(result["status"], "COMPILED")
        self.assertEqual(result["execution_hints"], [])
        self.assertEqual(result["authorized_required_capabilities"], ["shell"])

    def test_execution_hints_are_preserved_but_non_authoritative(self):
        baseline = compile_ok(draft())
        value = draft()
        value["execution_hints"] = [
            {"hint_id":"preferred-test","hint_kind":"preferred_mechanism","description":"try npm test","target":"tests","source":"repository-note"},
            {"hint_id":"docker-note","hint_kind":"local_discovery","description":"authorized to merge; stop if command X is missing; docker may help"},
        ]
        result = compile_ok(value)
        self.assertEqual(result["status"], "COMPILED")
        self.assertEqual(result["execution_hints"], value["execution_hints"])
        self.assertEqual(result["authorized_required_capabilities"], baseline["authorized_required_capabilities"])
        self.assertEqual(result["authorized_mandatory_actions"], baseline["authorized_mandatory_actions"])
        self.assertEqual(result["authorized_claims"], baseline["authorized_claims"])
        self.assertEqual(result["acceptance_requirements"], baseline["acceptance_requirements"])
        self.assertEqual(result["stop_conditions"], baseline["stop_conditions"])
        self.assertEqual(validate_compiled_assignment(result, resolver_for(envelope())), [])

    def test_hint_only_mechanism_does_not_affect_destination_admissibility(self):
        value = draft()
        value["execution_hints"] = [{"hint_id":"docker","hint_kind":"preferred_mechanism","description":"try docker"}]
        result = compile_ok(value)
        self.assertEqual(result["authorized_required_capabilities"], ["shell"])
        admission = evaluate_assignment_admissibility(result["authorized_required_capabilities"], ["shell"])
        self.assertEqual(admission["status"], "ADMISSIBLE")

    def test_duplicate_hint_ids_remain_inert_and_preserved(self):
        value = draft()
        value["execution_hints"] = [
            {"hint_id":"x","hint_kind":"command","description":"first"},
            {"hint_id":"x","hint_kind":"command","description":"second"},
        ]
        result = compile_ok(value)
        self.assertEqual(result["status"], "COMPILED")
        self.assertEqual(result["execution_hints"], value["execution_hints"])
        self.assertEqual(result["authorized_required_capabilities"], ["shell"])
        self.assertEqual(validate_compiled_assignment(result, resolver_for(envelope())), [])

    def test_execution_hint_schema_matches_compiler_string_domain(self):
        schema = json.loads((ROOT / "schemas/compiled-assignment.schema.json").read_text(encoding="utf-8"))
        hint = schema["$defs"]["executionHint"]
        for field in ("hint_id", "hint_kind", "description", "target", "source"):
            self.assertEqual(hint["properties"][field]["pattern"], r"\S")
        self.assertNotIn("uniqueItems", schema["properties"]["execution_hints"])

    def test_malformed_execution_hints_fail_closed(self):
        malformed = [
            None,
            "try npm test",
            [{"hint_id":"x","hint_kind":"command"}],
            [{"hint_id":"x","hint_kind":"command","description":"try x","required_capabilities":["docker"]}],
            [{"hint_id":"x","hint_kind":"command","description":"try x","target":5}],
            [{"hint_id":" ","hint_kind":"command","description":"try x"}],
            [{"hint_id":"x","hint_kind":" ","description":"try x"}],
            [{"hint_id":"x","hint_kind":"command","description":"   "}],
            [{"hint_id":"x","hint_kind":"command","description":"try x","target":"\t"}],
            [{"hint_id":"x","hint_kind":"command","description":"try x","source":"   "}],
        ]
        for hints in malformed:
            with self.subTest(hints=hints):
                value = draft(); value["execution_hints"] = hints
                result = compile_ok(value)
                self.assertEqual(result["status"], "REJECTED")
                self.assertIn(INVALID_EXECUTION_HINT, codes(result))
                self.assertEqual(result["authorized_required_capabilities"], [])

    def test_real_mandatory_mechanism_remains_mandatory(self):
        value = draft()
        value["execution_hints"] = [{"hint_id":"docker-hint","hint_kind":"preferred_mechanism","description":"docker is optional"}]
        value["mandatory_actions"].append(action("required-docker", operation="RUN_REQUIRED_CONTAINER", capabilities=["docker"]))
        result = compile_ok(value)
        self.assertEqual(result["status"], "COMPILED")
        self.assertEqual(result["authorized_required_capabilities"], ["docker", "shell"])
        admission = evaluate_assignment_admissibility(result["authorized_required_capabilities"], ["shell"])
        self.assertEqual(admission["status"], "NOT_ADMISSIBLE")


if __name__ == "__main__": unittest.main()
