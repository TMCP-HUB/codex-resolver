#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_TEMPLATE_FILES = [
    "templates/BRANCH_STATE.md",
    "templates/HANDOFF.md",
    "templates/PROJECT_CHRONICLE.md",
    "templates/TASK_EVIDENCE.md",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing: list[str] = []

    for rel in REQUIRED_TEMPLATE_FILES:
        path = root / rel
        if not path.exists():
            missing.append(rel)

    if missing:
        print("Missing required playbook files:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Playbook state looks structurally complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
