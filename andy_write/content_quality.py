"""Editor-focused quality diagnostics, not an AI-content detector.

Signals are grounded in observable text and source records. They measure
coverage, useful detail, originality of expression, and evidence handling,
not the probability that a human or a model authored the words.
"""
from __future__ import annotations
from collections import Counter
import json
import re
from urllib.parse import urlsplit
from .io import now

EMPTY_PHRASES = (
    "in the realm of", "embark on a journey", "treasure trove",
    "tapestry of", "delve into", "unlock the secrets",
    "ever-evolving landscape", "in today's fast-paced",
    "it is important to note", "it's important to note",
    "a world of possibilities", "game-changing", "seamless experience",
    "let's dive in", "without further ado", "as we explore",
    "in this comprehensive guide", "navigate the complexities",
    "at the end of the day", "a comprehensive understanding"
)
# These are observable actions, not a guarantee of helpfulness.
READER_ACTIONS = (
    "check", "compare", "save", "photograph", "document", "inspect",
    "place", "lift", "move", "keep", "confirm", "record", "read",
    "stop", "ask", "contact", "remove", "open", "support",
    "match", "protect", "prepare", "set aside", "arrange",
    "look for", "follow", "avoid", "note", "identify",
    "measure", "review", "verify"
)
SUSPECT_CLAIMS = (
    r"\bscientifically proven\b",
    r"\b(?:studies|research) (?:have )?(?:shown|proven)\b",
    r"\bmost (?:customers|owners|users) (?:say|agree|find)\b",
)
BODY_SECTIONS = re.compile(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", re.M | re.S)
MARKDOWN_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")

def split_sections(article: str) -> list[dict]:
    return [{"heading": m.group(1).strip(), "body": m.group(2).strip()}
            for m in BODY_SECTIONS.finditer(article)]

def edit_sections(original: str, replacements: dict[str, str]) -> str:
    """Patch only requested H2 bodies; all unrelated sections stay byte-identical."""
    seen = set()
    def replace(match: re.Match) -> str:
        heading = match.group(1).strip()
        if heading not in replacements:
            return match.group(0)
        seen.add(heading)
        new_body = replacements[heading].strip()
        if len(new_body.split()) < 30:
            raise ValueError("Replacement section is too short")
        return "## " + heading + "\n\n" + new_body + "\n\n"
    result = BODY_SECTIONS.sub(replace, original)
    if set(replacements) != seen:
        raise ValueError("Missing section(s) in original article")
    return result

def parse_rewritten_sections(model_response: str, wanted: list[str]) -> dict[str, str]:
    """Accept only exact H2 headings, no extra or missing changed sections."""
    present = split_sections(model_response)
    if len(present) != len(wanted) or {s["heading"] for s in present} != set(wanted):
        raise ValueError("Chapter rewrite returned unexpected headings")
    if len({s["heading"] for s in present}) != len(present):
        raise ValueError("Duplicate H2 section in model response")
    return {s["heading"]: s["body"] for s in present}

def normalize_intro(article: str) -> tuple[str, bool]:
    """Conservative, meaning-preserving 3-paragraph introduction normalization.

    Only splits an existing two-sentence second paragraph. Never inserts new
    facts or rewrites body content.
    """
    marker = "\n## "
    if marker not in article:
        return article, False
    prefix, suffix = article.split(marker, 1)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", prefix) if p.strip()]
    if len(paragraphs) != 3 or not paragraphs[0].startswith("# "):
        return article, False
    heading, opening, answer_and_bridge = paragraphs
    if "**" in answer_and_bridge:
        return article, False
    sentences = re.split(r"(?<=[.!?])\s+", answer_and_bridge, maxsplit=1)
    if len(sentences) != 2:
        return article, False
    direct, bridge = sentences
    if len(direct.split()) < 5 or len(bridge.split()) < 5:
        return article, False
    normalized = (heading + "\n\n" + opening + "\n\n**" +
                  direct + "**\n\n" + bridge + "\n\n## " + suffix)
    return normalized, True

def intro_structure(article: str) -> dict:
    head = article.split("\n## ", 1)[0]
    blocks = [s.strip() for s in re.split(r"\n\s*\n", head) if s.strip()]
    paragraphs = [p for p in blocks if not p.startswith("# ")]
    return {
        "paragraphs": len(paragraphs),
        "direct_answer_bold": len(paragraphs) >= 2 and
                              paragraphs[1].startswith("**") and
                              paragraphs[1].endswith("**"),
    }

def audit(article: str, job: dict, research_pack: dict | None = None,
          source_catalog: dict | None = None) -> dict:
    """Visible diagnostics with article section and genuine source status."""
    sec = [s for s in split_sections(article) if s["heading"] != "Conclusion"]
    lower = article.lower()
    issues: list[dict] = []
    clichés = [{"phrase": p, "count": len(re.findall(re.escape(p), lower))}
               for p in EMPTY_PHRASES if p in lower]
    for x in clichés:
        issues.append({"code": "GENERIC_FILLER", "severity": "review",
                       "heading": None, "detail": x["phrase"]})
    for pattern in SUSPECT_CLAIMS:
        for m in re.finditer(pattern, article, re.I):
            issues.append({"code": "SOURCELESS_AUTHORITY", "severity": "review",
                           "heading": None, "detail": m.group()[:90]})
    introduction = intro_structure(article)
    if introduction["paragraphs"] != 3 or not introduction["direct_answer_bold"]:
        issues.append({"code": "INTRO_STRUCTURE", "severity": "review",
                       "heading": None,
                       "detail": "Introduction needs opening, bold direct answer, and bridge"})
    actions_by_section: list[dict] = []
    for s in sec:
        text = s["body"]
        tokens = re.findall(r"\b[a-z]+(?:'[a-z]+)?\b", text.lower())
        words = len(tokens)
        matches = {act for act in READER_ACTIONS
                   if re.search(r"\b" + re.escape(act) + r"\b", text, re.I)}
        actions_by_section.append({
            "heading": s["heading"], "words": words,
            "distinct_action_terms": len(matches), "action_terms": sorted(matches)
        })
        if words < 65:
            issues.append({"code": "THIN_SECTION", "severity": "review",
                           "heading": s["heading"], "detail": f"{words} words"})
        if len(matches) < 2:
            issues.append({"code": "LOW_PRACTICAL_DETAIL", "severity": "review",
                           "heading": s["heading"],
                           "detail": f"Only {len(matches)} distinct action terms"})
    # Source statuses and links are separate: fetch-success never means fact-proven.
    urls = MARKDOWN_LINK.findall(article)
    internal, external = [], []
    brand_domain = job.get("brand_domain", "pairdoll.com")
    for uri in urls:
        host = urlsplit(uri).hostname or ""
        if host == brand_domain or host.endswith("." + brand_domain):
            internal.append(uri)
        else:
            external.append(uri)
    available = {row.get("url") for row in (research_pack or {}).get("sources", [])
                 if row.get("status") == "retrieved"}
    for uri in external:
        if research_pack is not None and uri not in available:
            issues.append({"code": "UNVERIFIED_EXTERNAL_LINK", "severity": "review",
                           "heading": None, "detail": uri})
    if research_pack is not None:
        if available and not external:
            issues.append({"code": "NO_SUPPORTING_EXTERNAL_LINK", "severity": "review",
                           "heading": None, "detail": "Relevant retrieved sources available"})
        if not internal:
            issues.append({"code": "MISSING_INTERNAL_LINK", "severity": "review",
                           "heading": None, "detail": "Link to a verified existing article if relevant"})
    # Specificity is required only when an anchor exists in the OWNER-SUPPLIED
    # reference. An optional detail is never a universal model specification.
    source_ids = {s.get("id"): s for s in (source_catalog or {}).get("segments", [])}
    verified_anchors = []
    for anchor in job.get("editorial_anchor_terms", []):
        phrase = anchor.get("term", "")
        source_id = anchor.get("source_id", "")
        if not phrase or not source_id or source_id not in source_ids:
            continue
        source_excerpt = source_ids[source_id].get("excerpt", "")
        if phrase.lower() not in source_excerpt.lower():
            continue
        verified_anchors.append(anchor)
        if phrase.lower() not in lower:
            hint = anchor.get("section_hint", "").lower()
            target = next((s["heading"] for s in sec
                           if hint and hint in s["heading"].lower()), None)
            issues.append({"code": "MISSING_REFERENCE_DETAIL", "severity": "review",
                           "heading": target, "detail": phrase,
                           "source_id": source_id,
                           "note": "May be model-dependent; describe conditionally"})
    actionable_sections = len([s for s in actions_by_section
                               if s["words"] >= 65 and s["distinct_action_terms"] >= 2])
    return {
        "job_id": job.get("job_id"),
        "created_at": now(),
        "description": "Textual people-first editorial diagnostics; NOT AI-origin detection or factual verification",
        "sections": actions_by_section,
        "introduction": introduction,
        "actionable_sections": actionable_sections,
        "total_sections": len(sec),
        "cliche_phrases": clichés,
        "eligible_source_detail_count": len(verified_anchors),
        "source_details_present": sum(
            a.get("term", "").lower() in lower for a in verified_anchors),
        "links": {"internal": internal, "external": external,
                  "retrieved_source_urls": sorted(u for u in available if u)},
        "issues": issues,
        "status": "REVIEW" if issues else "RULE_CHECK_PASS",
        "human_fact_check": "PENDING"
    }

def review_targets(quality: dict) -> list[str]:
    """Pick only affected H2s; preserving the rest of the article byte-for-byte."""
    headings = {i.get("heading") for i in quality["issues"]
                if i.get("code") in ("THIN_SECTION", "LOW_PRACTICAL_DETAIL",
                                    "MISSING_REFERENCE_DETAIL") and i.get("heading")}
    titles = [s["heading"] for s in quality["sections"]]
    codes = {i["code"] for i in quality["issues"]}
    if "NO_SUPPORTING_EXTERNAL_LINK" in codes:
        best = next((h for h in titles if "move" in h.lower() or "unpack" in h.lower()), None)
        if best:
            headings.add(best)
    if "MISSING_INTERNAL_LINK" in codes:
        best = next((h for h in titles if "inspection" in h.lower()), None)
        if best:
            headings.add(best)
    return [h for h in titles if h in headings][:3]
