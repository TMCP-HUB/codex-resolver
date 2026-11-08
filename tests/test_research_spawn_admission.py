from __future__ import annotations

from copy import deepcopy
import unittest

from tests.test_assignment_compiler import action
from tests.test_research_machine_only import base_wp
from tests.test_resolver_spawn import bundle
from tools.research_policy import admit_work_package
from tools.resolver_spawn import resolve_spawn

POLICY_SURFACE = "tools.research_policy.admit_work_package"


def attach_research_admission(value: dict, work_package: dict | None = None, admission_id: str = "RESEARCH-ADM-1") -> dict:
    work = deepcopy(work_package or base_wp())
    admission_result = admit_work_package(work)
    admission = {
        "artifact_id": admission_id,
        **admission_result,
        "WORK_PACKAGE_ID": work["WORK_PACKAGE_ID"],
        "QUESTION_ID": work["QUESTION_ID"],
        "POLICY_SURFACE": POLICY_SURFACE,
        "PROVENANCE": [POLICY_SURFACE, work["WORK_PACKAGE_ID"], work["QUESTION_ID"]],
        "WORK_PACKAGE": work,
    }
    value["decision"].update({
        "research_admission_ref": admission_id,
        "research_work_package_id": work["WORK_PACKAGE_ID"],
        "research_question_id": work["QUESTION_ID"],
    })
    value["artifacts"].append(admission)
    return admission


def research_bundle() -> dict:
    return bundle("research", "execute_research_work", "machine-only-execution")


class ResearchSpawnAdmissionContinuityTest(unittest.TestCase):
    def assert_escalates(self, value: dict, reason: str) -> dict:
        result = resolve_spawn(value)
        self.assertEqual((result["control_state"], result["reason"]), ("ESCALATE", reason), result)
        self.assertNotIn("assignment", result)
        return result

    def test_positive_real_research_admission_composes_to_spawn_ready(self) -> None:
        value = research_bundle()
        admission = attach_research_admission(value)
        self.assertEqual(admission["ADMISSION_STATUS"], "ADMITTED_MACHINE_RESEARCH")
        self.assertNotIn("research_admission", value["decision"])

        result = resolve_spawn(value)

        self.assertEqual((result["control_state"], result["status"]), ("ASSIGN", "SPAWN_READY"), result)
        self.assertEqual(result["research_admission_ref"], admission["artifact_id"])
        self.assertEqual(result["research_admission"]["WORK_PACKAGE_ID"], admission["WORK_PACKAGE_ID"])
        self.assertEqual(result["research_admission"]["QUESTION_ID"], admission["QUESTION_ID"])
        self.assertEqual(result["assignment_admissibility"]["status"], "ADMISSIBLE")
        self.assertEqual(result["assignment"]["execution_contract"]["proof_status"], "PROVEN")
        self.assertIn(admission["artifact_id"], result["assignment"]["related_artifacts"])

    def test_A_no_research_admission_fails_closed(self) -> None:
        self.assert_escalates(research_bundle(), "RESEARCH_ADMISSION_REQUIRED")

    def test_B_bare_legacy_marker_is_not_authority(self) -> None:
        value = research_bundle()
        value["decision"]["research_admission"] = "MACHINE_ONLY_ADMITTED"
        self.assert_escalates(value, "RESEARCH_ADMISSION_REQUIRED")

    def test_C_unresolved_admission_ref_fails_closed(self) -> None:
        value = research_bundle()
        attach_research_admission(value)
        value["decision"]["research_admission_ref"] = "RESEARCH-ADM-MISSING"
        self.assert_escalates(value, "RESEARCH_ADMISSION_UNRESOLVED")

    def test_D_malformed_admission_result_fails_closed(self) -> None:
        value = research_bundle()
        admission = attach_research_admission(value)
        admission["ERRORS"] = "not-a-list"
        self.assert_escalates(value, "RESEARCH_ADMISSION_RESULT_MISMATCH")

    def test_E_non_admitted_work_package_fails_closed(self) -> None:
        value = research_bundle()
        work = base_wp()
        work["REQUIRES_THIRD_PARTY_HUMAN"] = True
        admission = attach_research_admission(value, work)
        self.assertNotEqual(admission["ADMISSION_STATUS"], "ADMITTED_MACHINE_RESEARCH")
        self.assert_escalates(value, "RESEARCH_ADMISSION_NOT_ADMITTED")

    def test_F_admission_for_other_work_package_cannot_authorize_selected_work(self) -> None:
        value = research_bundle()
        attach_research_admission(value)
        value["decision"]["research_work_package_id"] = "WP-OTHER"
        self.assert_escalates(value, "RESEARCH_ADMISSION_IDENTITY_MISMATCH")

    def test_G_question_identity_mismatch_fails_closed(self) -> None:
        value = research_bundle()
        attach_research_admission(value)
        value["decision"]["research_question_id"] = "Q-OTHER"
        self.assert_escalates(value, "RESEARCH_ADMISSION_IDENTITY_MISMATCH")

    def test_H_lookalike_without_research_provenance_fails_closed(self) -> None:
        value = research_bundle()
        admission = attach_research_admission(value)
        admission["PROVENANCE"] = [admission["WORK_PACKAGE_ID"], admission["QUESTION_ID"]]
        self.assert_escalates(value, "MALFORMED_RESEARCH_ADMISSION")

    def test_I_valid_research_admission_does_not_bypass_generic_executability(self) -> None:
        value = research_bundle()
        attach_research_admission(value)
        value["assignment_compilation_draft"]["mandatory_actions"][0]["required_capabilities"].append("database_access")
        value["assignment_compilation_draft"]["authorized_required_capabilities"].append("database_access")

        result = resolve_spawn(value)

        self.assertEqual((result["control_state"], result["reason"]), ("WAIT", "ASSIGNMENT_NOT_ADMISSIBLE"), result)
        self.assertEqual(result["missing_capabilities"], ["database_access"])
        self.assertNotIn("assignment", result)

    def test_software_and_verification_do_not_require_research_fields(self) -> None:
        software = resolve_spawn(bundle())
        verification_value = bundle("verification", "verify_completion_claim", "exact-evidence-verification")
        verification_value["assignment_compilation_draft"]["evidence_requirements"] = [
            action("verification-evidence", capabilities=["python_runtime"], obligation_class="local_evidence")
        ]
        verification = resolve_spawn(verification_value)
        self.assertEqual((software["control_state"], software["status"]), ("ASSIGN", "SPAWN_READY"), software)
        self.assertEqual((verification["control_state"], verification["status"]), ("ASSIGN", "SPAWN_READY"), verification)


if __name__ == "__main__":
    unittest.main()
