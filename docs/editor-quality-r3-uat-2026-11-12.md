# Andy Write Editor / Quality / Media R3 UAT — 2026-11-12

## Scope

Based on Owner's 2026-11-12 direction to continue the approved Andy Write mainline, this change extends the existing GPT-6.1 Terra R2 system with evidence-focused editing and the first R3 components.

- **R2 Editor V2:** more specific and practical edits, owner reference details, conditional product descriptions, and relevant links only to URLs successfully retrieved.
- **R3 Quality foundation:** deterministic, explicit findings for low-detail H2s, empty filler phrases, missing reference-specific details, incomplete introductions, and missing grounded links. No AI-detection percentage or claims of human authorship.
- **Targeted repair:** the writer can rewrite only flagged H2s, then splice just those sections into the original article; unaffected sections are preserved byte-for-byte. Maximum revision count is bounded.
- **Intro format:** when the second introductory paragraph already has two distinct suitable sentences, safely split the existing text into a bold direct answer and bridge without adding any factual claim.
- **R3 Media planning:** one cover + one image job for each of six H2s. All image SEO metadata stays null until a real generated image is visually inspected, and any future image file requires valid checksum and an explicit review record.

## Genuine PairDoll UAT

Owner-supplied Notion article was used as the core reference. All operations were local read-only with respect to WordPress and other sites.

| Item | Previous GPT-6.1 Terra sample | New Editor/Quality revision |
|---|---:|---:|
| English words (static approximate) | 1,039 | 1,013 |
| Editorial quality findings | 4 | 0 |
| Original-source optional details preserved | 2 / 4 | 4 / 4 |
| Internal links | 0 | 1 |
| External verified-retrieval links | 0 | 1 |
| Three-part introduction + bold answer | yes | yes (format normalized without new content) |
| Final gate | REVIEW_REQUIRED | RULE_CHECK_PASS |

The before article flagged two missing source details (the reference mentions foam lining and separately protected accessories) plus absent internal and external links. The new output incorporates the concepts conditionally and cites the existing PairDoll first-time guide plus a NIOSH materials-handling source.

New excerpt file for Owner inspection: [Editor/Quality V2 sample](../examples/output/pairdoll-unboxing-editor-quality-v2.md).

## Real GPT-6.1 Terra incremental usage

This was not a synthetic test. The updated prompts resulted in two additional actual Codex CLI turns (draft, edit). No third targeted rewrite was needed because the stronger edit passed the new rule checks.

| Metric (additional 2 turns) | Actual |
|---|---:|
| Input Tokens | 35,110 |
| Cached input Tokens | 24,320 |
| Output Tokens | 2,590 |
| Final English words (independent counter) | 1,007 |
| Actual new model calls | 2 |
| Cumulative recorded model calls in this job | 4 |

Repeated identical writing parameters hit draft/edit caches and added **zero** calls. R2 budgets are counted from actual Codex JSONL usage; Plus account quota cannot be converted directly into USD API cost.

## QA and limitations

- The source and links were retrieved, but HTTP 200 and keyword heuristics do not prove the underlying claim. Human factual, safety, editorial and brand approval is still pending.
- The quality signals are **not** AI-detection scores, are not proof of originality, and can produce both false negatives and false positives. Real reader usefulness still requires human review.
- The selective chapter repair integration was verified through controlled regression tests. The live sample did not need a repair call beyond draft and edit.
- R3 Image generation, visual review, metadata authoring, WordPress upload, and Notion publishing are **not yet implemented**. The media manifest is an actual task queue proposal, not finished image assets.
- No existing WordPress posts were modified, no passwords or remote article bodies were published, and Git-ignored Notion source originals and raw event logs remain local.

## Engineering status

38 local unit tests PASS. GitHub Actions CI to be checked on branch HEAD.
