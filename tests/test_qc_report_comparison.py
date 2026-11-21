"""Synthetic comparison checks, not independent editorial labels."""
from copy import deepcopy
import unittest

from scripts.compare_context_qc_reports import compare_reports


def report(version: str) -> dict:
    return {
        "schema": version, "benchmark_id": "synthetic", "source_url": "https://test.invalid/a",
        "source_post_id": 1, "source_modified": "2026-11-21T00:00:00",
        "source_content_sha256": "synthetic-sha", "source_role": "public_competitor_qc_benchmark_only",
        "scope_subject": "adult products", "search_intent_verdict": "UNASSESSABLE",
        "status": "HUMAN_REVIEW_REQUIRED", "publish_ready": False,
        "human_labels_present": 0, "validated_truth_errors": None,
        "summary": {"by_priority": {"P1": 1}},
        "candidates": [{"code": "MODEL_SPEC_PROVENANCE_REVIEW", "anchor": "Wands",
                        "priority": "P1", "editorial_verdict": "NEEDS_HUMAN_REVIEW",
                        "verified_fact_error": False}],
    }


class ComparisonTests(unittest.TestCase):
    def test_identical_scope_preserves_counts_and_adds_evidence_detail(self):
        before, after = report("v1"), report("v1.1")
        after["candidates"][0]["review_details"] = {
            "explicit_model_identifier_present": False,
            "evidence_gaps": ["model_identity_unstated"]}
        result = compare_reports(before, after)
        self.assertTrue(result["same_candidate_locations"])
        self.assertEqual((result["before_count"], result["after_count"]), (1, 1))
        self.assertEqual(result["after_evidence_details"][0]["anchor"], "Wands")
        self.assertIsNone(result["quality_precision_or_recall"])
        self.assertFalse(result["publish_ready"])

    def test_source_or_revision_change_fails_closed(self):
        before = report("v1")
        after = deepcopy(before)
        after["source_content_sha256"] = "another-revision"
        with self.assertRaisesRegex(ValueError, "SCOPE_OR_SOURCE_CHANGED"):
            compare_reports(before, after)

    def test_human_truth_fabrication_or_publish_gate_fails_closed(self):
        before = report("v1")
        for path, value in (("human_labels_present", 1), ("publish_ready", True)):
            after = deepcopy(before)
            after[path] = value
            with self.assertRaises(ValueError):
                compare_reports(before, after)
        after = deepcopy(before)
        after["candidates"][0]["verified_fact_error"] = True
        with self.assertRaisesRegex(ValueError, "factual verdict"):
            compare_reports(before, after)


if __name__ == "__main__":
    unittest.main()
