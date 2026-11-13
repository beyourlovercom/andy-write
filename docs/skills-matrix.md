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
