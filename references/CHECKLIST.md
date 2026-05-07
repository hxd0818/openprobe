# 执行检查清单（v10 — 唯一必读文件）

> **这是调查执行的核心控制文档**。每轮迭代前打开，逐项打勾。
> 其他reference文件是"为什么这样做"的论文，本文件是"做什么"的操作手册。
> **违反本清单任一检查项 = 方法论违规 = 报告不合格。**

---

## 🚀 快速启动（首次使用）

```
1. 读 SKILL.md（工具用法 + 限流规则）
2. 读本文（CHECKLIST.md）← 你在这里
3. 开始调查
```

> ⚠️ 不需要先读其他11个reference文件。它们在需要时按需查阅。

---

## Phase 0：初始化（⏱ 约5-8分钟）

### 搜索执行

- [ ] **0a. 百科搜索**
  ```bash
  python3 scripts/investigate-v7.py "公司名" --baike
  ```
  - [ ] 读 baike.txt 全文 → 提取：全称/成立时间/总部/法人/注册资本/主营业务/股东

- [ ] **0b. 泛化搜索（2-3个query，覆盖基础面）**
  ```bash
  # query1: 身份确认（如果百科没搜到或信息不足）
  python3 scripts/investigate-v7.py "公司名" --query "公司名 全称 简介 主营"
  
  # query2: 联系方式（PIR-CONTACT专项）
  python3 scripts/investigate-v7.py "公司名" --query "公司名 联系方式 电话 邮箱 官网"
  
  # query3: 财务+规模（带时间锚定！）
  python3 scripts/investigate-v7.py "公司名" --query "公司名 营收 利润 2024 2025"
  ```
  - [ ] 每个搜索结果都 **cp q01.txt r0{序号}_{主题}.txt** （防覆盖）
  - [ ] 每个搜索结果都 **逐条阅读**（不是只看snippet）

### 初始化状态（⚠️ 必须产出 status.json）

- [ ] **0c. 写入初始 status.json**（模板见下方，复制后填充）

```json
{
  "_meta": {
    "target": "填目标企业全称",
    "created_at": "ISO时间",
    "updated_at": "ISO时间",
    "current_round": 0,
    "total_searches": 0,
    "total_raw_files": 0
  },
  "business_boundary": {
    "one_liner": "≤30字：这家公司干什么",
    "product_scope": "窄/中/广 + 核心品类",
    "customer": "卖给谁",
    "channel": "怎么卖",
    "profit_model": "怎么赚钱",
    "moat_assessment": "护城河是什么"
  },
  "seed_pool": {
    "seeds": [
      // 从百科+泛化搜索中提取的实体，每个一条
      // 至少5个种子才可进入Phase N
    ]
  },
  "pir": {
    "items": [
      {"id":"P-basis","q":"基础画像完整？","target":0.80,"current":0.0,"status":"pending"},
      {"id":"P-contact","q":"联系方式获取？","target":0.80,"current":0.0,"status":"pending"},
      {"id":"P-finance","q":"财务状况清晰？","target":0.75,"current":0.0,"status":"pending"},
      {"id":"P-competitor","q":"竞争格局明确？","target":0.70,"current":0.0,"status":"pending"},
      {"id":"P-capital","q":"资本关系完整？","target":0.70,"current":0.0,"status":"pending"},
      {"id":"P-risk","q":"风险识别充分？","target":0.70,"current":0.0,"status":"pending"}
    ],
    "summary": {"satisfied":0,"total":6}
  },
  "round_log": [],
  "convergence": {"is_converged":false}
}
```

**填写要求**：
- `business_boundary`：基于Phase 0数据填写，不知道的写"待确认"
- `seed_pool.seeds`：从已读的raw中提取实体（公司/人/关键词），至少5个
- `_meta.total_searches`：填实际执行的搜索次数
- `_meta.total_raw_files`：填raw目录下文件数

---

## Phase N：单轮迭代（⏱ 每轮约5-10分钟）

> **铁律：以下10步必须顺序执行，跳过任何一步=违规。**

### Step ① 读状态

- [ ] 读取 `data/{公司名}/status.json`
- [ ] 确认 `current_round` 值
- [ ] 查看 `seed_pool` 中 `explored=false` 的种子有哪些
- [ ] 查看 `pir` 中 `status!="satisfied"` 的项

### Step ② 回顾评估 + 决策

