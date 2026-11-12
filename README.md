# Andy Write Skills V1.0 — R0–R2 MVP

独立、可版本化的 AI 写作 Skill 系统。**本仓库不运行 WordPress 发布动作**，也不向线上站点写入任何内容。

## 已实现范围

- R0: Skill 契约、品牌隔离、独立 Private 仓库、来源追溯、敏感信息隔离。
- R1: Research 的 SerpApi 适配器（仅配置 API Key 时真实搜索）；默认 `dc_free` 模式通过中国 Mac 自建 DC 只读采集**明确列出的参考 URL**，并使用 OpenAlex 公开学术索引发现相关研究（非 Google SERP），绝不冒充 SERP 结果。Source 将原文按主题和段落归档，建立证据表。
- R2: 生成 Markdown 大纲、逐节写作 Prompt；支持导入本会话完成的英文草稿并执行编辑质量检查。提供 OpenAI Responses API 写作适配器，**需单独配置 OPENAI_API_KEY**。没有凭据时生成 Prompt，不虚构模型运行。
- QC 基准：只读取 KissSelf 2025-11 / 2025-12 的公开 WordPress API；仅存统计数据、不保存整篇 QC 正文。

## Quick start

从根目录执行：

```bash
python3 -m andy_write pipeline --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000
python3 -m andy_write usage --job examples/jobs/pairdoll-unboxing.json
python3 -m andy_write quality --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write media-plan --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write review --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
python3 -m andy_write benchmark --job examples/jobs/pairdoll-unboxing.json
python3 -m unittest discover -s tests -v
```

- 本地提供的 Notion 参考原文：`.runs/pairdoll-unboxing/source-original.notion.md`（不会进入 Git）。
- 默认使用 `dc_free` 来源模式，不需要 SerpApi 账号或 Key：采集已知网页 + OpenAlex 相关研究元数据；本地缓存 7 天以节约请求次数。它不能替代全网 Google 排名数据。可通过 `SERPAPI_API_KEY` + `research_mode: serpapi` 启用真实 Google SERP。
- 默认支持美国 Mac mini 的 Codex CLI + GPT-6.1 Terra (最低 0.159.0，当前已验证 0.167.2)，调用真实模型完成英文初稿、精修和限次字数修订；无需单独的 OpenAI API Key，但受到 ChatGPT Plus Codex 额度限制。
- 目标字数默认 1000 词，容差 7%；按真实模型响应记录 Tokens、缓存命中、阶段耗时；重复任务命中本地结果缓存不会重复耗费额度。
- 可选 --provider openai 需要独立 OPENAI_API_KEY；没有凭据会明确失败，不假冒模型生成。
- R3 已新增 Editor/Quality 基础检查和有条件的受影响章节定向修复；并新增封面 + 每个 H2 的媒体规划、图片文件校验门禁。**图片实际生成、视觉审核、Notion、Outreach、WordPress 发布尚未实现**。

## 安全规则

**PairDoll 只允许基于经 Owner 提供的参考文章改写；不允许独立虚构文章。** 旧 WordPress 文章（包括 Post 78585）不可修改。所有样稿仅供人工审核，不调用 WordPress 写入接口。没有依据时不得编造第一手体验、评价、数据、材料兼容性或厂家保证。所有编辑内注必须与发布正文分离。

详细信息见 [ARCHITECTURE](docs/architecture.md)、[UPSTREAM](docs/upstreams.md)、[AGENTS](AGENTS.md)。

完整 R2 Codex 接入指南：[Codex GPT-6.1 写作及用量日志](docs/codex-cli-r2.md)。

新一期 R3 Editor / Quality / Media 对照报告：[实测质量改进与后续门禁](docs/editor-quality-r3-uat-2026-11-12.md)。
