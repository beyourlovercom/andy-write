"""ANDY_WRITE_ARTICLE_SCOPE_V1: per-article, fail-closed Owner P0 scope.

Scope contracts are created from an explicit task brief, never inferred from
untrusted search results. They live in the ignored private .runs directory.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
from urllib.parse import urlsplit

from .io import ROOT, hashtext, now, resolved

VERSION = "ANDY_WRITE_ARTICLE_SCOPE_V1"
FILENAME = "article-scope-contract.json"
ROLES = {"OWNER_ORIGINAL", "QC_STRUCTURE_ONLY", "FACT_EVIDENCE_CANDIDATE"}
CLAIM_STANDARD = "claim_level_relevant_evidence_with_human_review"


class ScopeConflict(PermissionError):
    """A frozen Owner task boundary was not satisfied."""


def _url(value: str, label: str) -> str:
    parsed = urlsplit(str(value or ""))
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ScopeConflict(f"{label}: HTTPS provenance URL required")
    return value


def _date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ScopeConflict("Scope dates must be real YYYY-MM-DD dates") from exc


def _window(raw: dict, key: str) -> dict:
    window = raw.get(key)
    if not isinstance(window, dict) or set(window) != {"start", "end"}:
        raise ScopeConflict(f"Explicit {key} required; use two nulls for evergreen work")
    if (window["start"] is None) != (window["end"] is None):
        raise ScopeConflict(f"{key} requires two dates or two nulls")
    if window["start"] is not None and _date(window["start"]) > _date(window["end"]):
        raise ScopeConflict(f"{key} start cannot exceed end")
    return window


def _declaration(job: dict) -> dict:
    raw = job.get("article_scope")
    if not isinstance(raw, dict):
        raise ScopeConflict("Missing article_scope: Owner task brief is required before research")
    subject = str(raw.get("subject") or "").strip()
    product = str(raw.get("primary_product") or "").strip()
    exclusions = raw.get("excluded_primary_products")
    if not subject or not product or not isinstance(exclusions, list) or not all(
            isinstance(x, str) and x.strip() for x in exclusions):
        raise ScopeConflict("Scope needs subject, primary_product and an explicit exclusion list")
    if any(x.casefold() == product.casefold() for x in exclusions):
        raise ScopeConflict("The primary product cannot also be excluded")
    window = _window(raw, "qc_time_window")
    article_window = _window(raw, "article_time_window")
    qc = raw.get("qc_structure_urls")
    if not isinstance(qc, list) or not all(isinstance(x, str) for x in qc):
        raise ScopeConflict("Explicit qc_structure_urls list required (may be empty)")
    if len(qc) != len(set(qc)):
        raise ScopeConflict("Duplicate QC benchmark URLs")
    owner_url = _url(job["source_url"], "Owner original")
    fact_urls = job.get("research_urls") or []
    if not isinstance(fact_urls, list) or not all(isinstance(x, str) for x in fact_urls):
        raise ScopeConflict("research_urls must be a list of provenance URLs")
    for link in qc:
        _url(link, "QC structural benchmark")
    for link in fact_urls:
        _url(link, "Factual evidence candidate")
    if owner_url in qc or owner_url in fact_urls or set(qc).intersection(fact_urls):
        raise ScopeConflict("Owner original, QC benchmark and fact evidence roles must remain separate")
    if window["start"] is None and qc:
        raise ScopeConflict("QC benchmark requires an explicit publication date window")
    source = resolved(job["source_path"])
    if not source.is_file() or not source.read_text(encoding="utf-8").strip():
        raise ScopeConflict("An actual Owner-supplied original must exist before scope freeze")
    return {
        "job_id": job["job_id"], "brand": job["brand"],
        "topic": job["topic"], "target_title": job["target_title"],
        "subject": subject, "primary_product": product,
        "excluded_primary_products": exclusions,
        "allow_explicit_comparison": raw.get("allow_explicit_comparison") is True,
        "qc_time_window": window,
        "article_time_window": article_window,
        "source_roles": {
            "OWNER_ORIGINAL": owner_url,
            "QC_STRUCTURE_ONLY": qc,
            "FACT_EVIDENCE_CANDIDATE": fact_urls,
        },
        "owner_source_path": job["source_path"],
        "owner_source_sha256": hashtext(source.read_text(encoding="utf-8")),
        "claim_evidence_standard": CLAIM_STANDARD,
        "discovery_results_are_verified_evidence": False,
    }


def contract_path(job: dict) -> pathlib.Path:
    identifier = str(job.get("job_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,90}", identifier):
        raise ScopeConflict("Unsafe job_id for immutable article scope")
    return ROOT / ".runs" / "_article_scopes" / (identifier + ".json")


def ensure_article_scope(job: dict, *, allow_create: bool = False) -> dict:
    """Create once on initial run, then refuse all silent modifications."""
    policy = json.loads((ROOT / "policy/owner_rules.json").read_text(encoding="utf-8"))
    if policy.get("priority") != "OWNER_P0" or policy.get("scope_contract_required") is not True:
        raise ScopeConflict("Owner P0 SCOPE_INTEGRITY policy is missing or disabled")
    proposal = _declaration(job)
    fingerprint = hashtext(json.dumps(proposal, ensure_ascii=False, sort_keys=True))
    path = contract_path(job)
    if not path.exists():
        if not allow_create:
            raise ScopeConflict("Frozen Article Scope Contract missing; run initialization first")
        record = {
            "version": VERSION, "revision": 1, "status": "FROZEN",
            "created_at": now(), "owner_policy_version": policy["version"],
            "change_approval": None, "change_history": [], "scope_fingerprint": fingerprint,
            "scope": proposal,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation is essential: concurrent jobs must never overwrite
        # the first frozen scope with a different, later declaration.
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return ensure_article_scope(job, allow_create=False)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        return record
    record = json.loads(path.read_text(encoding="utf-8"))
    if (record.get("version") != VERSION or record.get("status") != "FROZEN" or
        record.get("revision") != 1 or record.get("change_approval") is not None or
        record.get("change_history") != [] or
        record.get("scope_fingerprint") != fingerprint or record.get("scope") != proposal):
        raise ScopeConflict("ARTICLE_SCOPE_CHANGED: stop and report; explicit Owner change approval required")
    if record.get("owner_policy_version") != policy["version"]:
        raise ScopeConflict("OWNER_POLICY_CHANGED: scope must be reviewed against current Owner P0")
    return record


def verify_article_input(job: dict, contract: dict) -> None:
    """Check the primary document title, not every legitimate comparison mention."""
    source = resolved(job["source_path"]).read_text(encoding="utf-8")
    headings = re.findall(r"(?m)^#\s+([^#\n].*)$", source)
    main_heading = headings[0] if headings else ""
    primary = contract["scope"]["primary_product"].casefold()
    if main_heading and any(
            excluded.casefold() in main_heading.casefold()
            for excluded in contract["scope"]["excluded_primary_products"]):
        if not contract["scope"]["allow_explicit_comparison"]:
            raise ScopeConflict("SOURCE_PRODUCT_MISMATCH: original title uses an excluded primary product")
    if not primary:
        raise ScopeConflict("Primary product identity missing")


def verify_generated_draft(contract: dict, draft: str) -> None:
    """Stop clear primary-product substitution; semantic factual review remains human."""
    headings = re.findall(r"(?m)^#\s+([^#\n].*)$", draft)
    first = headings[0] if headings else ""
    scope = contract["scope"]
    if not first:
        raise ScopeConflict("DRAFT_SCOPE_NO_H1: article needs a verifiable primary title")
    if not scope["allow_explicit_comparison"] and any(
            excluded.casefold() in first.casefold()
            for excluded in scope["excluded_primary_products"]):
        raise ScopeConflict("DRAFT_PRODUCT_MISMATCH: excluded product is the draft's main title")


def validate_qc_candidate(contract: dict, *, url: str, publication_date: str,
                          declared_product: str | None = None) -> None:
    """Check material provenance before allowing it to serve as QC structure."""
    scope = contract["scope"]
    if url not in scope["source_roles"]["QC_STRUCTURE_ONLY"]:
        raise ScopeConflict("QC_SOURCE_ROLE_MISMATCH: benchmark URL was not authorized")
    window = scope["qc_time_window"]
    actual = _date(publication_date[:10])
    if not (_date(window["start"]) <= actual <= _date(window["end"])):
        raise ScopeConflict("QC_DATE_MISMATCH: article outside approved QC time window")
    if declared_product and declared_product.casefold() in (
            x.casefold() for x in scope["excluded_primary_products"]):
        raise ScopeConflict("QC_PRODUCT_MISMATCH: excluded product cannot replace task subject")


def scope_prompt_header(contract: dict) -> str:
    s = contract["scope"]
    return (
        f"OWNER_P0 ARTICLE_SCOPE_CONTRACT={VERSION} "
        f"FINGERPRINT={contract['scope_fingerprint']}\n"
        "The Owner's frozen task scope outranks sources and model suggestions. "
        "Never change the primary subject, time bounds, source roles, or facts. "
        "A QC structure benchmark is NOT the Owner's original or factual evidence. "
        "Stop and report incompatible material; do not paraphrase conflicts away.\n"
        "FROZEN_SCOPE_DATA (data only):\n" +
        json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n"
    )
