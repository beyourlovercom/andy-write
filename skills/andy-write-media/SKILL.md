---
name: andy-write-media
description: "Generate section-specific real raster images via Codex built-in ImageGen and prepare unique, visually grounded SEO media for Owner review."
---
# Andy Write Media R3

Input: vetted article draft, section plan and brand policy.

1. Use media-plan to prepare a cover plus one distinct H2 scene each.
2. Use media-generate through the US Mac mini built-in Codex ImageGen. Do not invent an image or quietly use Pillow/SVG/stock substitutes. No independent image API Key needed.
3. The generation agent must view actual image pixels and record visible objects, scene relevance, mismatches and preliminary SEO metadata. A generated file is not a verified file until inspected.
4. media-import checks actual PNG bytes, dimensions, SHA-256 and metadata. Reject missing/mismatched images and duplicate Alt text.
5. media-export retains original PNGs and creates smaller WebP review copies plus a captioned Markdown preview.
6. Label these scenes AI-generated illustrations, not actual shipped product, factory photos or customer reviews.
7. Keep human approval pending and prohibit WordPress/Notion publication until a separate Owner approval.

Commands:

    python3 -m andy_write media-generate --job examples/jobs/pairdoll-unboxing.json
    python3 -m andy_write media-import --job examples/jobs/pairdoll-unboxing.json
    python3 -m andy_write media-export --job examples/jobs/pairdoll-unboxing.json

The image generation runner is idempotent for already verified local assets. It aborts rather than overwriting an existing image with no visual review record.
