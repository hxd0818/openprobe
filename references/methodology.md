# 螺旋迭代与种子扩散方法论 ⭐ v9.5

> **⚠️ v10 执行入口变更**：本文是方法论的**完整论文版**（含原理、schema细节、设计 rationale）。
> **如果你要执行调查，请先读 `CHECKLIST.md`**——它是本文的可执行浓缩版。
> 本文件在以下场景查阅：需要理解"为什么这样设计"、遇到复杂情况需参考完整schema、或CHECKLIST未覆盖的边界场景。

> **v9.4 核心变革**：将"螺旋迭代+种子扩散"从概念描述升级为**强制执行的状态机**。
> 
> **v9.5 核心变革**：新增**数据时效性强制门槛**（见 `data-quality-gate.md` §2.5）——
> 所有量化数据搜索必须带时间锚定，优先获取上年度最新数据，
> 旧数据必须先穷尽最新数据搜索努力才可降级使用，且PIR置信度自动施加时效折扣。
>
> **核心原则**：脚本只负责搜索。实体提取、去重、种子池更新、选种、收敛判断——**全部是 Agent 的工作**。
> 
> `status.json` 是迭代的**唯一状态真相源（Single Source of Truth）**。
> Agent 每轮迭代**必须**按顺序完成：读状态 → 选种 → 搜索 → 提取 → 更新状态 → 收敛判断。

---

## 目录

