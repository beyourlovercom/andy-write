# R10 — KS04 / KS05 真实证据复核与 QC 提醒取舍建议

- **复核日期：** 2026-11-21（Asia/Hong_Kong）
- **任务范围：** 仅核查 KissSelf 公共基准文章中两条候选提醒的可复核性，给出后续 QC 规则是否保留的技术建议。
- **原文：** [How to Boost Intimacy Using Waterproof Toys in the Shower](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html)（页面标记 Updated October 4, 2026）
- **阶段：** R10 Draft PR #10；人工、只读验证；非本地 Google SERP Search Intent 裁定。
- **边界：** 不改写 KissSelf、R8 冻结原稿、Scope Contract，不启用默认 QC 流水线、不合并、不部署。
- **与 Owner 决策的关系：** KS04/KS05 在 Owner 五项审核中原为「待查」。以下是证据复核后的 **QC 保留建议**，不是 Owner 已批准、不代表文章内容被判事实虚假。

## 结论

| 候选 | 推荐保留？ | 严重度 | 核查结论 | 误报控制 |
|---|---|---|---|---|
| KS04 按摩棒防水／电池参数 | **保留，收窄为型号及参数归属提醒** | P1 REVIEW | 找到了高度吻合的真实型号 **Magic Wand Waterproof HV-360** 和厂家规格／手册；问题在于文章未标明该型号，并把一组具体参数写成泛化的「Waterproof Model」 | 不因 IPX7、4 档等数值本身判虚假；有明确型号及对应说明书时可放行 |
| KS05 匿名限时报价 | **保留** | P2 REVIEW | 原文价格表出现 **Limited Time Offer / $89**，该行没有产品名称、SKU、商品链接、报价观察日或到期日；无法判定 $89 属于什么产品或是否仍有效 | 只提醒含促销／现价而无法定位商品与日期的行；一般价位范围不机械拦截 |

## KS04 — 原文与第一手证据

### 原文现场

