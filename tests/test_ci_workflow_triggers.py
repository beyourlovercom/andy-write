"""Dependency-free regression guard for Andy Write development PR CI."""

from __future__ import annotations

import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ".github/workflows/tests.yml",
    ".github/workflows/owner-rules.yml",
)
DEV_BRANCH = "feat/r0-r2-research-writing-mvp"


def event_branches(workflow: str, event: str) -> set[str]:
    """Read the intentionally inline branch allowlist without a YAML dependency."""
    match = re.search(
        rf"(?m)^  {re.escape(event)}:\s*\n    branches:\s*\[([^\]\n]+)\]\s*$",
        workflow,
    )
    if match is None:
        raise AssertionError(f"Missing {event} branch allowlist")
    return {value.strip().strip('"\'') for value in match.group(1).split(",")}


class CIWorkflowTriggersTests(unittest.TestCase):
    def test_dev_pull_requests_run_both_workflows(self):
        for filename in WORKFLOWS:
            with self.subTest(workflow=filename):
                content = (ROOT / filename).read_text(encoding="utf-8")
                self.assertEqual(event_branches(content, "pull_request"), {"main", DEV_BRANCH})

    def test_existing_push_paths_are_preserved(self):
        for filename in WORKFLOWS:
            with self.subTest(workflow=filename):
                content = (ROOT / filename).read_text(encoding="utf-8")
                expected = {"main", "feat/**"}
                if filename.endswith("owner-rules.yml"):
                    expected.add("policy/**")
                self.assertEqual(event_branches(content, "push"), expected)


if __name__ == "__main__":
    unittest.main()
