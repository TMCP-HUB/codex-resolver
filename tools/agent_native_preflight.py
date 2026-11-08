#!/usr/bin/env python3
"""Bounded Git checkout identity observation for agent-native Resolver execution.

The output proves only local checkout equality to caller-supplied exact revisions.
It never advertises a live provider capability, remote freshness, or assignment
admissibility. Obtain the expected SHAs from the authoritative remote first.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    if result.returncode:
        raise ValueError("git " + " ".join(args) + ": " + (result.stderr.strip() or "failed"))
    return result.stdout.strip()


def _checkout(root: str | Path, expected_sha: str, expected_branch: str | None) -> tuple[dict[str, Any], list[str]]:
    path = Path(root).expanduser().resolve()
    observation: dict[str, Any] = {"path": str(path)}
    errors: list[str] = []
    if not _SHA.fullmatch(expected_sha):
        return observation, ["EXPECTED_SHA_MUST_BE_FULL"]
    if not path.is_dir():
        return observation, ["CHECKOUT_PATH_MISSING"]
    try:
        toplevel = Path(_git(path, "rev-parse", "--show-toplevel")).resolve()
        if toplevel != path:
            errors.append("NOT_GIT_TOPLEVEL")
        observation["head_sha"] = _git(path, "rev-parse", "HEAD").lower()
        observation["branch"] = _git(path, "branch", "--show-current") or "DETACHED"
        observation["dirty"] = bool(_git(path, "status", "--porcelain", "--untracked-files=normal"))
        observation["origin"] = _git(path, "remote", "get-url", "origin")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        errors.append("GIT_CHECKOUT_UNOBSERVABLE")
        return observation, errors
    if observation["head_sha"] != expected_sha:
        errors.append("HEAD_SHA_MISMATCH")
    if expected_branch is not None and observation["branch"] != expected_branch:
        errors.append("BRANCH_MISMATCH")
    if observation["dirty"]:
        errors.append("DIRTY_CHECKOUT")
    return observation, errors


def observe(
    target: str | Path,
    resolver: str | Path,
    target_sha: str,
    resolver_sha: str,
    target_branch: str | None = None,
) -> dict[str, Any]:
    """Observe two selected checkouts; never fetch or mutate either repository."""
    target_data, target_errors = _checkout(target, target_sha, target_branch)
    resolver_data, resolver_errors = _checkout(resolver, resolver_sha, None)
    errors = (["TARGET_" + e for e in target_errors] +
              ["RESOLVER_" + e for e in resolver_errors])
    if target_data["path"] == resolver_data["path"]:
        errors.append("TARGET_AND_RESOLVER_MUST_BE_DISTINCT")
    return {
        "kind": "AGENT_NATIVE_LOCAL_CHECKOUT_OBSERVATION",
        "status": "LOCAL_STATE_MATCH" if not errors else "NOT_PROVEN",
        "target": target_data,
        "resolver": resolver_data,
        "errors": errors,
        "limitations": [
            "REMOTE_HEAD_FRESHNESS_NOT_PROVEN",
            "REMOTE_REPOSITORY_IDENTITY_NOT_PROVEN",
            "EXECUTION_SURFACE_CAPABILITIES_NOT_PROVEN",
            "ASSIGNMENT_AUTHORITY_NOT_PROVEN",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Local target repository root")
    parser.add_argument("--resolver", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--target-sha", required=True, help="Exact remotely confirmed target HEAD")
    parser.add_argument("--resolver-sha", required=True, help="Exact remotely confirmed Resolver HEAD")
    parser.add_argument("--target-branch", default=None, help="Expected checked-out target branch")
    args = parser.parse_args()
    result = observe(args.target, args.resolver, args.target_sha.lower(), args.resolver_sha.lower(), args.target_branch)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "LOCAL_STATE_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
