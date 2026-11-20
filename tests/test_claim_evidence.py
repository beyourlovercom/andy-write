"""Exact source relevance and human-entailment safety gates."""
from __future__ import annotations
import json
import unittest
from andy_write.claim_evidence import (
    sentences,find_candidates,trace_claims,validate_sources,
    apply_human_claim_reviews,CLAIM_REVIEW_DECLARATION,claim_review_sheet
)
from andy_write.io import hashtext,now

ORIGINAL=("\n\n".join([
    ("This Owner reference discusses carrying bulky delivered parcels. "
     "Keep a copy of the seller receipt and inspect the packaging. "
     "Compare the actual order confirmation, and note visible changes. ")*5,
    ("The original says to follow the actual manufacturer material care instructions. "
     "Do not assume accessories or cleansers are compatible for every product. "
     "Check labeling before any rinse or storage. ")*5,
]))
def external(url:str,text:str)->dict:
    return {"url":url,"retrieved_at":"2026-11-13T14:00:00+09:00",
            "retrieval_status":"retrieved","source_kind":"public_web_retrieval",
            "retrieval_channel":"direct_read_only_html",
            "body_sha256":hashtext(text),"paragraphs":[text]}
class EvidenceTests(unittest.TestCase):
    def test_actual_public_source_relevance_is_a_candidate_not_a_pass(self):
        claim="Keep records of purchases such as receipts and emails."
        record=external("https://consumer.ftc.gov/articles/online-shopping",
                        "Keep records of purchases, like receipts and emails, to make sure you can hold a seller to its promises.")
        result=find_candidates(claim,[record])
        self.assertTrue(result)
        self.assertEqual(result[0]["semantic_support_verified"],False)
        self.assertIn("NEEDS_ENTAILMENT",result[0]["risk_state"])
    def test_unrelated_government_domain_does_not_support_material_rating(self):
        claim="This silicone product has an IPX7 waterproof rating."
        record=external("https://www.cdc.gov/niosh/ergonomics/",
                        "Use assistive lifting devices to prevent injuries and reduce lifting risks.")
        self.assertEqual(find_candidates(claim,[record]),[])
    def test_exact_source_wording_not_human_fact_check(self):
        statement="Read the material label before cleaning the product."
        record=external("https://www.fda.gov/safety",
                        statement)
        hits=find_candidates(statement,[record])
        self.assertEqual(hits[0]["risk_state"],"EXACT_WORDING_NEEDS_FACT_REVIEW")
        self.assertFalse(hits[0]["semantic_support_verified"])
    def test_negation_mismatch_is_explicit_review(self):
        claim="This cleaner is compatible with silicone surfaces."
        record=external("https://www.fda.gov/safety",
                        "This cleaner is not compatible with silicone surfaces.")
        self.assertIn("POTENTIAL",find_candidates(claim,[record])[0]["risk_state"])
    def test_hypothetical_wrong_numeric_claim_requires_review(self):
        claim="The approved device can withstand 20 kg of force."
        record=external("https://www.fda.gov/safety",
                        "The approved device can withstand 10 kg of force.")
        self.assertIn("POTENTIAL",find_candidates(claim,[record])[0]["risk_state"])
    def test_owner_original_is_not_independent_verification(self):
        draft="# Guide\n\n## What to check?\n\nFollow the actual manufacturer instructions before washing."
        out=trace_claims(draft,ORIGINAL)
        self.assertEqual(out["summary"]["confirmed_supported_claims"],0)
        self.assertTrue(out["source_original_not_independent_proof"])
        self.assertFalse(out["publish_ready"])
        self.assertEqual(out["status"],"HUMAN_FACT_EVIDENCE_REVIEW_REQUIRED")
        self.assertGreater(out["summary"]["important_claims_total"],0)
    def test_cited_unrelated_public_page_not_proof(self):
        record=external("https://www.cdc.gov/niosh/ergonomics/",
                        "Lifting irregular objects in an awkward position can hurt your back.")
        claim="# Guide\n\n## Rating\n\nThis toy has an [IPX7 waterproof rating](https://www.cdc.gov/niosh/ergonomics/) for swimming and bathing."
        out=trace_claims(claim,ORIGINAL,[record])
        self.assertEqual(out["summary"]["claims_with_unrelated_or_unavailable_citation"],1)
        self.assertEqual(out["summary"]["confirmed_supported_claims"],0)
    def test_invalid_provenance_and_hash_block_external_source(self):
        good=external("https://consumer.ftc.gov/articles/online-shopping",
                      "Keep the records from the seller.")
        bad=dict(good,body_sha256="not-content-sha")
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            validate_sources([bad])
        bad=dict(good,source_kind="metadata_only")
        with self.assertRaisesRegex(ValueError,"cannot be presented"):
            validate_sources([bad])
    def test_duplicate_or_non_https_evidence_rejected(self):
        a=external("https://www.cdc.gov/a","Keep order records for your delivery.")
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            validate_sources([a,a])
        with self.assertRaises(ValueError):
            validate_sources([dict(a,url="http://localhost/private")])
    def test_no_machine_or_model_can_auto_approve_citation(self):
        draft="# Article\n\n## Care\n\nAlways follow manufacturer instructions when cleaning this silicone product."
        record=external("https://www.fda.gov/safety",
                        "Always follow manufacturer instructions when cleaning this silicone product.")
        report=trace_claims(draft,ORIGINAL,[record])
        self.assertGreater(report["summary"]["important_claims_total"],0)
        claimed=report["claims"][0]
        note={
            "claim_id":claimed["id"],"claim_sha256":claimed["claim_sha256"],
            "reviewer":"Real Example Editor","decision":"SUPPORTED_BY_QUOTED_SOURCE",
            "reviewer_declaration":CLAIM_REVIEW_DECLARATION,
            "reason":"This test explicitly compares the literal statement with source text.",
            "source_url":record["url"],
            "source_quote":record["paragraphs"][0],
        }
        with self.assertRaisesRegex(ValueError,"model-specific"):
            apply_human_claim_reviews(report,[record],[note])
        note["manufacturer_specific_confirmation"]=True
        with self.assertRaisesRegex(ValueError,"model-specific manufacturer"):
            apply_human_claim_reviews(report,[record],[note])
        # Synthetic example manual for unit testing ONLY, not a real product
        # or a false assertion of evidence in a real article.
        manual=external("https://manufacturer.example.com/docs/AB12",
                        "Always follow manufacturer instructions when cleaning this silicone product.")
        manual["evidence_role"]="manufacturer_primary"
        manual["manufacturer_domain"]="manufacturer.example.com"
        manual["product_model"]="AB12"
        manual["document_type"]="official_product_manual"
        note["source_url"]=manual["url"]
        note["manufacturer_model"]="AB12"
        out=apply_human_claim_reviews(report,[manual],[note])
        self.assertEqual(out["reviewed_claim_count"],1)
        self.assertEqual(out["owner_release_approval"],"PENDING")
        self.assertFalse(out["automatic_publish_ready"])
        self.assertGreaterEqual(out["pending_claim_count"],0)

    def test_government_page_cannot_become_manufacturer_manual_by_boolean(self):
        record=external("https://www.cdc.gov/niosh/ergonomics/",
                        "Check product safety instructions before use.")
        record.update({
            "evidence_role":"manufacturer_primary",
            "manufacturer_domain":"www.cdc.gov",
            "product_model":"AB12","document_type":"official_product_manual",
        })
        with self.assertRaisesRegex(ValueError,"Manufacturer primary evidence"):
            validate_sources([record])

    def test_manufacturer_role_requires_exact_model_and_domain(self):
        record=external("https://manufacturer.example.com/docs/AB12",
                        "Check product safety instructions before use.")
        record.update({
           "evidence_role":"manufacturer_primary",
           "manufacturer_domain":"manufacturer.example.com",
           "product_model":"AB12",
           "document_type":"official_model_specifications",
        })
        self.assertEqual(len(validate_sources([record])),1)
        wrong=dict(record,product_model="")
        with self.assertRaises(ValueError):
            validate_sources([wrong])
        wrong=dict(record,manufacturer_domain="other.example.com")
        with self.assertRaises(ValueError):
            validate_sources([wrong])

    def test_invented_evidence_quote_rejected_even_if_url_is_official(self):
        draft="# Article\n\n## Care\n\nAlways follow manufacturer instructions when cleaning this silicone product."
        record=external("https://www.fda.gov/safety",
                        "Always follow manufacturer instructions when cleaning this silicone product.")
        report=trace_claims(draft,ORIGINAL,[record])
        row=report["claims"][0]
        note={"claim_id":row["id"],"claim_sha256":row["claim_sha256"],
              "reviewer":"Example Editor","decision":"SUPPORTED_BY_QUOTED_SOURCE",
              "reviewer_declaration":CLAIM_REVIEW_DECLARATION,
              "reason":"Source information was checked in the editor's local review sheet.",
              "source_url":record["url"],
              "source_quote":"An invented statement that cannot be found in the original public page.",
              "manufacturer_specific_confirmation":True}
        with self.assertRaisesRegex(ValueError,"actual fetched text"):
            apply_human_claim_reviews(report,[record],[note])

    def test_private_claim_worklist_includes_every_important_fact(self):
        draft="# Guide\n\n## Guide\n\nAlways check manufacturer safety instructions before rinsing silicone parts."
        r=trace_claims(draft,ORIGINAL)
        sheet=claim_review_sheet(r)
        self.assertIn("CLM-0001",sheet)
        self.assertIn("Always check manufacturer safety instructions",sheet)
        self.assertIn("publish-blocked",sheet)
        self.assertNotIn("FACT_CHECK_PASS",sheet)

    def test_claim_ids_and_counts_reproducible(self):
        text="# Guide\n\n## Instructions\n\nCheck compatibility before cleaning the silicone unit. Never assume all labels are reliable."
        a=trace_claims(text,ORIGINAL)
        b=trace_claims(text,ORIGINAL)
        self.assertEqual([r["claim_sha256"] for r in a["claims"]],
                         [r["claim_sha256"] for r in b["claims"]])
        self.assertEqual(a["summary"]["important_claims_total"],
                         a["summary"]["human_entailment_review_pending"])

if __name__=="__main__":
    unittest.main()
