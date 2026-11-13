# R3 media: generation disabled by Owner (effective 2026-11-13)

**P0 rule: NO image generation and NO video generation by any tool. Codex CLI may ONLY rewrite user-provided articles.**

The older ImageGen test (7 PNGs, 7 WebPs) is a closed, historical UAT. Do not repeat it. The CLI command media-generate and the old ImageGen runner were removed.

Allowed R3 operations (do not invoke Codex or any generator):

- Review/inspect already-existing, legitimate owner-supplied image files or preserved historical test assets.
- Validate metadata against actual pixels, compare to the correct H2, inspect SHA-256 and dimensions.
- Keep pending human approval and no WordPress publishing without separate permission.

Previously produced image previews remain in the private GitHub draft for audit history; they are NOT a mandate to continue generation or proof of actual product packaging.
