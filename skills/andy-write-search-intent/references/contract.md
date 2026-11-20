# Search Intent Contract V1

The JSON contract is a handoff between Search Intent and the pre-existing Andy Write stages. Keep the original Owner keyword, topic and Article Scope Contract intact. **Do not update the runtime, article, outline or writer communication as a side effect.**

## Required shape

```json
{
  "contract_version": "andy-write-search-intent/v1",
  "mode": "prebrief",
  "target_keyword": "tpe vs silicone sex doll",
  "site": "example.com",
  "scope": {
    "audience": "Adults shopping for full-size dolls",
    "market_country": "US",
    "language": "en",
    "device": "mobile",
    "owner_scope_contract_id": null,
    "owner_requirements_preserved": true
  },
  "evidence": {
    "status": "provisional",
    "method": "general-search",
    "collected_at": "2026-11-19",
    "source_market_country": null,
    "source_language": null,
    "source_device": null,
    "limitations": ["General web search is not a geo-locked Google top ten"],
    "results": [
      {"url": "https://example.com/comparison-a", "title": "Comparison A", "page_type": "comparison", "observed_rank": null},
      {"url": "https://example.org/comparison-b", "title": "Comparison B", "page_type": "comparison", "observed_rank": null},
      {"url": "https://example.net/comparison-c", "title": "Comparison C", "page_type": "comparison", "observed_rank": null}
    ],
    "serp_features": {"ai_overview": "unknown", "people_also_ask": "unknown", "shopping": "unknown"}
  },
  "intent": {
    "primary": "commercial-investigation",
    "secondary": [],
    "observed_page_type_counts": {"comparison": 3},
    "searcher_question": "Which material best suits the purchase?",
    "buyer_stage": "comparison",
    "recommended_page_type": "comparison",
    "must_cover": ["Tradeoffs", "Material limits", "Budget and care"],
    "next_click": "Compare relevant full-size product options"
  },
  "audit": {"article_source": null, "article_page_type": null, "verdict": "Unassessable", "reason": "No article was supplied in prebrief mode"},
  "recommendations": [],
  "gate": "REVIEW",
  "approval_request": "Owner confirm target market and SERP capture before freezing brief"
}
```

## Field and decision rules

- `mode`: `prebrief` (no page needed) or `audit` (real page/source required).
- `evidence.status`: `verified` only for target-market Google SERP screenshot/API export with at least five **on-topic, independently identifiable, sufficiently stable organic results** with observed positions and **final destination URLs**. `provisional` for incomplete/unlocalized/unstable sources, unreviewed relevance, redirects, or unresolved branded results; `blocked` when there is no usable evidence. `verified` must specify country, language, device, date, source and `evidence.quality`.
- `evidence.method`: `serp-export`, `serp-screenshot`, or `general-search`. Only the first two can be `verified`.
- `source_market_country`, `source_language`, `source_device`: actual SERP capture settings, never simply copied from the desired target scope. Required and equal to `scope` in `verified` cases; `null` when unknown.
- `results`: each unique absolute **destination** URL, title, page type and `observed_rank`. Never put `google.com/goto` or another SERP redirect in this field. General search must leave rank `null`; rank 1–100 is valid for a verified screenshot/export. In OpenSEO, use `bestPosition`; merged `rank` is never a Google position. Page type enum: `guide`, `comparison`, `review-list`, `category`, `product`, `forum`, `homepage`, `other`.
- `evidence.quality`: required for `verified`; shape `{ "capture_kind": "multiple-reads", "sample_runs": 3, "on_topic_count": 6, "stable_on_topic_count": 5, "final_url_count": 6, "official_brand_domain": null, "official_domain_verified": null }`. Counts refer to **recorded evidence results**; `sample_runs` is an integer 1–20, other counts are nonnegative integers not exceeding recorded results. `on_topic_count` and `final_url_count` must be at least five. For `multiple-reads`, `stable_on_topic_count` and recorded results with `seen_in >= 2` must each number at least five. If `official_brand_domain` is set, `official_domain_verified` must be true and a stable result must match that domain. Leave `evidence.status=provisional` if the provider cannot prove these fields rather than inventing them. For a single verified screenshot, use `capture_kind=single-screenshot`, `sample_runs=1`, `screenshot_reviewed=true`, `method=serp-screenshot`; no repeated-observation stability may be claimed.
- `serp_features`: allowed states `observed`, `not-observed`, `unknown`; do not assert absence from general web search. Do not infer an AI Overview as an observed fact.
- `intent.primary`: `informational`, `commercial-investigation`, `transactional`, `navigational`, `mixed`, or `unknown`. When blocked, use `unknown`. `observed_page_type_counts` must sum to exactly the number of results recorded; no top-10 dominance claim unless 10 results are actually recorded.
- `audit.verdict`: `Match`, `Partial`, `Mismatch`, `Unassessable`. In `prebrief`, use `Unassessable` with a clear reason. In `audit`, require `article_source` and `article_page_type`, and never use `Match` when the evidence is blocked.
- `gate`: `PASS` only when `verified` and `Match`, or `verified` in prebrief mode with an unambiguous recommended format. `REVIEW` for provisional, mixed or Partial. `BLOCK` for blocked evidence, Mismatch or scope conflict. A `PASS` does **not** grant permission to publish or integrate the skill into Andy Write.
- `recommendations`: zero to three objects shaped `{ "priority": "P1", "issue": "...", "evidence_urls": ["https://..."], "minimal_action": "..." }`. Evidence URLs must appear in `evidence.results`; recommendations are advisory and must not be performed by this skill.
- Never insert guessed Google rankings, fabricated keyword volumes, CTR, SERP-feature confirmations or numeric SEO magic thresholds.

The validator checks structure and basic consistency. A human must still verify source interpretation and editorial judgment. `intent_report.md` should summarize the same evidence, explain discrepancies, cite result URLs and make the Owner's approval decision obvious in under a page before deeper details.
