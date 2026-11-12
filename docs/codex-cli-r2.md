# R2 自动写作执行器 — Codex CLI GPT-6.1

执行设备：美国 Mac mini，使用 BYL DC。该机 Codex CLI 已从 0.149.0 升级到 0.167.2，并已验证 GPT-6.1 Terra 可用。美国 Mac 的本地默认模型已变更为 gpt-6.1-terra；Andy Write 的每次调用也会显式传入模型 ID。

## 运行命令

完整 R1–R2，包括来源、证据、Markdown 大纲、英文初稿、编辑、字数修订：

    cd /Users/a/ai/andy-write
    python3 -m andy_write pipeline --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000 --tolerance 0.07 --max-revisions 1

只重新运行写作、编辑（相同参数命中缓存后不会重复调用）：

    python3 -m andy_write write --job examples/jobs/pairdoll-unboxing.json --model gpt-6.1-terra --target-words 1000

查看实际使用记录：

    python3 -m andy_write usage --job examples/jobs/pairdoll-unboxing.json

必要时使用 --force 重新生成；会产生新的模型调用，额外消耗套餐额度。

## 质量和额度规则

- GPT-6.1 Terra 最低 CLI 版本 0.159.0；使用非交互 JSONL 接口捕获每次真实 turn.completed.usage。
- 通过现有 ChatGPT 登录使用 Codex，免费于普通 API 独立账单，但会消耗 Codex 订阅额度；不是无限量。
- 只读 CLI 沙盒，不允许在 WordPress、Notion 或其他站点发布。
- 初稿和编辑各一次；如字数偏离、缺少六个问句 H2 或结构 QA 未通过，允许最多一次修订。最多可设 2 次。
- 默认 1,000 英文词，容差 7%，即 930–1,070 词。字数由 Python 独立计数，不能相信模型自行报告字数。
- 缓存依赖模型 ID、Prompt 哈希、实际输出 SHA-256。相同任务重复执行不会重新消耗模型用量。
- 每次真实成功或失败的调用记录到本地 codex-usage-ledger.jsonl：时间、模型、阶段、输入/缓存/输出/推理 Tokens、词数、结果和失败原因。
- 输入 Tokens 已包含缓存输入，输出 Tokens 的推理部分不另行加总。ChatGPT 订阅调用无法直接换算实际 API 账单。
- 本地规则 PASS 不等于事实核查 PASS。必须经人工审核才可公开发布。

## 本地输出

- article-auto-draft.md：GPT-6.1 初稿
- article-auto-edit.md：英文精修
- article-auto-tighten-1.md：若有超额，追加修订
- article-auto-final.md：本地送审稿
- codex-writing-result.json：真实字数及规则结果
- codex-usage-ledger.jsonl：逐次调用 Token 账本
- codex-<stage>-receipt.json：每个阶段的缓存指纹与使用量

所有运行日志均处于 Git 忽略的 .runs/ 下，不会提交原始 Notion 参考原文或模型事件流。
