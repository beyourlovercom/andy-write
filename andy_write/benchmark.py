"""Read-only QC 2025 sample comparator: derived metrics only, never save entire articles."""
from __future__ import annotations
import json
import re
import statistics
import subprocess
from html import unescape
from .io import now
from .research import validate_public_url
from .review import metrics

QC_API = ("https://kissself.com/wp-json/wp/v2/posts?"
          "after=2025-11-01T00:00:00&before=2026-01-01T00:00:00"
          "&per_page=100&_fields=id,title,content,link,date")

def scrape_qc_metrics() -> dict:
    validate_public_url(QC_API)
    proc = subprocess.run(["curl", "-L", "--proto", "=https", "--proto-redir", "=https",
                            "--silent", "--show-error", "--fail-with-body", "--max-time", "40",
                            "--max-filesize", "9000000", QC_API],
                           capture_output=True, text=True, timeout=45)
    if proc.returncode:
        raise RuntimeError(f"QC read-only public API failed: {proc.stderr[:160]}")
    rows = json.loads(proc.stdout)
    if not isinstance(rows, list):
        raise RuntimeError("Unexpected QC API result; refusing to fabricate benchmark")
    samples = []
    for row in rows:
        if not (row["date"][:7] in ("2025-11", "2025-12")):
            continue
        html = row["content"]["rendered"]
        clean = unescape(re.sub(r"<[^>]*>", " ", html))
        text = " ".join(clean.split())
        samples.append({"id": row["id"], "date": row["date"][:10],
                        "title": unescape(re.sub(r"<[^>]*>", "", row["title"]["rendered"])),
                        "url": row["link"], "words": len(re.findall(r"\b[\w'-]+\b", text)),
                        "h2": len(re.findall(r"<h2[ >]", html, re.I)),
                        "h3": len(re.findall(r"<h3[ >]", html, re.I)),
                        "tables": len(re.findall(r"<table[ >]", html, re.I)),
                        "images": len(re.findall(r"<img\b", html, re.I)),
                        "has_faq": bool(re.search(r"<h2[^>]*>\s*FAQ", html, re.I))})
    def med(name):
        return statistics.median(s[name] for s in samples) if samples else None
    return {"source": QC_API, "collection": "public_wordpress_rest_read_only",
            "model_provenance": "QC attribution reported by website owner; not independently verified",
            "scope": "2025-11-01 to 2025-12-31 inclusive", "sample_count": len(samples),
            "collected_at": now(),
            "median": {k: med(k) for k in ("words", "h2", "h3", "tables", "images")},
            "faq_count": sum(s["has_faq"] for s in samples),
            "representative": [{"id": r["id"], "date": r["date"], "title": r["title"], "url": r["url"]}
               for r in samples if "Sex Doll" in r["title"] or "How Do I Know If My Lube" in r["title"]][:5],
            "note": "Derived metadata only. No QC article body stored or reused."}

def compare_draft(benchmark: dict, article: str) -> dict:
    mine = metrics(article)
    return {"our_draft": mine, "qc_medians": benchmark.get("median"),
            "caveat": "Structural comparison only; quality requires factual and blind human review."}
