"""Offline R2 Codex CLI tests: no subscription usage, no network access."""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from andy_write.codex_cli import (
    DEFAULT_MODEL, append_ledger, codex_version, invoke_stage, run_writing,
    summarize_usage, word_count, word_range
)

def article(length=1):
    paragraphs = [
        f"The delivery checklist for section {n} should document order details and "
        f"packaging condition. Keep a careful record of visible damage, identify "
        f"missing components, and ask the seller for instructions before any repair "
        f"or material-specific cleaning steps. This advice is practical and avoids "
        f"assuming that all doll models have the same parts or care requirements."
        for n in range(6)
    ]
    names = [
        "What should you prepare before arrival?",
        "What should you check on the shipping carton?",
        "How can you unpack safely?",
        "What belongs in the inspection checklist?",
        "What if you find damage?",
        "When is the first cleaning appropriate?",
    ]
    return "# Safe Unboxing\n\n" + "\n\n".join(
        "## " + h + "\n\n" + paragraphs[i] * length
        for i, h in enumerate(names)
    ) + "\n\n## Conclusion\n\nDocument observations before beginning setup."

def fake_result(text):
    return text, {
        "model": DEFAULT_MODEL, "input_tokens": 1011,
        "cached_input_tokens": 500, "output_tokens": 105,
        "reasoning_output_tokens": 15, "visible_english_words": word_count(text),
        "provider": "codex_cli_chatgpt_subscription",
    }, '{"type":"turn.completed"}\n', ""

class TestR2Codex(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = pathlib.Path(self.temp.name)
        (self.directory / "writing-prompt.md").write_text(
            "Create a source-grounded checklist based on a supplied article.")
        self.source = self.directory / "owner-source.md"
        self.source.write_text(article(length=2),encoding="utf-8")
        from andy_write.io import hashtext
        (self.directory/"run-manifest.json").write_text(
            json.dumps({"source_sha256":hashtext(self.source.read_text(encoding="utf-8"))}))
        self.job = {"job_id": "test-unboxing", "brand": "pairdoll",
                    "source_path": "owner-source.md",
                    "source_url": "https://example.com/owner-article"}
        resolver = patch("andy_write.usage_policy.resolved",return_value=self.source)
        resolver.start()
        self.addCleanup(resolver.stop)

    def test_model_is_gpt61_and_version_gate(self):
        self.assertEqual(DEFAULT_MODEL, "gpt-6.1-terra")
        self.assertLess((0, 149, 0), (0, 159, 0))
        self.assertEqual(word_range(1000, 0.07), (930, 1070))

    def test_invalid_word_budget(self):
        for target, tolerance in [(100, 0.07), (1000, -0.01), (1000, 0.23)]:
            with self.assertRaises(ValueError):
                word_range(target, tolerance)

    def test_idempotent_run_and_usage_ledger(self):
        body = article()
        words = word_count(body)
        self.assertGreater(words, 250)
        with patch("andy_write.codex_cli.outdir", return_value=self.directory):
            with patch("andy_write.codex_cli.run_model",
                       return_value=fake_result(body)) as api:
                first = run_writing(self.job, target=words, tolerance=0.05)
                second = run_writing(self.job, target=words, tolerance=0.05)
        self.assertEqual(first["status"], "RULE_CHECK_PASS")
        self.assertEqual(api.call_count, 2)  # first draft and edit, no re-call
        self.assertEqual(second["cache_hits"], {"rewrite": True, "edit": True})
        use = summarize_usage(self.directory)
        self.assertEqual(use["calls_completed"], 2)
        self.assertEqual(use["totals"]["input_tokens"], 2022)
        self.assertEqual(use["totals"]["cached_input_tokens"], 1000)
        self.assertEqual(use["totals"]["output_tokens"], 210)

    def test_word_control_requests_one_extra_revision(self):
        good = article()
        long = article(length=2)
        desired = word_count(good)
        with patch("andy_write.codex_cli.outdir", return_value=self.directory):
            with patch("andy_write.codex_cli.run_model",
                       side_effect=[fake_result(long), fake_result(long), fake_result(good)]) as api:
                result = run_writing(self.job, target=desired,
                                     tolerance=0.04, max_revisions=1)
        self.assertEqual(api.call_count, 3)
        self.assertEqual(result["status"], "RULE_CHECK_PASS")
        self.assertEqual(result["last_stage"], "tighten-1")
        self.assertEqual(summarize_usage(self.directory)["calls_completed"], 3)

    def test_failed_model_call_is_not_success(self):
        with patch("andy_write.codex_cli.run_model",
                   side_effect=RuntimeError("Quota exhausted")):
            with self.assertRaisesRegex(RuntimeError, "Quota exhausted"):
                invoke_stage(self.job, "rewrite", "prompt", DEFAULT_MODEL, self.directory)
        data = summarize_usage(self.directory)
        self.assertEqual(data["calls_failed"], 1)
        self.assertEqual(data["calls_completed"], 0)
        self.assertFalse((self.directory / "article-auto-rewrite.md").exists())

    def test_ledger_does_not_double_count_cached_stage(self):
        body = article()
        with patch("andy_write.codex_cli.run_model",
                   return_value=fake_result(body)) as api:
            invoke_stage(self.job, "rewrite", "prompt", DEFAULT_MODEL, self.directory)
            invoke_stage(self.job, "rewrite", "prompt", DEFAULT_MODEL, self.directory)
        self.assertEqual(api.call_count, 1)
        self.assertEqual(summarize_usage(self.directory)["calls_completed"], 1)

if __name__ == "__main__":
    unittest.main()

class TestReferenceVersionGuard(unittest.TestCase):
    def test_source_changed_requires_research_rerun(self):
        from andy_write.codex_cli import run_writing
        from andy_write.io import hashtext
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            f = d / "source.md"
            f.write_text(article(length=2), encoding="utf-8")
            (d / "writing-prompt.md").write_text("previous text")
            (d / "run-manifest.json").write_text(json.dumps({
                "source_sha256": hashtext("old reference")}))
            job = {"job_id": "guard-test", "brand": "pairdoll",
                   "source_path": "fake-source", "source_url": "https://example.com/owner"}
            with patch("andy_write.codex_cli.outdir", return_value=d):
                with patch("andy_write.usage_policy.resolved", return_value=f):
                    with patch("andy_write.codex_cli.run_model") as model:
                        with self.assertRaisesRegex(PermissionError, "Source changed"):
                            run_writing(job)
                        model.assert_not_called()
