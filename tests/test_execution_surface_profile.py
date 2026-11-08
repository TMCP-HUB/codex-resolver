from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tests.test_executability import governed_chain, valid_chain, validate_chain
from tests.test_executability_parity import schema_accepts
from tests.test_resolver_spawn import bundle as spawn_bundle
from tests.test_resolver_transition import artifact, transition_bundle
from tools.executability import (
    evaluate_assignment_admissibility,
    validate_admissibility_against_profile,
    validate_capability_profile,
)
from tools.resolver_spawn import resolve_spawn
from tools.resolver_transition import resolve_transition


ROOT = Path(__file__).resolve().parents[1]


def _resolver(profile: dict[str, object]):
    evidence = profile["evidence_artifacts"][0]
    return lambda ref: evidence if ref == evidence["artifact_id"] else None


def _surface(
    surface_class: str,
    *,
    capabilities: list[str],
    evidence_channels: list[str],
    readiness: str = "READY",
    workspace_scope_ref: str = "ext-scope:runtime:0184",
) -> tuple[dict[str, object], object]:
    _, _, profile = deepcopy(valid_chain())
    profile["surface_class"] = surface_class
    profile["workspace_scope_ref"] = workspace_scope_ref
    profile["readiness"] = readiness
    profile["evidence_channels"] = list(evidence_channels)
    profile["available_capabilities"] = list(capabilities)
    profile["unavailable_capabilities"] = []
    evidence = profile["evidence_artifacts"][0]
    evidence["capabilities"] = list(capabilities)
    profile["capability_evidence"] = [
        {"capability": capability, "evidence_ref": evidence["artifact_id"]}
        for capability in capabilities
    ]
    return profile, _resolver(profile)


