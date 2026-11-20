"""Full CLI Dev-only gate smoke tests using *synthetic* offline evidence.

These tests prove orchestration, NOT real Google results or Owner content UAT.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import uuid

from tests.test_search_intent_gate import fixture

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".runs"


class IsolatedDevEndToEnd(unittest.TestCase):
    def setUp(self):
        PRIVATE.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="r7-e2e-", dir=PRIVATE)
        self.addCleanup(self.temp.cleanup)
        self.out = pathlib.Path(self.temp.name)
        self.job_id = "r7e2e_" + uuid.uuid4().hex[:20]
        frozen = PRIVATE / "_article_scopes" / (self.job_id + ".json")
        self.addCleanup(lambda: frozen.unlink(missing_ok=True))
        source = self.out / "synthetic-source.md"
        # The existing rewrite/source envelope requires a substantial input;
        # repeated mock text is strictly a CLI fixture, never editorial output.
        mock_detail = ("This is synthetic, nonfactual test text about checking "
                       "a support surface and keeping the Owner's product category "
                       "fixed while the application moves between pipeline stages. ") * 12
        source.write_text(
            "# Full Size Doll Care Guide\n\n"
            "## Prepare the Surface\n\n"
            "This is synthetic test prose about moving a heavy full size product "
            "and checking a stable support surface before any setup. " + mock_detail + "\n\n"
            "## Check Manufacturer Instructions\n\n"
            "This synthetic test section covers cleaning and drying choices "
            "without asserting real specifications or product guarantees. " + mock_detail + "\n",
            encoding="utf-8")
        self.job = {
            "job_id": self.job_id, "brand": "pairdoll",
            "topic": "full size doll care", "target_title": "Full Size Doll Care Guide",
            "target_keyword": "full size doll care", "brand_domain": "pairdoll.com",
            "search_intent_scope": {"audience": "adult owners", "market_country": "US",
                                    "language": "en", "device": "mobile"},
            "source_path": str(source.relative_to(ROOT)),
            "source_url": "https://example.invalid/fictional-owner-source",
            "output_dir": str(self.out.relative_to(ROOT)),
            "research_mode": "curated", "research_urls": [],
            "outline_mode": "source_hierarchy_v1",
            "article_scope": {
                "subject": "Synthetic CLI integration test for full size doll care",
                "primary_product": "full size doll",
                "excluded_primary_products": ["torso"],
                "article_time_window": {"start": None, "end": None},
                "qc_time_window": {"start": None, "end": None},
                "qc_structure_urls": [], "allow_explicit_comparison": False}}
        self.job_path = self.out / "synthetic-job.json"
        self.job_path.write_text(json.dumps(self.job), encoding="utf-8")
        init = self.cli("scope-init", enabled=False)
        self.assertEqual(init.returncode, 0, init.stderr)
        self.fingerprint = json.loads(init.stdout)["fingerprint"]

    def cli(self, command, *, enabled=True):
        env = {**os.environ, "ANDY_WRITE_ENV": "dev",
               "ANDY_WRITE_SEARCH_INTENT_R7_ENABLED": "1" if enabled else "0"}
        return subprocess.run([sys.executable, "-m", "andy_write", command,
                               "--job", str(self.job_path)], cwd=ROOT,
                              env=env, capture_output=True, text=True,
                              timeout=16, check=False)

    def save_contract(self, data):
        data["scope"]["owner_scope_contract_id"] = self.fingerprint
        (self.out / "intent_contract.json").write_text(json.dumps(data), encoding="utf-8")
        (self.out / "intent_report.md").write_text(
            "# Synthetic QC fixture, not a real SERP capture or editorial finding\n",
            encoding="utf-8")

    def test_verified_shape_pass_reaches_outline_but_not_draft(self):
        self.save_contract(fixture())
        result = self.cli("run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / "outline.md").exists())
        self.assertFalse((self.out / "article-v1.md").exists())
        self.assertEqual(json.loads((self.out / "search-intent-decision.json").read_text())["gate"], "PASS")
        self.assertEqual(json.loads((self.out / "run-manifest.json").read_text())["wordpress_status"], "UNTOUCHED")

    def test_provisional_review_pauses_before_source(self):
        self.save_contract(fixture(evidence="provisional", status="REVIEW"))
        result = self.cli("run")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Search Intent REVIEW", result.stderr)
        self.assertTrue((self.out / "research-pack.json").exists())
        self.assertFalse((self.out / "source-catalog.json").exists())
        self.assertFalse((self.out / "outline.md").exists())

    def test_mismatch_blocks_before_source(self):
        data = fixture(status="BLOCK")
        data["mode"] = "audit"
        data["audit"] = {"article_source": "https://example.invalid/fictional-page",
                         "article_page_type": "product", "verdict": "Mismatch",
                         "reason": "Synthetic product-vs-guide buyer-stage mismatch"}
        self.save_contract(data)
        result = self.cli("run")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Search Intent BLOCK", result.stderr)
        self.assertFalse((self.out / "outline.md").exists())


if __name__ == "__main__":
    unittest.main()
