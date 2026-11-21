"""R12 two-stage, offline and private KissSelf blind QC evaluation.

No network, rewrite, model call, WordPress or Production operation. All
inputs/outputs other than versioned benchmark contracts must be inside .runs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from andy_write.io import ROOT
from andy_write.qc_context_blind import (
    blank_pair_review, blank_source_review, build_blind_pairs,
    build_source_packet, render_pair_workbench, render_source_workbench,
    score_blind_review, seal_source_gold,
)


PRIVATE_ROOT = (ROOT / ".runs").resolve()


def private_path(raw: str) -> Path:
    p = Path(raw).resolve()
    if not p.is_relative_to(PRIVATE_ROOT):
        raise PermissionError("Real QC artifacts must remain in gitignored .runs")
    return p


def load(raw: str, *, scope: bool = False) -> dict:
    path = Path(raw).resolve() if scope else private_path(raw)
    if scope and not path.is_relative_to((ROOT / "docs").resolve()):
        raise PermissionError("Only versioned docs/ scope contracts are allowed")
    return json.loads(path.read_text(encoding="utf-8"))


def save(raw: str, value: dict | str) -> None:
    path = private_path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive file creation: never overwrite a human annotation or seal.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        if isinstance(value, str):
            f.write(value)
        else:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_subparsers(dest="mode", required=True)
    source = modes.add_parser("source-pack", help="Blind source-only inventory; no machine alerts")
    source.add_argument("--case", nargs=2, action="append", metavar=("WP_JSON", "SCOPE_JSON"), required=True)
    source.add_argument("--out", required=True)
    source.add_argument("--review-a", required=True)
    source.add_argument("--review-b", required=True)

    view = modes.add_parser("source-html", help="Offline readable HTML for source-only reviewers")
    view.add_argument("--source-pack", required=True)
    view.add_argument("--out", required=True)

    seal = modes.add_parser("seal-gold", help="Seal independent source labels before showing alerts")
    seal.add_argument("--source-pack", required=True)
    seal.add_argument("--review-a", required=True)
    seal.add_argument("--review-b", required=True)
    seal.add_argument("--adjudication", default=None)
    seal.add_argument("--out", required=True)

    pairs = modes.add_parser("pair-pack", help="Generate anonymized pairs after source gold is sealed")
    pairs.add_argument("--source-pack", required=True)
    pairs.add_argument("--gold", required=True)
    pairs.add_argument("--case", nargs=2, action="append", metavar=("BEFORE_REPORT", "AFTER_REPORT"), required=True)
    pairs.add_argument("--out", required=True)
    pairs.add_argument("--sealed-map", required=True)
    pairs.add_argument("--review-a", required=True)
    pairs.add_argument("--review-b", required=True)

    pair_view = modes.add_parser("pair-html", help="Offline blinded paired-alert grading UI")
    pair_view.add_argument("--pairs", required=True)
    pair_view.add_argument("--out", required=True)

    score = modes.add_parser("score", help="Score only two complete independent blind reviews")
    score.add_argument("--pairs", required=True)
    score.add_argument("--sealed-map", required=True)
    score.add_argument("--gold", required=True)
    score.add_argument("--review-a", required=True)
    score.add_argument("--review-b", required=True)
    score.add_argument("--out", required=True)
    a = p.parse_args()

    if a.mode == "source-pack":
        packet = build_source_packet([(load(src), load(scope, scope=True)) for src, scope in a.case])
        save(a.out, packet)
        save(a.review_a, blank_source_review(packet))
        save(a.review_b, blank_source_review(packet))
        print(json.dumps({"status": packet["status"], "articles": len(packet["sources"]),
                          "sections": len(packet["sections"]), "source_lock": packet["source_lock"]}))
    elif a.mode == "source-html":
        if not a.out.endswith(".html"):
            raise ValueError("Private reviewer UI must be an HTML file")
        packet = load(a.source_pack)
        save(a.out, render_source_workbench(packet))
        print(json.dumps({"status": "PRIVATE_SOURCE_REVIEW_UI_READY",
                          "sections": len(packet["sections"])}))
    elif a.mode == "seal-gold":
        gold = seal_source_gold(load(a.source_pack), load(a.review_a), load(a.review_b),
                                load(a.adjudication) if a.adjudication else None)
        save(a.out, gold)
        print(json.dumps({"status": gold["status"],
                          "disagreements": gold["disagreement_count"]}))
    elif a.mode == "pair-pack":
        if "sealed" not in private_path(a.sealed_map).parts:
            raise PermissionError("Sealed model-version mapping must use a private sealed/ directory")
        packet, gold = load(a.source_pack), load(a.gold)
        blind, mapping = build_blind_pairs(packet, gold,
                                           [(load(old), load(new)) for old, new in a.case])
        save(a.out, blind)
        save(a.sealed_map, mapping)
        save(a.review_a, blank_pair_review(blind))
        save(a.review_b, blank_pair_review(blind))
        print(json.dumps({"status": blind["status"], "pairs": len(blind["pairs"])}))
    elif a.mode == "pair-html":
        if not a.out.endswith(".html"):
            raise ValueError("Private reviewer UI must be an HTML file")
        pairs_packet = load(a.pairs)
        save(a.out, render_pair_workbench(pairs_packet))
        print(json.dumps({"status": "PRIVATE_BLIND_PAIR_UI_READY",
                          "pairs": len(pairs_packet["pairs"])}))
    else:
        result = score_blind_review(load(a.pairs), load(a.sealed_map), load(a.gold),
                                    load(a.review_a), load(a.review_b))
        save(a.out, result)
        print(json.dumps({"status": result["status"],
                          "review_opportunity_confusion": result["review_opportunity_confusion"],
                          "mean_notice_actionability_out_of_3": result["mean_notice_actionability_out_of_3"]}))


if __name__ == "__main__":
    main()
