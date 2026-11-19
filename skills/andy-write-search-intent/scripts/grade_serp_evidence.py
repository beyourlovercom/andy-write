#!/usr/bin/env python3
"""Conservative, offline source-quality grading of normalized SERP provider data.

Does not infer page relevance, intent, final URLs or brand identity.
"""

import argparse
import copy
import json
from urllib.parse import urlparse


def host(url):
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        return None
    return parsed.hostname.lower().removeprefix("www.")


def same_publisher(final_url, domain):
    final_host = host(final_url)
    if not final_host or not isinstance(domain, str) or not domain.strip():
        return False
    publisher = domain.lower().strip().removeprefix("www.")
    return final_host == publisher or final_host.endswith("." + publisher)


def grade(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a JSON object")
    rows = snapshot.get("results", [])
    if not isinstance(rows, list):
        raise ValueError("results must be a JSON array")
    runs = snapshot.get("sample_runs", 0)
    if type(runs) is not int or not 1 <= runs <= 20:
        raise ValueError("sample_runs must be between 1 and 20")

    valid = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        domain, title, position = row.get("domain"), row.get("title"), row.get("bestPosition")
        if not isinstance(domain, str) or not domain.strip() or not isinstance(title, str) or not title.strip():
            continue
        if type(position) is not int or not 1 <= position <= 100:
            continue
        # OpenSEO's merged `rank` column is not the original Google position.
        if type(row.get("seenIn")) is not int or not 1 <= row["seenIn"] <= runs:
            continue
        identifier = (domain.lower().strip(), title.strip().lower())
        if identifier in seen:
            continue
        seen.add(identifier)
        valid.append(row)

    def relevant(row):
        return row.get("relevance") == "on-topic"

    def stable(row):
        return runs >= 2 and row["seenIn"] >= 2

    def direct(row):
        return same_publisher(row.get("final_url"), row["domain"])

    on_topic = [r for r in valid if relevant(r)]
    stable_topic = [r for r in on_topic if stable(r)]
    final_topic = [r for r in on_topic if direct(r)]
    qualified = [r for r in on_topic if stable(r) and direct(r)]
    unknown = [r for r in valid if r.get("relevance") not in ("on-topic", "off-topic")]
    reasons = []

    if not all(isinstance(snapshot.get(k), str) and snapshot[k].strip()
               for k in ("keyword", "market_country", "language", "device", "provider")):
        reasons.append("Missing source-observed keyword, locale, language, device or provider")
    if len(on_topic) < 5:
        reasons.append(f"Only {len(on_topic)} explicitly on-topic identifiable results (need >=5)")
    if len(stable_topic) < 5:
        reasons.append(f"Only {len(stable_topic)} repeatedly observed on-topic results (need >=5)")
    if len(final_topic) < 5:
        reasons.append(f"Only {len(final_topic)} on-topic publisher final URLs confirmed (need >=5)")
    if len(qualified) < 5:
        reasons.append(f"Only {len(qualified)} results satisfy on-topic + stable + final URL together (need >=5)")
    if unknown:
        reasons.append(f"{len(unknown)} results have unreviewed/unclear relevance")

    official = None
    brand_status = "not-applicable"
    brand = snapshot.get("brand")
    if brand is not None:
        if not isinstance(brand, dict) or not isinstance(brand.get("official_domain"), str):
            reasons.append("Branded query lacks a verified official domain")
            brand_status = "unresolved"
        else:
            official = brand["official_domain"].lower().strip().removeprefix("www.")
            if not same_publisher(brand.get("verification_url"), official):
                reasons.append("Official domain has no independent first-party verification URL")
                brand_status = "unverified-identity"
            elif not any(stable(r) and same_publisher(r.get("final_url"), official) for r in valid):
                reasons.append("Official brand domain not repeatedly observed with verified final URL")
                brand_status = "unstable-official-domain"
            else:
                brand_status = "verified-stable-official-domain"

    result = {
        "keyword": snapshot.get("keyword"),
        "status": "blocked" if not valid else "verified" if not reasons else "provisional",
        "gate": "BLOCK" if not valid else "PASS-ELIGIBLE" if not reasons else "REVIEW",
        "metrics": {
            "raw_rows": len(rows), "identifiable_rows": len(valid), "on_topic_count": len(on_topic),
            "stable_on_topic_count": len(stable_topic), "final_url_count": len(final_topic),
            "qualified_count": len(qualified), "unclear_count": len(unknown), "sample_runs": runs,
        },
        "brand_status": brand_status,
        "official_brand_domain": official,
        "reasons": reasons or ["Evidence quality eligible; editorial intent and article checks still required"],
    }
    if not valid:
        result["reasons"].insert(0, "No identifiable, ranked organic rows")
    return result


def self_test():
    rows = [
        {"domain": f"shop{i}.example.com", "title": f"Comparison {i}", "bestPosition": i,
         "rank": 100 - i, "seenIn": 3, "url": "https://google.com/goto?url=opaque",
         "final_url": f"https://shop{i}.example.com/guide", "relevance": "on-topic"}
        for i in range(1, 7)
    ]
    base = {"keyword": "test comparison", "market_country": "US", "language": "en",
            "device": "mobile", "provider": "OpenSEO", "sample_runs": 3, "results": rows}
    assert grade(base)["status"] == "verified"
    no_final = copy.deepcopy(base)
    for row in no_final["results"]:
        row["final_url"] = None
    assert grade(no_final)["gate"] == "REVIEW"
    noisy = copy.deepcopy(base)
    for row in noisy["results"][:4]:
        row["relevance"] = "off-topic"
    assert grade(noisy)["gate"] == "REVIEW"
    lookalike = copy.deepcopy(base)
    lookalike["brand"] = {"name": "Realdoll", "official_domain": "realdoll.com",
                          "verification_url": "https://www.realdoll.com/pages/contact"}
    assert grade(lookalike)["brand_status"] == "unstable-official-domain"
    assert grade(lookalike)["gate"] == "REVIEW"
    bad_rank = copy.deepcopy(base)
    for row in bad_rank["results"]:
        row["bestPosition"] = None
    assert grade(bad_rank)["status"] == "blocked"
    print("SELF-TEST PASS (5: verified, redirected, off-topic, brand collision, absent observed rank)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Normalized SERP JSON file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.path:
        parser.error("Provide a normalized SERP JSON file or --self-test")
    with open(args.path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        output = [grade(x) for x in data]
    else:
        output = grade(data)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
