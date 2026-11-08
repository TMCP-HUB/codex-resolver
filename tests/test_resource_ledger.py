from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_DOWN, ROUND_UP, localcontext
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from tools.resource_ledger import (
    AuthorityViolation,
    GrantExpired,
    IdempotencyConflict,
    InsufficientCapacity,
    InvalidGrant,
    InvalidReservationTransition,
    ResourceLedger,
    ResourceLedgerError,
)

UTC = timezone.utc
T0 = datetime(2026, 9, 20, 0, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 20, 1, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 20, 2, 0, tzinfo=UTC)
FUTURE = "2030-01-01T00:00:00Z"
PURPOSES = ["RESULT_RECONCILIATION", "DURABLE_PARTIAL_OUTPUT", "FINAL_ACCOUNTING", "CONTROL_HANDOFF"]


def grant(
    grant_id: str = "G-ROOT",
    *,
    ordinary=5,
    final=2,
    mode="RESERVABLE_LIMIT",
    attempts=10,
    valid_until=FUTURE,
    scope_ref="project:p",
    candidate_ref=None,
    route_ref=None,
    purposes=None,
    resource_classes=None,
    limits=None,
):
    classes = resource_classes or ["MODEL_INFERENCE"]
    if limits is None:
        if mode == "OBSERVATION_ONLY":
            limits = [{
                "resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                "ordinary_limit": None, "finalization_reserve": None,
            }]
        else:
            limits = [{
                "resource_class": "MODEL_INFERENCE", "dimension": "TOKENS", "limit_mode": mode,
                "ordinary_limit": ordinary, "finalization_reserve": final,
            }]
    return {
        "artifact_type": "RESOURCE_GRANT",
        "artifact_id": grant_id,
        "produced_by_role": "control-director",
        "assignment_id": "A-1",
        "input_state_ref": "STATE-1",
        "status": "AUTHORIZED",
        "provenance": ["owner:approval"],
        "related_artifacts": [],
        "issued_by": "control-director",
        "authority_source": {
            "authority_type": "OWNER_APPROVED_RESOURCE_AUTHORITY",
            "authority_ref": "authority:owner-1",
        },
        "parent_grant_ref": None,
        "scope": {
            "scope_ref": scope_ref,
            "candidate_ref": candidate_ref,
            "route_ref": route_ref,
            "resource_classes": classes,
        },
        "limits": limits,
        "attempt_limit": attempts,
        "valid_until": valid_until,
        "finalization_policy": {"protected": True, "allowed_purposes": purposes or PURPOSES[:]},
    }


def child(parent, child_id="G-CHILD", **changes):
    c = deepcopy(parent)
    c["artifact_id"] = child_id
    c["provenance"] = ["parent:delegation"]
    c["authority_source"] = {
        "authority_type": "PARENT_RESOURCE_GRANT",
        "authority_ref": parent["artifact_id"],
    }
    c["parent_grant_ref"] = parent["artifact_id"]
    for key, value in changes.items():
        if key in {"scope_ref", "candidate_ref", "route_ref", "resource_classes"}:
            c["scope"][key] = value
        elif key == "purposes":
            c["finalization_policy"]["allowed_purposes"] = value
        else:
            c[key] = value
    return c


def evidence(child_scope="task:t", parent_scope="project:p", ref="scope-proof:123"):
    return {
        "child_scope_ref": child_scope,
        "parent_scope_ref": parent_scope,
        "evidence_ref": ref,
    }


class ResourceLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "shared.sqlite3")
        self.ledger = ResourceLedger(self.db)
        self.ledger.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def register(self, g=None):
        g = g or grant()
        self.ledger.register_grant(g)
        return g

    def reserve(self, *, gid="G-ROOT", qty=1, rid="R-1", op="OP-1", key="idem-r1", pool="ORDINARY", purpose=None, expires=None, now=T0):
        return self.ledger.reserve(
            gid, "MODEL_INFERENCE", "TOKENS", qty, rid, op, key,
            pool=pool, purpose=purpose, expires_at=expires, now=now,
        )

    def test_01_shared_file_ledger_initializes(self):
        self.assertTrue(Path(self.db).exists())
        self.ledger.initialize()

    def test_02_memory_authority_backend_is_rejected(self):
        for path in [":memory:", "file::memory:?cache=shared", "file:ledger?mode=memory&cache=shared"]:
            with self.subTest(path=path), self.assertRaises(ResourceLedgerError):
                ResourceLedger(path)

    def test_03_valid_root_grant_registers_and_reads_back(self):
        self.register()
        self.assertEqual(self.ledger.get_grant("G-ROOT")["limits"][0]["ordinary_limit"], Decimal("5"))

    def test_04_same_semantic_root_registration_is_idempotent(self):
        g = self.register()
        reordered = dict(reversed(list(g.items())))
        self.ledger.register_grant(reordered)
        self.assertEqual(self.ledger.get_grant("G-ROOT")["artifact_id"], "G-ROOT")

    def test_05_conflicting_same_grant_id_fails(self):
        g = self.register()
        conflict = deepcopy(g)
        conflict["limits"][0]["ordinary_limit"] = 6
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_grant(conflict)

    def test_06_equal_scope_child_passes_without_evidence(self):
        p = self.register()
        self.ledger.register_child_grant(child(p))
        self.assertIsNone(self.ledger.get_scope_relation_evidence("G-CHILD"))

    def test_07_different_scope_without_evidence_fails(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, scope_ref="task:t"))

    def test_08_different_scope_bare_tuple_relation_fails(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, scope_ref="task:t"), {("task:t", "project:p")})

    def test_09_different_scope_matching_durable_evidence_passes(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        self.assertEqual(self.ledger.get_scope_relation_evidence("G-CHILD")["evidence_ref"], "scope-proof:123")

    def test_10_scope_evidence_mismatched_refs_fail(self):
        p = self.register()
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(
                child(p, scope_ref="task:t"), evidence(child_scope="task:other")
            )

    def test_11_scope_evidence_survives_reopen(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        reopened = ResourceLedger(self.db)
        self.assertEqual(reopened.get_scope_relation_evidence("G-CHILD"), evidence())

    def test_12_conflicting_scope_evidence_reregistration_fails(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        self.ledger.register_child_grant(c, evidence())
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, evidence(ref="scope-proof:other"))

    def test_13_get_grant_does_not_expose_scope_evidence_metadata(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, scope_ref="task:t"), evidence())
        out = self.ledger.get_grant("G-CHILD")
        self.assertNotIn("scope_relation_evidence", out)
        self.assertNotIn("evidence_ref", repr(out))

    def test_14_root_scope_evidence_readback_is_null(self):
        self.register()
        self.assertIsNone(self.ledger.get_scope_relation_evidence("G-ROOT"))

    def test_15_resource_class_expansion_fails(self):
        p = self.register()
        c = child(p, resource_classes=["MODEL_INFERENCE", "REMOTE_CI"])
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_16_candidate_binding_expansion_fails(self):
        p = grant(candidate_ref="candidate:c")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, candidate_ref="candidate:other"))

    def test_17_route_binding_expansion_fails(self):
        p = grant(route_ref="route:r")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, route_ref=None))

    def test_18_child_attempt_expansion_fails(self):
        p = grant(attempts=3)
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, attempt_limit=4))

    def test_19_child_validity_expansion_fails(self):
        p = grant(valid_until="2026-09-20T02:00:00Z")
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, valid_until="2026-09-20T03:00:00Z"))

    def test_20_hard_to_reservable_narrowing_passes(self):
        p = grant(mode="HARD_LIMIT")
        self.register(p)
        c = child(p)
        c["limits"][0]["limit_mode"] = "RESERVABLE_LIMIT"
        self.ledger.register_child_grant(c)

    def test_21_reservable_to_hard_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["limit_mode"] = "HARD_LIMIT"
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_22_observation_parent_to_spend_authority_fails(self):
        p = grant(mode="OBSERVATION_ONLY")
        self.register(p)
        c = child(p)
        c["limits"][0].update(limit_mode="RESERVABLE_LIMIT", ordinary_limit=1, finalization_reserve=0)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_23_child_ordinary_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["ordinary_limit"] = 6
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_24_child_finalization_expansion_fails(self):
        p = self.register()
        c = child(p)
        c["limits"][0]["finalization_reserve"] = 3
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c)

    def test_25_child_finalization_purpose_expansion_fails(self):
        p = grant(purposes=["FINAL_ACCOUNTING"])
        self.register(p)
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(child(p, purposes=["FINAL_ACCOUNTING", "CONTROL_HANDOFF"]))

    def test_26_child_purpose_subset_passes(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, purposes=["FINAL_ACCOUNTING"]))

    def test_27_ordinary_reserve_succeeds(self):
        self.register()
        result = self.reserve(qty=2)
        self.assertEqual(result["status"], "RESERVED")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("2"))

    def test_28_ordinary_cannot_borrow_finalization_capacity(self):
        self.register(grant(ordinary=1, final=9))
        self.reserve(qty=1)
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=1, rid="R-2", op="OP-2", key="K-2")

    def test_29_finalization_requires_purpose(self):
        self.register()
        with self.assertRaises(AuthorityViolation):
            self.reserve(pool="FINALIZATION")

    def test_30_unauthorized_finalization_purpose_fails(self):
        self.register(grant(purposes=["FINAL_ACCOUNTING"]))
        with self.assertRaises(AuthorityViolation):
            self.reserve(pool="FINALIZATION", purpose="CONTROL_HANDOFF")

    def test_31_finalization_is_ancestor_bounded(self):
        p = grant(final=1)
        self.register(p)
        c = child(p)
        self.ledger.register_child_grant(c)
        self.reserve(gid="G-CHILD", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        with self.assertRaises(InsufficientCapacity):
            self.reserve(gid="G-CHILD", rid="R-2", op="O-2", key="K-2", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")

    def test_32_same_reserve_retry_is_idempotent(self):
        self.register()
        first = self.reserve()
        second = self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, "R-1", "OP-1", "idem-r1", now=T1)
        self.assertEqual(first, second)

    def test_33_conflicting_idempotency_key_fails(self):
        self.register()
        self.reserve()
        with self.assertRaises(IdempotencyConflict):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R-2", "OP-2", "idem-r1", now=T0)

    def test_34_conflicting_reservation_id_fails(self):
        self.register()
        self.reserve()
        with self.assertRaises(IdempotencyConflict):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R-1", "OP-X", "K-X", now=T0)

    def test_35_commit_converts_reserved_to_committed(self):
        self.register()
        self.reserve(qty=3)
        out = self.ledger.commit("R-1", 3, "C-1", now=T1)
        self.assertEqual(out["status"], "COMMITTED")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["reserved"], state["committed"]), (Decimal("0"), Decimal("3")))

    def test_36_commit_smaller_releases_remainder(self):
        self.register()
        self.reserve(qty=4)
        self.ledger.commit("R-1", 1, "C-1", now=T1)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("4"))

    def test_37_commit_greater_than_reserved_records_the_reported_amount(self):
        self.register()
        self.reserve(qty=1)
        result = self.ledger.commit("R-1", 2, "C-1", now=T1, measurement_source_ref="usage:receipt-1")
        self.assertEqual((result["quantity"], result["committed_quantity"], result["actual_over_reservation"]),
                         (Decimal(1), Decimal(2), Decimal(1)))
        self.assertEqual(result["measurement_source_refs"], ["usage:receipt-1"])
        self.assertEqual(self.ledger.get_reservation("R-1"), result)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["committed"], state["available"]), (Decimal(2), Decimal(3)))

    def test_38_duplicate_commit_is_idempotent(self):
        self.register()
        self.reserve(qty=2)
        first = self.ledger.commit("R-1", 1, "C-1", now=T1)
        second = self.ledger.commit("R-1", 1, "C-1", now=T2)
        self.assertEqual(first, second)

    def test_39_release_restores_availability(self):
        self.register()
        self.reserve(qty=3)
        self.ledger.release("R-1", "REL-1")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_40_duplicate_release_is_idempotent(self):
        self.register()
        self.reserve()
        first = self.ledger.release("R-1", "REL-1")
        second = self.ledger.release("R-1", "REL-1")
        self.assertEqual(first, second)

    def test_41_late_observation_after_release_preserves_release(self):
        self.register()
        self.reserve()
        release = self.ledger.release("R-1", "REL-1")
        actual = self.ledger.commit("R-1", 2, "C-1", now=T1, measurement_source_ref="usage:late")
        self.assertEqual((release["status"], actual["status"]), ("RELEASED", "RELEASED"))
        self.assertEqual(actual["committed_quantity"], Decimal(2))
        self.assertEqual(actual["measurement_source_refs"], ["usage:late"])
        self.assertEqual(self.ledger.commit("R-1", 2, "C-1", now=T2, measurement_source_ref="usage:late"), actual)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["committed"], Decimal(2))

    def test_42_expiry_restores_availability(self):
        self.register()
        self.reserve(qty=4, expires=T1)
        self.assertEqual(self.ledger.expire_reservations(T1), ["R-1"])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_43_fractional_expiry_not_due_at_whole_second(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(expires=half)
        self.assertEqual(self.ledger.expire_reservations(T1), [])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("1"))

    def test_44_fractional_expiry_due_at_exact_instant(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(expires=half)
        self.assertEqual(self.ledger.expire_reservations(half), ["R-1"])

    def test_45_mixed_fractional_expiry_only_due_row_expires(self):
        self.register()
        half = T1 + timedelta(microseconds=500000)
        self.reserve(rid="R-1", op="O-1", key="K-1", expires=T1)
        self.reserve(rid="R-2", op="O-2", key="K-2", expires=half)
        self.assertEqual(self.ledger.expire_reservations(T1), ["R-1"])
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("1"))

    def test_46_timezone_offset_expiry_is_chronological(self):
        self.register()
        self.reserve(expires="2026-09-20T08:00:00+07:00")
        self.assertEqual(self.ledger.expire_reservations("2026-09-20T01:00:00Z"), ["R-1"])

    def test_47_persisted_timestamp_has_fixed_microsecond_utc_format(self):
        self.register()
        out = self.reserve(expires=T1)
        self.assertEqual(out["created_at"], "2026-09-20T00:00:00.000000Z")
        self.assertEqual(out["expires_at"], "2026-09-20T01:00:00.000000Z")

    def test_48_malformed_stored_expiry_fails_closed_and_rolls_back(self):
        self.register()
        self.reserve(rid="R-1", op="O-1", key="K-1", expires=T1)
        self.reserve(rid="R-2", op="O-2", key="K-2", expires=T1)
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("UPDATE reservations SET expires_at='bad-timestamp' WHERE reservation_id='R-2'")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaises(ResourceLedgerError):
            self.ledger.expire_reservations(T1)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual(state["reserved"], Decimal("2"))

    def test_49_committed_usage_does_not_expire(self):
        self.register()
        self.reserve(qty=2, expires=T2)
        self.ledger.commit("R-1", 2, "C-1", now=T1)
        self.assertEqual(self.ledger.expire_reservations(T2), [])

    def test_50_expired_grant_rejects_new_reserve(self):
        self.register(grant(valid_until="2026-09-20T01:00:00Z"))
        with self.assertRaises(GrantExpired):
            self.reserve(now=T1)

    def test_51_pre_expiry_reservation_may_commit_after_grant_expiry(self):
        self.register(grant(valid_until="2026-09-20T01:00:00Z"))
        self.reserve(now=T0)
        self.assertEqual(self.ledger.commit("R-1", 1, "C-1", now=T2)["status"], "COMMITTED")

    def test_52_ten_concurrent_reservations_exactly_five_succeed(self):
        self.register(grant(ordinary=5, final=0))
        barrier = threading.Barrier(10)
        def worker(i):
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, f"R-{i}", f"O-{i}", f"K-{i}", now=T0)
                return "ok"
            except InsufficientCapacity:
                return "capacity"
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(results.count("ok"), 5)
        self.assertEqual(results.count("capacity"), 5)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["reserved"], state["committed"], state["available"]), (Decimal("5"), Decimal("0"), Decimal("0")))

    def test_53_sibling_children_cannot_overspend_shared_parent(self):
        p = grant(ordinary=5, final=0)
        self.register(p)
        self.ledger.register_child_grant(child(p, "C-1"))
        self.ledger.register_child_grant(child(p, "C-2"))
        barrier = threading.Barrier(10)
        def worker(i):
            gid = "C-1" if i % 2 == 0 else "C-2"
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.reserve(gid, "MODEL_INFERENCE", "TOKENS", 1, f"SR-{i}", f"SO-{i}", f"SK-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(sum(results), 5)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["reserved"], Decimal("5"))

    def test_54_atomic_attempt_limit_works(self):
        self.register(grant(attempts=5))
        barrier = threading.Barrier(10)
        def worker(i):
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.claim_attempt("G-ROOT", f"O-{i}", f"K-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(sum(results), 5)

    def test_55_sibling_attempts_cannot_exceed_parent(self):
        p = grant(attempts=4)
        self.register(p)
        self.ledger.register_child_grant(child(p, "C-1", attempt_limit=4))
        self.ledger.register_child_grant(child(p, "C-2", attempt_limit=4))
        barrier = threading.Barrier(8)
        def worker(i):
            gid = "C-1" if i % 2 == 0 else "C-2"
            local = ResourceLedger(self.db)
            barrier.wait()
            try:
                local.claim_attempt(gid, f"O-{i}", f"K-{i}", now=T0)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(worker, range(8)))
        self.assertEqual(sum(results), 4)

    def test_56_duplicate_attempt_is_idempotent(self):
        self.register(grant(attempts=1))
        first = self.ledger.claim_attempt("G-ROOT", "O-1", "K-1", now=T0)
        second = self.ledger.claim_attempt("G-ROOT", "O-1", "K-1", now=T1)
        self.assertEqual(first, second)

    def test_57_observation_only_reserve_fails(self):
        self.register(grant(mode="OBSERVATION_ONLY"))
        with self.assertRaises(AuthorityViolation):
            self.reserve()

    def test_58_read_model_exhaustion_states(self):
        self.register(grant(ordinary=1, final=1))
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "NOT_EXHAUSTED")
        self.reserve(qty=1)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY")
        self.reserve(rid="RF", op="OF", key="KF", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["exhaustion_state"], "EXHAUSTED")

    def test_59_high_precision_grant_round_trips_exactly(self):
        value = Decimal("99999999999999999999999999999")
        self.register(grant(ordinary=value))
        self.assertEqual(self.ledger.get_grant("G-ROOT")["limits"][0]["ordinary_limit"], value)

    def test_60_high_precision_distinct_grants_have_distinct_fingerprints_low_context(self):
        g1 = grant(ordinary=Decimal("99999999999999999999999999999"))
        g2 = grant(ordinary=Decimal("100000000000000000000000000000"))
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            _, fp1 = ResourceLedger._validate_grant(g1)
            _, fp2 = ResourceLedger._validate_grant(g2)
        self.assertNotEqual(fp1, fp2)

    def test_61_full_limit_plus_one_e_minus_28_is_rejected(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        self.reserve(qty=Decimal("1"))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=Decimal("1E-28"), rid="R-2", op="O-2", key="K-2")

    def test_62_one_e_minus_28_reservation_exact_available(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        self.reserve(qty=Decimal("1E-28"))
        available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999999"))

    def test_63_decimal_context_precision_5_round_down_cannot_hide_overspend(self):
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            self.register(grant(ordinary=Decimal("1"), final=0))
            self.reserve(qty=Decimal("1"))
            with self.assertRaises(InsufficientCapacity):
                self.reserve(qty=Decimal("1E-28"), rid="R-2", op="O-2", key="K-2")

    def test_64_decimal_context_precision_50_round_up_same_semantics(self):
        with localcontext(Context(prec=50, rounding=ROUND_UP)):
            self.register(grant(ordinary=Decimal("1"), final=0))
            self.reserve(qty=Decimal("1E-28"))
            available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999999"))

    def test_65_decimal_canonicalization_1_2300(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1.2300")), "1.23")

    def test_66_decimal_canonicalization_1e3(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1E+3")), "1000")

    def test_67_decimal_canonicalization_1e_minus_28(self):
        self.assertEqual(ResourceLedger._decimal_text(Decimal("1E-28")), "0.0000000000000000000000000001")

    def test_68_decimal_canonicalization_large_integer_no_rounding(self):
        text = "99999999999999999999999999999"
        with localcontext(Context(prec=5, rounding=ROUND_UP)):
            self.assertEqual(ResourceLedger._decimal_text(Decimal(text)), text)

    def test_69_commit_zero_releases_all(self):
        self.register()
        self.reserve(qty=2)
        out = self.ledger.commit("R-1", 0, "C-0", now=T1)
        self.assertEqual(out["committed_quantity"], Decimal("0"))
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"], Decimal("5"))

    def test_70_release_after_commit_fails(self):
        self.register()
        self.reserve()
        self.ledger.commit("R-1", 1, "C-1", now=T1)
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.release("R-1", "REL")

    def test_71_late_observation_at_expiry_preserves_expiry_and_records_usage(self):
        self.register()
        self.reserve(qty=2, expires=T1)
        result = self.ledger.commit("R-1", 1, "C-1", now=T1, measurement_source_ref="meter:late")
        self.assertEqual((result["status"], result["committed_quantity"]), ("EXPIRED", Decimal(1)))
        self.assertEqual(result["measurement_source_refs"], ["meter:late"])
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual((state["reserved"], state["committed"], state["available"]), (Decimal(0), Decimal(1), Decimal(4)))

    def test_72_bool_quantity_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=True)

    def test_73_nan_and_infinity_rejected(self):
        self.register()
        for value in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value), self.assertRaises(ResourceLedgerError):
                self.reserve(qty=value)

    def test_74_negative_quantity_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=-1)

    def test_75_zero_reservation_rejected(self):
        self.register()
        with self.assertRaises(ResourceLedgerError):
            self.reserve(qty=0)

    def test_76_invalid_grant_bool_attempt_rejected(self):
        with self.assertRaises(InvalidGrant):
            self.ledger.register_grant(grant(attempts=True))

    def test_77_invalid_grant_naive_valid_until_rejected(self):
        with self.assertRaises(InvalidGrant):
            self.ledger.register_grant(grant(valid_until="2030-01-01T00:00:00"))

    def test_78_parent_unbound_candidate_can_bind_child(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, candidate_ref="candidate:exact"))

    def test_79_parent_unbound_route_can_bind_child(self):
        p = self.register()
        self.ledger.register_child_grant(child(p, route_ref="route:exact"))

    def test_80_finalization_does_not_change_ordinary_pool(self):
        self.register(grant(ordinary=5, final=2))
        self.reserve(qty=2, pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(state["ordinary"]["available"], Decimal("5"))
        self.assertEqual(state["finalization"]["available"], Decimal("0"))

    def test_81_observation_read_model_has_no_spend_authority(self):
        self.register(grant(mode="OBSERVATION_ONLY"))
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertFalse(state["spend_authority"])
        self.assertEqual(state["ordinary"]["authorized"], Decimal("0"))

    def test_82_conflicting_commit_idempotency_key_fails(self):
        self.register()
        self.reserve(qty=2)
        self.ledger.commit("R-1", 1, "CK", now=T1)
        with self.assertRaises(IdempotencyConflict):
            self.ledger.commit("R-1", 2, "CK", now=T2)

    def test_83_conflicting_attempt_idempotency_key_fails(self):
        self.register(grant(attempts=3))
        self.ledger.claim_attempt("G-ROOT", "O-1", "AK", now=T0)
        with self.assertRaises(IdempotencyConflict):
            self.ledger.claim_attempt("G-ROOT", "O-2", "AK", now=T1)

    def test_84_scope_evidence_registration_is_atomic_with_grant(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        bad = evidence(ref="")
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, bad)
        with self.assertRaises(AuthorityViolation):
            self.ledger.get_grant("G-CHILD")

    def test_85_scope_evidence_conflict_does_not_mutate_preserved_record(self):
        p = self.register()
        c = child(p, scope_ref="task:t")
        self.ledger.register_child_grant(c, evidence())
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(c, evidence(ref="scope-proof:conflict"))
        self.assertEqual(self.ledger.get_scope_relation_evidence("G-CHILD"), evidence())

    def test_86_exact_child_capacity_comparison_independent_of_context(self):
        p = grant(ordinary=Decimal("1"))
        self.register(p)
        c = child(p)
        c["limits"][0]["ordinary_limit"] = Decimal("1.0000000000000000000000000001")
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            with self.assertRaises(AuthorityViolation):
                self.ledger.register_child_grant(c)

    def test_87_available_exact_after_multiple_tiny_reservations(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        for i in range(3):
            self.reserve(qty=Decimal("1E-28"), rid=f"R-{i}", op=f"O-{i}", key=f"K-{i}")
        available = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["available"]
        self.assertEqual(available, Decimal("0.9999999999999999999999999997"))

    def test_88_exact_committed_totals_ignore_ambient_context(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        for i in range(2):
            self.reserve(qty=Decimal("1E-28"), rid=f"R-{i}", op=f"O-{i}", key=f"K-{i}")
            self.ledger.commit(f"R-{i}", Decimal("1E-28"), f"C-{i}", now=T1)
        with localcontext(Context(prec=5, rounding=ROUND_UP)):
            state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]
        self.assertEqual(state["committed"], Decimal("2E-28"))
        self.assertEqual(state["available"], Decimal("0.9999999999999999999999999998"))

    def test_89_no_datetime_text_ordering_in_expiry_sql(self):
        source = Path(__file__).resolve().parents[1].joinpath("tools/resource_ledger.py").read_text()
        self.assertNotIn("expires_at <= ?", source)
        self.assertNotIn("expires_at < ?", source)

    def test_90_no_decimal_normalize_in_production(self):
        source = Path(__file__).resolve().parents[1].joinpath("tools/resource_ledger.py").read_text()
        self.assertNotIn(".normalize(", source)

    def test_91_same_authority_semantics_across_decimal_contexts(self):
        def run_case(name, context):
            db = str(Path(self.tmp.name) / f"{name}.sqlite3")
            ledger = ResourceLedger(db)
            ledger.initialize()
            with localcontext(context):
                ledger.register_grant(grant(ordinary=Decimal("1"), final=0))
                ledger.reserve(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS", Decimal("1E-28"),
                    "R-1", "O-1", "K-1", now=T0,
                )
                available_after_tiny = ledger.get_resource_state(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS"
                )["ordinary"]["available"]
                ledger.reserve(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS",
                    Decimal("0.9999999999999999999999999999"),
                    "R-2", "O-2", "K-2", now=T0,
                )
                with self.assertRaises(InsufficientCapacity):
                    ledger.reserve(
                        "G-ROOT", "MODEL_INFERENCE", "TOKENS", Decimal("1E-28"),
                        "R-3", "O-3", "K-3", now=T0,
                    )
                final_available = ledger.get_resource_state(
                    "G-ROOT", "MODEL_INFERENCE", "TOKENS"
                )["ordinary"]["available"]
            return available_after_tiny, final_available

        low = run_case("ctx-low", Context(prec=5, rounding=ROUND_DOWN))
        high = run_case("ctx-high", Context(prec=50, rounding=ROUND_UP))
        self.assertEqual(low, high)
        self.assertEqual(low, (Decimal("0.9999999999999999999999999999"), Decimal("0")))

    def test_overrun_is_visible_on_ancestors_and_reduces_total_remaining(self):
        parent = self.register(grant(ordinary=10, final=2))
        self.ledger.register_child_grant(child(parent))
        self.reserve(gid="G-CHILD", qty=2)
        actual = self.ledger.commit("R-1", 11, "C-1", now=T1, measurement_source_ref="meter:actual")
        self.assertEqual((actual["quantity"], actual["committed_quantity"], actual["actual_over_reservation"]),
                         (Decimal(2), Decimal(11), Decimal(9)))
        for gid in ("G-CHILD", "G-ROOT"):
            state = self.ledger.get_resource_state(gid, "MODEL_INFERENCE", "TOKENS")
            self.assertEqual((state["ordinary"]["committed"], state["ordinary"]["deficit"],
                              state["ordinary"]["available"], state["finalization"]["available"],
                              state["total"]["available"]),
                             (Decimal(11), Decimal(1), Decimal(0), Decimal(1), Decimal(1)))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(gid="G-CHILD", qty=2, rid="F-2", op="OP-F2", key="KEY-F2",
                         pool="FINALIZATION", purpose="FINAL_ACCOUNTING", now=T2)
        self.reserve(gid="G-CHILD", qty=1, rid="F-1", op="OP-F1", key="KEY-F1",
                     pool="FINALIZATION", purpose="FINAL_ACCOUNTING", now=T2)

    def test_overrun_does_not_erase_reservations_already_issued(self):
        self.register(grant(ordinary=5, final=0))
        self.reserve(qty=2, rid="R-A", op="OP-A", key="KEY-A")
        self.reserve(qty=3, rid="R-B", op="OP-B", key="KEY-B")
        self.ledger.commit("R-A", 4, "C-A", now=T1)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["ordinary"]["reserved"], state["ordinary"]["committed"],
                          state["ordinary"]["available"], state["total"]["deficit"]),
                         (Decimal(3), Decimal(4), Decimal(0), Decimal(2)))
        self.assertEqual(self.ledger.get_reservation("R-B")["status"], "RESERVED")
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=1, rid="R-C", op="OP-C", key="KEY-C", now=T1)
        self.assertEqual(self.ledger.commit("R-B", 3, "C-B", now=T2)["committed_quantity"], Decimal(3))
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["total"]["deficit"], Decimal(2))

    def test_late_usage_after_expiry_preserves_status_and_existing_reservations(self):
        self.register(grant(ordinary=5, final=0))
        self.reserve(qty=1, expires=T1)
        self.assertEqual(self.ledger.expire_reservations(T1), ["R-1"])
        self.reserve(qty=5, rid="R-2", op="OP-2", key="KEY-2", now=T1)
        result = self.ledger.commit("R-1", 2, "LATE", now=T2, measurement_source_ref="meter:late-expired")
        self.assertEqual((result["status"], result["committed_quantity"]), ("EXPIRED", Decimal(2)))
        self.assertEqual(self.ledger.get_reservation("R-1")["measurement_source_refs"], ["meter:late-expired"])
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["ordinary"]["reserved"], state["ordinary"]["committed"],
                          state["total"]["available"], state["total"]["deficit"]),
                         (Decimal(5), Decimal(2), Decimal(0), Decimal(2)))
        self.assertEqual(self.ledger.get_reservation("R-2")["status"], "RESERVED")

    def test_recorded_source_and_retries_are_idempotent(self):
        self.register()
        self.reserve(qty=2)
        first = self.ledger.commit("R-1", 3, "C-1", now=T1, measurement_source_ref="meter:first")
        self.assertEqual(self.ledger.commit("R-1", 3, "C-1", now=T2, measurement_source_ref="meter:first"), first)
        second = self.ledger.commit("R-1", 3, "C-2", now=T2, measurement_source_ref="meter:second")
        self.assertEqual(second["measurement_source_refs"], ["meter:first", "meter:second"])
        self.assertEqual(self.ledger.get_reservation("R-1"), second)
        with self.assertRaises(IdempotencyConflict):
            self.ledger.commit("R-1", 3, "C-1", now=T2, measurement_source_ref="meter:second")
        with self.assertRaises(InvalidReservationTransition):
            self.ledger.commit("R-1", 4, "C-3", now=T2, measurement_source_ref="meter:third")
        self.assertEqual(self.ledger.get_reservation("R-1"), second)

    def test_missing_actual_and_missing_source_stay_distinct(self):
        self.register()
        self.reserve()
        with self.assertRaises(ResourceLedgerError):
            self.ledger.commit("R-1", None, "UNKNOWN", now=T1)
        before = self.ledger.get_reservation("R-1")
        self.assertIsNone(before["committed_quantity"])
        self.assertIsNone(before["actual_over_reservation"])
        actual = self.ledger.commit("R-1", 2, "C-1", now=T1)
        self.assertEqual(actual["committed_quantity"], Decimal(2))
        self.assertIsNone(actual["measurement_source_refs"])
        self.assertEqual(actual["actual_over_reservation"], Decimal(1))

    def test_overrun_and_deficit_use_exact_decimals(self):
        self.register(grant(ordinary=Decimal("1"), final=0))
        self.reserve(qty=Decimal("1E-28"))
        actual = Decimal("1.0000000000000000000000000001")
        with localcontext(Context(prec=5, rounding=ROUND_DOWN)):
            result = self.ledger.commit("R-1", actual, "C-1", now=T1, measurement_source_ref="meter:exact")
            state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(result["committed_quantity"], actual)
        self.assertEqual(result["actual_over_reservation"], Decimal("1"))
        self.assertEqual((state["ordinary"]["committed"], state["total"]["deficit"], state["total"]["available"]),
                         (actual, Decimal("1E-28"), Decimal(0)))

    def test_parallel_actual_and_reservation_preserve_the_real_order(self):
        self.register(grant(ordinary=10, final=0))
        self.reserve(qty=5)
        barrier = threading.Barrier(2)
        def record_actual():
            barrier.wait()
            return ResourceLedger(self.db).commit("R-1", 11, "C-1", now=T1, measurement_source_ref="meter:parallel")
        def reserve_other():
            barrier.wait()
            try:
                ResourceLedger(self.db).reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 4,
                                               "R-2", "OP-2", "KEY-2", now=T1)
                return True
            except InsufficientCapacity:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            actual_future = pool.submit(record_actual)
            reserve_future = pool.submit(reserve_other)
            actual, reserved = actual_future.result(), reserve_future.result()
        self.assertEqual(actual["committed_quantity"], Decimal(11))
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(state["ordinary"]["reserved"], Decimal(4 if reserved else 0))
        self.assertEqual(state["total"]["available"], Decimal(0))
        self.assertEqual(state["total"]["deficit"], Decimal(5 if reserved else 1))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(qty=1, rid="R-3", op="OP-3", key="KEY-3", now=T2)

    def test_resource_state_uses_one_snapshot_during_real_pool_transfer(self):
        for journal_mode in ("WAL", "DELETE"):
            with self.subTest(journal_mode=journal_mode):
                db = str(Path(self.tmp.name) / f"snapshot-{journal_mode}.sqlite3")
                writer = ResourceLedger(db, busy_timeout_ms=10000)
                writer.initialize()
                connection = sqlite3.connect(db)
                try:
                    actual_mode = connection.execute(f"PRAGMA journal_mode={journal_mode}").fetchone()[0]
                finally:
                    connection.close()
                self.assertEqual(actual_mode.upper(), journal_mode)
                writer.register_grant(grant(ordinary=5, final=5))
                writer.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 5,
                               "ORD", "OP-ORD", "KEY-ORD", now=T0)
                ordinary_read, resume_read = threading.Event(), threading.Event()
                writer_started, writer_finished = threading.Event(), threading.Event()

                class PausingReader(ResourceLedger):
                    @classmethod
                    def _allocation_totals(cls, conn, gid, resource_class, dimension, pool):
                        totals = super()._allocation_totals(conn, gid, resource_class, dimension, pool)
                        if pool == "ORDINARY":
                            ordinary_read.set()
                            if not resume_read.wait(10):
                                raise TimeoutError("state reader was not resumed")
                        return totals

                def transfer():
                    writer_started.set()
                    try:
                        # Two real writes: after release the used total is zero;
                        # after the new finalization reserve it is five again.
                        writer.release("ORD", "RELEASE-ORD")
                        writer.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 5,
                                       "FINAL", "OP-FINAL", "KEY-FINAL", pool="FINALIZATION",
                                       purpose="FINAL_ACCOUNTING", now=T1)
                    finally:
                        writer_finished.set()

                reader = PausingReader(db, busy_timeout_ms=10000)
                interleaved = None
                with ThreadPoolExecutor(max_workers=2) as pool:
                    state_future = pool.submit(reader.get_resource_state, "G-ROOT", "MODEL_INFERENCE", "TOKENS")
                    try:
                        self.assertTrue(ordinary_read.wait(5))
                        transfer_future = pool.submit(transfer)
                        self.assertTrue(writer_started.wait(5))
                        if journal_mode == "WAL":
                            interleaved = writer_finished.wait(5)
                    finally:
                        # A rollback-journal writer may need this reader to end
                        # before its first commit can complete.
                        resume_read.set()
                    state = state_future.result(timeout=10)
                    transfer_future.result(timeout=10)
                if journal_mode == "WAL":
                    self.assertTrue(interleaved, "WAL writer did not commit while the snapshot was held")
                self.assertEqual((state["ordinary"]["reserved"], state["finalization"]["reserved"],
                                  state["total"]["available"]), (Decimal(5), Decimal(0), Decimal(5)))
                after = writer.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
                self.assertEqual((after["ordinary"]["reserved"], after["finalization"]["reserved"],
                                  after["total"]["available"]), (Decimal(0), Decimal(5), Decimal(5)))


