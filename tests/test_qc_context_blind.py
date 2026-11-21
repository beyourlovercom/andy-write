"""Only SYNTHETIC blind-workflow fixtures; never fake real editor labels."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

from andy_write.io import hashtext
from andy_write.qc_context_blind import (
    blank_pair_review, blank_source_review, build_blind_pairs,
    build_source_packet, render_pair_workbench, render_source_workbench,
    score_blind_review, seal_source_gold,
)
from scripts.r12_blind_qc import private_path


def case(pid: int):
    html = ("<h2 id='a'>Product A</h2><p>Explicit model M-2 is IPX7 waterproof.</p>"
            "<h2 id='b'>Product B</h2><p>Generic safe care directions.</p>")
    source = {"id": pid, "link": f"https://test.invalid/{pid}",
              "modified": "2026-11-21T00:00:00", "content": {"rendered": html}}
    scope = {"schema": "andy-write-context-qc-scope/v1", "benchmark_id": f"B-{pid}",
             "source": {"source_role": "public_competitor_qc_benchmark_only",
                        "post_id": pid, "url": source["link"],
                        "modified": source["modified"], "rendered_content_sha256": hashtext(html)},
             "scope": {"subject": "testing", "primary_product_class": "adult goods",
                       "audience": "adults", "serp_intent_status": "UNASSESSABLE"},
             "off_scope_signals": [{"id": "OTHER", "terms": ["baby", "children"], "min_distinct": 2}]}
    return source, scope


def report(source, scope, *, upgraded=False, with_candidate=True):
    candidates = []
    if with_candidate:
        candidates.append({"heading": "Product A", "anchor": "a",
                           "code": "MODEL_SPEC_PROVENANCE_REVIEW", "priority": "P1",
                           "reason": "Specific model attribution requires manufacturer passage",
                           "signal_terms": ["device-water-or-battery-spec"],
                           "editorial_verdict": "NEEDS_HUMAN_REVIEW", "verified_fact_error": False,
                           **({"review_details": {"manufacturer_passage_verified": False}}
                              if upgraded else {})})
    return {"source_url": source["link"], "source_post_id": source["id"],
            "source_modified": source["modified"],
            "source_content_sha256": scope["source"]["rendered_content_sha256"],
            "source_role": "public_competitor_qc_benchmark_only",
            "benchmark_id": scope["benchmark_id"],
            "status": "HUMAN_REVIEW_REQUIRED", "publish_ready": False,
            "human_labels_present": 0, "validated_truth_errors": None,
            "candidates": candidates}


def human_source(packet, name, *, disagreement=False):
    review = blank_source_review(packet)
    review["reviewer_id"] = name
    for section in review["sections"]:
        if section["id"] == packet["sections"][0]["id"]:
            section["issue_codes"] = [] if disagreement else ["MODEL_SPEC_PROVENANCE_REVIEW"]
            section["rationale"] = None if disagreement else "Specific model needs exact manufacturer manual"
        else:
            section["issue_codes"] = []
    return review


class BlindContextTests(unittest.TestCase):
    def setUp(self):
        self.cases = [case(11), case(22)]
        self.packet = build_source_packet(self.cases)
        self.a = human_source(self.packet, "Editor One")
        self.b = human_source(self.packet, "Editor Two")

    def test_source_first_packet_has_no_machine_alerts_or_version(self):
        self.assertEqual(len(self.packet["sources"]), 2)
        self.assertEqual(len(self.packet["sections"]), 4)
        self.assertNotIn('"candidates"', json.dumps(self.packet).lower())
        self.assertNotIn("R11", json.dumps(self.packet))
        self.assertEqual(self.packet["human_labels_present"], 0)

    def test_source_modified_or_hash_changed_fails_closed(self):
        source, contract = deepcopy(self.cases[0])
        source["content"]["rendered"] += "tampered"
        with self.assertRaisesRegex(ValueError, "R9_SOURCE_CONFLICT"):
            build_source_packet([(source, contract), self.cases[1]])

    def test_offline_source_form_exposes_no_machine_version_or_auto_labels(self):
        html = render_source_workbench(self.packet)
        self.assertIn("离线", html)
        self.assertIn("reviewed", html)
        self.assertNotIn('"R11"', html)
        self.assertNotIn('"candidates":', html)

    def test_offline_pair_form_contains_no_sealed_version_map(self):
        gold = seal_source_gold(self.packet, self.a, self.b)
        reps = [(report(s, c), report(s, c, upgraded=True)) for s, c in self.cases]
        blind, mapping = build_blind_pairs(self.packet, gold, reps)
        html = render_pair_workbench(blind)
        self.assertIn("匿名提醒", html)
        self.assertNotIn('"baseline"', html)
        self.assertNotIn('"upgraded"', html)
        self.assertIn("PRIVATE_EVALUATOR_ONLY", json.dumps(mapping))

    def test_unlabeled_template_and_same_editor_rejected(self):
        with self.assertRaisesRegex(ValueError, "reviewer identity"):
            seal_source_gold(self.packet, blank_source_review(self.packet), self.b)
        with self.assertRaisesRegex(ValueError, "distinct"):
            seal_source_gold(self.packet, self.a, {**self.b, "reviewer_id": "editor one"})

    def test_incomplete_positive_rationale_rejected(self):
        review = deepcopy(self.a)
        review["sections"][0]["rationale"] = "short"
        with self.assertRaisesRegex(ValueError, "rationale"):
            seal_source_gold(self.packet, review, self.b)

    def test_disagreement_requires_owner_and_full_matching_adjudication(self):
        other = human_source(self.packet, "Editor Two", disagreement=True)
        with self.assertRaisesRegex(ValueError, "OWNER_ADJUDICATION_REQUIRED"):
            seal_source_gold(self.packet, self.a, other)
        issue_id = self.packet["sections"][0]["id"]
        gold = seal_source_gold(self.packet, self.a, other,
                                {"owner_id": "Owner", "source_lock": self.packet["source_lock"],
                                 "decisions": {issue_id: ["MODEL_SPEC_PROVENANCE_REVIEW"]}})
        self.assertTrue(gold["owner_adjudicated"])
        self.assertEqual(gold["disagreement_count"], 1)

    def test_pair_pack_requires_sealed_independent_gold(self):
        reps = [(report(s, c), report(s, c, upgraded=True)) for s, c in self.cases]
        with self.assertRaisesRegex(ValueError, "Seal complete"):
            build_blind_pairs(self.packet, {"source_lock": self.packet["source_lock"]}, reps)

    def test_real_two_stage_blind_score_with_synthetic_human_annotations(self):
        gold = seal_source_gold(self.packet, self.a, self.b)
        reps = [(report(s, c), report(s, c, upgraded=True)) for s, c in self.cases]
        blind, sealed = build_blind_pairs(self.packet, gold, reps)
        self.assertEqual(len(blind["pairs"]), 2)
        self.assertNotIn("baseline", json.dumps(blind))
        self.assertNotIn("upgraded", json.dumps(blind))
        self.assertEqual(set(sealed["mapping"]), {p["id"] for p in blind["pairs"]})
        ra, rb = blank_pair_review(blind), blank_pair_review(blind)
        ra["reviewer_id"], rb["reviewer_id"] = "Editor Three", "Editor Four"
        for rev in (ra, rb):
            for row in rev["pairs"]:
                row["left_actionability"] = 2
                row["right_actionability"] = 3
        score = score_blind_review(blind, sealed, gold, ra, rb)
        self.assertEqual(score["source_section_count"], 4)
        self.assertEqual(score["review_opportunity_confusion"]["baseline"],
                         score["review_opportunity_confusion"]["upgraded"])
        self.assertEqual(score["review_opportunity_confusion"]["baseline"]["tp"], 1)
        self.assertEqual(score["review_opportunity_confusion"]["baseline"]["fp"], 1)
        self.assertIsNone(score["true_factual_error_count"])
        self.assertFalse(score["publish_ready"])

    def test_missing_or_duplicate_pair_ratings_cannot_score(self):
        gold = seal_source_gold(self.packet, self.a, self.b)
        reps = [(report(s, c), report(s, c, upgraded=True)) for s, c in self.cases]
        blind, mapping = build_blind_pairs(self.packet, gold, reps)
        ra, rb = blank_pair_review(blind), blank_pair_review(blind)
        ra["reviewer_id"], rb["reviewer_id"] = "Editor Three", "Editor Four"
        for rev in (ra, rb):
            for row in rev["pairs"]:
                row["left_actionability"] = 2
                row["right_actionability"] = 3
        rb["pairs"][0]["right_actionability"] = None
        with self.assertRaisesRegex(ValueError, "grades"):
            score_blind_review(blind, mapping, gold, ra, rb)

    def test_missing_prediction_is_counted_as_fn_not_ignored(self):
        gold = seal_source_gold(self.packet, self.a, self.b)
        reps = [(report(s, c, with_candidate=False), report(s, c, upgraded=True))
                for s, c in self.cases]
        blind, mapping = build_blind_pairs(self.packet, gold, reps)
        ra, rb = blank_pair_review(blind), blank_pair_review(blind)
        ra["reviewer_id"], rb["reviewer_id"] = "Editor Three", "Editor Four"
        for rev in (ra, rb):
            for row in rev["pairs"]:
                row["left_actionability"] = 1
                row["right_actionability"] = 3
        score = score_blind_review(blind, mapping, gold, ra, rb)
        self.assertEqual(score["review_opportunity_confusion"]["baseline"]["fn"], 1)

    def test_public_export_refused(self):
        with self.assertRaises(PermissionError):
            private_path("/workspace/scratch/exposed-source-only.json")


if __name__ == "__main__":
    unittest.main()
