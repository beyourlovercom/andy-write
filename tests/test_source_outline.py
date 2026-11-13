"""Source headings, not borrowed competitor prose, drive adaptive source plans."""
from __future__ import annotations
import unittest
from andy_write.source import classify
from andy_write.outline import section_plan, markdown_outline
from andy_write.source_outline import to_question
from andy_write.codex_cli import (
    initial_prompt,edit_prompt,tighten_prompt,editorial_gate
)

ORIGINAL="""# Owner's Existing Complete Guide

Original text outlines a detailed setup process. Read actual equipment model
instructions before changing the routine, and avoid broad claims.

## Preparing the Product

### Read the manual

Read the correct user manual. This reference explains which accessories should
be checked and how to verify a model's compatibility.

### Inspect the pieces

Inspect the accessory kit and preserve the receipt before actual assembly.

## Cleaning and Care

### Check material compatibility

Use product-specific instructions. Never assume all products are waterproof
or can be sanitized using the same cleaner.

### Dry and store

Follow verified storage directions and avoid blanket suggestions about heat.

## What Not To Do

Do not invent brand certification or test results. The original manual is
not automatically proof of product safety.

## Conclusion

Wrap up the material-specific checks without generating an unrelated story.
"""
JOB={"job_id":"unit-source-plan","brand":"demo","topic":"product care",
     "target_title":"Owner Product Care Advice","outline_mode":"source_hierarchy_v1"}

class SourceHierarchyTests(unittest.TestCase):
    def setUp(self):
        self.catalog=classify(ORIGINAL,"https://example.com/owner-original")
        self.plan=section_plan(JOB,self.catalog,ORIGINAL)

    def test_preserve_original_topic_headings_and_h3s(self):
        self.assertEqual(len(self.plan),3)
        self.assertEqual([x["h3_count"] for x in self.plan],[2,2,0])
        self.assertEqual(self.plan[0]["source_heading"],"Preparing the Product")
        self.assertTrue(all(x["heading"].endswith("?") for x in self.plan))
        self.assertTrue(all(x["source_heading_evidence"]=="AUTHENTIC_H2" for x in self.plan))
        self.assertNotIn("arrival",str([x["heading"] for x in self.plan]))

    def test_mark_product_safety_review(self):
        self.assertTrue(self.plan[1]["manufacturer_material_review"])
        result=markdown_outline(JOB,self.plan,{"claims":[]})
        self.assertIn("MANUFACTURER CHECK REQUIRED",result)
        self.assertIn("No generated images or videos",result)
        self.assertNotIn("generate in R3",result)

    def test_stale_original_hash_is_rejected(self):
        with self.assertRaisesRegex(PermissionError,"hash"):
            section_plan(JOB,self.catalog,ORIGINAL+"Tampered after R1")

    def test_missing_headings_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"2\\+ authentic H2"):
            section_plan(JOB,classify("One ordinary paragraph with sufficient source words.", "https://example.com/source"),
                         "One ordinary paragraph with sufficient source words.")

    def test_source_title_question_editorial_cleanup(self):
        self.assertEqual(to_question("How to Use Your Sex Doll Torso 101"),
                         "How do you use your sex doll torso?")
        self.assertEqual(to_question("What NOT to do"),"What should you avoid?")
        self.assertEqual(to_question("Best Positions To Try With Your Sex Doll Torso"),
                         "Which positions can you consider with your sex doll torso?")

    def test_reader_headings_cannot_leak_editorial_review_process(self):
        from andy_write.review import check
        article=("# Article Title\n\n"
                 "## Which practical tips from the original guide need review?\n\n"
                 "Check the source to see what should change. "*3
                 + "\n\n## Conclusion\n\nAn ending.")
        result=check(article,{"job_id":"reader-heading-test"})
        self.assertTrue(any(x["code"]=="EDITORIAL_PROCESS_HEADING_LEAK"
                            for x in result["issues"]))
        clean=article.replace(
            "Which practical tips from the original guide need review?",
            "What practical tips apply when using your sex doll torso?")
        out=check(clean,{"job_id":"reader-heading-test"})
        self.assertFalse(any(x["code"]=="EDITORIAL_PROCESS_HEADING_LEAK"
                             for x in out["issues"]))

    def test_flattened_source_subtopics_trigger_manual_review(self):
        from andy_write.codex_cli import editorial_gate
        headings=[x["heading"] for x in self.plan]
        doc="# A Title\n\n"+ "\n\n".join(
             "## "+h+"\n\n"+("Source paraphrase about "+h+" without nested headings. ")*25
            for h in headings)+"\n\n## Conclusion\n\nFinish."
        result=editorial_gate(doc,JOB,expected_headings=headings,
                              expected_subtopics=12)
        self.assertTrue(any(x["code"]=="SOURCE_H3_HIERARCHY_FLATTENED"
                            for x in result["issues"]))
        self.assertEqual(result["status"],"REVIEW")

    def test_prompts_adapt_to_actual_number_of_h2_not_fixed_six(self):
        headings=[x["heading"] for x in self.plan]
        p=initial_prompt("Original source with paragraphs",1200,1050,1350,
                         expected_headings=headings)
        self.assertIn(headings[0],p)
        self.assertIn("Never invent six sections",p)
        e=edit_prompt("# Draft",1200,1050,1350,expected_headings=headings)
        self.assertNotIn("actual delivery",e)
        self.assertIn(headings[2],e)
        t=tighten_prompt("# Draft",1200,1050,1350,{"issues":[]},
                         expected_headings=headings)
        self.assertIn("exact H2s",t)
        self.assertNotIn("all six",t)

    def test_output_headings_are_a_gate_not_word_count_quota(self):
        headings=[x["heading"] for x in self.plan]
        art="# Title\n\n"+ "\n\n".join("## "+h+"\n\n"+("Plain guide paragraphs. "*17)
                for h in headings)+"\n\n## Conclusion\n\nReview the source."
        ok=editorial_gate(art,JOB,expected_headings=headings)
        self.assertFalse(any(x["code"]=="SOURCE_H2_PLAN_MISMATCH" for x in ok["issues"]))
        bad=editorial_gate(art.replace(headings[1],"Unrelated Shopping Advice?"),
                           JOB,expected_headings=headings)
        self.assertTrue(any(x["code"]=="SOURCE_H2_PLAN_MISMATCH" for x in bad["issues"]))

    def test_historical_unboxing_remains_unchanged_mode(self):
        classic={"job_id":"legacy","topic":"sex doll unboxing","target_title":"Unboxing Guide"}
        old=section_plan(classic,self.catalog)
        self.assertEqual(len(old),6)
        self.assertTrue(all(x["heading"].endswith("?") for x in old))

if __name__=="__main__":
    unittest.main()
