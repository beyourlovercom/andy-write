"""R7 Dev-only Search Intent contract bridge: offline, synthetic fixtures only."""
import copy
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from andy_write import search_intent_gate as gate


def fixture(*, evidence="verified", verdict="Unassessable", status="PASS"):
    results = [{"url": f"https://publisher{i}.example.com/guide", "title": f"Guide {i}",
                "page_type": "guide", "observed_rank": i, "seen_in": 3,
                "relevance": "on-topic"} for i in range(1, 7)]
    quality = {"capture_kind": "multiple-reads", "sample_runs": 3,
               "on_topic_count": 6, "stable_on_topic_count": 6, "final_url_count": 6,
               "official_brand_domain": None, "official_domain_verified": None}
    if evidence == "provisional":
        results = [{"url": "https://publisher.example.com/guide", "title": "Guide",
                    "page_type": "guide", "observed_rank": None}]
    return {
        "contract_version": "andy-write-search-intent/v1", "mode": "prebrief",
        "target_keyword": "full size doll care", "site": "pairdoll.com",
        "scope": {"audience": "adult owners", "market_country": "US", "language": "en",
                  "device": "mobile", "owner_scope_contract_id": "owner-fingerprint",
                  "owner_requirements_preserved": True},
        "evidence": {"status": evidence,
                     "method": "serp-export" if evidence == "verified" else "general-search",
                     "collected_at": "2026-11-19", "source_market_country": "US" if evidence == "verified" else None,
                     "source_language": "en" if evidence == "verified" else None,
                     "source_device": "mobile" if evidence == "verified" else None,
                     "limitations": [] if evidence == "verified" else ["Unlocalized search"],
                     "results": results,
                     "serp_features": {"ai_overview": "unknown"},
                     **({"quality": quality} if evidence == "verified" else {})},
        "intent": {"primary": "informational", "secondary": [],
                   "observed_page_type_counts": {"guide": len(results)},
                   "searcher_question": "How to care?", "buyer_stage": "learning",
                   "recommended_page_type": "guide", "must_cover": ["care"],
                   "next_click": "Read care details"},
        "audit": {"article_source": None, "article_page_type": None,
                  "verdict": verdict, "reason": "No article supplied in prebrief"},
        "recommendations": [], "gate": status,
        "approval_request": "Owner reviews intent and stage gating"}


class SearchIntentGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="andy-write-r7-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.out = self.root / ".runs" / "unit-job"
        self.out.mkdir(parents=True)
        self.owner = {"scope_fingerprint": "owner-fingerprint"}
        self.job = {"job_id": "unit-job", "target_keyword": "full size doll care",
                    "brand_domain": "pairdoll.com",
                    "search_intent_scope": {"audience": "adult owners", "market_country": "US",
                                            "language": "en", "device": "mobile"}}
        self.root_patch = patch.object(gate, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.env = patch.dict(os.environ, {gate.FLAG: "1", gate.ENV: "dev"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def save(self, data=None):
        (self.out / "intent_contract.json").write_text(
            json.dumps(fixture() if data is None else data), encoding="utf-8")
        (self.out / "intent_report.md").write_text("# QC evidence - test only\n", encoding="utf-8")

    def test_pass_and_retry_is_idempotent(self):
        self.save()
        self.assertEqual(gate.enforce(self.job, self.owner, self.out)["next_stage"], "SOURCE")
        gate.enforce(self.job, self.owner, self.out)
        self.assertEqual(len(list((self.out / "search-intent-decisions").glob("*.json"))), 1)
        self.assertFalse(json.loads((self.out / "search-intent-decision.json").read_text())["publish_ready"])

    def test_review_pauses(self):
        self.save(fixture(evidence="provisional", status="REVIEW"))
        with self.assertRaisesRegex(gate.SearchIntentGateError, "REVIEW"):
            gate.enforce(self.job, self.owner, self.out)
        self.assertEqual(json.loads((self.out / "search-intent-decision.json").read_text())["next_stage"], "STOP")

    def test_mismatch_blocks(self):
        data = fixture(status="BLOCK")
        data["mode"] = "audit"
        data["audit"] = {"article_source": "https://example.com/article",
                         "article_page_type": "product", "verdict": "Mismatch", "reason": "Wrong stage"}
        self.save(data)
        with self.assertRaisesRegex(gate.SearchIntentGateError, "BLOCK"):
            gate.enforce(self.job, self.owner, self.out)

    def test_provisional_cannot_fake_pass(self):
        self.save(fixture(evidence="provisional", status="PASS"))
        with self.assertRaisesRegex(gate.SearchIntentGateError, "validation failed"):
            gate.enforce(self.job, self.owner, self.out)

    def test_google_redirect_rejected(self):
        data = fixture()
        data["evidence"]["results"][0]["url"] = "https://google.com/goto?x=1"
        self.save(data)
        with self.assertRaisesRegex(gate.SearchIntentGateError, "SERP redirect"):
            gate.enforce(self.job, self.owner, self.out)

    def test_brand_lookalike_cannot_prove_official_domain(self):
        data = fixture()
        data["target_keyword"] = "realdoll official website"
        self.job["target_keyword"] = data["target_keyword"]
        data["evidence"]["quality"]["official_brand_domain"] = "lookalike.example.com"
        data["evidence"]["quality"]["official_domain_verified"] = True
        self.save(data)
        with self.assertRaisesRegex(gate.SearchIntentGateError, "official-domain"):
            gate.enforce(self.job, self.owner, self.out)

    def test_keyword_site_and_scope_mismatch(self):
        for field, value, expected_error in (
            ("target_keyword", "torso", "Target keyword"),
            ("site", "other.com", "Target site"),
        ):
            data = fixture()
            data[field] = value
            self.save(data)
            with self.subTest(field=field), self.assertRaisesRegex(gate.SearchIntentGateError, expected_error):
                gate.enforce(self.job, self.owner, self.out)
        data = fixture()
        data["scope"]["owner_scope_contract_id"] = "wrong-fingerprint"
        self.save(data)
        with self.assertRaisesRegex(gate.SearchIntentGateError, "fingerprint"):
            gate.enforce(self.job, self.owner, self.out)
        data = fixture()
        data["scope"]["device"] = "desktop"
        data["evidence"]["source_device"] = "desktop"
        self.save(data)
        with self.assertRaisesRegex(gate.SearchIntentGateError, "device"):
            gate.enforce(self.job, self.owner, self.out)

    def test_missing_or_invalid_artifacts_fail_closed(self):
        with self.assertRaisesRegex(gate.SearchIntentGateError, "required"):
            gate.enforce(self.job, self.owner, self.out)
        self.save()
        (self.out / "intent_contract.json").write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(gate.SearchIntentGateError, "invalid JSON"):
            gate.enforce(self.job, self.owner, self.out)

    def test_dev_only_and_off_by_default(self):
        with patch.dict(os.environ, {gate.FLAG: "0"}):
            self.assertFalse(gate.enabled())
        with patch.dict(os.environ, {gate.FLAG: "1", gate.ENV: "production"}):
            with self.assertRaisesRegex(gate.SearchIntentGateError, "only"):
                gate.enabled()

    def test_non_dev_configuration_stops_before_research(self):
        from andy_write import __main__ as cli
        with patch.dict(os.environ, {gate.FLAG: "1", gate.ENV: "production"}), \
             patch.object(cli, "cached_research") as collector:
            with self.assertRaisesRegex(gate.SearchIntentGateError, "only"):
                cli.run(self.job)
            collector.assert_not_called()

    def test_revisions_are_audited_not_overwritten(self):
        self.save(fixture(evidence="provisional", status="REVIEW"))
        with self.assertRaises(gate.SearchIntentGateError):
            gate.enforce(self.job, self.owner, self.out)
        self.save(fixture())
        self.assertEqual(gate.enforce(self.job, self.owner, self.out)["gate"], "PASS")
        self.assertEqual(len(list((self.out / "search-intent-decisions").glob("*.json"))), 2)

    def test_workflow_never_enters_source_after_review(self):
        from andy_write import __main__ as cli
        self.save(fixture(evidence="provisional", status="REVIEW"))
        original = self.root / "article.md"
        original.write_text("# Existing test article\n", encoding="utf-8")
        job = {**self.job, "source_path": "article.md", "source_url": "https://example.com/original"}
        pack = {"collection_mode": "fixture-not-serp", "sources": []}
        with patch.object(cli, "ensure_article_scope", return_value=self.owner), \
             patch.object(cli, "verify_article_input"), \
             patch.object(cli, "outdir", return_value=self.out), \
             patch.object(cli, "resolved", return_value=original), \
             patch.object(cli, "cached_research", return_value=(pack, True)), \
             patch.object(cli, "classify") as source:
            with self.assertRaises(gate.SearchIntentGateError):
                cli.run(job)
            source.assert_not_called()
        self.assertTrue((self.out / "research-pack.json").exists())
        self.assertFalse((self.out / "outline.md").exists())

    def test_stale_prior_pass_cannot_bypass_direct_write(self):
        from andy_write import __main__ as cli
        self.save()
        gate.enforce(self.job, self.owner, self.out)
        (self.out / "writing-prompt.md").write_text("stale approved prompt", encoding="utf-8")
        self.save(fixture(evidence="provisional", status="REVIEW"))
        with patch.object(cli, "ensure_article_scope", return_value=self.owner), \
             patch.object(cli, "verify_article_input"), \
             patch.object(cli, "outdir", return_value=self.out), \
             patch.object(cli, "run_writing") as writer:
            with self.assertRaisesRegex(gate.SearchIntentGateError, "REVIEW"):
                cli.write(self.job, None, "codex", 1000, 0.07, 1, False)
            writer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
