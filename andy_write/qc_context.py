"""Offline, scope-anchored candidate QC for a public HTML benchmark.

This deliberately does not make a semantic/factual truth verdict. Signals are
supplied by a frozen benchmark contract, not learned from the article body.
No remote fetch, LLM, article rewriting, or model-specific truth inference.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

from .io import hashtext, now

VERSION = "andy-write-context-qc/v1.1"
SPEC = re.compile(r"\b(?:IPX[4-9]|IP6[7-9]|\d+\s?ATM)\b", re.I)
SPEC_ASSERTION = re.compile(
    r"\b(?:submerg\w*|immers\w*|waterproof|water.resistant|"
    r"\d+\s?(?:minutes?|hours?|meters?|metres?|days?))\b", re.I)
CLEANING = re.compile(r"\b(?:vinegar|bleach|disinfect\w*|steriliz\w*|sanitiz\w*)\b", re.I)
PRICE = re.compile(r"(?:[$€£]\s?\d|\b(?:USD|EUR|GBP)\s?\d)", re.I)
OFFER = re.compile(r"\b(?:limited.time offer|special offer|flash sale|sale price)\b", re.I)
BATTERY_SPEC = re.compile(
    r"\b(?:charg(?:e|ing)(?:\s+time)?|battery\s+life|run\s*time|play\s*time)\b"
    r".{0,65}\b\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b", re.I)
MODEL_ID = re.compile(
    r"\b(?:model|sku|part\s*(?:number|no\.?))\s*[:#-]?\s*"
    r"(?!IPX[4-9]\b|IP6[7-9]\b)(?=[A-Z0-9-]*\d)"
    r"[A-Z0-9][A-Z0-9-]{2,}\b", re.I)
CONTRAST = re.compile(
    r"\b(?:unlike|rather than|not a|not the same as|do not confuse|"
    r"different from|instead of)\b", re.I)


class SectionReader(HTMLParser):
    """Extract contextual blocks, link URLs, and table rows from WP HTML."""

    TAGS = {"p", "li", "tr", "h2", "h3", "h4", "td", "th"}
    IGNORE = {"script", "style", "svg", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._active: list[dict] = []
        self._section = {"heading": "(article)", "anchor": ""}
        self._hierarchy: dict[int, tuple[str, str]] = {}
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag in self.IGNORE:
            self._ignored += 1
        if self._ignored:
            return
        if tag in self.TAGS:
            self._active.append({"tag": tag, "text": [], "links": [],
                                 "cells": [], "id": a.get("id") or a.get("data-anchor") or ""})
        if tag == "a":
            href = a.get("href") or ""
            for block in self._active:
                if href.startswith("https://"):
                    block["links"].append(href)

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        for block in self._active:
            block["text"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.IGNORE:
            self._ignored = max(0, self._ignored - 1)
            return
        if self._ignored:
            return
        for index in range(len(self._active) - 1, -1, -1):
            block = self._active[index]
            if block["tag"] != tag:
                continue
            self._active.pop(index)
            content = " ".join(" ".join(block["text"]).split())
            if not content:
                return
            if tag in {"td", "th"}:
                # Preserve column boundaries only in memory. Raw cell content
                # must never be placed in the persisted benchmark report.
                for ancestor in reversed(self._active):
                    if ancestor["tag"] == "tr":
                        ancestor["cells"].append(content)
                        break
                return
            if tag.startswith("h"):
                level = int(tag[1])
                for old in list(self._hierarchy):
                    if old >= level:
                        del self._hierarchy[old]
                self._hierarchy[level] = (content, block["id"])
                # A repeated H4 such as "Pros and Cons" must not erase the
                # product-specific parent H3. R8 has many identical H4 names.
                anchor_level = 3 if 3 in self._hierarchy else 2
                if anchor_level in self._hierarchy:
                    heading, explicit_id = self._hierarchy[anchor_level]
                    generated = re.sub(r"[^A-Za-z0-9 ]", "", heading)
                    generated = "_".join(generated.split())
                    self._section = {"heading": heading,
                                     "anchor": explicit_id or generated}
            else:
                self.blocks.append({"kind": "table_row" if tag == "tr" else tag,
                                    **self._section, "text": content,
                                    "links": sorted(set(block["links"])),
                                    "cells": block["cells"] if tag == "tr" else []})
            return


def _has(text: str, term: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I))


def _unnamed_offer(row: dict) -> bool:
    """A promotional phrase in a product-name cell is not a product identity."""
    cells = row.get("cells") or []
    if len(cells) >= 2:
        label = cells[0].strip()
        if OFFER.search(label) and PRICE.search(" ".join(cells[1:])):
            remainder = OFFER.sub("", label).strip(" :-–—|()[]")
            return not remainder
    # Minimal malformed or flattened table fallback.
    return bool(re.fullmatch(
        r"\s*(?:limited.time offer|special offer|flash sale|sale price)"
        r"\s+[$€£]\s?\d[\d.,]*\s*", row["text"], re.I))


def validate_contract(contract: dict, source: dict) -> None:
    if not isinstance(contract, dict) or contract.get("schema") != "andy-write-context-qc-scope/v1":
        raise ValueError("Explicit benchmark-only context QC scope contract required")
    expected = contract.get("source") or {}
    if (expected.get("source_role") != "public_competitor_qc_benchmark_only"
        or expected.get("post_id") != source.get("id")
        or expected.get("url") != source.get("link")
        or expected.get("modified") != source.get("modified")
        or expected.get("rendered_content_sha256") != hashtext(source["content"]["rendered"])):
        raise ValueError("R9_SOURCE_CONFLICT: WP identity, revision, role, or content SHA changed")
    scope = contract.get("scope")
    if (not isinstance(scope, dict) or not scope.get("subject")
        or not scope.get("primary_product_class") or not scope.get("audience")
        or scope.get("serp_intent_status") != "UNASSESSABLE"):
        raise ValueError("R9 requires explicit subject/product/audience and unknown SERP status")
    signals = contract.get("off_scope_signals")
    if not isinstance(signals, list) or not signals:
        raise ValueError("At least one explicitly scoped off-topic signal required")
    ids = set()
    for item in signals:
        if not isinstance(item, dict) or item.get("id") in ids:
            raise ValueError("Distinct off-scope signal IDs required")
        ids.add(item["id"])
        terms = item.get("terms")
        if (not isinstance(terms, list) or len(terms) < 2
            or not all(isinstance(t, str) and 2 <= len(t) <= 70 for t in terms)
            or not isinstance(item.get("min_distinct"), int)
            or not 2 <= item["min_distinct"] <= len(terms)):
            raise ValueError("Each off-scope signal needs two independent terms")


def audit_public_context(source: dict, contract: dict) -> dict:
    """Generate derived candidate receipts, never claim a factual error."""
    if not isinstance(source, dict) or not isinstance(source.get("content"), dict):
        raise ValueError("One exact WP post JSON object required")
    validate_contract(contract, source)
    reader = SectionReader()
    reader.feed(source["content"]["rendered"])
    sections: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for block in reader.blocks:
        sections[(block["heading"], block["anchor"])].append(block)
    issues = []
    seen = set()

    def flag(code: str, priority: str, heading: str, anchor: str,
             blocks: list[dict], matched: list[str], reason: str,
             review_details: dict | None = None) -> None:
        key = (code, heading, anchor)
        if key in seen:
            return
        seen.add(key)
        # Only public heading metadata, hashes, reason codes and URLs escape.
        receipt = {
            "id": f"CTX-{len(issues)+1:03d}", "code": code, "priority": priority,
            "heading": heading, "anchor": anchor,
            "evidence_url": source["link"] + ("#" + anchor if anchor else ""),
            "block_sha256": [hashtext(b["text"]) for b in blocks[:8]],
            "signal_terms": sorted(set(matched)), "reason": reason,
            "editorial_verdict": "NEEDS_HUMAN_REVIEW",
            "verified_fact_error": False,
        }
        if review_details:
            receipt["review_details"] = review_details
        issues.append(receipt)

    for (heading, anchor), blocks in sections.items():
        text = " ".join(b["text"] for b in blocks)
        for signal in contract["off_scope_signals"]:
            hits = [term for term in signal["terms"] if _has(text, term)]
            if len(hits) < signal["min_distinct"]:
                continue
            relevant = [b for b in blocks if any(_has(b["text"], t) for t in hits)]
            if relevant and all(CONTRAST.search(b["text"]) for b in relevant):
                continue  # explicit, bounded contrast is not product substitution
            flag("PRODUCT_OR_AUDIENCE_DRIFT_REVIEW", "P0", heading, anchor,
                 relevant, hits, "Independent off-scope product/audience cues; check actual user job")

        candidate_specs = [b for b in blocks if ((SPEC.search(b["text"])
                           and SPEC_ASSERTION.search(b["text"]))
                           or BATTERY_SPEC.search(b["text"]))
                           and not re.search(r"\b(?:check|verify|consult)\s+(?:the\s+)?"
                                             r"(?:manufacturer|manual|rating)\b", b["text"], re.I)]
        if candidate_specs:
            model_identified = bool(MODEL_ID.search(heading + " " + text))
            flag("MODEL_SPEC_PROVENANCE_REVIEW", "P1", heading, anchor,
                 candidate_specs, ["device-water-or-battery-spec"],
                 "Product-specific water/battery parameters need exact model, "
                 "manufacturer manual and applicable test conditions",
                 {"explicit_model_identifier_present": model_identified,
                  "claim_source_link_present": any(b["links"] for b in candidate_specs),
                  "manufacturer_passage_verified": False,
                  "evidence_gaps": (["model_identity_unstated"] if not model_identified else [])
                  + ["exact_model_manual_passage_unverified"]})

        cleaning = [b for b in blocks if CLEANING.search(b["text"])]
        if cleaning and re.search(r"\b(?:clean|care|maintenance|disinfect|saniti[sz])", heading, re.I):
            # Outbound links are metadata, not proof that a claim is entailed.
            flag("CLEANING_CLAIM_SOURCE_REVIEW", "P1", heading, anchor,
                 cleaning, ["cleaning-protocol"],
                 "Exact product/material/model compatibility and source passage unverified")

        rows = [b for b in blocks if b["kind"] == "table_row"]
        if rows and any(PRICE.search(b["text"]) for b in rows):
            offer_rows = [b for b in rows if OFFER.search(b["text"])]
            anonymous = [b for b in offer_rows if _unnamed_offer(b)]
            if offer_rows or contract.get("price_observed_at") is None:
                flag("PRICE_OFFER_FRESHNESS_REVIEW", "P2", heading, anchor,
                     anonymous or offer_rows or [b for b in rows if PRICE.search(b["text"])],
                     (["undated-price"] if not contract.get("price_observed_at") else [])
                     + ["unnamed-limited-offer" if anonymous else
                        "limited-offer" if offer_rows else "price-table"],
                     "Exact product identity, observation date and offer validity need review",
                     {"anonymous_offer_row_present": bool(anonymous),
                      "price_observation_date_present": bool(contract.get("price_observed_at")),
                      "row_product_link_present": any(b["links"] for b in (anonymous or offer_rows)),
                      "evidence_gaps": (["offer_product_identity_missing"] if anonymous else [])
                      + (["price_observed_at_missing"] if not contract.get("price_observed_at") else [])
                      + (["offer_validity_unverified"] if offer_rows else [])})

    counts = Counter(x["priority"] for x in issues)
    return {
        "schema": VERSION, "benchmark_id": contract["benchmark_id"],
        "generated_at": now(), "source_url": source["link"],
        "source_post_id": source["id"], "source_modified": source["modified"],
        "source_content_sha256": hashtext(source["content"]["rendered"]),
        "source_role": "public_competitor_qc_benchmark_only",
        "scope_subject": contract["scope"]["subject"],
        "search_intent_verdict": "UNASSESSABLE",
        "status": "HUMAN_REVIEW_REQUIRED", "publish_ready": False,
        "human_labels_present": 0, "validated_truth_errors": None,
        "summary": {"candidate_count": len(issues), "by_priority": dict(counts),
                    "sections_inspected": len(sections)},
        "candidates": issues,
        "limitations": [
            "Operator-defined off-scope signal set is not an independent human label",
            "Heuristic hits are candidates; non-hits do not establish factual or semantic PASS",
            "Link presence and government domain do not establish product/model claim support",
            "No target-market verified SERP or Owner original was supplied",
            "Only derived hashes/heading metadata may be committed; full article stays private",
            "Model IDs or linked pages are not machine-verified manufacturer entailment",
            "Price candidate metadata cannot prove an offer is false or expired",
        ],
    }


def audit_frozen_owner_draft(draft: str, frozen_scope: dict) -> dict:
    """Manual Dev QA of an existing Owner draft, without changing the pipeline.

    The only product exclusions come from the actual frozen Article Scope
    Contract. A brief comparative mention is never a machine factual error.
    """
    from .article_scope import VERSION as OWNER_SCOPE_VERSION

    if (frozen_scope.get("version") != OWNER_SCOPE_VERSION
        or frozen_scope.get("status") != "FROZEN"
        or not frozen_scope.get("scope_fingerprint")):
        raise ValueError("Actual frozen Owner Article Scope Contract required")
    scope = frozen_scope["scope"]
    excluded = scope["excluded_primary_products"]
    allow_comparison = scope["allow_explicit_comparison"]
    chunks = re.findall(r"(?ms)^##\s+([^\n]+)\n(.*?)(?=^##\s+|\Z)", draft)
    issues = []
    if not allow_comparison:
        for heading, body in chunks:
            for product in excluded:
                pattern = re.compile(r"(?<!\w)" + re.escape(product) + r"(?!\w)", re.I)
                # A section named for the wrong product, or two substantive
                # mentions in body, merits review. Do not count a negated
                # comparison line as a primary-product substitution.
                without_contrast = [p for p in re.split(r"\n\s*\n", body)
                                    if not CONTRAST.search(p)]
                substantial = sum(len(pattern.findall(p)) for p in without_contrast)
                if not pattern.search(heading) and substantial < 2:
                    continue
                issues.append({
                    "id": f"OWNER-CTX-{len(issues)+1:03d}",
                    "code": "EXCLUDED_PRODUCT_SECTION_REVIEW",
                    "priority": "P0", "heading": heading.strip(),
                    "excluded_product": product,
                    "body_sha256": hashtext(body),
                    "reason": "Possible section-level primary-product substitution; check Owner job",
                    "editorial_verdict": "NEEDS_HUMAN_REVIEW",
                    "verified_fact_error": False,
                })
    return {
        "schema": "andy-write-owner-draft-context-qc/v1",
        "job_id": scope["job_id"], "article_scope_fingerprint": frozen_scope["scope_fingerprint"],
        "draft_sha256": hashtext(draft), "source_role": "owner_original_scope_only",
        "status": "HUMAN_REVIEW_REQUIRED", "publish_ready": False,
        "human_labels_present": 0,
        "search_intent_verdict": "UNASSESSABLE_WITHOUT_VERIFIED_SERP",
        "summary": {"sections_inspected": len(chunks),
                    "product_substitution_candidates": len(issues)},
        "candidates": issues,
        "limitations": [
            "Only explicit Owner-frozen exclusions are matched; no LLM semantic classification",
            "A non-hit is not an assurance of article intent, factual correctness or prose quality",
            "Comparisons allowed by the frozen Owner scope are not auto-blocked",
            "Manually invoked Dev report only; no default writing workflow integration",
        ],
    }
