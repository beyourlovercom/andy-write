"""V1.2 cross-topic, deterministic traceability regression tests.

Examples are synthetic to avoid committing user article originals. The real
two-document evaluation corpus is kept privately under .runs on US Mac mini.
"""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from andy_write.fidelity import (
    CONTRACT, canonical, content_terms, inspect_fidelity,
    numeric_claim_candidates, source_units,
)
from andy_write.io import hashtext


def synthetic_article(kind: str = "irrigation") -> str:
    if kind == "irrigation":
        topics = [
            ("connector locknuts", "polyethylene pipe","rubber grommet","tightened fitting"),
            ("flow pressure", "lateral line","drip emitter","wetting pattern"),
            ("field inspection", "blocked filter","visible leakage","maintenance log"),
            ("winter storage", "empty manifold","clean tubing","weather protection"),
        ]
    else:
        topics = [
            ("customer order", "receipt archive", "tracking reference", "refund policy"),
            ("shipping inspection", "carton corner", "photo evidence", "damage report"),
            ("return window", "service contact", "vendor decision", "time limit"),
            ("support escalation", "ticket reference", "saved messages", "resolution log"),
        ]
    parts = []
    for i, keys in enumerate(topics,1):
        parts.append(
            f"## Section {i}\n\n"
            f"Inspect the {keys[0]} alongside the {keys[1]} and "
            f"the {keys[2]}. Record the {keys[3]} before finishing the "
            f"procedure. These instructions focus on observation rather "
            f"than claims about untested equipment. Document findings "
            f"and retain the written reference for later comparison.")
    return "\n\n".join(parts)


