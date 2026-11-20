"""Deterministic synthetic controls; these are NOT human editorial labels."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from andy_write.io import hashtext
from andy_write.qc_context import audit_public_context


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
