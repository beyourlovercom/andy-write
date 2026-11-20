from __future__ import annotations
import unittest
from pathlib import Path
from andy_write.io import ROOT
from andy_write.media import plan_media, verify_media_manifest

class MediaTests(unittest.TestCase):
    def setUp(self):
        self.article = (ROOT/"examples/output/pairdoll-unboxing-gpt61-terra-review.md").read_text()
        self.job = {"job_id":"test-media"}

    def test_cover_plus_six_h2_images(self):
        plan = plan_media(self.job,self.article)
        self.assertEqual(len(plan["assets"]),7)
        self.assertEqual(len({r["id"] for r in plan["assets"]}),7)
        self.assertEqual(len({r["prompt"] for r in plan["assets"]}),7)
        self.assertEqual(plan["stage"],"R3_MEDIA_PLANNING_ONLY")

    def test_no_premature_alt_or_metadata(self):
        plan = plan_media(self.job,self.article)
        for a in plan["assets"]:
            self.assertIsNone(a["seo_metadata"]["alt"])
            self.assertIsNone(a["image_path"])
            self.assertEqual(a["visual_review"],"PENDING")
        self.assertEqual(verify_media_manifest(plan)["status"],"BLOCK")

    def test_duplicate_alt_is_rejected(self):
        plan = plan_media(self.job,self.article)
        for a in plan["assets"]:
            a["status"]="visual_verified"
            a["image_path"]="/tmp/image.png"
            a["image_sha256"]="fakehash"
            a["seo_metadata"]={k:"Generic description" for k in ("title","alt","caption","description")}
        result = verify_media_manifest(plan)
        self.assertEqual(result["status"],"BLOCK")
        self.assertIn("duplicate_alt", {v["problem"] for v in result["issues"]})

if __name__=="__main__":
    unittest.main()

class TestMediaVerifiedBytes(unittest.TestCase):
    def test_actual_file_and_visual_inspection_required(self):
        import tempfile,hashlib
        from pathlib import Path
        from andy_write.media import verify_media_manifest
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"image.png"
            path.write_bytes(b"test mock image bytes")
            item={
                "id":"cover","section":None,"status":"visual_verified",
                "image_path":str(path),
                "image_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "visual_review":{"reviewer":"UAT-human","reviewed_at":"2026-11-12"},
                "seo_metadata":{"title":"Box inspection","alt":"Shipping box on table",
                     "caption":"Check package condition","description":"Shipment before opening."}
            }
            self.assertEqual(verify_media_manifest({"assets":[item]})["status"],"READY")
            path.write_bytes(b"different bytes")
            result=verify_media_manifest({"assets":[item]})
            self.assertEqual(result["status"],"BLOCK")
            self.assertIn("image_checksum_mismatch",{i["problem"] for i in result["issues"]})
