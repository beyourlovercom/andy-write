---
name: andy-write-research
description: "Collect source candidates with explicit SERP-vs-curated provenance and traceable retrieval."
---
# Andy Write Research — R1
Input: Article Job config, market and user-provided reference.
1. Read Brand profile and site index if available.
2. Expand query intent; SerpApi requires real API key and actual response.
3. If unavailable, use declared curated public HTTPS sources only. Label mode `curated_url_fetch_NOT_SERP`.
4. Persist URL, retrieval timestamp, title, status and limited excerpts. Search ranking is unknown in curated mode.
5. Never treat retrieval alone as fact verification. Output `research-pack.json`.
Use `python3 -m andy_write run --job ...` to exercise.
