from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LIMIT_MODES = {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"}
_ROOT_AUTHORITY_TYPES = {
    "OWNER_APPROVED_RESOURCE_AUTHORITY",
    "AUTONOMY_ENVELOPE",
    "OTHER_DURABLE_RESOURCE_AUTHORITY",
}
_PARENT_AUTHORITY_TYPE = "PARENT_RESOURCE_GRANT"
_FINALIZATION_PURPOSES = {
    "RESULT_RECONCILIATION",
    "DURABLE_PARTIAL_OUTPUT",
    "FINAL_ACCOUNTING",
    "CONTROL_HANDOFF",
}
_MODE_NARROWING = {
    "HARD_LIMIT": {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
    "RESERVABLE_LIMIT": {"RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
    "OBSERVATION_ONLY": {"OBSERVATION_ONLY"},
}
_SCOPE_EVIDENCE_KEYS = {"child_scope_ref", "parent_scope_ref", "evidence_ref"}


class ResourceLedgerError(Exception):
    """Base error for bounded resource-ledger operations."""


class InvalidGrant(ResourceLedgerError):
    pass


class AuthorityViolation(ResourceLedgerError):
    pass


class InsufficientCapacity(ResourceLedgerError):
    pass


class IdempotencyConflict(ResourceLedgerError):
    pass


class InvalidReservationTransition(ResourceLedgerError):
    pass


class GrantExpired(ResourceLedgerError):
    pass


def _coeff_exp(value: Decimal) -> tuple[int, int]:
    """Return exact integer coefficient/exponent, independent of Decimal context."""
    if not value.is_finite():
        raise ResourceLedgerError("non-finite Decimal is not valid authority state")
    sign, digits, exponent = value.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    if coefficient == 0:
        return 0, 0
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    return coefficient, exponent


def _decimal_from_coeff_exp(coefficient: int, exponent: int) -> Decimal:
    if coefficient == 0:
        return Decimal("0")
    sign = 1 if coefficient < 0 else 0
    digits = tuple(int(ch) for ch in str(abs(coefficient)))
    return Decimal((sign, digits, exponent))


def _exact_sum(values: list[Decimal] | tuple[Decimal, ...]) -> Decimal:
    pairs = [_coeff_exp(v) for v in values]
    if not pairs:
        return Decimal("0")
    common_exp = min(exp for _, exp in pairs)
    total = sum(coeff * (10 ** (exp - common_exp)) for coeff, exp in pairs)
    return _decimal_from_coeff_exp(total, common_exp)


def _exact_subtract(first: Decimal, *rest: Decimal) -> Decimal:
    pairs = [_coeff_exp(first)] + [(-c, e) for c, e in map(_coeff_exp, rest)]
    common_exp = min(exp for _, exp in pairs)
    total = sum(coeff * (10 ** (exp - common_exp)) for coeff, exp in pairs)
    return _decimal_from_coeff_exp(total, common_exp)


def _exact_compare(left: Decimal, right: Decimal) -> int:
    lc, le = _coeff_exp(left)
    rc, rexp = _coeff_exp(right)
    common_exp = min(le, rexp)
    li = lc * (10 ** (le - common_exp))
    ri = rc * (10 ** (rexp - common_exp))
    return (li > ri) - (li < ri)


def canonical_shared_limits(value: object) -> list[dict[str, Any]]:
    """Normalize explicitly authorized shared totals without inventing prices."""
    if not isinstance(value, list):
        raise ResourceLedgerError("shared_limits must be an array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        required = {"limit_id", "dimension", "resource_classes", "total_limit"}
        if not isinstance(item, dict) or not required <= set(item) or set(item) - required - {"finalization_reserve"}:
            raise ResourceLedgerError("shared limit fields are malformed")
        identity, dimension, classes = item["limit_id"], item["dimension"], item["resource_classes"]
        if not isinstance(identity, str) or not identity.strip() or identity in seen:
            raise ResourceLedgerError("shared limit identity is empty or duplicated")
        seen.add(identity)
        if not isinstance(dimension, str) or not _IDENTIFIER.fullmatch(dimension):
            raise ResourceLedgerError("shared limit dimension is invalid")
        if (not isinstance(classes, list) or not classes or
                not all(isinstance(c, str) and _IDENTIFIER.fullmatch(c) for c in classes) or
                len(classes) != len(set(classes))):
            raise ResourceLedgerError("shared limit resource classes are invalid")
        quantities = []
        for key in ("total_limit", "finalization_reserve"):
            raw = item.get(key, 0)
            if isinstance(raw, bool) or not isinstance(raw, (int, float, Decimal)):
                raise ResourceLedgerError(f"shared limit {key} must be a JSON number")
            try:
                amount = Decimal(str(raw))
            except (InvalidOperation, ValueError):
                raise ResourceLedgerError(f"shared limit {key} is invalid") from None
            if not amount.is_finite() or _exact_compare(amount, Decimal(0)) < 0:
                raise ResourceLedgerError(f"shared limit {key} must be non-negative and finite")
            quantities.append(amount)
        if _exact_compare(quantities[1], quantities[0]) > 0:
            raise ResourceLedgerError("shared finalization reserve exceeds total")
        result.append({"limit_id": identity, "dimension": dimension,
                       "resource_classes": sorted(classes), "total_limit": quantities[0],
                       "finalization_reserve": quantities[1]})
    return sorted(result, key=lambda item: item["limit_id"])


class ResourceLedger:
    """Transactional shared-file implementation of frozen RESOURCE_GRANT authority."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 5000) -> None:
        raw = str(database_path)
        lowered = raw.lower()
        if raw == ":memory:" or ":memory:" in lowered or (
            lowered.startswith("file:") and "mode=memory" in lowered
        ):
            raise ResourceLedgerError(
                "authoritative resource ledger requires one shared on-disk SQLite file"
            )
        if not raw.strip():
            raise ResourceLedgerError("database path must be non-empty")
        if isinstance(busy_timeout_ms, bool) or not isinstance(busy_timeout_ms, int) or busy_timeout_ms <= 0:
            raise ResourceLedgerError("busy_timeout_ms must be a positive integer")
        self.database_path = raw
        self.busy_timeout_ms = busy_timeout_ms
        self._uri = lowered.startswith("file:")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
            uri=self._uri,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        return conn

    def initialize(self) -> None:
        if not self._uri:
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS grants (
                    grant_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    grant_json TEXT NOT NULL,
                    parent_grant_id TEXT NULL REFERENCES grants(grant_id),
                    authority_type TEXT NOT NULL,
                    scope_ref TEXT NOT NULL,
                    candidate_ref TEXT NULL,
                    route_ref TEXT NULL,
                    attempt_limit INTEGER NULL,
                    valid_until TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS grant_resource_classes (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    resource_class TEXT NOT NULL,
                    PRIMARY KEY (grant_id, resource_class)
                );

                CREATE TABLE IF NOT EXISTS grant_limits (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    limit_mode TEXT NOT NULL,
                    ordinary_limit TEXT NULL,
                    finalization_reserve TEXT NULL,
                    PRIMARY KEY (grant_id, resource_class, dimension)
                );

                CREATE TABLE IF NOT EXISTS grant_shared_limits (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    limit_id TEXT NOT NULL,
                    authority_ref TEXT NOT NULL,
                    interpretation_ref TEXT NULL,
                    dimension TEXT NOT NULL,
                    resource_classes_json TEXT NOT NULL,
                    total_limit TEXT NOT NULL,
                    finalization_reserve TEXT NOT NULL,
                    PRIMARY KEY (grant_id, limit_id)
                );

                CREATE TABLE IF NOT EXISTS grant_shared_views (
                    grant_id TEXT PRIMARY KEY REFERENCES grants(grant_id),
                    authority_ref TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL,
                    interpretation_ref TEXT NULL,
                    view_fingerprint TEXT NOT NULL,
                    snapshot TEXT NOT NULL,
                    corrected INTEGER NOT NULL,
                    lineage_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS grant_finalization_purposes (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    purpose TEXT NOT NULL,
                    PRIMARY KEY (grant_id, purpose)
                );

                CREATE TABLE IF NOT EXISTS grant_scope_relation_evidence (
                    child_grant_id TEXT PRIMARY KEY REFERENCES grants(grant_id) ON DELETE CASCADE,
                    child_scope_ref TEXT NOT NULL,
                    parent_scope_ref TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    purpose TEXT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NULL,
                    status TEXT NOT NULL,
                    committed_quantity TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS reservation_allocations (
                    reservation_id TEXT NOT NULL REFERENCES reservations(reservation_id) ON DELETE CASCADE,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    reserved TEXT NOT NULL,
                    committed TEXT NOT NULL,
                    PRIMARY KEY (reservation_id, grant_id)
                );

                CREATE TABLE IF NOT EXISTS attempt_claims (
                    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    operation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (grant_id, operation_id)
                );

                CREATE TABLE IF NOT EXISTS attempt_allocations (
                    claim_id INTEGER NOT NULL REFERENCES attempt_claims(claim_id) ON DELETE CASCADE,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    PRIMARY KEY (claim_id, grant_id)
                );

                CREATE TABLE IF NOT EXISTS idempotency_operations (
                    idempotency_key TEXT PRIMARY KEY,
                    operation_kind TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                """
            )
        finally:
            conn.close()

    @staticmethod
    def _require_text(value: Any, field: str, *, nullable: bool = False) -> str | None:
        if value is None and nullable:
            return None
        if not isinstance(value, str) or not value:
            raise InvalidGrant(f"{field} must be a non-empty string" + (" or null" if nullable else ""))
        return value

    @staticmethod
    def _require_exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise InvalidGrant(f"{field} must be an object")
        keys = set(value)
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            raise InvalidGrant(f"{field} fields invalid: missing={missing}, extra={extra}")
        return value

    @staticmethod
    def _decimal(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
            raise ResourceLedgerError(f"{field} must be a finite non-negative decimal quantity")
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ResourceLedgerError(f"{field} must be a finite non-negative decimal quantity") from None
        if not result.is_finite() or _exact_compare(result, Decimal("0")) < 0 or (
            not allow_zero and _exact_compare(result, Decimal("0")) == 0
        ):
            comparator = "positive" if not allow_zero else "non-negative"
            raise ResourceLedgerError(f"{field} must be finite and {comparator}")
        return result

    @classmethod
    def _grant_decimal(cls, value: Any, field: str) -> Decimal:
        if isinstance(value, str):
            raise InvalidGrant(f"{field} must be a JSON numeric value, not a string")
        try:
            return cls._decimal(value, field)
        except ResourceLedgerError as exc:
            raise InvalidGrant(str(exc)) from None

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        coefficient, exponent = _coeff_exp(value)
        if coefficient == 0:
            return "0"
        negative = coefficient < 0
        digits = str(abs(coefficient))
        if exponent >= 0:
            text = digits + ("0" * exponent)
        else:
            split = len(digits) + exponent
            if split > 0:
                text = digits[:split] + "." + digits[split:]
            else:
                text = "0." + ("0" * (-split)) + digits
        return ("-" if negative else "") + text

    @staticmethod
    def _parse_datetime(value: Any, field: str, *, nullable: bool = False) -> datetime | None:
        if value is None and nullable:
            return None
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ResourceLedgerError(f"{field} must be a valid timezone-aware datetime") from None
        else:
            raise ResourceLedgerError(f"{field} must be a valid timezone-aware datetime")
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ResourceLedgerError(f"{field} must be timezone-aware")
        return dt.astimezone(timezone.utc)

    @classmethod
    def _grant_datetime(cls, value: Any, field: str) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidGrant(f"{field} must be a date-time string or null")
        try:
            return cls._parse_datetime(value, field)
        except ResourceLedgerError as exc:
            raise InvalidGrant(str(exc)) from None

    @staticmethod
    def _datetime_text(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

    @classmethod
    def _now(cls, value: datetime | str | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        parsed = cls._parse_datetime(value, "now")
        if parsed is None:
            raise ResourceLedgerError("now must be a timezone-aware datetime")
        return parsed

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _fingerprint(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @classmethod
    def _record_fingerprint(cls, value: Any) -> str:
        """Fingerprint an actual resolved record, preserving JSON value types."""
        def typed(item: Any) -> Any:
            if isinstance(item, dict):
                return ["object", [[key, typed(item[key])] for key in sorted(item)]]
            if isinstance(item, list):
                return ["array", [typed(entry) for entry in item]]
            if item is None:
                return ["null"]
            if isinstance(item, bool):
                return ["bool", item]
            if isinstance(item, (int, float, Decimal)):
                number = Decimal(str(item))
                if not number.is_finite():
                    raise AuthorityViolation("Owner record contains a non-finite number")
                coefficient, exponent = _coeff_exp(number)
                return ["number", str(coefficient), exponent]
            if isinstance(item, str):
                return ["string", item]
            raise AuthorityViolation("Owner record is not a resolved JSON object")
        return cls._fingerprint(typed(value))

    @classmethod
    def _validate_grant(cls, grant: Any) -> tuple[dict[str, Any], str]:
        required = {
            "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
            "status", "provenance", "related_artifacts", "issued_by", "authority_source",
            "parent_grant_ref", "scope", "limits", "attempt_limit", "valid_until", "finalization_policy",
        }
        obj = cls._require_exact_keys(grant, required, "RESOURCE_GRANT")
        if obj["artifact_type"] != "RESOURCE_GRANT":
            raise InvalidGrant("artifact_type must be RESOURCE_GRANT")
        grant_id = cls._require_text(obj["artifact_id"], "artifact_id")
        if obj["status"] != "AUTHORIZED":
            raise InvalidGrant("status must be AUTHORIZED")
        if obj["issued_by"] != "control-director" or obj["produced_by_role"] != "control-director":
            raise InvalidGrant("RESOURCE_GRANT must be issued and produced by control-director")
        for nullable_name in ("assignment_id", "input_state_ref", "parent_grant_ref"):
            cls._require_text(obj[nullable_name], nullable_name, nullable=True)

        provenance = obj["provenance"]
        if not isinstance(provenance, list) or not provenance:
            raise InvalidGrant("provenance must be a non-empty array")
        if any(not isinstance(x, str) or not x for x in provenance) or len(set(provenance)) != len(provenance):
            raise InvalidGrant("provenance must contain unique non-empty strings")
        related = obj["related_artifacts"]
        if not isinstance(related, list):
            raise InvalidGrant("related_artifacts must be an array")
        if any(not isinstance(x, str) or not x for x in related) or len(set(related)) != len(related):
            raise InvalidGrant("related_artifacts must contain unique non-empty strings")

        authority = cls._require_exact_keys(
            obj["authority_source"], {"authority_type", "authority_ref"}, "authority_source"
        )
        authority_type = authority["authority_type"]
        if authority_type not in _ROOT_AUTHORITY_TYPES | {_PARENT_AUTHORITY_TYPE}:
            raise InvalidGrant("authority_source.authority_type is not recognized")
        cls._require_text(authority["authority_ref"], "authority_source.authority_ref")
        parent_ref = obj["parent_grant_ref"]
        if authority_type == _PARENT_AUTHORITY_TYPE:
            if not isinstance(parent_ref, str) or not parent_ref:
                raise InvalidGrant("PARENT_RESOURCE_GRANT requires parent_grant_ref")
            if authority["authority_ref"] != parent_ref:
                raise InvalidGrant("parent authority_ref must identify parent_grant_ref")
        elif parent_ref is not None:
            raise InvalidGrant("non-parent authority_source requires parent_grant_ref = null")

        scope = cls._require_exact_keys(
            obj["scope"], {"scope_ref", "candidate_ref", "route_ref", "resource_classes"}, "scope"
        )
        cls._require_text(scope["scope_ref"], "scope.scope_ref")
        cls._require_text(scope["candidate_ref"], "scope.candidate_ref", nullable=True)
        cls._require_text(scope["route_ref"], "scope.route_ref", nullable=True)
        classes = scope["resource_classes"]
        if not isinstance(classes, list) or not classes:
            raise InvalidGrant("scope.resource_classes must be non-empty")
        if any(not isinstance(x, str) or _IDENTIFIER.fullmatch(x) is None for x in classes):
            raise InvalidGrant("resource_classes must use canonical identifiers")
        if len(set(classes)) != len(classes):
            raise InvalidGrant("resource_classes must be unique")

        limits = obj["limits"]
        if not isinstance(limits, list) or not limits:
            raise InvalidGrant("limits must be non-empty")
        normalized_limits: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        for index, raw in enumerate(limits):
            limit = cls._require_exact_keys(
                raw,
                {"resource_class", "dimension", "limit_mode", "ordinary_limit", "finalization_reserve"},
                f"limits[{index}]",
            )
            resource_class = limit["resource_class"]
            dimension = limit["dimension"]
            if not isinstance(resource_class, str) or _IDENTIFIER.fullmatch(resource_class) is None:
                raise InvalidGrant("limit resource_class must be a canonical identifier")
            if resource_class not in classes:
                raise InvalidGrant("limit resource_class must belong to grant scope")
            if not isinstance(dimension, str) or _IDENTIFIER.fullmatch(dimension) is None:
                raise InvalidGrant("limit dimension must be a canonical identifier")
            key = (resource_class, dimension)
            if key in seen_keys:
                raise InvalidGrant("duplicate (resource_class, dimension) limit")
            seen_keys.add(key)
            mode = limit["limit_mode"]
            if mode not in _LIMIT_MODES:
                raise InvalidGrant("limit_mode is not recognized")
            if mode == "OBSERVATION_ONLY":
                if limit["ordinary_limit"] is not None or limit["finalization_reserve"] is not None:
                    raise InvalidGrant("OBSERVATION_ONLY requires null capacities")
                ordinary_text = final_text = None
            else:
                ordinary = cls._grant_decimal(limit["ordinary_limit"], f"limits[{index}].ordinary_limit")
                final = cls._grant_decimal(limit["finalization_reserve"], f"limits[{index}].finalization_reserve")
                ordinary_text = cls._decimal_text(ordinary)
                final_text = cls._decimal_text(final)
            normalized_limits.append({
                "resource_class": resource_class,
                "dimension": dimension,
                "limit_mode": mode,
                "ordinary_limit": ordinary_text,
                "finalization_reserve": final_text,
            })

        attempt_limit = obj["attempt_limit"]
        if attempt_limit is not None and (
            isinstance(attempt_limit, bool) or not isinstance(attempt_limit, int) or attempt_limit < 1
        ):
            raise InvalidGrant("attempt_limit must be null or an integer >= 1")
        valid_until = cls._grant_datetime(obj["valid_until"], "valid_until")

        policy = cls._require_exact_keys(
            obj["finalization_policy"], {"protected", "allowed_purposes"}, "finalization_policy"
        )
        if policy["protected"] is not True:
            raise InvalidGrant("finalization_policy.protected must be true")
        purposes = policy["allowed_purposes"]
        if not isinstance(purposes, list) or not purposes:
            raise InvalidGrant("finalization_policy.allowed_purposes must be non-empty")
        if any(x not in _FINALIZATION_PURPOSES for x in purposes) or len(set(purposes)) != len(purposes):
            raise InvalidGrant("finalization_policy.allowed_purposes is invalid")

        normalized = {
            "artifact_type": "RESOURCE_GRANT",
            "artifact_id": grant_id,
            "produced_by_role": "control-director",
            "assignment_id": obj["assignment_id"],
            "input_state_ref": obj["input_state_ref"],
            "status": "AUTHORIZED",
            "provenance": sorted(provenance),
            "related_artifacts": sorted(related),
            "issued_by": "control-director",
            "authority_source": {
                "authority_type": authority_type,
                "authority_ref": authority["authority_ref"],
            },
            "parent_grant_ref": parent_ref,
            "scope": {
                "scope_ref": scope["scope_ref"],
                "candidate_ref": scope["candidate_ref"],
                "route_ref": scope["route_ref"],
                "resource_classes": sorted(classes),
            },
            "limits": sorted(normalized_limits, key=lambda x: (x["resource_class"], x["dimension"])),
            "attempt_limit": attempt_limit,
            "valid_until": cls._datetime_text(valid_until) if valid_until else None,
            "finalization_policy": {
                "protected": True,
                "allowed_purposes": sorted(purposes),
            },
        }
        return normalized, cls._fingerprint(normalized)

    @staticmethod
    def _begin_write(conn: sqlite3.Connection) -> None:
        conn.execute("BEGIN IMMEDIATE")

    @staticmethod
    def _row_grant(conn: sqlite3.Connection, grant_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM grants WHERE grant_id = ?", (grant_id,)).fetchone()
        if row is None:
            raise AuthorityViolation(f"grant not registered: {grant_id}")
        return row

    @staticmethod
    def _limit_row(conn: sqlite3.Connection, grant_id: str, resource_class: str, dimension: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM grant_limits WHERE grant_id = ? AND resource_class = ? AND dimension = ?",
            (grant_id, resource_class, dimension),
        ).fetchone()
        if row is None:
            raise AuthorityViolation(f"grant {grant_id} has no authority for {resource_class}/{dimension}")
        return row

    @classmethod
    def _ancestry(cls, conn: sqlite3.Connection, grant_id: str) -> list[sqlite3.Row]:
        chain: list[sqlite3.Row] = []
        seen: set[str] = set()
        current: str | None = grant_id
        while current is not None:
            if current in seen:
                raise AuthorityViolation("grant ancestry contains a cycle")
            seen.add(current)
            row = cls._row_grant(conn, current)
            chain.append(row)
            parent = row["parent_grant_id"]
            current = str(parent) if parent is not None else None
        return chain

    @classmethod
    def _grant_expired(cls, grant_row: sqlite3.Row, now: datetime) -> bool:
        raw = grant_row["valid_until"]
        if raw is None:
            return False
        parsed = cls._parse_datetime(str(raw), "valid_until")
        if parsed is None:
            raise AuthorityViolation("stored grant validity is malformed")
        return now >= parsed

    @staticmethod
    def _ensure_unreserved_usage(conn: sqlite3.Connection) -> None:
        # Old ledgers need no manual migration: create the table in the first
        # actual observation's transaction. Reads alone do not change the DB.
        conn.execute("""CREATE TABLE IF NOT EXISTS unreserved_usage (
            observation_id TEXT PRIMARY KEY,
            grant_id TEXT NOT NULL REFERENCES grants(grant_id),
            resource_class TEXT NOT NULL, dimension TEXT NOT NULL,
            operation_id TEXT NULL, pool TEXT NOT NULL, status TEXT NOT NULL,
            quantity TEXT NULL, last_known_quantity TEXT NULL,
            metering_quality TEXT NOT NULL, unknown_resource_state TEXT NOT NULL,
            measurement_source_ref TEXT NULL, rate_or_quota_revision_ref TEXT NULL,
            revision INTEGER NOT NULL, history_json TEXT NOT NULL
        )""")

    @staticmethod
    def _unreserved_rows(conn: sqlite3.Connection, grant_id: str, dimension: str) -> list[sqlite3.Row]:
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'unreserved_usage'").fetchone() is None:
            return []
        return conn.execute("""
            WITH RECURSIVE descendants(grant_id) AS (
                SELECT ? UNION SELECT grants.grant_id FROM grants
                JOIN descendants ON grants.parent_grant_id = descendants.grant_id
            )
            SELECT observation.*, source_limit.limit_mode AS source_limit_mode
            FROM unreserved_usage AS observation
            JOIN descendants ON observation.grant_id = descendants.grant_id
            LEFT JOIN grant_limits AS source_limit ON source_limit.grant_id = observation.grant_id
              AND source_limit.resource_class = observation.resource_class
              AND source_limit.dimension = observation.dimension
            WHERE observation.dimension = ? AND observation.status = 'ACTIVE'
        """, (grant_id, dimension)).fetchall()

    @staticmethod
    def _unknown_blocks(row: sqlite3.Row) -> bool:
        # Missing optional observation-only telemetry is non-blocking; an
        # unknown actual against a finite limit cannot prove availability.
        return row["quantity"] is None and row["source_limit_mode"] != "OBSERVATION_ONLY"

    @classmethod
    def _allocation_totals(
        cls,
        conn: sqlite3.Connection,
        grant_id: str,
        resource_class: str,
        dimension: str,
        pool: str,
    ) -> tuple[Decimal, Decimal]:
        rows = conn.execute(
            """
            SELECT reserved, committed
            FROM reservation_allocations
            WHERE grant_id = ? AND resource_class = ? AND dimension = ? AND pool = ?
            """,
            (grant_id, resource_class, dimension, pool),
        ).fetchall()
        reserved = _exact_sum([Decimal(row["reserved"]) for row in rows])
        observed = cls._unreserved_rows(conn, grant_id, dimension)
        committed = _exact_sum([Decimal(row["committed"]) for row in rows]
                               + [Decimal(row["quantity"]) for row in observed
                                  if row["resource_class"] == resource_class and row["pool"] == pool
                                  and row["quantity"] is not None])
        return reserved, committed

    @classmethod
    def _idempotency_lookup(
        cls, conn: sqlite3.Connection, key: str, operation_kind: str, fingerprint: str
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT operation_kind, fingerprint, result_json FROM idempotency_operations WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if row["operation_kind"] != operation_kind or row["fingerprint"] != fingerprint:
            raise IdempotencyConflict("idempotency key is already bound to a conflicting operation")
        return cls._decode_result(row["result_json"])

    @classmethod
    def _record_idempotency(
        cls,
        conn: sqlite3.Connection,
        key: str,
        operation_kind: str,
        fingerprint: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        result_json = cls._encode_result(result)
        conn.execute(
            "INSERT INTO idempotency_operations(idempotency_key, operation_kind, fingerprint, result_json) VALUES (?, ?, ?, ?)",
            (key, operation_kind, fingerprint, result_json),
        )
        return cls._decode_result(result_json)

    @classmethod
    def _encode_result(cls, result: dict[str, Any]) -> str:
        def convert(value: Any) -> Any:
            if isinstance(value, Decimal):
                return {"__decimal__": cls._decimal_text(value)}
            if isinstance(value, dict):
                return {key: convert(nested) for key, nested in value.items()}
            if isinstance(value, list):
                return [convert(nested) for nested in value]
            return value

        return cls._canonical_json(convert(result))

    @classmethod
    def _decode_result(cls, raw: str) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, dict) and set(value) == {"__decimal__"}:
                return Decimal(value["__decimal__"])
            if isinstance(value, dict):
                return {key: convert(nested) for key, nested in value.items()}
            if isinstance(value, list):
                return [convert(nested) for nested in value]
            return value

        decoded = convert(json.loads(raw))
        if not isinstance(decoded, dict):
            raise ResourceLedgerError("stored idempotency result is malformed")
        return decoded

    @staticmethod
    def _require_id(value: Any, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise ResourceLedgerError(f"{field} must be a non-empty string")
        return value

    @classmethod
    def _validate_scope_evidence(
        cls,
        evidence: Any,
        child_scope_ref: str,
        parent_scope_ref: str,
    ) -> dict[str, str]:
        if not isinstance(evidence, dict) or set(evidence) != _SCOPE_EVIDENCE_KEYS:
            raise AuthorityViolation(
                "different-scope child requires scope relation evidence with child_scope_ref, parent_scope_ref, evidence_ref"
            )
        child = evidence.get("child_scope_ref")
        parent = evidence.get("parent_scope_ref")
        evidence_ref = evidence.get("evidence_ref")
        if not all(isinstance(x, str) and x for x in (child, parent, evidence_ref)):
            raise AuthorityViolation("scope relation evidence fields must be non-empty strings")
        if child != child_scope_ref or parent != parent_scope_ref:
            raise AuthorityViolation("scope relation evidence does not match child/parent scope refs")
        return {
            "child_scope_ref": child,
            "parent_scope_ref": parent,
            "evidence_ref": evidence_ref,
        }

    def register_grant(self, grant: dict[str, Any]) -> dict[str, Any]:
        normalized, fingerprint = self._validate_grant(grant)
        if normalized["authority_source"]["authority_type"] not in _ROOT_AUTHORITY_TYPES:
            raise InvalidGrant("register_grant accepts root durable authority only")
        conn = self._connect()
        try:
            self._begin_write(conn)
            existing = conn.execute(
                "SELECT fingerprint FROM grants WHERE grant_id = ?", (normalized["artifact_id"],)
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise AuthorityViolation("grant id is already registered with different authority")
                conn.commit()
                return self.get_grant(normalized["artifact_id"])
            self._insert_grant(conn, normalized, fingerprint)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return self.get_grant(normalized["artifact_id"])

    def register_child_grant(
        self,
        grant: dict[str, Any],
        scope_relation_evidence: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized, fingerprint = self._validate_grant(grant)
        if normalized["authority_source"]["authority_type"] != _PARENT_AUTHORITY_TYPE:
            raise InvalidGrant("register_child_grant requires PARENT_RESOURCE_GRANT authority")
        parent_id = normalized["parent_grant_ref"]
        if not isinstance(parent_id, str) or not parent_id:
            raise InvalidGrant("child grant requires parent_grant_ref")
        conn = self._connect()
        try:
            self._begin_write(conn)
            parent_row = self._row_grant(conn, parent_id)
            parent = self._effective_grant_on_conn(conn, parent_row)
            child_scope = normalized["scope"]["scope_ref"]
            parent_scope = parent["scope"]["scope_ref"]
            evidence: dict[str, str] | None = None
            if child_scope != parent_scope:
                evidence = self._validate_scope_evidence(scope_relation_evidence, child_scope, parent_scope)
            elif scope_relation_evidence is not None:
                raise AuthorityViolation("equal-scope child does not require external scope relation evidence")

            existing = conn.execute(
                "SELECT fingerprint FROM grants WHERE grant_id = ?", (normalized["artifact_id"],)
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise AuthorityViolation("grant id is already registered with different authority")
                persisted = conn.execute(
                    "SELECT child_scope_ref, parent_scope_ref, evidence_ref FROM grant_scope_relation_evidence WHERE child_grant_id = ?",
                    (normalized["artifact_id"],),
                ).fetchone()
                if evidence is None:
                    if persisted is not None:
                        raise AuthorityViolation("stored equal-scope grant unexpectedly has scope relation evidence")
                else:
                    if persisted is None or dict(persisted) != evidence:
                        raise AuthorityViolation("grant is already registered with conflicting scope relation evidence")
                conn.commit()
                return self.get_grant(normalized["artifact_id"])

            self._enforce_child_narrowing(parent, normalized, evidence is not None)
            self._ancestry(conn, parent_id)
            self._insert_grant(conn, normalized, fingerprint)
            if evidence is not None:
                conn.execute(
                    """
                    INSERT INTO grant_scope_relation_evidence(
                        child_grant_id, child_scope_ref, parent_scope_ref, evidence_ref
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        normalized["artifact_id"],
                        evidence["child_scope_ref"],
                        evidence["parent_scope_ref"],
                        evidence["evidence_ref"],
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return self.get_grant(normalized["artifact_id"])

    @classmethod
    def _enforce_child_narrowing(
        cls,
        parent: dict[str, Any],
        child: dict[str, Any],
        different_scope_proven: bool,
    ) -> None:
        ps = parent["scope"]
        cs = child["scope"]
        if cs["scope_ref"] != ps["scope_ref"] and not different_scope_proven:
            raise AuthorityViolation("child scope is not proven equal to or narrower than parent scope")
        if not set(cs["resource_classes"]).issubset(ps["resource_classes"]):
            raise AuthorityViolation("child resource classes expand parent authority")
        for binding in ("candidate_ref", "route_ref"):
            parent_binding = ps[binding]
            child_binding = cs[binding]
            if parent_binding is not None and child_binding != parent_binding:
                raise AuthorityViolation(f"child {binding} expands or changes parent binding")

        parent_attempt = parent["attempt_limit"]
        child_attempt = child["attempt_limit"]
        if parent_attempt is not None and (child_attempt is None or child_attempt > parent_attempt):
            raise AuthorityViolation("child attempt authority expands parent authority")

        parent_until = cls._grant_datetime(parent["valid_until"], "parent.valid_until")
        child_until = cls._grant_datetime(child["valid_until"], "child.valid_until")
        if parent_until is not None and (child_until is None or child_until > parent_until):
            raise AuthorityViolation("child validity expands parent validity")

        parent_purposes = set(parent["finalization_policy"]["allowed_purposes"])
        child_purposes = set(child["finalization_policy"]["allowed_purposes"])
        if not child_purposes.issubset(parent_purposes):
            raise AuthorityViolation("child finalization purposes expand parent authority")

        parent_limits = {(x["resource_class"], x["dimension"]): x for x in parent["limits"]}
        for child_limit in child["limits"]:
            key = (child_limit["resource_class"], child_limit["dimension"])
            parent_limit = parent_limits.get(key)
            if parent_limit is None:
                raise AuthorityViolation("child resource key is absent from parent authority")
            if child_limit["limit_mode"] not in _MODE_NARROWING[parent_limit["limit_mode"]]:
                raise AuthorityViolation("child limit mode relaxes parent enforcement")
            if child_limit["limit_mode"] == "OBSERVATION_ONLY":
                continue
            if parent_limit["limit_mode"] == "OBSERVATION_ONLY":
                raise AuthorityViolation("observation-only parent cannot create spend authority")
            child_ordinary = Decimal(child_limit["ordinary_limit"])
            parent_ordinary = Decimal(parent_limit["ordinary_limit"])
            child_final = Decimal(child_limit["finalization_reserve"])
            parent_final = Decimal(parent_limit["finalization_reserve"])
            if _exact_compare(child_ordinary, parent_ordinary) > 0:
                raise AuthorityViolation("child ordinary capacity expands parent authority")
            if _exact_compare(child_final, parent_final) > 0:
                raise AuthorityViolation("child finalization reserve expands parent authority")

    @staticmethod
    def _insert_grant(conn: sqlite3.Connection, grant: dict[str, Any], fingerprint: str) -> None:
        scope = grant["scope"]
        conn.execute(
            """
            INSERT INTO grants(
                grant_id, fingerprint, grant_json, parent_grant_id, authority_type, scope_ref,
                candidate_ref, route_ref, attempt_limit, valid_until
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grant["artifact_id"], fingerprint, ResourceLedger._canonical_json(grant), grant["parent_grant_ref"],
                grant["authority_source"]["authority_type"], scope["scope_ref"], scope["candidate_ref"],
                scope["route_ref"], grant["attempt_limit"], grant["valid_until"],
            ),
        )
        conn.executemany(
            "INSERT INTO grant_resource_classes(grant_id, resource_class) VALUES (?, ?)",
            [(grant["artifact_id"], item) for item in scope["resource_classes"]],
        )
        conn.executemany(
            """
            INSERT INTO grant_limits(
                grant_id, resource_class, dimension, limit_mode, ordinary_limit, finalization_reserve
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    grant["artifact_id"], item["resource_class"], item["dimension"], item["limit_mode"],
                    item["ordinary_limit"], item["finalization_reserve"],
                )
                for item in grant["limits"]
            ],
        )
        conn.executemany(
            "INSERT INTO grant_finalization_purposes(grant_id, purpose) VALUES (?, ?)",
            [(grant["artifact_id"], purpose) for purpose in grant["finalization_policy"]["allowed_purposes"]],
        )

    def get_grant(self, grant_id: str) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            row = self._row_grant(conn, grant_id)
            grant = json.loads(row["grant_json"])
        finally:
            conn.close()
        for item in grant["limits"]:
            if item["ordinary_limit"] is not None:
                item["ordinary_limit"] = Decimal(item["ordinary_limit"])
                item["finalization_reserve"] = Decimal(item["finalization_reserve"])
        return grant

    @classmethod
    def _class_limits_on_conn(cls, conn: sqlite3.Connection, grant_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT resource_class, dimension, limit_mode, ordinary_limit, finalization_reserve "
            "FROM grant_limits WHERE grant_id = ? ORDER BY resource_class, dimension",
            (grant_id,),
        ).fetchall()
        return [dict(item) for item in rows]

    @classmethod
    def _effective_grant_on_conn(cls, conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
        """Project the ledger's active per-class limits without changing the stored grant."""
        grant = json.loads(row["grant_json"])
        limits = cls._class_limits_on_conn(conn, row["grant_id"])
        grant["limits"] = [
            {"resource_class": item["resource_class"], "dimension": item["dimension"],
             "limit_mode": item["limit_mode"],
             "ordinary_limit": Decimal(item["ordinary_limit"]) if item["ordinary_limit"] is not None else None,
             "finalization_reserve": Decimal(item["finalization_reserve"]) if item["finalization_reserve"] is not None else None}
            for item in limits
        ]
        return grant

    def get_effective_grant(self, grant_id: str) -> dict[str, Any]:
        """Read current limits for enforcement; get_grant retains the original artifact."""
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            return self._effective_grant_on_conn(conn, self._row_grant(conn, grant_id))
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    def get_scope_relation_evidence(self, grant_id: str) -> dict[str, str] | None:
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            self._row_grant(conn, grant_id)
            row = conn.execute(
                "SELECT child_scope_ref, parent_scope_ref, evidence_ref FROM grant_scope_relation_evidence WHERE child_grant_id = ?",
                (grant_id,),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def get_resource_state(self, grant_id: str, resource_class: str, dimension: str) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        self._require_id(resource_class, "resource_class")
        self._require_id(dimension, "dimension")
        conn = self._connect()
        try:
            # The grant, both pool totals, and derived availability must all
            # describe one SQLite snapshot, even while writers commit changes.
            conn.execute("BEGIN")
            grant = self._row_grant(conn, grant_id)
            limit = self._limit_row(conn, grant_id, resource_class, dimension)
            now = datetime.now(timezone.utc)
            zero = Decimal("0")
            ordinary_reserved, ordinary_committed = self._allocation_totals(
                conn, grant_id, resource_class, dimension, "ORDINARY"
            )
            final_reserved, final_committed = self._allocation_totals(
                conn, grant_id, resource_class, dimension, "FINALIZATION"
            )
            unknown_rows = [row for row in self._unreserved_rows(conn, grant_id, dimension)
                            if row["resource_class"] == resource_class and row["quantity"] is None]
            blocking_unknown = any(self._unknown_blocks(row) for row in unknown_rows)
            def annotate_unknown(result: dict[str, Any], *, finite: bool) -> dict[str, Any]:
                if not unknown_rows:
                    return result
                result["unknown_observations"] = len(unknown_rows)
                result["unknown_resource_state"] = "ACTUAL_UNKNOWN"
                result["availability_basis"] = ("UNKNOWN_FINITE_ACTUAL" if blocking_unknown
                                                else "KNOWN_RECORDED_ONLY")
                for name, pool in (("ordinary", "ORDINARY"), ("finalization", "FINALIZATION")):
                    if any(row["pool"] == pool for row in unknown_rows):
                        result[name]["known_committed"] = result[name]["committed"]
                        result[name]["committed"] = None
                        if finite:
                            result[name]["known_deficit"] = result[name]["deficit"]
                            result[name]["deficit"] = None
                    if finite and blocking_unknown:
                        result[name]["available"] = None
                if finite:
                    result["total"]["known_committed"] = result["total"]["committed"]
                    result["total"]["committed"] = None
                    result["total"]["known_deficit"] = result["total"]["deficit"]
                    result["total"]["deficit"] = None
                    if result["exhaustion_state"] != "EXHAUSTED":
                        result["exhaustion_state"] = "UNKNOWN"
                    if blocking_unknown:
                        result["total"]["available"] = None
                return result
            if limit["limit_mode"] == "OBSERVATION_ONLY":
                return annotate_unknown({
                    "grant_id": grant_id,
                    "resource_class": resource_class,
                    "dimension": dimension,
                    "limit_mode": "OBSERVATION_ONLY",
                    "spend_authority": False,
                    "ordinary": {"authorized": zero, "reserved": ordinary_reserved,
                                 "committed": ordinary_committed, "available": zero},
                    "finalization": {"authorized": zero, "reserved": final_reserved,
                                     "committed": final_committed, "available": zero},
                    "exhaustion_state": "EXHAUSTED",
                    "grant_expired": self._grant_expired(grant, now),
                }, finite=False)
            ordinary_authorized = Decimal(limit["ordinary_limit"])
            final_authorized = Decimal(limit["finalization_reserve"])
            ordinary_balance = _exact_subtract(ordinary_authorized, ordinary_reserved, ordinary_committed)
            final_balance = _exact_subtract(final_authorized, final_reserved, final_committed)
            total_authorized = _exact_sum([ordinary_authorized, final_authorized])
            total_reserved = _exact_sum([ordinary_reserved, final_reserved])
            total_committed = _exact_sum([ordinary_committed, final_committed])
            total_balance = _exact_subtract(total_authorized, total_reserved, total_committed)
            # A recorded overrun is a fact, not extra authority. Both pools
            # are bounded by the remaining total as well as their own limits.
            ordinary_available = max(zero, min(ordinary_balance, total_balance))
            final_available = max(zero, min(final_balance, total_balance))
            if _exact_compare(ordinary_available, zero) == 0 and _exact_compare(final_available, zero) == 0:
                exhaustion = "EXHAUSTED"
            elif _exact_compare(ordinary_available, zero) == 0 and _exact_compare(final_available, zero) > 0:
                exhaustion = "ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY"
            else:
                exhaustion = "NOT_EXHAUSTED"
            return annotate_unknown({
                "grant_id": grant_id,
                "resource_class": resource_class,
                "dimension": dimension,
                "limit_mode": limit["limit_mode"],
                "spend_authority": True,
                "ordinary": {
                    "authorized": ordinary_authorized,
                    "reserved": ordinary_reserved,
                    "committed": ordinary_committed,
                    "available": ordinary_available,
                    "deficit": max(zero, _exact_subtract(zero, ordinary_balance)),
                },
                "finalization": {
                    "authorized": final_authorized,
                    "reserved": final_reserved,
                    "committed": final_committed,
                    "available": final_available,
                    "deficit": max(zero, _exact_subtract(zero, final_balance)),
                },
                "total": {"authorized": total_authorized, "reserved": total_reserved,
                          "committed": total_committed, "available": max(zero, total_balance),
                          "deficit": max(zero, _exact_subtract(zero, total_balance))},
                "exhaustion_state": exhaustion,
                "grant_expired": self._grant_expired(grant, now),
            }, finite=True)
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    @classmethod
    def _shared_limits_on_conn(cls, conn: sqlite3.Connection, grant_id: str) -> list[dict[str, Any]]:
        try:
            rows = conn.execute(
                "SELECT * FROM grant_shared_limits WHERE grant_id = ? ORDER BY limit_id", (grant_id,)
            ).fetchall()
        except sqlite3.OperationalError as exc:
            # A database created by the previous ledger cannot yet contain any
            # shared limits. Do not require unrelated old grants to be migrated.
            if str(exc) == "no such table: grant_shared_limits":
                return []
            raise
        return [{"grant_id": row["grant_id"], "limit_id": row["limit_id"],
                 "authority_ref": row["authority_ref"], "interpretation_ref": row["interpretation_ref"],
                 "dimension": row["dimension"], "resource_classes": json.loads(row["resource_classes_json"]),
                 "total_limit": Decimal(row["total_limit"]),
                 "finalization_reserve": Decimal(row["finalization_reserve"])} for row in rows]

    @classmethod
    def _shared_state_on_conn(cls, conn: sqlite3.Connection, limit: dict[str, Any]) -> dict[str, Any]:
        classes = set(limit["resource_classes"])
        rows = conn.execute(
            "SELECT resource_class, pool, reserved, committed FROM reservation_allocations "
            "WHERE grant_id = ? AND dimension = ?",
            (limit["grant_id"], limit["dimension"]),
        ).fetchall()
        observations = [row for row in cls._unreserved_rows(conn, limit["grant_id"], limit["dimension"])
                        if row["resource_class"] in classes]
        def amounts(pool: str) -> tuple[Decimal, Decimal]:
            matching = [row for row in rows if row["resource_class"] in classes and row["pool"] == pool]
            return (_exact_sum([Decimal(row["reserved"]) for row in matching]),
                    _exact_sum([Decimal(row["committed"]) for row in matching]
                               + [Decimal(row["quantity"]) for row in observations
                                  if row["pool"] == pool and row["quantity"] is not None]))
        ordinary_reserved, ordinary_committed = amounts("ORDINARY")
        final_reserved, final_committed = amounts("FINALIZATION")
        ordinary_used = _exact_sum([ordinary_reserved, ordinary_committed])
        final_used = _exact_sum([final_reserved, final_committed])
        used = _exact_sum([ordinary_used, final_used])
        total = limit["total_limit"]
        reserve = limit["finalization_reserve"]
        ordinary_authorized = _exact_subtract(total, reserve)
        remaining = _exact_subtract(total, used)
        ordinary_available = max(Decimal(0), min(remaining, _exact_subtract(ordinary_authorized, ordinary_used)))
        # The reserve protects a portion from ordinary work. It is not a
        # separate ceiling on otherwise authorized finalization; per-class
        # grant limits and purposes still apply to every finalization request.
        final_available = max(Decimal(0), remaining)
        unknown_rows = [row for row in observations if row["quantity"] is None]
        blocking_unknown = any(cls._unknown_blocks(row) for row in unknown_rows)
        result = {**limit,
                "ordinary": {"authorized": ordinary_authorized, "reserved": ordinary_reserved,
                             "committed": ordinary_committed, "available": ordinary_available},
                "finalization": {"authorized": total, "reserved": final_reserved,
                                 "committed": final_committed, "available": final_available},
                "used": used, "deficit": max(Decimal(0), _exact_subtract(used, total)),
                "over_limit": _exact_compare(used, total) > 0}
        if unknown_rows:
            result["unknown_observations"] = len(unknown_rows)
            result["unknown_resource_state"] = "ACTUAL_UNKNOWN"
            result["availability_basis"] = ("UNKNOWN_FINITE_ACTUAL" if blocking_unknown
                                            else "KNOWN_RECORDED_ONLY")
            for name, pool in (("ordinary", "ORDINARY"), ("finalization", "FINALIZATION")):
                if any(row["pool"] == pool for row in unknown_rows):
                    result[name]["known_committed"] = result[name]["committed"]
                    result[name]["committed"] = None
                if blocking_unknown:
                    result[name]["available"] = None
            result["known_used"] = result["used"]
            result["used"] = None
            result["known_deficit"] = result["deficit"]
            result["deficit"] = None
            result["over_limit"] = True if result["over_limit"] else None
        return result

    def get_shared_limits(self, grant_id: str) -> list[dict[str, Any]]:
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            self._row_grant(conn, grant_id)
            return self._shared_limits_on_conn(conn, grant_id)
        finally:
            conn.close()

    def get_shared_limit_state(self, grant_id: str, limit_id: str) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        self._require_id(limit_id, "limit_id")
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            self._row_grant(conn, grant_id)
            matches = [item for item in self._shared_limits_on_conn(conn, grant_id) if item["limit_id"] == limit_id]
            if len(matches) != 1:
                raise AuthorityViolation("shared limit is not registered")
            return self._shared_state_on_conn(conn, matches[0])
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    @classmethod
    def _shared_view_on_conn(cls, conn: sqlite3.Connection, grant_id: str) -> dict[str, Any] | None:
        try:
            row = conn.execute("SELECT * FROM grant_shared_views WHERE grant_id = ?", (grant_id,)).fetchone()
        except sqlite3.OperationalError as exc:
            if str(exc) == "no such table: grant_shared_views":
                return None
            raise
        if row is None:
            return None
        lineage = json.loads(row["lineage_json"])
        return {"grant_id": row["grant_id"], "authority_ref": row["authority_ref"],
                "source_fingerprint": row["source_fingerprint"], "interpretation_ref": row["interpretation_ref"],
                "view_fingerprint": row["view_fingerprint"], "snapshot": row["snapshot"],
                "corrected": bool(row["corrected"]), "lineage": lineage,
                "per_class_corrected": any(isinstance(entry, dict) and entry.get("kind") == "PER_CLASS_CORRECTION"
                                           for entry in lineage)}

    @classmethod
    def _root_shared_row(cls, conn: sqlite3.Connection, grant_id: str) -> sqlite3.Row:
        seen: set[str] = set()
        while True:
            if grant_id in seen:
                raise AuthorityViolation("resource grant ancestry contains a cycle")
            seen.add(grant_id)
            row = cls._row_grant(conn, grant_id)
            if row["parent_grant_id"] is None:
                return row
            grant_id = row["parent_grant_id"]

    def get_owner_shared_selection(self, grant_id: str) -> dict[str, Any] | None:
        """Read the selected complete view, including an explicitly empty view."""
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            root = self._root_shared_row(conn, grant_id)
            return self._shared_view_on_conn(conn, root["grant_id"])
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    def get_owner_resource_snapshot(self, grant_id: str, authority_resolver: Any,
                                    resource_interpretation_ref: str | None = None) -> dict[str, Any]:
        """Read the grant, source and current view fingerprints for an explicit correction."""
        from tools.resource_admission import _canonical_owner_resource_decision
        self._require_id(grant_id, "grant_id")
        if not callable(authority_resolver):
            raise AuthorityViolation("Owner authority resolver is unavailable")
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            root = self._root_shared_row(conn, grant_id)
            original = json.loads(root["grant_json"])
            authority = original["authority_source"]
            if authority["authority_type"] != "OWNER_APPROVED_RESOURCE_AUTHORITY":
                raise AuthorityViolation("root grant is not bound to an Owner resource decision")
            ref = authority["authority_ref"]
            source = deepcopy(authority_resolver(ref))
            if _canonical_owner_resource_decision(source)["artifact_id"] != ref:
                raise AuthorityViolation("Owner resource source identity is unresolved")
            source_fingerprint = self._record_fingerprint(source)
            selection = self._shared_view_on_conn(conn, root["grant_id"])
            if selection:
                view = deepcopy(authority_resolver(selection["interpretation_ref"] or ref))
                if (selection["authority_ref"] != ref
                        or selection["source_fingerprint"] != source_fingerprint
                        or selection["view_fingerprint"] != self._record_fingerprint(view)):
                    raise AuthorityViolation("selected Owner view or source is unavailable or changed")
                if resource_interpretation_ref is None:
                    resource_interpretation_ref = selection["interpretation_ref"]
            if resource_interpretation_ref == ref:
                resource_interpretation_ref = None
            candidate = deepcopy(authority_resolver(resource_interpretation_ref)) if resource_interpretation_ref else source
            if _canonical_owner_resource_decision(candidate)["artifact_id"] != (resource_interpretation_ref or ref):
                raise AuthorityViolation("candidate Owner view identity is unresolved")
            return {"grant_id": root["grant_id"], "grant_fingerprint": root["fingerprint"],
                    "authority_ref": ref, "source_fingerprint": source_fingerprint,
                    "selection_snapshot": selection["snapshot"] if selection else None,
                    "effective_fingerprint": self._fingerprint(self._class_limits_on_conn(conn, root["grant_id"])),
                    "candidate_ref": resource_interpretation_ref,
                    "candidate_fingerprint": self._record_fingerprint(candidate)}
        except AuthorityViolation:
            raise
        except Exception as exc:
            raise AuthorityViolation("Owner resource source is unavailable") from exc
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    def _owner_shared_candidate(self, grant_id: str, authority_resolver: Any,
                                interpretation_ref: str | None, *, correction: bool,
                                per_class_correction: bool = False) -> dict[str, Any]:
        from tools.resource_admission import _canonical_grant, _owner_root_shared_limits
        if not callable(authority_resolver):
            raise AuthorityViolation("Owner authority resolver is unavailable")
        raw_grant = self.get_grant(grant_id)
        seen: set[str] = set()
        while raw_grant.get("parent_grant_ref") is not None:
            if grant_id in seen:
                raise AuthorityViolation("resource grant ancestry contains a cycle")
            seen.add(grant_id)
            grant_id = self._require_id(raw_grant["parent_grant_ref"], "parent_grant_ref")
            raw_grant = self.get_grant(grant_id)
        grant = _canonical_grant(self.get_effective_grant(grant_id))
        authority_ref = grant["authority_source"]["authority_ref"]
        try:
            source = authority_resolver(authority_ref)
            view = authority_resolver(interpretation_ref) if interpretation_ref is not None else source
            def resolved(ref: str) -> Any:
                if ref == authority_ref:
                    return source
                if interpretation_ref is not None and ref == interpretation_ref:
                    return view
                return authority_resolver(ref)
            limits = _owner_root_shared_limits(grant, resolved, interpretation_ref,
                                                allow_shared_correction=correction,
                                                allow_per_class_correction=per_class_correction)
            if limits is None:
                raise AuthorityViolation("Owner resource authority is unresolved")
            return {"grant_id": grant_id, "authority_ref": authority_ref,
                    "source_fingerprint": self._record_fingerprint(source),
                    "interpretation_ref": interpretation_ref, "view_fingerprint": self._record_fingerprint(view),
                    "limits": limits}
        except AuthorityViolation:
            raise
        except Exception as exc:
            raise AuthorityViolation("Owner resource authority is unresolved") from exc

    @classmethod
    def _insert_shared_view_limits(cls, conn: sqlite3.Connection, candidate: dict[str, Any]) -> None:
        # Equivalent descriptions within the same selected view describe one
        # boundary, even when they carry different technical identifiers.
        terms_seen: set[tuple[Any, ...]] = set()
        for limit in candidate["limits"]:
            terms = (limit["dimension"], tuple(limit["resource_classes"]),
                     limit["total_limit"], limit["finalization_reserve"])
            if terms in terms_seen:
                continue
            terms_seen.add(terms)
            conn.execute(
                "INSERT INTO grant_shared_limits "
                "(grant_id, limit_id, authority_ref, interpretation_ref, dimension, resource_classes_json, total_limit, finalization_reserve) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (candidate["grant_id"], limit["limit_id"], candidate["authority_ref"],
                 candidate["interpretation_ref"], limit["dimension"],
                 cls._canonical_json(limit["resource_classes"]), cls._decimal_text(limit["total_limit"]),
                 cls._decimal_text(limit["finalization_reserve"])),
            )

    @classmethod
    def _write_shared_view(cls, conn: sqlite3.Connection, root: sqlite3.Row,
                           candidate: dict[str, Any], previous: dict[str, Any] | None,
                           *, corrected: bool, per_class_correction: bool = False) -> dict[str, Any]:
        old_snapshot = previous["snapshot"] if previous else None
        snapshot = cls._fingerprint([root["grant_id"], root["fingerprint"], candidate["authority_ref"],
                                     candidate["source_fingerprint"], candidate["interpretation_ref"],
                                     candidate["view_fingerprint"], old_snapshot])
        lineage = list(previous["lineage"]) if previous else []
        if previous:
            lineage.append({key: previous[key] for key in (
                "authority_ref", "source_fingerprint", "interpretation_ref", "view_fingerprint", "snapshot")})
        if per_class_correction:
            lineage.append({"kind": "PER_CLASS_CORRECTION", "grant_fingerprint": root["fingerprint"],
                            "authority_ref": candidate["authority_ref"],
                            "source_fingerprint": candidate["source_fingerprint"],
                            "interpretation_ref": candidate["interpretation_ref"],
                            "view_fingerprint": candidate["view_fingerprint"], "snapshot": snapshot,
                            "previous_limits": candidate["previous_per_class_limits"],
                            "effective_limits": candidate["per_class_limits"]})
        if candidate.get("legacy_shared_refs"):
            lineage.append({"kind": "PREVIOUS_SHARED_REFS", "refs": candidate["legacy_shared_refs"]})
        conn.execute("DELETE FROM grant_shared_limits WHERE grant_id = ?", (root["grant_id"],))
        cls._insert_shared_view_limits(conn, candidate)
        conn.execute(
            "INSERT OR REPLACE INTO grant_shared_views "
            "(grant_id, authority_ref, source_fingerprint, interpretation_ref, view_fingerprint, snapshot, corrected, lineage_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (root["grant_id"], candidate["authority_ref"], candidate["source_fingerprint"],
             candidate["interpretation_ref"], candidate["view_fingerprint"], snapshot, int(corrected),
             cls._canonical_json(lineage)),
        )
        return cls._shared_view_on_conn(conn, root["grant_id"])

    def register_owner_shared_limits(self, grant_id: str, authority_resolver: Any,
                                     resource_interpretation_ref: str | None = None) -> list[dict[str, Any]]:
        """Select one complete view; ordinary registration never replaces it."""
        from tools.resource_admission import _canonical_owner_resource_decision, _same_record_value, _shared_limit_terms
        self._require_id(grant_id, "grant_id")
        selected = self.get_owner_shared_selection(grant_id)
        if selected and resource_interpretation_ref is None:
            resource_interpretation_ref = selected["interpretation_ref"]
        candidate = self._owner_shared_candidate(grant_id, authority_resolver, resource_interpretation_ref,
                                                  correction=bool(selected and selected["corrected"]),
                                                  per_class_correction=bool(selected and selected["per_class_corrected"]))
        if selected:
            old_ref = selected["interpretation_ref"] or selected["authority_ref"]
            try:
                old_view = authority_resolver(old_ref)
                old_interpretation = _canonical_owner_resource_decision(old_view)["resource_interpretation"]
                new_view = authority_resolver(resource_interpretation_ref or candidate["authority_ref"])
                new_interpretation = _canonical_owner_resource_decision(new_view)["resource_interpretation"]
                same_context = (old_interpretation is None and new_interpretation is None) or (
                    isinstance(old_interpretation, dict) and isinstance(new_interpretation, dict)
                    and _same_record_value({k: v for k, v in old_interpretation.items() if k != "shared_limits"},
                                           {k: v for k, v in new_interpretation.items() if k != "shared_limits"}))
                if (candidate["authority_ref"] != selected["authority_ref"]
                        or candidate["source_fingerprint"] != selected["source_fingerprint"]
                        or self._record_fingerprint(old_view) != selected["view_fingerprint"]
                        or not same_context
                        or _shared_limit_terms(candidate["limits"]) != _shared_limit_terms(
                            old_interpretation["shared_limits"] if old_interpretation else [])):
                    raise AuthorityViolation("a different Owner view requires explicit correction")
            except AuthorityViolation:
                raise
            except Exception as exc:
                raise AuthorityViolation("selected Owner view is unresolved") from exc
        elif (not candidate["limits"] and resource_interpretation_ref is None
              and not self.get_shared_limits(candidate["grant_id"])):
            return []
        self.initialize()
        conn = self._connect()
        try:
            self._begin_write(conn)
            root = self._root_shared_row(conn, grant_id)
            current = self._shared_view_on_conn(conn, root["grant_id"])
            if (current or {}).get("snapshot") != (selected or {}).get("snapshot"):
                raise AuthorityViolation("selected Owner view changed concurrently")
            if current is None:
                existing = self._shared_limits_on_conn(conn, root["grant_id"])
                if existing and (any(item["authority_ref"] != candidate["authority_ref"] for item in existing)
                                 or _shared_limit_terms(existing) != _shared_limit_terms(candidate["limits"])):
                    raise AuthorityViolation("existing shared limits do not match the complete Owner view")
                self._write_shared_view(conn, root, candidate, None, corrected=False)
            states = [self._shared_state_on_conn(conn, limit)
                      for limit in self._shared_limits_on_conn(conn, root["grant_id"])]
            conn.commit()
            return states
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def replace_owner_shared_limits(self, grant_id: str, authority_resolver: Any,
                                    resource_interpretation_ref: str | None, *,
                                    expected_snapshot: str, expected_source_fingerprint: str) -> list[dict[str, Any]]:
        """Explicitly correct a previously reviewed view against the same Owner source.

        The responsible intake verifies the real source and supplies the complete
        corrected view. The ledger compares the observed selection and source in
        its write transaction; it does not interpret or authenticate Owner words.
        """
        self._require_id(grant_id, "grant_id")
        if not isinstance(expected_snapshot, str) or not isinstance(expected_source_fingerprint, str):
            raise AuthorityViolation("the reviewed view and source snapshot are required")
        selected = self.get_owner_shared_selection(grant_id)
        candidate = self._owner_shared_candidate(grant_id, authority_resolver, resource_interpretation_ref,
                                                  correction=True,
                                                  per_class_correction=bool(selected and selected["per_class_corrected"]))
        self.initialize()
        conn = self._connect()
        try:
            self._begin_write(conn)
            root = self._root_shared_row(conn, grant_id)
            current = self._shared_view_on_conn(conn, root["grant_id"])
            if (current is None or current["snapshot"] != expected_snapshot
                    or current["source_fingerprint"] != expected_source_fingerprint
                    or candidate["source_fingerprint"] != expected_source_fingerprint
                    or current["authority_ref"] != candidate["authority_ref"]):
                raise AuthorityViolation("reviewed Owner view or source changed")
            self._write_shared_view(conn, root, candidate, current, corrected=True)
            states = [self._shared_state_on_conn(conn, limit)
                      for limit in self._shared_limits_on_conn(conn, root["grant_id"])]
            conn.commit()
            return states
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def replace_owner_per_class_limits(self, grant_id: str, authority_resolver: Any,
                                       resource_interpretation_ref: str | None = None, *,
                                       expected_snapshot: dict[str, Any]) -> dict[str, Any]:
        """Correct the root's effective limits against its already recorded Owner source.

        The responsible intake must inspect that source and supply the complete
        interpretation. Fingerprints compare the reviewed inputs; they do not
        authenticate the source or interpret the Owner's words.
        """
        from tools.resource_admission import (
            _canonical_grant, _canonical_owner_resource_decision, _owner_root_shared_limits,
            _shared_limit_terms,
        )
        self._require_id(grant_id, "grant_id")
        if not callable(authority_resolver) or not isinstance(expected_snapshot, dict):
            raise AuthorityViolation("the reviewed Owner source and ledger snapshot are required")
        required = {"grant_id", "grant_fingerprint", "authority_ref", "source_fingerprint",
                    "selection_snapshot", "effective_fingerprint", "candidate_ref", "candidate_fingerprint"}
        if set(expected_snapshot) != required:
            raise AuthorityViolation("the reviewed Owner resource snapshot is malformed")
        selected = self.get_owner_shared_selection(grant_id)
        try:
            root_id = expected_snapshot["grant_id"]
            original = self.get_grant(root_id)
            authority_ref = original["authority_source"]["authority_ref"]
            if selected and resource_interpretation_ref is None:
                resource_interpretation_ref = selected["interpretation_ref"]
            if resource_interpretation_ref == authority_ref:
                resource_interpretation_ref = None
            if resource_interpretation_ref != expected_snapshot["candidate_ref"]:
                raise AuthorityViolation("the reviewed candidate Owner view changed")
            source = deepcopy(authority_resolver(authority_ref))
            view = deepcopy(authority_resolver(resource_interpretation_ref)) if resource_interpretation_ref else source
            owner = _canonical_owner_resource_decision(view)
            candidate_grant = {**original, "limits": owner["authorized_resource_limits"]}
            normalized, _ = self._validate_grant(candidate_grant)
            effective = _canonical_grant(candidate_grant)
            def resolved(ref: str) -> Any:
                if ref == authority_ref:
                    return source
                if resource_interpretation_ref is not None and ref == resource_interpretation_ref:
                    return view
                return authority_resolver(ref)
            limits = _owner_root_shared_limits(
                effective, resolved, resource_interpretation_ref,
                allow_shared_correction=bool(selected and selected["corrected"]),
                allow_per_class_correction=True,
            )
            if limits is None:
                raise AuthorityViolation("corrected Owner resource interpretation is unresolved")
            candidate = {"grant_id": root_id, "authority_ref": authority_ref,
                         "source_fingerprint": self._record_fingerprint(source),
                         "interpretation_ref": resource_interpretation_ref,
                         "view_fingerprint": self._record_fingerprint(view),
                         "limits": limits, "per_class_limits": normalized["limits"]}
            if selected:
                old_ref = selected["interpretation_ref"] or authority_ref
                if self._record_fingerprint(authority_resolver(old_ref)) != selected["view_fingerprint"]:
                    raise AuthorityViolation("the selected Owner interpretation changed")
        except AuthorityViolation:
            raise
        except Exception as exc:
            raise AuthorityViolation("corrected Owner resource interpretation is unresolved") from exc
        self.initialize()
        conn = self._connect()
        try:
            self._begin_write(conn)
            root = self._root_shared_row(conn, grant_id)
            current = self._shared_view_on_conn(conn, root["grant_id"])
            old_limits = self._class_limits_on_conn(conn, root["grant_id"])
            if (root["grant_id"] != expected_snapshot["grant_id"]
                    or root["fingerprint"] != expected_snapshot["grant_fingerprint"]
                    or candidate["authority_ref"] != expected_snapshot["authority_ref"]
                    or candidate["source_fingerprint"] != expected_snapshot["source_fingerprint"]
                    or candidate["view_fingerprint"] != expected_snapshot["candidate_fingerprint"]
                    or (current or {}).get("snapshot") != expected_snapshot["selection_snapshot"]
                    or self._fingerprint(old_limits) != expected_snapshot["effective_fingerprint"]
                    or (current is not None and (
                        current["authority_ref"] != candidate["authority_ref"]
                        or current["source_fingerprint"] != candidate["source_fingerprint"]))):
                raise AuthorityViolation("the reviewed grant, Owner source or effective view changed")
            existing = self._shared_limits_on_conn(conn, root["grant_id"])
            if current is not None or existing:
                if (any(item["authority_ref"] != candidate["authority_ref"] for item in existing)
                        or _shared_limit_terms(existing) != _shared_limit_terms(candidate["limits"])):
                    raise AuthorityViolation("per-class correction must preserve the selected shared groups")
                candidate["limits"] = [{key: item[key] for key in
                    ("limit_id", "dimension", "resource_classes", "total_limit", "finalization_reserve")}
                    for item in existing]
                if current is None:
                    candidate["legacy_shared_refs"] = sorted({
                        item["interpretation_ref"] or item["authority_ref"] for item in existing})
            candidate["previous_per_class_limits"] = old_limits
            conn.execute("DELETE FROM grant_limits WHERE grant_id = ?", (root["grant_id"],))
            conn.executemany(
                "INSERT INTO grant_limits "
                "(grant_id, resource_class, dimension, limit_mode, ordinary_limit, finalization_reserve) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(root["grant_id"], limit["resource_class"], limit["dimension"], limit["limit_mode"],
                  limit["ordinary_limit"], limit["finalization_reserve"])
                 for limit in candidate["per_class_limits"]],
            )
            result = self._write_shared_view(conn, root, candidate, current,
                corrected=bool(current and current["corrected"]), per_class_correction=True)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reserve(
        self,
        grant_id: str,
        resource_class: str,
        dimension: str,
        quantity: Any,
        reservation_id: str,
        operation_id: str,
        idempotency_key: str,
        pool: str = "ORDINARY",
        purpose: str | None = None,
        expires_at: datetime | str | None = None,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        for value, name in [
            (grant_id, "grant_id"), (resource_class, "resource_class"), (dimension, "dimension"),
            (reservation_id, "reservation_id"), (operation_id, "operation_id"), (idempotency_key, "idempotency_key"),
        ]:
            self._require_id(value, name)
        amount = self._decimal(quantity, "quantity", allow_zero=False)
        if pool not in {"ORDINARY", "FINALIZATION"}:
            raise ResourceLedgerError("pool must be ORDINARY or FINALIZATION")
        if pool == "FINALIZATION":
            if purpose not in _FINALIZATION_PURPOSES:
                raise AuthorityViolation("FINALIZATION requires an authorized frozen purpose")
        elif purpose is not None:
            raise ResourceLedgerError("ordinary reservations do not carry a finalization purpose")
        now_dt = self._now(now)
        expires_dt = self._parse_datetime(expires_at, "expires_at", nullable=True)
        if expires_dt is not None and expires_dt <= now_dt:
            raise ResourceLedgerError("expires_at must be after reservation creation time")
        request = {
            "grant_id": grant_id,
            "resource_class": resource_class,
            "dimension": dimension,
            "quantity": self._decimal_text(amount),
            "reservation_id": reservation_id,
            "operation_id": operation_id,
            "pool": pool,
            "purpose": purpose,
            "expires_at": self._datetime_text(expires_dt) if expires_dt else None,
        }
        fingerprint = self._fingerprint(request)
        created_at_text = self._datetime_text(now_dt)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "RESERVE", fingerprint)
            if prior is not None:
                conn.commit()
                return prior

            existing = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if existing is not None:
                same = (
                    existing["grant_id"] == grant_id
                    and existing["resource_class"] == resource_class
                    and existing["dimension"] == dimension
                    and existing["quantity"] == self._decimal_text(amount)
                    and existing["operation_id"] == operation_id
                    and existing["pool"] == pool
                    and existing["purpose"] == purpose
                    and existing["expires_at"] == request["expires_at"]
                )
                if not same:
                    raise IdempotencyConflict("reservation_id is already bound to a conflicting request")
                result = self._reservation_result(existing)
                result = self._record_idempotency(conn, idempotency_key, "RESERVE", fingerprint, result)
                conn.commit()
                return result

            chain = self._ancestry(conn, grant_id)
            allocation_grants: list[sqlite3.Row] = []
            for grant_row in chain:
                if self._grant_expired(grant_row, now_dt):
                    raise GrantExpired(f"grant expired: {grant_row['grant_id']}")
                limit = self._limit_row(conn, grant_row["grant_id"], resource_class, dimension)
                if limit["limit_mode"] == "OBSERVATION_ONLY":
                    raise AuthorityViolation("OBSERVATION_ONLY creates no spend authority")
                if any(row["resource_class"] == resource_class and self._unknown_blocks(row)
                       for row in self._unreserved_rows(conn, grant_row["grant_id"], dimension)):
                    raise ResourceLedgerError("resource availability is unknown because an actual is unmeasured")
                if pool == "FINALIZATION":
                    allowed = conn.execute(
                        "SELECT 1 FROM grant_finalization_purposes WHERE grant_id = ? AND purpose = ?",
                        (grant_row["grant_id"], purpose),
                    ).fetchone()
                    if allowed is None:
                        raise AuthorityViolation("finalization purpose is not authorized throughout the grant chain")
                authorized = Decimal(
                    limit["ordinary_limit"] if pool == "ORDINARY" else limit["finalization_reserve"]
                )
                reserved, committed = self._allocation_totals(
                    conn, grant_row["grant_id"], resource_class, dimension, pool
                )
                used_after = _exact_sum([committed, reserved, amount])
                if _exact_compare(used_after, authorized) > 0:
                    raise InsufficientCapacity(
                        f"insufficient {pool.lower()} capacity at grant {grant_row['grant_id']}"
                    )
                other_pool = "FINALIZATION" if pool == "ORDINARY" else "ORDINARY"
                other_reserved, other_committed = self._allocation_totals(
                    conn, grant_row["grant_id"], resource_class, dimension, other_pool
                )
                total_authorized = _exact_sum([Decimal(limit["ordinary_limit"]), Decimal(limit["finalization_reserve"])])
                if _exact_compare(_exact_sum([used_after, other_reserved, other_committed]), total_authorized) > 0:
                    raise InsufficientCapacity(f"insufficient total capacity at grant {grant_row['grant_id']}")
                for shared in self._shared_limits_on_conn(conn, grant_row["grant_id"]):
                    if shared["dimension"] != dimension or resource_class not in shared["resource_classes"]:
                        continue
                    state = self._shared_state_on_conn(conn, shared)
                    available = state["ordinary" if pool == "ORDINARY" else "finalization"]["available"]
                    if available is None:
                        raise ResourceLedgerError("shared resource availability is unknown because an actual is unmeasured")
                    if _exact_compare(amount, available) > 0:
                        raise InsufficientCapacity(
                            f"insufficient shared {pool.lower()} capacity at grant {grant_row['grant_id']}"
                        )
                allocation_grants.append(grant_row)

            conn.execute(
                """
                INSERT INTO reservations(
                    reservation_id, grant_id, resource_class, dimension, quantity, operation_id,
                    pool, purpose, created_at, expires_at, status, committed_quantity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'RESERVED', NULL)
                """,
                (
                    reservation_id, grant_id, resource_class, dimension, self._decimal_text(amount), operation_id,
                    pool, purpose, created_at_text, request["expires_at"],
                ),
            )
            for grant_row in allocation_grants:
                conn.execute(
                    """
                    INSERT INTO reservation_allocations(
                        reservation_id, grant_id, resource_class, dimension, pool, reserved, committed
                    ) VALUES (?, ?, ?, ?, ?, ?, '0')
                    """,
                    (
                        reservation_id, grant_row["grant_id"], resource_class, dimension, pool,
                        self._decimal_text(amount),
                    ),
                )
            created = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if created is None:
                raise ResourceLedgerError("reservation mutation did not materialize")
            result = self._record_idempotency(
                conn, idempotency_key, "RESERVE", fingerprint, self._reservation_result(created)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def _reservation_result(cls, row: sqlite3.Row) -> dict[str, Any]:
        actual = Decimal(row["committed_quantity"]) if row["committed_quantity"] is not None else None
        sources = None
        if "measurement_sources_json" in row.keys() and row["measurement_sources_json"] is not None:
            try:
                sources = json.loads(row["measurement_sources_json"])
            except (TypeError, ValueError):
                raise ResourceLedgerError("stored measurement sources are malformed") from None
            if not isinstance(sources, list) or not all(isinstance(ref, str) and ref for ref in sources):
                raise ResourceLedgerError("stored measurement sources are malformed")
        return {
            "reservation_id": row["reservation_id"],
            "grant_id": row["grant_id"],
            "resource_class": row["resource_class"],
            "dimension": row["dimension"],
            "quantity": Decimal(row["quantity"]),
            "operation_id": row["operation_id"],
            "pool": row["pool"],
            "purpose": row["purpose"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "status": row["status"],
            "committed_quantity": actual,
            "actual_over_reservation": (max(Decimal(0), _exact_subtract(actual, Decimal(row["quantity"])))
                                        if actual is not None else None),
            "measurement_source_refs": sources,
        }

    def get_reservation(self, reservation_id: str) -> dict[str, Any]:
        """Read the reservation and any separately recorded usage evidence."""
        self._require_id(reservation_id, "reservation_id")
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if row is None:
                raise InvalidReservationTransition("reservation does not exist")
            return self._reservation_result(row)
        finally:
            conn.close()

    @classmethod
    def _unreserved_result(cls, row: sqlite3.Row) -> dict[str, Any]:
        try:
            history = json.loads(row["history_json"])
            if not isinstance(history, list):
                raise ValueError("history is not a list")
            for entry in history:
                if not isinstance(entry, dict):
                    raise ValueError("history entry is not an object")
                for name in ("quantity", "last_known_quantity"):
                    if entry.get(name) is not None:
                        entry[name] = Decimal(entry[name])
        except (ValueError, TypeError, InvalidOperation):
            raise ResourceLedgerError("stored unreserved usage history is malformed") from None
        return {
            "observation_id": row["observation_id"], "grant_id": row["grant_id"],
            "resource_class": row["resource_class"], "dimension": row["dimension"],
            "operation_id": row["operation_id"], "pool": row["pool"], "status": row["status"],
            "quantity": Decimal(row["quantity"]) if row["quantity"] is not None else None,
            "last_known_quantity": (Decimal(row["last_known_quantity"])
                                    if row["last_known_quantity"] is not None else None),
            "metering_quality": row["metering_quality"], "unknown_resource_state": row["unknown_resource_state"],
            "measurement_source_ref": row["measurement_source_ref"],
            "rate_or_quota_revision_ref": row["rate_or_quota_revision_ref"],
            "revision": row["revision"], "history": history,
        }

    def get_unreserved_usage(self, observation_id: str) -> dict[str, Any]:
        self._require_id(observation_id, "observation_id")
        conn = self._connect()
        try:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'unreserved_usage'").fetchone() is None:
                raise ResourceLedgerError("unreserved observation does not exist")
            row = conn.execute("SELECT * FROM unreserved_usage WHERE observation_id = ?", (observation_id,)).fetchone()
            if row is None:
                raise ResourceLedgerError("unreserved observation does not exist")
            return self._unreserved_result(row)
        finally:
            conn.close()

    def record_unreserved_usage(
        self, grant_id: str, resource_class: str, dimension: str, quantity: Any,
        observation_id: str, *, operation_id: str | None = None, pool: str = "ORDINARY",
        metering_quality: str | None = None, measurement_source_ref: str | None = None,
        rate_or_quota_revision_ref: str | None = None, unknown_resource_state: str | None = None,
        expected_revision: int | None = None, idempotency_key: str | None = None,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Record a fact not already represented by a reservation, without authorizing spend.

        Use commit for an actual linked to a reservation. A stable observation
        identity handles retries; use its current revision for corrections.
        Different identities may be distinct costs even with one source or operation.
        """
        for value, name in [(grant_id, "grant_id"), (resource_class, "resource_class"),
                            (dimension, "dimension"), (observation_id, "observation_id")]:
            self._require_id(value, name)
        for value, name in [(operation_id, "operation_id"), (measurement_source_ref, "measurement_source_ref"),
                            (rate_or_quota_revision_ref, "rate_or_quota_revision_ref"), (idempotency_key, "idempotency_key")]:
            if value is not None:
                self._require_id(value, name)
        if not _IDENTIFIER.fullmatch(resource_class) or not _IDENTIFIER.fullmatch(dimension):
            raise ResourceLedgerError("resource class and dimension must use canonical identifiers")
        if pool not in {"ORDINARY", "FINALIZATION"}:
            raise ResourceLedgerError("pool must be ORDINARY or FINALIZATION")
        if expected_revision is not None and (isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int) or expected_revision < 1):
            raise ResourceLedgerError("expected_revision must be a positive integer or null")
        amount = None if quantity is None else self._decimal(quantity, "quantity")
        quality = metering_quality if metering_quality is not None else ("UNKNOWN" if amount is None else "NORMALIZED_ACTUAL")
        if quality not in {"AUTHORITATIVE_ACTUAL", "NORMALIZED_ACTUAL", "UNKNOWN"}:
            raise ResourceLedgerError("unreserved usage must be an actual or unknown")
        if (quality == "UNKNOWN") != (amount is None):
            raise ResourceLedgerError("unknown usage must have null quantity")
        if quality == "AUTHORITATIVE_ACTUAL" and measurement_source_ref is None:
            raise ResourceLedgerError("authoritative actual requires a measurement source")
        unknown = unknown_resource_state if unknown_resource_state is not None else ("ACTUAL_UNKNOWN" if amount is None else "KNOWN")
        if (not isinstance(unknown, str) or not unknown.strip() or (amount is None and unknown == "KNOWN")
                or (amount is not None and unknown != "KNOWN")):
            raise ResourceLedgerError("unknown state contradicts its quantity")
        amount_text = None if amount is None else self._decimal_text(amount)
        request = {"grant_id": grant_id, "resource_class": resource_class, "dimension": dimension,
                   "quantity": amount_text, "observation_id": observation_id, "operation_id": operation_id,
                   "pool": pool, "metering_quality": quality, "unknown_resource_state": unknown,
                   "measurement_source_ref": measurement_source_ref,
                   "rate_or_quota_revision_ref": rate_or_quota_revision_ref, "expected_revision": expected_revision}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            if idempotency_key is not None:
                prior = self._idempotency_lookup(conn, idempotency_key, "UNRESERVED_USAGE", fingerprint)
                if prior is not None:
                    conn.commit()
                    return prior
            self._ensure_unreserved_usage(conn)
            # Reporting facts, even unauthorized or late facts, grants no authority.
            self._ancestry(conn, grant_id)
            current = conn.execute("SELECT * FROM unreserved_usage WHERE observation_id = ?", (observation_id,)).fetchone()
            fields = (grant_id, resource_class, dimension, operation_id, pool, amount_text,
                      quality, unknown, measurement_source_ref, rate_or_quota_revision_ref)
            names = ("grant_id", "resource_class", "dimension", "operation_id", "pool", "quantity",
                     "metering_quality", "unknown_resource_state", "measurement_source_ref", "rate_or_quota_revision_ref")
            if current is None:
                if expected_revision is not None:
                    raise IdempotencyConflict("observation revision does not exist")
                revision, history, last_known = 1, [], None
            elif current["status"] == "ACTIVE" and all(current[name] == value for name, value in zip(names, fields)):
                result = self._unreserved_result(current)
                if idempotency_key is not None:
                    result = self._record_idempotency(conn, idempotency_key, "UNRESERVED_USAGE", fingerprint, result)
                conn.commit()
                return result
            else:
                if expected_revision != current["revision"]:
                    raise IdempotencyConflict("observation correction requires its current revision")
                revision = current["revision"] + 1
                history = json.loads(current["history_json"])
                if not isinstance(history, list):
                    raise ResourceLedgerError("stored unreserved usage history is malformed")
                last_known = current["quantity"] or current["last_known_quantity"]
            if amount is not None:
                last_known = None
            snapshot = {**{name: value for name, value in zip(names, fields)}, "status": "ACTIVE",
                        "revision": revision, "last_known_quantity": last_known,
                        "recorded_at": self._datetime_text(self._now(now))}
            history.append(snapshot)
            values = (grant_id, resource_class, dimension, operation_id, pool, "ACTIVE", amount_text,
                      last_known, quality, unknown, measurement_source_ref, rate_or_quota_revision_ref,
                      revision, self._canonical_json(history), observation_id)
            if current is None:
                conn.execute("""INSERT INTO unreserved_usage (grant_id, resource_class, dimension, operation_id,
                    pool, status, quantity, last_known_quantity, metering_quality, unknown_resource_state,
                    measurement_source_ref, rate_or_quota_revision_ref, revision, history_json, observation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
            else:
                conn.execute("""UPDATE unreserved_usage SET grant_id=?, resource_class=?, dimension=?, operation_id=?,
                    pool=?, status=?, quantity=?, last_known_quantity=?, metering_quality=?, unknown_resource_state=?,
                    measurement_source_ref=?, rate_or_quota_revision_ref=?, revision=?, history_json=?
                    WHERE observation_id=?""", values)
            row = conn.execute("SELECT * FROM unreserved_usage WHERE observation_id = ?", (observation_id,)).fetchone()
            result = self._unreserved_result(row)
            if idempotency_key is not None:
                result = self._record_idempotency(conn, idempotency_key, "UNRESERVED_USAGE", fingerprint, result)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def withdraw_unreserved_usage(self, observation_id: str, *, expected_revision: int,
                                  reason: str, now: datetime | str | None = None) -> dict[str, Any]:
        """Withdraw an erroneous/duplicate accounting record, preserving its history."""
        self._require_id(observation_id, "observation_id")
        self._require_id(reason, "reason")
        if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 1:
            raise ResourceLedgerError("expected_revision must be a positive integer")
        conn = self._connect()
        try:
            self._begin_write(conn)
            self._ensure_unreserved_usage(conn)
            current = conn.execute("SELECT * FROM unreserved_usage WHERE observation_id = ?", (observation_id,)).fetchone()
            if current is None:
                raise ResourceLedgerError("unreserved observation does not exist")
            history = json.loads(current["history_json"])
            if not isinstance(history, list) or not history:
                raise ResourceLedgerError("stored unreserved usage history is malformed")
            if (current["status"] == "WITHDRAWN" and history[-1].get("reason") == reason
                    and expected_revision == current["revision"] - 1):
                conn.commit()
                return self._unreserved_result(current)
            if current["status"] != "ACTIVE" or expected_revision != current["revision"]:
                raise IdempotencyConflict("withdrawal requires the current active observation revision")
            revision = current["revision"] + 1
            history.append({"revision": revision, "status": "WITHDRAWN", "reason": reason,
                            "quantity": current["quantity"], "last_known_quantity": current["last_known_quantity"],
                            "recorded_at": self._datetime_text(self._now(now))})
            conn.execute("UPDATE unreserved_usage SET status='WITHDRAWN', revision=?, history_json=? WHERE observation_id=?",
                         (revision, self._canonical_json(history), observation_id))
            updated = conn.execute("SELECT * FROM unreserved_usage WHERE observation_id = ?", (observation_id,)).fetchone()
            conn.commit()
            return self._unreserved_result(updated)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def _attach_measurement_source(cls, conn: sqlite3.Connection, row: sqlite3.Row,
                                   source_ref: str | None) -> sqlite3.Row:
        if source_ref is None:
            return row
        if "measurement_sources_json" not in row.keys():
            # An old shared ledger remains usable without migration until a
            # real measurement source must be preserved.
            conn.execute("ALTER TABLE reservations ADD COLUMN measurement_sources_json TEXT NULL")
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (row["reservation_id"],)).fetchone()
            if row is None:
                raise ResourceLedgerError("reservation disappeared while recording measurement")
        sources = cls._reservation_result(row)["measurement_source_refs"] or []
        if source_ref not in sources:
            sources.append(source_ref)
            conn.execute("UPDATE reservations SET measurement_sources_json = ? WHERE reservation_id = ?",
                         (cls._canonical_json(sources), row["reservation_id"]))
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (row["reservation_id"],)).fetchone()
            if row is None:
                raise ResourceLedgerError("reservation disappeared while recording measurement")
        return row

    def commit(
        self,
        reservation_id: str,
        quantity: Any,
        idempotency_key: str,
        now: datetime | str | None = None,
        *,
        measurement_source_ref: str | None = None,
    ) -> dict[str, Any]:
        self._require_id(reservation_id, "reservation_id")
        self._require_id(idempotency_key, "idempotency_key")
        if measurement_source_ref is not None:
            self._require_id(measurement_source_ref, "measurement_source_ref")
        actual = self._decimal(quantity, "quantity")
        now_dt = self._now(now)
        request = {"reservation_id": reservation_id, "quantity": self._decimal_text(actual)}
        if measurement_source_ref is not None:
            request["measurement_source_ref"] = measurement_source_ref
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "COMMIT", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if row is None:
                raise InvalidReservationTransition("reservation does not exist")
            if row["committed_quantity"] is not None:
                if _exact_compare(Decimal(row["committed_quantity"]), actual) != 0:
                    raise InvalidReservationTransition("reservation already committed with a different quantity")
                row = self._attach_measurement_source(conn, row, measurement_source_ref)
                result = self._record_idempotency(
                    conn, idempotency_key, "COMMIT", fingerprint, self._reservation_result(row)
                )
                conn.commit()
                return result
            if row["status"] not in {"RESERVED", "RELEASED", "EXPIRED"}:
                raise InvalidReservationTransition(f"cannot commit reservation in state {row['status']}")
            status = row["status"]
            expires_raw = row["expires_at"] if status == "RESERVED" else None
            if expires_raw is not None:
                expires = self._parse_datetime(expires_raw, "expires_at")
                if expires is None:
                    raise ResourceLedgerError("stored reservation expiry is malformed")
                if expires <= now_dt:
                    self._expire_one(conn, reservation_id)
                    status = "EXPIRED"
            if status == "RESERVED":
                status = "COMMITTED"
            conn.execute(
                "UPDATE reservation_allocations SET reserved = '0', committed = ? WHERE reservation_id = ?",
                (self._decimal_text(actual), reservation_id),
            )
            conn.execute(
                "UPDATE reservations SET status = ?, committed_quantity = ? WHERE reservation_id = ?",
                (status, self._decimal_text(actual), reservation_id),
            )
            updated = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if updated is None:
                raise ResourceLedgerError("reservation commit did not materialize")
            updated = self._attach_measurement_source(conn, updated, measurement_source_ref)
            result = self._record_idempotency(
                conn, idempotency_key, "COMMIT", fingerprint, self._reservation_result(updated)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(
        self,
        reservation_id: str,
        idempotency_key: str,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        self._require_id(reservation_id, "reservation_id")
        self._require_id(idempotency_key, "idempotency_key")
        if now is not None:
            self._now(now)
        request = {"reservation_id": reservation_id}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "RELEASE", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if row is None:
                raise InvalidReservationTransition("reservation does not exist")
            if row["status"] == "RELEASED":
                result = self._record_idempotency(
                    conn, idempotency_key, "RELEASE", fingerprint, self._reservation_result(row)
                )
                conn.commit()
                return result
            if row["status"] != "RESERVED":
                raise InvalidReservationTransition(f"cannot release reservation in state {row['status']}")
            conn.execute(
                "UPDATE reservation_allocations SET reserved = '0' WHERE reservation_id = ?", (reservation_id,)
            )
            conn.execute(
                "UPDATE reservations SET status = 'RELEASED' WHERE reservation_id = ?", (reservation_id,)
            )
            updated = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if updated is None:
                raise ResourceLedgerError("reservation release did not materialize")
            result = self._record_idempotency(
                conn, idempotency_key, "RELEASE", fingerprint, self._reservation_result(updated)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _expire_one(conn: sqlite3.Connection, reservation_id: str) -> None:
        conn.execute(
            "UPDATE reservation_allocations SET reserved = '0' WHERE reservation_id = ?", (reservation_id,)
        )
        conn.execute(
            "UPDATE reservations SET status = 'EXPIRED' WHERE reservation_id = ? AND status = 'RESERVED'",
            (reservation_id,),
        )

    def expire_reservations(self, now: datetime | str) -> list[str]:
        now_dt = self._now(now)
        conn = self._connect()
        try:
            self._begin_write(conn)
            candidates = conn.execute(
                """
                SELECT reservation_id, expires_at
                FROM reservations
                WHERE status = 'RESERVED' AND expires_at IS NOT NULL
                ORDER BY reservation_id
                """
            ).fetchall()
            ids: list[str] = []
            for row in candidates:
                parsed = self._parse_datetime(row["expires_at"], "expires_at")
                if parsed is None:
                    raise ResourceLedgerError("stored reservation expiry is malformed")
                if parsed <= now_dt:
                    ids.append(row["reservation_id"])
            for reservation_id in ids:
                self._expire_one(conn, reservation_id)
            conn.commit()
            return ids
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def claim_attempt(
        self,
        grant_id: str,
        operation_id: str,
        idempotency_key: str,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        self._require_id(operation_id, "operation_id")
        self._require_id(idempotency_key, "idempotency_key")
        now_dt = self._now(now)
        request = {"grant_id": grant_id, "operation_id": operation_id}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "ATTEMPT", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            existing = conn.execute(
                "SELECT claim_id, created_at FROM attempt_claims WHERE grant_id = ? AND operation_id = ?",
                (grant_id, operation_id),
            ).fetchone()
            if existing is not None:
                result = {
                    "claim_id": existing["claim_id"],
                    "grant_id": grant_id,
                    "operation_id": operation_id,
                    "created_at": existing["created_at"],
                }
                result = self._record_idempotency(conn, idempotency_key, "ATTEMPT", fingerprint, result)
                conn.commit()
                return result
            chain = self._ancestry(conn, grant_id)
            bounded: list[sqlite3.Row] = []
            for grant_row in chain:
                if self._grant_expired(grant_row, now_dt):
                    raise GrantExpired(f"grant expired: {grant_row['grant_id']}")
                if grant_row["attempt_limit"] is None:
                    continue
                count_row = conn.execute(
                    "SELECT COUNT(*) AS n FROM attempt_allocations WHERE grant_id = ?",
                    (grant_row["grant_id"],),
                ).fetchone()
                if count_row is None:
                    raise ResourceLedgerError("attempt allocation count could not be read")
                claimed = int(count_row["n"])
                if claimed >= int(grant_row["attempt_limit"]):
                    raise InsufficientCapacity(f"attempt authority exhausted at grant {grant_row['grant_id']}")
                bounded.append(grant_row)
            cursor = conn.execute(
                "INSERT INTO attempt_claims(grant_id, operation_id, created_at) VALUES (?, ?, ?)",
                (grant_id, operation_id, self._datetime_text(now_dt)),
            )
            claim_id = int(cursor.lastrowid)
            for grant_row in bounded:
                conn.execute(
                    "INSERT INTO attempt_allocations(claim_id, grant_id) VALUES (?, ?)",
                    (claim_id, grant_row["grant_id"]),
                )
            result = {
                "claim_id": claim_id,
                "grant_id": grant_id,
                "operation_id": operation_id,
                "created_at": self._datetime_text(now_dt),
            }
            result = self._record_idempotency(conn, idempotency_key, "ATTEMPT", fingerprint, result)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
