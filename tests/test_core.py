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
        for url in ["http://example.org", "https://localhost", "https://192.168.1.15", "https://user:secret@example.com", "file:///etc/passwd"]:
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

class TestFreeResearch(unittest.TestCase):
    def setUp(self):
        self.job = {"job_id": "test-free", "brand": "pairdoll",
                    "topic": "manual handling", "research_mode": "dc_free",
                    "research_urls": [], "queries": ["google test"],
                    "openalex_queries": ["manual handling ergonomics"]}

    def test_openalex_metadata_is_not_verified(self):
        from andy_write.discovery import parse_openalex
        raw = {"results": [
            {"title": "Ergonomics and lifting", "id": "https://openalex.org/W42",
             "doi": "https://doi.org/10.0000/example", "publication_date": "2025-01-01",
             "primary_location": {"landing_page_url": "https://publisher.example.org/works/42"}},
            {"title": "Blocked local work", "id": "https://127.0.0.1/W12"}]}
        records = parse_openalex(raw, "ergonomics")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "discovered_not_fetched")
        self.assertEqual(records[0]["verification"], "metadata_discovery_only")

    def test_keyless_openalex_http_mock(self):
        from andy_write.discovery import discover_openalex
        payload = {"results": [{"title": "A research paper",
            "id": "https://openalex.org/W99", "doi": "https://doi.org/10.0000/test"}]}
        with patch("andy_write.discovery.curl_read", return_value=(200, json.dumps(payload))) as get:
            result = discover_openalex(self.job)
        self.assertEqual(result["method"], "openalex_keyless_metadata_NOT_GOOGLE_SERP")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(get.call_count, 1)

    def test_dc_free_not_google_serp(self):
        with patch("andy_write.research.collect_curated", return_value={"sources": [], "collection_mode": "curated_url_fetch_NOT_SERP"}):
            with patch("andy_write.discovery.discover_openalex", return_value={
                "sources": [], "queries_executed": ["ergonomics"], "queries_failed": []}):
                p = research(self.job)
        self.assertIn("NOT_GOOGLE_SERP", p["collection_mode"])
        self.assertIsNone(p["organic_rankings"])
        self.assertEqual(p["queries_not_executed_google"], ["google test"])

    def test_cache_reuses_result_and_invalidates_changes(self):
        from andy_write.cache import cached_research
        import tempfile
        mock_response = {"retrieved_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
            "sources": [], "collection_mode": "dc_free_curated_plus_openalex_NOT_GOOGLE_SERP"}
        with tempfile.TemporaryDirectory() as folder:
            with patch("andy_write.cache.research", return_value=mock_response) as mock:
                dest = pathlib.Path(folder)
                first, hit_one = cached_research(self.job, dest)
                second, hit_two = cached_research(self.job, dest)
                third, hit_three = cached_research({**self.job, "topic": "changed"}, dest)
        self.assertFalse(hit_one)
        self.assertTrue(hit_two)
        self.assertFalse(hit_three)
        self.assertEqual(mock.call_count, 2)
