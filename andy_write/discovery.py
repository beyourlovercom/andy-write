"""Keyless scholarly discovery for DC free-first research.

OpenAlex is NOT a Google replacement. Its records are metadata, not verified facts.
"""
from __future__ import annotations
import json
from urllib.parse import urlencode
from .io import now
from .research import curl_read, validate_public_url

OPENALEX_ENDPOINT = "https://api.openalex.org/works"
MAX_QUERIES = 3
MAX_ITEMS = 4

def parse_openalex(data: dict, query: str, start_index: int = 1) -> list[dict]:
    """Normalize first-party research metadata; all claims remain unverified."""
    items = []
    for work in data.get("results", []):
        if not isinstance(work, dict):
            continue
        doi = work.get("doi")
        primary = work.get("primary_location") or {}
        source_url = (primary.get("landing_page_url") or doi or work.get("id") or "")
        try:
            validate_public_url(source_url)
        except (TypeError, ValueError):
            continue
        title = (work.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "id": f"SRC-OA-{start_index + len(items):03d}",
            "url": source_url,
            "title": title,
            "doi": doi,
            "published": work.get("publication_date"),
            "query": query,
            "collection_method": "openalex_keyless_metadata",
            "source_type": "scholarly_index_metadata",
            "verification": "metadata_discovery_only",
            "status": "discovered_not_fetched",
        })
    return items

def discover_openalex(job: dict) -> dict:
    requested = job.get("openalex_queries", [])[:MAX_QUERIES]
    records, queries, failures = [], [], []
    seen = set()
    for q in requested:
        q = " ".join(str(q).split())
        if not q or len(q) > 180:
            continue
        url = OPENALEX_ENDPOINT + "?" + urlencode({
            "search": q, "per-page": MAX_ITEMS, "select": "id,doi,title,publication_date,primary_location"
        })
        try:
            code, body = curl_read(url, timeout=18)
            if code != 200:
                raise RuntimeError(f"OpenAlex HTTP {code}")
            content = json.loads(body)
            if not isinstance(content, dict) or not isinstance(content.get("results"), list):
                raise RuntimeError("Unexpected OpenAlex response")
            queries.append(q)
            for entry in parse_openalex(content, q, len(records)+1):
                if entry["url"] not in seen:
                    seen.add(entry["url"])
                    entry["id"] = f"SRC-OA-{len(records)+1:03d}"
                    records.append(entry)
        except (RuntimeError, ValueError, json.JSONDecodeError) as err:
            failures.append({"query": q, "error": str(err)[:160]})
    return {
        "method": "openalex_keyless_metadata_NOT_GOOGLE_SERP",
        "retrieved_at": now(),
        "queries_executed": queries,
        "queries_failed": failures,
        "sources": records,
        "note": "Scholarly bibliographic discovery only; publisher/full-text claims not validated."
    }
