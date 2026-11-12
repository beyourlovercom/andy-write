---
name: andy-write-media
description: "R3 article image planning: separate cover and each H2, visual grounding and unique SEO metadata."
---
# Andy Write Media — R3 planning foundation

Input: owner-approved article draft, H2 sections and brand assets.

1. Create one distinct cover prompt and one contextually grounded image task for each question-form H2.
2. Avoid unrelated images, generic repeated stock compositions, brand/product hallucinations, text overlays or explicit anatomy.
3. Do NOT fill SEO metadata before the image is generated and its actual pixels are visually inspected.
4. After generation, write UNIQUE image-specific Title, Alt, Caption and Description based on what the picture truly shows. Alt describes the visible content rather than stuffing keywords.
5. Record file path, checksum, visual reviewer, media size, and final metadata for every real image; reject any missing picture/metadata or duplicated Alt text.
6. Never upload media to R2 source articles or WordPress without a separate approved R3/R5 deployment step.

This version implements the task manifest and metadata completeness checks; automatic image generation, visual inspection and WordPress media upload are NOT implemented.
