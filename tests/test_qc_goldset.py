"""No fabricated human labels or source data in tracked QC outputs."""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from andy_write.qc_goldset import build_goldset,write_goldset,LABEL_OPTIONS
from andy_write.io import ROOT

def fixture(kind:int=0)->str:
    return "\n\n".join(
        (f"## Section {n}\n\nThe owner describes a real source procedure {n}. "
         f"Manufacturer instructions and product warnings can change from model to model. "
         f"Check accessory {n} and document the result before accepting unsupported care claims. "
         f"Remember material compatibility and avoid heat for delicate assemblies. ")
        for n in range(1,20))

class GoldsetTests(unittest.TestCase):
    def setUp(self):
        self.source=fixture()
        self.draft=self.source.replace("avoid heat","check limits")
    def test_reproducible_stratified_sample(self):
        a=build_goldset(self.source,self.draft,size=12)
        b=build_goldset(self.source,self.draft,size=12)
        self.assertEqual(a["sampled_source_paragraphs"],
                         b["sampled_source_paragraphs"])
        self.assertEqual(a["sample_count"],12)
        self.assertLess(min(a["sampled_source_paragraphs"]),8)
        self.assertGreater(max(a["sampled_source_paragraphs"]),30)
        self.assertEqual(len(set(a["sampled_source_paragraphs"])),12)
    def test_no_automatic_human_approval(self):
        o=build_goldset(self.source,self.draft)
        self.assertIsNone(o["gold_standard_semantic_score"])
        self.assertEqual(o["owner_approval"],"PENDING")
        self.assertFalse(o["labels_are_human_provided"])
        self.assertTrue(all(x["proposed_label"] is None and
                            x["owner_confirmation"]=="PENDING" for x in o["cases"]))
    def test_full_passage_included_only_for_private_worksheet(self):
        o=build_goldset(self.source,self.draft)
        self.assertTrue(any("manufacturer" in x["source_text_for_private_review"].lower()
                            for x in o["cases"]))
        self.assertTrue(any(x["material_claim_review_candidate"] for x in o["cases"]))
    def test_block_tracking_user_original_in_repository(self):
        with self.assertRaisesRegex(ValueError,"private .runs"):
            write_goldset(self.source,self.draft,ROOT/"docs/exposed-labels.json",12)
    def test_reject_undersized_or_too_large_sample(self):
        for n in (1,3,41):
            with self.subTest(size=n):
                with self.assertRaises(ValueError):
                    build_goldset(self.source,self.draft,n)
    def test_model_comparator_cannot_define_auto_semantic_retention_rate(self):
        o=build_goldset(self.source,self.draft)
        self.assertNotIn("automatic_semantic_retention_pct",o)
        self.assertIn("LOST_USEFUL_INFORMATION",LABEL_OPTIONS)
        self.assertIn("INTENTIONALLY_OMITTED_UNSAFE_OR_INAPPLICABLE",LABEL_OPTIONS)

if __name__=="__main__":
    unittest.main()
