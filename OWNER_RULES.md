# Andy Write Owner P0 Development Rules — v1.1.0

**Effective:** 2026-11-13. **Updated:** 2026-11-17. **Authority:** Highest priority within Andy Write project usage rules, above Skill files and task-level instructions; never above platform/security controls.

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

## P0-04 SCOPE_INTEGRITY — 初始任务范围不可篡改

Owner 原文（不可弱化）：

> **任何 Skill、AI 模型、搜索结果、参考文章、图片或素材，都不得擅自改变初始任务定义。**
>
> 如果发现产品对象、时间、来源身份或事实证据与初始约束冲突，必须停止对应操作并报告，不能自行扩大范围，也不能通过改写文字掩盖冲突。

**Preflight contract:** Before retrieval, analysis, writing, rewriting, QA, or media selection, freeze a task-specific Scope Contract containing (1) target subject, product identity and exclusions, (2) applicable dates/time windows and their intended use, (3) provenance, permission and role of each source class (Owner original, QC structural benchmark, factual evidence, media), and (4) the evidence standard for each important factual claim. Missing or ambiguous required fields block the affected operation until resolved.

**Hard boundary:** No Skill, model, search result, reference article, image, asset or later stage may expand or redefine that contract. Check candidate materials before admitting them; merely finding a relevant keyword or providing a link does not establish support for the same claim. If product identity, dates, source role or factual evidence conflicts, stop the affected operation, preserve the original definition, and report the exact mismatch and source. Do not paraphrase a conflict away, silently substitute a different product, or automatically repurpose a QC example as an original source.

**Controlled change:** Only the Owner can explicitly approve an amended scope; record the approval, scope version and impact before resuming. A mention of an excluded product in an approved comparison is not a change of primary subject. These boundaries are per task: a full-size sex doll task cannot be replaced with torso content, while an independently approved torso task remains legitimate.

**Evidence required:** frozen Scope Contract, source-role manifest, recorded block/allow decisions, claim-level relevant citations for important facts, and regression cases for wrong product, wrong date, mismatched source role, and unsupported claims.

## Other existing Owner P0 restrictions, retained

Codex CLI may ONLY rewrite a full preexisting user-provided article, with verifiable provenance, source SHA-256 and read-only tool-free execution. No Codex for coding, research, outlines, QA, media, website operations or other tasks. Image generation and video generation are prohibited with every provider, including Codex built-ins. Only passive review of historical/user-provided media is permitted.

Production publishing and GitHub main merges require separate Owner authorization; do not disclose credentials or commit source originals. A heuristic QA PASS does not equal verified facts.

## Mandatory acceptance sequence

1. Specify reusable Skill change, frozen task Scope Contract and source/QC baseline.
2. Implement in an isolated branch with backwards-compatible interfaces.
3. Run automated regression and relevant real-reference UAT, capturing actual measurements.
4. Open PR using .github/pull_request_template.md with previous stable commit and rollback procedure.
5. Request Owner approval before merging or deploying. If validation fails, retain previous stable version and revert the candidate.

**Policy version:** owner-p0-v1.1.0. Any change to these top-level rules must itself use PR, automated tests, UAT, rollback and Owner approval.
