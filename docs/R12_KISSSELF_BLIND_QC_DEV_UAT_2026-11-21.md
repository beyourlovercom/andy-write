# R12 — KissSelf 真实来源盲评 QC：技术就绪，人工阶段待完成

- 日期：2026-11-21（Asia/Hong_Kong）
- 授权：Owner 批准按 R12.1 冻结真实文章／标准 → R12.2 独立盲评 → R12.3 评估的顺序推进；**不授权写作、改稿、合并或 Production**。
- 当前状态：**R12.1 数据冻结／离线评审包 Dev technical PASS；R12.2 两名独立真人审稿人尚未提交源文标签；没有真实 TP/FP/FN、可操作性均分或 Owner UAT PASS。**
- GitHub：`feat/r12-kissself-blind-qc`，叠加在 [R11 Draft PR #11](https://github.com/beyourlovercom/andy-write/pull/11) 的 `9138ab912b4836c38c7e243d1b825bd131ef9c25` 上；没有动 main。

## 真实样本和锁定

| 来源角色（两篇均为 `public_competitor_qc_benchmark_only`） | Post ID | WordPress rendered HTML SHA-256 | 逐节独立审查单位 | R10 → R11 候选 |
|---|---:|---|---:|---:|
| KissSelf 防水淋浴成人玩具 | 26268 | `f691c7f330bef6e15589c68b2ef231fabfc7a393f8f00f9acb38eb5c84f19af9` | 29 | 7 → 7 |
| KissSelf 成人玩具清洁 | 26353 | `a3dc40ad6144eede73bf2e265b8cf67118aacdaa474b2ccc0c072a1f1f8f9363` | 29 | 3 → 3 |

两份输入均为 R11 Dev 已使用的私有、冻结 WP 快照；`build_source_packet` 再次验证 Scope Contract 的 URL、Post ID、modified、rendered SHA-256 和来源角色。总计 **58 个源文审查单位**，无跨文章借用 Scope。`source_lock`：`3b78ec13edb9c26ce8040e425320f5a8d3903cb13e9e622a21c6908dd1b4496e`。

**重要边界：** 竞品文章是 QC 结构／风险基准，不是 Owner 原稿、可照抄文本、厂家事实真值或经过本地化验证的 Search Intent 数据。KS01–KS03 的 Owner「保留提醒」选择不是人工真值；KS04/KS05 的研究建议亦不是 Owner 最终签核。

## 盲评机制及当前进度

1. **源文先盲审（真实包已生成）**：用 `source-pack` 枚举全部 58 节，不提供 R10/R11 候选位置、检测文字或版本。两位不同的真人编辑逐节填是否有「值得人工核查的缺口」，包括明确审过的阴性段落；正向标签须填写理由。`source-html` 提供完全离线、中文填写界面，导出后仍按 `source_lock` 验证；全文和人工记录只留在美国 Mac mini `.runs`。
2. **冻结独立金标（尚未执行）**：`seal-gold` 必须验证两份完整、不同身份的人工标注；有分歧时只能通过同一 source lock 下的 Owner 逐项裁定。空模板、同一审稿人、缺节、缺正向理由均失败关闭。
3. **隐藏版本提醒对照（被第 2 步门禁阻断，未生成）**：`pair-pack` 把两份相同来源的候选以匿名 A/B 随机左右呈现，版本映射仅存 `.runs/.../sealed/`、不能交给审稿人。`pair-html` 让两名独立编辑为每张提醒的可操作性打 0–3 分。
4. **揭盲后计分（尚未执行）**：`score` 仅在金标和两套完整匿名评分都存在时计算逐节／类别的审查机会 `TP/FP/FN`、precision/recall 及提醒可操作性均分。**这些指标不是事实真假、搜索意图匹配率或实际文章写作质量。**

由于 R10 → R11 的 10 个候选身份和位置全部相同，即使真人标注完成，**理论上两版候选检出 precision/recall 必然相同**；有可能改善的是提醒解释的可操作性，须经过真正的隐藏版本评分才可断言。

## 验证记录（美国 Mac mini，自建 DC）

- 隔离工作树：`/Users/a/ai/worktrees/andy-write-r12-dev`，与 R10/R11 Dev 并行独立；未重启设备、Chrome 或任何应用。
- `python3 -m unittest discover -s tests -q`：**231/231 PASS**；在本地与 Mac Dev 各通过。
- `source-pack`：两篇 29+29 个源文单位；有私有 `source_only_private.json`、两个空人工模板（`reviewer_id=null`）、`source_only_review.html`；未代填任何标签。
- HTML：美国 Mac mini 上 `node` JavaScript 语法校验 **PASS**；私有表单及模板权限均为 `-rw-------`。
- 未调用外部模型／付费接口，没有原文或个人标注上传 GitHub，未接入默认写作 QC 流水线，没有 WordPress 或 Production 写入。

## 复现（仅隔离 Dev 的私有输入）

```bash
python3 -m unittest discover -s tests -q
python3 scripts/r12_blind_qc.py source-pack \
  --case .runs/r12-kissself-20261121/first_current_wp.json docs/r9_kissself_benchmark_scope.v1.json \
  --case .runs/r12-kissself-20261121/second_current_wp.json docs/r10_kissself_cleaning_scope.v1.json \
  --out .runs/r12-kissself-20261121/source_only_private.json \
  --review-a .runs/r12-kissself-20261121/editor_a_source_labels.json \
  --review-b .runs/r12-kissself-20261121/editor_b_source_labels.json
python3 scripts/r12_blind_qc.py source-html \
  --source-pack .runs/r12-kissself-20261121/source_only_private.json \
  --out .runs/r12-kissself-20261121/source_only_review.html
```

**上述文件已存在；`source-pack` 和 `source-html` 默认采用独占创建以保护真实审稿数据，请勿重复覆盖。** 填完两份独立审稿表单并完成有争议项 Owner 裁决之后才能执行下一阶段命令；没有机器人或脚本代填路径。

## Owner 待办与回滚

1. 指定两位**不同的真实编辑**分别使用离线表单完成 58 节的源文盲审，不要让第二位先看第一位的结论。预计审稿工作量由 Owner/编辑自定；本轮尚无真实耗时。
2. 对不一致段落进行 Owner 仲裁，随后才能放出 10 组匿名 A/B 提醒、两位独立打分及最后的检出／可操作性对照。
3. 只有拿到人工得分才决定是否修正 Skill 阈值或文案；不因静态测试 PASS 就宣布真实质量提升。文章改写仍须另行授权。
4. 代码回滚：保留稳定的 R11 `9138ab912b4836c38c7e243d1b825bd131ef9c25` 和独立 R11 Dev 工作树；如 R12 方案未被接受，保持 R12 Draft 不合并，停止使用私有 R12 评测包即可。
