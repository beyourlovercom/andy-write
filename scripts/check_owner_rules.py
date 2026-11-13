#!/usr/bin/env python3
"""Dependency-free CI check for highest-priority Andy Write Owner P0 rules."""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED = {"SKILL_FIRST", "EVIDENCE_BASED", "VERSION_ROLLBACK"}

def check(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    def read(path: str) -> str:
        filename = root / path
        if not filename.is_file():
            errors.append("Missing file: " + path)
            return ""
        return filename.read_text(encoding="utf-8")
    agents = read("AGENTS.md")
    owner = read("OWNER_RULES.md")
    raw = read("policy/owner_rules.json")
    pr = read(".github/pull_request_template.md")
    read(".github/workflows/owner-rules.yml")
    read("README.md")
    try:
        policy = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append("Invalid policy JSON: " + str(exc))
        policy = {}
    if policy.get("priority") != "OWNER_P0":
        errors.append("Owner policy priority must be OWNER_P0")
    if not str(policy.get("version", "")).startswith("owner-p0-v"):
        errors.append("Versioned P0 policy is required")
    principles = policy.get("principles", [])
    if not isinstance(principles, list):
        principles = []
    actual = [item.get("id") for item in principles if isinstance(item, dict)]
    if set(actual) != EXPECTED or len(actual) != 3:
        errors.append("All three Owner principles are mandatory and unique")
    for identifier in EXPECTED:
        if identifier not in agents or identifier not in owner:
            errors.append("Missing P0 principle in root files: " + identifier)
    evidence = next((row for row in principles
                     if isinstance(row, dict) and row.get("id") == "EVIDENCE_BASED"), {})
    if evidence.get("ai_detector_percentage_as_acceptance") is not False:
        errors.append("AI detector percentage cannot be a quality acceptance metric")
    if not agents.startswith("# Andy Write — Owner P0"):
        errors.append("AGENTS.md must declare Owner P0 first")
    if policy.get("codex_cli_allowed_purpose") != "rewrite_existing_user_supplied_article_only":
        errors.append("Codex CLI must remain article-rewrite-only")
    for key in ("codex_cli_other_purposes_allowed", "image_generation_enabled",
                "video_generation_enabled", "auto_merge_allowed",
                "production_auto_publish_allowed"):
        if policy.get(key) is not False:
            errors.append(key + " must be false")
    for phrase in ("Codex CLI", "image generation", "video generation", "Owner"):
        if phrase.casefold() not in agents.casefold() or phrase.casefold() not in owner.casefold():
            errors.append("Owner safety restrictions not visible in root policy: " + phrase)
    for phrase in ("Skill", "QC", "tests", "Rollback", "Owner"):
        if phrase.casefold() not in pr.casefold():
            errors.append("PR template missing acceptance evidence: " + phrase)
    if (root / "andy_write/imagegen_runner.py").exists():
        errors.append("Forbidden active image generator exists")
    entry = root / "andy_write/__main__.py"
    if entry.is_file() and '"media-generate"' in entry.read_text(encoding="utf-8"):
        errors.append("Forbidden image/video generation entrypoint exists")
    return errors

def main() -> int:
    issues = check()
    if issues:
        print("OWNER P0 POLICY FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1
    print("OWNER P0 POLICY PASS: Skills-first / Evidence-driven / Version-rollback")
    return 0

if __name__ == "__main__":
    sys.exit(main())
