# Reuse matrix for R0–R2

| Module | Public upstream | Current integration | Remaining gate |
|---|---|---|---|
| Research | SerpApi official skills / MCP | Independent live adapter implemented, no SERPAPI_API_KEY configured | Live Google response + attribution UAT |
| Source | Crawl4AI / Firecrawl | Stdlib paragraph/topic classifier, curated HTTPS fetch | Deep extraction, citation span validation |
| Outline | marketingskills/content-strategy | Native question-H2 Markdown builder and section contract | Generalize section mapping beyond canary |
| Draft | marketingskills/copywriting | V1.1 full Owner original with SHA-256 and immutable prompt; rewrite-only Codex CLI + optional API | Real rewrite quality and Token UAT |
| Editor | blader/humanizer; marketingskills/copy-editing | Basic editorial linter and human-reviewed sample | Non-deterministic prose QA automation |
| QC Benchmark | KissSelf public WP REST | 2025-11/12 only metrics and sample references | Human blind editorial assessment |

Open source repositories are cited, **not vendored**. No third-party Skill installed or executed on production hosts.

## V1.2 source-to-rewrite verification

The reusable Source, Editor and Quality Skills now provide source-to-rewrite paragraph mapping, distinctive-term evidence signals, short-source-item accounting and explicit human review decisions. It is an offline Python comparison, not a semantic judge. Two actual private source articles were tested with identity and controlled-deletion baselines. Existing same-topic and narrow-scope historical drafts were inspected, with human semantic review still pending. No Codex/Media model is used for QA. See docs/v1.2-cross-article-fidelity-uat-2026-11-13.md.

## KissSelf 2025 year-end QC benchmark — V1.2

A public December 2025 article (updated October 2026) was reverse-analysed read-only. Reusable Source/Outline/Quality/Editor changes now include source-owned H2/H3 hierarchy, conditional material caution, link-to-claim review candidates, reader title leakage prevention, and a private 12-case human QC goldset. Same Owner-source before/after real GPT-6.1 Terra rewriting improved nested headings from 0 to 13 and eliminated 2 leaked process headings; semantic fidelity is pending human labels. See docs/v1.2-kissself-qc-reverse-2026-11-13.md.
