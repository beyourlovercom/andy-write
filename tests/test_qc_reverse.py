"""Public WP QC benchmarking is a no-model, no-article-copy workflow."""
from __future__ import annotations
import json
import pathlib
import unittest
from andy_write.qc_reverse import (
    html_qc_profile, markdown_qc_profile, compare_structure,
    skill_gap_actions, score_paragraph_risks, classify_links,
)

def article_html() -> str:
    paragraph=("A waterproof toy may need a model-specific water rating. "
               "Read the manufacturer manual before cleaning. "
               "Always check the material and connector before use. "
               "The retailer does not verify the battery or warranty. ")
    return (
        "<h2>Key Takeaways</h2><p>"+paragraph*5+"</p>"
        "<h2>Choosing a Device</h2><h3>Safety Rating</h3>"
        "<p>"+paragraph*5+"</p>"
        "<ul><li>Check model rating</li><li>Keep original instructions</li></ul>"
        "<table><tr><th>Rating</th><th>Scope</th></tr>"
        "<tr><td>IPX7</td><td>See manufacturer</td></tr></table>"
        "<img src='/file.webp' alt='Sealed waterproof device on table' />"
        "<img src='/empty.webp' alt='' />"
        "<a href='https://example.com/evidence'>Evidence</a>"
        "<a href='https://kissself.com/guide.html'>Related</a>"
        "<h2>FAQ</h2><p>"+paragraph*5+"</p>"
    )

class ReverseQcTests(unittest.TestCase):
    def setUp(self):
        self.doc=html_qc_profile(article_html(),
                 url="https://kissself.com/example.html",
                 date="2025-12-26T12:00:00",
                 modified="2026-10-04T12:00:00",
                 article_id=42)

    def test_real_public_meta_no_time_machine(self):
        self.assertEqual(self.doc["original_publication_date"][:4],"2025")
        self.assertFalse(self.doc["original_2025_snapshot_verified"])
        self.assertTrue(self.doc["derived_only"])

    def test_structural_counts(self):
        d=self.doc["structure"]
        self.assertEqual(d["h2_count"],3)
        self.assertEqual(d["h3_count"],1)
        self.assertEqual(d["table_count"],1)
        self.assertEqual(d["images_count"],2)
        self.assertEqual(d["images_with_nonempty_alt"],1)
        self.assertTrue(d["faq_heading_present"])
        self.assertTrue(d["key_takeaways_heading_present"])

    def test_real_links_count_but_not_called_citations(self):
        link=self.doc["links"]
        self.assertEqual(link["internal_link_instances"],1)
        self.assertEqual(link["external_link_instances"],1)
        self.assertEqual(link["unique_external_domains"],1)
        self.assertNotIn("verified_sources",link)

    def test_claim_flags_not_fake_news_judgement(self):
        risks=self.doc["risk_review"]
        self.assertGreater(risks["flagged_paragraph_count"],0)
        self.assertIn("MATERIAL_SAFETY_REVIEW",risks["reason_counts"])
        self.assertIn("UNIVERSAL_CLAIM_REVIEW",risks["reason_counts"])
        self.assertIn("not verified false claims",risks["warning"])

    def test_do_not_commit_full_competitor_article_body(self):
        s=json.dumps(self.doc)
        self.assertNotIn("Read the manufacturer manual before cleaning",s)
        self.assertNotIn("The retailer does not verify the battery",s)
        self.assertIn("source_content_sha256",s)

    def test_existing_draft_comparison_is_not_quality_ranking(self):
        ours=markdown_qc_profile(
            "# Existing article\n\nIntroduction.\n\n## What should I check?\n\n"
            "Inspect the order details and compare care instructions.\n\n"
            "## Conclusion\n\nFollow the verified manual.",
            source_label="https://pairdoll.com/guide/")
        comp=compare_structure(self.doc,ours)
        self.assertEqual(comp["comparison_type"],"STRUCTURAL_ONLY_NOT_QUALITY_OR_RANKING")
        self.assertIn("Different topics",comp["important_context"])
        self.assertEqual(ours["structure"]["images_count"],0)
        ids=[x["id"] for x in skill_gap_actions(self.doc,ours)]
        self.assertIn("QC_PRODUCT_SPEC_SCOPE",ids)
        self.assertIn("QC_CONDITIONAL_STRUCTURE",ids)
        self.assertIn("QC_MEDIA_POLICY",ids)

    def test_structure_only_cannot_force_h3_count(self):
        ours=markdown_qc_profile("# S\n\n## Q?\n\nAdvice and context.",source_label="https://pairdoll.com/")
        actions=skill_gap_actions(self.doc,ours)
        action=next(a for a in actions if a["id"]=="QC_CONDITIONAL_STRUCTURE")
        self.assertIn("no numeric quota",action["acceptance_gate"].lower())

    def test_short_or_nonpublic_article_rejected(self):
        with self.assertRaises(ValueError):
            html_qc_profile("<p>Only one brief sentence</p>",
               url="https://kissself.com/a",date="2025-12-01",modified="")
        with self.assertRaises(ValueError):
            html_qc_profile(article_html(),
               url="http://kissself.com/a",date="2025-12-01",modified="")

    def test_material_review_flag_not_equivalent_to_error(self):
        r=score_paragraph_risks(["Always check cleaning instructions for IPX7 devices"])
        self.assertEqual(r["flagged_paragraph_count"],1)
        self.assertNotIn("is_false",r)

if __name__=="__main__":
    unittest.main()