class FidelityContractTests(unittest.TestCase):
    def setUp(self):
        self.source = synthetic_article("irrigation")
        self.other = synthetic_article("retail")

    def test_two_distinct_topics_have_identity_baseline(self):
        for article in (self.source, self.other):
            with self.subTest(source=hashtext(article)[:9]):
                result = inspect_fidelity(article, article, source_ref="private-ref")
                summary = result["summary"]
                self.assertGreater(summary["source_units_considered"], 2)
                self.assertEqual(summary["exact_text_present_units"],
                                 summary["source_units_considered"])
                self.assertEqual(summary["unmapped_units_needing_review"], 0)
                self.assertEqual(summary["human_review_completion_percent"], 0)
                self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")

    def test_controlled_deletion_is_detected_on_both_topics(self):
        for article in (self.source, self.other):
            with self.subTest(source=hashtext(article)[:9]):
                chunks = article.split("\n\n")
                self.assertGreaterEqual(len(chunks), 4)
                modified = "\n\n".join(chunks[:-1])
                report = inspect_fidelity(article, modified)
                self.assertLess(report["summary"]["exact_text_present_units"],
                                report["summary"]["source_units_considered"])
                self.assertGreater(report["summary"]["unmapped_units_needing_review"], 0)

    def test_lexical_candidate_not_misreported_as_semantic_pass(self):
        source = self.source
        altered = source.replace("Record the", "Neglect the")  # changes the meaning!
        report = inspect_fidelity(source, altered)
        self.assertGreater(report["summary"]["lexical_candidate_units"], 0)
        self.assertEqual(report["human_factual_approval"], "PENDING")
        self.assertEqual(report["status"], "HUMAN_REVIEW_REQUIRED")

    def test_new_numeric_statements_are_review_candidates_not_fact_labels(self):
        report = inspect_fidelity(self.source, self.source + "\n\nSet pressure to 24 kg.")
        self.assertIn("24kg", report["summary"]["new_numeric_claim_candidates"])
        self.assertNotIn("fake_claims", report["summary"])

    def test_numeric_claim_existing_does_not_flag(self):
        base = self.source + "\n\nWater pipe is 16 mm wide."
        result = inspect_fidelity(base, base)
        self.assertNotIn("16mm",result["summary"]["new_numeric_claim_candidates"])

    def test_metadata_does_not_expose_article_text(self):
        unusual = "uniquevividphrasezirconium"
        original = self.source + "\n\n" + unusual*8 + " inspect connector leaks."
        report = inspect_fidelity(original, original)
        serialized=json.dumps(report)
        self.assertNotIn(unusual, serialized)
        self.assertIn("source_sha256",serialized)
        self.assertIn(CONTRACT,serialized)

    def test_human_positive_annotation_requires_exact_target_quote(self):
        original = self.source
        report = inspect_fidelity(original,original)
        unit = report["units"][0]
        invalid = {"source_id":unit["source_id"],"source_sha256":unit["source_sha256"],
                   "reviewer":"Owner","status":"RETAINED",
                   "reason":"Reviewed and compared against original source.",
                   "target_quote":"a made-up quote that is not in the draft"}
        with self.assertRaisesRegex(ValueError,"literal target quote"):
            inspect_fidelity(original,original,reviewer_notes=[invalid])

    def test_manual_review_annotation_is_not_machine_fact_approval(self):
        report = inspect_fidelity(self.source,self.source)
        unit = report["units"][0]
        note={"source_id":unit["source_id"],"source_sha256":unit["source_sha256"],
              "reviewer":"Owner",
              "status":"CHANGED_WITH_APPROVAL",
              "reason":"Approved retaining the important procedure with a rewrite.",
              "target_quote":"Inspect the connector locknuts"}
        reviewed=inspect_fidelity(self.source,self.source,reviewer_notes=[note])
        self.assertEqual(reviewed["summary"]["human_approved_changed_units"],1)
        self.assertEqual(reviewed["human_factual_approval"],"PENDING")
        self.assertNotIn("Approved retaining",json.dumps({
            k:v for k,v in reviewed.items() if k!="units"
        }))

    def test_invalid_reviewer_notes_blocked(self):
        row=inspect_fidelity(self.source,self.source)["units"][0]
        for changes in ({"source_sha256":"stale"}, {"reviewer":""},
                        {"status":"AUTOMATICALLY_VERIFIED"}):
            note = {"source_id":row["source_id"],
                    "source_sha256":row["source_sha256"],"reviewer":"Owner",
                    "status":"RETAINED",
                    "reason":"Human checked the source against existing target.",
                    "target_quote":"Inspect the connector locknuts"}
            note.update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    inspect_fidelity(self.source,self.source,reviewer_notes=[note])

    def test_reject_topic_only_input_or_empty_output(self):
        with self.assertRaisesRegex(ValueError,"substantive"):
            inspect_fidelity("a short title","Anything")
        with self.assertRaisesRegex(ValueError,"No draft"):
            inspect_fidelity(self.source,"")

    def test_all_source_paragraphs_have_traceable_ids(self):
        from andy_write.fidelity import PARAGRAPH
        source = self.source + "\n\n## A short heading\n\nSmall note."
        report = inspect_fidelity(source, source)
        summary = report["summary"]
        self.assertTrue(summary["all_source_paragraphs_accounted_for"])
        self.assertEqual(
            summary["source_items_total_including_short"],
            len(PARAGRAPH.split(source)))
        self.assertGreater(summary["source_paragraphs_not_scored"], 0)
        units = report["units"] + report["short_or_heading_units"]
        self.assertEqual(len({x["source_id"] for x in units}), len(units))

    def test_short_source_can_be_manually_marked_intentionally_omitted(self):
        source = self.source + "\n\nOptional unsafe guidance."
        report = inspect_fidelity(source, self.source)
        note = report["short_or_heading_units"][-1]
        decision = {
            "source_id":note["source_id"],
            "source_sha256":note["source_sha256"],
            "status":"INTENTIONALLY_OMITTED",
            "reviewer":"Owner",
            "reason":"Intentionally omitted after verifying it is not applicable to this product."
        }
        with_review = inspect_fidelity(source, self.source, reviewer_notes=[decision])
        self.assertEqual(with_review["summary"]["human_intentionally_omitted_units"],1)
        self.assertEqual(with_review["human_factual_approval"],"PENDING")

    def test_private_review_sheet_contains_ids_not_original_text(self):
        from andy_write.fidelity import review_sheet
        report = inspect_fidelity(self.source,self.other)
        sheet = review_sheet(report)
        self.assertIn("SRC-P",sheet)
        self.assertIn("HUMAN",sheet.upper())
        self.assertIn("INTENTIONALLY_OMITTED",sheet)
        self.assertNotIn("connector locknuts",sheet)

    def test_cli_output_must_stay_gitignored_and_private(self):
        from andy_write.__main__ import fidelity as command
        with tempfile.TemporaryDirectory() as d:
            source=pathlib.Path(d)/"original.md"
            source.write_text(self.source)
            with patch("andy_write.__main__.resolved",return_value=source):
                with self.assertRaisesRegex(ValueError,"ignored"):
                    command("source.md","target.md","docs/published-report.json")

if __name__ == "__main__":
    unittest.main()
