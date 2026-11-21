"""Compare two private context-QC reports against the *same* frozen source.

Only source hashes, section anchors, code/priority counts and generic evidence
gaps appear in the derived output. This is not a human quality measurement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCE_FIELDS = (
    "benchmark_id", "source_url", "source_post_id", "source_modified",
    "source_content_sha256", "source_role", "scope_subject",
    "search_intent_verdict",
)


def compare_reports(before: dict, after: dict) -> dict:
    for field in SOURCE_FIELDS:
        if before.get(field) != after.get(field):
            raise ValueError(f"SCOPE_OR_SOURCE_CHANGED: {field}")
    for report in (before, after):
        if (report.get("status") != "HUMAN_REVIEW_REQUIRED"
            or report.get("publish_ready") is not False
            or report.get("human_labels_present") != 0
            or report.get("validated_truth_errors") is not None):
            raise ValueError("Actual independent human labels or publishing gate changed")

    def by_key(report: dict) -> dict:
        result = {}
        for candidate in report["candidates"]:
            key = (candidate["code"], candidate["anchor"], candidate["priority"])
            if key in result:
                raise ValueError("Duplicate candidate identity")
            if (candidate["editorial_verdict"] != "NEEDS_HUMAN_REVIEW"
                or candidate["verified_fact_error"] is not False):
                raise ValueError("Candidate incorrectly treated as factual verdict")
            result[key] = candidate
        return result

    old, new = by_key(before), by_key(after)

    def printable(keys: set) -> list[dict]:
        return [{"code": code, "anchor": anchor, "priority": priority}
                for code, anchor, priority in sorted(keys)]

    evidence = [{"code": code, "anchor": anchor, "priority": priority,
                 "review_details": candidate["review_details"]}
                for (code, anchor, priority), candidate in sorted(new.items())
                if candidate.get("review_details")]
    return {
        "schema": "andy-write-qc-before-after/v1",
        "benchmark_id": before["benchmark_id"],
        "source_content_sha256": before["source_content_sha256"],
        "source_post_id": before["source_post_id"],
        "source_role": before["source_role"],
        "before_schema": before["schema"], "after_schema": after["schema"],
        "before_count": len(old), "after_count": len(new),
        "before_priority_counts": before["summary"]["by_priority"],
        "after_priority_counts": after["summary"]["by_priority"],
        "same_candidate_locations": set(old) == set(new),
        "added": printable(set(new) - set(old)),
        "removed": printable(set(old) - set(new)),
        "after_evidence_details": evidence,
        "search_intent_verdict": "UNASSESSABLE",
        "human_labels_present": 0,
        "validated_truth_errors": None,
        "quality_precision_or_recall": None,
        "status": "HUMAN_REVIEW_REQUIRED",
        "publish_ready": False,
        "limitations": "Candidate counts and evidence-gap specificity are not editorial accuracy or a writing A/B score",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    # The reports refer to public articles, but their source receipts and
    # precise private QA history remain outside committed source control.
    repo = Path(__file__).resolve().parents[1]
    private = (repo / ".runs").resolve()

    def private_path(raw: str) -> Path:
        p = Path(raw).resolve()
        if not p.is_relative_to(private):
            raise PermissionError("QC comparisons require ignored .runs paths")
        return p

    before, after, target = map(private_path, (args.before, args.after, args.report))
    result = compare_reports(json.loads(before.read_text(encoding="utf-8")),
                             json.loads(after.read_text(encoding="utf-8")))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in
                      {"after_evidence_details", "limitations"}}, indent=2))


if __name__ == "__main__":
    main()