- [ ] 在脑中（或草稿纸）回答：
  - 上轮发现了什么新东西？
  - 哪个PIR置信度最低？→ **本轮重点方向**
  - 种子池里哪个未探索种子最有价值？
  - 有没有异常信号需要立即追查？
- [ ] **写出本轮计划**（1-2句话）：本轮重点方向 + 选中的种子 + 预期

### Step ③ 设计 Query + 搜索

**Query设计铁律（5条）**：

| # | 规则 | 检查 |
|---|------|------|
| Q1 | 单query ≤ 5关键词 | [ ] 本轮所有query均≤5词 |
| Q2 | 一query一问题 | [ ] 每个query只问一件事 |
| Q3 | 已知实体用精确名 | [ ] 用了具体公司名/人名而非泛词 |
| Q4 | 每轮 ≤ 6次搜索 | [ ] 本轮搜索次数≤6 |
| Q5 | 量化数据带时间锚定 | [ ] 含数字的query带年份/最新 |

**执行**：
```bash
python3 scripts/investigate-v7.py "公司名" --query "你的query"

# 立即保存！
cp data/{公司名}/raw/q01.txt data/{公司名}/raw/r{轮次}_{主题}.txt
```

### Step ⑤ 搜索质量自评（⭐ 读取结果后立即做）

- [ ] 结果质量判定：□ 高质量(≥7/10相关) □ 中质量(4-6) □ 低质量(≤3)
- [ ] 无关/噪音条目数：___ / 10
- [ ] 如果低质量 → 记录原因（太长? 词不准? 公开渠道无?）
- [ ] **低质量结果不加入种子池**（除非确实有有效新实体）

### Step ⑥ 分析整合（核心工作！）

- [ ] **逐条阅读**本次所有搜索结果的每一条（不是只看标题/snippet）
- [ ] 对每条判断：
  - [ ] 新实体？→ 准备加入种子池
  - [ ] 新关系？→ 记录
  - [ ] 验证/推翻已有信息？→ 标注
  - [ ] 量化数据？→ 记录数值+来源+期间
  - [ ] 噪音？→ 忽略但记录在round_log

### Step ⑦ 更新种子池

- [ ] 每个新实体 → 去重检查 → 新增 or 更新已有seed
- [ ] 本轮探索过的种子标记 `explored=true, explored_round=N`

### Step ⑧ 更新 PIR 置信度

- [ ] 对每个PIR项：本轮有新证据吗？
  - 有🟢直接数据 → +0.15~0.25
  - 有🟡推算数据 → +0.10~0.20
  - 有定性信息 → +0.05~0.10
  - 无 → 不变
- [ ] confidence ≥ target → status 改为 "satisfied"

### Step ⑨ 写回 status.json

- [ ] 更新：`_meta`(round/searches/files) + `seed_pool` + `pir` + `round_log`(追加)
- [ ] 写入文件

### Step ⑩ 收敛判断

- [ ] 逐一检查收敛条件：

| 条件 | 检查 | 通过？ |
|------|------|--------|
| C1 | 所有CRITICAL PIR satisfied? | [ ] 是/否 |
| C2 | 所有HIGH PIR satisfied/stalled? | [ ] 是/否 |
| C3 | 已执行最后验证轮? | [ ] 是/否 |
| C4 | 有效轮次 ≥ 6? | [ ] 是/否 (当前第N轮) |

- [ ] **全部通过** → 进入报告撰写
- [ ] **任一不通过** → 回到Step ①，开始下一轮
- [ ] 达到 **15轮** → 强制停止，生成阶段性报告

---

## 报告撰写前最终检查

- [ ] status.json 所有字段更新至最新轮
- [ ] confidence > 0.6 的种子全部 explored=true
- [ ] round_log 每轮都有 next_round_plan
- [ ] convergence.is_converged = true 且 reason 有据

---

## 🔥 常见违规速查（自查用）

| 违规行为 | 正确做法 |
|---------|---------|
| 搜完直接写报告 | 必须走完①-⑩，且C1-C4通过 |
| 不读raw就分析 | 逐条阅读每条搜索结果 |
| 不cp就覆盖q01.txt | 每次搜索后立即 cp rN_xxx.txt |
| query塞一堆关键词 | 拆成多个≤5词的精确query |
| "跑了6轮差不多了" | 只看PIR是否达标，不看轮次 |
| 种子池不维护 | 每轮必须新增/更新种子 |
| PIR一次性填完 | 每轮必须更新置信度 |
| 低质量搜索结果也提取 | 自评低质量则不加入种子池 |
| 量化数据不带年份 | 必须带2024/2025/最新等锚定词 |

