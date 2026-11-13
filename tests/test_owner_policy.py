"""2026-11-13 Owner directives, tested without running Codex or generating media."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, patch
from andy_write import __main__ as cli
from andy_write.io import ROOT
from andy_write.usage_policy import (
    POLICY_VERSION, permit_codex_stage, block_media_generation,
    verified_source_article
)
from andy_write.codex_cli import run_model, invoke_stage, run_writing

class OwnerScopeRegression(unittest.TestCase):
    def test_generation_disabled_by_committed_policy(self):
        policy=json.loads((ROOT/"configs/policy.json").read_text())
        self.assertFalse(policy["image_generation_enabled"])
        self.assertFalse(policy["video_generation_enabled"])
        self.assertEqual(policy["codex_cli_allowed_purpose"],
                         "user_supplied_article_rewriting_only")
        for medium in ("image","video"):
            with self.assertRaises(PermissionError):
                block_media_generation(medium)

    def test_no_imagegen_module_or_cli_entrypoint(self):
        self.assertIsNone(importlib.util.find_spec("andy_write.imagegen_runner"))
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as event:
                cli.main(["media-generate", "--job", "examples/jobs/pairdoll-unboxing.json"])
        self.assertEqual(event.exception.code, 2)

    def test_only_rewrite_stages_permitted(self):
        for stage in ("rewrite","edit","quality-chapters-1","tighten-1"):
            permit_codex_stage(stage)
        for stage in ("imagegen","video","research","outline","qa",
                      "draft-from-topic","publish","code","search"):
            with self.subTest(stage=stage):
                with self.assertRaises(PermissionError):
                    permit_codex_stage(stage)

    def test_unknown_stage_never_invokes_model(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("andy_write.codex_cli.run_model") as model:
                with self.assertRaises(PermissionError):
                    invoke_stage({"job_id":"no-tools"}, "video",
                                 "Write a video", "gpt-6.1-terra",
                                 pathlib.Path(directory))
                model.assert_not_called()

    def test_codex_requires_source_even_if_prompt_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp)
            (d/"writing-prompt.md").write_text("Rewrite article")
            with patch("andy_write.codex_cli.outdir",return_value=d):
                with patch("andy_write.codex_cli.run_model") as model:
                    with self.assertRaisesRegex(PermissionError,"user-supplied"):
                        run_writing({"job_id":"job-without-original"})
                    model.assert_not_called()

    def test_original_source_must_be_substantive(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp)
            p=d/"source.md"
            p.write_text("One topic only")
            (d/"run-manifest.json").write_text(json.dumps({"source_sha256":"unused"}))
            with patch("andy_write.usage_policy.resolved",return_value=p):
                with self.assertRaisesRegex(PermissionError,"substantive"):
                    verified_source_article({"source_path":"source.md",
                         "source_url":"https://example.com/owner"},d)

    def test_codex_model_refuses_tool_action_even_on_completed_turn(self):
        events=[
            {"type":"thread.started"},
            {"type":"item.completed",
             "item":{"type":"command_execution","command":"cat file"}},
            {"type":"item.completed","item":{"type":"agent_message",
                    "text":"# Safe Article Rewrite\n\n"+"This is an existing article. "*120}},
            {"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":50}}
        ]
        process=Mock(returncode=0,stdout="\n".join(json.dumps(e) for e in events),stderr="")
        with patch("andy_write.codex_cli.codex_version",return_value=(0,167,2)):
            with patch("andy_write.codex_cli.subprocess.run",return_value=process):
                with self.assertRaisesRegex(RuntimeError,"Disallowed model tool action"):
                    run_model("gpt-6.1-terra","Rewrite supplied original",stage="edit")
        # No real CLI process was invoked; subprocess is mocked.

if __name__ == "__main__":
    unittest.main()
