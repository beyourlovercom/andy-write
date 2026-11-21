# R11 — KissSelf 模型参数与报价溯源 QC 升级／Dev UAT（2026-11-21）

**状态：Dev technical PASS；Owner UAT 待确认；Draft PR 待 CI / 审阅。**

## 目标和授权边界

Owner 授权 R11 将 R10 KS04/KS05 的实证发现沉淀为**可复用 Skill、检测条件、回归测试**，并使用**两份同一冻结 KissSelf 真实 WP 原文快照**对比升级前后 QC 输出。原文仅为公开结构／风险基准，不是 Owner 写作原稿或自动事实真值。禁止改写文章、接入默认写作流水线、合并或 Production 发布。

- R10 起点：`c982907dd2cff36aa95907b9bd3fa0991c7aa288`（原 Draft PR #10）。
- R11：`feat/r11-kissself-model-offer-qc`，**堆叠在 R10 Draft 分支上**，并非对 `main` 的独立完整改动。
- 代码：`andy_write/qc_context.py`；复用规则：`skills/andy-write-quality/SKILL.md`。
- 回归：`tests/test_qc_context.py` 和 `tests/test_qc_report_comparison.py`。
- 可复核工具：`scripts/compare_context_qc_reports.py`；所有原文、执行报告均保存在 US Mac mini Git 忽略的 `.runs`。

## 前后结果（美国 Mac mini／自建 DC）

| 冻结基准 | 内容 SHA-256 | R10 v1 | R11 v1.1 | P0 / P1 / P2 | 位置变化 |
|---|---|---:|---:|---|---|
| KissSelf #26268 成人淋浴防水玩具 | `f691c7f330bef6e15589c68b2ef231fabfc7a393f8f00f9acb38eb5c84f19af9` | 7 | 7 | 2 / 4 / 1 → 2 / 4 / 1 | 0 增加，0 移除 |
| KissSelf #26353 成人玩具清洁 | `a3dc40ad6144eede73bf2e265b8cf67118aacdaa474b2ccc0c072a1f1f8f9363` | 3 | 3 | 0 / 3 / 0 → 0 / 3 / 0 | 0 增加，0 移除 |

两份 `compare_context_qc_reports.py` 输出均为 `same_candidate_locations: true`，验证了**相同 URL／post ID／modified／rendered SHA-256／source role／scope／Search Intent 状态**，未使用不同页面版本营造对比提升。

### KS04：证据类型更具体

- 第一篇 `Massage_Wands` P1 仍为 `MODEL_SPEC_PROVENANCE_REVIEW`。
- R11 输出：`explicit_model_identifier_present=false`；`claim_source_link_present=true`；`manufacturer_passage_verified=false`；缺口 `model_identity_unstated`、`exact_model_manual_passage_unverified`。
- 解释：IPX7 链接存在并不能证明所有防水按摩棒型号通用；[R10 真实证据复核](R10_KS04_KS05_REAL_EVIDENCE_REVIEW_2026-11-21.md)发现 Magic Wand Waterproof HV-360 厂商手册的特定数据高度吻合，因此**不判捏造**，只要求注明型号、对应手册及条件。
- 加入数值充电／续航声明的检测；带型号与链接也仍需要真人核对型号与说明书原句，不自动 PASS。

### KS05：促销身份和时效拆分

- 第一篇 `Suction_Toys` P2 仍为 `PRICE_OFFER_FRESHNESS_REVIEW`。
- R11 输出：`anonymous_offer_row_present=true`；`price_observation_date_present=false`；`row_product_link_present=false`；缺口 `offer_product_identity_missing`、`price_observed_at_missing`、`offer_validity_unverified`。
- 已命名、已有观察日期的**普通价格**是回归负例，不机械报匿名促销；即使有观察日期，匿名“Limited Time Offer / $89”仍须 REVIEW。没有判定 $89 虚假。

## 验证和质量门禁

- US Mac mini 隔离工作树：`/Users/a/ai/worktrees/andy-write-r11-dev`，本轮未覆盖 R10 Dev 工作树，也未重启设备／Chrome。
- `python3 -m unittest discover -s tests -q`：**219/219 PASS**（R10 为 210 项；R11 新增 6 项 KS04/KS05 正反例及 3 项对比工具测试）。
- 两篇真实样本 `qc-context`：均 `HUMAN_REVIEW_REQUIRED`，`publish_ready=false`，`human_labels_present=0`，`validated_truth_errors=null`；Search Intent 仍 `UNASSESSABLE`。
- 冻结内容未经更新，抓取样本依然只作为公开文章基准；无人工精确率／召回率或真实写作质量评分。
- 这次对比证明**证据缺口表述更可操作，且两样本候选位置未回归**；**没有证明误报率下降或 Andy Write 新文章质量提高**。

## 复现（只读、Dev 私有数据）

```bash
python3 -m unittest discover -s tests -q
python3 -m andy_write qc-context --post-json .runs/r11-kissself-20261121/first_current_wp.json --scope docs/r9_kissself_benchmark_scope.v1.json --report .runs/r11-kissself-20261121/first_after.json
python3 -m andy_write qc-context --post-json .runs/r11-kissself-20261121/second_current_wp.json --scope docs/r10_kissself_cleaning_scope.v1.json --report .runs/r11-kissself-20261121/second_after.json
python3 scripts/compare_context_qc_reports.py --before .runs/r11-kissself-20261121/first_context_report.json --after .runs/r11-kissself-20261121/first_after.json --report .runs/r11-kissself-20261121/first_comparison.json
python3 scripts/compare_context_qc_reports.py --before .runs/r11-kissself-20261121/second_context_report.json --after .runs/r11-kissself-20261121/second_after.json --report .runs/r11-kissself-20261121/second_comparison.json
```

## 兼容、回滚和下一步

- 兼容：仍为 `qc-context` **手动、离线、只读**；同一候选代码、优先级和源锁定条件；schema 从 `andy-write-context-qc/v1` 升到 `/v1.1`，新增 `review_details`。未修改默认写作流程或 Scope Contract。
- 回滚：如 R11 审核不通过，保留 R10 基线 `c982907dd2cff36aa95907b9bd3fa0991c7aa288`，不用合并即可丢弃 R11 分支；已部署的 R10 Dev 工作树未变。
- 待完成：GitHub Draft PR CI、Owner 阅读审核；**无独立事实真值标签，不得将 219 个测试冒充生产／内容质量验收**。
- 下一阶段 R12：如 Owner 另行授权并提供精确完整原稿、冻结 Article Scope Contract 和审稿人，方可做**真实写作 A/B 与独立编辑评分**；本次 R11 仅比较 QC 系统在两份真实竞品文章上的表现。
