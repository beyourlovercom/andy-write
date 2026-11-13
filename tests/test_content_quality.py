"""Evidence-aware editorial regression tests: no detector prediction claims."""
from __future__ import annotations
import json
import pathlib
import unittest
from unittest.mock import patch

from andy_write.content_quality import (
    EMPTY_PHRASES, audit, edit_sections, parse_rewritten_sections, review_targets, split_sections
)
from andy_write.io import ROOT

JOB = ROOT / "examples/jobs/pairdoll-unboxing.json"
SAMPLE = ROOT / "examples/output/pairdoll-unboxing-gpt61-terra-review.md"

class ContentQualityTests(unittest.TestCase):
    def setUp(self):
        self.job = json.loads(JOB.read_text(encoding="utf-8"))
        self.article = SAMPLE.read_text(encoding="utf-8")
        self.research = {
            "sources": [
                {"url": "https://www.cdc.gov/niosh/publications/numbered/2026-119.html",
                 "status": "retrieved"},
                {"url": "https://pairdoll.com/how-to-use-a-sex-doll-what-first-time-owners-should-know-about-setup-cleaning-and-care/",
                 "status": "retrieved"},
                {"url": "https://consumer.ftc.gov/articles/online-shopping",
                 "status": "unavailable"},
            ]
        }
        self.catalog = {
            "segments": [
                {"id": "SEG-036", "excerpt": "The foam lining, a fabric drawstring bag, and padding may be present."},
                {"id": "SEG-050", "excerpt": "If wire finger options were selected, check for finger damage."},
                {"id": "SEG-053", "excerpt": "Photograph any damage before handling further."},
            ]
        }

    def test_sample_fails_source_specificity_and_links(self):
        q = audit(self.article, self.job, self.research, self.catalog)
        codes = {i["code"] for i in q["issues"]}
        self.assertIn("NO_SUPPORTING_EXTERNAL_LINK", codes)
        self.assertIn("MISSING_INTERNAL_LINK", codes)
        self.assertIn("MISSING_REFERENCE_DETAIL", codes)
        targets = review_targets(q)
        self.assertIn("How can you unpack and move the doll safely?", targets)
        self.assertIn("What belongs on the first inspection checklist?", targets)
        self.assertLessEqual(len(targets), 3)

    def test_hype_detection_no_fake_percent_score(self):
        text = "# Heading\n\n## Why inspect?\n\nIn the realm of commerce, embark on a journey and delve into damage reports.\n"
        q = audit(text, {"job_id": "test"})
        self.assertGreaterEqual(len(q["cliche_phrases"]), 3)
        self.assertNotIn("ai_probability", q)

    def test_only_verified_existing_links_count(self):
        text = self.article.replace(
            "Place the carton where its flaps can open",
            "[Read the NIOSH lifting note](https://www.cdc.gov/niosh/publications/numbered/2026-119.html). Place the carton where its flaps can open")
        text = text.replace(
            "Use good light and work through the following list:",
            "[Further care advice](https://pairdoll.com/how-to-use-a-sex-doll-what-first-time-owners-should-know-about-setup-cleaning-and-care/). Use good light and work through the following list:")
        q = audit(text, self.job, self.research, self.catalog)
        codes = {i["code"] for i in q["issues"]}
        self.assertNotIn("NO_SUPPORTING_EXTERNAL_LINK", codes)
        self.assertNotIn("MISSING_INTERNAL_LINK", codes)

    def test_malformed_or_unverified_external_link_flagged(self):
        text = self.article.replace(
            "Place the carton where its flaps can open",
            "[FTC claim](https://consumer.ftc.gov/articles/online-shopping). Place the carton where its flaps can open")
        q = audit(text, self.job, self.research, self.catalog)
        self.assertIn("UNVERIFIED_EXTERNAL_LINK", {i["code"] for i in q["issues"]})

    def test_only_affected_sections_changed(self):
        first = split_sections(self.article)[2]
        original = self.article
        changed = edit_sections(original, {first["heading"]: first["body"] + "\n\nCheck any foam supports."})
        assert first["heading"] in changed
        a, b = split_sections(original), split_sections(changed)
        self.assertEqual(len(a), len(b))
        for old, new in zip(a, b):
            if old["heading"] != first["heading"]:
                self.assertEqual(old, new)
        self.assertIn("Check any foam supports.", changed)

    def test_chapter_parse_requires_exact_headings(self):
        requested = ["What should you check?", "How can you proceed?"]
        response = ("# Section Revisions\n\n## What should you check?\n\n"
                    + "Check the box. " * 15 + "\n\n## How can you proceed?\n\n"
                    + "Photograph the labels. " * 15)
        got = parse_rewritten_sections(response, requested)
        self.assertEqual(set(got), set(requested))
        with self.assertRaisesRegex(ValueError, "unexpected headings"):
            parse_rewritten_sections(response, requested[:1])

    def test_anchor_not_present_in_reference_is_not_enforced(self):
        q = audit(self.article, self.job, self.research, {"segments": []})
        self.assertNotIn("MISSING_REFERENCE_DETAIL", {i["code"] for i in q["issues"]})

if __name__ == "__main__":
    unittest.main()

