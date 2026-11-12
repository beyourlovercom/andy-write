---
name: andy-write-research
description: "Collect source candidates with explicit SERP-vs-curated provenance and traceable retrieval."
---
# Andy Write Research — R1
Input: Article Job config, market and user-provided reference.
1. Read Brand profile and site index if available.
2. Prefer `research_mode=dc_free`: DC fetches explicitly allowed public HTTPS source URLs and discovers related papers via OpenAlex without a key. This is NOT Google SERP or whole-Web discovery.
3. Expand query intent; SerpApi requires a real API key and successful response when true Google ranking is required.
4. Without SerpApi, use `dc_free_curated_plus_openalex_NOT_GOOGLE_SERP` or `curated_url_fetch_NOT_SERP`. Never send automated Google queries via Chrome or bypass anti-bot challenges.
5. Persist URL, retrieval timestamp, title, status and limited excerpts. Search ranking is unknown in free mode. Mark OpenAlex papers `metadata_discovery_only` until verified.
6. Reuse seven-day local cache to minimize external requests; never treat retrieval alone as fact verification. Output `research-pack.json`.
Use `python3 -m andy_write run --job ...` to exercise.
