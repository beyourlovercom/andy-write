#!/usr/bin/env python3
"""Validate an Andy Write Search Intent v1 handoff; no network or writes."""

import argparse
import copy
import json
import sys
from urllib.parse import urlparse

VERSION = "andy-write-search-intent/v1"
PAGE_TYPES = {"guide", "comparison", "review-list", "category", "product", "forum", "homepage", "other"}
INTENTS = {"informational", "commercial-investigation", "transactional", "navigational", "mixed", "unknown"}
FEATURE_STATES = {"observed", "not-observed", "unknown"}
VERDICTS = {"Match", "Partial", "Mismatch", "Unassessable"}
METHODS = {"serp-export", "serp-screenshot", "general-search"}


def valid_url(value):
    try:
        parts = urlparse(value)
        return parts.scheme in ("https", "http") and bool(parts.netloc)
    except (TypeError, ValueError):
        return False


def is_serp_redirect(value):
    if not valid_url(value):
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return (host == "google.com" or host.endswith(".google.com")) and parsed.path in ("/goto", "/url")


def same_publisher_domain(url, domain):
    if not valid_url(url) or not isinstance(domain, str) or not domain:
        return False
    h = (urlparse(url).hostname or "").lower().removeprefix("www.")
    domain = domain.lower().removeprefix("www.")
    return h == domain or h.endswith("." + domain)


