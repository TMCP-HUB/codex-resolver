"""GitHub candidate readback at the existing Software/Control handoff boundary.

No network client, provider session, scheduler, ticket, or second durable artifact
ontology is introduced. The Control side supplies a *fresh independent GitHub
reader*, never the Executor's self-report as remote evidence.

The explicit Assignment delivery declaration controls applicability. Manual Stage 1
checks reported delivery against GitHub; it does not authenticate the internal
Control bundle against arbitrary coordinated edits.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import re

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
Reader = Callable[[str, str, str | int], Mapping[str, object] | None]


def _result(status: str, reason: str, **details: object) -> dict[str, object]:
    return {"status": status, "reason": reason, **details}


def validate_delivery_requirement(requirement: object) -> list[str]:
    if not isinstance(requirement, Mapping):
        return ["github_candidate_delivery must be an object"]
    expected = {"repository", "base_branch", "allowed_kinds"}
    if set(requirement) != expected:
        return ["github_candidate_delivery has unexpected or missing fields"]
    if not isinstance(requirement.get("repository"), str) or not _REPO.fullmatch(requirement["repository"]):
        return ["github_candidate_delivery.repository must be owner/repo"]
    if not isinstance(requirement.get("base_branch"), str) or not requirement["base_branch"].strip():
        return ["github_candidate_delivery.base_branch must be nonblank"]
    kinds = requirement.get("allowed_kinds")
    if (not isinstance(kinds, list) or not kinds
            or any(not isinstance(k, str) or k not in {"PULL_REQUEST", "BRANCH"} for k in kinds)
            or len(kinds) != len(set(kinds))):
        return ["github_candidate_delivery.allowed_kinds must be unique PULL_REQUEST/BRANCH"]
    return []


def check_github_candidate(
    assignment: Mapping[str, object],
    executor_result: Mapping[str, object],
    reader: Reader | None,
) -> dict[str, object]:
    """Read actual candidate from GitHub through the Control-supplied reader.

    It does not grant authority to publish, does not validate application claims,
    and does not replace the generic durable output/readback contract.
    """
    requirement = assignment.get("github_candidate_delivery")
    if requirement is None:
        return _result("NOT_REQUIRED", "NO_GITHUB_CANDIDATE_REQUIREMENT")
    errors = validate_delivery_requirement(requirement)
    if errors:
        return _result("INVALID", "MALFORMED_GITHUB_CANDIDATE_REQUIREMENT", errors=errors)
    assert isinstance(requirement, Mapping)
    assignment_id = assignment.get("assignment_id")
    if not isinstance(assignment_id, str) or not assignment_id.strip():
        return _result("INVALID", "ASSIGNMENT_ID_MISSING")
    if executor_result.get("assignment_id") != assignment_id:
        return _result("INVALID", "CANDIDATE_ASSIGNMENT_ID_MISMATCH")
    candidate = executor_result.get("published_candidate")
    if not isinstance(candidate, Mapping):
        return _result("NOT_PROVEN", "GITHUB_CANDIDATE_NOT_PUBLISHED")
    expected = {"kind", "repository", "ref", "head_sha"}
    if set(candidate) != expected:
        return _result("INVALID", "MALFORMED_GITHUB_CANDIDATE_REFERENCE")
    kind, repository, reference, head_sha = (candidate[key] for key in ("kind", "repository", "ref", "head_sha"))
    if kind not in requirement["allowed_kinds"] or repository != requirement["repository"]:
        return _result("INVALID", "GITHUB_CANDIDATE_SCOPE_MISMATCH")
    if not isinstance(head_sha, str) or not _SHA.fullmatch(head_sha):
        return _result("INVALID", "GITHUB_CANDIDATE_SHA_INVALID")
    if kind == "PULL_REQUEST":
        if isinstance(reference, bool) or not isinstance(reference, int) or reference < 1:
            return _result("INVALID", "GITHUB_PR_NUMBER_INVALID")
    elif not isinstance(reference, str) or not reference.startswith(f"resolver/{assignment_id}/") or len(reference) <= len(f"resolver/{assignment_id}/"):
        return _result("INVALID", "GITHUB_BRANCH_ASSIGNMENT_ID_MISMATCH")
    if reader is None:
        return _result("NOT_PROVEN", "INDEPENDENT_GITHUB_READBACK_UNAVAILABLE")
    try:
        observed = reader(kind, repository, reference)
    except Exception:
        return _result("NOT_PROVEN", "GITHUB_READBACK_FAILED")
    if not isinstance(observed, Mapping):
        return _result("NOT_PROVEN", "GITHUB_CANDIDATE_UNRESOLVED")
    if kind == "PULL_REQUEST":
        base = observed.get("base")
        head = observed.get("head")
        if not isinstance(base, Mapping) or not isinstance(head, Mapping):
            return _result("NOT_PROVEN", "GITHUB_PR_IDENTITY_UNRESOLVED")
        base_repo = base.get("repo")
        head_repo = head.get("repo")
        if not isinstance(base_repo, Mapping) or not isinstance(head_repo, Mapping):
            return _result("NOT_PROVEN", "GITHUB_PR_REPOSITORY_UNRESOLVED")
        if (observed.get("number") != reference
            or base_repo.get("full_name") != repository
            or head_repo.get("full_name") != repository
            or base.get("ref") != requirement["base_branch"]
            or head.get("sha") != head_sha):
            return _result("NOT_PROVEN", "GITHUB_PR_EXACT_CANDIDATE_MISMATCH")
        if observed.get("merged") is True:
            # A merged PR does not prove who merged it. Control reconciles promotion authority.
            return _result("NOT_PROVEN", "GITHUB_PR_MERGED_REQUIRES_PROMOTION_RECONCILIATION")
        if (observed.get("state") != "open" or observed.get("merged") is not False
                or not isinstance(observed.get("draft"), bool)):
            return _result("NOT_PROVEN", "GITHUB_PR_NOT_OPEN_FOR_VERIFICATION")
        body = observed.get("body")
        marker = f"Resolver-Assignment: {assignment_id}"
        if not isinstance(body, str) or marker not in body.splitlines():
            return _result("NOT_PROVEN", "GITHUB_PR_ASSIGNMENT_MARKER_MISSING")
    else:
        commit = observed.get("commit")
        if (observed.get("name") != reference or not isinstance(commit, Mapping)
            or commit.get("sha") != head_sha):
            return _result("NOT_PROVEN", "GITHUB_BRANCH_EXACT_CANDIDATE_MISMATCH")
        if reference == requirement["base_branch"]:
            return _result("INVALID", "GITHUB_BRANCH_MUST_NOT_BE_BASE")
    return _result("PROVEN", "GITHUB_CANDIDATE_READBACK_PROVEN",
                   repository=repository, kind=kind, ref=reference, head_sha=head_sha)
