"""No-quota offline test of Codex built-in image generation orchestration."""
from __future__ import annotations
import json
import pathlib
import struct
import tempfile
import unittest
from unittest.mock import patch
from andy_write.imagegen_runner import run_imagegen, build_batch_prompt
from andy_write.media import plan_media
from andy_write.io import ROOT

ARTICLE=(ROOT/"examples/output/pairdoll-unboxing-editor-quality-v2.md").read_text()
JOB={"job_id":"media-runner-test"}

class ImagegenRunnerTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=pathlib.Path(tmp.name)
        self.media=self.root/"media"
        self.media.mkdir()
        self.plan=plan_media(JOB, ARTICLE)
        (self.root/"media-manifest.json").write_text(json.dumps(self.plan))
        self.image_header=(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR"
                           + struct.pack(">II",1672,941) + b"\x08\x02\x00\x00\x00")

    def test_cache_reuses_all_seven_real_images(self):
        observations=[]
        for asset in self.plan["assets"]:
            (self.media/(asset["id"]+".png")).write_bytes(self.image_header+b"\x00"*400)
            observations.append({"id":asset["id"],"tool_generated":True,
                                 "reviewer":"codex_image_vision_review",
                                 "matches_article_section":True,"mismatches":[]})
        (self.media/"visual-observations.json").write_text(json.dumps(observations))
        with patch("andy_write.imagegen_runner.outdir",return_value=self.root):
            with patch("andy_write.imagegen_runner.subprocess.run") as model:
                result=run_imagegen(JOB,ARTICLE)
                model.assert_not_called()
        self.assertEqual(result["status"],"CACHE_HIT")
        self.assertEqual(result["model_calls"],0)
        self.assertEqual(result["images_cached"],7)

    def test_unverified_existing_image_never_overwritten(self):
        (self.media/"cover.png").write_bytes(self.image_header+b"\x00"*400)
        with patch("andy_write.imagegen_runner.outdir",return_value=self.root):
            with self.assertRaisesRegex(RuntimeError,"Unverified existing image"):
                run_imagegen(JOB,ARTICLE)

    def test_separate_prompts_and_no_file_substitutes(self):
        prompt=build_batch_prompt(JOB,self.plan,self.plan["assets"],self.media)
        self.assertEqual(prompt.count("save="),7)
        self.assertIn("BUILT-IN Codex ImageGen",prompt)
        self.assertIn("Do not use SVG",prompt)

    def test_unsupported_model_fails_without_consuming_quota(self):
        with self.assertRaisesRegex(ValueError,"verified GPT-6.1 Terra"):
            run_imagegen(JOB,ARTICLE,model="gpt-5.6-luna")

if __name__=="__main__":
    unittest.main()
