# Andy Write Skills V1.0 — R0–R2 MVP

独立、可版本化的 AI 写作 Skill 系统。**本仓库不运行 WordPress 发布动作**，也不向线上站点写入任何内容。

## 已实现范围

- R0: Skill 契约、品牌隔离、独立 Private 仓库、来源追溯、敏感信息隔离。
- R1: Research 的 SerpApi 适配器（仅配置 API Key 时真实搜索）；无 Key 时只读采集**明确列出的参考 URL**，绝不冒充 SERP 结果。Source 将原文按主题和段落归档，建立证据表。
- R2: 生成 Markdown 大纲、逐节写作 Prompt；支持导入本会话完成的英文草稿并执行编辑质量检查。提供 OpenAI Responses API 写作适配器，**需单独配置 OPENAI_API_KEY**。没有凭据时生成 Prompt，不虚构模型运行。
- QC 基准：只读取 KissSelf 2025-11 / 2025-12 的公开 WordPress API；仅存统计数据、不保存整篇 QC 正文。

## Quick start

从根目录执行：

```bash
python3 -m andy_write run --job examples/jobs/pairdoll-unboxing.json
python3 -m andy_write review --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-v2.md
python3 -m andy_write benchmark --job examples/jobs/pairdoll-unboxing.json
python3 -m unittest discover -s tests -v
```

- 本地提供的 Notion 参考原文：`.runs/pairdoll-unboxing/source-original.notion.md`（不会进入 Git）。
- 默认使用 `curated` 来源模式。可通过 `SERPAPI_API_KEY` 启用真实 Google 搜索。
- 可使用 `OPENAI_API_KEY` 并执行 `python3 -m andy_write write --job ... --model ...` 进行自动写作；凭据缺失时程序拒绝假装成功。
- R3 Media、Quality 正式门禁、Notion、Outreach、Publish 尚未实现。

## 安全规则

**PairDoll 只允许基于经 Owner 提供的参考文章改写；不允许独立虚构文章。** 旧 WordPress 文章（包括 Post 78585）不可修改。所有样稿仅供人工审核，不调用 WordPress 写入接口。没有依据时不得编造第一手体验、评价、数据、材料兼容性或厂家保证。所有编辑内注必须与发布正文分离。

详细信息见 [ARCHITECTURE](docs/architecture.md)、[UPSTREAM](docs/upstreams.md)、[AGENTS](AGENTS.md)。