1. [状态机总览](#1-状态机总览)
2. [status.json 强制 Schema](#2-status-json-强制-schema)
3. [Phase 0：初始化](#3-phase-0初始化)
4. [Phase N：单轮迭代五步法](#4-phase-n单轮迭代五步法)
5. [收敛判断](#5-收敛判断)
6. [四大维度导航](#6-四大维度导航)
7. [行业自适应](#7-行业自适应)

> **种子池管理与实体分层策略**已独立为 `references/entity-tier-strategy.md`。
> 含：种子生命周期/选种策略/扩散模式 + **Tier 1/2/3 分层处理规则**（v9.5新增）。

---

---

## 1. 状态机总览

```
                    ┌─────────────────────┐
                    │   Phase 0: 初始化     │
                    │  百科 + 泛化搜索(3)   │
                    │  → 写入 status.json  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Phase N: 迭代循环    │
                    │                      │
                    │  ① 读 status.json     │
                    │  ② 回顾上轮 + 评估缺口 │
                    │  ③ 从种子池选种       │
                    │  ④ 设计 query         │
                    │  ⑤ 调用脚本搜索        │
                    │  ⑥ 提取新实体/关系    │
                    │  ⑦ 去重 + 归入种子池   │
                    │  ⑧ 更新 PIR 置信度    │
                    │  ⑨ 写回 status.json   │
                    │  ⑩ 收敛判断           │
                    │     ├─ 未收敛 → 回到①  │
                    │     └─ 收敛 → 写报告   │
                    └──────────────────────┘
```

**铁律：步骤①-⑩，缺一不可。每轮必须产出更新的 status.json。**

---

## 2. status.json 强制 Schema

> 这是调查过程的**唯一状态文件**。Agent 必须在 Phase 0 结束时创建它，并在每轮结束时更新它。
> 报告生成后，status.json 作为调查过程审计轨迹保留。

```json
{
  "_meta": {
    "target": "目标企业全称",
    "skill_version": "v9.4",
    "created_at": "ISO时间戳",
    "updated_at": "ISO时间戳",
    "current_round": 0,
    "total_searches": 0,
    "total_raw_files": 0
  },

  "business_boundary": {
    "one_liner": "≤30字商业本质描述",
    "product_scope": "窄/中/广 + 核心品类",
    "customer": "客群画像",
    "channel": "主力渠道",
    "profit_model": "盈利模式",
    "moat_assessment": "护城河判断"
  },

  "seed_pool": {
    "stats": {
      "total_seeds": 0,
      "explored_count": 0,
      "unexplored_count": 0,
      "by_type": {"company": 0, "person": 0, "keyword": 0}
    },
    "seeds": [
      {
        "id": "s001",
        "name": "实体名称",
        "type": "company | person | product | keyword",
        "source_round": 0,
        "source_file": "baike.txt / r1_xxx.txt",
        "confidence": 0.4,
        "dimensions": ["competitor", "supply_chain"],
        "explored": false,
        "explored_round": null,
        "discoveries": [],
        "notes": ""
      }
    ]
  },

  "pir": {
    "items": [
      {
        "id": "P-basis",
        "layer": 1,
        "question": "企业基础画像是否完整？",
        "target_confidence": 0.80,
        "current_confidence": 0.0,
        "status": "pending",
        "evidence_summary": "",
        "gaps": []
      }
    ],
    "summary": {
      "satisfied": 0,
      "total": 5,
      "blocked_by": []
    }
  },

  "round_log": [
    {
      "round": 0,
      "phase": "init",
      "searches_performed": ["baike", "q_financial", "q_capital", "q_competitor"],
      "new_seeds_found": 12,
      "seeds_explored": [],
      "key_findings": ["发现X", "确认Y"],
      "next_round_plan": "针对竞对维度深挖",
      "convergence_assessment": "未收敛——PIR竞争维度仅0.3"
    }
  ],

  "convergence": {
    "is_converged": false,
    "final_round": null,
    "reason": "",
    "quality_gate_pass": false,
    "unmet_conditions": []
  }
}
```

### 字段使用规则

| 字段 | 谁写 | 何时写 | 用途 |
|------|------|--------|------|
| `_meta` | Agent | 创建+每轮更新 | 调查元数据 |
| `business_boundary` | Agent | Phase 0 完成后写一次 | 锚定调查范围 |
| `seed_pool` | Agent | **每轮必须更新** | 种子管理的核心 |
| `pir` | Agent | **每轮必须更新** | 收敛驱动的核心 |
| `round_log` | Agent | **每轮追加一条** | 审计轨迹+可复现性 |
| `convergence` | Agent | 每轮评估+最终判定 | 收敛决策记录 |

---

## 3. Phase 0：初始化

### 3.1 执行

```bash
# 1. 百科查询（必做）
python3 scripts/investigate-v7.py "公司名" --baike

# 2. 泛化搜索（2-3个query，覆盖基础面）
python3 scripts/investigate-v7.py "公司名" --query "主营业务 简介 营收"
python3 scripts/investigate-v7.py "公司名" --query "融资 股东 控股股东 创始人"
python3 scripts/investigate-v7.py "公司名" --query "竞争对手 行业地位 最新动态"
```

### 3.2 初始化后必须完成的动作（⚠️ 不是可选项）

**动作1：提取初始种子**
- 从百科和泛化搜索结果中**逐条阅读**，提取所有实体
- 每个实体 → 一条 seed 记录
- 初始置信度设为 0.3-0.5（来源越权威越高）
- 标注所属维度（一个种子可属于多个维度）

**动作2：写 business_boundary**
- 基于 Phase 0 数据，填写商业边界五问
- 这决定了后续所有维度的调查方向
- **写入 status.json**

**动作3：实例化 PIR**
- Layer 1（基线）5个问题自动激活
- 根据 business_boundary 追加 Layer 2 问题
- 如用户有特别关注点 → Layer 0
- **全部写入 status.json.pir**

**动作4：创建初始 status.json**
- 合并以上所有内容
- 写入 `data/{公司名}/status.json`
- **这是后续所有迭代的基础**

---

## 4. Phase N：单轮迭代五步法

> ⚠️ 每一步都必须执行。跳过任何一步 = 违反方法论。

### Step ①：读取状态

```
读取 data/{公司名}/status.json
→ 确认 current_round
→ 查看 seed_pool 中 explored=false 的种子
→ 查看 pir 中 status!="satisfied" 的项
→ 查看上一轮 round_log 的 next_round_plan
```

### Step ②：回顾评估 + 决策

回答以下问题并**记录在本轮 round_log 中**：

```
□ 上轮搜索发现了什么？（新实体？新关系？矛盾数据？）
□ 各 PIR 当前置信度？哪个最低？
□ 种子池健康度？有多少高置信度未探索种子？
□ 是否有异常信号需要立即追查？
□ 本轮重点方向是什么？（必须明确写出）
```

**决策输出**：本轮重点方向 + 选中的种子列表 + 每个 seed 对应的 query 思路

### Step ③：设计 Query + 执行搜索 ⭐ v9.5 新增规范

> **v9.5 核心变革**：新增 Query 设计铁律和搜索质量自评机制。
> Agent 必须知道自己使用的是搜索引擎，并遵循搜索引擎的工作原理设计 query。
> **⭐v9.5 进一步强化**：所有量化数据搜索 **必须带时间锚定**（见 `data-quality-gate.md` §2.5.B），违反"最新优先"铁律 = 方法论违规。

#### Query 设计铁律（5条，v9.5从4条升级）

| # | 铁律 | 原因 | 违规处理 |
|---|------|------|---------|
| **Q1** | 单个 query **≤ 5 个关键词**（含实体名） | 搜索引擎对多关键词会稀释权重，返回"所有词的折中"，哪个问题都答不好 | 必须**拆分为多个搜索**，每个 ≤5 词 |
| **Q2** | 一个 query **只回答一个明确的问题** | 混合多个问题 = 所有问题的答案都是半成品 | 按"一个问题一次搜索"拆分 |
| **Q3** | **已知实体名 → 精确搜索**；**未知方向 → 泛化搜索** | 精确搜索命中率高；泛化搜索用于发现新实体 | 已知实体时必须用精确名称+具体维度词 |
| **Q4** | **每轮搜索总数 3-6 个**（非 query 数，是实际调用脚本次数） | 质量 > 数量。每次搜索都要读取和分析，多了Agent处理不过来 | 超过6个说明本轮方向太散，应聚焦 |
| **Q5** ⭐ | **量化数据搜索必须带时间锚定**（年份/最新/年报） | 无时间锚定的搜索倾向返回高流量旧内容（旧招股书/旧新闻），导致使用过期数据 | **必须补搜带年份的query**；详见 `data-quality-gate.md` §2.5.B |

#### Query 设计模板（参考）

```
✅ 好的 query 设计（每个回答一个明确问题 + ⭐带时间锚定）：

  精确搜索（已知实体）：
    "{实体名} {具体维度} {时间}"          例: "滔搏 2024 2025 营收 利润"
    "{实体名} {关系类型} {对方实体}"        例: "叶国富 WOW COLOUR 控股 关系"
    "{事件} {地点} 时间线"                例: "KKV 卓悦中心 闭店 纠纷 2025 2026"

  泛化搜索（未知/发现型）：
    "{行业} 排名 榜单 {年份}"              例: "潮流零售 排名 CCFA 2024"
    "{赛道} 新兴品牌 玩家"                例: "美妆集合店 新兴品牌 国潮"
    "{公司名} 风险 诉讼 处罚"             例: "KK集团 税务 处罚 违法"

  ⭐ 量化数据必须带时间锚定（v9.5 强制）：
    "KK集团 营收 2025"                    ✅ 直接搜最新年
    "KK集团 营收 2024"                     ✅ 回溯一年
    "名创优品 门店数 2025"                 ✅ 同期对比数据
    "泛联信息 最新 年报 财报"              ✅ "最新"作为兜底锚定词

❌ 不好的 query 设计（违反铁律的典型错误）：

  "吴悦宁 陈世欣 郭惠波 高管团队 履历 背景 教育"
  → 违反 Q1(7个词) + Q2(混合4个人的履历)
  → 应拆为: "吴悦宁 履历 背景 教育" / "陈世欣 法定代表人 关联企业"

  "喜燃 番茄口袋 三福 酷乐潮玩 九木杂物社 52TOYS 营收 门店"
  → 违反 Q1(10+词) + Q2(混合8个竞对的财务)
  → 应拆为: 先搜"潮流集合店 竞争对手 排名"发现玩家，再逐个精确搜索

  ⭐ v9.5 新增违规类型：
  "KK集团 营收 利润 毛利率"              → 违反 Q5（无时间锚定！）
  → 应为: "KK集团 营收 2025" / "KK集团 营收 2024"
  
  "泛联信息 团队规模 员工"               → 违反 Q5（无时间锚定！）
  → 应为: "泛联信息 员工人数 2025"
```

#### 执行搜索

```
调用脚本（每次一个 query）：
python3 scripts/investigate-v7.py "公司名" --query "q1"

保存结果（必须 cp q01.txt r{N}_{topic}.txt 防覆盖）
```

### Step ③⑤：搜索质量自评 ⭐（新增步骤，在读取结果后、分析整合前执行）

> **为什么需要**：Agent 必须判断"这次搜索好不好"，而不是机械地提取所有内容。
> 低质量搜索不重做 = 种子池被噪音污染 = PIR 虚高。

```
每次读取搜索结果后，在写入 round_log 前必须完成：

┌─ 结果质量自评 ───────────────────────────────┐
│                                              │
│  本轮搜索意图: _________________________       │
│                                              │
│  □ 高质量（≥7/10 条目与查询高度相关）         │
│     → 直接进入 Step ④ 分析整合              │
│                                              │
│  □ 中质量（4-6/10 相关，但信息密度不足）       │
│     → 仍可提取，但在 round_log 中标注           │
│     → 考虑下一轮用更精准的 query 补充          │
│                                              │
│  □ 低质量（≤3/10 相关，大量无关/重复/噪音）     │
│     → 在 round_log 中记录失败原因:            │
│       □ query 太长(>5词)？→ 下轮拆分重搜      │
│       □ 关键词不准确？→ 换同义词/换角度重搜    │
│       □ 该信息不在公开渠道？→ 声明 stalled    │
│       □ 搜索引擎对该主题覆盖差？→ 换引擎/换源   │
│     → **不将低质量结果中的实体加入种子池**      │
│       （除非某条结果确实包含有效新实体）        │
│                                              │
│  无关/噪音条目数: ___ / 10                  │
│  是否需要针对同一问题重新搜索: □ 是 □ 否      │
│                                              │
└──────────────────────────────────────────────┘
```

### Step ④：分析整合 — **这是 Agent 核心工作**

```
逐条阅读搜索结果：

对每条结果：
  ├─ 是否包含新的实体（公司/人/产品）？
  │   └─ 是 → 准备加入种子池（Step ⑤处理）
  ├─ 是否包含新的关系（投资/任职/合作/诉讼）？
  │   └─ 是 → 记录关系，准备更新对应维度JSON
  ├─ 是否验证或推翻了已有信息？
  │   └─ 是 → 更新对应种子的 confidence
  ├─ 是否包含量化数据？
  │   └─ 是 → 记录数值+来源+数据期间（遵守 analyst-identity.md 铁律5）
  └─ 是否是噪音/无关？
      └─ 是 → 忽略，但记录在 round_log 中（证明读过）
```

### Step ⑤：更新种子池 — **去重 + 归入**

```
对每个新发现的实体：
  
  1. 去重检查：seed_pool 中是否已有同名实体？
     ├─ 有（完全同名）→ 不新增，改为：
     │   ├── 追加 source_round 和 source_file
     │   ├── 提升 confidence（+0.1~0.2，多源发现提升更多）
     │   └── 追加 dimensions（如果有新维度标签）
     │
     └─ 无 → 新增一条 seed 记录：
         {
           "id": "s{序号}",
           "name": "新实体名",
           "type": "company/person/product/keyword",
           "source_round": N,
           "source_file": "rN_xxx.txt",
           "confidence": 0.3,  // 新种子初始值
           "dimensions": ["根据内容判断"],
           "explored": false,
           "explored_round": null,
           "discoveries": [],
           "notes": "从哪条搜索结果的哪个位置发现的"
         }

  2. 将本轮探索过的种子标记 explored=true, explored_round=N
```

### Step ⑥：更新 PIR 置信度 ⭐v9.5 加入时效/推算等级折扣

```
对每个 PIR item：
  本轮是否有新证据支持该问题？
  ├─ 是且有🟢/🟡直接数据 → raw_confidence += 0.15~0.25（不超过1.0）
  │   └─ 最终 confidence = raw_confidence × 1.00(🟢) 或 ×0.95(🟡)
  ├─ 是且有~推算数据 → raw_confidence += 0.10~0.20（不超过1.0）
  │   └─ 最终 confidence = raw_confidence × 推算等级系数
  │       ~碎片推算(Level 2) → ×0.85
  │       ~旧数据推算(Level 3) → ×0.65
  │   （详见 `data-quality-gate.md` §2.5.C）
  ├─ 是但只有定性信息 → confidence += 0.05~0.10（无折扣，定性不受时效影响）
  ├─ 否（本轮无相关发现）→ 不变
  └─ 发现反面证据 → 降低 confidence 并记录
  
  if confidence ≥ target_confidence → status = "satisfied"
  if 连续3轮该 PIR 无提升 → status = "stalled"，记录原因
```

### Step ⑦：写回 status.json

```
更新以下字段：
  _meta.updated_at / current_round / total_searches / total_raw_files
  seed_pool（新增/更新种子）
  pir（更新置信度和状态）
  round_log（追加本轮记录）
  convergence（重新评估）
  
写入 data/{公司名}/status.json
```

### Step ⑧：收敛判断

见第6节。如果未收敛 → 回到 Step ①。

---

## 5. 收敛判断

### 6.1 收敛前置条件（必须全部满足）

| # | 条件 | 检查方法 |
|---|------|---------|
| C1 | 所有 CRITICAL PIR ∈ {satisfied, n/a} | 读 pir.items |
| C2 | 所有 HIGH PIR ∈ {satisfied, stalled, abandoned, n/a} | 读 pir.items |
| C3 | 已执行"最后验证轮"（针对最低置信度PIR的专项搜索） | 检查 round_log |
| **C4** | **有效轮次 ≥ 6**（⭐v9.5从4上调：轮次是下限护栏，不是收敛目标） | 检查 _meta.current_round |
| **C5** | **entity_pool 已同步**（⭐v9.5新增） | 各维度JSON中的实体已全部回写 entity_pool，无遗漏 |

### 6.2 安全阀

| 触发条件 | 动作 |
|---------|------|
| 达到 **15轮** 仍未收敛 | **强制暂停**，生成阶段性报告，标注未满足的 PIR |

> **⭐v9.5 核心原则重申**：收敛的唯一依据是 **PIR 是否达标**。
> 轮次的作用纯粹是**护栏**——C4 是"别太早停"，安全阀是"别无限跑"。
> **禁止**出现"已跑N轮，差不多了"这种以轮次为理由的收敛决策。
| 连续 **3轮无效**（无新实体/无PIR提升） | 进入收敛评估，考虑声明 stalled 或换策略 |
| **种子池枯竭**（unexplored < 3 且泛化搜索也无新种子） | 声明信息饱和，标注信息缺口 |

### 6.3 收敛时的最终检查清单

```
□ status.json 所有字段已更新至最新一轮
□ seed_pool 中 confidence > 0.6 的种子全部 explored=true
□ pir.summary.satisfied / pir.summary.total 的比值可接受
□ round_log 中每轮都有清晰的 next_round_plan（证明有规划非盲目）
□ convergence.is_converged = true 且 reason 有据可查
□ **entity_pool 完整性**（⭐v9.5）：各维度JSON实体数去重后 ≈ entity_pool条数（偏差≤15%）
```

---

## 6. 四大维度导航

> 各维度的详细推理框架见对应的 reference 文件。
> 此处仅说明维度与种子池/PIR的关系。

| 维度 | 详细方法论文档 | 对应的 PIR 典型问题 | 典型种子类型 |
|------|---------------|-------------------|------------|
| 竞争对手 | `competitor-research.md` v9.3 | "竞对图谱是否完整？L1是否全覆盖？" | company(竞对), keyword(赛道) |
| 产业链 | `supply-chain.md` v9.2 | "供应链关键节点是否已识别？" | company(供应商/客户), keyword(渠道) |
| 资本关系 | `capital-research.md` v9.2 | "控制链和融资链是否完整？" | company(股东/被投), person(实控人/高管) |
| 关键人物 | `people-research.md` v9.2 | "决策者画像是否完整？" | person(创始人/CEO/董事) |

**维度交叉**：当一个种子同时属于多个维度（如"叶国富"既是竞对CEO又是资本方），在 dimensions 数组中标注全部适用维度。探索该种子时，可同时更新多个维度的 PIR。

---

## 7. 行业自适应

Agent 应在 Phase 0 的 business_phase 中自行判断行业类型，据此调整：
- 哪些 PIR 需要提升 target_confidence（G端企业的资本维度可能更重要）
- 哪些发现工具更有效（已在各维度 reference 文件的工具箱中说明）
- 信息缺口在哪（不同行业的 OSINT 信息源差异巨大）

具体思考框架见 `supply-chain.md` v9.2 §7 和 `competitor-research.md` v9.3 的 Step 1 商业边界定义。

---

*本文件 v9.4 将螺旋迭代从"概念"升级为"强制状态机"。*
*v9.5 新增数据时效性强制门槛（§2.5），Query设计铁律从4条升级为5条，PIR置信度纳入时效折扣。*
**种子池管理与实体分层策略见 `entity-tier-strategy.md`（v9.5）。**