class ExecutionSurfaceProfileTest(unittest.TestCase):
    def test_reference_surface_advertisements_are_provider_neutral_and_valid(self) -> None:
        cases = [
            (
                "CHATGPT_CHAT",
                ["connector:document_store", "repository_remote_read"],
                ["connector_result", "chat_completion"],
            ),
            (
                "REMOTE_DEV_ENV",
                ["repository_remote_read", "shell", "python_runtime"],
                ["terminal_stdout", "unit_test_result"],
            ),
            (
                "REMOTE_CODE_EXECUTOR",
                ["repository_local_checkout", "shell", "python_runtime"],
                ["terminal_stdout", "unit_test_result", "durable_artifact_ref"],
            ),
            (
                "BROWSER_CONSOLE",
                ["interactive_browser", "provider_log_read"],
                ["deployment_status", "durable_artifact_ref"],
            ),
        ]
        for surface_class, capabilities, channels in cases:
            with self.subTest(surface_class=surface_class):
                profile, resolver = _surface(
                    surface_class,
                    capabilities=capabilities,
                    evidence_channels=channels,
                )
                self.assertEqual(validate_capability_profile(profile, resolver), [])
                self.assertEqual(profile["readiness"], "READY")
                self.assertTrue(profile["workspace_scope_ref"].startswith("ext-scope:"))
                for forbidden in ["provider_id", "resource_id", "connector_id", "surface_id", "browser_tab_id", "conversation_id"]:
                    self.assertNotIn(forbidden, profile)

    def test_new_profile_shape_has_schema_runtime_parity(self) -> None:
        schema = json.loads((ROOT / "schemas/capability-profile.schema.json").read_text(encoding="utf-8"))
        _, _, profile = deepcopy(valid_chain())
        resolver = _resolver(profile)
        self.assertTrue(schema_accepts(profile, schema))
        self.assertEqual(validate_capability_profile(profile, resolver), [])

        candidates: list[dict[str, object]] = []
        for field in ["surface_class", "workspace_scope_ref", "readiness", "evidence_channels"]:
            candidate = deepcopy(profile)
            del candidate[field]
            candidates.append(candidate)
        bad_class = deepcopy(profile); bad_class["surface_class"] = ""; candidates.append(bad_class)
        bad_scope = deepcopy(profile); bad_scope["workspace_scope_ref"] = ""; candidates.append(bad_scope)
        bad_readiness = deepcopy(profile); bad_readiness["readiness"] = "UNKNOWN"; candidates.append(bad_readiness)
        no_channels = deepcopy(profile); no_channels["evidence_channels"] = []; candidates.append(no_channels)
        duplicate_channels = deepcopy(profile); duplicate_channels["evidence_channels"] = ["terminal_stdout", "terminal_stdout"]; candidates.append(duplicate_channels)

        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.assertFalse(schema_accepts(candidate, schema))
                self.assertTrue(validate_capability_profile(candidate, _resolver(candidate)))

    def test_unhashable_readiness_fails_closed_in_validator_and_schema(self) -> None:
        schema = json.loads((ROOT / "schemas/capability-profile.schema.json").read_text(encoding="utf-8"))
        for readiness in [[], {}]:
            with self.subTest(readiness=readiness):
                _, _, profile = deepcopy(valid_chain())
                profile["readiness"] = readiness
                errors = validate_capability_profile(profile, _resolver(profile))
                self.assertIn("readiness is invalid", errors)
                self.assertFalse(schema_accepts(profile, schema))

    def test_workspace_scope_and_exact_profile_binding_remain_deterministic(self) -> None:
        _, record, profile = deepcopy(valid_chain())
        resolver = _resolver(profile)
        self.assertEqual(profile["workspace_scope_ref"], "ext-scope:runtime:test")
        self.assertEqual(validate_admissibility_against_profile(record, profile, resolver), [])

        wrong = deepcopy(profile)
        wrong["artifact_id"] = "CAP-OTHER"
        errors = validate_admissibility_against_profile(record, wrong, _resolver(wrong))
        self.assertTrue(any("capability_profile_ref mismatch" in error for error in errors), errors)
        self.assertEqual(wrong["workspace_scope_ref"], profile["workspace_scope_ref"])

    def test_read_and_mutation_capabilities_are_exact_non_authorizing_facts(self) -> None:
        available = ["repository_remote_read", "ci_read", "provider_log_read"]
        for required in ["repository_remote_write", "ci_trigger", "production_mutation"]:
            with self.subTest(required=required):
                result = evaluate_assignment_admissibility([required], available)
                self.assertEqual(result["status"], "NOT_ADMISSIBLE")
                self.assertEqual(result["unsatisfied_required_capabilities"], [required])

        profile, resolver = _surface(
            "REMOTE_DEV_ENV",
            capabilities=available,
            evidence_channels=["terminal_stdout"],
        )
        self.assertEqual(validate_capability_profile(profile, resolver), [])
        for mutation in ["repository_remote_write", "ci_trigger", "production_mutation"]:
            self.assertNotIn(mutation, profile["available_capabilities"])

    def test_evidence_channels_do_not_replace_capability_evidence_authority(self) -> None:
        profile, resolver = _surface(
            "REMOTE_DEV_ENV",
            capabilities=["shell"],
            evidence_channels=["terminal_stdout", "unit_test_result"],
        )
        self.assertEqual(validate_capability_profile(profile, resolver), [])
        profile["capability_evidence"] = []
        errors = validate_capability_profile(profile, resolver)
        self.assertTrue(any("missing evidence" in error for error in errors), errors)
        self.assertEqual(profile["evidence_channels"], ["terminal_stdout", "unit_test_result"])

    def test_usable_readiness_strings_remain_admissible(self) -> None:
        for readiness in ["READY", "DEGRADED"]:
            with self.subTest(readiness=readiness):
                _, record, profile = deepcopy(valid_chain())
                profile["readiness"] = readiness
                resolver = _resolver(profile)
                self.assertEqual(validate_capability_profile(profile, resolver), [])
                self.assertEqual(validate_admissibility_against_profile(record, profile, resolver), [])

                value = spawn_bundle()
                cited = next(item for item in value["artifacts"] if item.get("artifact_type") == "CAPABILITY_PROFILE")
                cited["readiness"] = readiness
                result = resolve_spawn(value)
                self.assertEqual(result.get("status"), "SPAWN_READY", result)

    def test_nonusable_readiness_is_structurally_valid_but_cannot_admit(self) -> None:
        for readiness in ["PROVISIONING_REQUIRED", "AUTH_REQUIRED", "UNAVAILABLE"]:
            with self.subTest(readiness=readiness):
                _, record, profile = deepcopy(valid_chain())
                profile["readiness"] = readiness
                resolver = _resolver(profile)
                self.assertEqual(validate_capability_profile(profile, resolver), [])
                errors = validate_admissibility_against_profile(record, profile, resolver)
                self.assertTrue(any("readiness does not permit current execution" in error for error in errors), errors)

                value = spawn_bundle()
                cited = next(item for item in value["artifacts"] if item.get("artifact_type") == "CAPABILITY_PROFILE")
                cited["readiness"] = readiness
                result = resolve_spawn(value)
                self.assertNotEqual(result.get("status"), "SPAWN_READY", result)
                self.assertNotIn("assignment", result)

    def test_spawn_rejects_unhashable_readiness_without_raising(self) -> None:
        for readiness in [[], {}]:
            with self.subTest(readiness=readiness):
                value = spawn_bundle()
                cited = next(item for item in value["artifacts"] if item.get("artifact_type") == "CAPABILITY_PROFILE")
                cited["readiness"] = readiness
                result = resolve_spawn(value)
                self.assertEqual(
                    (result.get("control_state"), result.get("reason")),
                    ("ESCALATE", "MALFORMED_CAPABILITY_PROFILE"),
                    result,
                )
                self.assertNotEqual(result.get("status"), "SPAWN_READY", result)
                self.assertNotIn("assignment", result)

    def test_ready_profile_preserves_spawn_and_complete_chain_happy_paths(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        self.assertEqual(profile["readiness"], "READY")
        self.assertEqual(validate_chain(assignment, record, profile), [])
        spawned = resolve_spawn(spawn_bundle())
        self.assertEqual(spawned.get("status"), "SPAWN_READY", spawned)

    def test_stale_capability_evidence_still_fails_closed(self) -> None:
        _, _, profile = deepcopy(valid_chain())
        evidence = profile["evidence_artifacts"][0]
        evidence["valid_until"] = "2026-01-01T00:00:01Z"
        errors = validate_capability_profile(profile, _resolver(profile))
        self.assertTrue(any("expired" in error for error in errors), errors)

    def test_exact_route_assignment_profile_binding_survives_extension(self) -> None:
        assignment, record, profile = deepcopy(valid_chain())
        resolver, route = governed_chain(assignment, record, profile)
        self.assertEqual(route["segments"][1]["capability_profile_ref"], profile["artifact_id"])
        self.assertEqual(assignment["execution_contract"]["capability_profile_ref"], profile["artifact_id"])
        self.assertEqual(record["capability_profile_ref"], profile["artifact_id"])
        self.assertEqual(validate_chain(assignment, record, profile), [])
        self.assertNotIn("surface_class", route["segments"][1])
        self.assertNotIn("workspace_scope_ref", route["segments"][1])
        self.assertEqual(validate_capability_profile(profile, resolver), [])

    def test_provider_resource_and_connector_names_are_not_universal_surface_identifiers(self) -> None:
        profile, resolver = _surface(
            "REMOTE_DEV_ENV",
            capabilities=["shell", "connector:repo_adapter"],
            evidence_channels=["connector_result", "terminal_stdout"],
            workspace_scope_ref="ext-scope:runtime:provider-opaque",
        )
        self.assertEqual(validate_capability_profile(profile, resolver), [])
        self.assertEqual(profile["surface_class"], "REMOTE_DEV_ENV")
        self.assertIn("connector:repo_adapter", profile["available_capabilities"])
        self.assertNotEqual(profile["surface_class"], "connector:repo_adapter")
        self.assertFalse(any(key in profile for key in ["github_repository", "google_drive_resource", "provider_account"] ))

    def test_transition_revalidation_rejects_nonusable_current_profile(self) -> None:
        for readiness in ["PROVISIONING_REQUIRED", "AUTH_REQUIRED", "UNAVAILABLE"]:
            with self.subTest(readiness=readiness):
                value = transition_bundle()
                old = artifact(value, value["spawned"]["capability_profile_ref"])
                profile = deepcopy(old)
                profile["artifact_id"] = f"PROFILE-NOW-{readiness}"
                profile["readiness"] = readiness
                evidence = deepcopy(profile["evidence_artifacts"][0])
                evidence["artifact_id"] = f"EVIDENCE-NOW-{readiness}"
                profile["evidence_artifacts"] = [evidence]
                profile["related_artifacts"] = [evidence["artifact_id"]]
                for claim in profile["capability_evidence"]:
                    claim["evidence_ref"] = evidence["artifact_id"]
                value["artifacts"].extend([profile, evidence])
                value["refs"]["current_capability_profile_ref"] = profile["artifact_id"]
                artifact(value, "DIRECTOR-POST")["transition_authority"]["requires_current_executability"] = True
                result = resolve_transition(value)
                self.assertEqual(
                    (result.get("control_state"), result.get("reason")),
                    ("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED"),
                    result,
                )

    def test_transition_revalidation_rejects_unhashable_readiness_without_raising(self) -> None:
        for readiness in [[], {}]:
            with self.subTest(readiness=readiness):
                value = transition_bundle()
                old = artifact(value, value["spawned"]["capability_profile_ref"])
                profile = deepcopy(old)
                profile["artifact_id"] = "PROFILE-NOW-MALFORMED"
                profile["readiness"] = readiness
                evidence = deepcopy(profile["evidence_artifacts"][0])
                evidence["artifact_id"] = "EVIDENCE-NOW-MALFORMED"
                profile["evidence_artifacts"] = [evidence]
                profile["related_artifacts"] = [evidence["artifact_id"]]
                for claim in profile["capability_evidence"]:
                    claim["evidence_ref"] = evidence["artifact_id"]
                value["artifacts"].extend([profile, evidence])
                value["refs"]["current_capability_profile_ref"] = profile["artifact_id"]
                artifact(value, "DIRECTOR-POST")["transition_authority"]["requires_current_executability"] = True
                result = resolve_transition(value)
                self.assertEqual(
                    (result.get("control_state"), result.get("reason")),
                    ("WAIT", "CURRENT_EXECUTABILITY_REVALIDATION_REQUIRED"),
                    result,
                )


if __name__ == "__main__":
    unittest.main()