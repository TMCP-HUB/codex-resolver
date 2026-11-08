from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, getcontext
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.resource_admission import evaluate_resource_admission
from tools.durable_artifact_port import LocalFileDurableReferencePort, RESOLVED
from tools.resource_ledger import AuthorityViolation, InsufficientCapacity, ResourceLedger
from tests.test_resource_governance_contract import schema_accepts

NOW = datetime(2026, 9, 20, 4, 0, tzinfo=timezone.utc)
ODR = "ODR-RG04"


def root(
    gid="G-LEAF", *, ordinary=5, final=0, mode="RESERVABLE_LIMIT",
    authority_type="OWNER_APPROVED_RESOURCE_AUTHORITY", authority_ref=ODR,
):
    capacities = (None, None) if mode == "OBSERVATION_ONLY" else (ordinary, final)
    return {
        "artifact_type": "RESOURCE_GRANT", "artifact_id": gid, "produced_by_role": "control-director",
        "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": "AUTHORIZED",
        "provenance": ["owner:resource-authority"], "related_artifacts": [], "issued_by": "control-director",
        "authority_source": {"authority_type": authority_type, "authority_ref": authority_ref},
        "parent_grant_ref": None,
        "scope": {"scope_ref": "assignment:A-1", "candidate_ref": "candidate:1", "route_ref": "ROUTE-1",
                  "resource_classes": ["MODEL_INFERENCE"]},
        "limits": [{"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                    "ordinary_limit": capacities[0], "finalization_reserve": capacities[1]}],
        "attempt_limit": 3, "valid_until": "2030-01-01T00:00:00Z",
        "finalization_policy": {"protected": True, "allowed_purposes": ["FINAL_ACCOUNTING"]},
    }


def rich_root(gid="G-LEAF"):
    g = root(gid)
    g["scope"]["resource_classes"] = ["MODEL_INFERENCE", "REMOTE_CI"]
    g["limits"].append({"resource_class": "MODEL_INFERENCE", "dimension": "MODEL_CALLS",
                        "limit_mode": "HARD_LIMIT", "ordinary_limit": 7, "finalization_reserve": 1})
    g["finalization_policy"]["allowed_purposes"] = ["FINAL_ACCOUNTING", "CONTROL_HANDOFF"]
    return g


def child(parent, gid="G-LEAF", *, ordinary=5, final=0):
    g = deepcopy(parent)
    g["artifact_id"] = gid
    g["authority_source"] = {"authority_type": "PARENT_RESOURCE_GRANT", "authority_ref": parent["artifact_id"]}
    g["parent_grant_ref"] = parent["artifact_id"]
    g["provenance"] = [parent["artifact_id"]]
    g["limits"] = [{"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": "RESERVABLE_LIMIT",
                    "ordinary_limit": ordinary, "finalization_reserve": final}]
    g["scope"]["resource_classes"] = ["MODEL_INFERENCE"]
    return g


def decision(g=None, **kw):
    g = deepcopy(g or root())
    value = {
        "artifact_type": "OWNER_DECISION_RECORD", "artifact_id": ODR, "produced_by_role": "owner-interface",
        "assignment_id": g["assignment_id"], "input_state_ref": g["input_state_ref"], "status": "RECORDED",
        "provenance": ["OWNER/K0", "decision:resource-authority"], "related_artifacts": [g["artifact_id"]],
        "question_ref": "Q-RG04-RESOURCE-AUTHORITY",
        "options_presented": ["AUTHORIZE_RESOURCE_AUTHORITY", "DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"],
        "selected_option": "AUTHORIZE_RESOURCE_AUTHORITY", "owner_constraints": [],
        "consequences_acknowledged": ["finite-resource-authority"], "authority_role": "OWNER_K0",
        "decision_kind": "OWNER_APPROVED_RESOURCE_AUTHORITY",
        "authorized_resource_grant_ref": g["artifact_id"], "authorized_scope": g["scope"]["scope_ref"],
        "authorized_candidate_ref": g["scope"]["candidate_ref"], "authorized_route_ref": g["scope"]["route_ref"],
        "authorized_resource_classes": deepcopy(g["scope"]["resource_classes"]),
        "authorized_resource_limits": deepcopy(g["limits"]), "authorized_attempt_limit": g["attempt_limit"],
        "authorized_valid_until": g["valid_until"],
        "authorized_finalization_policy": deepcopy(g["finalization_policy"]), "non_transitive": True,
    }
    value.update(kw)
    return value


def item(state="ESTIMATED", *, upper=Decimal("2"), dim="TOKENS"):
    if state == "UNKNOWN":
        return {
            "resource_class": "MODEL_INFERENCE", "dimension": dim, "estimate_state": "UNKNOWN",
            "point_estimate": None, "quantiles": [], "upper_bound": None, "confidence": "UNKNOWN",
            "historical_sample_count": None, "unknown_resource_state": "ESTIMATE_UNKNOWN",
        }
    return {
        "resource_class": "MODEL_INFERENCE", "dimension": dim, "estimate_state": "ESTIMATED",
        "point_estimate": upper, "quantiles": [], "upper_bound": upper, "confidence": "HIGH",
        "historical_sample_count": 9, "unknown_resource_state": "KNOWN",
    }


def estimate(*items, status=None, **kw):
    items = list(items or [item()])
    states = [entry["estimate_state"] for entry in items]
    status = status or (
        "ESTIMATED" if all(entry == "ESTIMATED" for entry in states)
        else "UNKNOWN" if all(entry == "UNKNOWN" for entry in states)
        else "PARTIAL"
    )
    value = {
        "artifact_type": "RESOURCE_ESTIMATE", "artifact_id": "RE-1", "produced_by_role": "resource-estimator",
        "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": status, "provenance": ["basis:1"],
        "related_artifacts": [], "subject_ref": "CA-1", "route_ref": "ROUTE-1",
        "estimator_revision_ref": "rg02:merged", "basis_refs": ["basis:1"], "estimates": deepcopy(items),
    }
    value.update(kw)
    return value


class Reader:
    def __init__(self, grants, available=None, *, fail_grants=(), fail_states=()):
        self.grants = deepcopy(grants)
        self.available = dict(available or {})
        self.fail_grants = set(fail_grants)
        self.fail_states = set(fail_states)
        self.calls = []

    def get_grant(self, gid):
        self.calls.append(("get_grant", gid))
        if gid in self.fail_grants:
            raise OSError("backend")
        return deepcopy(self.grants.get(gid))

    def get_resource_state(self, gid, resource_class, dimension):
        self.calls.append(("get_resource_state", gid, resource_class, dimension))
        if (gid, resource_class, dimension) in self.fail_states:
            raise OSError("backend")
        available = Decimal(str(self.available[(gid, resource_class, dimension)]))
        mode = next(
            entry["limit_mode"] for entry in self.grants[gid]["limits"]
            if (entry["resource_class"], entry["dimension"]) == (resource_class, dimension)
        )
        return {
            "grant_id": gid, "resource_class": resource_class, "dimension": dimension, "limit_mode": mode,
            "spend_authority": True,
            "ordinary": {"authorized": available, "reserved": Decimal(0), "committed": Decimal(0), "available": available},
            "finalization": {"authorized": Decimal(0), "reserved": Decimal(0), "committed": Decimal(0), "available": Decimal(0)},
            "exhaustion_state": "NOT_EXHAUSTED", "grant_expired": False,
        }

    def register_grant(self, *args, **kwargs):
        raise AssertionError("resource admission attempted mutation")

    register_child_grant = reserve = commit = release = claim_attempt = register_grant


def reader(g=None, available=5):
    g = g or root()
    states = {
        (g["artifact_id"], entry["resource_class"], entry["dimension"]): available
        for entry in g["limits"] if entry["limit_mode"] != "OBSERVATION_ONLY"
    }
    return Reader({g["artifact_id"]: g}, states)


def run(r, *, g=None, e=None, auth=None, **kw):
    g = root() if g is None else g
    args = dict(
        artifact_id="RA-1", assignment_id="A-1", input_state_ref="STATE-1",
        compiled_assignment={"artifact_id": "CA-1"},
        assignment_admissibility={"artifact_type": "ASSIGNMENT_ADMISSIBILITY", "artifact_id": "AA-1", "status": "ADMISSIBLE"},
        route_ref="ROUTE-1", state_identity="candidate:1", resource_estimate_ref="RE-1",
        resource_estimate=estimate() if e is None else e, resource_grant_ref="G-LEAF", resource_grant=g,
        resource_state_reader=r, authority_resolver=({ODR: decision(g)} if auth is None else auth).get,
        availability_evidence_refs=(), unclassified_metered_side_effect_refs=(), now=NOW,
    )
    args.update(kw)
    return evaluate_resource_admission(**args)


def assert_owner_block(testcase, g, d=None, *, auth=None, reason="AUTHORITY_SOURCE_UNRESOLVED"):
    authority_map = auth if auth is not None else {ODR: (decision(g) if d is None else d)}
    out = run(reader(g), g=g, auth=authority_map)
    testcase.assertIn(reason, out["blocking_reasons"])
    testcase.assertEqual(out["unknown_resource_state"], "KNOWN")
    return out


def condition_review():
    # The fact was established by a different assignment from the resource grant.
    evidence = {"artifact_type": "STATE_OBSERVATION", "artifact_id": "AUDIT-STATE",
                "produced_by_role": "control-director", "input_state_ref": "AUDIT-INPUT",
                "status": "CURRENT", "provenance": ["audit:source"], "related_artifacts": [],
                "state_identity": "audit:passed", "authority_scope": "audit:scope"}
    result = {"artifact_type": "EXECUTOR_RESULT", "artifact_id": "AUDIT-RESULT", "produced_by_role": "executor",
              "assignment_id": "AUDIT-ASSIGNMENT", "input_state_ref": "AUDIT-INPUT", "status": "COMPLETE",
              "provenance": ["audit:source"], "related_artifacts": ["AUDIT-STATE"],
              "resulting_state_refs": ["AUDIT-STATE"], "evidence_refs": ["AUDIT-STATE"],
              "deferred_findings": [], "limitations": [],
              "claims": [{"claim_id": "AUDIT-PASSED", "claim": "Audit passed", "evidence_refs": ["AUDIT-STATE"]}]}
    review = {"artifact_type": "DIRECTOR_DECISION", "artifact_id": "AUDIT-REVIEW", "produced_by_role": "control-director",
              "assignment_id": "AUDIT-ASSIGNMENT", "input_state_ref": "AUDIT-INPUT", "status": "RECORDED",
              "provenance": ["AUDIT-RESULT"], "related_artifacts": ["AUDIT-STATE"],
              "executor_result_ref": "AUDIT-RESULT", "verification_result_ref": None,
              "control_state": "COMPLETE", "decision": "Audit outcome reviewed", "next_owner": None,
              "director_review": {
                  "review_type": "DIRECTOR_REVIEW", "assignment_id": "AUDIT-ASSIGNMENT",
                  "executor_result_ref": "AUDIT-RESULT", "input_state_ref": "AUDIT-INPUT",
                  "verified_state_identity": "audit:passed", "status": "CONFIRMED",
                  "claim_verdicts": [{"claim_id": "AUDIT-PASSED", "verdict": "CONFIRMED",
                                      "evidence_refs": ["AUDIT-STATE"]}]}}
    return {item["artifact_id"]: item for item in (evidence, result, review)}


def condition_case(grant, *, constraints=None, qualifications=None):
    source = "Use this budget after the audit passes."
    original = decision(grant, owner_constraints=[source], resource_interpretation={
        "source_text": source, "unresolved_constraints": list(["Audit passes."] if constraints is None else constraints),
        "unresolved_qualifications": list(qualifications or []),
    })
    view = deepcopy(original); view["artifact_id"] = "INTERPRETATION-1"; view["related_artifacts"].append(ODR)
    view["resource_interpretation"]["unresolved_constraints"] = []
    view["resource_interpretation"]["unresolved_qualifications"] = []
    view["resource_interpretation"]["condition_resolutions"] = [{
        "condition_kind": "CONSTRAINT", "condition_index": 0, "review_ref": "AUDIT-REVIEW",
        "claim_id": "AUDIT-PASSED", "evidence_refs": ["AUDIT-STATE"],
    }]
    return original, view, {ODR: original, "INTERPRETATION-1": view, **condition_review()}


class ResourceAdmissionTest(unittest.TestCase):
    def test_recorded_condition_can_be_resolved_with_existing_review_and_evidence(self):
        grant = root()
        original, view, authority = condition_case(grant)
        before = deepcopy(original)
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/owner-decision-record.schema.json").read_text())
        self.assertTrue(schema_accepts(view, schema))
        with tempfile.TemporaryDirectory() as td:
            ledger = ResourceLedger(Path(td) / "shared.sqlite3"); ledger.initialize()
            registered = ledger.register_grant(grant)
            ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 4, "R-1", "OP-1", "KEY-1", now=NOW)
            self.assertEqual(run(ledger, g=grant, auth=authority, e=estimate(item(upper=1)),
                resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
            out = run(ledger, g=grant, auth=authority, e=estimate(item(upper=2)),
                      resource_interpretation_ref="INTERPRETATION-1")
            self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", out["blocking_reasons"])
            self.assertEqual(ledger.get_grant("G-LEAF"), registered)
            self.assertEqual(original, before)

    def test_owner_interface_can_record_direct_condition_assessment_without_review(self):
        grant = root()
        original, view, authority = condition_case(grant)
        original_before = deepcopy(original)
        link = view["resource_interpretation"]["condition_resolutions"][0]
        del link["review_ref"]; del link["claim_id"]
        link["note"] = "The responsible intake established the audit result from its source."
        authority = {ODR: original, "INTERPRETATION-1": view}
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/owner-decision-record.schema.json").read_text())
        self.assertTrue(schema_accepts(view, schema))
        for field in ("review_ref", "claim_id"):
            incomplete = deepcopy(view)
            incomplete["resource_interpretation"]["condition_resolutions"][0][field] = "only-one"
            self.assertFalse(schema_accepts(incomplete, schema))
        with tempfile.TemporaryDirectory() as td:
            ledger = ResourceLedger(Path(td) / "shared.sqlite3"); ledger.initialize()
            registered = ledger.register_grant(grant)
            ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 4, "R-1", "OP-1", "KEY-1", now=NOW)
            self.assertEqual(run(ledger, g=grant, auth=authority, e=estimate(item(upper=1)),
                resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
            self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", run(ledger, g=grant, auth=authority,
                e=estimate(item(upper=2)), resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
            self.assertEqual(ledger.get_grant("G-LEAF"), registered)
            self.assertEqual(original, original_before)
            link.pop("note")
            self.assertEqual(run(ledger, g=grant, auth=authority, e=estimate(item(upper=1)),
                resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        link["evidence_refs"] = []
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])

    def test_condition_requires_a_confirmed_matching_review_when_selected(self):
        grant = root()
        _, _, authority = condition_case(grant)
        cases = []
        a = deepcopy(authority); del a["AUDIT-REVIEW"]; cases.append(a)
        a = deepcopy(authority); del a["AUDIT-RESULT"]; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"] = {"artifact_id": "AUDIT-REVIEW", "status": "CONFIRMED"}; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["director_review"]["claim_verdicts"][0]["verdict"] = "QUALIFIED"; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["director_review"]["status"] = "BLOCKED"; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["director_review"]["status"] = "QUALIFIED"; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["director_review"]["claim_verdicts"][0]["claim_id"] = "OTHER"; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["director_review"]["claim_verdicts"][0]["evidence_refs"] = ["OTHER"]; cases.append(a)
        a = deepcopy(authority); a["AUDIT-RESULT"]["assignment_id"] = "WRONG-AUDIT"; cases.append(a)
        a = deepcopy(authority); a["AUDIT-REVIEW"]["assignment_id"] = "WRONG-DECISION"; cases.append(a)
        a = deepcopy(authority)
        candidate = {"kind": "PULL_REQUEST", "repository": "example/repo", "ref": 1, "head_sha": "a" * 40}
        a["AUDIT-RESULT"]["published_candidate"] = candidate
        a["AUDIT-REVIEW"]["director_review"]["verified_candidate"] = {**candidate, "head_sha": "b" * 40}
        cases.append(a)
        a = deepcopy(authority); a["INTERPRETATION-1"]["resource_interpretation"]["condition_resolutions"][0]["condition_index"] = 1; cases.append(a)
        a = deepcopy(authority); a["INTERPRETATION-1"]["resource_interpretation"]["condition_resolutions"][0]["condition_kind"] = []; cases.append(a)
        a = deepcopy(authority); del a["INTERPRETATION-1"]["resource_interpretation"]["condition_resolutions"][0]["claim_id"]; cases.append(a)
        a = deepcopy(authority); del a["INTERPRETATION-1"]["resource_interpretation"]["condition_resolutions"][0]["review_ref"]; cases.append(a)
        for authority_map in cases:
            with self.subTest(authority_map=authority_map):
                out = run(reader(grant), g=grant, auth=authority_map, resource_interpretation_ref="INTERPRETATION-1")
                self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", out["blocking_reasons"])

        # The review's task is independent of the budget's task; the Director's
        # current state need not equal the Executor's earlier input state.
        authority["AUDIT-REVIEW"]["input_state_ref"] = "AUDIT-CURRENT-STATE"
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        authority["AUDIT-REVIEW"]["director_review"]["verified_candidate"] = candidate
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        authority["AUDIT-RESULT"]["published_candidate"] = candidate
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")

    def test_each_original_condition_identity_requires_a_link(self):
        grant = root()
        _, view, authority = condition_case(grant, constraints=["Same condition", "Same condition"],
                                            qualifications=["Same condition"])
        link = view["resource_interpretation"]["condition_resolutions"][0]
        del link["review_ref"]; del link["claim_id"]
        view["resource_interpretation"]["condition_resolutions"].append({**link, "condition_index": 1})
        blocked = run(reader(grant), g=grant, auth=authority, resource_interpretation_ref="INTERPRETATION-1")
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", blocked["blocking_reasons"])
        view["resource_interpretation"]["condition_resolutions"].append({**link, "condition_kind": "QUALIFICATION"})
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        view["resource_interpretation"]["unresolved_qualifications"] = ["Still unresolved"]
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])

        _, view, authority = condition_case(grant, constraints=[], qualifications=["Audit passes."])
        view["resource_interpretation"]["condition_resolutions"][0]["condition_kind"] = "QUALIFICATION"
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")

    def test_reviewed_durable_evidence_is_reused_without_rereading_payload(self):
        grant = root()
        _, view, authority = condition_case(grant)
        with tempfile.TemporaryDirectory() as td:
            port = LocalFileDurableReferencePort(td, "audit:sor")
            created = port.materialize("audit:sor", "audit:report", b"PASS")
            ref = created.artifact_ref
            observation = port.readback("audit:sor", ref)
            self.assertEqual((observation.status, observation.payload), (RESOLVED, b"PASS"))
            view["resource_interpretation"]["condition_resolutions"][0]["evidence_refs"] = [ref]
            authority["AUDIT-REVIEW"]["director_review"]["claim_verdicts"][0]["evidence_refs"] = [ref]
            def resolver(requested):
                if requested == ref:
                    self.fail("admission must reuse the existing assessment, not reread its source")
                return authority.get(requested)
            self.assertEqual(run(reader(grant), g=grant, auth=authority, authority_resolver=resolver,
                resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")

    def test_existing_verifier_claim_may_also_resolve_a_condition(self):
        grant = root()
        _, view, authority = condition_case(grant)
        authority["AUDIT-VERIFICATION"] = {
            "artifact_type": "VERIFICATION_RESULT", "artifact_id": "AUDIT-VERIFICATION",
            "produced_by_role": "control-verifier", "assignment_id": "AUDIT-ASSIGNMENT",
            "input_state_ref": "AUDIT-INPUT", "status": "CONFIRMED", "provenance": ["AUDIT-RESULT"],
            "related_artifacts": ["AUDIT-STATE"], "executor_result_ref": "AUDIT-RESULT",
            "verified_state_identity": "audit:passed", "claim_verdicts": [
                {"claim_id": "AUDIT-PASSED", "verdict": "CONFIRMED", "evidence_refs": ["AUDIT-STATE"]}],
            "additional_findings": [], "evidence_gaps": [],
        }
        view["resource_interpretation"]["condition_resolutions"][0]["review_ref"] = "AUDIT-VERIFICATION"
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        authority["AUDIT-VERIFICATION"]["status"] = "QUALIFIED"
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
        authority["AUDIT-VERIFICATION"]["status"] = "CONFIRMED"
        candidate = {"kind": "PULL_REQUEST", "repository": "example/repo", "ref": 1, "head_sha": "a" * 40}
        authority["AUDIT-VERIFICATION"]["verified_candidate"] = candidate
        authority["AUDIT-RESULT"]["published_candidate"] = {**candidate, "head_sha": "b" * 40}
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
        authority["AUDIT-RESULT"]["published_candidate"] = candidate
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        authority["AUDIT-VERIFICATION"]["claim_verdicts"][0]["verdict"] = "NOT_PROVEN"
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])

    def test_direct_resource_instruction_uses_existing_grant_without_fabricated_options(self):
        grant = root()
        grant["attempt_limit"] = None
        grant["valid_until"] = None
        grant["scope"].update(candidate_ref=None, route_ref=None)
        owner = decision(grant)
        for field in ("question_ref", "options_presented", "selected_option"):
            del owner[field]
        source = "For this assignment, use at most five tokens."
        owner.update(resource_input_mode="DIRECT_INSTRUCTION", owner_constraints=[source],
                     resource_interpretation={"source_text": source, "unresolved_constraints": [],
                                              "unresolved_qualifications": []})
        self.assertIsNone(owner["authorized_attempt_limit"])
        self.assertIsNone(owner["authorized_valid_until"])
        self.assertIsNone(owner["authorized_candidate_ref"])
        self.assertIsNone(owner["authorized_route_ref"])
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/owner-decision-record.schema.json").read_text())
        self.assertTrue(schema_accepts(owner, schema))
        self.assertEqual(run(reader(grant), g=grant, auth={ODR: owner})["status"], "ADMISSIBLE")
        unresolved = deepcopy(owner)
        unresolved["resource_interpretation"]["unresolved_constraints"] = ["Only after the audit passes."]
        assert_owner_block(self, grant, unresolved)
        unresolved = deepcopy(owner)
        unresolved["resource_interpretation"]["unresolved_qualifications"] = ["Only for a later candidate."]
        assert_owner_block(self, grant, unresolved)
        cleared = deepcopy(unresolved); cleared["artifact_id"] = "INTERPRETATION-1"
        cleared["related_artifacts"].append(ODR)
        cleared["resource_interpretation"]["unresolved_qualifications"] = []
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant,
            auth={ODR: unresolved, "INTERPRETATION-1": cleared}, resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
        no_source = deepcopy(owner); no_source["resource_interpretation"]["source_text"] = "  "
        self.assertFalse(schema_accepts(no_source, schema))
        assert_owner_block(self, grant, no_source)
        unsupported = deepcopy(owner); unsupported["authorized_resource_limits"][0]["ordinary_limit"] = 6
        assert_owner_block(self, grant, unsupported)
        invented = deepcopy(owner); invented["options_presented"] = ["AUTHORIZE_RESOURCE_AUTHORITY"]
        self.assertFalse(schema_accepts(invented, schema))
        assert_owner_block(self, grant, invented)

    def test_existing_grant_uses_separate_linked_interpretation_without_duplicating_capacity(self):
        grant = root()
        grant["attempt_limit"] = None
        grant["valid_until"] = None
        grant["scope"].update(candidate_ref=None, route_ref=None)
        original = decision(grant, owner_constraints=["At most five tokens."])
        original["future_owner_terms"] = {"condition": [True]}
        original_before = deepcopy(original)
        normalized = deepcopy(original); normalized["artifact_id"] = "NORMALIZED-1"
        normalized["related_artifacts"].append(ODR)
        normalized["resource_interpretation"] = {"source_text": "At most five tokens.",
                                                  "unresolved_constraints": [], "unresolved_qualifications": []}
        auth = {ODR: original, "NORMALIZED-1": normalized}
        with tempfile.TemporaryDirectory() as td:
            ledger = ResourceLedger(Path(td) / "shared.sqlite3"); ledger.initialize()
            registered = ledger.register_grant(grant)
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant, auth=auth)["blocking_reasons"])
            result = run(ledger, g=grant, auth=auth, resource_interpretation_ref="NORMALIZED-1")
            self.assertEqual(result["status"], "ADMISSIBLE")
            self.assertEqual(ledger.get_grant(grant["artifact_id"]), registered)
            self.assertEqual(original, original_before)
            self.assertEqual(registered["authority_source"]["authority_ref"], ODR)
            equivalent = deepcopy(normalized)
            equivalent["authorized_resource_limits"][0]["ordinary_limit"] = 5.0
            equivalent["qualifications"] = []
            self.assertEqual(run(ledger, g=grant, auth={ODR: original, "NORMALIZED-1": equivalent},
                resource_interpretation_ref="NORMALIZED-1")["status"], "ADMISSIBLE")
            ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 4, "R-1", "OP-1", "KEY-1", now=NOW)
            blocked = run(ledger, g=grant, auth=auth, resource_interpretation_ref="NORMALIZED-1")
            self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", blocked["blocking_reasons"])
            changed = deepcopy(normalized); changed["authorized_resource_limits"][0]["ordinary_limit"] = 6
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth={ODR: original, "NORMALIZED-1": changed}, resource_interpretation_ref="NORMALIZED-1")["blocking_reasons"])
            changed = deepcopy(normalized); changed["future_owner_terms"]["condition"] = [1]
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth={ODR: original, "NORMALIZED-1": changed}, resource_interpretation_ref="NORMALIZED-1")["blocking_reasons"])
            changed = deepcopy(normalized); changed["qualifications"] = ["Only after the audit."]
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth={ODR: original, "NORMALIZED-1": changed}, resource_interpretation_ref="NORMALIZED-1")["blocking_reasons"])
            unlinked = deepcopy(normalized); unlinked["related_artifacts"].remove(ODR)
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth={ODR: original, "NORMALIZED-1": unlinked}, resource_interpretation_ref="NORMALIZED-1")["blocking_reasons"])
            original_missing_grant = deepcopy(original); original_missing_grant["related_artifacts"] = []
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth={ODR: original_missing_grant, "NORMALIZED-1": normalized}, resource_interpretation_ref="NORMALIZED-1")["blocking_reasons"])
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(ledger, g=grant,
                auth=auth, resource_interpretation_ref=ODR)["blocking_reasons"])

    def test_new_option_response_may_include_its_initial_interpretation(self):
        grant = root()
        grant["attempt_limit"] = grant["valid_until"] = None
        grant["scope"].update(candidate_ref=None, route_ref=None)
        original = decision(grant, owner_constraints=["No more than five tokens."],
            resource_interpretation={"source_text": "Authorize that option; no more than five tokens.",
                                     "unresolved_constraints": [], "unresolved_qualifications": []})
        legacy = deepcopy(original); del legacy["resource_interpretation"]
        assert_owner_block(self, grant, legacy)
        self.assertEqual(run(reader(grant), g=grant, auth={ODR: original})["status"], "ADMISSIBLE")
        original["resource_interpretation"]["unresolved_constraints"] = ["Only after the audit passes."]
        assert_owner_block(self, grant, original)

    def test_linked_interpretation_accepts_unordered_authority_but_not_changed_limits(self):
        grant = rich_root()
        original = decision(grant, owner_constraints=["Use only the approved amounts."])
        view = deepcopy(original); view["artifact_id"] = "INTERPRETATION-1"
        view["related_artifacts"].append(ODR)
        view["resource_interpretation"] = {"source_text": "Use only the approved amounts.",
                                           "unresolved_constraints": [], "unresolved_qualifications": []}
        view["authorized_resource_classes"].reverse()
        view["authorized_resource_limits"].reverse()
        view["authorized_finalization_policy"]["allowed_purposes"].reverse()
        view["authorized_valid_until"] = "2030-01-01T07:00:00+07:00"
        view["authorized_attempt_limit"] = 3.0
        authority = {ODR: original, "INTERPRETATION-1": view}
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/owner-decision-record.schema.json").read_text())
        self.assertTrue(schema_accepts(view, schema))
        self.assertEqual(run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["status"], "ADMISSIBLE")
        for invalid in (True, 3.1, float("nan"), 4.0):
            view["authorized_attempt_limit"] = invalid
            self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
                resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
        view["authorized_attempt_limit"] = 3.0
        view["authorized_resource_limits"][0]["ordinary_limit"] += 1
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])
        view["authorized_resource_limits"][0]["ordinary_limit"] -= 1
        view["authorized_valid_until"] = "2030-01-01T07:00:01+07:00"
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(reader(grant), g=grant, auth=authority,
            resource_interpretation_ref="INTERPRETATION-1")["blocking_reasons"])

    def test_happy_binding_order_independence_and_exact_decimal(self):
        g = root()
        out = run(reader(g), g=g)
        self.assertEqual(out["status"], "ADMISSIBLE")
        self.assertEqual(out["provenance"], ["AA-1", "G-LEAF", "RE-1"])
        self.assertEqual(out, run(reader(g), g=g))
        for e, reason in [
            (estimate(route_ref="X"), "ESTIMATE_ROUTE_MISMATCH"),
            (estimate(assignment_id="X"), "OTHER_CONTRACT_BLOCK"),
            (estimate(input_state_ref="X"), "OTHER_CONTRACT_BLOCK"),
            (estimate(subject_ref="X"), "OTHER_CONTRACT_BLOCK"),
        ]:
            with self.subTest(reason=reason):
                self.assertIn(reason, run(reader(g), g=g, e=e)["blocking_reasons"])

        exact = Decimal("1.0000000000000000000000000000")
        required = Decimal("1.0000000000000000000000000001")
        g = root(ordinary=exact)
        self.assertIn(
            "RESERVABLE_LIMIT_INSUFFICIENT",
            run(reader(g, exact), g=g, e=estimate(item(upper=required)))["blocking_reasons"],
        )

        g = rich_root()
        d = decision(g)
        d["authorized_resource_classes"].reverse()
        d["authorized_resource_limits"].reverse()
        d["authorized_finalization_policy"]["allowed_purposes"].reverse()
        d["authorized_valid_until"] = "2030-01-01T07:00:00+07:00"
        d["project_id"] = "PROJECT-1"
        self.assertEqual(run(reader(g), g=g, auth={ODR: d})["status"], "ADMISSIBLE")

    def test_owner_authority_negative_matrix(self):
        cases = []
        g = root(authority_ref="MISSING")
        cases.append(("authority ref missing", g, None, {}, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(authority_ref="G-LEAF")
        cases.append(("self reference", g, None, {"G-LEAF": decision(g, artifact_id="G-LEAF")}, "AUTHORITY_SOURCE_UNRESOLVED"))

        g = root()
        d = decision(g)
        d.pop("question_ref")
        cases.append(("schema invalid", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        reduced = {
            "artifact_id": ODR, "artifact_type": "OWNER_DECISION_RECORD", "produced_by_role": "owner-interface",
            "status": "RECORDED", "authority_role": "OWNER_K0", "provenance": ["OWNER/K0"],
        }
        cases.append(("reduced R1 record", root(), reduced, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        for name, field, value in [
            ("wrong artifact type", "artifact_type", "RESOURCE_GRANT"),
            ("wrong producer", "produced_by_role", "control-director"),
            ("wrong status", "status", "DRAFT"),
            ("wrong authority role", "authority_role", "OWNER_K1"),
            ("wrong decision kind", "decision_kind", "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"),
            ("non affirmative", "selected_option", "DEFER"),
            ("nontransitive false", "non_transitive", False),
            ("target mismatch", "authorized_resource_grant_ref", "G-OTHER"),
            ("assignment mismatch", "assignment_id", "A-OTHER"),
            ("input mismatch", "input_state_ref", "STATE-OTHER"),
            ("scope mismatch", "authorized_scope", "assignment:OTHER"),
            ("candidate mismatch", "authorized_candidate_ref", "candidate:other"),
            ("route mismatch", "authorized_route_ref", "ROUTE-X"),
            ("attempt mismatch", "authorized_attempt_limit", 4),
            ("validity mismatch", "authorized_valid_until", "2030-01-02T00:00:00Z"),
        ]:
            g = root()
            d = decision(g)
            d[field] = value
            cases.append((name, g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        g = root(); d = decision(g); d["options_presented"] = ["DO_NOT_AUTHORIZE_RESOURCE_AUTHORITY", "DEFER"]
        cases.append(("affirmative absent", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_classes"] = ["REMOTE_CI"]
        cases.append(("class set mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = rich_root(); d = decision(g); d["authorized_resource_limits"] = d["authorized_resource_limits"][:1]
        cases.append(("limit key missing", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"].append({
            "resource_class": "MODEL_INFERENCE", "dimension": "MODEL_CALLS", "limit_mode": "HARD_LIMIT",
            "ordinary_limit": 1, "finalization_reserve": 0,
        })
        cases.append(("extra limit key", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"][0]["limit_mode"] = "HARD_LIMIT"
        cases.append(("mode mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"][0]["ordinary_limit"] = 6
        cases.append(("ordinary mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(final=2); d = decision(g); d["authorized_resource_limits"][0]["finalization_reserve"] = 1
        cases.append(("reserve mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_resource_limits"].append(deepcopy(d["authorized_resource_limits"][0]))
        cases.append(("duplicate owner limit", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_finalization_policy"]["allowed_purposes"] = ["CONTROL_HANDOFF"]
        cases.append(("purpose mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["authorized_finalization_policy"]["protected"] = False
        cases.append(("protected mismatch", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["related_artifacts"] = ["G-OTHER"]
        cases.append(("grant absent related", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["owner_constraints"] = ["interpret me"]
        cases.append(("constraints nonempty", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))
        g = root(); d = decision(g); d["qualifications"] = ["interpret me"]
        cases.append(("qualifications nonempty", g, d, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        unrelated = {
            "artifact_type": "OWNER_DECISION_RECORD", "artifact_id": ODR, "produced_by_role": "owner-interface",
            "assignment_id": "A-1", "input_state_ref": "STATE-1", "status": "RECORDED",
            "provenance": ["OWNER/K0"], "related_artifacts": ["HRA-1"], "question_ref": "Q-HR",
            "options_presented": ["AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"],
            "selected_option": "AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM", "owner_constraints": [],
            "consequences_acknowledged": [], "qualifications": [], "authority_role": "OWNER_K0",
            "decision_kind": "CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM", "project_id": "P-1",
            "authorized_question_id": "RQ-1", "authorized_scope": "bounded",
            "authorized_namespace": "human-research/rq-1", "authorization_id": "HRA-1",
            "non_transitive": True, "default_research_mode_unchanged": True,
        }
        cases.append(("unrelated valid owner decision", root(), unrelated, None, "AUTHORITY_SOURCE_UNRESOLVED"))

        bad_grant = root()
        bad_grant["limits"][0]["resource_class"] = "REMOTE_CI"
        bad_grant["limits"][0]["dimension"] = "RUNNER_MINUTES"
        cases.append(("grant limit outside scope", bad_grant, decision(bad_grant), None, "OTHER_CONTRACT_BLOCK"))

        parent = root("G-P")
        direct_child = child(parent)
        direct_child["authority_source"] = {"authority_type": "OWNER_APPROVED_RESOURCE_AUTHORITY", "authority_ref": ODR}
        cases.append(("child reuses root owner decision", direct_child, decision(parent), None, "OTHER_CONTRACT_BLOCK"))

        autonomy = root(authority_type="AUTONOMY_ENVELOPE", authority_ref="AE-1")
        cases.append(("unsupported autonomy envelope", autonomy, None, {"AE-1": {"artifact_type": "AUTONOMY_ENVELOPE", "artifact_id": "AE-1"}}, "AUTHORITY_SOURCE_UNRESOLVED"))
        other = root(authority_type="OTHER_DURABLE_RESOURCE_AUTHORITY", authority_ref="DA-1")
        cases.append(("unsupported other durable authority", other, None, {"DA-1": {"artifact_type": "DURABLE_RESOURCE_AUTHORITY", "artifact_id": "DA-1"}}, "AUTHORITY_SOURCE_UNRESOLVED"))

        for name, g, d, authority_map, reason in cases:
            with self.subTest(name=name):
                assert_owner_block(self, g, d, auth=authority_map, reason=reason)

    def test_parent_chain_root_owner_binding_and_shared_parent_availability(self):
        parent = root("G-P", ordinary=5, final=0)
        parent["scope"].update(candidate_ref=None, route_ref=None)
        leaf = child(parent)
        states = {
            ("G-P", "MODEL_INFERENCE", "TOKENS"): 5,
            ("G-LEAF", "MODEL_INFERENCE", "TOKENS"): 5,
        }
        r = Reader({"G-P": parent, "G-LEAF": leaf}, states)
        authority_map = {ODR: decision(parent)}
        self.assertEqual(run(r, g=leaf, auth=authority_map)["status"], "ADMISSIBLE")

        invalid_owner = decision(parent)
        invalid_owner["authorized_attempt_limit"] = 99
        out = run(r, g=leaf, auth={ODR: invalid_owner})
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", out["blocking_reasons"])

        r.available[("G-P", "MODEL_INFERENCE", "TOKENS")] = 1
        out = run(r, g=leaf, auth=authority_map, e=estimate(item(upper=2)))
        self.assertEqual(out["evaluations"][0]["available_amount"], Decimal(1))
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", out["blocking_reasons"])

    def test_complete_estimate_validator_and_unknown_policy(self):
        malformed = []
        for field in ("point_estimate", "quantiles", "confidence", "historical_sample_count", "upper_bound"):
            entry = item(); entry.pop(field); malformed.append(estimate(entry))
        entry = item(); entry["extra"] = 1; malformed.append(estimate(entry))
        artifact = estimate(); artifact["extra"] = 1; malformed.append(artifact)
        for quantiles in (
            [{"probability": 0, "quantity": 1}],
            [{"probability": Decimal("1.1"), "quantity": 1}],
            [{"probability": Decimal(".9"), "quantity": -1}],
        ):
            entry = item(); entry["quantiles"] = quantiles; malformed.append(estimate(entry))
        entry = item(); entry["confidence"] = "CERTAIN"; malformed.append(estimate(entry))
        for value in (Decimal("-1"), Decimal("NaN")):
            entry = item(); entry["point_estimate"] = value; malformed.append(estimate(entry))
        entry = item(); entry["unknown_resource_state"] = "ESTIMATE_UNKNOWN"; malformed.append(estimate(entry))
        for field, value in (
            ("point_estimate", 1),
            ("quantiles", [{"probability": Decimal(".9"), "quantity": 1}]),
            ("upper_bound", 1),
            ("historical_sample_count", 0),
        ):
            entry = item("UNKNOWN"); entry[field] = value; malformed.append(estimate(entry))
        malformed += [
            estimate(item(), status="UNKNOWN"),
            estimate(item("UNKNOWN"), status="ESTIMATED"),
            estimate(item(), status="PARTIAL"),
        ]
        entry = item(); malformed.append(estimate(entry, deepcopy(entry)))

        for artifact in malformed:
            with self.subTest(status=artifact.get("status")):
                g = root()
                out = run(reader(g), g=g, e=artifact)
                self.assertIn("OTHER_CONTRACT_BLOCK", out["blocking_reasons"])
                self.assertEqual(out["evaluations"], [])

        entry = item(); entry["upper_bound"] = None
        g = root()
        out = run(reader(g), g=g, e=estimate(entry))
        self.assertIn("UNKNOWN_REQUIRED_RESOURCE", out["blocking_reasons"])
        self.assertNotIn("OTHER_CONTRACT_BLOCK", out["blocking_reasons"])

    def test_availability_modes_failures_no_mutation_and_decimal_context(self):
        g = root()
        self.assertIn("GRANT_MISSING", run(Reader({}, {}), g=g)["blocking_reasons"])
        failure = run(Reader({"G-LEAF": g}, {}, fail_grants={"G-LEAF"}), g=g)
        self.assertEqual(failure["unknown_resource_state"], "AVAILABILITY_UNKNOWN")

        observation = root(mode="OBSERVATION_ONLY")
        r = Reader({"G-LEAF": observation}, {})
        self.assertEqual(run(r, g=observation, e=estimate(item("UNKNOWN")))["status"], "ADMISSIBLE")
        self.assertFalse(any(call[0] == "get_resource_state" for call in r.calls))
        self.assertIn(
            "UNCLASSIFIED_METERED_SIDE_EFFECT",
            run(reader(g), g=g, unclassified_metered_side_effect_refs=("surface:x",))["blocking_reasons"],
        )

        old_precision = getcontext().prec
        try:
            getcontext().prec = 2
            low = run(reader(g), g=g)
            getcontext().prec = 50
            high = run(reader(g), g=g)
        finally:
            getcontext().prec = old_precision
        self.assertEqual(low, high)

        r = reader(g)
        before = (deepcopy(r.grants), deepcopy(r.available))
        run(r, g=g)
        self.assertEqual(before, (r.grants, r.available))

        with tempfile.TemporaryDirectory() as td:
            ledger = ResourceLedger(Path(td) / "shared.sqlite3")
            ledger.initialize()
            parent = root("G-P", ordinary=5, final=0)
            parent["scope"].update(candidate_ref=None, route_ref=None)
            child_a = child(parent, "G-A", ordinary=5, final=0)
            child_b = child(parent, "G-LEAF", ordinary=5, final=0)
            ledger.register_grant(parent)
            ledger.register_child_grant(child_a)
            ledger.register_child_grant(child_b)
            ledger.reserve("G-A", "MODEL_INFERENCE", "TOKENS", 4, "R-A", "OP-A", "K-A", now=NOW)

            authority_map = {ODR: decision(parent)}
            blocked = run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=2)))
            self.assertEqual(blocked["evaluations"][0]["available_amount"], Decimal(1))
            self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", blocked["blocking_reasons"])

            before_state = ledger.get_resource_state("G-LEAF", "MODEL_INFERENCE", "TOKENS")
            run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=1)))
            self.assertEqual(before_state, ledger.get_resource_state("G-LEAF", "MODEL_INFERENCE", "TOKENS"))

            ledger.release("R-A", "REL-A", now=NOW)
            self.assertEqual(
                run(ledger, g=child_b, auth=authority_map, e=estimate(item(upper=2)))["status"],
                "ADMISSIBLE",
            )


class PerClassCorrectionAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = ResourceLedger(Path(self.tmp.name) / "per-class.sqlite")
        self.ledger.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def test_correct_owner_terms_repair_grant_without_a_prior_shared_view(self):
        grant = root(ordinary=5)
        owner = decision(grant)
        owner["authorized_resource_limits"][0]["ordinary_limit"] = 10
        owner["resource_interpretation"] = {
            "source_text": "The actual approved token budget is ten.",
            "unresolved_constraints": [], "unresolved_qualifications": []}
        auth = {ODR: owner}
        self.ledger.register_grant(grant)
        original_grant, original_owner = self.ledger.get_grant("G-LEAF"), deepcopy(owner)
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 4, "BEFORE", "OP-B", "KEY-B", now=NOW)
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", run(self.ledger, g=grant, auth=auth)["blocking_reasons"])
        snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get)
        self.assertIsNone(snapshot["selection_snapshot"])
        self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, expected_snapshot=snapshot)
        self.assertEqual(self.ledger.get_grant("G-LEAF"), original_grant)
        self.assertEqual(owner, original_owner)
        self.assertEqual(self.ledger.get_effective_grant("G-LEAF")["limits"][0]["ordinary_limit"], Decimal(10))
        admitted = run(self.ledger, g=grant, auth=auth, e=estimate(item(upper=6)))
        self.assertEqual(admitted["status"], "ADMISSIBLE", admitted)
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 6, "AFTER", "OP-A", "KEY-A", now=NOW)
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 1, "OVER", "OP-O", "KEY-O", now=NOW)

    def test_linked_correction_retains_conditions_and_existing_shared_limit(self):
        grant = root(ordinary=5)
        source, selected, auth = condition_case(grant)
        source["resource_interpretation"]["shared_limits"] = [{
            "limit_id": "TOTAL", "dimension": "TOKENS", "resource_classes": ["MODEL_INFERENCE"], "total_limit": 9}]
        selected["resource_interpretation"]["shared_limits"] = deepcopy(source["resource_interpretation"]["shared_limits"])
        corrected = deepcopy(selected); corrected["artifact_id"] = "CORRECTED"
        corrected["authorized_resource_limits"][0]["ordinary_limit"] = 10
        corrected["resource_interpretation"]["shared_limits"][0]["limit_id"] = "SAME-TOTAL"
        auth["CORRECTED"] = corrected
        original_source = deepcopy(source)
        self.ledger.register_grant(grant)
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, selected["artifact_id"])
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 4, "BEFORE", "OP-B", "KEY-B", now=NOW)
        missing_condition = deepcopy(corrected); missing_condition["artifact_id"] = "MISSING-CONDITION"
        del missing_condition["resource_interpretation"]["condition_resolutions"]
        auth["MISSING-CONDITION"] = missing_condition
        bad_snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get, "MISSING-CONDITION")
        with self.assertRaises(AuthorityViolation):
            self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, "MISSING-CONDITION", expected_snapshot=bad_snapshot)
        altered_shared = deepcopy(corrected); altered_shared["artifact_id"] = "ALTERED-SHARED"
        altered_shared["resource_interpretation"]["shared_limits"][0]["total_limit"] = 8
        auth["ALTERED-SHARED"] = altered_shared
        bad_snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get, "ALTERED-SHARED")
        with self.assertRaises(AuthorityViolation):
            self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, "ALTERED-SHARED", expected_snapshot=bad_snapshot)
        snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get, "CORRECTED")
        self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, "CORRECTED", expected_snapshot=snapshot)
        admitted = run(self.ledger, g=grant, auth=auth, e=estimate(item(upper=5)))
        self.assertEqual(admitted["status"], "ADMISSIBLE", admitted)
        self.assertEqual(admitted["resource_interpretation_ref"], "CORRECTED")
        self.assertEqual(self.ledger.get_shared_limits("G-LEAF")[0]["limit_id"], "TOTAL")
        self.assertEqual(source, original_source)
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 5, "AFTER", "OP-A", "KEY-A", now=NOW)
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 1, "OVER", "OP-O", "KEY-O", now=NOW)
        next_view = deepcopy(corrected); next_view["artifact_id"] = "TIGHTER-SHARED"
        next_view["resource_interpretation"]["shared_limits"][0]["total_limit"] = 8
        auth["TIGHTER-SHARED"] = next_view
        chosen = self.ledger.get_owner_shared_selection("G-LEAF")
        self.ledger.replace_owner_shared_limits("G-LEAF", auth.get, "TIGHTER-SHARED",
            expected_snapshot=chosen["snapshot"], expected_source_fingerprint=chosen["source_fingerprint"])
        self.assertEqual(self.ledger.get_shared_limit_state("G-LEAF", "SAME-TOTAL")["deficit"], Decimal(1))
        self.assertEqual(self.ledger.get_effective_grant("G-LEAF")["limits"][0]["ordinary_limit"], Decimal(10))

    def test_older_child_and_new_grandchild_use_corrected_root(self):
        parent = root("G-ROOT", ordinary=5)
        source = decision(parent)
        source["resource_interpretation"] = {"source_text": "Use the Owner's stated budget.",
            "unresolved_constraints": [], "unresolved_qualifications": []}
        higher = deepcopy(source); higher["artifact_id"] = "HIGHER"; higher["related_artifacts"].append(ODR)
        higher["authorized_resource_limits"][0]["ordinary_limit"] = 10
        lower = deepcopy(source); lower["artifact_id"] = "LOWER"; lower["related_artifacts"].append(ODR)
        auth = {ODR: source, "HIGHER": higher, "LOWER": lower}
        self.ledger.register_grant(parent)
        snapshot = self.ledger.get_owner_resource_snapshot("G-ROOT", auth.get, "HIGHER")
        self.ledger.replace_owner_per_class_limits("G-ROOT", auth.get, "HIGHER", expected_snapshot=snapshot)
        old_child = child(parent, ordinary=10)
        self.ledger.register_child_grant(old_child)
        snapshot = self.ledger.get_owner_resource_snapshot("G-ROOT", auth.get, "LOWER")
        self.ledger.replace_owner_per_class_limits("G-ROOT", auth.get, "LOWER", expected_snapshot=snapshot)
        admitted = run(self.ledger, g=old_child, auth=auth, e=estimate(item(upper=1)))
        self.assertEqual(admitted["status"], "ADMISSIBLE", admitted)
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 1, "CHILD", "OP-CHILD", "KEY-CHILD", now=NOW)
        grandchild = child(old_child, gid="G-GRANDCHILD", ordinary=8)
        self.ledger.register_child_grant(grandchild)
        grand_result = run(self.ledger, g=grandchild, auth=auth, e=estimate(item(upper=1)),
                           resource_grant_ref="G-GRANDCHILD")
        self.assertEqual(grand_result["status"], "ADMISSIBLE", grand_result)
        self.ledger.reserve("G-GRANDCHILD", "MODEL_INFERENCE", "TOKENS", 1, "GRAND", "OP-GRAND", "KEY-GRAND", now=NOW)
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("G-GRANDCHILD", "MODEL_INFERENCE", "TOKENS", 4, "EXTRA", "OP-EXTRA", "KEY-EXTRA", now=NOW)

    def test_correction_can_reuse_direct_condition_assessment_without_review(self):
        grant = root(ordinary=5)
        source, view, auth = condition_case(grant)
        resolution = view["resource_interpretation"]["condition_resolutions"][0]
        del resolution["review_ref"]
        del resolution["claim_id"]
        view["authorized_resource_limits"][0]["ordinary_limit"] = 10
        self.ledger.register_grant(grant)
        snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get, view["artifact_id"])
        self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, view["artifact_id"], expected_snapshot=snapshot)
        result = run(self.ledger, g=grant, auth=auth, e=estimate(item(upper=6)))
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual(self.ledger.get_effective_grant("G-LEAF")["limits"][0]["ordinary_limit"], Decimal(10))

    def test_correction_to_observation_keeps_admission_nonblocking(self):
        grant = root(ordinary=5)
        owner = decision(grant)
        owner["resource_interpretation"] = {"source_text": "Use the actual Owner resource policy.",
            "unresolved_constraints": [], "unresolved_qualifications": []}
        view = deepcopy(owner); view["artifact_id"] = "OBSERVATION"; view["related_artifacts"].append(ODR)
        view["authorized_resource_limits"][0].update(
            limit_mode="OBSERVATION_ONLY", ordinary_limit=None, finalization_reserve=None)
        auth = {ODR: owner, "OBSERVATION": view}
        self.ledger.register_grant(grant)
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 2, "OLD", "OP-OLD", "KEY-OLD", now=NOW)
        snapshot = self.ledger.get_owner_resource_snapshot("G-LEAF", auth.get, "OBSERVATION")
        self.ledger.replace_owner_per_class_limits("G-LEAF", auth.get, "OBSERVATION", expected_snapshot=snapshot)
        result = run(self.ledger, g=grant, auth=auth, e=estimate(item(upper=6)))
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual(result["evaluations"][0]["reason"], "OBSERVATION_ONLY_NON_BLOCKING")
        self.assertEqual(self.ledger.get_resource_state("G-LEAF", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"],
                         Decimal(2))


class SharedResourceAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = ResourceLedger(Path(self.tmp.name) / "shared.sqlite")
        self.ledger.initialize()
        self.grant = root(ordinary=10)
        self.grant["scope"]["resource_classes"] = ["MODEL_INFERENCE", "REMOTE_CI"]
        self.grant["limits"] = [
            {"resource_class": name, "dimension": "USD", "limit_mode": "RESERVABLE_LIMIT",
             "ordinary_limit": 10, "finalization_reserve": 0}
            for name in ("MODEL_INFERENCE", "REMOTE_CI")
        ]
        self.owner = decision(self.grant)
        self.owner["resource_interpretation"] = {
            "source_text": "These resources have one total budget of ten.",
            "unresolved_constraints": [], "unresolved_qualifications": [],
            "shared_limits": [{"limit_id": "BUDGET-1", "dimension": "USD",
                               "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
                               "total_limit": 10, "finalization_reserve": 0}],
        }
        self.ledger.register_grant(self.grant)
        self.auth = {ODR: self.owner}

    def tearDown(self):
        self.tmp.cleanup()

    def estimate(self, *classes, upper=6):
        items = []
        for name in classes:
            e = item(upper=upper, dim="USD")
            e["resource_class"] = name
            items.append(e)
        return estimate(*items)

    def bind(self):
        self.ledger.register_owner_shared_limits("G-LEAF", self.auth.get)

    def test_unregistered_owner_total_is_not_claimed_as_admitted(self):
        before = self.ledger.get_grant("G-LEAF")
        result = run(self.ledger, g=self.grant, e=self.estimate("MODEL_INFERENCE"), auth=self.auth)
        self.assertIn("SHARED_LIMIT_REGISTRATION_REQUIRED", result["blocking_reasons"])
        self.assertEqual(self.ledger.get_shared_limits("G-LEAF"), [])
        self.assertEqual(self.ledger.get_grant("G-LEAF"), before)

    def test_one_known_component_reuses_its_existing_estimate(self):
        self.bind()
        result = run(self.ledger, g=self.grant, e=self.estimate("MODEL_INFERENCE"), auth=self.auth)
        self.assertEqual(result["status"], "ADMISSIBLE")
        self.assertEqual(result["shared_evaluations"][0]["estimated_requirement"], Decimal(6))

    def test_admission_uses_the_selected_corrected_view_and_empty_correction(self):
        self.bind()
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 6, "BEFORE", "OP-BEFORE", "KEY-BEFORE", now=NOW)
        corrected = deepcopy(self.owner); corrected["artifact_id"] = "CORRECTED"
        corrected["related_artifacts"].append(ODR)
        corrected["resource_interpretation"]["shared_limits"][0]["total_limit"] = 9
        empty = deepcopy(corrected); empty["artifact_id"] = "EMPTY"
        empty["resource_interpretation"]["shared_limits"] = []
        auth = {ODR: self.owner, "CORRECTED": corrected, "EMPTY": empty}
        selected = self.ledger.get_owner_shared_selection("G-LEAF")
        self.ledger.replace_owner_shared_limits("G-LEAF", auth.get, "CORRECTED",
            expected_snapshot=selected["snapshot"], expected_source_fingerprint=selected["source_fingerprint"])
        blocked = run(self.ledger, g=self.grant, e=self.estimate("REMOTE_CI", upper=4), auth=auth)
        self.assertEqual(blocked["resource_interpretation_ref"], "CORRECTED")
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", blocked["blocking_reasons"])
        allowed = run(self.ledger, g=self.grant, e=self.estimate("REMOTE_CI", upper=3), auth=auth)
        self.assertEqual(allowed["status"], "ADMISSIBLE", allowed)
        selected = self.ledger.get_owner_shared_selection("G-LEAF")
        self.ledger.replace_owner_shared_limits("G-LEAF", auth.get, "EMPTY",
            expected_snapshot=selected["snapshot"], expected_source_fingerprint=selected["source_fingerprint"])
        after = run(self.ledger, g=self.grant, e=self.estimate("REMOTE_CI", upper=4), auth=auth)
        self.assertEqual(after["status"], "ADMISSIBLE", after)
        self.assertEqual(after["resource_interpretation_ref"], "EMPTY")
        self.assertEqual(self.ledger.get_owner_shared_selection("G-LEAF")["interpretation_ref"], "EMPTY")
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "CORRECTED")

    def test_finalization_uses_its_authorized_pool_without_exposing_it_to_ordinary_work(self):
        grant = deepcopy(self.grant)
        for limit in grant["limits"]:
            limit["finalization_reserve"] = 2
        owner = decision(grant)
        owner["resource_interpretation"] = deepcopy(self.owner["resource_interpretation"])
        owner["resource_interpretation"]["shared_limits"][0]["finalization_reserve"] = 2
        ledger = ResourceLedger(Path(self.tmp.name) / "finalization.sqlite")
        ledger.initialize(); ledger.register_grant(grant)
        auth = {ODR: owner}; ledger.register_owner_shared_limits("G-LEAF", auth.get)
        ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 8, "ORD", "OP-ORD", "KEY-ORD", now=NOW)
        e = self.estimate("MODEL_INFERENCE", upper=1)
        ordinary = run(ledger, g=grant, e=e, auth=auth)
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", ordinary["blocking_reasons"])
        final = run(ledger, g=grant, e=e, auth=auth, finalization_purpose="FINAL_ACCOUNTING")
        self.assertEqual(final["status"], "ADMISSIBLE", final)
        self.assertEqual(final["finalization_purpose"], "FINAL_ACCOUNTING")
        self.assertEqual(final["shared_evaluations"][0]["available_amount"], Decimal(2))
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/resource-admission.schema.json").read_text())
        self.assertTrue(schema_accepts(json.loads(json.dumps(final, default=float)), schema))
        denied = run(ledger, g=grant, e=e, auth=auth, finalization_purpose="CONTROL_HANDOFF")
        self.assertIn("GRANT_SCOPE_MISMATCH", denied["blocking_reasons"])
        self.assertTrue(schema_accepts(json.loads(json.dumps(denied, default=float)), schema))
        ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 1, "FIN", "OP-FIN", "KEY-FIN",
                       now=NOW, pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.assertEqual(ledger.get_shared_limit_state("G-LEAF", "BUDGET-1")["used"], Decimal(9))

    def test_previously_bound_interpretation_is_reused_without_changing_source_or_grant(self):
        source = decision(self.grant, owner_constraints=["These resources have one total budget of ten."])
        linked = deepcopy(self.owner)
        linked["artifact_id"] = "NORMALIZED-1"
        linked["owner_constraints"] = deepcopy(source["owner_constraints"])
        linked["related_artifacts"].append(ODR)
        auth = {ODR: source, "NORMALIZED-1": linked}
        original_source, original_grant = deepcopy(source), self.ledger.get_grant("G-LEAF")
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 6, "OLD", "OP-OLD", "KEY-OLD", now=NOW)
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-1")
        self.assertEqual(self.ledger.get_shared_limit_state("G-LEAF", "BUDGET-1")["used"], Decimal(6))
        result = run(self.ledger, g=self.grant, e=self.estimate("REMOTE_CI", upper=4), auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual(result["resource_interpretation_ref"], "NORMALIZED-1")
        self.assertEqual(result["shared_evaluations"][0]["available_amount"], Decimal(4))
        self.assertEqual(self.ledger.get_grant("G-LEAF"), original_grant)
        self.assertEqual(source, original_source)


    def test_same_owner_same_limit_with_distinct_ids_reuses_one_normalized_estimate(self):
        source = decision(self.grant, owner_constraints=["These resources have one total budget of ten."])
        first = deepcopy(self.owner); first["artifact_id"] = "NORMALIZED-1"
        first["owner_constraints"] = deepcopy(source["owner_constraints"])
        first["related_artifacts"].append(ODR)
        second = deepcopy(first); second["artifact_id"] = "NORMALIZED-2"
        second["resource_interpretation"]["shared_limits"][0]["limit_id"] = "OTHER-TOTAL"
        auth = {ODR: source, "NORMALIZED-1": first, "NORMALIZED-2": second}
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-1")
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-2")
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI")
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": "BUDGET-1",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "estimate_state": "ESTIMATED",
            "upper_bound": 9, "basis_refs": ["basis:1"]}]
        result = run(self.ledger, g=self.grant, e=e, auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual([entry["estimated_requirement"] for entry in result["shared_evaluations"]],
                         [Decimal(9)])
        self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 6, "R-A", "OP-A", "KEY-A", now=NOW)
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("G-LEAF", "REMOTE_CI", "USD", 5, "R-B", "OP-B", "KEY-B", now=NOW)

    def test_original_owner_limit_accepts_equivalent_linked_identity(self):
        source = deepcopy(self.owner)
        linked = deepcopy(source); linked["artifact_id"] = "LINKED"
        linked["related_artifacts"].append(ODR)
        linked["resource_interpretation"]["shared_limits"][0]["limit_id"] = "RENAMED"
        auth = {ODR: source, "LINKED": linked}
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "LINKED")
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI")
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": "RENAMED",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "estimate_state": "ESTIMATED",
            "upper_bound": 9, "basis_refs": ["basis:1"]}]
        result = run(self.ledger, g=self.grant, e=e, auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        original_limits = self.ledger.get_shared_limits("G-LEAF")
        linked["resource_interpretation"]["shared_limits"][0].update(limit_id="OTHER-TOTAL", total_limit=9)
        result = run(self.ledger, g=self.grant, e=e, auth=auth, resource_interpretation_ref="LINKED")
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", result["blocking_reasons"])
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "LINKED")
        self.assertEqual(self.ledger.get_shared_limits("G-LEAF"), original_limits)
        linked["resource_interpretation"]["shared_limits"] = deepcopy(source["resource_interpretation"]["shared_limits"])
        linked["resource_interpretation"]["shared_limits"].append({"limit_id": "OTHER-TOTAL", "dimension": "USD",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": 9})
        result = run(self.ledger, g=self.grant, e=e, auth=auth, resource_interpretation_ref="LINKED")
        self.assertIn("AUTHORITY_SOURCE_UNRESOLVED", result["blocking_reasons"])
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "LINKED")
        self.assertEqual(self.ledger.get_shared_limits("G-LEAF"), original_limits)

    def test_equivalent_pending_limit_and_existing_bound_do_not_deadlock(self):
        source = decision(self.grant, owner_constraints=["These resources have one total budget of ten."])
        first = deepcopy(self.owner); first["artifact_id"] = "NORMALIZED-1"
        first["owner_constraints"] = deepcopy(source["owner_constraints"]); first["related_artifacts"].append(ODR)
        second = deepcopy(first); second["artifact_id"] = "NORMALIZED-2"
        second["resource_interpretation"]["shared_limits"][0]["limit_id"] = "OTHER-TOTAL"
        auth = {ODR: source, "NORMALIZED-1": first, "NORMALIZED-2": second}
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-1")
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI")
        group = {"grant_ref": "G-LEAF", "limit_id": "OTHER-TOTAL",
                 "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
                 "estimate_state": "ESTIMATED", "upper_bound": 9, "basis_refs": ["basis:1"]}
        e["shared_estimates"] = [group]
        before = run(self.ledger, g=self.grant, e=e, auth=auth, resource_interpretation_ref="NORMALIZED-2")
        self.assertEqual(before["status"], "ADMISSIBLE", before)
        self.assertEqual(before["shared_evaluations"][0]["estimated_requirement"], Decimal(9))
        self.assertEqual([group["limit_id"] for group in self.ledger.get_shared_limits("G-LEAF")], ["BUDGET-1"])
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-2")
        self.assertEqual(run(self.ledger, g=self.grant, e=e, auth=auth,
                             resource_interpretation_ref="NORMALIZED-2")["status"], "ADMISSIBLE")
        first_estimate = {**group, "limit_id": "BUDGET-1", "estimate_state": "UNKNOWN",
                          "upper_bound": None, "basis_refs": []}
        e["shared_estimates"] = [first_estimate, group]; e["status"] = "PARTIAL"
        result = run(self.ledger, g=self.grant, e=e, auth=auth,
                     resource_interpretation_ref="NORMALIZED-2")
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual([entry["estimated_requirement"] for entry in result["shared_evaluations"]],
                         [Decimal(9)])
        e["shared_estimates"][0] = {**group, "limit_id": "BUDGET-1", "upper_bound": 1,
                                    "resource_classes": ["MODEL_INFERENCE"]}
        e["status"] = "ESTIMATED"
        result = run(self.ledger, g=self.grant, e=e, auth=auth, resource_interpretation_ref="NORMALIZED-2")
        self.assertEqual([entry["estimated_requirement"] for entry in result["shared_evaluations"]],
                         [Decimal(9)])
        e["shared_estimates"][0] = {**group, "limit_id": "BUDGET-1", "upper_bound": 6}
        e["shared_estimates"][1] = {**group, "upper_bound": 7}; e["status"] = "ESTIMATED"
        result = run(self.ledger, g=self.grant, e=e, auth=auth, resource_interpretation_ref="NORMALIZED-2")
        self.assertEqual([entry["estimated_requirement"] for entry in result["shared_evaluations"]],
                         [Decimal(7)])

    def test_single_component_keeps_the_higher_existing_estimate(self):
        self.bind()
        self.ledger.reserve("G-LEAF", "REMOTE_CI", "USD", 5, "OLD", "OP-OLD", "KEY-OLD", now=NOW)
        e = self.estimate("MODEL_INFERENCE", upper=7)
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": "BUDGET-1",
            "resource_classes": ["MODEL_INFERENCE"], "estimate_state": "ESTIMATED",
            "upper_bound": 3, "basis_refs": ["basis:1"]}]
        result = run(self.ledger, g=self.grant, e=e, auth=self.auth)
        self.assertEqual(result["shared_evaluations"][0]["estimated_requirement"], Decimal(7))
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", result["blocking_reasons"])

    def test_equivalent_groups_in_one_view_share_one_budget(self):
        source = decision(self.grant, owner_constraints=["These resources have one total budget of ten."])
        first = deepcopy(self.owner); first["artifact_id"] = "NORMALIZED-1"
        first["owner_constraints"] = deepcopy(source["owner_constraints"])
        first["related_artifacts"].append(ODR)
        second_group = deepcopy(first["resource_interpretation"]["shared_limits"][0])
        second_group["limit_id"] = "TOTAL-2"
        first["resource_interpretation"]["shared_limits"].append(second_group)
        auth = {ODR: source, "NORMALIZED-1": first}
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "NORMALIZED-1")
        result = run(self.ledger, g=self.grant, e=self.estimate("MODEL_INFERENCE"), auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertIn("NORMALIZED-1", result["related_artifacts"])
        self.assertEqual(len(result["shared_evaluations"]), 1)
        self.assertEqual(len(self.ledger.get_shared_limits("G-LEAF")), 1)

    def test_unrelated_recorded_limit_does_not_block_independent_resource(self):
        grant = deepcopy(self.grant)
        grant["limits"].append({"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS",
                                "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 10,
                                "finalization_reserve": 0})
        ledger = ResourceLedger(Path(self.tmp.name) / "independent.sqlite")
        ledger.initialize(); ledger.register_grant(grant)
        words = "The dollar resources share ten dollars; inference is also limited to ten tokens."
        source = decision(grant, owner_constraints=[words])
        dollar = deepcopy(source); dollar["artifact_id"] = "VIEW-DOLLAR"
        dollar["related_artifacts"].append(ODR)
        dollar["resource_interpretation"] = {"source_text": words, "unresolved_constraints": [],
            "unresolved_qualifications": [], "shared_limits": [{"limit_id": "DOLLARS", "dimension": "USD",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": 10}]}
        dollar["resource_interpretation"]["shared_limits"].append({"limit_id": "TOKENS", "dimension": "TOKENS",
            "resource_classes": ["MODEL_INFERENCE"], "total_limit": 10})
        auth = {ODR: source, "VIEW-DOLLAR": dollar}
        ledger.register_owner_shared_limits("G-LEAF", auth.get, "VIEW-DOLLAR")
        e = self.estimate("MODEL_INFERENCE")
        self.assertEqual(run(ledger, g=grant, e=e, auth=auth)["status"], "ADMISSIBLE")

    def test_zero_finalization_reserve_needs_no_explicit_owner_field(self):
        del self.owner["resource_interpretation"]["shared_limits"][0]["finalization_reserve"]
        self.bind()
        state = self.ledger.get_shared_limit_state("G-LEAF", "BUDGET-1")
        self.assertEqual(state["ordinary"]["available"], Decimal(10))
        self.assertEqual(state["finalization_reserve"], Decimal(0))
        result = run(self.ledger, g=self.grant, e=self.estimate("MODEL_INFERENCE"), auth=self.auth)
        self.assertEqual(result["status"], "ADMISSIBLE")

    def test_multiple_components_need_a_normalized_total_not_an_invented_sum(self):
        self.bind()
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI")
        result = run(self.ledger, g=self.grant, e=e, auth=self.auth)
        self.assertIn("UNKNOWN_REQUIRED_RESOURCE", result["blocking_reasons"])
        self.assertIsNone(result["shared_evaluations"][0]["estimated_requirement"])
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": "BUDGET-1",
                                  "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
                                  "estimate_state": "ESTIMATED", "upper_bound": 12,
                                  "basis_refs": ["basis:1"]}]
        result = run(self.ledger, g=self.grant, e=e, auth=self.auth)
        self.assertIn("RESERVABLE_LIMIT_INSUFFICIENT", result["blocking_reasons"])
        e["shared_estimates"][0]["upper_bound"] = 9
        self.assertEqual(run(self.ledger, g=self.grant, e=e, auth=self.auth)["status"], "ADMISSIBLE")

    def test_forecast_for_same_authorized_superset_covers_current_components(self):
        grant = deepcopy(self.grant)
        grant["scope"]["resource_classes"].append("PAID_TOOL")
        grant["limits"].append({"resource_class": "PAID_TOOL", "dimension": "USD",
                                "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 10,
                                "finalization_reserve": 0})
        owner = decision(grant)
        owner["resource_interpretation"] = deepcopy(self.owner["resource_interpretation"])
        owner["resource_interpretation"]["shared_limits"][0]["resource_classes"].append("PAID_TOOL")
        ledger = ResourceLedger(Path(self.tmp.name) / "superset.sqlite")
        ledger.initialize(); ledger.register_grant(grant)
        auth = {ODR: owner}; ledger.register_owner_shared_limits("G-LEAF", auth.get)
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI")
        grouped = {"grant_ref": "G-LEAF", "limit_id": "BUDGET-1",
                   "resource_classes": ["MODEL_INFERENCE", "PAID_TOOL", "REMOTE_CI"],
                   "estimate_state": "ESTIMATED", "upper_bound": 9, "basis_refs": ["basis:1"]}
        e["shared_estimates"] = [grouped]
        self.assertEqual(run(ledger, g=grant, e=e, auth=auth)["status"], "ADMISSIBLE")
        for changes in ({"grant_ref": "OTHER-GRANT"},
                        {"resource_classes": ["MODEL_INFERENCE", "PAID_TOOL"]},
                        {"resource_classes": ["MODEL_INFERENCE", "REMOTE_CI", "REMOTE_BROWSER"]}):
            with self.subTest(changes=changes):
                e["shared_estimates"] = [{**grouped, **changes}]
                result = run(ledger, g=grant, e=e, auth=auth)
                self.assertIn("UNKNOWN_REQUIRED_RESOURCE", result["blocking_reasons"])

    def test_one_complete_view_registers_and_enforces_two_dimensions(self):
        grant = deepcopy(self.grant)
        grant["limits"].extend({"resource_class": name, "dimension": "TOKENS", "limit_mode": "RESERVABLE_LIMIT",
                                "ordinary_limit": 10, "finalization_reserve": 0}
                               for name in ("MODEL_INFERENCE", "REMOTE_CI"))
        ledger = ResourceLedger(Path(self.tmp.name) / "two-dimensions.sqlite")
        ledger.initialize(); original_grant = ledger.register_grant(grant)
        words = "Both resources share ten dollars and four tokens."
        source = decision(grant, owner_constraints=[words])
        def view(ref, limit_id, dimension, total):
            linked = deepcopy(source); linked["artifact_id"] = ref; linked["related_artifacts"].append(ODR)
            linked["resource_interpretation"] = {"source_text": words, "unresolved_constraints": [],
                "unresolved_qualifications": [], "shared_limits": [{"limit_id": limit_id, "dimension": dimension,
                "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": total}]}
            return linked
        usd = view("COMPLETE-VIEW", "USD-TOTAL", "USD", 10)
        usd["resource_interpretation"]["shared_limits"].append({"limit_id": "TOKEN-TOTAL", "dimension": "TOKENS",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": 4})
        auth = {ODR: source, "COMPLETE-VIEW": usd}
        entries = []
        for dim in ("USD", "TOKENS"):
            for name in ("MODEL_INFERENCE", "REMOTE_CI"):
                entry = item(upper=1, dim=dim); entry["resource_class"] = name; entries.append(entry)
        e = estimate(*entries)
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": limit_id,
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "estimate_state": "ESTIMATED",
            "upper_bound": 2, "basis_refs": ["basis:1"]} for limit_id in ("USD-TOTAL", "TOKEN-TOTAL")]
        before = run(ledger, g=grant, e=e, auth=auth, resource_interpretation_ref="COMPLETE-VIEW")
        self.assertEqual(before["blocking_reasons"], ["SHARED_LIMIT_REGISTRATION_REQUIRED"], before)
        ledger.register_owner_shared_limits("G-LEAF", auth.get, "COMPLETE-VIEW")
        result = run(ledger, g=grant, e=e, auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual(result["resource_interpretation_ref"], "COMPLETE-VIEW")
        self.assertEqual({entry["dimension"] for entry in result["shared_evaluations"]}, {"USD", "TOKENS"})
        self.assertEqual(ledger.get_grant("G-LEAF"), original_grant)
        ledger.reserve("G-LEAF", "MODEL_INFERENCE", "TOKENS", 3, "T1", "OP-T1", "KEY-T1", now=NOW)
        with self.assertRaises(InsufficientCapacity):
            ledger.reserve("G-LEAF", "REMOTE_CI", "TOKENS", 2, "T2", "OP-T2", "KEY-T2", now=NOW)


    def test_overlapping_total_and_narrower_limit_both_apply(self):
        words = "The two resources share ten dollars, with five for inference."
        source = decision(self.grant, owner_constraints=[words])
        def view(ref, limit_id, classes, total):
            linked = deepcopy(source); linked["artifact_id"] = ref; linked["related_artifacts"].append(ODR)
            linked["resource_interpretation"] = {"source_text": words, "unresolved_constraints": [],
                "unresolved_qualifications": [], "shared_limits": [{"limit_id": limit_id, "dimension": "USD",
                "resource_classes": classes, "total_limit": total}]}
            return linked
        full = view("VIEW-FULL", "FULL", ["MODEL_INFERENCE", "REMOTE_CI"], 10)
        full["resource_interpretation"]["shared_limits"].append({"limit_id": "NARROW", "dimension": "USD",
            "resource_classes": ["MODEL_INFERENCE"], "total_limit": 5})
        auth = {ODR: source, "VIEW-FULL": full}
        self.ledger.register_owner_shared_limits("G-LEAF", auth.get, "VIEW-FULL")
        e = self.estimate("MODEL_INFERENCE", "REMOTE_CI", upper=3)
        e["shared_estimates"] = [{"grant_ref": "G-LEAF", "limit_id": "FULL",
            "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "estimate_state": "ESTIMATED",
            "upper_bound": 6, "basis_refs": ["basis:1"]}]
        result = run(self.ledger, g=self.grant, e=e, auth=auth)
        self.assertEqual(result["status"], "ADMISSIBLE", result)
        self.assertEqual({entry["limit_id"] for entry in result["shared_evaluations"]}, {"FULL", "NARROW"})
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("G-LEAF", "MODEL_INFERENCE", "USD", 6, "TOO-MUCH", "OP", "KEY", now=NOW)

    def test_unrelated_resource_does_not_require_shared_registration(self):
        self.grant["scope"]["resource_classes"].append("PAID_TOOL")
        self.grant["limits"].append({"resource_class": "PAID_TOOL", "dimension": "TOKENS",
                                     "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 10,
                                     "finalization_reserve": 0})
        self.owner = decision(self.grant)
        self.owner["resource_interpretation"] = {
            "source_text": "The two dollar resources share a total budget of ten.",
            "unresolved_constraints": [], "unresolved_qualifications": [],
            "shared_limits": [{"limit_id": "BUDGET-1", "dimension": "USD",
                               "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
                               "total_limit": 10, "finalization_reserve": 0}],
        }
        self.auth = {ODR: self.owner}
        ledger = ResourceLedger(Path(self.tmp.name) / "other.sqlite")
        ledger.initialize()
        ledger.register_grant(self.grant)
        e = item(upper=2, dim="TOKENS"); e["resource_class"] = "PAID_TOOL"
        self.assertEqual(run(ledger, g=self.grant, e=estimate(e), auth=self.auth)["status"], "ADMISSIBLE")


if __name__ == "__main__":
    unittest.main()
