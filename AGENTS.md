# Andy Write — Owner P0 Highest Project Rules

> **Priority: OWNER_P0, effective 2026-11-13.** These rules outrank all Andy Write Skill instructions, workflow prompts, project plans, and historical UAT notes. They do not override applicable system or security requirements. Canonical policy: OWNER_RULES.md; structured mirror: policy/owner_rules.json.

## Three permanent development principles

1. **SKILL_FIRST — Skill 优先。** Every fix or improvement must become a reusable versioned Skill or shared contract with regression coverage. Repairing only one article is NOT completion.
2. **EVIDENCE_BASED — 数据驱动。** Compare real user-provided reference articles against traceable QC benchmarks and reproducible quality metrics. Save before/after evidence and limitations. AI detector percentages are NOT acceptance criteria, proof of authorship, or a measure of article quality.
3. **VERSION_ROLLBACK — 版本可回退。** Every Skill upgrade requires a GitHub PR, automated tests, recorded UAT/acceptance, and a concrete rollback ref. Preserve the stable version. Never push unreviewed changes directly to main, and never auto-merge.

## Other binding Owner P0 safety restrictions

- Codex CLI may ONLY rewrite an existing complete user-supplied article, including its English editing or chapter-level revision. Every rewrite requires a substantive original source, provenance and a matching recorded source SHA-256, and must be read-only and tool-free. Codex is forbidden for any research, classification, outlines, QA, code, deployment, Notion, WordPress, image/video work or any other task.
- ALL image generation and video generation are forbidden, regardless of provider or workaround. Prior images are only historical assets available for passive review.
- No WordPress production writes or GitHub main merges without separate explicit Owner approval.
- Do not commit secrets, customer data, original supplied articles, raw events, or ignored run directories.
- Never invent factual evidence, citations, product tests or tool success. Static QA passing is not human factual approval.

## Every Skill PR must provide

Owning reusable Skill change; real source and QC baseline; before/after evidence and method; regression/CI results; UAT; scope and compatibility; previous stable commit/tag plus rollback procedure; Owner merge approval status. The PR template and Owner policy checks formalize this.

See OWNER_RULES.md for detailed acceptance definitions.
