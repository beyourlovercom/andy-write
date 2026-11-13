# andy-write

Independent versioned source-grounded editorial agent Skills.

**Highest Owner P0 project rules:** [AGENTS.md](AGENTS.md) and [OWNER_RULES.md](OWNER_RULES.md).

- **SKILL_FIRST — Skill 优先:** Fix reusable Skills instead of a single article.
- **EVIDENCE_BASED — 数据驱动:** Validate with real articles, QC baseline and reproducible metrics; do not rely on AI detector percentages.
- **VERSION_ROLLBACK — 版本可回退:** PR, automated tests, UAT, preserve previous stable versions and rollback refs.

Codex CLI remains strictly limited to rewriting a supplied article. All image and video generation remains disabled.

Run the offline Owner policy validator: python3 scripts/check_owner_rules.py
