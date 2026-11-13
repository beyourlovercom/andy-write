"""Offline policy regressions; never invoke Codex or network."""
from __future__ import annotations
import json
import pathlib
import shutil
import tempfile
import unittest
from scripts.check_owner_rules import ROOT, check

FILES = [
    "AGENTS.md", "OWNER_RULES.md", "README.md",
    "policy/owner_rules.json",
    ".github/pull_request_template.md",
    ".github/workflows/owner-rules.yml"
]

class OwnerRulesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name)
        for name in FILES:
            dest = self.path / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)

    def test_rule_set_is_complete_and_highest_priority(self):
        self.assertEqual(check(self.path), [])
        data = json.loads((self.path/"policy/owner_rules.json").read_text())
        self.assertEqual(data["priority"], "OWNER_P0")
        self.assertEqual(len(data["principles"]), 3)

    def test_missing_skill_rule_fails(self):
        agents = self.path/"AGENTS.md"
        agents.write_text(agents.read_text().replace("SKILL_FIRST", "SKILL_MISSING"))
        self.assertTrue(any("SKILL_FIRST" in msg for msg in check(self.path)))

    def test_ai_detector_cannot_be_required_acceptance(self):
        policy = self.path/"policy/owner_rules.json"
        data = json.loads(policy.read_text())
        data["principles"][1]["ai_detector_percentage_as_acceptance"] = True
        policy.write_text(json.dumps(data))
        self.assertTrue(any("AI detector" in msg for msg in check(self.path)))

    def test_forbidden_media_generation_fails(self):
        policy = self.path/"policy/owner_rules.json"
        data = json.loads(policy.read_text())
        data["image_generation_enabled"] = True
        policy.write_text(json.dumps(data))
        self.assertTrue(any("image_generation_enabled" in msg for msg in check(self.path)))

    def test_codex_scope_cannot_expand(self):
        policy = self.path/"policy/owner_rules.json"
        data = json.loads(policy.read_text())
        data["codex_cli_other_purposes_allowed"] = True
        policy.write_text(json.dumps(data))
        self.assertTrue(any("codex_cli_other_purposes_allowed" in msg for msg in check(self.path)))

    def test_unreviewed_automerge_fails(self):
        policy = self.path/"policy/owner_rules.json"
        data = json.loads(policy.read_text())
        data["auto_merge_allowed"] = True
        policy.write_text(json.dumps(data))
        self.assertTrue(any("auto_merge_allowed" in msg for msg in check(self.path)))

    def test_missing_pr_template_fails(self):
        (self.path/".github/pull_request_template.md").unlink()
        self.assertTrue(any("pull_request_template" in msg for msg in check(self.path)))

if __name__ == "__main__":
    unittest.main()
