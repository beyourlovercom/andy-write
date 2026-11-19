# SERP evidence quality V1.1

Run a source-quality gate **before** intent labeling. A three-read merged search result is not a stable ranking. OpenSEO's `rank` is the row index in a merged list; only `bestPosition` denotes a position observed in one of the reads. `seenIn` records how many reads contained a result. A Google `/goto` URL is a redirect, not proof of the final publisher page.

## Normalize and assess

Create a JSON input for `scripts/grade_serp_evidence.py`, using source-observed fields; do not invent unknown values:

```json
{
  "keyword": "tpe vs silicone sex doll",
  "market_country": "US",
  "language": "en",
  "device": "mobile",
  "provider": "OpenSEO",
  "sample_runs": 3,
  "results": [
    {"domain": "example.com", "title": "Material comparison", "bestPosition": 2, "seenIn": 2, "url": "https://google.com/goto?url=...", "final_url": null, "relevance": "on-topic"}
  ]
}
```

- Classify each observed organic result's `relevance` as `on-topic`, `off-topic` or `unclear` **after checking the page**, never solely by a keyword overlap rule. Rows with null titles/domains are not usable. `off-topic` rows are logged but excluded from intent inference. Unreviewed results stay `unclear` and cannot justify `verified`.
- For multiple reads, count a page as stable only when `seenIn >= 2` and `sample_runs >= 2`. A single complete first-party/export screenshot may be manually verified, but is not repeatedly stable. For this provider gate, `verified` requires at least five stable on-topic results.
- Verify `final_url` points directly to the observed publisher domain, not a Google redirect or an unrelated domain. Until final URLs are resolved, mark provisional. Use the source's domain field only to describe an unverified publisher, not as a link.
- For branded navigational searches, include `brand: {"name":"Realdoll", "official_domain":"realdoll.com", "verification_url":"https://www.realdoll.com/pages/contact"}` **only when an independent first-party page confirms the domain**. If that official domain is missing or appears only in one of three reads, preserve the brand intent as a hypothesis but gate `REVIEW`. If official identity is unknown, leave it unresolved; never use a near-match domain as proof.
- Never equate `not-observed` with confirmed absence of a SERP feature, never invent search volume/CTR, and never claim Google's ten results were verified from a merged incomplete sample.

The checker emits `verified`/`provisional`/`blocked`, numeric counts, and explicit reasons. The checker does not decide whether a particular article is Match, Partial or Mismatch; that remains editorial judgment against a page actually read.

## Gate examples

1. 10 merged rows but all final URLs are Google redirects: **provisional / REVIEW**, not PASS.
2. Two relevant cleaning guides among unrelated toy sites: **provisional / REVIEW**.
3. A brand's official domain appears once amid near-matches: **provisional / REVIEW**.
4. Five on-topic, repeatedly observed, final-URL-confirmed pages in correct country/language/device with no unresolved brand conflict: **eligible for verified**; article fit still independently determines PASS/REVIEW/BLOCK.