1. [KissSelf #Massage_Wands](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Massage_Wands) 在对比表中以「Waterproof Model」指称一个未命名对象，列出：
   - 4 种强度、4 个震动模式；
   - IPX7、1 米／30 分钟；
   - 约 4 小时充电、约 2.5 小时运行；
   - 充电时不运行。
2. 该处文章没有明确品牌／型号／SKU。IPX7 文内链接指向媒体解释材料，不是对应产品说明书；非防水列的「3 小时充电／3 小时运行」和「通常能边充边用」也未在该段确定可核验型号。

### 真实产品证据

- [Magic Wand Original／Vibratex 产品页：Magic Wand Waterproof](https://magicwandoriginal.com/magic-wand-waterproof-massager/)：品牌官方资料明确该系列有 **IPX7、4 强度／4 模式**。该站声明 Vibratex 负责正品 Magic Wand 的进口、分销与营销；品牌站因网页检索访问限制，本轮采用已索引内容交叉复核。
- [Magic Wand Waterproof HV-360 原厂用户手册 PDF](https://theoriginalwand.com/wp-content/uploads/2025/09/Hitachi-Magic-Wand-Waterproof-HV-360-Instructions-User-Manual.pdf)：封面标注 HV-360；第 9 页四档／四模式；第 11 页写明约 **4 小时**充满、约 **2.5 小时**续航，后者测试条件是 25°C、空载；第 9 页写明连接充电器时不可运行。**手册由经销商托管，但文档本身为对应型号厂商说明书**。
- [Magic Wand US：HV-360 产品资料](https://magicwandus.com/products/magic-wand-waterproof-hv-360-personal-massager)：将 IPX7、4 档／4 模式、充电 4 小时／续航约 2.5 小时直接绑定 HV-360 型号，是独立在售页面的交叉核对。

**证据判断：** 有充分证据说明这组数字在至少一个特定型号上是有来源的，**不是已证伪的捏造数据**；但尚不能把它泛化到所有「防水按摩棒」。例如「2.5 小时」是手册条件下的典型电池持续时间，而非任何使用强度下的保底时长。此外，型号、手册年份与批次可能影响参数，不能据此确认所有同类产品通用。

**重要安全限定：** HV-360 手册明确禁止在洗澡／淋浴的湿区充电，不能把表格「边充边用」的泛化比较理解为允许在湿区插电使用。

**建议保留的 QC 行为：**
- 若内容给出具体 IP 评级、充电／续航、震动档位或安全操作声明，却只写类别名称／“Waterproof Model”，发 **P1「型号及厂商证据缺失」**。
- 提醒编辑补足具体型号、制造商资料链接和适用条件；已附有准确型号与来源时，不应仅因数字出现而触发误报。
- 既不自动判为事实错误，也不要求自动删除这些数字；对原文只记录修订建议。

## KS05 — 原文与报价核对

### 原文现场

[KissSelf #Suction_Toys](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Suction_Toys) 的产品／报价表第一行把 **Limited Time Offer** 放在「Toy Name」列，并列 **$89**。

同一表其他行至少具有可辨认的品牌／型号（如 LELO Sona 2 Cruise），但不能用那些商品的身份来推断 $89 对应哪款商品；该行没有独立产品链接和报价日期／促销结束时间。

### 第三方核对边界

- [LELO SONA 2 Cruise 厂商产品页](https://www.lelo.com/sona-2-cruise) 可追溯该**另一行**的型号、常规 $159 标价，并能观察促销价随活动变化；这 **不** 支持匿名 $89 行。
- 对匿名 $89 这行，由于没有唯一商品身份、店铺和有效期，**不存在可执行的 SKU 级价格交叉核验**。本结论是「可追溯资料缺失」，**不是**「$89 一定错误」。

**建议保留的 QC 行为：**
- 出现「限时优惠」／当前售价等实时营销文案时，若商品名称／SKU／有效链接、观察日期或促销期限缺失，则发 **P2「报价可追溯性不足」**。
- 作为人工核查提醒，不自动标记价格错误；合理的非实时报价区间或明确注明为示意的例子避免机械拦截。
- 原文建议：识别商品并补齐可验证链接／报价时间，或去掉无法核验的限时营销行；**此处并未获授权改文**。

## 裁定与后续门禁

1. **研究建议：KS04 = KEEP_P1_MODEL_EVIDENCE; KS05 = KEEP_P2_OFFER_TRACEABILITY。** 两者仍为人工 REVIEW 提醒，优先保持当前可回退的手工 Dev 方式。
2. KS04 的实证发现有助于降低误报：准确来源只能证明某**具体型号**的参数，不是证明原文的泛化表达准确。若未来升级规则，须加「带型号／厂家证据则不误报」的测试。
3. KS05 通过文本本身证实缺少产品身份和价格时间链；不应以找不到对应 $89 商品为由宣称这是虚假价格。
4. **Owner 原先的 KS04/KS05「待查」不擅自改为 Owner 已确认。** 若要将建议冻结为已批准的永久规则，另行提交 Owner 选择和 Dev 回归。
5. 本次未改写任何文章、未编辑运行时规则／Skills、未补造人工真值、未合并 PR、未发布 Production；Search Intent Match 仍 Unassessable（缺目标关键词与当地 SERP）。

### 证据等级与限制

- **可直接复现：** KissSelf 2026-11-21 可见原文表格和营销行；HV-360 原厂手册/供应商资料中明确型号参数。
- **有条件匹配：** KS04 的表格高度吻合 HV-360，**但文章没有说它用的是该型号**，所以不能声称溯源已被原作者确认。
- **无法核验：** KS05 匿名 $89 的商品和日期；不产生真假定论。
- **不在本次范围：** 历史价格回溯、OEM 批次实测、Search Intent SERP 验收、生产环境写入。
