"""Offline assertions: source gate, search labeling, article QA and outline contracts."""
from __future__ import annotations
import os
import json
import pathlib
import unittest
from unittest.mock import patch
from andy_write.io import hashtext, resolved, read_job, ROOT
from andy_write.research import research, validate_public_url
from andy_write.source import classify, evidence, topic_for
from andy_write.outline import section_plan, markdown_outline
from andy_write.review import check
from andy_write.llm import write_openai

EXAMPLE = "examples/jobs/pairdoll-unboxing.json"

class TestAndyWrite(unittest.TestCase):
    def setUp(self):
        self.job = json.loads((ROOT / EXAMPLE).read_text(encoding="utf-8"))
        self.ref = """## Arrival
A shipping confirmation and tracking number show arrival time.

## Unboxing
Open the box carefully, keep the foam, and inspect the accessories.

## Inspection
Look for damage and take photographs for support.

## Cleaning
Care routines must follow manufacturer instructions."""
        self.catalog = classify(self.ref, self.job["source_url"])
        self.ledger = evidence({"sources": [
            {"id": "SRC-WEB-001", "url": "https://consumer.ftc.gov/articles/online-shopping", "status": "retrieved"},
            {"id": "SRC-WEB-002", "url": "https://www.cdc.gov/niosh/ergonomics/", "status": "retrieved"}]},
            self.catalog)

    def test_source_required_by_brand(self):
        self.assertEqual(self.job["brand"], "pairdoll")
        self.assertIn("protected_existing_post_ids", self.job)
        with patch("andy_write.io.resolved", return_value=pathlib.Path("/no-existing/notion-source.md")):
            with self.assertRaisesRegex(RuntimeError, "User-supplied reference is required"):
                read_job(EXAMPLE)

    def test_source_hash_is_stable(self):
        self.assertEqual(hashtext(self.ref), hashtext(self.ref))
        self.assertNotEqual(hashtext(self.ref), hashtext(self.ref+"x"))

    def test_source_topic_classification(self):
        self.assertEqual(topic_for("The cleaning instructions advise washing and drying"), "cleaning")
        self.assertEqual(topic_for("Inspect for damage and tears on the skin"), "inspection")

    def test_evidence_not_automatically_verified(self):
        self.assertEqual(self.ledger["claims"][0]["status"], "needs_editorial_verification")
        self.assertEqual(self.ledger["claims"][1]["status"], "needs_editorial_verification")

    def test_outline_has_expected_h2s(self):
        items = section_plan(self.job, self.catalog)
        outline = markdown_outline(self.job, items, self.ledger)
        self.assertEqual(len(items), 6)
        self.assertEqual(outline.count("\n## "), 11)  # intro, toc, claim, 6 H2, conclusion, link plan
        self.assertIn("[image", outline)
        self.assertIn("[Claim:", outline)
        for section in items:
            self.assertTrue(section["heading"].endswith("?"))

    def test_serpapi_key_required(self):
        j = {**self.job, "research_mode": "serpapi"}
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "SERPAPI_API_KEY absent"):
                research(j)

    def test_curated_is_not_serp(self):
        j = {**self.job, "research_mode": "curated", "research_urls": []}
        self.assertEqual(research(j)["collection_mode"], "curated_url_fetch_NOT_SERP")

    def test_reject_non_public_urls(self):
        for url in ["http://example.org", "https://localhost", "https://192.168.1.15", "file:///etc/passwd"]:
            with self.assertRaises(ValueError):
                validate_public_url(url)

    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            resolved("../../etc/passwd")

    def test_editorial_leak_blocked(self):
        result = check("# Test\n\n## Question?\n\nEditorial image placement 1: TODO:\n\n## Conclusion\n\nEnd.", self.job)
        self.assertEqual(result["status"], "BLOCK")

    def test_unverified_first_person_flag(self):
        result = check("# Test\n\n## Question?\n\nI personally tested this item.\n\n## Conclusion\n\nEnd.", self.job)
        self.assertEqual(result["status"], "REVIEW")

    def test_no_claim_placeholder_in_prose(self):
        result = check("# Test\n\n[Claim: XXX]\n\n## Conclusion\n\nEnd.", self.job)
        self.assertEqual(result["status"], "BLOCK")

    def test_no_model_key_means_no_fake_draft(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY absent"):
                write_openai("Test")

if __name__ == "__main__":
    unittest.main()
