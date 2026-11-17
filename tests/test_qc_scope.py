"""Benchmark-scoping regressions; no real Owner text or competitor prose."""
import copy
import unittest

from andy_write.io import hashtext
from andy_write.qc_scope import QC_SCOPE_VERSION, validate_qc_scope
from andy_write.qc_reverse import html_qc_profile, markdown_qc_profile, compare_structure
from andy_write.content_quality import repeated_section_information, audit


class ApprovedBenchmarkScopeTests(unittest.TestCase):
    def setUp(self):
        body = "<h2>Material choices</h2><p>" + ("Compare exact models and manuals. " * 65) + "</p>"
        self.snapshot = {"id": 87, "link": "https://example.com/approved-doll.html",
                         "date": "2025-12-20T12:00:00", "modified": "2026-07-28T12:00:00",
                         "content": {"rendered": body}}
        self.contract = {
            "version": QC_SCOPE_VERSION, "owner_approval": "EXPLICIT",
            "benchmark": {"source_role": "QC_STRUCTURE_ONLY", "post_id": 87,
                          "url": self.snapshot["link"],
                          "published_date": "2025-12-20", "modified_date": "2026-07-28",
                          "content_sha256": hashtext(body),
                          "primary_topic": "full-size doll", "reader_intent": "materials and use"},
            "existing_owner_draft": {"source_role": "EXISTING_OWNER_ARTICLE",
                                     "url": "https://brand.example/", "primary_topic": "full-size doll",
                                     "reader_intent": "unboxing"},
            "excluded_primary_topics": ["torso"],
        }

    def test_cross_intent_remains_structural_and_has_no_article_job(self):
        result = validate_qc_scope(self.snapshot, self.contract, "https://brand.example/")
        self.assertEqual(result["intent_relation"], "CROSS_INTENT_STRUCTURE_ONLY")
        self.assertFalse(result["article_scope_created"])
        self.assertEqual(result["release_gate"], "HUMAN_FACT_AND_SEMANTIC_REVIEW_REQUIRED")
        competitor = html_qc_profile(self.snapshot["content"]["rendered"],
                   url=self.snapshot["link"], date=self.snapshot["date"],
                   modified=self.snapshot["modified"], article_id=87)
        ours = markdown_qc_profile("# A\n\n## Unboxing\n\nInspect the package.",
                                   source_label="https://brand.example/")
        comparison = compare_structure(competitor, ours, result["intent_relation"])
        self.assertEqual(comparison["comparison_type"],
                         "STRUCTURAL_ONLY_NOT_QUALITY_OR_RANKING")
        self.assertEqual(comparison["intent_relation"], "CROSS_INTENT_STRUCTURE_ONLY")

    def test_same_declared_intent_still_needs_human_review(self):
        contract = copy.deepcopy(self.contract)
        contract["existing_owner_draft"]["reader_intent"] = "materials and use"
        result = validate_qc_scope(self.snapshot, contract, "https://brand.example/")
        self.assertIn("HUMAN_REVIEW_REQUIRED", result["intent_relation"])

    def test_source_url_revision_and_identity_are_immutable(self):
        for field, value in (("link", "https://example.com/torso.html"),
                             ("id", 88), ("modified", "2026-08-01T01:00:00")):
            altered = copy.deepcopy(self.snapshot)
            altered[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_qc_scope(altered, self.contract, "https://brand.example/")
        altered = copy.deepcopy(self.snapshot)
        altered["content"]["rendered"] += "<p>Unapproved revision.</p>"
        with self.assertRaisesRegex(ValueError, "REVISION_CHANGED"):
            validate_qc_scope(altered, self.contract, "https://brand.example/")

    def test_torso_substitution_role_swap_and_unapproved_contract_rejected(self):
        for key, value in (("primary_topic", "torso"),
                           ("primary_topic", "torso doll"),
                           ("reader_intent", "")):
            contract = copy.deepcopy(self.contract)
            contract["benchmark"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_qc_scope(self.snapshot, contract, "https://brand.example/")
        contract = copy.deepcopy(self.contract)
        contract["benchmark"]["source_role"] = "OWNER_ORIGINAL"
        with self.assertRaises(PermissionError):
            validate_qc_scope(self.snapshot, contract, "https://brand.example/")
        contract = copy.deepcopy(self.contract)
        contract["owner_approval"] = "ASSUMED"
        with self.assertRaises(PermissionError):
            validate_qc_scope(self.snapshot, contract, "https://brand.example/")


class InformationValueReviewTests(unittest.TestCase):
    REPEAT = ("Check the exact manufacturer instructions and confirm which material "
              "is specified before following any proposed cleaning procedure.")

    def test_duplicated_useful_warning_is_review_not_fact_error(self):
        article = ("# Draft\n\nIntro text.\n\n## Materials\n\n" + self.REPEAT +
                   "\n\n## Cleaning\n\n" + self.REPEAT)
        repeats = repeated_section_information(article)
        self.assertEqual(len(repeats), 1)
        self.assertEqual(repeats[0]["headings"], ["Materials", "Cleaning"])
        self.assertNotIn("manufacturer instructions", str(repeats))
        report = audit(article, {"job_id": "fictional-sample"})
        self.assertIn("CROSS_SECTION_REPETITION_REVIEW",
                      [x["code"] for x in report["issues"]])
        self.assertEqual(report["human_fact_check"], "PENDING")

    def test_distinct_section_information_has_no_repeat_flag(self):
        article = ("# Draft\n\n## Materials\n\n" + self.REPEAT +
                   "\n\n## Cleaning\n\nCompare a different specific model, check its "
                   "official instructions, and document any incompatibility first.")
        self.assertEqual(repeated_section_information(article), [])


if __name__ == "__main__":
    unittest.main()
