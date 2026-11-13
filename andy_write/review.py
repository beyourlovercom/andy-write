"""Lightweight deterministic editorial gate; semantic fact-check requires human or model."""
from __future__ import annotations
import re
from .io import now

INTERNAL_MARKERS = (
 "editorial image placement", "english article draft", "中文编辑与审核说明",
 "adapted from a detailed beginner", "todo:", "prompt for ai",
 "source guide lists", "owner review", "do not publish"
)
SUSPICIOUS_EXPERIENCE = (
 r"\bi (?:personally )?(?:tested|used|tried|unboxed|reviewed)\b",
 r"\bwe (?:personally )?(?:tested|used|tried|unboxed|reviewed)\b",
 r"\breal customers (?:say|report|agree)\b"
)

def metrics(markdown: str) -> dict:
    no_urls = re.sub(r"https?://\S+", "", markdown)
    tokens = re.findall(r"\b[\w'-]+\b", no_urls)
    h2s = re.findall(r"^## (.+)$", markdown, flags=re.M)
    links = re.findall(r"\]\((https?://[^)]+)\)", markdown)
    paras = [p.strip() for p in re.split(r"\n\s*\n", markdown) if len(p.strip()) > 80]
    repeated = len(paras) - len(set(paras))
    return {"words": len(tokens), "h2_count": len(h2s), "link_count": len(links),
            "paragraph_count": len(paras), "exact_duplicate_paragraphs": repeated,
            "image_slots": markdown.count("[image")}

def check(markdown: str, job: dict) -> dict:
    lower = markdown.lower()
    findings = []
    for marker in INTERNAL_MARKERS:
        if marker in lower:
            findings.append({"severity": "block", "code": "INTERNAL_NOTE", "detail": marker})
    for pattern in SUSPICIOUS_EXPERIENCE:
        if re.search(pattern, markdown, flags=re.I):
            findings.append({"severity": "review", "code": "FIRST_HAND_CLAIM", "detail": pattern})
    if re.search(r"^\[Claim", markdown, flags=re.M):
        findings.append({"severity": "block", "code": "UNRESOLVED_CLAIM", "detail": "[Claim] placeholder"})
    if "## Conclusion" not in markdown:
        findings.append({"severity": "review", "code": "MISSING_CONCLUSION"})
    for h2 in re.findall(r"^## (.+)$", markdown, flags=re.M):
        if h2 != "Conclusion" and re.search(
            r"\b(?:original guide|source article|editorial review|"
            r"need review|should be reviewed|draft version|"
            r"writing process|model output)\b", h2, re.I):
            findings.append({
                "severity":"review","code":"EDITORIAL_PROCESS_HEADING_LEAK",
                "detail":h2[:110]})
        if h2 != "Conclusion" and not h2.endswith("?"):
            findings.append({"severity": "review", "code": "NON_QUESTION_H2", "detail": h2})
    urls = re.findall(r"\]\((https?://[^)]+)\)", markdown)
    ext = [u for u in urls if not u.startswith("https://pairdoll.com/")]
    shopping_signals = ("amazon.com", "aliexpress.", "etsy.com", "shopify.com", "ebay.com")
    for url in ext:
        if any(term in url.lower() for term in shopping_signals):
            findings.append({"severity": "block", "code": "COMMERCE_EXTERNAL_LINK", "detail": url})
    result = metrics(markdown)
    if result["exact_duplicate_paragraphs"]:
        findings.append({"severity": "block", "code": "DUPLICATED_PARAGRAPH",
                         "detail": str(result["exact_duplicate_paragraphs"])})
    if not markdown.strip().startswith("# "):
        findings.append({"severity": "block", "code": "NO_H1"})
    return {"job_id": job["job_id"], "reviewed_at": now(), "metrics": result, "issues": findings,
            "status": "BLOCK" if any(f["severity"] == "block" for f in findings) else
                      ("REVIEW" if findings else "RULE_CHECK_PASS"),
            "caveat": "Static checks cannot verify facts, author experience, SEO rankings or human quality."}
