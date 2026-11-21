"""Deterministic synthetic controls; these are NOT human editorial labels."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from andy_write.io import hashtext
from andy_write.qc_context import audit_public_context, audit_frozen_owner_draft
from andy_write.article_scope import VERSION as ARTICLE_SCOPE_VERSION


def source(html: str) -> dict:
    return {"id": 26268, "link": "https://example.test/adult-waterproof-toys",
            "modified": "2026-10-04T15:03:30", "content": {"rendered": html}}


def contract(post: dict) -> dict:
    return {
        "schema": "andy-write-context-qc-scope/v1", "benchmark_id": "synthetic-r9",
        "source": {"source_role": "public_competitor_qc_benchmark_only",
                   "post_id": post["id"], "url": post["link"],
                   "modified": post["modified"],
                   "rendered_content_sha256": hashtext(post["content"]["rendered"])},
        "scope": {"subject": "Adult shower intimacy", "primary_product_class": "adult toys",
                  "audience": "adults", "serp_intent_status": "UNASSESSABLE"},
        "off_scope_signals": [
            {"id": "wearable", "terms": ["health tracking", "5ATM", "smart ring"],
             "min_distinct": 2},
            {"id": "child", "terms": ["baby", "neck float", "children"],
             "min_distinct": 2}],
        "price_observed_at": None,
    }


class ContextQCTests(unittest.TestCase):
    def test_owner_frozen_draft_section_drift_is_manual_only(self):
        frozen = {"version": ARTICLE_SCOPE_VERSION, "status": "FROZEN",
                  "scope_fingerprint": "synthetic-fingerprint",
                  "scope": {"job_id": "fictional-owner-job",
                            "excluded_primary_products": ["torso"],
                            "allow_explicit_comparison": False}}
        prose = ("# Full-Size Doll Care\n\n"
                 "## Storage Recommendations\n\nThis torso is easier to store.\n\n"
                 "A torso can be kept on a compact shelf.\n\n"
                 "## Legitimate Caution\n\nUnlike a torso, a full-size product "
                 "can require more space.\n")
        result = audit_frozen_owner_draft(prose, frozen)
        self.assertEqual(result["summary"]["product_substitution_candidates"], 1)
        self.assertEqual(result["candidates"][0]["heading"], "Storage Recommendations")
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(result["publish_ready"])
        self.assertEqual(result["human_labels_present"], 0)
        frozen["scope"]["allow_explicit_comparison"] = True
        allowed = audit_frozen_owner_draft(prose, frozen)
        self.assertEqual(allowed["candidates"], [])

    def test_manual_draft_context_requires_actual_frozen_scope(self):
        with self.assertRaisesRegex(ValueError, "Actual frozen Owner"):
            audit_frozen_owner_draft("# Test\n", {"scope": {"job_id": "no"}})

    def test_repeated_h4_heading_keeps_parent_product_identity(self):
        html = (
            '<h2>Waterproof Products</h2>'
            '<h3>Wearable Rings</h3><h4>Pros and Cons</h4>'
            '<p>This health tracking product carries a 5ATM rating.</p>'
            '<h3>Other Products</h3><h4>Pros and Cons</h4>'
            '<p>This child accessory is for baby neck float lessons.</p>')
        post = source(html)
        result = audit_public_context(post, contract(post))
        flagged = [(c["heading"], c["anchor"]) for c in result["candidates"]
                   if c["priority"] == "P0"]
        self.assertEqual(flagged, [("Wearable Rings", "Wearable_Rings"),
                                   ("Other Products", "Other_Products")])

    def test_five_distinct_candidates_not_claimed_as_errors(self):
        html = (
            '<h2 id="Couples_Rings">Couples Rings</h2>'
            '<p>The metal wearable offers health tracking and 5ATM water resistance.</p>'
            '<h2 id="Safety_in_Wet_Environments">Safety in Wet Environments</h2>'
            '<p>Baby neck float reminders for children are included here.</p>'
            '<h2 id="Cleaning_and_Care">Cleaning and Care</h2>'
            '<p>Disinfect the toy with vinegar without checking its material.</p>'
            '<h2 id="Massage_Wands">Massage Wands</h2>'
            '<p>IPX7 waterproof construction permits 30 minutes submerged.</p>'
            '<h2 id="Suction_Toys">Suction Toys</h2>'
            '<table><tr><td>Limited Time Offer</td><td>$39</td></tr></table>')
        post = source(html)
        result = audit_public_context(post, contract(post))
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(result["summary"]["by_priority"], {"P0": 2, "P1": 2, "P2": 1})
        self.assertEqual(result["human_labels_present"], 0)
        self.assertIsNone(result["validated_truth_errors"])
        self.assertFalse(result["publish_ready"])
        self.assertEqual(len(result["candidates"]), 5)
        self.assertTrue(all(c["editorial_verdict"] == "NEEDS_HUMAN_REVIEW"
                            for c in result["candidates"]))
        rendered = json.dumps(result)
        self.assertNotIn("The metal wearable offers", rendered)
        self.assertNotIn("Disinfect the toy with", rendered)

    def test_legitimate_comparison_and_caution_not_automatically_flagged(self):
        html = (
            '<h2 id="scope">Product distinctions</h2><p>Unlike a health tracking '
            'ring with 5ATM, this product is an adult toy, not a wellness wearable.</p>'
            '<h2>How to choose</h2><p>Check the manufacturer manual for an IPX7 '
            'rating before use; do not assume a device can be submerged.</p>'
            '<h2>Products</h2><table><tr><td>Product model ABC</td><td>$45</td></tr></table>')
        post = source(html)
        scope = contract(post)
        scope["price_observed_at"] = "2026-11-20"
        result = audit_public_context(post, scope)
        self.assertEqual(result["summary"]["candidate_count"], 0)
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")

    def test_frozen_source_identity_and_role_fail_closed(self):
        post = source("<h2>Care</h2><p>Keep things clean.</p>")
        frozen = contract(post)
        for mutation in (lambda c: c["source"].update({"post_id": 1}),
                         lambda c: c["source"].update({"source_role": "owner_original"}),
                         lambda c: c["source"].update({"modified": "2025-12-26"}),
                         lambda c: c["source"].update({"rendered_content_sha256": "other"})):
            broken = deepcopy(frozen)
            mutation(broken)
            with self.assertRaisesRegex(ValueError, "R9_SOURCE_CONFLICT"):
                audit_public_context(post, broken)
        post["content"]["rendered"] += "changed"
        with self.assertRaisesRegex(ValueError, "R9_SOURCE_CONFLICT"):
            audit_public_context(post, frozen)

    def test_same_topic_without_off_scope_group_is_not_a_mismatch(self):
        post = source('<h2>Adult choices</h2><p>Comfort and preference are important.</p>')
        result = audit_public_context(post, contract(post))
        self.assertEqual(result["search_intent_verdict"], "UNASSESSABLE")
        self.assertEqual(result["candidates"], [])

    def test_actual_r8_contract_is_benchmark_only(self):
        path = Path("docs/r9_kissself_benchmark_scope.v1.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["source"]["source_role"],
                         "public_competitor_qc_benchmark_only")
        self.assertEqual(data["human_editorial_labels_present"], 0)
        self.assertEqual(data["source"]["post_id"], 26268)


if __name__ == "__main__":
    unittest.main()