---

---

## 📖 Round 1 完整示范（以"特来电"为例）

> 以下展示严格按CHECKLIST执行的一轮完整迭代是什么样子的。
> **这是你执行调查时的参照物。**

### 前置条件
- Phase 0 已完成：百科搜到 → 泛化搜索3轮完成 → status.json已写入（Round 0）
- status.json显示：current_round=0，所有PIR current=0.0~0.2

---

### Step ① 读状态

```
读取 status.json → current_round=0 → 下轮是Round 1
PIR缺口：P-basis(0.2) P-contact(0.1) P-finance(0.0) P-competitor(0.0) P-capital(0.0) P-risk(0.0)
种子池：8个种子（特锐德/于德翔/郭永光/星星充电/国调基金/充电桩/宁德时代/青岛）
未探索：全部8个
```

### Step ② 回顾评估 + 决策

```
上轮(Phase 0)发现：
  - 确认公司全称：特来电新能源股份有限公司
  - 母公司特锐德(300001.SZ)控股78.96%
  - 2024年首次盈利，营收48.91亿
  - 联系方式仅获官网URL，缺电话/邮箱
  
本轮决策：
  重点方向：财务深挖（P-finance=0 最低）+ 联系方式补强（P-contact=0.1）
  选种：直接搜索（不选特定种子，用精确query获取量化数据）
  预期：获得2024-2025完整财务数据 + 销售联系方式
```

### Step ③ 设计 Query + 搜索

```
Query设计（每轮≤6次，每个≤5词，量化数据带年份）：

  Q1: "特来电 营收 利润 2024 2025"     ← P-finance，带时间锚定 ✅
  Q2: "特来电 联系电话 销售 邮箱"       ← P-contact，精确 ✅  
  Q3: "特来电 市场份额 充电量 2025"     ← P-finance+P-competitor ✅
```

执行：
```bash
# Q1
python3 scripts/investigate-v7.py "特来电" --query "特来电 营收 利润 2024 2025"
cp data/特来电/raw/q01.txt data/特来电/raw/r01_finance.txt   # ✅ 立即cp

# Q2  
python3 scripts/investigate-v7.py "特来电" --query "特来电 联系电话 销售 邮箱"
cp data/特来电/raw/q01.txt data/特来电/raw/r01_contact.txt    # ✅ 立即cp

# Q3
python3 scripts/investigate-v7.py "特来电" --query "特来电 市场份额 充电量 2025"
cp data/特来电/raw/q01.txt data/特来电/raw/r01_market.txt     # ✅ 立即cp
```

### Step ⑤ 搜索质量自评

```
Q1(r01_finance):  ⭐ 高质量(9/10相关)
  - 第1条：特锐德2025年报数据（157.86亿营收/12.43亿净利）
  - 第2条：华通集团投资新闻（含特来电90万台/24%市占率/196亿度充电量）
  - 第3条：五一充电分析（行业背景）
  → 直接进入Step ⑥分析

Q2(r01_contact):  ⭐ 高质量(8/10相关)
  - 第1条：官网联系页（黄洪勇18883222938/huanghy@teld.cn 等3个销售）
  - 第2条：官网首页（400热线/总机0532-89083366）
  - 第7条：爱企查（总部详细地址+邮编）
  → 直接进入Step ⑥分析

Q3(r01_market):  ⭐ 高质量(8/10相关)
  - 第1条：充电联盟排名数据
  - 第5条：2025年8月TOP5运营商市占率
  → 直接进入Step ⑥分析

无关噪音：0条 | 需要重搜：否
```

### Step ⑥ 分析整合（逐条阅读示例）

