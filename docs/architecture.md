# Andy Write V1.0 architecture — R0–R2

## Orchestrator and contracts

One article job = one JSON config with `job_id`, `brand`, `topic`, `target_title`, `source_path`, `source_url`, `research_mode`, `research_urls`, `protected_post_ids`. All outputs live under gitignored `.runs/<job_id>/`.

R1:
- `research-pack.json`: acquisition method (`serpapi_live`, `curated_url_fetch_NOT_SERP` or `dc_free_curated_plus_openalex_NOT_GOOGLE_SERP`), query, timestamp, URL status, retrieval errors. `curated_url_fetch` is **not** search.
- `source-catalog.json`: segments with stable IDs, section, topic and original source identity. Source text kept local.
- `evidence-ledger.json`: claims, source IDs, evidence status and caveats. An URL responding HTTP 200 does not by itself validate every claim.
R2:
- `outline.md`: topic-led Markdown H1, image slot, 3-paragraph introduction plan, TOC, claim references, question H2, paragraph intent, image slots, conclusion, link plan.
- `writing-prompt.md`: evidence-constrained editorial instructions, ground-truth source only.
- `article-v1.md`, `article-v2.md`: user/LLM-supplied content with provenance; `review.json` flags unsupported promises, internal notes and structural failures.
- `benchmark.json`: derived metrics, not source article bodies.

## Shared services
- Brand profile (isolated per brand) under `configs/brands/`.
- Site Index (R0 contract, future live WP integration).
- Evidence Store (local per-job ledger).
- Policy (source, editorial safety, approval guardrail).

## Model interface
For autonomous prose generation, an actual model backend must be configured. MVP supports OpenAI Responses API via environment key. Without an API key, the pipeline produces reviewed prompts and accepts a separate editorial draft from the active assistant. It never silently substitutes generic template text for a model-written article.

## Future
R3 Media generation + title/alt/caption/description after visual verification; quality gates; outreach. R4 Notion approvals. R5 WordPress Application Password draft/approved publish with protected Post ID. None is active in this MVP.

## Keyless self-hosted DC acquisition

- DC drives the CLI, public HTTPS source download, OpenAlex metadata lookup and topic clustering. No external paid SERP API is required in `dc_free`.
- OpenAlex is an academic works index, not a complete Web/Google index. Its records remain unverified until original publications are checked.
- All Google search query phrases stay labeled `queries_not_executed_google` in free mode. No automated Google result scraping, proxy rotation or CAPTCHA bypass.
- Public source retrieval cache is keyed to job/topic/URL/query and refreshed after seven days.
- For actual Google results use SerpApi Free (250/month as of 2026-11) with a key; DC then performs the extraction and source auditing.

## No-key reference providers and limits

- `dc_free` combines known HTTPS sources with OpenAlex `/works` metadata. Query limits: at most 3 OpenAlex queries and 4 matches per query. DC executes network reads locally; no SerpApi payment required.
- OpenAlex has rate limits and can return unrelated academic works. Provider metadata is a **lead**, not a validated primary source.
- Brave API may provide monthly credits but requires a card and has result-retention restrictions; it is **not** silently enabled in the MVP.
- Google Custom Search JSON API is closed to new customers; self-hosted Chrome scraping Google Search is not the default for policy/reliability reasons.
