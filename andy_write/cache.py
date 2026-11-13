"""Free-mode research cache: prevent repeated requests and conserve public quotas."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import json
from .io import hashtext, write_json
from .research import research

INPUTS = ("job_id", "brand", "topic", "research_mode", "research_urls",
          "queries", "openalex_queries")

def fingerprint(job: dict) -> str:
    return hashtext(json.dumps(
        {field: job.get(field) for field in INPUTS}, sort_keys=True,
        ensure_ascii=False))

def cached_research(job: dict, output_dir, ttl_hours: int = 168) -> tuple[dict, bool]:
    """Seven-day cache for curated/DC free modes; never claim live refresh for cached data."""
    if job.get("research_mode", "curated") not in ("curated", "dc_free"):
        return research(job), False
    path = output_dir / "research-pack.json"
    key = fingerprint(job)
    if path.is_file() and ttl_hours > 0:
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            updated = datetime.fromisoformat(old["retrieved_at"])
            fresh = datetime.now(timezone.utc) - updated <= timedelta(hours=ttl_hours)
            if old.get("cache_fingerprint") == key and fresh:
                return old, True
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            pass
    pack = research(job)
    pack["cache_fingerprint"] = key
    write_json(path, pack)
    return pack, False
