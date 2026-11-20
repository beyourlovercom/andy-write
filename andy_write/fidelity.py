"""V1.2 offline source-fidelity diagnostics, NOT semantic/factual verification.

Never calls Codex/LLMs, network, image or video generators. A lexical match is
a REVIEW CANDIDATE, not proof of semantic retention.
"""
from __future__ import annotations
from collections import Counter
import re
from .io import hashtext, now

CONTRACT = "andy-write-source-fidelity-v1.2"
STOP = set("""
a an and are as at be been being but by can could did do does for from had
has have he her his how i if in into is it its may might must my no not of on
or our out over she should so than that the their there these they this those
to was were what when where which while who will with would you your about
also all any before after then first second third very use using used one two
only more most other such through some each every here still just like keep
want make because now time been them can both need following below above
""".split())
TOKEN = re.compile(r"[a-z0-9]+(?:['’\-][a-z0-9]+)?|[\u4e00-\u9fff]", re.I)
PARAGRAPH = re.compile(r"\n\s*\n")
UNIT_MIN_CONTENT_WORDS = 8
NUMERIC_WITH_UNIT = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s?(?:kg|kgs|lb|lbs|mm|cm|inches?|"
    r"hours?|days?|weeks?|months?|years?|percent|%|°c|°f|usd)|"
    r"\$\s?\d+(?:\.\d+)?)\b", re.I
)

