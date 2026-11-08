from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_admissibility_record,
    validate_assignment_execution_contract,
    validate_capability_profile,
    validate_execution_route,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    profile = {
        "artifact_type": "CAPABILITY_PROFILE",
        "artifact_id": "CAP-1",
        "produced_by_role": "control-director",
        "assignment_id": None,
        "input_state_ref": "state-1",
        "status": "CURRENT",
        "provenance": ["local-probe"],
        "related_artifacts": ["EVIDENCE-1"],
        "destination_id": "agent-1",
        "runtime_identity": "runtime-1",
        "surface_class": "REMOTE_DEV_ENV",
        "workspace_scope_ref": "ext-scope:runtime:test",
        "readiness": "READY",
        "evidence_channels": ["terminal_stdout", "unit_test_result", "durable_artifact_ref"],
        "available_capabilities": ["shell", "python_runtime", "repository_remote_read", "durable_artifact_write"],
        "unavailable_capabilities": ["outbound_network"],
        "capability_evidence": [
            {"capability": "shell", "evidence_ref": "EVIDENCE-1"},
            {"capability": "python_runtime", "evidence_ref": "EVIDENCE-1"},
            {"capability": "repository_remote_read", "evidence_ref": "EVIDENCE-1"},
            {"capability": "durable_artifact_write", "evidence_ref": "EVIDENCE-1"},
        ],
        "evidence_artifacts": [{
            "artifact_type": "CAPABILITY_EVIDENCE",
            "produced_by_role": "capability-probe",
            "assignment_id": None,
            "input_state_ref": "probe:local",
            "provenance": ["deterministic local probe"],
            "related_artifacts": ["runtime-1"],
            "observation_method": "local runtime probe",
            "created_from": "probe-run-1",
            "artifact_id": "EVIDENCE-1",
            "status": "RESOLVED",
            "runtime_identity": "runtime-1",
            "capabilities": ["shell", "python_runtime", "repository_remote_read", "durable_artifact_write"],
            "observed_at": "2026-01-01T00:00:00Z",
            "valid_until": "2999-01-01T00:00:00Z",
        }],
        "freshness_boundary": {
            "observed_at": "2026-01-01T00:00:00Z",
            "valid_until": "2999-01-01T00:00:00Z",
        },
        "limitations": [],
    }
    record = {
        "artifact_type": "ASSIGNMENT_ADMISSIBILITY",
        "artifact_id": "ADM-1",
        "produced_by_role": "control-director",
        "assignment_id": None,
        "input_state_ref": "state-1",
        "status": "ADMISSIBLE",
        "provenance": ["CAP-1"],
        "related_artifacts": ["CAP-1"],
        "assignment_draft_id": "DRAFT-1",
        "compiled_assignment_ref": "COMPILED-1",
        "destination_id": "agent-1",
        "runtime_identity": "runtime-1",
        "capability_profile_ref": "CAP-1",
        "route_ref": "ROUTE-1",
        "mandatory_actions": [{
            "action_id": "run_tests",
            "required_capabilities": ["shell", "python_runtime"],
            "evidence_path": "python -m unittest",
        }],
        "required_capabilities": ["shell", "python_runtime"],
        "available_capabilities": ["shell", "python_runtime", "repository_remote_read", "durable_artifact_write"],
        "unsatisfied_required_capabilities": [],
        "mandatory_evidence_paths": ["python -m unittest"],
        "execution_mode": "local",
        "transition_proof": {
            "proof_class": "ASSIGNMENT_ADMISSION",
            "proof_status": "PROVEN",
            "assignment_ref": "ASSIGN-1",
            "admissibility_ref": "ADM-1",
            "destination_id": "agent-1",
            "runtime_identity": "runtime-1",
            "dependency_bindings": [{"dependency_ref": "state-1", "proven_identity": "state-1"}],
        },
    }
    assignment = {
        "artifact_type": "ASSIGNMENT",
        "artifact_id": "ASSIGN-1",
        "produced_by_role": "control-director",
        "assignment_id": "ASSIGN-1",
        "input_state_ref": "state-1",
        "status": "ISSUED",
        "provenance": ["ADM-1"],
        "related_artifacts": ["ADM-1", "CAP-1"],
        "objective": "Run the prescribed verification.",
        "authority": ["OWNER/K0"],
        "scope": {
            "allowed": ["run prescribed verification"],
            "forbidden": ["repair code"],
        },
        "acceptance": ["required verification evidence is produced"],
        "stop_conditions": ["runtime drift invalidates the admitted execution route"],
        "result_to": "agent-1",
        "execution_contract": {
            "assignment_draft_ref": "DRAFT-1",
            "compiled_assignment_ref": "COMPILED-1",
            "destination_id": "agent-1",
            "runtime_identity": "runtime-1",
            "capability_profile_ref": "CAP-1",
            "admissibility_ref": "ADM-1",
            "route_ref": "ROUTE-1",
            "proof_status": "PROVEN",
            "required_capabilities": ["shell", "python_runtime"],
            "unsatisfied_required_capabilities": [],
            "mandatory_evidence_paths": ["python -m unittest"],
            "execution_mode": "local",
        },
    }
    return assignment, record, profile


