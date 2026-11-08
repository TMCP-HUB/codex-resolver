from __future__ import annotations

import unittest

from tests.test_research_machine_only import base_wp
from tools.research_policy import validate_source, validate_work_package


def sample_source(source_id: str) -> dict:
    return {
        "SOURCE_ID": source_id,
        "PROVENANCE_CLASS": "OFFICIAL_REFERENCE",
        "ORIGIN": "EXTERNAL_PREEXISTING",
        "HUMAN_ORIGIN": False,
        "PROJECT_GENERATION_PROHIBITED": True,
        "DESCRIPTION": "Pre-existing official technical documentation",
        "SOURCE_URI": "https://example.org/reference",
    }


class SourceDiscoveryTest(unittest.TestCase):
    def test_research_work_package_needs_no_preselected_sites(self) -> None:
        wp = base_wp()
        self.assertNotIn("SOURCE_SELECTION_MODE", wp)
        self.assertNotIn("SOURCE_SCOPE", wp)
        self.assertEqual(validate_work_package(wp), [])

    def test_valid_discovered_source_is_admitted(self) -> None:
        self.assertEqual(validate_source(sample_source("FOUND-LATER")), [])

    def test_source_selection_fields_are_not_part_of_research_contract(self) -> None:
        wp = base_wp()
        wp["SOURCE_SCOPE"] = ["PRESELECTED"]
        self.assertTrue(any("SOURCE_SCOPE" in error for error in validate_work_package(wp)))

    def test_source_provenance_policy_is_preserved(self) -> None:
        source = sample_source("SOURCE-1")
        source["HUMAN_ORIGIN"] = True
        source["ORIGIN"] = "PROJECT_MACHINE_GENERATED"
        errors = validate_source(source)
        self.assertTrue(any("human-origin source cannot be project machine-generated" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