class SharedResourceLimitTest(unittest.TestCase):
    def setUp(self):
        from tests.test_resource_admission import decision
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = ResourceLedger(Path(self.tmp.name) / "ledger.sqlite")
        self.ledger.initialize()
        self.grant = grant(resource_classes=["MODEL_INFERENCE", "REMOTE_CI"], limits=[
            {"resource_class": name, "dimension": "USD", "limit_mode": "RESERVABLE_LIMIT",
             "ordinary_limit": 10, "finalization_reserve": 2}
            for name in ("MODEL_INFERENCE", "REMOTE_CI")
        ])
        self.owner = decision(self.grant)
        self.owner["artifact_id"] = self.grant["authority_source"]["authority_ref"]
        self.owner["resource_interpretation"] = {
            "source_text": "The two resources share a total budget of ten.",
            "unresolved_constraints": [], "unresolved_qualifications": [],
            "shared_limits": [{"limit_id": "BUDGET-1", "dimension": "USD",
                               "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"],
                               "total_limit": 10, "finalization_reserve": 0}],
        }
        self.ledger.register_grant(self.grant)

    def tearDown(self):
        self.tmp.cleanup()

    def bind(self):
        return self.ledger.register_owner_shared_limits(
            self.grant["artifact_id"], lambda ref: self.owner if ref == self.owner["artifact_id"] else None
        )

    def views(self, *totals):
        source = deepcopy(self.owner)
        del source["resource_interpretation"]["shared_limits"]
        records = {source["artifact_id"]: source}
        for index, total in enumerate(totals):
            view = deepcopy(source)
            view["artifact_id"] = f"VIEW-{index}"
            view["related_artifacts"].append(source["artifact_id"])
            view["resource_interpretation"]["shared_limits"] = ([] if total is None else [{
                "limit_id": f"TOTAL-{index}", "dimension": "USD",
                "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": total}])
            records[view["artifact_id"]] = view
        return records

    def correct(self, records, ref, selected):
        return self.ledger.replace_owner_shared_limits(
            "G-ROOT", records.get, ref, expected_snapshot=selected["snapshot"],
            expected_source_fingerprint=selected["source_fingerprint"])

    def reserve(self, resource_class, qty, rid, *, op=None, key=None, **kwargs):
        return self.ledger.reserve("G-ROOT", resource_class, "USD", qty, rid,
                                   op or ("OP-" + rid), key or ("KEY-" + rid), now=T0, **kwargs)

    def test_existing_history_is_included_without_changing_grant(self):
        self.reserve("MODEL_INFERENCE", 6, "OLD")
        before = self.ledger.get_grant("G-ROOT")
        states = self.bind()
        self.assertEqual(states[0]["ordinary"]["reserved"], Decimal("6"))
        self.assertEqual(states[0]["ordinary"]["available"], Decimal("4"))
        self.assertEqual(self.ledger.get_grant("G-ROOT"), before)
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 5, "TOO-MUCH")
        self.reserve("REMOTE_CI", 4, "EXACT")
        self.assertEqual(self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")["ordinary"]["available"], 0)

    def test_shared_total_is_atomic_across_competing_classes(self):
        self.bind()
        barrier = threading.Barrier(2)
        def attempt(name):
            barrier.wait()
            try:
                self.reserve(name, 6, name)
                return "reserved"
            except InsufficientCapacity:
                return "insufficient"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["MODEL_INFERENCE", "REMOTE_CI"]))
        self.assertCountEqual(results, ["reserved", "insufficient"])
        self.assertEqual(self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")["used"], Decimal("6"))

    def test_shared_total_uses_exact_decimal_for_each_ledger_allocation(self):
        self.owner["resource_interpretation"]["shared_limits"][0]["total_limit"] = Decimal("1")
        self.bind()
        self.reserve("MODEL_INFERENCE", Decimal("0.0000000000000000000000000001"), "A")
        self.reserve("REMOTE_CI", Decimal("0.9999999999999999999999999999"), "B")
        self.assertEqual(self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")["used"], Decimal("1"))
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", Decimal("0.0000000000000000000000000001"), "C")

    def test_same_operation_can_have_distinct_costs_and_retry_is_idempotent(self):
        self.bind()
        self.reserve("MODEL_INFERENCE", 3, "R1", op="SAME-OP", key="RETRY")
        self.reserve("MODEL_INFERENCE", 3, "R1", op="SAME-OP", key="RETRY")
        self.reserve("REMOTE_CI", 4, "R2", op="SAME-OP")
        self.assertEqual(self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")["used"], Decimal("7"))

    def test_finalization_reserve_is_inside_owner_total(self):
        self.owner["resource_interpretation"]["shared_limits"][0]["finalization_reserve"] = 2
        self.bind()
        self.reserve("MODEL_INFERENCE", 8, "ORD")
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 1, "ORD-EXTRA")
        self.reserve("REMOTE_CI", 2, "FINAL", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertEqual((state["used"], state["finalization"]["available"]), (Decimal("10"), Decimal("0")))

    def test_authorized_finalization_can_use_common_total_without_separate_protected_reserve(self):
        del self.owner["resource_interpretation"]["shared_limits"][0]["finalization_reserve"]
        self.bind()
        self.reserve("MODEL_INFERENCE", 1, "FINAL", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.reserve("REMOTE_CI", 9, "ORD")
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertEqual(state["finalization_reserve"], Decimal(0))
        self.assertEqual(state["used"], Decimal(10))
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 1, "MORE")

    def test_finalization_can_exceed_protected_portion_without_exceeding_total(self):
        self.owner["resource_interpretation"]["shared_limits"][0]["finalization_reserve"] = 2
        self.bind()
        self.reserve("MODEL_INFERENCE", 2, "FINAL-A", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.reserve("REMOTE_CI", 1, "FINAL-B", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.reserve("REMOTE_CI", 7, "ORD")
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertEqual((state["used"], state["ordinary"]["available"]), (Decimal(10), Decimal(0)))

    def test_over_limit_historical_usage_is_visible_and_blocks_new_reservation(self):
        self.reserve("MODEL_INFERENCE", 8, "A")
        self.reserve("REMOTE_CI", 4, "B")
        state = self.bind()[0]
        self.assertEqual(state["used"], Decimal("12"))
        self.assertTrue(state["over_limit"])
        self.assertEqual(state["ordinary"]["available"], Decimal("0"))
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 1, "C")

    def test_root_decision_must_authorize_the_linked_budget(self):
        self.owner["resource_interpretation"]["unresolved_constraints"] = ["only after approval"]
        with self.assertRaises(AuthorityViolation):
            self.bind()
        self.assertEqual(self.ledger.get_shared_limits("G-ROOT"), [])

    def test_parent_shared_total_covers_competing_child_grants(self):
        self.bind()
        for name in ("C-A", "C-B"):
            self.ledger.register_child_grant(child(self.grant, child_id=name))
        self.ledger.reserve("C-A", "MODEL_INFERENCE", "USD", 6, "R-A", "OP-A", "ID-A", now=T0)
        with self.assertRaises(InsufficientCapacity):
            self.ledger.reserve("C-B", "REMOTE_CI", "USD", 5, "R-B", "OP-B", "ID-B", now=T0)
        self.assertEqual(self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")["used"], Decimal("6"))

    def test_conflicting_view_requires_explicit_correction_and_keeps_history(self):
        records = self.views(9, 10, 5, None)
        original, original_grant = deepcopy(records), self.ledger.get_grant("G-ROOT")
        self.ledger.register_owner_shared_limits("G-ROOT", records.get, "VIEW-0")
        self.reserve("MODEL_INFERENCE", 8, "BEFORE")
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_owner_shared_limits("G-ROOT", records.get, "VIEW-1")
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 2, "BLOCKED")
        first = self.ledger.get_owner_shared_selection("G-ROOT")
        state = self.correct(records, "VIEW-1", first)[0]
        self.assertEqual((state["used"], state["ordinary"]["available"]), (Decimal(8), Decimal(2)))
        second = self.ledger.get_owner_shared_selection("G-ROOT")
        self.assertEqual(second["lineage"][-1]["snapshot"], first["snapshot"])
        state = self.correct(records, "VIEW-2", second)[0]
        self.assertEqual((state["used"], state["deficit"], state["ordinary"]["available"]),
                         (Decimal(8), Decimal(3), Decimal(0)))
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 1, "AFTER")
        self.assertEqual(self.ledger.get_reservation("BEFORE")["quantity"], Decimal(8))
        third = self.ledger.get_owner_shared_selection("G-ROOT")
        self.assertEqual(self.correct(records, "VIEW-3", third), [])
        self.assertEqual(self.ledger.get_owner_shared_selection("G-ROOT")["interpretation_ref"], "VIEW-3")
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_owner_shared_limits("G-ROOT", records.get, "VIEW-0")
        self.assertEqual(self.ledger.get_grant("G-ROOT"), original_grant)
        self.assertEqual(records, original)

    def test_correction_uses_one_atomic_compare_and_swap(self):
        records = self.views(9, 10, 5)
        self.ledger.register_owner_shared_limits("G-ROOT", records.get, "VIEW-0")
        selected = self.ledger.get_owner_shared_selection("G-ROOT")
        barrier = threading.Barrier(2)
        def attempt(ref):
            barrier.wait()
            try:
                self.correct(records, ref, selected)
                return "updated"
            except AuthorityViolation:
                return "stale"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["VIEW-1", "VIEW-2"]))
        self.assertCountEqual(results, ["updated", "stale"])
        actual = self.ledger.get_owner_shared_selection("G-ROOT")
        self.assertIn(actual["interpretation_ref"], {"VIEW-1", "VIEW-2"})
        self.assertEqual(len(actual["lineage"]), 1)

    def test_late_overrun_after_correction_counts_and_keeps_measurement(self):
        records = self.views(9, 10)
        self.ledger.register_owner_shared_limits("G-ROOT", records.get, "VIEW-0")
        self.reserve("MODEL_INFERENCE", 5, "LATE")
        self.ledger.release("LATE", "RELEASE-LATE", now=T1)
        self.reserve("REMOTE_CI", 4, "STILL-RESERVED")
        selected = self.ledger.get_owner_shared_selection("G-ROOT")
        self.correct(records, "VIEW-1", selected)
        self.ledger.commit("LATE", 8, "COMMIT-LATE", now=T2, measurement_source_ref="meter:late")
        state = self.ledger.get_shared_limit_state("G-ROOT", "TOTAL-1")
        self.assertEqual((state["used"], state["deficit"]), (Decimal(12), Decimal(2)))
        self.assertEqual(self.ledger.get_reservation("LATE")["measurement_source_refs"], ["meter:late"])
        self.assertEqual(self.ledger.get_reservation("STILL-RESERVED")["status"], "RESERVED")
        with self.assertRaises(InsufficientCapacity):
            self.reserve("REMOTE_CI", 1, "TOO-LATE")

    def test_one_view_enforces_distinct_dimensions_and_overlapping_groups(self):
        from tests.test_resource_admission import decision
        other = ResourceLedger(Path(self.tmp.name) / "multiple.sqlite")
        other.initialize()
        mixed = deepcopy(self.grant)
        for name in ("MODEL_INFERENCE", "REMOTE_CI"):
            mixed["limits"].append({"resource_class": name, "dimension": "TOKENS",
                "limit_mode": "RESERVABLE_LIMIT", "ordinary_limit": 10, "finalization_reserve": 0})
        owner = decision(mixed)
        owner["artifact_id"] = mixed["authority_source"]["authority_ref"]
        broad = {"limit_id": "USD-ALL", "dimension": "USD",
                 "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": 10}
        owner["resource_interpretation"] = {
            "source_text": "The dollar and token totals and the inference sublimit apply.",
            "unresolved_constraints": [], "unresolved_qualifications": [],
            "shared_limits": [broad, {**broad, "limit_id": "USD-ALIAS"},
                {"limit_id": "USD-INFERENCE", "dimension": "USD",
                 "resource_classes": ["MODEL_INFERENCE"], "total_limit": 4},
                {"limit_id": "TOKENS-ALL", "dimension": "TOKENS",
                 "resource_classes": ["MODEL_INFERENCE", "REMOTE_CI"], "total_limit": 3}]}
        other.register_grant(mixed)
        other.register_owner_shared_limits("G-ROOT", lambda ref: owner if ref == owner["artifact_id"] else None)
        self.assertEqual(len(other.get_shared_limits("G-ROOT")), 3)
        def reserve(name, dimension, amount, identity):
            return other.reserve("G-ROOT", name, dimension, amount, identity,
                                 "OP-" + identity, "KEY-" + identity, now=T0)
        reserve("MODEL_INFERENCE", "USD", 4, "I-USD")
        with self.assertRaises(InsufficientCapacity):
            reserve("MODEL_INFERENCE", "USD", 1, "OVER-SUBLIMIT")
        reserve("REMOTE_CI", "USD", 6, "R-USD")
        reserve("MODEL_INFERENCE", "TOKENS", 3, "I-TOKENS")
        with self.assertRaises(InsufficientCapacity):
            reserve("REMOTE_CI", "TOKENS", 1, "OVER-TOKENS")


    def test_unreserved_facts_affect_shared_total_and_unknown_is_not_zero(self):
        self.bind()
        self.ledger.record_unreserved_usage("G-ROOT", "MODEL_INFERENCE", "USD", 3, "U")
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertEqual((state["used"], state["ordinary"]["available"]), (3, 7))
        self.ledger.record_unreserved_usage("G-ROOT", "MODEL_INFERENCE", "USD", None, "U", expected_revision=1)
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertIsNone(state["used"])
        self.assertIsNone(state["ordinary"]["available"])
        with self.assertRaises(ResourceLedgerError):
            self.reserve("REMOTE_CI", 1, "REMOTE")

    def test_observation_only_child_unknown_does_not_block_shared_finite_work(self):
        self.bind()
        leaf = child(self.grant, limits=[{"resource_class": "MODEL_INFERENCE", "dimension": "USD",
            "limit_mode": "OBSERVATION_ONLY", "ordinary_limit": None, "finalization_reserve": None}],
            resource_classes=["MODEL_INFERENCE"])
        self.ledger.register_child_grant(leaf)
        self.ledger.record_unreserved_usage("G-CHILD", "MODEL_INFERENCE", "USD", None, "U")
        state = self.ledger.get_shared_limit_state("G-ROOT", "BUDGET-1")
        self.assertIsNone(state["used"])
        self.assertEqual(state["ordinary"]["available"], 10)
        self.assertEqual(state["availability_basis"], "KNOWN_RECORDED_ONLY")
        self.assertIsNone(state["deficit"])
        self.assertIsNone(state["over_limit"])
        per_class = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "USD")
        self.assertEqual(per_class["exhaustion_state"], "UNKNOWN")
        self.assertEqual(per_class["ordinary"]["available"], 10)
        self.reserve("REMOTE_CI", 1, "REMOTE")


