from __future__ import annotations

from collections.abc import Mapping

ALLOWED_FIELDS = {
    "artifact_type",
    "present",
    "runtime_version",
    "pak_state",
    "available_browser_operations",
}
PAK_STATES = {"OFF", "MANUAL", "AUTO"}


def validate_sbc_runtime_context(value: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["context must be an object"]

    extra = sorted(set(value) - ALLOWED_FIELDS)
    if extra:
        errors.append(f"unexpected fields: {extra}")

    if value.get("artifact_type") != "SBC_RUNTIME_CONTEXT":
        errors.append("artifact_type must be SBC_RUNTIME_CONTEXT")
    if value.get("present") is not True:
        errors.append("present must be true")

    version = value.get("runtime_version")
    if not isinstance(version, str) or not version.strip():
        errors.append("runtime_version must be a non-empty string")

    if value.get("pak_state") not in PAK_STATES:
        errors.append("pak_state is invalid")

    operations = value.get("available_browser_operations")
    if not isinstance(operations, list):
        errors.append("available_browser_operations must be a list")
    else:
        if any(not isinstance(item, str) or not item.strip() for item in operations):
            errors.append("available_browser_operations must contain non-empty strings")
        elif len(set(operations)) != len(operations):
            errors.append("available_browser_operations must be unique")

    return errors


def resolve_bootstrap_runtime_mode(
    value: Mapping[str, object] | None,
) -> tuple[str, list[str]]:
    if value is None:
        return "ORDINARY_CHAT", []
    errors = validate_sbc_runtime_context(value)
    if errors:
        return "INVALID_CONTEXT", errors
    return "SBC_BROWSER", []
