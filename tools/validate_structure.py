#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]

ROOT_REQUIRED = [
    "AGENTS.md",
    "README.md",
    "SYSTEM_MANIFEST.yaml",
    "ROUTER.md",
    "BOOTSTRAP.md",
    "ARCHITECTURE_MIGRATION_MAP.md",
    "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
    "contracts/EXECUTABILITY_CONTRACT.md",
    "contracts/ASSIGNMENT_COMPILATION_CONTRACT.md",
    "contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md",
    "schemas/compiled-assignment.schema.json",
    "schemas/execution-envelope.schema.json",
    "schemas/state-observation.schema.json",
    "schemas/sbc-runtime-context.schema.json",
    "tools/assignment_compiler.py",
    "tools/executability.py",
    "tools/bootstrap_runtime.py",
    "engines/foundation/MANIFEST.yaml",
    "engines/foundation/workflows/form-project-foundation.md",
    "engines/foundation/schemas/project-seed.schema.json",
    "engines/foundation/schemas/project-outcome.schema.json",
    "engines/foundation/schemas/consequential-unknown-map.schema.json",
    "engines/foundation/schemas/topology-plan.schema.json",
    "engines/foundation/schemas/topology-bootstrap.schema.json",
    "engines/foundation/skills/plan-project-topology/SKILL.md",
    "tools/project_topology.py",
]

ROLE_REQUIRED_SECTIONS = [
    "## PURPOSE",
    "## RESPONSIBILITY",
    "## AUTHORITY",
    "## DOES_NOT_OWN",
    "## CONTEXT CONTRACT",
    "## REQUIRED INPUTS",
    "## OPTIONAL INPUTS",
    "## FORBIDDEN / UNNECESSARY CONTEXT",
    "## PROCEDURE",
    "## ARTIFACT POLICY",
    "## OUTPUTS",
    "## HANDOFF",
    "## STOP / ESCALATION",
    "## FAILURE MODES",
]

ACTIVE_SKILL_NAMESPACES = [
    ROOT / "kernel/skills",
    ROOT / "protocols/skills",
    ROOT / "engines/verification/skills",
    ROOT / "engines/production/software/skills",
    ROOT / "engines/production/software/patterns",
    ROOT / "engines/foundation/skills",
    ROOT / "library/skills",
]

RESEARCH_ENFORCEMENT_SURFACES = [
    "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
    "engines/research/MANIFEST.yaml",
    "engines/research/RESEARCH_CONTROL_CONTRACT.md",
    "engines/research/ROLES.md",
    "engines/research/workflows/default-machine-research.md",
    "engines/research/bootstrap/DEFAULT_MACHINE_ONLY_BOOTSTRAP.yaml",
    "engines/research/templates/research-question.yaml",
    "engines/research/templates/research-work-package.yaml",
    "engines/research/templates/machine-experiment.yaml",
    "schemas/research-question.schema.json",
    "schemas/research-work-package.schema.json",
    "schemas/research-source.schema.json",
    "schemas/machine-experiment.schema.json",
    "schemas/research-method-freeze.schema.json",
    "schemas/human-research-authorization.schema.json",
    "schemas/owner-decision-record.schema.json",
    "tools/research_policy.py",
    "tools/validate_structure.py",
    "tests/test_research_machine_only.py",
    "tests/test_structure.py",
]

