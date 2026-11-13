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

## V1.2 source-fidelity / content-retention audit

Before accepting a rewriting candidate, run the independent local Python Fidelity
check (andy_write.fidelity). For each original paragraph, record stable ID,
source SHA-256, a possible output paragraph range, source-distinctive word
overlap and manual review status. Keep short and heading-only source paragraphs
in a separate numbered queue; do not silently exclude them.

EXACT_TEXT_PRESENT means literal text, LEXICAL_CANDIDATE means review only,
UNMAPPED_REVIEW means no match was proven, not necessarily omitted meaning.
New numbers are source-check candidates, not evidence of fabricated facts.
Never use an AI-detector percentage as a quality metric. Never claim human
semantic approval based on deterministic matching.

The writing pipeline now generates source-fidelity-report.json and a private
source-fidelity-review.md automatically. The CLI also supports independent
fidelity checks on any two existing local article files. Never use Codex CLI
for QA, evidence matching or script execution. Owner notes must have rationale,
source hashes and (for positive claims) a real exact target quotation.
Unsafe, universalized or SKU-inapplicable original advice may be intentionally
omitted if documented; literal word copying is not the quality goal.

## V1.2 KissSelf reverse-QC calibration — evidence before word count

Use public WordPress articles ONLY as structural and risk benchmarks, never as
model rewrite sources or canonical truth. The read-only, offline qc-profile
command accepts a private WP REST snapshot and an existing Owner article draft,
producing a derived-metrics report with no competitor prose retained in Git.
Track words, heading hierarchy, tables, actual image Alt coverage, list/callout
frequency, internal/external link patterns and sentence-level product/safety
claim candidates. Match each citation to the exact claim it supports; HTTP
200 or a government-domain link alone does not validate adjacent prose.

KissSelf's public December 26 2025 sample currently contains 27 H3s and 9
tables in about 5.9k words, but that is NOT an SEO or editorial quality target
for a 1k-word piece. Require intent/source-grounded subsections, decision
tables and FAQ only when justified, and avoid keyword stuffing, link volume
targets or unsupported material/IP claims. Product/maker guidance is required
for compatibility, cleaning, waterproofing and disinfection assertions.
Outputs are HUMAN_REVIEW_REQUIRED when facts/semantic retention are uncertain.

Owner P0: Codex CLI ONLY rewrites a complete Owner-provided original; this
reverse-QC skill never invokes Codex. All image/video generation prohibited.
