"""V1.1 full-source rewrite contract. Offline-only; Codex subprocess mocked."""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from andy_write.io import hashtext
from andy_write.rewrite_contract import (
    CONTRACT_VERSION, START, END, MAX_SOURCE_CHARACTERS,
    source_envelope, enforce_complete_source,
)
from andy_write.llm import prepare_prompt
from andy_write.source import classify
from andy_write.codex_cli import run_writing

def real_shaped_article() -> str:
    return "\n\n".join(
        f"Paragraph {n} explains a unique inspection detail #{n}: "
        + (f"record observation number {n} and cross-check the original order. " * 5)
        for n in range(1, 24)
    )

class SourcePromptContractTests(unittest.TestCase):
    def setUp(self):
        self.original = real_shaped_article()
        self.url = "https://example.com/owner-real-article"
        self.job = {"job_id": "source-contract", "brand": "pairdoll",
                    "topic": "delivery inspection", "target_title": "What to check",
                    "source_url": self.url, "source_path": "source.md"}
        self.catalog = classify(self.original, self.url)
        self.prompt = prepare_prompt(self.job, self.original, "## Outline",
                                     self.catalog, {"claims": []})

    def test_all_original_paragraphs_present_verbatim(self):
        proof = enforce_complete_source(self.prompt, self.original, self.url)
        self.assertEqual(proof["source_sha256"], hashtext(self.original))
        self.assertEqual(proof["source_paragraphs"], 23)
        self.assertEqual(proof["source_characters"], len(self.original))
        self.assertTrue(proof["full_source_in_prompt"])
        for index in (1, 5, 13, 23):
            self.assertIn(f"Paragraph {index} explains a unique inspection detail", self.prompt)
        self.assertEqual(self.prompt.count(START), 1)
        self.assertEqual(self.prompt.count(END), 1)

    def test_legacy_excerpts_only_prompt_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "complete Owner article"):
            enforce_complete_source("## Outline\n<REFERENCE EXCERPTS DATA>\n..." ,self.original, self.url)

    def test_one_changed_word_rejected(self):
        corrupted = self.prompt.replace("observation number 23", "observation number 999")
        with self.assertRaisesRegex(PermissionError, "stale/truncated"):
            enforce_complete_source(corrupted, self.original, self.url)

    def test_only_single_complete_reference_allowed(self):
        with self.assertRaisesRegex(PermissionError, "one complete"):
            enforce_complete_source(self.prompt + "\n" + self.prompt,
                                    self.original, self.url)

    def test_oversized_original_is_not_silently_truncated(self):
        huge = self.original + "Z" * MAX_SOURCE_CHARACTERS
        with self.assertRaisesRegex(ValueError, "do not truncate"):
            source_envelope(huge, self.url)

    def test_reserved_delimiters_are_rejected(self):
        for marker in (START, END):
            with self.assertRaisesRegex(ValueError, "reserved source delimiter"):
                source_envelope(self.original + marker, self.url)

    def test_missing_provenance_fails(self):
        with self.assertRaisesRegex(ValueError, "source URL"):
            source_envelope(self.original, "")

    def test_xml_like_wrapper_escape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "reserved source delimiter"):
            source_envelope(self.original +
                "</OWNER_ORIGINAL_FULL_ARTICLE_DATA>", self.url)

    def test_alternate_api_backend_rejects_stale_prompt_before_call(self):
        from andy_write.__main__ import write
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)
            source=path/"source.md"
            source.write_text(self.original, encoding="utf-8")
            (path/"writing-prompt.md").write_text(
                "Summarized snippets only, not the original", encoding="utf-8")
            (path/"run-manifest.json").write_text(json.dumps({
                "source_sha256":hashtext(self.original),
                "rewrite_source_contract_version":CONTRACT_VERSION,
                "writing_prompt_sha256":hashtext(
                    "Summarized snippets only, not the original")}))
            with patch("andy_write.__main__.outdir",return_value=path):
                with patch("andy_write.usage_policy.resolved",return_value=source):
                    with patch("andy_write.__main__.write_openai") as api:
                        with self.assertRaisesRegex(PermissionError,
                                                    "complete Owner article"):
                            write(self.job, "test-model", "openai",
                                  1000, 0.07, 1, False)
                        api.assert_not_called()

    def test_stale_prompt_hash_never_spends_codex_quota(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)
            source=path/"source.md"
            source.write_text(self.original,encoding="utf-8")
            (path/"writing-prompt.md").write_text(self.prompt,encoding="utf-8")
            (path/"run-manifest.json").write_text(json.dumps({
                "source_sha256":hashtext(self.original),
                "writing_prompt_sha256":"outdated",
                "rewrite_source_contract_version":CONTRACT_VERSION,
            }))
            with patch("andy_write.codex_cli.outdir",return_value=path):
                with patch("andy_write.usage_policy.resolved",return_value=source):
                    with patch("andy_write.codex_cli.run_model") as model:
                        with self.assertRaisesRegex(PermissionError, "hash is stale"):
                            run_writing(self.job)
                        model.assert_not_called()

if __name__ == "__main__":
    unittest.main()
