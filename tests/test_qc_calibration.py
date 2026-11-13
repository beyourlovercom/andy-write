"""Artificial examples only. Never commit or fabricate 12 real human labels."""
from __future__ import annotations
import json
import unittest
from andy_write.qc_calibration import (
    calibrate, validate_packet, machine_positive, REVIEW_DECLARATION
)
from andy_write.qc_goldset import build_goldset
from andy_write.fidelity import inspect_fidelity, PARAGRAPH

def article()->str:
    return "\n\n".join(
        f"## Topic {n}\n\nCheck the material for procedure {n} and verify supplier "
        f"instructions before reusing the container. Save the receipt from "
        f"purchase number {n} and check the handling condition carefully. "
        f"Always inspect the matching accessory and documented care steps."
        for n in range(1,25))

class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.original=article()
        self.draft=self.original
        self.packet=build_goldset(self.original,self.draft,size=12)
    def test_frozen_packet_valid(self):
        self.assertEqual(len(validate_packet(self.packet,self.original,self.draft)),12)
    def test_without_real_human_labels_no_semantic_metric(self):
        result=calibrate(self.packet,self.original,self.draft)
        self.assertEqual(result["status"],"AWAITING_HUMAN_LABELS")
        self.assertIsNone(result["gold_standard_semantic_accuracy"])
        self.assertIsNone(result["calibrated_threshold"])
        self.assertEqual(result["human_labels_present"],0)
        self.assertFalse(result["auto_apply_calibration"])
    def test_tampered_source_or_draft_never_reuses_labels(self):
        for item in (("source",self.original+"Changed." ,self.draft),
                     ("draft",self.original,self.draft+"Changed.")):
            with self.subTest(where=item[0]):
                with self.assertRaisesRegex(ValueError,"SHA-256"):
                    calibrate(self.packet,item[1],item[2])
    def test_partial_or_duplicate_human_labels_fail_closed(self):
        note=self.fake_note(self.packet["cases"][0], "SEMANTICALLY_RETAINED")
        with self.assertRaisesRegex(ValueError,"Exactly 12"):
            calibrate(self.packet,self.original,self.draft,[note])
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            calibrate(self.packet,self.original,self.draft,[note]*12)
    def fake_note(self,case,label):
        return {
            "source_id":case["source_id"],
            "source_sha256":case["source_sha256"],
            "reviewer":"Example Editor (synthetic test only)",
            "reviewer_declaration":REVIEW_DECLARATION,
            "reason":"This is a simulated unit test verifying that no labels are invented.",
            "target_quote":"Check the material for procedure",
            "label":label
        }
    def test_claimed_positive_must_have_existing_draft_quote(self):
        notes=[self.fake_note(x,"SEMANTICALLY_RETAINED") for x in self.packet["cases"]]
        notes[0]["target_quote"]="A completely invented nonexisting statement"
        with self.assertRaisesRegex(ValueError,"real draft passage"):
            calibrate(self.packet,self.original,self.draft,notes)
    def test_machine_or_missing_attestation_not_allowed(self):
        notes=[self.fake_note(x,"SEMANTICALLY_RETAINED") for x in self.packet["cases"]]
        notes[0]["reviewer"]="AI-automatic classification"
        with self.assertRaisesRegex(ValueError,"impersonate"):
            calibrate(self.packet,self.original,self.draft,notes)
        notes[0]["reviewer"]="Real Editor"
        notes[0]["reviewer_declaration"]="did not inspect"
        with self.assertRaisesRegex(ValueError,"declaration"):
            calibrate(self.packet,self.original,self.draft,notes)
    def test_balanced_fixture_yields_only_exploratory_proposal(self):
        notes=[self.fake_note(x,"SEMANTICALLY_RETAINED" if i<6
                              else "LOST_USEFUL_INFORMATION")
               for i,x in enumerate(self.packet["cases"])]
        out=calibrate(self.packet,self.original,self.draft,notes)
        self.assertEqual(out["human_labels_present"],12)
        self.assertEqual(out["owner_approval"],"PENDING")
        self.assertIsNone(out["calibrated_threshold"])
        self.assertIn(out["calibration_status"],
                      ("NO_POSITIVE_NEGATIVE_PREDICTION_DIVERSITY",
                       "EXPLORATORY_ONLY_NEEDS_INDEPENDENT_HOLDOUT"))
        self.assertIn("fp",out["baseline_confusion"])
        self.assertFalse(out["auto_apply_calibration"])
        self.assertEqual(out["approved_human_label_count"],0)
    def test_one_sided_human_labels_not_valid_calibration(self):
        notes=[self.fake_note(x,"SEMANTICALLY_RETAINED")
               for x in self.packet["cases"]]
        out=calibrate(self.packet,self.original,self.draft,notes)
        self.assertEqual(out["calibration_status"],"INSUFFICIENT_BALANCED_GOLDSET")
        self.assertIsNone(out["calibrated_threshold"])
    def test_short_item_never_machine_semantic_pass(self):
        self.assertFalse(machine_positive({"state":"SHORT_OR_HEADING_REVIEW"},
                                          recall=.4,anchors=.3))

if __name__=="__main__":
    unittest.main()