class TestIntroduction(unittest.TestCase):
    def test_split_existing_answer_and_bridge_without_new_claim(self):
        from andy_write.content_quality import normalize_intro, intro_structure
        original = ("# Title\n\nAn introduction about delivery day.\n\n"
                    "Keep the carton until the inspection is complete. "
                    "Follow your own product instructions during unpacking.\n\n"
                    "## What should I do?\n\nLook for scratches carefully.")
        revised, done = normalize_intro(original)
        self.assertTrue(done)
        self.assertEqual(intro_structure(revised)["paragraphs"], 3)
        self.assertTrue(intro_structure(revised)["direct_answer_bold"])
        self.assertEqual(revised.replace("**", "").replace("\n\n", " ").split(),
                         original.replace("\n\n", " ").split())
        second, again = normalize_intro(revised)
        self.assertFalse(again)
        self.assertEqual(revised, second)

    def test_unrepairable_one_sentence_is_review(self):
        from andy_write.content_quality import normalize_intro, audit
        original = "# Title\n\nOpening here.\n\nThe carton is present.\n\n## What to do?\n\nLook over the box."
        result, fixed = normalize_intro(original)
        self.assertFalse(fixed)
        self.assertIn("INTRO_STRUCTURE",
            {issue["code"] for issue in audit(result, {"job_id": "test"})["issues"]})

class TestTargetedChapterWorkflow(unittest.TestCase):
    def test_model_only_repairs_flagged_sections(self):
        from andy_write.codex_cli import run_writing, word_count
        from andy_write.content_quality import split_sections
        from tempfile import TemporaryDirectory
        sample = SAMPLE.read_text(encoding="utf-8")
        source = {"sources": [
            {"url":"https://www.cdc.gov/niosh/publications/numbered/2026-119.html",
             "status":"retrieved"},
            {"url":"https://pairdoll.com/how-to-use-a-sex-doll-what-first-time-owners-should-know-about-setup-cleaning-and-care/",
             "status":"retrieved"}]}
        segments = {"segments":[]}
        job = {
            "job_id":"targeted-edit",
            "brand":"pairdoll",
            "brand_domain":"pairdoll.com",
            "quality_profile":"people_first",
            "source_path":"owner-source.md",
            "source_url":"https://example.com/owner-reference",
        }
        all_sections = split_sections(sample)
        chosen = [
            next(s for s in all_sections if "unpack and move" in s["heading"]),
            next(s for s in all_sections if "inspection checklist" in s["heading"]),
        ]
        links = [
            "[NIOSH lifting guidance](https://www.cdc.gov/niosh/publications/numbered/2026-119.html).",
            "[Related first-time owner guide](https://pairdoll.com/how-to-use-a-sex-doll-what-first-time-owners-should-know-about-setup-cleaning-and-care/)."
        ]
        fragments = "# Section Revisions\n\n" + "\n\n".join(
            "## " + sec["heading"] + "\n\n" + sec["body"] + "\n\n" + links[i]
            for i, sec in enumerate(chosen))
        def fake_result(body):
            return (body,{"model":"gpt-6.1-terra","input_tokens":200,
                    "cached_input_tokens":100,"output_tokens":300,
                    "reasoning_output_tokens":0,"visible_english_words":word_count(body)},
                    '{"type":"turn.completed"}\n',"")
        with TemporaryDirectory() as folder:
            dest = pathlib.Path(folder)
            original = dest / "owner-source.md"
            original.write_text(sample, encoding="utf-8")
            from andy_write.io import hashtext
            from andy_write.rewrite_contract import source_envelope, CONTRACT_VERSION
            prompt = "Grounded draft context.\n" + source_envelope(sample, job["source_url"])
            (dest/"writing-prompt.md").write_text(prompt, encoding="utf-8")
            (dest/"run-manifest.json").write_text(
                json.dumps({"source_sha256":hashtext(sample),
                            "writing_prompt_sha256":hashtext(prompt),
                            "rewrite_source_contract_version":CONTRACT_VERSION}))
            (dest/"research-pack.json").write_text(json.dumps(source))
            (dest/"source-catalog.json").write_text(json.dumps(segments))
            with patch("andy_write.codex_cli.outdir", return_value=dest):
              with patch("andy_write.usage_policy.resolved", return_value=original):
                with patch("andy_write.codex_cli.run_model",
                    side_effect=[fake_result(sample), fake_result(sample), fake_result(fragments)]) as model:
                    output = run_writing(job,target=word_count(sample),tolerance=.12,max_revisions=1)
            after=(dest/"article-auto-final.md").read_text()
            self.assertEqual(model.call_count,3)
            self.assertEqual(output["last_stage"],"quality-chapters-1")
            self.assertEqual(output["status"],"RULE_CHECK_PASS")
            self.assertEqual(output["source_fidelity"]["status"],"HUMAN_REVIEW_REQUIRED")
            self.assertTrue((dest/"source-fidelity-review.md").exists())
            self.assertIn(links[0],after)
            self.assertIn(links[1],after)
            before_sections={s["heading"]:s["body"] for s in all_sections}
            after_sections={s["heading"]:s["body"] for s in split_sections(after)}
            for heading in before_sections:
                if heading not in {sec["heading"] for sec in chosen}:
                    self.assertEqual(before_sections[heading],after_sections[heading])