def compiled_for(record, capabilities=None):
    capabilities = list(record["required_capabilities"] if capabilities is None else capabilities)
    action = {"action_id":"run_tests", "claim_ref":"claim-tests", "responsibility":"EXECUTOR", "operation":"RUN_TESTS", "obligation_class":"local_execution", "context_fact_ref":None, "required_capabilities":capabilities, "evidence_path":"python -m unittest"}
    return {
        "artifact_type":"COMPILED_ASSIGNMENT", "artifact_id":record["compiled_assignment_ref"],
        "produced_by_role":"control-director", "assignment_id":None, "input_state_ref":"state-1",
        "status":"COMPILED", "provenance":["DRAFT-1"], "related_artifacts":["DRAFT-1"],
        "assignment_draft_ref":record["assignment_draft_id"], "authority_class":"FROZEN_CANDIDATE",
        "authorized_claims":[{"claim_id":"claim-tests","claim_kind":"TASK_OUTCOME","authority_source":"RESOLVER_BOUND","target_ref":"acceptance:tests","responsibility":"EXECUTOR","independent_verification_required":False,"classification":"runtime_resolved"}],
        "immutable_invariants":[], "runtime_resolved_invariants":[], "context_facts":[],
        "executor_responsibilities":[action], "control_responsibilities":[], "platform_responsibilities":[],
        "acceptance_requirements":[{"requirement_id":"tests"}], "evidence_requirements":[], "stop_conditions":[],
        "supported_execution_envelope_ref":"ENVELOPE-1", "supported_execution_envelope_status":"SUPPORTED", "authorized_mandatory_actions":[action], "authorized_evidence_requirements":[],
        "authorized_required_capabilities":capabilities, "compilation_status":"COMPILED", "compilation_errors":[],
    }

def envelope_resolver(ref):
    if ref != "ENVELOPE-1": return None
    return {"artifact_type":"EXECUTION_ENVELOPE","artifact_id":"ENVELOPE-1","produced_by_role":"control-director","assignment_id":None,"input_state_ref":"state-1","status":"CURRENT","provenance":["portfolio"],"related_artifacts":[],"supported_obligation_classes":["local_execution"]}


