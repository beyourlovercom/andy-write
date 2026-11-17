# Andy Write — Owner P0 Highest Project Rules

> **Priority: OWNER_P0, effective 2026-11-13; updated 2026-11-17.** These rules outrank all Andy Write Skill instructions, workflow prompts, project plans, and historical UAT notes. They do not override applicable system or security requirements. Canonical policy: OWNER_RULES.md; structured mirror: policy/owner_rules.json.

## Four permanent development principles

1. **SKILL_FIRST — Skill 优先。** Every fix or improvement must become a reusable versioned Skill or shared contract with regression coverage. Repairing only one article is NOT completion.
2. **EVIDENCE_BASED — 数据驱动。** Compare real user-provided reference articles against traceable QC benchmarks and reproducible quality metrics. Save before/after evidence and limitations. AI detector percentages are NOT acceptance criteria, proof of authorship, or a measure of article quality.
3. **VERSION_ROLLBACK — 版本可回退。** Every Skill upgrade requires a GitHub PR, automated tests, recorded UAT/acceptance, and a concrete rollback ref. Preserve the stable version. Never push unreviewed changes directly to main, and never auto-merge.

4. **SCOPE_INTEGRITY — 初始任务范围不可篡改。** Before any research, writing, evaluation, or media work, freeze the job's product/topic identity, temporal bounds, source provenance and role, and claim-level evidence requirements in a task-specific Scope Contract. No downstream source or model may silently change it.

> **任何 Skill、AI 模型、搜索结果、参考文章、图片或素材，都不得擅自改变初始任务定义。**
>
> 如果发现产品对象、时间、来源身份或事实证据与初始约束冲突，必须停止对应操作并报告，不能自行扩大范围，也不能通过改写文字掩盖冲突。

**Implementation: `ANDY_WRITE_ARTICLE_SCOPE_V1`.** Every new article must have an Owner-specified `article_scope` in its own job JSON and a frozen private `.runs/_article_scopes/<job_id>.json` contract before research. Use `python3 -m andy_write scope-init --job PATH` or the normal `run` command. All job-based stages and both rewrite backends validate the same fingerprint; any change stops and requires explicit recorded Owner authorization. Read `skills/andy-write-article-scope/SKILL.md` and `docs/ANDY_WRITE_ARTICLE_SCOPE_V1.md` before downstream article Skills. Existing unscoped articles are not silently backfilled.

Treat a QC structural reference as structural evidence only, never as the Owner's rewrite original or as automatic support for product facts. A full-size doll cannot be silently replaced by a torso; mentioning a torso in an expressly authorized comparison is allowed. Any scope change requires explicit Owner approval and a new version of the Scope Contract.

## Other binding Owner P0 safety restrictions

- Codex CLI may ONLY rewrite an existing complete user-supplied article, including its English editing or chapter-level revision. Every rewrite requires a substantive original source, provenance and a matching recorded source SHA-256, and must be read-only and tool-free. Codex is forbidden for any research, classification, outlines, QA, code, deployment, Notion, WordPress, image/video work or any other task.
- ALL image generation and video generation are forbidden, regardless of provider or workaround. Prior images are only historical assets available for passive review.
- No WordPress production writes or GitHub main merges without separate explicit Owner approval.
- Do not commit secrets, customer data, original supplied articles, raw events, or ignored run directories.
- Never invent factual evidence, citations, product tests or tool success. Static QA passing is not human factual approval.

## Every Skill PR must provide

Owning reusable Skill change; real source, a frozen task Scope Contract, and QC baseline; before/after evidence and method; regression/CI results; UAT; scope and compatibility; previous stable commit/tag plus rollback procedure; Owner merge approval status. The PR template and Owner policy checks formalize this.

See OWNER_RULES.md for detailed acceptance definitions.
