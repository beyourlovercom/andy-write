> **Owner P0 update, 2026-11-13:** Codex CLI is reserved strictly for rewriting existing user-supplied full articles. All image/video generation is prohibited. Earlier imagegen instructions in this historical document have been superseded. See docs/owner-policy-2026-11-13.md.

# Andy Write R3 ImageGen UAT — November 13, 2026

## Production boundary

All 7 generated images remain review candidates only. No WordPress writes or published content. Original PNGs remain in the Git-ignored job folder on US Mac mini. Private GitHub PR contains lightweight WebP copies with an article preview.

## Real generated results

| Item | Actual result |
|---|---|
| Original PNG images | 7; 17,287,580 bytes total |
| Review WebP images | 7; 1,096,960 bytes total |
| Resolution | 1672 x 941 per image, 16:9 |
| Scenes | Cover + 6 unique question H2s |
| Tool | Codex CLI 0.167.2, built-in ImageGen, ChatGPT subscription |
| Visual candidate QA | 7/7 machine-vision checks passed |
| SEO metadata | 7 unique Title, Alt, Caption and Description records |
| Human approval | PENDING |
| WordPress | NOT TOUCHED |

The images are AI-generated editorial illustrations and NOT actual PairDoll warehouse or customer-delivery photographs. Captions identify them accordingly.

## Recorded Codex usage, not fabricated image API pricing

| Session | Images | Input Tokens | Cached input Tokens | Output Tokens |
|---|---:|---:|---:|---:|
| cover | 1 | 100,725 | 90,112 | 633 |
| six-h2 | 6 | 605,257 | 580,608 | 2,813 |
| **Total** | **7** | **705,982** | **670,720** | **3,446** |

These are Codex CLI turn counters, not independently itemized ImageGen tool billing or remaining Plus quota. No separate paid Image API Key was configured.

## Repeatable and safe

The ImageGen runner checks saved PNGs and visual observations and skips all seven without launching a model on a repeat run. The R3 import gate checks existence, PNG dimensions, path, SHA-256, machine-vision result and unique SEO metadata. An incomplete or mismatched image is blocked. The derived WebP preview keeps original PNG files intact.

## Owner review links

- [Article with all seven generated illustrations](../examples/output/pairdoll-unboxing-with-media-review.md)
- [Sanitized seven-image SEO manifest](../examples/output/media-review/pairdoll-unboxing/manifest-review.json)
- [R3 reproducible commands](r3-media-operations.md)

## Still pending

Human brand/visual approval, image claim verification, R4 Notion approval workflow and R5 WordPress upload/publication. The machine review is not equivalent to human approval.