def governed_chain(assignment, record, profile):
    evidence = profile["evidence_artifacts"][0]
    resolver = lambda ref: evidence if ref == evidence["artifact_id"] else None
    route = {
        "artifact_type":"EXECUTION_ROUTE", "artifact_id":"ROUTE-1", "produced_by_role":"control-director",
        "assignment_id":None, "input_state_ref":"state-1", "status":"ADMISSIBLE", "provenance":["CAP-1"],
        "related_artifacts":["CAP-1"], "assignment_draft_id":"DRAFT-1", "final_result":{"segment_ref":"durable","destination_id":"agent-1"},
        "segments":[
            {"segment_id":"delivery","route_role":"CANDIDATE_DELIVERY","destination_id":"agent-1","runtime_identity":"runtime-1","capability_profile_ref":"CAP-1","required_capabilities":["repository_remote_read"],"execution_mode":"local"},
            {"segment_id":"execute","route_role":"EXECUTION_VERIFICATION","destination_id":"agent-1","runtime_identity":"runtime-1","capability_profile_ref":"CAP-1","required_capabilities":["shell","python_runtime"],"execution_mode":"local"},
            {"segment_id":"durable","route_role":"DURABLE_EVIDENCE_CONTROL","destination_id":"agent-1","runtime_identity":"runtime-1","capability_profile_ref":"CAP-1","required_capabilities":["durable_artifact_write"],"execution_mode":"local"},
        ],
        "handoffs":[
            {"from_segment":"delivery","to_segment":"execute","source_required_capabilities":[],"target_required_capabilities":[],"internal_required_capabilities":["repository_remote_read"],"same_surface":True},
            {"from_segment":"execute","to_segment":"durable","source_required_capabilities":[],"target_required_capabilities":[],"internal_required_capabilities":["durable_artifact_write"],"same_surface":True},
        ],
    }
    return resolver, route


def validate_chain(assignment, record, profile):
    resolver, route = governed_chain(assignment, record, profile)
    return validate_assignment_execution_contract(assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)


