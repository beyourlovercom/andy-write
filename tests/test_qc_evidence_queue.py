"""Human evidence workflow has no automatic factual approval and no file leaks."""
from __future__ import annotations
import csv
import pathlib
import tempfile
import unittest
from andy_write.io import ROOT
from andy_write.claim_evidence import trace_claims
from andy_write.qc_evidence_queue import build_queue,export_queue,category_for

SOURCE=("Check the manufacturer's care instructions and actual product material "
        "before cleaning. Keep the original purchase receipt and document any "
        "handling problem. The order confirmation is part of the original customer "
        "record. ")*10
DRAFT="""# Guide

## What to verify?

Always review cleaning instructions before washing silicone material.
Avoid extreme heat or unapproved lubricant for this specific model.
Store this product away from direct sunlight and high temperature.
"""
class QueueTests(unittest.TestCase):
    def setUp(self):
        self.report=trace_claims(DRAFT,SOURCE)
    def test_all_important_claims_accounted_for_and_prioritized(self):
        queue=build_queue(self.report)
        self.assertEqual(queue["important_claims"],len(self.report["claims"]))
        self.assertEqual(queue["high_priority"]+queue["medium_priority"],
                         queue["important_claims"])
        self.assertEqual(queue["actual_human_fact_approvals"],0)
        self.assertFalse(queue["model_available"])
        self.assertTrue(all(r["reviewer_decision"]=="PENDING"
                            for r in queue["rows"]))
    def test_model_absence_is_explicit_and_does_not_auto_approve(self):
        queue=build_queue(self.report)
        self.assertTrue(all(r["manufacturer_model"]=="NOT_PROVIDED"
                            for r in queue["rows"]))
        with_model=build_queue(self.report,product_model="AB12")
        self.assertTrue(with_model["model_available"])
        self.assertEqual(with_model["actual_human_fact_approvals"],0)
    def test_content_categories_not_fake_factual_labels(self):
        self.assertEqual(category_for("Do not expose this toy to direct sunlight"),
                         "HEAT_TEMPERATURE")
        self.assertEqual(category_for("Use a compatible lubricant"),
                         "LUBRICANT_CHEMICAL")
        self.assertEqual(category_for("Do not submerge electronics"),
                         "WATERPROOF_ELECTRONICS")
    def test_private_output_guard(self):
        with self.assertRaisesRegex(PermissionError,"private"):
            export_queue(self.report,ROOT/"docs/evidence.csv")
    def test_csv_formula_injection_is_escaped(self):
        source=build_queue(self.report)
        source["rows"][0]["claim"]="=HYPERLINK('https://evil.invalid')"
        # Test the real CSV writer with a deliberately modified private report
        report=self.report.copy()
        reports=[dict(x) for x in report["claims"]]
        reports[0]["claim"]="=HYPERLINK('https://evil.invalid')"
        report["claims"]=reports
        p=ROOT/".runs"/"test-qc-evidence-formula-safe.csv"
        try:
            export_queue(report,p)
            with p.open(encoding="utf-8-sig",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertTrue(any(r["claim"].startswith("'=") for r in rows))
        finally:
            p.unlink(missing_ok=True)
if __name__=="__main__":
    unittest.main()
