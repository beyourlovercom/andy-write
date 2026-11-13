# Andy Write Skills V1.0 — R0–R2 MVP

**Owner P0 — 最高研发规则（2026-11-13）：** [AGENTS.md](AGENTS.md) / [OWNER_RULES.md](OWNER_RULES.md)

- **SKILL_FIRST / Skill 优先：** 修复必须沉淀到通用 Skill 和测试，不能只改一篇文章。
- **EVIDENCE_BASED / 数据驱动：** 以真实原文、QC 基准和可复现指标验收，不把 AI 检测率当作内容质量指标。
- **VERSION_ROLLBACK / 版本可回退：** 每次升级必须经过 PR、自动测试、UAT、回退记录和 Owner 合并授权。

Codex CLI 仅限改写用户提供的完整文章；所有图片、视频生成均禁用。

最高级规则已在 `main` 生效，验证命令：`python3 scripts/check_owner_rules.py`。


独立、可版本化的 AI 写作 Skill 系统。**本仓库不运行 WordPress 发布动作**，也不向线上站点写入任何内容。

## 已实现范围

- R0: Skill 契约、品牌隔离、独立 Private 仓库、来源追溯、敏感信息隔离。
- R1: Research 的 SerpApi 适配器（仅配置 API Key 时真实搜索）；默认 `dc_free` 模式通过中国 Mac 自建 DC 只读采集**明确列出的参考 URL**，并使用 OpenAlex 公开学术索引发现相关研究（非 Google SERP），绝不冒充 SERP 结果。Source 将原文按主题和段落归档，建立证据表。
- R2: 生成 Markdown 大纲、逐节写作 Prompt；支持导入本会话完成的英文草稿并执行编辑质量检查。提供 OpenAI Responses API 写作适配器，**需单独配置 OPENAI_API_KEY**。没有凭据时生成 Prompt，不虚构模型运行。
- QC 基准：只读取 KissSelf 2025-11 / 2025-12 的公开 WordPress API；仅存统计数据、不保存整篇 QC 正文。

## Quick start

从根目录执行：

```bash
python3 -m andy_write run --job examples/jobs/pairdoll-unboxing.json
python3 -m andy_write write --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000
python3 -m andy_write usage --job examples/jobs/pairdoll-unboxing.json
python3 -m andy_write quality --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write media-plan --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write review --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write benchmark --job examples/jobs/pairdoll-unboxing.json
python3 -m unittest discover -s tests -v
```

- 本地提供的 Notion 参考原文：`.runs/pairdoll-unboxing/source-original.notion.md`（不会进入 Git）。
- 默认使用 `dc_free` 来源模式，不需要 SerpApi 账号或 Key：采集已知网页 + OpenAlex 相关研究元数据；本地缓存 7 天以节约请求次数。它不能替代全网 Google 排名数据。可通过 `SERPAPI_API_KEY` + `research_mode: serpapi` 启用真实 Google SERP。
- 默认支持美国 Mac mini 的 Codex CLI + GPT-6.1 Terra (最低 0.159.0，当前已验证 0.167.2)，仅改写用户提供的完整原文、精修和限次定向重写；无需单独的 OpenAI API Key，但受到 ChatGPT Plus Codex 额度限制。
- 目标字数默认 1000 词，容差 7%；按真实模型响应记录 Tokens、缓存命中、阶段耗时；重复任务命中本地结果缓存不会重复耗费额度。
- **V1.1 完整原文契约：** 模型改写前必须验证整篇 Owner 原文、来源、原文/Prompt SHA-256；旧摘要提示会被拒绝。真实输入完整性数据和限制见 [V1.1 UAT](docs/v1.1-full-source-skill-uat-2026-11-13.md)。
- 可选 --provider openai 需要独立 OPENAI_API_KEY；没有凭据会明确失败，不假冒模型生成。
- Owner P0（2026-11-13）：Codex CLI **仅允许改写用户提供的完整文章**，不得用于其他用途。**所有图片、视频生成禁用**，不允许通过其他工具绕过。既有 R3 图片仅为历史审核素材。

## 安全规则

**PairDoll 只允许基于经 Owner 提供的参考文章改写；不允许独立虚构文章。** 旧 WordPress 文章（包括 Post 78585）不可修改。所有样稿仅供人工审核，不调用 WordPress 写入接口。没有依据时不得编造第一手体验、评价、数据、材料兼容性或厂家保证。所有编辑内注必须与发布正文分离。

详细信息见 [ARCHITECTURE](docs/architecture.md)、[UPSTREAM](docs/upstreams.md)、[AGENTS](AGENTS.md)。

完整 R2 Codex 接入指南：[Codex GPT-6.1 写作及用量日志](docs/codex-cli-r2.md)。

新一期 R3 Editor / Quality / Media 对照报告：[实测质量改进与后续门禁](docs/editor-quality-r3-uat-2026-11-12.md)。

R3 真实配图验收与预览：
- [7 张配图的 Markdown 预览](examples/output/pairdoll-unboxing-with-media-review.md)
- [历史 ImageGen UAT（已停用，不得重跑）](docs/r3-imagegen-uat-2026-11-13.md)
- [R3 媒体禁令与历史素材审核](docs/r3-media-operations.md)

Owner 约束详见 [P0 Codex 文章改写专用与媒体生成禁令](docs/owner-policy-2026-11-13.md)。


## V1.2 跨文章忠实度验证（本地 Python，不调用 Codex）

每次改写完成，自动生成逐段忠实度映射报告与人工审核清单。
也可以对已有文章运行独立对照：

    python3 -m andy_write fidelity --source .runs/pairdoll-unboxing/source-original.notion.md --draft examples/output/pairdoll-unboxing-editor-quality-v2.md --report .runs/pairdoll-unboxing/fidelity-review.json

机器输出是精确文本、关键词匹配候选及待确认段落，不是语义保留率。
原文短段落和标题也全部编号，不再无声忽略。人工审核的合理删减
（尤其过时或不安全的原文建议）允许记录理由，不能通过重复堆词实现高分。

[真实双文章 UAT](docs/v1.2-cross-article-fidelity-uat-2026-11-13.md) ·
[Skill 操作与人工审核规则](docs/v1.2-fidelity-operations.md)
