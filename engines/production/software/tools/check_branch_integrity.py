#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

REQUIRED_LABELS = [
    "Current branch:",
    "Target branch:",
    "Base SHA:",
    "Merge base SHA:",
    "Working HEAD:",
    "Intended HEAD:",
    "PR HEAD:",
    "Reviewed HEAD:",
    "Tested HEAD:",
    "Target HEAD at last integration check:",
    "Risk level:",
]

IDENTITY_LABELS = [
    "Base SHA:",
    "Merge base SHA:",
    "Working HEAD:",
    "Intended HEAD:",
    "PR HEAD:",
    "Reviewed HEAD:",
    "Tested HEAD:",
    "Target HEAD at last integration check:",
]


def find_branch_state_file(root: Path) -> Path | None:
    direct = root / "BRANCH_STATE.md"
    if direct.exists():
        return direct

    candidate = root / "templates" / "BRANCH_STATE.md"
    if candidate.exists():
        return candidate

    return None


def _field_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^[ \t]*-?[ \t]*{re.escape(label)}[ \t]*(.*)$", text)
    return None if match is None else match.group(1).strip()


def validate_branch_state_text(text: str) -> list[str]:
    errors: list[str] = []

    for label in REQUIRED_LABELS:
        if _field_value(text, label) is None:
            errors.append(f"missing required label: {label}")

    for label in REQUIRED_LABELS:
        value = _field_value(text, label)
        if value is not None and not value:
            kind = "identity" if label in IDENTITY_LABELS else "field"
            errors.append(f"blank required {kind}: {label}")

    return errors


def main() -> int:
    root = Path.cwd()
    path = find_branch_state_file(root)
    if path is None:
        print("No BRANCH_STATE.md found in current directory or templates/.")
        return 1

    errors = validate_branch_state_text(path.read_text(encoding="utf-8"))
    if errors:
        print(f"Branch state file failed integrity checks in {path}:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Branch state file {path} passed basic integrity checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
