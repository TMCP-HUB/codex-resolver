import json
from pathlib import Path
import unittest

from tools.bootstrap_runtime import resolve_bootstrap_runtime_mode, validate_sbc_runtime_context

ROOT = Path(__file__).resolve().parents[1]


def valid_context() -> dict[str, object]:
    return {
        "artifact_type": "SBC_RUNTIME_CONTEXT",
        "present": True,
        "runtime_version": "0.1",
        "pak_state": "OFF",
        "available_browser_operations": [],
    }


class SbcRuntimeContextTest(unittest.TestCase):
    def test_absent_context_is_ordinary_chat(self) -> None:
        self.assertEqual(resolve_bootstrap_runtime_mode(None), ("ORDINARY_CHAT", []))

    def test_valid_explicit_context_is_sbc_browser(self) -> None:
        for state in ["OFF", "MANUAL", "AUTO"]:
            value = valid_context()
            value["pak_state"] = state
            self.assertEqual(validate_sbc_runtime_context(value), [])
            self.assertEqual(resolve_bootstrap_runtime_mode(value), ("SBC_BROWSER", []))

    def test_malformed_explicit_context_fails_closed(self) -> None:
        cases: list[dict[str, object]] = []
        value = valid_context(); value["present"] = False; cases.append(value)
        value = valid_context(); value["runtime_version"] = " "; cases.append(value)
        value = valid_context(); value["pak_state"] = "UNKNOWN"; cases.append(value)
        value = valid_context(); value["available_browser_operations"] = ["click", "click"]; cases.append(value)
        value = valid_context(); value["available_browser_operations"] = [3]; cases.append(value)
        value = valid_context(); value["provider_id"] = "openai"; cases.append(value)
        value = valid_context(); value["authority"] = "OWNER"; cases.append(value)
        value = valid_context(); value["browser_tab_id"] = "tab-1"; cases.append(value)

        for value in cases:
            with self.subTest(value=value):
                mode, errors = resolve_bootstrap_runtime_mode(value)
                self.assertEqual(mode, "INVALID_CONTEXT")
                self.assertTrue(errors)

    def test_unknown_operation_names_are_opaque_observations(self) -> None:
        value = valid_context()
        value["available_browser_operations"] = ["provider_future_op"]
        self.assertEqual(validate_sbc_runtime_context(value), [])
        self.assertEqual(resolve_bootstrap_runtime_mode(value)[0], "SBC_BROWSER")

    def test_schema_is_closed_and_does_not_encode_provider_or_authority(self) -> None:
        schema = json.loads((ROOT / "schemas/sbc-runtime-context.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {"artifact_type", "present", "runtime_version", "pak_state", "available_browser_operations"},
        )
        serialized = json.dumps(schema).lower()
        for forbidden in ["provider_id", "browser_tab_id", "conversation_id", "authority", "capability_profile"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