class PerClassCorrectionLedgerTest(unittest.TestCase):
    def setUp(self):
        from tests.test_resource_admission import decision
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = ResourceLedger(Path(self.tmp.name) / "ledger.sqlite")
        self.ledger.initialize()
        self.original = grant(ordinary=5, final=0)
        self.source = decision(self.original)
        self.source["artifact_id"] = self.original["authority_source"]["authority_ref"]
        self.source["resource_interpretation"] = {"source_text": "Use the budget specified by the Owner source.",
            "unresolved_constraints": [], "unresolved_qualifications": []}
        self.auth = {self.source["artifact_id"]: self.source}
        self.ledger.register_grant(self.original)

    def tearDown(self):
        self.tmp.cleanup()

    def view(self, name, amount):
        result = deepcopy(self.source)
        result["artifact_id"] = name
        result["related_artifacts"].append(self.source["artifact_id"])
        result["authorized_resource_limits"][0]["ordinary_limit"] = amount
        self.auth[name] = result
        return result

    def snapshot(self, name=None):
        return self.ledger.get_owner_resource_snapshot("G-ROOT", self.auth.get, name)

    def correct(self, name, snapshot):
        return self.ledger.replace_owner_per_class_limits("G-ROOT", self.auth.get, name, expected_snapshot=snapshot)

    def reserve(self, amount, rid, gid="G-ROOT"):
        return self.ledger.reserve(gid, "MODEL_INFERENCE", "TOKENS", amount, rid,
                                   "OP-" + rid, "KEY-" + rid, now=T0)

    def test_successive_corrections_preserve_each_value_and_late_usage(self):
        self.view("VIEW-10", 10)
        self.view("VIEW-5", 5)
        original_grant, original_source = self.ledger.get_grant("G-ROOT"), deepcopy(self.source)
        self.reserve(4, "PAID")
        self.ledger.commit("PAID", 4, "COMMIT-PAID", now=T1, measurement_source_ref="meter:paid")
        self.reserve(1, "LATE")
        self.ledger.release("LATE", "RELEASE-LATE", now=T1)
        self.correct("VIEW-10", self.snapshot("VIEW-10"))
        self.reserve(4, "OUTSTANDING")
        self.correct("VIEW-5", self.snapshot("VIEW-5"))
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["total"]["committed"], state["total"]["reserved"],
                          state["total"]["available"], state["total"]["deficit"]),
                         (Decimal(4), Decimal(4), Decimal(0), Decimal(3)))
        self.assertEqual(self.reserve(4, "OUTSTANDING")["status"], "RESERVED")
        self.ledger.commit("LATE", 3, "COMMIT-LATE", now=T2, measurement_source_ref="meter:late")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["total"]["committed"], state["total"]["reserved"], state["total"]["deficit"]),
                         (Decimal(7), Decimal(4), Decimal(6)))
        self.assertEqual(self.ledger.get_reservation("LATE")["measurement_source_refs"], ["meter:late"])
        self.assertEqual(self.ledger.get_reservation("OUTSTANDING")["status"], "RESERVED")
        events = [entry for entry in self.ledger.get_owner_shared_selection("G-ROOT")["lineage"]
                  if entry.get("kind") == "PER_CLASS_CORRECTION"]
        self.assertEqual([(event["previous_limits"][0]["ordinary_limit"], event["effective_limits"][0]["ordinary_limit"])
                          for event in events], [("5", "10"), ("10", "5")])
        self.assertEqual([event["interpretation_ref"] for event in events], ["VIEW-10", "VIEW-5"])
        self.assertEqual(self.ledger.get_grant("G-ROOT"), original_grant)
        self.assertEqual(self.source, original_source)

    def test_children_use_current_parent_without_expanding_existing_children(self):
        self.view("VIEW-10", 10)
        self.view("VIEW-5", 5)
        self.ledger.register_child_grant(child(self.original, "OLD-CHILD"))
        self.correct("VIEW-10", self.snapshot("VIEW-10"))
        new_child = child(self.original, "NEW-CHILD")
        new_child["limits"][0]["ordinary_limit"] = 8
        self.ledger.register_child_grant(new_child)
        with self.assertRaises(InsufficientCapacity):
            self.reserve(6, "OLD-TOO-MUCH", "OLD-CHILD")
        self.correct("VIEW-5", self.snapshot("VIEW-5"))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(6, "PARENT-TOO-MUCH", "NEW-CHILD")
        later = child(self.original, "LATER-CHILD")
        later["limits"][0]["ordinary_limit"] = 6
        with self.assertRaises(AuthorityViolation):
            self.ledger.register_child_grant(later)

    def test_concurrent_corrections_from_unselected_view_have_one_winner(self):
        self.view("VIEW-10", 10)
        self.view("VIEW-8", 8)
        snapshots = {name: self.snapshot(name) for name in ("VIEW-10", "VIEW-8")}
        self.assertIsNone(snapshots["VIEW-10"]["selection_snapshot"])
        barrier = threading.Barrier(2)
        def attempt(name):
            barrier.wait()
            try:
                self.correct(name, snapshots[name])
                return "updated"
            except AuthorityViolation:
                return "stale"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["VIEW-10", "VIEW-8"]))
        self.assertCountEqual(results, ["updated", "stale"])
        self.assertIn(self.ledger.get_effective_grant("G-ROOT")["limits"][0]["ordinary_limit"], {Decimal(8), Decimal(10)})

    def test_reservation_and_smaller_correction_are_serialized(self):
        self.view("VIEW-10", 10)
        self.view("VIEW-5", 5)
        self.correct("VIEW-10", self.snapshot("VIEW-10"))
        snapshot = self.snapshot("VIEW-5")
        barrier = threading.Barrier(2)
        def correct():
            barrier.wait()
            self.correct("VIEW-5", snapshot)
            return "corrected"
        def reserve():
            barrier.wait()
            try:
                self.reserve(6, "RACE")
                return "reserved"
            except InsufficientCapacity:
                return "insufficient"
        with ThreadPoolExecutor(max_workers=2) as pool:
            correction_future, reserve_future = pool.submit(correct), pool.submit(reserve)
            self.assertEqual(correction_future.result(), "corrected")
            reservation_result = reserve_future.result()
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        if reservation_result == "reserved":
            self.assertEqual((state["total"]["reserved"], state["total"]["deficit"]), (Decimal(6), Decimal(1)))
        else:
            self.assertEqual((state["total"]["reserved"], state["total"]["available"]), (Decimal(0), Decimal(5)))
        with self.assertRaises(InsufficientCapacity):
            self.reserve(6, "AFTER-RACE")

    def test_changed_or_unavailable_source_never_creates_correction(self):
        self.view("VIEW-10", 10)
        snapshot = self.snapshot("VIEW-10")
        changed = deepcopy(self.auth)
        changed[self.source["artifact_id"]]["owner_constraints"] = ["Different source"]
        with self.assertRaises(AuthorityViolation):
            self.ledger.replace_owner_per_class_limits("G-ROOT", changed.get, "VIEW-10", expected_snapshot=snapshot)
        with self.assertRaises(AuthorityViolation):
            self.ledger.replace_owner_per_class_limits("G-ROOT", lambda ref: None, "VIEW-10", expected_snapshot=snapshot)
        changed_view = deepcopy(self.auth)
        changed_view["VIEW-10"]["authorized_resource_limits"][0]["ordinary_limit"] = 20
        with self.assertRaises(AuthorityViolation):
            self.ledger.replace_owner_per_class_limits("G-ROOT", changed_view.get, "VIEW-10", expected_snapshot=snapshot)
        self.assertEqual(self.ledger.get_effective_grant("G-ROOT")["limits"][0]["ordinary_limit"], Decimal(5))

    def test_older_ledger_can_select_view_during_first_correction(self):
        self.view("VIEW-10", 10)
        with sqlite3.connect(self.ledger.database_path) as conn:
            conn.execute("DROP TABLE grant_shared_views")
        self.correct("VIEW-10", self.snapshot("VIEW-10"))
        self.assertEqual(self.ledger.get_effective_grant("G-ROOT")["limits"][0]["ordinary_limit"], Decimal(10))
        self.assertEqual(self.ledger.get_owner_shared_selection("G-ROOT")["interpretation_ref"], "VIEW-10")

    def test_a_previously_selected_view_can_be_corrected_back_to_the_original_source(self):
        self.view("VIEW-10", 10)
        self.correct("VIEW-10", self.snapshot("VIEW-10"))
        source_ref = self.source["artifact_id"]
        self.correct(source_ref, self.snapshot(source_ref))
        self.assertEqual(self.ledger.get_effective_grant("G-ROOT")["limits"][0]["ordinary_limit"], Decimal(5))
        self.assertIsNone(self.ledger.get_owner_shared_selection("G-ROOT")["interpretation_ref"])

    def test_correction_preserves_ordinary_and_finalization_pool_accounting(self):
        view = self.view("VIEW-FINAL", 5)
        view["authorized_resource_limits"][0]["finalization_reserve"] = 2
        self.correct("VIEW-FINAL", self.snapshot("VIEW-FINAL"))
        self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "FINAL", "OP-FINAL", "KEY-FINAL",
                            now=T0, pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        self.reserve(5, "ORDINARY")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["total"]["committed"], state["total"]["reserved"], state["total"]["available"]),
                         (Decimal(0), Decimal(7), Decimal(0)))

    def test_observation_correction_reports_prior_and_late_allocations_in_both_pools(self):
        from tests.test_resource_admission import decision
        ledger = ResourceLedger(Path(self.tmp.name) / "observation.sqlite")
        ledger.initialize()
        original = grant(ordinary=5, final=2)
        owner = decision(original)
        owner["artifact_id"] = original["authority_source"]["authority_ref"]
        owner["resource_interpretation"] = {"source_text": "Use the actual Owner resource policy.",
            "unresolved_constraints": [], "unresolved_qualifications": []}
        view = deepcopy(owner); view["artifact_id"] = "OBSERVATION"
        view["related_artifacts"].append(owner["artifact_id"])
        view["authorized_resource_limits"][0].update(
            limit_mode="OBSERVATION_ONLY", ordinary_limit=None, finalization_reserve=None)
        auth = {owner["artifact_id"]: owner, view["artifact_id"]: view}
        ledger.register_grant(original)
        def reserve(amount, rid, **kwargs):
            ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", amount, rid,
                           "OP-" + rid, "KEY-" + rid, now=T0, **kwargs)
        reserve(2, "ORDINARY")
        reserve(1, "PAID")
        ledger.commit("PAID", 1, "COMMIT-PAID", now=T1, measurement_source_ref="meter:paid")
        reserve(1, "LATE")
        ledger.release("LATE", "RELEASE-LATE", now=T1)
        reserve(1, "FINAL", pool="FINALIZATION", purpose="FINAL_ACCOUNTING")
        snapshot = ledger.get_owner_resource_snapshot("G-ROOT", auth.get, "OBSERVATION")
        ledger.replace_owner_per_class_limits("G-ROOT", auth.get, "OBSERVATION", expected_snapshot=snapshot)
        state = ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertFalse(state["spend_authority"])
        self.assertEqual((state["ordinary"]["reserved"], state["ordinary"]["committed"],
                          state["finalization"]["reserved"], state["finalization"]["committed"]),
                         (Decimal(2), Decimal(1), Decimal(1), Decimal(0)))
        self.assertEqual((state["ordinary"]["available"], state["finalization"]["available"]),
                         (Decimal(0), Decimal(0)))
        with self.assertRaises(AuthorityViolation):
            reserve(1, "NEW")
        ledger.commit("LATE", 3, "COMMIT-LATE", now=T2, measurement_source_ref="meter:late")
        state = ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["ordinary"]["reserved"], state["ordinary"]["committed"],
                          state["finalization"]["reserved"], state["finalization"]["committed"]),
                         (Decimal(2), Decimal(4), Decimal(1), Decimal(0)))
        self.assertEqual(ledger.get_reservation("LATE")["measurement_source_refs"], ["meter:late"])


class UnreservedUsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ledger.sqlite"
        self.ledger = ResourceLedger(self.path)
        self.ledger.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, amount, observation="U-1", **kwargs):
        return self.ledger.record_unreserved_usage("G-ROOT", "MODEL_INFERENCE", "TOKENS", amount, observation, **kwargs)

    def test_observation_only_actual_retry_and_existing_database(self):
        self.ledger.register_grant(grant(mode="OBSERVATION_ONLY"))
        with sqlite3.connect(self.path) as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM sqlite_master WHERE name='unreserved_usage'").fetchone())
        actual = self.record(3, measurement_source_ref="meter:1", rate_or_quota_revision_ref="rate:1")
        self.assertEqual(self.record(3, measurement_source_ref="meter:1", rate_or_quota_revision_ref="rate:1"), actual)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(state["ordinary"]["committed"], 3)
        self.assertFalse(state["spend_authority"])
        self.assertIsNone(actual["operation_id"])
        self.assertEqual(actual["rate_or_quota_revision_ref"], "rate:1")

    def test_known_unknown_known_preserves_history_without_using_old_amount(self):
        self.ledger.register_grant(grant(mode="HARD_LIMIT", ordinary=10, final=0))
        self.record(3)
        unknown = self.record(None, expected_revision=1, unknown_resource_state="PROVIDER_LATE")
        self.assertIsNone(unknown["quantity"])
        self.assertEqual(unknown["last_known_quantity"], 3)
        self.assertEqual(unknown["unknown_resource_state"], "PROVIDER_LATE")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertIsNone(state["ordinary"]["committed"])
        self.assertEqual(state["ordinary"]["known_committed"], 0)
        self.assertIsNone(state["ordinary"]["available"])
        self.assertEqual(state["exhaustion_state"], "UNKNOWN")
        with self.assertRaises(ResourceLedgerError):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, "R", "OP", "K", now=T0)
        known = self.record(4, expected_revision=2)
        self.assertEqual([x["quantity"] for x in known["history"]], [3, None, 4])
        self.assertEqual(known["history"][1]["last_known_quantity"], 3)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["committed"], 4)

    def test_withdraw_duplicate_retains_history_and_does_not_fabricate_zero(self):
        self.ledger.register_grant(grant(mode="HARD_LIMIT", ordinary=10, final=0))
        self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R", "OP", "reserve", now=T0)
        self.ledger.commit("R", 2, "commit", now=T1)
        self.record(2)
        withdrawn = self.ledger.withdraw_unreserved_usage("U-1", expected_revision=1, reason="duplicate of R")
        self.assertEqual(withdrawn["status"], "WITHDRAWN")
        self.assertEqual(withdrawn["quantity"], 2)
        self.assertEqual(withdrawn["history"][-1]["reason"], "duplicate of R")
        self.assertEqual(self.ledger.withdraw_unreserved_usage("U-1", expected_revision=1, reason="duplicate of R"), withdrawn)
        self.assertEqual(self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")["ordinary"]["committed"], 2)
        self.record(2, expected_revision=2)
        self.ledger.withdraw_unreserved_usage("U-1", expected_revision=3, reason="duplicate of R")
        with self.assertRaises(IdempotencyConflict):
            self.ledger.withdraw_unreserved_usage("U-1", expected_revision=1, reason="duplicate of R")

    def test_same_operation_and_source_can_represent_distinct_real_costs(self):
        self.ledger.register_grant(grant(mode="HARD_LIMIT", ordinary=10, final=0))
        self.record(2, operation_id="OP", measurement_source_ref="meter:1")
        self.record(3, observation="U-2", operation_id="OP", measurement_source_ref="meter:1")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual((state["ordinary"]["committed"], state["ordinary"]["available"]), (5, 5))

    def test_unknown_without_child_limit_is_not_mistaken_for_observation_only(self):
        limits = [{"resource_class": "MODEL_INFERENCE", "dimension": dimension,
                   "limit_mode": "HARD_LIMIT", "ordinary_limit": 5, "finalization_reserve": 0}
                  for dimension in ("TOKENS", "MODEL_CALLS")]
        parent = grant(limits=limits)
        self.ledger.register_grant(parent)
        self.ledger.register_child_grant(child(parent, limits=[limits[1]]))
        self.ledger.record_unreserved_usage("G-CHILD", "MODEL_INFERENCE", "TOKENS", None, "U")
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertIsNone(state["ordinary"]["available"])
        with self.assertRaises(ResourceLedgerError):
            self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 1, "R", "OP", "K", now=T0)

    def test_observation_unknown_preserves_proven_finite_exhaustion(self):
        parent = grant(mode="HARD_LIMIT", ordinary=2, final=0)
        self.ledger.register_grant(parent)
        leaf = child(parent, limits=[{"resource_class": "MODEL_INFERENCE", "dimension": "TOKENS",
            "limit_mode": "OBSERVATION_ONLY", "ordinary_limit": None, "finalization_reserve": None}])
        self.ledger.register_child_grant(leaf)
        self.ledger.record_unreserved_usage("G-CHILD", "MODEL_INFERENCE", "TOKENS", None, "U")
        self.ledger.reserve("G-ROOT", "MODEL_INFERENCE", "TOKENS", 2, "R", "OP", "K", now=T0)
        state = self.ledger.get_resource_state("G-ROOT", "MODEL_INFERENCE", "TOKENS")
        self.assertEqual(state["exhaustion_state"], "EXHAUSTED")
        self.assertEqual(state["ordinary"]["available"], 0)
        self.assertEqual(state["availability_basis"], "KNOWN_RECORDED_ONLY")

    def test_unknown_observation_preserves_admission_semantics_and_schema(self):
        from tests.test_resource_admission import root, run, estimate, item
        from tests.test_resource_governance_contract import schema_accepts
        for mode, expected in (("HARD_LIMIT", "NOT_ADMISSIBLE"), ("OBSERVATION_ONLY", "ADMISSIBLE")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as path:
                ledger = ResourceLedger(Path(path) / "ledger.sqlite")
                ledger.initialize()
                g = root(mode=mode)
                ledger.register_grant(g)
                ledger.record_unreserved_usage("G-LEAF", "MODEL_INFERENCE", "TOKENS", None, "U")
                result = run(ledger, g=g, e=estimate(item(upper=1)))
                self.assertEqual(result["status"], expected, result)
                if mode == "HARD_LIMIT":
                    self.assertEqual(result["unknown_resource_state"], "AVAILABILITY_UNKNOWN")
                else:
                    self.assertEqual(result["evaluations"][0]["reason"], "OBSERVATION_ONLY_NON_BLOCKING")
                serializable = json.loads(json.dumps(result, default=lambda x: float(x) if isinstance(x, Decimal) else x))
                schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/resource-admission.schema.json").read_text())
                self.assertTrue(schema_accepts(serializable, schema))


if __name__ == "__main__":
    unittest.main()