```
=== r01_finance.txt 逐条分析 ===

[1] 特锐德2025年报：营收157.86亿(+2.68%)，净利12.43亿(+35.62%)
  → 新实体：无 | 新关系：确认特来电为特锐德子公司
  → 量化数据：特锐德集团层面（非特来电单独），记录但标注口径差异
  → 验证：与Phase 0信息一致

[2] 华通集团投资新闻（2026-05-06，⭐最新！🟢）：
  → 量化数据：特来电运营公共终端约90万，直流54.2万，市占率~24%，第1
  → 量化数据：2025年充电量约196亿度，市占率~23%，第1
  → 量化数据：累计充电量逼近590亿度，注册用户突破5300万
  → 新实体：华通创投/华资盛通基金（投资方种子 s009）
  → 关键发现：IPO进展——"已进入上市辅导阶段"

[3-10] ... (逐条分析，此处省略但实际必须逐条读)

=== r01_contact.txt 逐条分析 ===

[1] 官网联系页：
  → 量化数据：3个销售人员直联（手机+邮箱）
  → 联系方式：黄洪勇/杨成/秦丽萍 + 400热线 + 总机
  → PIR-CONTACT 大幅提升

[2] 官网首页：实时数据面板
  → 量化数据：总充电量/终端数/覆盖城市/碳减排（实时变化，仅供参考）

... (逐条继续)
```

### Step ⑦ 更新种子池

```
新增种子：
  s009: 华通创投/华资盛通基金 [company] source=r01_finance conf=0.6 dim=[capital]
  s010: 充电联盟 [organization] source=r01_market conf=0.7 dim=[competitor]
  
更新已有种子：
  s001(特锐德): confidence 0.5→0.6 (新来源验证) + dimension追加[finance]
  s003(于德翔): explored=true, explored_round=1 (本轮未专门探索于德翔，保持false)

标记已探索：
  本轮是定向搜索（非种子驱动），无需标记seed explored
```

### Step ⑧ 更新 PIR

```
P-basis:  0.2 → 0.25 (+0.05, 定性补充)
P-contact: 0.1 → 0.75 (+0.65, 🟢获电话x3/邮箱x4/地址详细) ⭐大幅提升
P-finance: 0.0 → 0.55 (+0.55, 🟢获2025核心经营数据) ⭐大幅提升
P-competitor: 0.0 → 0.20 (+0.20, 获TOP5排名数据)
P-capital: 0.0 → 0.10 (+0.10, 发现华通基金)
P-risk: 0.0 → 0.00 (本轮未涉及)

satisfied: 0 | total: 6
→ 未收敛，最低项 P-risk=0 / P-capital=0.1
```

### Step ⑨ 写回 status.json

```json
{
  "_meta": {"current_round": 1, "total_searches": 3+3=6, "total_raw_files": 9},
  "pir": { /* 更新后置信度如上 */ },
  "round_log": [{
    "round": 1,
    "focus": "财务深挖+联系方式补强",
    "searches": ["r01_finance", "r01_contact", "r01_market"],
    "quality": ["高(9/10)", "高(8/10)", "高(8/10)"],
    "new_seeds": ["s009华通创投", "s010充电联盟"],
    "key_findings": [
      "2025年特来电90万终端/24%市占率/196亿度充电量(🟢华通新闻2026-05)",
      "获3个销售直联+400+总机+详细地址(P-contact跃升至0.75)",
      "已进入上市辅导阶段"
    ],
    "next_round_plan": "资本结构深挖(P-capital=0.1)+竞争对手L1(P-competitor=0.2)",
    "convergence_assessment": "未收敛——P-risk=0/P-capital=0.1严重不足，需≥6轮"
  }],
  "seed_pool": { /* 更新后 */ }
}
```

写入 `data/特来电/status.json` ✅

### Step ⑩ 收敛判断

| 条件 | 结果 |
|------|------|
| C1 CRITICAL全部satisfied? | ❌ P-basis(0.25)<0.80, P-contact(0.75)<0.80 |
| C2 HIGH全部satisfied/stalled? | ❌ P-finance(0.55), P-competitor(0.20), P-capital(0.10), P-risk(0) |
| C3 最后验证轮? | ❌ 尚未做 |
| C4 轮次≥6? | ❌ 当前第1轮 |

**结论：未收敛 → 回到Step ①，开始Round 2**

---

> **示范要点总结**：
> 1. 每步都有明确输出（不是脑中想想要了就过）
> 2. 搜索质量有自评（不是默认都高质量）
> 3. 逐条阅读raw（不是只看前3条snippet）
> 4. 种子池真正增删改（不是摆设）
> 5. PIR有具体数值变动（不是最后一次性填）
> 6. round_log有实质内容（证明思考过方向选择）
> 7. 收敛判断逐项检查（不是拍脑袋说"差不多了"）

---

*本文件 v10 与 methodology.md v9.5 完全对齐，是其可执行版本。*
*方法论细节变更时同步更新本文。*
