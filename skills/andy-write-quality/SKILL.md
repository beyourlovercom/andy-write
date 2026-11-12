---
name: andy-write-quality
description: "Evidence-aware article QA: source detail retention, practical value, links, intro format, and focused rewrites without fake AI-detector scores."
---
# Andy Write Quality — R3 quality foundation

Input: a user-provided reference + Source catalog and verified URL retrieval metadata, Markdown article, Brand policy.

Run:

    python3 -m andy_write quality --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md

Rules:
1. Detect empty promotional phrases, unsupported authority statements, low-practical-detail H2s, duplicate structure, missing intro bold answer, and unresolved editorial notes.
2. Extract factual grounding candidates from owner-provided original paragraphs. Require that optional packaging details are described CONDITIONALLY, not as universal product specs.
3. Only cite actually retrieved URLs; HTTP 200 verifies accessibility, not factual truth. Never invent sources, reviews, test results or model properties.
4. Generate a machine-readable audit and only affected H2 headings. The writer may request a targeted revision, preserving all unrelated section bodies.
5. Count English words independently; default 1000 ±7%. If requirements fail after bounded revision, output REVIEW_REQUIRED.
6. This is an editorial heuristic, NOT an AI-detection prediction or substitute for human factual review.
7. Save under gitignored .runs, never publish to WordPress or Notion without separate Owner authorization.

Maturity: R3 Quality foundation. Deep citation span verification, image QA and comprehensive live link checks are future work.
