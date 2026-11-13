# Andy Write Owner P0 Development Rules — v1.0.0

**Effective:** 2026-11-13. **Authority:** Highest priority within Andy Write project usage rules, above Skill files and task-level instructions; never above platform/security controls.

## P0-01 SKILL_FIRST — Skill 优先

Owner rule: 每次解决一个问题，都将改进沉淀到通用 Skill，而不是只修某篇文章。

Every repair must change the applicable reusable Skill, its shared contract or its regression tests. A one-off prompt or article edit is not final completion. Identify cross-article and cross-brand applicability. When practical, test a second article type before declaring a change stable.

**Evidence required:** owning Skill and version, generalized behavior, regression cases, and an example showing the original defect is fixed.

## P0-02 EVIDENCE_BASED — 数据驱动

Owner rule: 通过真实文章、QC 基准和质量指标验证优化效果，不凭 AI 检测器的百分比判断好坏。

Use real Owner-provided reference articles, documented QC comparison sources, and reproducible metrics (source detail retention, factual support, completeness, actionable information, valid links, language quality assessment, token cost). Report before and after, uncertainty, and limitations. AI detector percentage is forbidden as the deciding acceptance metric; it is not proof of human authorship, originality or content quality.

**Evidence required:** source provenance, baseline, metric definitions, before/after results and human editorial/UAT signoff when needed.

## P0-03 VERSION_ROLLBACK — 版本可回退

Owner rule: 每次升级经过 GitHub PR、自动测试与验收，保留旧版本，不破坏已稳定的能力。

Develop on a branch and submit a GitHub PR. Complete automated tests and record UAT before Owner-controlled merge. Include exact rollback commit/tag and restoration instructions. Protect prior stable Skill contracts. No direct main push, no automatic merge, no unapproved publish.

**Evidence required:** PR URL, passing CI, acceptance/UAT results, compatibility note, rollback ref and explicit Owner merge approval.

## Other existing Owner P0 restrictions, retained

Codex CLI may ONLY rewrite a full preexisting user-provided article, with verifiable provenance, source SHA-256 and read-only tool-free execution. No Codex for coding, research, outlines, QA, media, website operations or other tasks. Image generation and video generation are prohibited with every provider, including Codex built-ins. Only passive review of historical/user-provided media is permitted.

Production publishing and GitHub main merges require separate Owner authorization; do not disclose credentials or commit source originals. A heuristic QA PASS does not equal verified facts.

## Mandatory acceptance sequence

1. Specify reusable Skill change and source/QC baseline.
2. Implement in an isolated branch with backwards-compatible interfaces.
3. Run automated regression and relevant real-reference UAT, capturing actual measurements.
4. Open PR using .github/pull_request_template.md with previous stable commit and rollback procedure.
5. Request Owner approval before merging or deploying. If validation fails, retain previous stable version and revert the candidate.

**Policy version:** owner-p0-v1.0.0. Any change to these top-level rules must itself use PR, automated tests, UAT, rollback and Owner approval.
