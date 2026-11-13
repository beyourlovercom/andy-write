"""Offline R3 asset import and QA regressions. No actual image generation."""
from __future__ import annotations
import json
import pathlib
import struct
import tempfile
import unittest
from unittest.mock import patch
from andy_write.media_workflow import import_observations, png_dimensions, review_ready
from andy_write.media_export import export_review_preview
from andy_write.io import ROOT
from andy_write.media import plan_media

ARTICLE=(ROOT/"examples/output/pairdoll-unboxing-editor-quality-v2.md").read_text(encoding="utf-8")
JOB={"job_id":"media-test","brand":"pairdoll"}

def png_stub() -> bytes:
    return (b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" +
            struct.pack(">II", 1672, 941) + b"\x08\x02\x00\x00\x00" + b"\x00"*1200)

def candidate(asset_id: str) -> dict:
    return {"id":asset_id, "filename":asset_id+".png", "tool_generated":True,
            "reviewer":"codex_image_vision_review",
            "observed_scene":"Box and phone on the table for shipping inspection",
            "matches_article_section":True, "mismatches":[],
            "visible_objects":["box","phone"],
            "seo_metadata":{
                "title":"Unique inspection scene "+asset_id,
                "alt":"Camera and carton seen for "+asset_id,
                "caption":"Inspection procedure for "+asset_id,
                "description":"Shipping box with phone camera in "+asset_id+" inspection scene."
            }}

class MediaWorkflowTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=pathlib.Path(tmp.name)
        (self.root/"media").mkdir()
        for ident in ("cover", *("h2-%02d"%i for i in range(1,7))):
            (self.root/"media"/(ident+".png")).write_bytes(png_stub())
        self.observations=[candidate(ident) for ident in ("cover", *("h2-%02d"%i for i in range(1,7)))]

    def test_generated_assets_need_owner_approval(self):
        with patch("andy_write.media_workflow.outdir",return_value=self.root):
            result=import_observations(JOB,ARTICLE,self.observations)
        self.assertEqual(result["status"],"READY_FOR_OWNER_REVIEW")
        self.assertFalse(result["publish_ready"])
        manifest=json.loads((self.root/"media-manifest.json").read_text())
        summary=review_ready(manifest)
        self.assertTrue(summary["review_ready"])
        self.assertFalse(summary["publish_ready"])
        self.assertEqual(len({a["seo_metadata"]["alt"] for a in manifest["assets"]}),7)

    def test_mismatched_image_rejected(self):
        self.observations[1]["matches_article_section"]=False
        with patch("andy_write.media_workflow.outdir",return_value=self.root):
            result=import_observations(JOB,ARTICLE,self.observations)
        self.assertEqual(result["status"],"PARTIAL")
        self.assertIn("h2-01",{x["id"] for x in result["rejected"]})

    def test_metadata_absent_is_rejected(self):
        self.observations[2]["seo_metadata"]["alt"]=""
        with patch("andy_write.media_workflow.outdir",return_value=self.root):
            result=import_observations(JOB,ARTICLE,self.observations)
        self.assertEqual(result["status"],"PARTIAL")

    def test_duplicate_alt_blocked(self):
        self.observations[2]["seo_metadata"]["alt"]=self.observations[1]["seo_metadata"]["alt"]
        with patch("andy_write.media_workflow.outdir",return_value=self.root):
            result=import_observations(JOB,ARTICLE,self.observations)
        self.assertEqual(result["status"],"PARTIAL")

    def test_partial_reviews_do_not_crash_readiness(self):
        manifest=plan_media(JOB,ARTICLE)
        self.assertFalse(review_ready(manifest)["review_ready"])

    def test_invalid_png_dimensions_rejected(self):
        bad=self.root/"media"/"h2-03.png"
        bad.write_text("not a PNG")
        with patch("andy_write.media_workflow.outdir",return_value=self.root):
            result=import_observations(JOB,ARTICLE,self.observations)
        self.assertEqual(result["status"],"PARTIAL")
        self.assertIn("h2-03",{x["id"] for x in result["rejected"]})

    def test_no_review_export_if_images_missing(self):
        (self.root/"media-manifest.json").write_text(
            json.dumps(plan_media(JOB,ARTICLE)),encoding="utf-8")
        with patch("andy_write.media_export.outdir",return_value=self.root):
            with self.assertRaisesRegex(RuntimeError,"missing or rejected images"):
                # cwebp availability is mocked: only QA should matter
                with patch("andy_write.media_export.shutil.which",return_value="/usr/bin/cwebp"):
                    export_review_preview(JOB,ARTICLE)

if __name__=="__main__":
    unittest.main()
