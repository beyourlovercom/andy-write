# Owner P0: Codex CLI article rewrite only; all image/video generation disabled

Effective: 2026-11-13.

## Scope

- Codex CLI allowed: rewrite an existing full-length owner-provided article, native-English edit of that same article, targeted rephrasing/repair of existing chapters.
- Codex CLI prohibited: any research, source classification, outline planning, factual/SEO QA, software development, image/video generation, any site/system operation, publishing, WordPress or Notion.
- All image generation and video generation are disabled in Andy Write, irrespective of provider. No alternatives, fallback generator, direct image API, automation, or self-hosted generation.
- No existing generated assets deleted: the 7 R3 PNGs stay in the local Git-ignored UAT directory and 7 derived WebP previews stay in the private repository as historical artifacts.

## Technical enforcement

- ImageGen runner and media-generate CLI command are removed from the feature branch.
- Policy in configs/policy.json disables both media generation types.
- Explicit stage allowlist prevents Codex use for non-rewrite operations.
- Codex rewrite fails closed unless it has a substantial source article, provenance URL and matching R1 source fingerprint.
- Codex read-only subprocess result is rejected if any tool action is observed.
- Unrelated steps use non-Codex local tools; no Codex involved for media review.
- Automated policy regression tests execute with mocked subprocess, no real Codex invocation.

## Limitations

Repository gates cannot prevent an independent terminal user from calling the globally installed Codex binary outside Andy Write. Global Codex AGENTS.md instructions reinforce this Owner restriction, but are policy instructions rather than a tamper-proof operating-system access control.

The historical R3 ImageGen UAT report remains a factual record of earlier work, now superseded by this decision. No further images or videos may be generated without new explicit Owner authorization.
