"""Unseen other-industry holdout must remain sealed until real human labels."""
from __future__ import annotations
import hashlib
import unittest
from andy_write.qc_blind import check_holdout
from andy_write.io import ROOT
from andy_write.qc_blind import verify_private_holdout

BYTES=("A real owner manuscript is deliberately not loaded into code here. "*35).encode()
MANIFEST={
    "status":"SEALED_UNSEEN_HOLDOUT_NO_EVALUATION",
    "sha256":hashlib.sha256(BYTES).hexdigest(),
    "bytes":len(BYTES),
    "testing":{"rewrites_completed":0,"labels_completed":0,"training_access":False}
}
class BlindTests(unittest.TestCase):
    def test_normal_sealed_holdout_does_not_launch_evaluation(self):
        r=check_holdout(MANIFEST,BYTES)
        self.assertEqual(r["status"],"HOLDOUT_SEALED_WAITING_FOR_HUMAN_GOLDSET")
        self.assertFalse(r["automatic_model_evaluation_allowed"])
        self.assertEqual(r["owner_explicit_unseal_approval"],"PENDING")
    def test_modified_source_refuses_blind_label(self):
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            check_holdout(MANIFEST,BYTES+b"tampered")
    def test_used_or_unsealed_holdout_is_contaminated(self):
        for key in ("rewrites_completed","labels_completed","training_access"):
            altered={**MANIFEST,"testing":{**MANIFEST["testing"],key:1}}
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"contamination"):
                    check_holdout(altered,BYTES)
    def test_even_eligible_prerequisite_never_auto_unseals(self):
        c={"calibration_status":"EXPLORATORY_ONLY_NEEDS_INDEPENDENT_HOLDOUT"}
        a={"status":"AGREEMENT_COMPUTED_NOT_OWNER_APPROVED"}
        r=check_holdout(MANIFEST,BYTES,c,a)
        self.assertTrue(r["engineering_prerequisites_ready"])
        self.assertFalse(r["automatic_model_evaluation_allowed"])
        self.assertEqual(r["owner_explicit_unseal_approval"],"PENDING")
    def test_holdout_source_must_stay_private(self):
        with self.assertRaises(PermissionError):
            verify_private_holdout(ROOT/"docs/manifest.json",
                ROOT/"README.md",ROOT/".runs/test-status.json")
if __name__=="__main__":
    unittest.main()
