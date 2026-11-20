"""Owner P0 article scope must be per-job, immutable, and fail closed."""
from __future__ import annotations

import json
import contextlib
import io
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

from andy_write import article_scope as gate
from andy_write import benchmark as qc_benchmark
from andy_write import __main__ as cli


class ArticleScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.original = self.root / "original.md"
        self.original.write_text("# How to Unbox a Full-Size Sex Doll\n\n" + "Details. " * 200)
        p = self.root / "policy" / "owner_rules.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({
            "priority": "OWNER_P0", "version": "owner-p0-v1.1.0",
            "scope_contract_required": True,
        }))
        self.root_patch = patch.object(gate, "ROOT", self.root)
        self.file_patch = patch.object(gate, "resolved", lambda name: self.original)
        self.root_patch.start()
        self.file_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.file_patch.stop)
        self.job = {
            "job_id": "fullsize-001", "brand": "pairdoll",
            "topic": "full-size sex doll unboxing", "target_title": "Delivery Checklist",
            "source_path": ".runs/fullsize/source.md",
            "source_url": "https://example.com/owner-fullsize",
            "research_urls": ["https://example.com/fact-evidence"],
            "article_scope": {
                "subject": "full-size sex doll delivery and inspection",
                "primary_product": "full-size sex doll",
                "excluded_primary_products": ["sex doll torso", "torso"],
                "qc_time_window": {"start": "2025-10-01", "end": "2025-12-31"},
                "article_time_window": {"start": None, "end": None},
                "qc_structure_urls": ["https://kissself.com/2025-qc-example"],
                "allow_explicit_comparison": False,
            },
        }

    def test_first_run_freezes_and_next_run_reuses(self):
        record = gate.ensure_article_scope(self.job, allow_create=True)
        self.assertEqual(record["version"], gate.VERSION)
        self.assertEqual(record["revision"], 1)
        self.assertEqual(gate.ensure_article_scope(self.job), record)
        self.assertIn("OWNER_P0", gate.scope_prompt_header(record))

    def test_each_article_has_independent_contract(self):
        first = gate.ensure_article_scope(self.job, allow_create=True)
        other = {**self.job, "job_id": "torso-002", "topic": "torso maintenance"}
        other["article_scope"] = {**self.job["article_scope"],
            "subject": "sex doll torso maintenance", "primary_product": "sex doll torso",
            "excluded_primary_products": ["full-size sex doll"]}
        self.original.write_text("# Sex Doll Torso Maintenance\n\n" + "Synthetic details. " * 200)
        second = gate.ensure_article_scope(other, allow_create=True)
        self.assertNotEqual(gate.contract_path(self.job), gate.contract_path(other))
        self.assertNotEqual(first["scope_fingerprint"], second["scope_fingerprint"])

    def test_scope_edit_requires_owner_process(self):
        gate.ensure_article_scope(self.job, allow_create=True)
        altered = json.loads(json.dumps(self.job))
        altered["article_scope"]["subject"] = "unapproved expanded product scope"
        with self.assertRaisesRegex(gate.ScopeConflict, "ARTICLE_SCOPE_CHANGED"):
            gate.ensure_article_scope(altered, allow_create=True)

    def test_source_edits_cannot_silently_replace_contract(self):
        gate.ensure_article_scope(self.job, allow_create=True)
        self.original.write_text("# Unrelated Article\n" + "Changed. " * 200)
        with self.assertRaisesRegex(gate.ScopeConflict, "ARTICLE_SCOPE_CHANGED"):
            gate.ensure_article_scope(self.job)

    def test_missing_frozen_scope_blocks_later_steps(self):
        with self.assertRaisesRegex(gate.ScopeConflict, "missing"):
            gate.ensure_article_scope(self.job, allow_create=False)

    def test_torso_original_rejected_for_fullsize(self):
        self.original.write_text("# How to Enjoy Your Sex Doll Torso\n" + "Data. " * 200)
        with self.assertRaisesRegex(gate.ScopeConflict, "SOURCE_PRODUCT_MISMATCH"):
            gate.ensure_article_scope(self.job, allow_create=True)
        self.assertFalse(gate.contract_path(self.job).exists())

    def test_comparison_is_not_naively_prohibited(self):
        self.original.write_text("# Full-Size Versus Torso Comparison\n" + "Data. " * 200)
        self.job["article_scope"]["allow_explicit_comparison"] = True
        record = gate.ensure_article_scope(self.job, allow_create=True)
        gate.verify_article_input(self.job, record)

    def test_old_qc_article_rejected_even_when_same_site(self):
        record = gate.ensure_article_scope(self.job, allow_create=True)
        with self.assertRaisesRegex(gate.ScopeConflict, "QC_DATE_MISMATCH"):
            gate.validate_qc_candidate(record,
                url="https://kissself.com/2025-qc-example", publication_date="2022-01-15")

    def test_valid_2025_qc_does_not_become_owner_original(self):
        record = gate.ensure_article_scope(self.job, allow_create=True)
        gate.validate_qc_candidate(record,
            url="https://kissself.com/2025-qc-example", publication_date="2025-12-26")
        self.assertNotEqual(record["scope"]["source_roles"]["OWNER_ORIGINAL"],
                            record["scope"]["source_roles"]["QC_STRUCTURE_ONLY"][0])

    def test_cross_role_url_substitution_is_blocked(self):
        self.job["article_scope"]["qc_structure_urls"] = self.job["research_urls"][:]
        with self.assertRaisesRegex(gate.ScopeConflict, "roles must remain separate"):
            gate.ensure_article_scope(self.job, allow_create=True)

    def test_output_title_scope_conflict_is_blocked(self):
        record = gate.ensure_article_scope(self.job, allow_create=True)
        with self.assertRaisesRegex(gate.ScopeConflict, "DRAFT_PRODUCT_MISMATCH"):
            gate.verify_generated_draft(record, "# The Best Sex Doll Torso\n\nGreat advice.")

    def test_output_title_same_product_is_allowed(self):
        record = gate.ensure_article_scope(self.job, allow_create=True)
        gate.verify_generated_draft(record, "# Full-Size Sex Doll Unboxing\n\nGreat advice.")

    def test_missing_time_definition_blocks_new_article(self):
        del self.job["article_scope"]["article_time_window"]
        with self.assertRaisesRegex(gate.ScopeConflict, "article_time_window"):
            gate.ensure_article_scope(self.job, allow_create=True)

    def test_unscoped_job_fails_before_research(self):
        del self.job["article_scope"]
        with self.assertRaisesRegex(gate.ScopeConflict, "Missing article_scope"):
            gate.ensure_article_scope(self.job, allow_create=True)

    def test_scope_init_cli_freezes_without_research_or_model(self):
        stdout = io.StringIO()
        with patch.object(cli, "read_job", return_value=self.job), patch.object(
                cli, "cached_research") as research, contextlib.redirect_stdout(stdout):
            self.assertEqual(cli.main(["scope-init", "--job", "unused.json"]), 0)
        research.assert_not_called()
        self.assertIn(gate.VERSION, stdout.getvalue())
        self.assertTrue(gate.contract_path(self.job).is_file())

    def test_run_does_not_start_research_without_owner_scope(self):
        del self.job["article_scope"]
        with patch.object(cli, "read_job", return_value=self.job), patch.object(
                cli, "cached_research") as research, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["run", "--job", "unused.json"]), 2)
        research.assert_not_called()

    def test_qc_metrics_never_admit_unapproved_year_or_url(self):
        frozen = gate.ensure_article_scope(self.job, allow_create=True)
        rows = [{"id": n, "link": url, "date": day,
                 "title": {"rendered": title}, "content": {"rendered": "<h2>FAQ</h2><p>Checklist</p>"}}
                for n, url, day, title in (
                    (1, "https://kissself.com/2025-qc-example", "2025-12-26", "Full Size Doll Care"),
                    (2, "https://kissself.com/2022-torso", "2022-06-08", "Torso Cleaning"))]
        proc = Mock(returncode=0, stdout=json.dumps(rows), stderr="")
        with patch.object(qc_benchmark, "validate_public_url"), patch.object(
                qc_benchmark.subprocess, "run", return_value=proc):
            metrics = qc_benchmark.scrape_qc_metrics(contract=frozen)
        self.assertEqual(metrics["sample_count"], 1)
        self.assertEqual(metrics["representative"][0]["id"], 1)

    def test_qc_metrics_reject_authorized_url_with_wrong_product(self):
        frozen = gate.ensure_article_scope(self.job, allow_create=True)
        row = {"id": 3, "link": "https://kissself.com/2025-qc-example",
               "date": "2025-12-26", "title": {"rendered": "Sex Doll Torso Care"},
               "content": {"rendered": "<h2>Details</h2>"}}
        proc = Mock(returncode=0, stdout=json.dumps([row]), stderr="")
        with patch.object(qc_benchmark, "validate_public_url"), patch.object(
                qc_benchmark.subprocess, "run", return_value=proc):
            with self.assertRaisesRegex(gate.ScopeConflict, "QC_PRODUCT_MISMATCH"):
                qc_benchmark.scrape_qc_metrics(contract=frozen)


if __name__ == "__main__":
    unittest.main()