class ExecutabilityContractTest(unittest.TestCase):
    def test_governed_evidence_resolution_boundary(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        resolver, route = governed_chain(assignment, record, profile)
        self.assertTrue(validate_assignment_execution_contract(assignment, record, profile, None, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver))
        self.assertTrue(validate_assignment_execution_contract(assignment, record, profile, lambda ref: None, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver))
        def exploding(ref): raise RuntimeError("probe unavailable")
        self.assertTrue(any("failed closed" in e for e in validate_assignment_execution_contract(assignment, record, profile, exploding, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        wrong = deepcopy(profile["evidence_artifacts"][0]); wrong["artifact_id"] = "WRONG"
        self.assertTrue(any("identity mismatch" in e for e in validate_assignment_execution_contract(assignment, record, profile, lambda ref: wrong, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        missing_provenance = deepcopy(profile["evidence_artifacts"][0]); del missing_provenance["observation_method"]
        self.assertTrue(any("observation_method" in e for e in validate_assignment_execution_contract(assignment, record, profile, lambda ref: missing_provenance, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        disagreement = deepcopy(profile["evidence_artifacts"][0]); disagreement["created_from"] = "different-run"
        self.assertTrue(any("disagrees" in e for e in validate_assignment_execution_contract(assignment, record, profile, lambda ref: disagreement, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        self.assertEqual(validate_assignment_execution_contract(assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver), [])

    def test_route_adversarial_matrix(self) -> None:
        assignment, record, profile = deepcopy(valid_chain()); resolver, route = governed_chain(assignment, record, profile)
        profiles = {"CAP-1": profile}
        self.assertEqual(validate_execution_route(route, profiles, resolver), [])
        multi = deepcopy(route); multi_profiles = {}; evidence = {}
        for index, (segment, suffix) in enumerate(zip(multi["segments"], ["D", "X", "C"])):
            candidate = deepcopy(profile); candidate["artifact_id"] = f"CAP-{suffix}"; candidate["destination_id"] = f"agent-{suffix}"; candidate["runtime_identity"] = f"runtime-{suffix}"
            artifact = candidate["evidence_artifacts"][0]; artifact["artifact_id"] = f"EVIDENCE-{suffix}"; artifact["runtime_identity"] = f"runtime-{suffix}"
            candidate["related_artifacts"] = [artifact["artifact_id"]]
            for claim in candidate["capability_evidence"]: claim["evidence_ref"] = artifact["artifact_id"]
            segment["destination_id"] = candidate["destination_id"]; segment["runtime_identity"] = candidate["runtime_identity"]; segment["capability_profile_ref"] = candidate["artifact_id"]
            multi_profiles[candidate["artifact_id"]] = candidate; evidence[artifact["artifact_id"]] = artifact
        multi["final_result"]["destination_id"] = "agent-C"
        for edge in multi["handoffs"]:
            edge["same_surface"] = False
            edge["internal_required_capabilities"] = []
            edge["source_required_capabilities"] = ["durable_artifact_write"]
            edge["target_required_capabilities"] = ["repository_remote_read"]
        self.assertEqual(validate_execution_route(multi, multi_profiles, evidence.get), [])
        cases = []
        no_publish = deepcopy(multi); no_publish["handoffs"][0]["source_required_capabilities"] = ["repository_remote_write"]; cases.append((no_publish,multi_profiles,evidence.get))
        no_receive = deepcopy(multi); no_receive["handoffs"][0]["target_required_capabilities"] = ["durable_artifact_read"]; cases.append((no_receive,multi_profiles,evidence.get))
        source_only = deepcopy(multi); source_only["handoffs"][0]["target_required_capabilities"] = []; cases.append((source_only,multi_profiles,evidence.get))
        target_only = deepcopy(multi); target_only["handoffs"][0]["source_required_capabilities"] = []; cases.append((target_only,multi_profiles,evidence.get))
        missing_edge = deepcopy(route); missing_edge["handoffs"] = missing_edge["handoffs"][:1]; cases.append(missing_edge)
        runtime_mismatch = deepcopy(route); runtime_mismatch["segments"][1]["runtime_identity"] = "other"; cases.append(runtime_mismatch)
        for case in cases:
            bad, case_profiles, case_resolver = case if isinstance(case, tuple) else (case, profiles, resolver)
            with self.subTest(route=bad): self.assertTrue(validate_execution_route(bad, case_profiles, case_resolver))
        bad_assignment = deepcopy(assignment); bad_assignment["result_to"] = "elsewhere"
        self.assertTrue(any("result_to" in e for e in validate_assignment_execution_contract(bad_assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        other_draft = deepcopy(route); other_draft["assignment_draft_id"] = "OTHER"
        self.assertTrue(any("assignment_draft_id" in e for e in validate_assignment_execution_contract(assignment, record, profile, resolver, other_draft, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        fake_endpoint = deepcopy(route); fake_endpoint["final_result"]["destination_id"] = "control-layer"
        self.assertTrue(any("durable segment" in e for e in validate_assignment_execution_contract(assignment, record, profile, resolver, fake_endpoint, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        wrong_segment = deepcopy(route); wrong_segment["final_result"]["segment_ref"] = "execute"
        self.assertTrue(any("durable segment" in e for e in validate_assignment_execution_contract(assignment, record, profile, resolver, wrong_segment, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))
        unresolved = deepcopy(route); unresolved["final_result"]["segment_ref"] = "missing"
        self.assertTrue(any("unresolved" in e for e in validate_assignment_execution_contract(assignment, record, profile, resolver, unresolved, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)))

    def test_execution_segment_exact_assignment_binding(self) -> None:
        for field, value in [("destination_id","other"),("runtime_identity","other"),("capability_profile_ref","other")]:
            assignment, record, profile = deepcopy(valid_chain()); resolver, route = governed_chain(assignment, record, profile)
            route["segments"][1][field] = value
            errors = validate_assignment_execution_contract(assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)
            self.assertTrue(any(f"execution segment {field} mismatch" in error for error in errors), errors)

    def test_timestamp_strict_offsets_and_overflow_fail_closed(self) -> None:
        for valid in ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00+05:30", "2026-01-01T00:00:00-05:00"]:
            assignment, record, profile = deepcopy(valid_chain()); resolver, route = governed_chain(assignment, record, profile)
            profile["freshness_boundary"]["observed_at"] = valid
            profile["evidence_artifacts"][0]["observed_at"] = valid
            self.assertFalse(any("timestamp" in e or "offset" in e for e in validate_assignment_execution_contract(assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)), valid)
        for invalid in ["2026-01-01T00:00:00", "2026-01-01T00:00:00+14:99", "2026-01-01T00:00:00+24:00", "2026-01-01T00:00:00+99:99", "2026-01-01T00:60:00Z", "9999-12-31T23:59:59-23:59"]:
            assignment, record, profile = deepcopy(valid_chain()); resolver, route = governed_chain(assignment, record, profile)
            profile["freshness_boundary"]["observed_at"] = invalid
            errors = validate_assignment_execution_contract(assignment, record, profile, resolver, route, compiled_assignment=compiled_for(record), execution_envelope_resolver=envelope_resolver)
            self.assertTrue(errors, invalid)
    def test_required_subset_available_is_admissible(self) -> None:
        result = evaluate_assignment_admissibility(["shell"], ["shell", "python_runtime"])
        self.assertEqual(result["status"], "ADMISSIBLE")
        self.assertEqual(result["unsatisfied_required_capabilities"], [])

    def test_missing_local_runtime_is_not_admissible(self) -> None:
        result = evaluate_assignment_admissibility(
            ["repository_remote_read", "repository_local_checkout", "shell", "python_runtime"],
            ["repository_remote_read", "repository_remote_write", "connector:github"],
        )
        self.assertEqual(result["status"], "NOT_ADMISSIBLE")
        self.assertEqual(
            result["unsatisfied_required_capabilities"],
            ["python_runtime", "repository_local_checkout", "shell"],
        )

    def test_complete_chain_passes(self) -> None:
        self.assertEqual(validate_chain(*valid_chain()), [])

    def test_recompiled_assignment_invalidates_old_admissibility(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        compiled = compiled_for(record)
        compiled["artifact_id"] = "COMPILED-2"
        resolver, route = governed_chain(assignment, record, profile)
        errors = validate_assignment_execution_contract(
            assignment, record, profile, resolver, route, compiled_assignment=compiled
        )
        self.assertTrue(any("compiled_assignment_ref mismatch" in error for error in errors), errors)

    def test_compiled_capabilities_may_be_strict_subset_of_final_requirements(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        resolver, route = governed_chain(assignment, record, profile)
        compiled = compiled_for(record, ["shell"])
        errors = validate_assignment_execution_contract(
            assignment, record, profile, resolver, route,
            compiled_assignment=compiled, execution_envelope_resolver=envelope_resolver,
        )
        self.assertEqual(errors, [])

    def test_compiled_capability_cannot_disappear_downstream(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["mandatory_actions"][0]["required_capabilities"] = ["shell"]
        record["required_capabilities"] = ["shell"]
        assignment["execution_contract"]["required_capabilities"] = ["shell"]
        resolver, route = governed_chain(assignment, record, profile)
        route["segments"][1]["required_capabilities"] = ["shell"]
        errors = validate_assignment_execution_contract(
            assignment, record, profile, resolver, route,
            compiled_assignment=compiled_for(record, ["shell", "python_runtime"]),
            execution_envelope_resolver=envelope_resolver,
        )
        self.assertTrue(any("drops compiled assignment capabilities" in error for error in errors), errors)

    def test_unaccounted_final_capability_remains_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["required_capabilities"].append("repository_local_checkout")
        errors = validate_chain(assignment, record, profile)
        self.assertTrue(any("union of mandatory action requirements" in error for error in errors), errors)

    def test_accounted_but_unavailable_final_capability_remains_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["mandatory_actions"][0]["required_capabilities"].append("repository_local_checkout")
        record["required_capabilities"].append("repository_local_checkout")
        record["unsatisfied_required_capabilities"] = ["repository_local_checkout"]
        record["status"] = "NOT_ADMISSIBLE"
        errors = validate_chain(assignment, record, profile)
        self.assertTrue(any("non-ADMISSIBLE" in error or "unsatisfied" in error for error in errors), errors)

    def assert_contract_rejected(
        self,
        assignment: dict[str, object],
        record: dict[str, object],
        profile: dict[str, object],
        fragment: str,
    ) -> None:
        errors = validate_chain(assignment, record, profile)
        self.assertTrue(any(fragment in error for error in errors), msg=str(errors))

    def test_assignment_chain_mismatches_rejected(self) -> None:
        mutations = [
            ("assignment_draft_ref", "UNRELATED", "assignment_draft_ref mismatch"),
            ("admissibility_ref", "ADM-X", "admissibility_ref mismatch"),
            ("capability_profile_ref", "CAP-X", "capability_profile_ref mismatch"),
            ("destination_id", "agent-X", "assignment destination mismatch"),
            ("runtime_identity", "runtime-X", "assignment runtime_identity mismatch"),
            ("required_capabilities", ["shell"], "required_capabilities do not match"),
            ("mandatory_evidence_paths", ["different"], "mandatory_evidence_paths do not match"),
            ("execution_mode", "remote", "execution_mode does not match"),
        ]
        for field, value, fragment in mutations:
            with self.subTest(field=field):
                assignment, record, profile = deepcopy(valid_chain())
                assignment["execution_contract"][field] = value  # type: ignore[index]
                self.assert_contract_rejected(assignment, record, profile, fragment)

    def test_missing_or_blank_draft_binding_rejected(self) -> None:
        for value in [None, ""]:
            assignment, record, profile = deepcopy(valid_chain())
            if value is None:
                del assignment["execution_contract"]["assignment_draft_ref"]  # type: ignore[index]
            else:
                assignment["execution_contract"]["assignment_draft_ref"] = value  # type: ignore[index]
            self.assert_contract_rejected(assignment, record, profile, "assignment_draft_ref")

    def test_schema_required_assignment_surface_rejected_when_missing(self) -> None:
        required_fields = [
            "produced_by_role",
            "input_state_ref",
            "status",
            "provenance",
            "related_artifacts",
            "objective",
            "authority",
            "scope",
            "acceptance",
            "stop_conditions",
            "result_to",
        ]
        for field in required_fields:
            with self.subTest(field=field):
                assignment, record, profile = deepcopy(valid_chain())
                del assignment[field]
                self.assert_contract_rejected(assignment, record, profile, f"assignment.{field}")

    def test_non_admissible_and_nonempty_unsatisfied_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["status"] = "NOT_ADMISSIBLE"
        record["available_capabilities"] = ["shell"]
        record["unsatisfied_required_capabilities"] = ["python_runtime"]
        profile["available_capabilities"] = ["shell"]
        profile["capability_evidence"] = [{"capability": "shell", "evidence_ref": "EVIDENCE-1"}]
        assignment["execution_contract"]["unsatisfied_required_capabilities"] = ["python_runtime"]  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "non-ADMISSIBLE")
        self.assert_contract_rejected(assignment, record, profile, "unsatisfied required capabilities")

    def test_profile_overlap_and_missing_evidence_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["unavailable_capabilities"] = ["shell"]
        self.assert_contract_rejected(assignment, record, profile, "both available and unavailable")
        assignment, record, profile = deepcopy(valid_chain())
        profile["capability_evidence"] = []
        self.assert_contract_rejected(assignment, record, profile, "missing evidence")

    def test_incomplete_profile_rejected(self) -> None:
        for field in [
            "artifact_type",
            "produced_by_role",
            "assignment_id",
            "input_state_ref",
            "status",
            "provenance",
            "related_artifacts",
            "runtime_identity",
            "surface_class",
            "workspace_scope_ref",
            "readiness",
            "evidence_channels",
            "freshness_boundary",
            "limitations",
        ]:
            with self.subTest(field=field):
                assignment, record, profile = deepcopy(valid_chain())
                del profile[field]
                self.assertTrue(validate_chain(assignment, record, profile))

    def test_expired_profile_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["freshness_boundary"]["valid_until"] = "2000-01-01T00:00:00Z"  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "expired")

    def test_evidence_beginning_after_profile_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["evidence_artifacts"][0]["observed_at"] = "2026-01-01T00:00:01Z"  # type: ignore[index]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "begins after the profile freshness boundary",
        )

    def test_future_evidence_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["evidence_artifacts"][0]["observed_at"] = "2998-01-01T00:00:00Z"  # type: ignore[index]
        self.assert_contract_rejected(assignment, record, profile, "starts in the future")

    def test_unresolved_and_fake_evidence_rejected(self) -> None:
        for evidence_ref in ["UNKNOWN-EVIDENCE", "fabricated"]:
            assignment, record, profile = deepcopy(valid_chain())
            profile["capability_evidence"][0]["evidence_ref"] = evidence_ref  # type: ignore[index]
            self.assert_contract_rejected(assignment, record, profile, "unresolved")

    def test_unreferenced_invalid_evidence_artifact_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["evidence_artifacts"].append({"artifact_id": "BROKEN"})  # type: ignore[union-attr]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "evidence_artifacts[1].artifact_type",
        )

    def test_schema_unique_capability_lists_rejected_when_duplicated(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        profile["available_capabilities"] = ["shell", "shell", "python_runtime"]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "available_capabilities must not contain duplicates",
        )
        assignment, record, profile = deepcopy(valid_chain())
        profile["evidence_artifacts"][0]["capabilities"] = ["shell", "shell", "python_runtime"]  # type: ignore[index]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "evidence_artifacts[0].capabilities must not contain duplicates",
        )
        assignment, record, profile = deepcopy(valid_chain())
        record["required_capabilities"] = ["shell", "shell", "python_runtime"]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "required_capabilities must not contain duplicates",
        )

    def test_profile_admissibility_runtime_and_available_mismatch_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["runtime_identity"] = "runtime-X"
        self.assert_contract_rejected(assignment, record, profile, "runtime identity mismatch")
        assignment, record, profile = deepcopy(valid_chain())
        record["available_capabilities"] = ["shell"]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "do not match cited capability profile",
        )

    def test_record_requirement_derivation_rejected(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        record["mandatory_actions"][0]["required_capabilities"] = ["shell"]  # type: ignore[index]
        self.assert_contract_rejected(
            assignment,
            record,
            profile,
            "union of mandatory action requirements",
        )

    def test_cli_requires_complete_arguments(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/executability.py", "--assignment", "a.json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--assignment requires --record and --profile", result.stderr)

    def test_cli_valid_and_invalid_complete_chain(self) -> None:
        assignment, record, profile = valid_chain()
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            resolver, route = governed_chain(assignment, record, profile)
            for name, value in [
                ("assignment", assignment),
                ("record", record),
                ("profile", profile),
                ("evidence", profile["evidence_artifacts"]),
                ("route", route),
                ("compiled", compiled_for(record)),
                ("envelope", envelope_resolver("ENVELOPE-1")),
            ]:
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths.append(path)
            command = [
                sys.executable,
                "tools/executability.py",
                "--assignment",
                str(paths[0]),
                "--record",
                str(paths[1]),
                "--profile",
                str(paths[2]),
                "--evidence-bundle",
                str(paths[3]),
                "--route",
                str(paths[4]),
                "--compiled-assignment",
                str(paths[5]),
                "--execution-envelope",
                str(paths[6]),
            ]
            valid = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

            invalid_assignment = deepcopy(assignment)
            del invalid_assignment["objective"]
            paths[0].write_text(json.dumps(invalid_assignment), encoding="utf-8")
            invalid_schema = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(invalid_schema.returncode, 0)
            self.assertIn("assignment.objective", invalid_schema.stdout)

            assignment["execution_contract"]["assignment_draft_ref"] = "UNRELATED"  # type: ignore[index]
            paths[0].write_text(json.dumps(assignment), encoding="utf-8")
            invalid_binding = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(invalid_binding.returncode, 0)
            self.assertIn("assignment_draft_ref mismatch", invalid_binding.stdout)


if __name__ == "__main__":
    unittest.main()