def check(report):
    errors = []

    def fail(message):
        errors.append(message)

    if not isinstance(report, dict):
        return ["Report root must be an object"]
    if report.get("contract_version") != VERSION:
        fail("contract_version must equal " + VERSION)
    mode = report.get("mode")
    if mode not in ("prebrief", "audit"):
        fail("mode must be prebrief or audit")
    for k in ("target_keyword", "site"):
        if not isinstance(report.get(k), str) or not report[k].strip():
            fail(k + " must be a nonempty string")

    scope = report.get("scope", {})
    if not isinstance(scope, dict):
        scope = {}
    for k in ("audience", "market_country", "language", "device"):
        if not isinstance(scope.get(k), str) or not scope.get(k, "").strip():
            fail("scope." + k + " is required")
    if "owner_scope_contract_id" not in scope:
        fail("scope.owner_scope_contract_id must be present (null if unknown)")
    if scope.get("owner_requirements_preserved") is not True:
        fail("scope.owner_requirements_preserved must be true")

    evidence = report.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    status, method = evidence.get("status"), evidence.get("method")
    if status not in ("verified", "provisional", "blocked"):
        fail("evidence.status invalid")
    if method not in METHODS:
        fail("evidence.method invalid")
    if not isinstance(evidence.get("collected_at"), str) or not evidence.get("collected_at"):
        fail("evidence.collected_at required")
    if not isinstance(evidence.get("limitations"), list):
        fail("evidence.limitations must be a list")

    results = evidence.get("results", [])
    if not isinstance(results, list):
        fail("evidence.results must be a list")
        results = []
    urls = set()
    counts = {}
    observed_stable = 0
    observed_on_topic = 0
    stable_on_topic = 0
    for i, result in enumerate(results):
        if not isinstance(result, dict):
            fail(f"results[{i}] must be an object")
            continue
        url = result.get("url")
        if not valid_url(url):
            fail(f"results[{i}].url must be an absolute HTTP(S) URL")
        elif is_serp_redirect(url):
            fail(f"results[{i}].url must be a direct publisher URL, not a Google SERP redirect")
        elif url in urls:
            fail(f"results[{i}].url duplicated")
        else:
            urls.add(url)
        if not isinstance(result.get("title"), str) or not result["title"].strip():
            fail(f"results[{i}].title required")
        page_type = result.get("page_type")
        if page_type not in PAGE_TYPES:
            fail(f"results[{i}].page_type invalid")
        else:
            counts[page_type] = counts.get(page_type, 0) + 1
        rank = result.get("observed_rank")
        if rank is not None and (type(rank) is not int or rank < 1 or rank > 100):
            fail(f"results[{i}].observed_rank invalid")
        if method == "general-search" and rank is not None:
            fail(f"results[{i}] general-search must not invent Google rank")
        if status == "verified" and rank is None:
            fail(f"results[{i}] verified results must record rank")

        if status == "verified":
            if result.get("relevance") != "on-topic":
                fail(f"results[{i}].relevance must be explicitly on-topic for verified evidence")
            else:
                observed_on_topic += 1

        if status == "verified" and result.get("seen_in") is not None:
            if type(result["seen_in"]) is not int or result["seen_in"] < 1:
                fail(f"results[{i}].seen_in must be a positive integer")
            elif result["seen_in"] >= 2:
                observed_stable += 1
                if result.get("relevance") == "on-topic":
                    stable_on_topic += 1

    features = evidence.get("serp_features", {})
    if not isinstance(features, dict):
        fail("evidence.serp_features must be an object")
    else:
        for k, v in features.items():
            if v not in FEATURE_STATES:
                fail("SERP feature " + k + " has invalid status")
            if method == "general-search" and v == "not-observed":
                fail("general-search cannot assert SERP feature absence: " + k)
    if status == "verified" and (method == "general-search" or len(urls) < 5):
        fail("verified evidence requires localized source and at least five observed ranked pages")
    if status == "verified":
        for evidence_key, scope_key in (("source_market_country", "market_country"),
                                        ("source_language", "language"), ("source_device", "device")):
            if evidence.get(evidence_key) != scope.get(scope_key):
                fail("verified source settings do not match target: " + evidence_key)

        quality = evidence.get("quality")
        if not isinstance(quality, dict):
            fail("verified evidence requires evidence.quality counts and source checks")
        else:
            runs = quality.get("sample_runs")
            kind = quality.get("capture_kind")
            if type(runs) is not int or not 1 <= runs <= 20:
                fail("evidence.quality.sample_runs must be 1..20")
            if kind not in ("multiple-reads", "single-screenshot"):
                fail("evidence.quality.capture_kind invalid")
            for k in ("on_topic_count", "stable_on_topic_count", "final_url_count"):
                val = quality.get(k)
                if type(val) is not int or val < 0 or val > len(urls):
                    fail("evidence.quality." + k + " must be an observed count <= result count")
            if type(quality.get("on_topic_count")) is int and quality["on_topic_count"] < 5:
                fail("verified requires at least five reviewed on-topic results")
            if type(quality.get("on_topic_count")) is int and quality["on_topic_count"] != observed_on_topic:
                fail("evidence.quality.on_topic_count must equal the explicit result relevance labels")
            if type(quality.get("final_url_count")) is int and quality["final_url_count"] < 5:
                fail("verified requires at least five confirmed final URLs")
            if type(quality.get("final_url_count")) is int and quality["final_url_count"] != len(urls):
                fail("evidence.quality.final_url_count must equal recorded final destination links")
            if kind == "multiple-reads":
                if type(runs) is int and runs < 2:
                    fail("multiple-reads requires at least two sample runs")
                if type(quality.get("stable_on_topic_count")) is int and quality["stable_on_topic_count"] < 5:
                    fail("verified multi-read evidence requires five stable on-topic results")
                if observed_stable < 5:
                    fail("verified multi-read evidence must provide seen_in >=2 on five recorded results")
                if type(quality.get("stable_on_topic_count")) is int and quality["stable_on_topic_count"] != stable_on_topic:
                    fail("evidence.quality.stable_on_topic_count must equal stable recorded on-topic results")
            if kind == "single-screenshot":
                if method != "serp-screenshot" or runs != 1 or quality.get("screenshot_reviewed") is not True:
                    fail("single-screenshot requires one reviewed original SERP screenshot")
            official = quality.get("official_brand_domain")
            if "official website" in report.get("target_keyword", "").lower() and not official:
                fail("official website query cannot be verified without official_brand_domain")
            if official is not None:
                if not isinstance(official, str) or not official or quality.get("official_domain_verified") is not True:
                    fail("official brand domain must be independently verified")
                elif not any(isinstance(row, dict) and same_publisher_domain(row.get("url"), official)
                             and (kind == "single-screenshot" or row.get("seen_in", 0) >= 2)
                             for row in results):
                    fail("verified brand intent must include stable official-domain result")
    if status == "blocked" and len(urls) > 0:
        fail("blocked evidence must not include usable results")
    if status == "provisional" and not urls:
        fail("provisional evidence requires at least one usable result")

    intent = report.get("intent", {})
    if not isinstance(intent, dict):
        intent = {}
    if intent.get("primary") not in INTENTS:
        fail("intent.primary invalid")
    observed_counts = intent.get("observed_page_type_counts", {})
    if not isinstance(observed_counts, dict) or observed_counts != counts:
        fail("intent.observed_page_type_counts must equal recorded results by page type")
    if not isinstance(intent.get("secondary"), list):
        fail("intent.secondary must be a list")
    if not isinstance(intent.get("must_cover"), list):
        fail("intent.must_cover must be a list")
    for k in ("searcher_question", "buyer_stage", "recommended_page_type", "next_click"):
        if not isinstance(intent.get(k), str) or not intent[k].strip():
            fail("intent." + k + " required")
    if status == "blocked" and intent.get("primary") != "unknown":
        fail("blocked evidence must abstain from intent inference")

    audit = report.get("audit", {})
    if not isinstance(audit, dict):
        audit = {}
    verdict = audit.get("verdict")
    if verdict not in VERDICTS:
        fail("audit.verdict invalid")
    if mode == "prebrief" and verdict != "Unassessable":
        fail("prebrief requires Unassessable verdict")
    if mode == "audit":
        if not isinstance(audit.get("article_source"), str) or not audit.get("article_source", "").strip():
            fail("audit requires article_source")
        if audit.get("article_page_type") not in PAGE_TYPES:
            fail("audit requires article_page_type")
        if status == "blocked" and verdict != "Unassessable":
            fail("blocked evidence requires Unassessable verdict")

    recs = report.get("recommendations", [])
    if not isinstance(recs, list) or len(recs) > 3:
        fail("recommendations must contain 0 to 3 items")
    else:
        for i, rec in enumerate(recs):
            if not isinstance(rec, dict):
                fail(f"recommendations[{i}] must be object")
                continue
            for k in ("priority", "issue", "minimal_action"):
                if not isinstance(rec.get(k), str) or not rec[k].strip():
                    fail(f"recommendations[{i}].{k} required")
            eurls = rec.get("evidence_urls", [])
            if not isinstance(eurls, list) or not eurls or any(url not in urls for url in eurls):
                fail(f"recommendations[{i}].evidence_urls must reference recorded results")

    gate = report.get("gate")
    if gate not in ("PASS", "REVIEW", "BLOCK"):
        fail("gate invalid")
    if status == "blocked" and gate != "BLOCK":
        fail("blocked evidence requires BLOCK")
    if verdict == "Mismatch" and gate != "BLOCK":
        fail("Mismatch requires BLOCK")
    if verdict == "Partial" and gate != "REVIEW":
        fail("Partial requires REVIEW")
    if status == "provisional" and gate == "PASS":
        fail("provisional evidence cannot yield PASS")
    if gate == "PASS" and (status != "verified" or (mode == "audit" and verdict != "Match")):
        fail("PASS requires verified evidence and matching page in audit mode")
    if intent.get("primary") in ("mixed", "unknown") and gate == "PASS":
        fail("mixed/unknown intent requires REVIEW or BLOCK")
    if not isinstance(report.get("approval_request"), str) or not report["approval_request"].strip():
        fail("approval_request required")
    return errors