def strip_markup(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\((?:https?://[^)]+)\)", r"\1", text)
    text = re.sub(r"</?[\w-]+(?:\s+[^>]*?)?>", " ", text)
    text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|[-*]\s+|\d+[.)]\s+)", "", text)
    text = re.sub(r"[*_~]", "", text).replace(chr(96), "")
    return re.sub(r"\s+", " ", text).strip()

def canonical(text: str) -> str:
    return " ".join(TOKEN.findall(strip_markup(text).casefold()))

def content_terms(text: str) -> set[str]:
    return {t for t in TOKEN.findall(strip_markup(text).casefold())
            if t not in STOP and (len(t) >= 3 or "\u4e00" <= t <= "\u9fff")}

def source_units(article: str) -> list[dict]:
    """Track meaningful prose units; short headings are deliberately not scored."""
    rows = []
    for n, part in enumerate(PARAGRAPH.split(article), 1):
        cleaned = strip_markup(part)
        if len(content_terms(cleaned)) < UNIT_MIN_CONTENT_WORDS or len(cleaned) < 45:
            continue
        rows.append({
            "id": f"SRC-P{n:04d}", "paragraph": n,
            "source_sha256": hashtext(part), "characters": len(part),
            "terms": content_terms(part), "canonical": canonical(part),
        })
    # Within-document distinctiveness prevents generic shared sentences from
    # falsely matching a deleted source section. Rare keywords are evidence
    # for review candidates, not proof of semantic equivalence.
    frequency = Counter(term for row in rows for term in row["terms"])
    max_frequency = max(1, int(len(rows)*0.35))
    for row in rows:
        row["distinctive_terms"] = {
            t for t in row["terms"] if frequency[t] <= max_frequency}
    return rows

def target_windows(article: str) -> list[dict]:
    paragraphs = [p for p in PARAGRAPH.split(article) if strip_markup(p)]
    windows = []
    for i in range(len(paragraphs)):
        for size in (1, 2, 3):
            if i + size > len(paragraphs):
                continue
            part = "\n\n".join(paragraphs[i:i+size])
            windows.append({
                "start_paragraph": i+1, "end_paragraph": i+size,
                "canonical": canonical(part),
                "terms": content_terms(part),
            })
    return windows

def candidate_match(unit: dict, windows: list[dict]) -> dict:
    best = {"state": "UNMAPPED_REVIEW", "lexical_recall": 0.,
            "lexical_precision": 0., "target_paragraphs": None}
    best_score = 0.
    for window in windows:
        if unit["canonical"] and unit["canonical"] in window["canonical"]:
            return {"state": "EXACT_TEXT_PRESENT",
                    "lexical_recall": 1., "lexical_precision": 1.,
                    "target_paragraphs": [window["start_paragraph"], window["end_paragraph"]]}
        overlap = unit["terms"] & window["terms"]
        distinctive = unit.get("distinctive_terms") or set()
        rare_overlap = distinctive & window["terms"]
        rare_recall = len(rare_overlap)/len(distinctive) if distinctive else 0.
        recall = len(overlap)/len(unit["terms"]) if unit["terms"] else 0.
        precision = len(overlap)/len(window["terms"]) if window["terms"] else 0.
        score = recall*.85 + precision*.15
        if score > best_score:
            best_score = score
            best = {
                "state": ("LEXICAL_CANDIDATE"
                          if recall >= .58 and len(overlap) >= 5
                          and len(rare_overlap) >= 2 and rare_recall >= .50
                          else "UNMAPPED_REVIEW"),
                "distinctive_anchor_recall": round(rare_recall, 4),
                "distinctive_anchor_count": len(distinctive),
                "lexical_recall": round(recall, 4),
                "lexical_precision": round(precision, 4),
                "target_paragraphs": [window["start_paragraph"],
                                      window["end_paragraph"]] if overlap else None,
            }
    return best

def numeric_claim_candidates(text: str) -> set[str]:
    return {re.sub(r"\s+", "", x.casefold())
            for x in NUMERIC_WITH_UNIT.findall(strip_markup(text))}

def inspect_fidelity(source: str, draft: str, *,
                     source_ref: str | None = None,
                     reviewer_notes: list[dict] | None = None) -> dict:
    if len("".join(source.split())) < 900:
        raise ValueError("Fidelity requires a substantive real source article")
    if not draft.strip():
        raise ValueError("No draft supplied")
    units = source_units(source)
    if not units:
        raise ValueError("No substantive paragraphs found")
    windows = target_windows(draft)
    target_terms = content_terms(draft)
    evidence = []
    # No paragraph silently disappears. Short notes, headings and one-liners
    # get their own private review record rather than entering lexical scoring.
    all_parts = PARAGRAPH.split(source)
    eligible = {row["paragraph"] for row in units}
    unscored = [{
        "source_id": f"SRC-P{i:04d}",
        "source_paragraph_number": i,
        "source_sha256": hashtext(part),
        "source_characters": len(part),
        "state": "SHORT_OR_HEADING_REVIEW",
        "reviewer_status": "PENDING",
        "note": "Not suitable for automatic lexical scoring; manual review",
    } for i,part in enumerate(all_parts,1) if i not in eligible]
    for unit in units:
        match = candidate_match(unit, windows)
        anchors = unit.get("distinctive_terms") or set()
        anchor_matches = anchors & target_terms
        evidence.append({
            "source_id": unit["id"],
            "source_sha256": unit["source_sha256"],
            "source_paragraph_number": unit["paragraph"],
            "source_characters": unit["characters"],
            "distinctive_anchors_total": len(anchors),
            "distinctive_anchors_in_draft": len(anchor_matches),
            **match,
            "reviewer_status": "PENDING",
        })
    by_id = {row["source_id"]: row for row in (evidence + unscored)}
    for note in reviewer_notes or []:
        sid = note.get("source_id")
        row = by_id.get(sid)
        if row is None or note.get("source_sha256") != row["source_sha256"]:
            raise ValueError("Reviewer note has unknown/stale source ID or hash")
        status = note.get("status")
        if status not in ("RETAINED", "CHANGED_WITH_APPROVAL", "INTENTIONALLY_OMITTED"):
            raise ValueError("Invalid human review status")
        if not note.get("reviewer") or len(str(note.get("reason","")).strip()) < 12:
            raise ValueError("Human reviewer and substantive rationale required")
        quoted = str(note.get("target_quote","")).strip()
        if status in ("RETAINED","CHANGED_WITH_APPROVAL") and (
            len(quoted) < 12 or quoted not in draft):
            raise ValueError("Positive review needs literal target quote")
        row["reviewer_status"] = status
        row["reviewer"] = str(note["reviewer"])[:120]
        row["reviewed_reason"] = str(note["reason"])[:500]
        row["review_target_quote_sha256"] = hashtext(quoted) if quoted else None
    states = Counter(row["state"] for row in evidence)
    reviewed = Counter(row["reviewer_status"] for row in (evidence + unscored))
    new_numbers = sorted(numeric_claim_candidates(draft)-numeric_claim_candidates(source))
    total = len(evidence)
    all_count = len(evidence) + len(unscored)
    anchors_total = sum(x["distinctive_anchors_total"] for x in evidence)
    anchors_found = sum(x["distinctive_anchors_in_draft"] for x in evidence)
    return {
        "contract_version": CONTRACT, "created_at": now(),
        "source_ref": source_ref,
        "source_sha256": hashtext(source), "draft_sha256": hashtext(draft),
        "metric_scope": "Lexical traceability, NOT semantic or factual retention",
        "source_text_disclosed": False,
        "human_factual_approval": "PENDING",
        "status": "HUMAN_REVIEW_REQUIRED",
        "summary": {
            "source_units_considered": total,
            "source_paragraphs_total": len(PARAGRAPH.split(source)),
            "exact_text_present_units": states["EXACT_TEXT_PRESENT"],
            "lexical_candidate_units": states["LEXICAL_CANDIDATE"],
            "unmapped_units_needing_review": states["UNMAPPED_REVIEW"],
            "exact_text_presence_percent": round(100*states["EXACT_TEXT_PRESENT"]/total,2),
            "distinctive_token_presence_percent": round(
                100*anchors_found/anchors_total,2) if anchors_total else None,
            "distinctive_source_token_occurrences": anchors_total,
            "distinctive_token_occurrences_in_draft": anchors_found,
            "source_paragraphs_not_scored": len(unscored),
            "short_or_heading_items_pending": sum(
                x["reviewer_status"] == "PENDING" for x in unscored),
            "all_source_paragraphs_accounted_for": all_count == len(all_parts),
            "source_items_total_including_short": all_count,
            "human_review_pending_units": reviewed["PENDING"],
            "human_retained_units": reviewed["RETAINED"],
            "human_approved_changed_units": reviewed["CHANGED_WITH_APPROVAL"],
            "human_intentionally_omitted_units": reviewed["INTENTIONALLY_OMITTED"],
            "human_review_completion_percent": round(
                100*(all_count-reviewed["PENDING"])/all_count,2),
            "new_numeric_claim_candidates": new_numbers[:30],
        },
        "units": evidence, "short_or_heading_units": unscored,
    }

def review_sheet(report: dict) -> str:
    """Build a private Owner/Editor worksheet without copying original prose."""
    if report.get("contract_version") != CONTRACT:
        raise ValueError("Unsupported fidelity report version")
    lines = [
        "# Andy Write V1.2 — Source Fidelity Manual Review",
        "",
        "**Machine lexical signals are not semantic retention or factual verification.**",
        "Compare the actual private source and draft; do not mark a change as retained",
        "solely because it shares words. Note intentional deletion of unsafe advice.",
        "",
        "| Original paragraph | Candidate target paragraphs | Machine state | Distinctive terms present | Human decision |",
        "|---|---|---|---:|---|",
    ]
    for item in report["units"] + report.get("short_or_heading_units", []):
        window = item.get("target_paragraphs")
        where = (f"{window[0]}–{window[1]}" if window else "not mapped")
        value = (f"{item['distinctive_anchors_in_draft']}/"
                 f"{item['distinctive_anchors_total']}"
                 if "distinctive_anchors_total" in item else "not scored")
        lines.append("| " + " | ".join([
            item["source_id"], where, item["state"], value,
            item.get("reviewer_status", "PENDING")
        ]) + " |")
    lines.extend([
        "",
        "## Manual decision protocol",
        "",
        "1. Open the private original and draft; compare each numbered paragraph.",
        "2. Mark RETAINED, CHANGED_WITH_APPROVAL or INTENTIONALLY_OMITTED.",
        "3. For changed/removed instructions, note the reason and any safety caveat.",
        "4. A positive retention decision must cite a literal target quote and reviewer.",
        "5. Keep human notes in private .runs and rerun fidelity --notes; never",
        "   claim full human approval without actual review of all paragraphs.",
        "",
        "No images/videos or Codex calls are involved in this workflow.",
    ])
    return "\n".join(lines) + "\n"