EXECUTABILITY_ENFORCEMENT_SURFACES = [
    "contracts/ASSIGNMENT_COMPILATION_CONTRACT.md",
    "contracts/EXECUTABILITY_CONTRACT.md",
    "schemas/compiled-assignment.schema.json",
    "schemas/execution-envelope.schema.json",
    "schemas/capability-profile.schema.json",
    "schemas/assignment-admissibility.schema.json",
    "schemas/assignment.schema.json",
    "schemas/state-observation.schema.json",
    "tools/executability.py",
    "tools/assignment_compiler.py",
    "tests/test_assignment_compiler.py",
    "tests/test_executability.py",
    "tests/test_executability_structure.py",
    "roles/control-director/ROLE.md",
    "roles/executor/ROLE.md",
    "roles/control-verifier/ROLE.md",
    "library/skills/skill-authoring/SKILL.md",
    "library/templates/SKILL_TEMPLATE.md",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def manifest_path_values(text: str) -> set[str]:
    # Extract repository-relative md/yaml/json/py paths from simple manifests.
    return set(re.findall(r"(?:^|\s)([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|yaml|json|py))\s*$", text, flags=re.MULTILINE))


def _load_schema(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def validate_research_machine_only_gate(
    root: Path = ROOT,
    regression_runner: Callable[[], list[str]] | None = None,
) -> list[str]:
    """Normal bounded Research gate: active-surface lint + deterministic policy regressions."""
    errors: list[str] = []
    try:
        import sys
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from tools.research_policy import lint_active_repository, run_machine_only_regressions

        for err in lint_active_repository(root):
            fail(errors, f"research machine-only policy: {err}")
        runner = regression_runner or run_machine_only_regressions
        for err in runner():
            fail(errors, f"research machine-only regression: {err}")
    except Exception as exc:
        fail(errors, f"research machine-only policy/regression validator unavailable: {exc}")
    return errors


def validate_executability_gate(root: Path = ROOT) -> list[str]:
    """Structural and deterministic gate for destination executability admission."""
    errors: list[str] = []

    for rel in EXECUTABILITY_ENFORCEMENT_SURFACES:
        if not (root / rel).is_file():
            fail(errors, f"missing executability enforcement surface: {rel}")

    try:
        assignment = _load_schema(root, "schemas/assignment.schema.json")
        if "execution_contract" not in assignment.get("required", []):
            fail(errors, "ASSIGNMENT schema does not require execution_contract")
        execution_contract = assignment.get("properties", {}).get("execution_contract", {})
        required = set(execution_contract.get("required", []))
        for field in {
            "destination_id",
            "compiled_assignment_ref",
            "capability_profile_ref",
            "admissibility_ref",
            "proof_status",
            "required_capabilities",
            "unsatisfied_required_capabilities",
            "mandatory_evidence_paths",
            "execution_mode",
        }:
            if field not in required:
                fail(errors, f"ASSIGNMENT execution_contract missing required field: {field}")
        props = execution_contract.get("properties", {})
        if props.get("proof_status", {}).get("const") != "PROVEN":
            fail(errors, "ASSIGNMENT execution_contract does not require proof_status=PROVEN")
        if props.get("unsatisfied_required_capabilities", {}).get("maxItems") != 0:
            fail(errors, "ASSIGNMENT may contain unsatisfied required capabilities")

        admissibility = _load_schema(root, "schemas/assignment-admissibility.schema.json")
        if "compiled_assignment_ref" not in admissibility.get("required", []):
            fail(errors, "ASSIGNMENT_ADMISSIBILITY does not bind COMPILED_ASSIGNMENT")
        status_values = admissibility.get("properties", {}).get("status", {}).get("enum", [])
        if status_values != ["ADMISSIBLE", "NOT_ADMISSIBLE"]:
            fail(errors, "ASSIGNMENT_ADMISSIBILITY status contract drifted")
        compiled = _load_schema(root, "schemas/compiled-assignment.schema.json")
        if "authorized_claims" not in compiled.get("required", []) or "supported_execution_envelope_ref" not in compiled.get("required", []):
            fail(errors, "COMPILED_ASSIGNMENT lacks claim or execution-envelope authority binding")
        if "authorized_evidence_requirements" not in compiled.get("required", []):
            fail(errors, "COMPILED_ASSIGNMENT lacks first-class authorized evidence closure")
        envelope_schema = _load_schema(root, "schemas/execution-envelope.schema.json")
        if envelope_schema.get("properties", {}).get("artifact_type", {}).get("const") != "EXECUTION_ENVELOPE":
            fail(errors, "EXECUTION_ENVELOPE schema is not registered correctly")
        if compiled.get("properties", {}).get("authority_class", {}).get("enum") != [
            "FROZEN_CANDIDATE", "MOVING_PR", "MOVING_BRANCH", "POST_MERGE_STATE", "LIVE_REMOTE_STATE"
        ]:
            fail(errors, "COMPILED_ASSIGNMENT authority classes drifted")
        context_enum = compiled["properties"]["context_facts"]["items"]["properties"]["authority_source"]["enum"]
        if context_enum != ["PLATFORM_PROVIDED", "RESOLVER_BOUND", "EXECUTOR_RESOLVED", "REMOTE_LIVE"]:
            fail(errors, "COMPILED_ASSIGNMENT context authority classes drifted")
    except Exception as exc:
        fail(errors, f"executability schema validation unavailable: {exc}")

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    router = (root / "ROUTER.md").read_text(encoding="utf-8")
    director = (root / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
    for label, text in [("AGENTS", agents), ("Router", router), ("Control Director", director)]:
        if "ASSIGNMENT_NOT_ADMISSIBLE" not in text:
            fail(errors, f"{label} does not fail closed on non-admissible destination")
        if "REQUIRED_CAPABILITIES" not in text:
            fail(errors, f"{label} does not derive/compare required capabilities")
    if "NO ASSIGNMENT WITHOUT EXECUTABILITY PROOF" not in agents:
        fail(errors, "root agent rules are missing the executability kernel law")
    if "CAPABILITY_PROFILE" not in director or "ASSIGNMENT_ADMISSIBILITY" not in director:
        fail(errors, "Control Director does not materialize destination capability/admissibility control")
    if director.find("COMPILED_ASSIGNMENT") > director.find("destination executability preflight"):
        fail(errors, "Control Director does not compile before destination executability")
    if router.find("compile structured assignment semantics") > router.find("derive REQUIRED_CAPABILITIES"):
        fail(errors, "Router does not compile before capability derivation")
    forbidden_platform_names = ["CODEX_CLOUD", "ChatGPT", "Cloudflare", "Google Drive"]
    compiler_core = (root / "tools/assignment_compiler.py").read_text(encoding="utf-8") + json.dumps(compiled)
    for name in forbidden_platform_names:
        if name in compiler_core:
            fail(errors, f"platform-specific name entered compiler Core: {name}")

    system_manifest = (root / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
    if "destination_executability: contracts/EXECUTABILITY_CONTRACT.md" not in system_manifest:
        fail(errors, "system manifest does not register destination executability contract")
    if "assignment_compilation: contracts/ASSIGNMENT_COMPILATION_CONTRACT.md" not in system_manifest:
        fail(errors, "system manifest does not register assignment compilation contract")

    software_manifest = (root / "engines/production/software/MANIFEST.yaml").read_text(encoding="utf-8")
    verification_manifest = (root / "engines/verification/MANIFEST.yaml").read_text(encoding="utf-8")
    research_manifest = (root / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
    if "destination_executability_preflight_passes" not in software_manifest:
        fail(errors, "Software Engine does not require destination executability preflight")
    if "destination_executability_preflight_passes_for_mandatory_evidence" not in verification_manifest:
        fail(errors, "Verification Engine does not preflight mandatory evidence capabilities")
    if "method_level_machine_only_admission_not_destination_proof" not in research_manifest:
        fail(errors, "Research Engine still conflates machine-only admission with destination proof")

    authoring = (root / "library/skills/skill-authoring/SKILL.md").read_text(encoding="utf-8")
    skill_template = (root / "library/templates/SKILL_TEMPLATE.md").read_text(encoding="utf-8")
    if "Execution contract" not in authoring:
        fail(errors, "skill-authoring does not require an Execution contract")
    for marker in ["Required execution capabilities", "Supported execution modes", "ASSIGNMENT_NOT_ADMISSIBLE"]:
        if marker not in skill_template:
            fail(errors, f"skill template missing executability marker: {marker}")

    try:
        import sys
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from tools.executability import evaluate_assignment_admissibility

        admissible = evaluate_assignment_admissibility(
            ["repository_remote_read"],
            ["repository_remote_read", "connector:github"],
        )
        if admissible["status"] != "ADMISSIBLE" or admissible["unsatisfied_required_capabilities"]:
            fail(errors, "executability evaluator rejects a valid subset")
        impossible = evaluate_assignment_admissibility(
            ["repository_remote_read", "repository_local_checkout", "shell"],
            ["repository_remote_read", "connector:github"],
        )
        if impossible["status"] != "NOT_ADMISSIBLE":
            fail(errors, "executability evaluator accepts missing mandatory capabilities")
        if impossible["unsatisfied_required_capabilities"] != ["repository_local_checkout", "shell"]:
            fail(errors, "executability evaluator missing-set result drifted")
    except Exception as exc:
        fail(errors, f"executability evaluator unavailable: {exc}")

    return errors


def validate_software_skill_index(root: Path = ROOT) -> list[str]:
    """Compare procedural index entries with active Software skill directories."""
    errors: list[str] = []
    index = root / "engines/production/software/SKILLS_INDEX.md"
    skills = root / "engines/production/software/skills"
    if not index.is_file():
        return ["missing engine-local Software skill index"]
    text = index.read_text(encoding="utf-8")
    sections = re.findall(
        r"^## Software procedural skills\s*$([\s\S]*?)(?=^## |\Z)",
        text, flags=re.MULTILINE,
    )
    if len(sections) != 1:
        return ["Software index must contain exactly one procedural skills section"]
    entries = re.findall(r"^\s*-\s+`([a-z0-9][a-z0-9-]*)`\s*$", sections[0], flags=re.MULTILINE)
    actual = {p.parent.name for p in skills.glob("*/SKILL.md") if p.is_file()}
    listed = set(entries)
    for skill_id in sorted(actual - listed):
        fail(errors, f"Software index missing procedural skill: {skill_id}")
    for skill_id in sorted(listed - actual):
        fail(errors, f"Software index lists stale procedural skill: {skill_id}")
    for skill_id in sorted(listed):
        if entries.count(skill_id) > 1:
            fail(errors, f"Software index lists duplicate procedural skill: {skill_id}")
    return errors


def validate() -> list[str]:
    errors: list[str] = []

    for rel in ROOT_REQUIRED:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing root control file: {rel}")

    # Old global runtime discovery surfaces must be gone from the active root.
    for rel in [".agents", ".codex", "SKILLS_INDEX.md"]:
        if (ROOT / rel).exists():
            fail(errors, f"legacy ordinary runtime surface still active at root: {rel}")

    system_manifest = (ROOT / "SYSTEM_MANIFEST.yaml").read_text(encoding="utf-8")
    for rel in re.findall(r"manifest_path:\s*([^\s]+)", system_manifest):
        if not (ROOT / rel).is_file():
            fail(errors, f"root manifest references missing engine manifest: {rel}")

    for marker, message in [
        ("bootstrap_entry: BOOTSTRAP.md", "root manifest does not register Liaison bootstrap entry"),
        ("contract: contracts/SBC_RUNTIME_CONTEXT_CONTRACT.md", "root manifest does not register SBC runtime context contract"),
        ("schema: schemas/sbc-runtime-context.schema.json", "root manifest does not register SBC runtime context schema"),
        ("validator: tools/bootstrap_runtime.py", "root manifest does not register SBC runtime context validator"),
        ("manifest_path: engines/foundation/MANIFEST.yaml", "root manifest does not register Foundation manifest"),
        ("form_project_foundation", "root manifest does not register Foundation formation capability"),
    ]:
        if marker not in system_manifest:
            fail(errors, message)

    if "global_skill_discovery: forbidden_during_ordinary_execution" not in system_manifest:
        fail(errors, "root manifest does not explicitly forbid ordinary global skill discovery")
    if "research_machine_only: kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md" not in system_manifest:
        fail(errors, "root manifest does not register the machine-only Research constitution")
    if "engine_id: research" not in system_manifest or "status: available" not in system_manifest:
        fail(errors, "Research Engine is not materialized as an available engine")

    router = (ROOT / "ROUTER.md").read_text(encoding="utf-8")
    for forbidden in [".agents/skills", "archive/legacy-codex/SKILLS_INDEX.md"]:
        if forbidden in router:
            fail(errors, f"router points to forbidden global/legacy discovery surface: {forbidden}")
    if "kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md" not in router:
        fail(errors, "router does not apply Research machine-only constitutional precedence")

    engine_manifests = [
        ROOT / "engines/production/software/MANIFEST.yaml",
        ROOT / "engines/verification/MANIFEST.yaml",
        ROOT / "engines/research/MANIFEST.yaml",
        ROOT / "engines/foundation/MANIFEST.yaml",
    ]
    for manifest in engine_manifests:
        if not manifest.is_file():
            fail(errors, f"missing engine manifest: {manifest.relative_to(ROOT)}")
            continue
        text = manifest.read_text(encoding="utf-8")
        for rel in manifest_path_values(text):
            if not (ROOT / rel).exists():
                fail(errors, f"{manifest.relative_to(ROOT)} references missing path: {rel}")

    research_manifest = (ROOT / "engines/research/MANIFEST.yaml").read_text(encoding="utf-8")
    for required in [
        "default_research_mode: MACHINE_ONLY",
        "constitutional_authority: kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md",
        "third_party_human_research: true",
        "owner_manual_research_labor: true",
        "reachable_from_default_workflow: false",
        "question: validate_question",
        "work_package: validate_work_package",
        "source: validate_source",
        "experiment: validate_experiment",
        "method_freeze: validate_method_freeze",
        "separate_human_research_authorization: validate_human_research_authorization",
        "structural_regression_gate: tools/validate_structure.py",
    ]:
        if required not in research_manifest:
            fail(errors, f"Research manifest missing machine-only control: {required}")

    for rel in RESEARCH_ENFORCEMENT_SURFACES:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing active Research enforcement surface: {rel}")

    role_paths = [
        ROOT / "roles/control-director/ROLE.md",
        ROOT / "roles/control-verifier/ROLE.md",
        ROOT / "roles/executor/ROLE.md",
        ROOT / "roles/owner-interface/ROLE.md",
    ]
    for role in role_paths:
        if not role.is_file():
            fail(errors, f"missing role contract: {role.relative_to(ROOT)}")
            continue
        text = role.read_text(encoding="utf-8")
        for section in ROLE_REQUIRED_SECTIONS:
            if section not in text:
                fail(errors, f"{role.relative_to(ROOT)} missing section {section}")

    director = (ROOT / "roles/control-director/ROLE.md").read_text(encoding="utf-8")
    if "EXECUTOR_RESULT" not in director or "VERIFICATION_RESULT" not in director:
        fail(errors, "Control Director contract does not explicitly consume both role-native results")
    for state in ["ASSIGN", "WAIT", "ESCALATE", "COMPLETE"]:
        if state not in director:
            fail(errors, f"Control Director missing terminal control state: {state}")

    owner = (ROOT / "roles/owner-interface/ROLE.md").read_text(encoding="utf-8")
    if "OWNER_DECISION_RECORD" not in owner:
        fail(errors, "Owner Interface does not materialize durable Owner decisions")

    for schema in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"invalid JSON schema syntax {schema.relative_to(ROOT)}: {exc}")

    foundation_schemas = [
        "engines/foundation/schemas/project-seed.schema.json",
        "engines/foundation/schemas/project-outcome.schema.json",
        "engines/foundation/schemas/consequential-unknown-map.schema.json",
    ]
    for rel in foundation_schemas:
        try:
            schema = _load_schema(ROOT, rel)
            if schema.get("additionalProperties") is not False:
                fail(errors, f"foundation schema is not closed: {rel}")
            properties = schema.get("properties", {})
            if properties.get("status", {}).get("const") != "WORKING":
                fail(errors, f"foundation schema does not require WORKING status: {rel}")
            if properties.get("authoritative", {}).get("const") is not False:
                fail(errors, f"foundation schema is not machine-checkably non-authoritative: {rel}")
        except Exception as exc:
            fail(errors, f"foundation schema validation unavailable {rel}: {exc}")

    required_research_schemas = [
        "schemas/research-question.schema.json",
        "schemas/research-work-package.schema.json",
        "schemas/machine-experiment.schema.json",
        "schemas/research-method-freeze.schema.json",
        "schemas/research-source.schema.json",
        "schemas/human-research-authorization.schema.json",
        "schemas/owner-decision-record.schema.json",
    ]
    for rel in required_research_schemas:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing Research Engine schema: {rel}")

    if len(list((ROOT / "schemas").glob("*.schema.json"))) < 5:
        fail(errors, "fewer than five required role-native schemas are materialized")

    # Schema/validator closure and required-field contracts must not drift apart.
    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.research_policy import (
            HUMAN_AUTH_FIELDS,
            MACHINE_EXPERIMENT_REQUIRED,
            METHOD_FREEZE_REQUIRED,
            QUESTION_REQUIRED_FIELDS,
            SOURCE_REQUIRED_FIELDS,
            WORK_PACKAGE_REQUIRED_FIELDS,
        )
        schema_contracts = [
            ("schemas/research-question.schema.json", QUESTION_REQUIRED_FIELDS),
            ("schemas/research-work-package.schema.json", WORK_PACKAGE_REQUIRED_FIELDS),
            ("schemas/research-source.schema.json", SOURCE_REQUIRED_FIELDS),
            ("schemas/machine-experiment.schema.json", MACHINE_EXPERIMENT_REQUIRED),
            ("schemas/research-method-freeze.schema.json", METHOD_FREEZE_REQUIRED),
            ("schemas/human-research-authorization.schema.json", HUMAN_AUTH_FIELDS),
        ]
        for rel, policy_required in schema_contracts:
            schema = _load_schema(ROOT, rel)
            if schema.get("additionalProperties") is not False:
                fail(errors, f"Research schema is not closed: {rel}")
            schema_required = set(schema.get("required", []))
            if schema_required != set(policy_required):
                fail(errors, f"schema/policy required-field drift: {rel}")
    except Exception as exc:
        fail(errors, f"Research schema/policy contract comparison unavailable: {exc}")

    seen: dict[str, str] = {}
    for namespace in ACTIVE_SKILL_NAMESPACES:
        if not namespace.is_dir():
            fail(errors, f"missing active skill namespace: {namespace.relative_to(ROOT)}")
            continue
        for child in sorted(p for p in namespace.iterdir() if p.is_dir()):
            skill_id = child.name
            prior = seen.get(skill_id)
            if prior:
                fail(errors, f"duplicate active skill id {skill_id}: {prior} and {child.relative_to(ROOT)}")
            else:
                seen[skill_id] = str(child.relative_to(ROOT))
            if not (child / "SKILL.md").is_file():
                fail(errors, f"skill directory has no SKILL.md: {child.relative_to(ROOT)}")

    patterns = ROOT / "engines/production/software/patterns"
    if patterns.is_dir():
        for pattern in sorted(p for p in patterns.iterdir() if p.is_dir()):
            text = (pattern / "SKILL.md").read_text(encoding="utf-8").lower()
            if "solution pattern" not in text or "optional" not in text:
                fail(errors, f"pattern lost optional Solution Pattern classification: {pattern.name}")

    errors.extend(validate_software_skill_index(ROOT))

    legacy_factory = ROOT / "archive/legacy-codex/LOCALFLOW_FACTORY.md"
    if not legacy_factory.is_file():
        fail(errors, "legacy LOCALFLOW_FACTORY.md was not preserved in archive")

    errors.extend(validate_executability_gate(ROOT))
    errors.extend(validate_research_machine_only_gate(ROOT))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Project Resolver structural validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Project Resolver structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