def self_test():
    sample = {
        "contract_version": VERSION, "mode": "audit", "target_keyword": "care guide", "site": "example.com",
        "scope": {"audience": "adult owners", "market_country": "US", "language": "en", "device": "mobile",
                  "owner_scope_contract_id": None, "owner_requirements_preserved": True},
        "evidence": {"status": "provisional", "method": "general-search", "collected_at": "2026-11-19",
                     "source_market_country": None, "source_language": None, "source_device": None,
                     "limitations": ["Generic search"], "results": [{"url": "https://example.com/guide", "title": "Guide", "page_type": "guide", "observed_rank": None}],
                     "serp_features": {"ai_overview": "unknown"}},
        "intent": {"primary": "informational", "secondary": [], "observed_page_type_counts": {"guide": 1},
                   "searcher_question": "How?", "buyer_stage": "learning", "recommended_page_type": "guide",
                   "must_cover": ["safe care"], "next_click": "follow instructions"},
        "audit": {"article_source": "https://example.com/guide", "article_page_type": "guide", "verdict": "Partial", "reason": "Insufficient depth"},
        "recommendations": [{"priority": "P1", "issue": "Depth", "minimal_action": "Add steps",
                              "evidence_urls": ["https://example.com/guide"]}],
        "gate": "REVIEW", "approval_request": "Owner reviews the angle"
    }
    assert not check(sample), check(sample)
    invalid = copy.deepcopy(sample)
    invalid["evidence"]["results"][0]["observed_rank"] = 1
    assert any("general-search" in x for x in check(invalid))
    invalid = copy.deepcopy(sample)
    invalid["gate"] = "PASS"
    assert any("provisional" in x for x in check(invalid))
    invalid = copy.deepcopy(sample)
    invalid["audit"]["verdict"] = "Mismatch"
    assert any("Mismatch" in x for x in check(invalid))
    invalid = copy.deepcopy(sample)
    invalid["intent"]["observed_page_type_counts"] = {"guide": 10}
    assert any("recorded results" in x for x in check(invalid))
    invalid = copy.deepcopy(sample)
    invalid["evidence"]["results"][0]["url"] = "https://google.com/goto?url=opaque"
    assert any("SERP redirect" in x for x in check(invalid))
    verified = copy.deepcopy(sample)
    verified["evidence"].update({"status": "verified", "method": "serp-export", "source_market_country": "US",
                                 "source_language": "en", "source_device": "mobile", "limitations": [],
                                 "results": [{"url": f"https://source{i}.example.com/page", "title": "Comparison",
                                              "page_type": "guide", "observed_rank": i, "seen_in": 3,
                                              "relevance": "on-topic"}
                                             for i in range(1, 7)],
                                 "quality": {"capture_kind": "multiple-reads", "sample_runs": 3,
                                             "on_topic_count": 6, "stable_on_topic_count": 6,
                                             "final_url_count": 6, "official_brand_domain": None,
                                             "official_domain_verified": None}})
    verified["intent"]["observed_page_type_counts"] = {"guide": 6}
    verified["audit"]["verdict"] = "Match"
    verified["recommendations"] = []
    verified["gate"] = "PASS"
    assert not check(verified), check(verified)
    unstable = copy.deepcopy(verified)
    for row in unstable["evidence"]["results"]:
        row["seen_in"] = 1
    assert any("seen_in" in x for x in check(unstable))
    brand = copy.deepcopy(verified)
    brand["evidence"]["quality"].update({"official_brand_domain": "realdoll.com",
                                         "official_domain_verified": True})
    assert any("official-domain" in x for x in check(brand))
    print("SELF-TEST PASS (9 controls: valid, rank fabrication, false PASS, mismatch gate,"
          " invented counts, redirect, qualified verified, instability, brand collision)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="intent_contract.json file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.path:
        parser.error("Provide an intent_contract.json path or --self-test")
    with open(args.path, "r", encoding="utf-8") as f:
        report = json.load(f)
    errors = check(report)
    if errors:
        for message in errors:
            print("ERROR:", message, file=sys.stderr)
        return 1
    print("VALID: Andy Write Search Intent V1 contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
