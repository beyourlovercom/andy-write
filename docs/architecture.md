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
Autonomous R2 prose generation now uses explicit GPT-6.1 Terra through the ChatGPT-authenticated Codex CLI: read-only mode, actual JSONL usage tracking, per-stage SHA-256 replay protection, independent word-counting, optional bounded rework. The OpenAI Responses API adapter remains an independently authenticated optional provider.

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

## R3 initial editorial and media gate

- Editor V2 receives real owner-source anchor IDs and only retrieved public URLs; it must preserve conditional model-specific statements.
- Quality audit verifies practical sections, avoids filler, requires grounded source detail only when it actually appeared in the supplied original, validates contextual links against the retrieval record, checks the three-part intro with a bold direct answer.
- When only particular H2s fail, the bounded Codex rewrite response must name the same H2s. The patcher replaces only those bodies and leaves everything else untouched.
- Image planning exports one cover and one per H2 task, but no SEO title, alt, caption, or description is filled until actual image creation and human/vision inspection. Hash and review are required for future media readiness.
- These checks are **heuristics**, not factual verification or any AI-origin scoring. Human editorial review remains required. R3 full image generation and publication are pending.
