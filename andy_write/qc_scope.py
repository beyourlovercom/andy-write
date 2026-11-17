"""Owner-authorized, immutable scope for offline competitor reverse-QC.

This is NOT an Article Scope Contract and never authorizes a new article,
rewriting competitor prose, or fact approval. The contract holds only public
metadata and the declared intent of an existing Owner article.
"""
from __future__ import annotations

from urllib.parse import urlsplit
import re

from .io import hashtext

QC_SCOPE_VERSION = "ANDY_WRITE_QC_SCOPE_V1"


def validate_qc_scope(snapshot: dict, contract: dict, draft_url: str) -> dict:
    """Fail closed if a public benchmark drifts from Owner's exact approval."""
    if contract.get("version") != QC_SCOPE_VERSION:
        raise ValueError("QC_SCOPE_VERSION_MISMATCH")
    if contract.get("owner_approval") != "EXPLICIT":
        raise PermissionError("QC_SCOPE_OWNER_APPROVAL_REQUIRED")
    reference = contract.get("benchmark", {})
    draft = contract.get("existing_owner_draft", {})
    if (reference.get("source_role") != "QC_STRUCTURE_ONLY" or
            draft.get("source_role") != "EXISTING_OWNER_ARTICLE"):
        raise PermissionError("QC_SCOPE_EVIDENCE_ROLE_MISMATCH")
    url = snapshot.get("link", "")
    if (not url.startswith("https://") or urlsplit(url).fragment or
            urlsplit(url).query or reference.get("url") != url or
            reference.get("post_id") != snapshot.get("id")):
        raise ValueError("QC_SCOPE_BENCHMARK_IDENTITY_CHANGED")
    if (reference.get("published_date") != snapshot.get("date", "")[:10] or
            reference.get("modified_date") != snapshot.get("modified", "")[:10] or
            reference.get("content_sha256") != hashtext(snapshot["content"]["rendered"])):
        raise ValueError("QC_SCOPE_BENCHMARK_REVISION_CHANGED")
    if draft.get("url") != draft_url or not draft_url.startswith("https://"):
        raise ValueError("QC_SCOPE_OWNER_ARTIFACT_CHANGED")
    benchmark_topic = reference.get("primary_topic", "").strip().casefold()
    owner_topic = draft.get("primary_topic", "").strip().casefold()
    benchmark_intent = reference.get("reader_intent", "").strip().casefold()
    owner_intent = draft.get("reader_intent", "").strip().casefold()
    excluded = [str(v).strip().casefold() for v in contract.get("excluded_primary_topics", [])]
    excluded_primary = any(
        re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", topic)
        for term in excluded if term for topic in (benchmark_topic, owner_topic))
    if (not benchmark_topic or not owner_topic or not benchmark_intent or
            not owner_intent or excluded_primary):
        raise ValueError("QC_SCOPE_TOPIC_OR_INTENT_INVALID")
    relation = ("SAME_DECLARED_INTENT_HUMAN_REVIEW_REQUIRED"
                if benchmark_intent == owner_intent else
                "CROSS_INTENT_STRUCTURE_ONLY")
    return {
        "version": QC_SCOPE_VERSION,
        "status": "FROZEN_QC_SCOPE",
        "benchmark_post_id": snapshot["id"],
        "benchmark_url": url,
        "benchmark_content_sha256": reference["content_sha256"],
        "benchmark_topic": benchmark_topic,
        "owner_topic": owner_topic,
        "intent_relation": relation,
        "source_roles": ["QC_STRUCTURE_ONLY", "EXISTING_OWNER_ARTICLE"],
        "release_gate": "HUMAN_FACT_AND_SEMANTIC_REVIEW_REQUIRED",
        "article_scope_created": False,
    }
