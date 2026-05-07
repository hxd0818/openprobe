# 产出物 JSON 格式规范与数据沉淀

> 本文件定义所有调查产出的 **JSON 数据格式**、目录结构、命名规范和数据复用机制。
> **报告撰写标准与自检清单**见 `references/report-writing-guide.md`（§11 全部内容已迁移）。

---

## 目录

1. [目录结构](#1-目录结构)
2. [status.json — 调查状态中枢](#2-statusjson-–-调查状态中枢)
3. [profile.json — 目标企业画像](#3-profilejson-–-目标企业画像)
4. [entity_pool.json — 实体主索引](#4-entity_pooljson-–-实体主索引)
5. [competitors.json — 竞争格局](#5-competitorsjson-–-竞争格局)
6. [supply_chain.json — 产业链上下游](#6-supply_chainjson-–-产业链上下游)
7. [capital_graph.json — 资本关系图谱](#7-capital_graphjson-–-资本关系图谱)
8. [round_logs/ — 轮次日志](#8-round_logs-–-轮次日志)
9. [raw/ — 原始数据](#9-raw-–-原始数据)
10. [数据复用机制](#10-数据复用机制)

---

## 1. 目录结构

```
data/{公司名}/
├── raw/                           # 原始搜索数据（脚本自动生成）
│   ├── q01.txt / q02.txt / ...    # 每个query一个文件
│   ├── baike.txt                  # 百科结果
│   └── u01.txt / ...              # URL抓取结果
├── status.json                    # ⭐ 调查状态中枢（Agent维护）
├── profile.json                   # ⭐ 目标企业画像
├── entity_pool.json               # ⭐ 实体主索引
├── competitors.json               # ⭐ 竞争格局分析
├── supply_chain.json              # ⭐ 产业链上下游
├── capital_graph.json             # ⭐ 资本关系图谱
├── round_logs/                    # ⭐ 轮次日志
│   └── round_N.json               # 每轮一个文件
├── report.md                      # Markdown报告（Agent撰写）
├── report.pdf                     # PDF报告（gen_pdf.py生成）
```

## 2. status.json — 调查状态中枢

Agent 每轮迭代后更新此文件，是断点续跑的核心入口。

```json
{
  "company": "目标公司名",
  "version": "v8",
  "started_at": "2026-04-05T10:00:00+08:00",
  "updated_at": "2026-04-05T11:30:00+08:00",
  "company_type": "G端服务",
  "rounds_completed": 3,
  "max_rounds": 8,
  "convergence": {
    "is_converged": false,
    "reason": null,
    "stale_rounds": 0,
    "max_stale_allowed": 2
  },
  "dimension_confidence": {
    "competitor": {"score": 0.65, "note": "L1竞对2家待深挖"},
    "supply_chain": {"score": 0.75, "note": "下游较完整，上游缺供应商"},
    "capital": {"score": 0.40, "note": "仅完成股权链向上追踪"}
  },
  "seed_pool_snapshot": {
    "total_seeds": 28,
    "explored": 15,
    "unexplored_high_conf": 5,
    "top_unexplored": ["种子A", "种子B"]
  },
  "next_round_suggestions": {
    "focus": ["capital", "competitor_L1_deep"],
    "reason": "资本维度置信度最低(0.4)，竞对L1需补充第3家",
    "suggested_queries": [
      "{公司名} 战略投资 并购 收购了",
      "竞对C 公司 融资 产品 客户"
    ]
  },
  "milestones": {
    "seed_init": {"done": true, "at": "...", "output": "profile.json"},
    "round_1": {"done": true, "at": "...", "queries": 5, "new_entities": 12},
    "round_2": {"done": true, "at": "...", "queries": 8, "new_entities": 7},
    "round_3": {"done": true, "at": "...", "queries": 4, "new_entities": 0},
    "final_report": {"done": false, "at": null}
  },
  "search_stats": {
    "total_queries": 17,
    "raw_files": 19,
    "total_results_est": 450
  },
  "data_quality_summary": {
    "generated_at": "2026-04-07T00:00:00+08:00",
    "total_data_points": 42,
    "currency_distribution": {
      "fresh": 28,
      "current": 10,
      "stale": 3,
      "obsolete": 1,
      "static_na": 5
    },
    "estimation_distribution": {
      "direct_fresh": 28,
      "direct_current": 10,
      "fragment_estimated": 3,     // Level 2 碎片推算
      "legacy_estimated": 1         // Level 3 旧数据推算
    },
    "gap_items": [
      {
        "field": "market_share_2025",
        "importance": "auxiliary",
        "attempts_made": ["'泛联信息 市场份额'", "'分布式存储 市场格局 泛联'", "'UBIX market share'"],
        "resolution": "impact_assessment",
        "impact_note": "不影响核心竞争格局定性判断",
        "pir_affected": null
      }
    ],
    "quality_grade": "PASS"  // PASS / RESTRICTED / FAIL
  },
  "notes": "第三轮无新实体，stale_rounds=1，再一轮无新实体则收敛"
}
```

**关键字段说明**：
- `convergence` — 收敛状态机
- `dimension_confidence` — 三维置信度（驱动下一轮决策）
- `seed_pool_snapshot` — 种子池快照（指导种子选择）
- `next_round_suggestions` — Agent留给"自己"的备忘录

## 3. profile.json — 目标企业画像

Phase 0 初始化后创建，后续轮次持续更新。

```json
{
  "company_full_name": "法定全称",
  "aliases": ["简称", "曾用名"],
  "industry": "所属行业",
  "core_business": ["核心业务1", "核心业务2"],
  "products_services": [
    {
      "name": "产品/服务名",
      "description": "做什么的",
      "target_customer": "卖给谁"
    }
  ],
  "customer_type": "G端/B端/C端/混合",
  "revenue_model": "项目制/订阅制/产品销售/混合",
  "company_type": "G端服务|制造业|SaaS互联网|零售消费|金融|医药生物|地产建筑|其他",
  "business_model": "B2G|B2B|B2C|B2B2C|平台型|产品型|服务型",
  "scale": {
    "revenue": "约X亿",
    "employees": "约X人"
  },
  "key_facts": {
    "legal_rep": "法人代表",
    "founded": "成立时间",
    "stock_code": "股票代码",
    "shareholders": ["主要股东"],
    "headquarters": "总部地址（详细到省市区街道门牌）",
    "main_domain": "主域名/官网URL"
  },
  "contact_info": {
    "phone": {"general": "总机/客服电话", "hotline": "服务热线(如有)", "fax": "传真号码"},
    "email": {"general": "公开邮箱(如info@/contact@)", "business": "商务合作邮箱", "hr": "招聘邮箱", "media": "媒体/PR联系邮箱"},
    "address": {"hq": "总部详细地址", "branches": [{"city": "城市", "address": "分公司/办事处地址"}]},
    "website": {"official": "官网URL", "recruit": "招聘页面URL", "news": "新闻中心/媒体入口URL"},
    "social_media": {"wechat": "微信公众号名称", "weibo": "微博官方账号", "douyin": "抖音号", "linkedin": "领英主页", "xiaohongshu": "小红书号"},
    "customer_service": {"platform": "在线客服平台(如微信公众号/APP内)", "worktime": "客服工作时间"},
    "investor_relations": {"phone": "投资者关系电话", "email": "IR邮箱", "page": "IR专栏URL(上市公司)"},
    "other_channels": ["其他公开联系方式"]
  },
  "confidence": 85,
  "last_updated": "2026-04-05T10:30:00+08:00"
}
```

## 4. entity_pool.json — 实体主索引

所有发现的实体的统一索引，是各维度JSON的数据源。

```json
{
  "entities": [
    {
      "id": "ent_001",
      "name": "实体名称",
      "normalized_name": "规范全称",
      "aliases": ["别名1"],
      "type": "company|person|product|organization",
      "directions": {
        "primary": "competitor|upstream|downstream|lateral|capital_related",
        "secondary": ["supply_chain_upstream"],
        "confidence": 0.85
      },
      "evidence": [
        {
          "source": "bidding_ccgp|news_annual_report|equity_officer|search_generic|baike",
          "source_detail": "具体来源描述",
          "found_at_round": 1,
          "confidence_contribution": 0.3
        }
      ],
      "source_count": 3,
      "confidence": 0.8,
      "is_competitor": true,
      "competitor_tier": "L1|L2|L3|L4|null",
      "dimensions_active": ["competitor", "supply_chain"],
      "mention_count": 5,
      "first_seen_round": 1,
      "last_updated_round": 3,
      "notes": "备注"
    }
  ],
  "summary": {
    "total_unique": 28,
    "by_type": {"company": 22, "person": 4, "organization": 2},
    "by_direction": {
      "competitor": 8,
      "upstream": 6,
      "downstream": 10,
      "lateral": 3,
      "capital_related": 5,
      "unknown": 2
    },
    "high_confidence_count": 15,
    "pending_validation": 5
  },
  "produced_at": "2026-04-05T12:00:00+08:00"
}
```

**核心字段说明**：
- `directions.primary` — 主要归类方向
- `directions.secondary` — 交叉关联方向
- `evidence[]` — 所有证据链（支持交叉验证计算）
- `dimensions_active` — 该实体已激活哪些维度

## 5. competitors.json — 竞争格局

```json
{
  "tier_summary": {
    "L1_direct": [{"name": "公司A", "confidence": 0.9}],
    "L2_indirect": [{"name": "公司B", "confidence": 0.7}],
    "L3_potential": [{"name": "公司C", "confidence": 0.5}],
    "L4_substitute": [{"name": "内部团队", "confidence": 0.3}]
  },
  "market_structure": {
    "leaders": ["公司A"],
    "challengers": ["公司B", "目标公司"],
    "niche_players": ["公司D", "公司E"],
    "new entrants": ["公司F"]
  },
  "competition_matrix": [
    {
      "company": "竞对A",
      "product_completeness": 4,
      "price_competitiveness": 2,
      "customer_coverage": 5,
      "tech_strength": 4,
      "brand_reputation": 5
    }
  ],
  "differentiation_analysis": {
    "target_usp": "目标企业的独特价值主张",
    "competitor_moats": {"竞对A": "护城河描述"},
    "market_gaps": ["空白点1"]
  },
  "threat_assessment": [
    {"type": "direct_competition", "source": "竞对A", "urgency": "高", "response_suggestion": "建议"}
  ],
  "l1_profiles_ref": ["competitors/竞对A/profile.json"],
  "summary": {
    "total_competitors": 12,
    "l1_count": 2,
    "high_confidence": 8,
    "key_finding": "市场呈双寡头格局，目标公司与竞对A共同占据约60%份额"
  },
  "produced_at": "2026-04-05T12:00:00+08:00"
}
```

## 6. supply_chain.json — 产业链上下游

```json
{
  "upstream": [
    {
      "name": "供应商A",
      "type": "供应商/技术方/数据源/资金方/控股方",
      "evidence_sources": ["path1_bidding", "path3_news"],
      "confidence": 0.8,
      "revenue_contribution_est": "估算占比",
      "detail": "具体证据描述",
      "cross_refs": {"competitors": null, "capital": "investor"}
    }
  ],
  "downstream": [
    {
      "name": "客户X",
      "type": "客户(G端)/客户(B端)/分销商/加盟商",
      "evidence_sources": ["bidding_ccgp"],
      "confidence": 1.0,
      "revenue_contribution_est": "约15%",
      "deal_count": 5,
      "detail": "中标记录5次，总额约XXX万",
      "cross_refs": null
    }
  ],
  "lateral": [
    {"name": "合作伙伴Y", "type": "联合投标方/生态伙伴/战略联盟", "evidence_sources": [], "confidence": 0.6, "detail": ""}
  ],
  "concentration_risk": {
    "upstream_risk": "中",
    "downstream_risk": "低",
    "top_upstream": [{"name": "供应商A", "weight_est": 0.35}],
    "top_downstream": [{"name": "客户X", "deal_count": 5}]
  },
  "summary": {
    "total_entities_found": 20,
    "high_confidence_count": 14,
    "key_findings": ["关键发现1", "关键发现2"]
  },
  "produced_at": "2026-04-05T12:00:00+08:00"
}
```

## 7. capital_graph.json — 资本关系图谱

详见 `references/capital-research.md` 中的输出格式。节点-边结构：

```json
{
  "nodes": [
    {"name": "公司A", "type": "target|parent|subsidiary|investor|investee|officer|related", "detail": {}}
  ],
  "edges": [
    {"from": "A", "to": "B", "relation": "控股|参股|投资|高管兼任|联合投标|同地址|家族关联", "evidence": "...", "confidence": 0.9}
  ],
  "summary": {"total_nodes": 15, "total_edges": 22, "key_findings": []},
  "produced_at": "..."
}
```

## 8. round_logs/ — 轮次日志

每轮迭代一个文件：`round_logs/round_N.json`

```json
{
  "round": 1,
  "started_at": "2026-04-05T10:30:00+08:00",
  "ended_at": "2026-04-05T10:45:00+08:00",
  "focus_dimensions": ["competitor"],
  "focus_reason": "竞对维度为空白，优先启动",
  "queries_submitted": [{"label": "q01", "query": "关键词", "engine": "all"}],
  "results_summary": {
    "total_results": 85,
    "new_entities_found": 12,
    "entities_by_type": {"company": 8, "person": 3, "product": 1},
    "surprising_finds": ["意外发现A"]
  },
  "decisions_made": ["确认X公司为L1直接竞对", "Y公司标记为潜在上游供应商，下轮验证"],
  "seed_pool_changes": {"added": 12, "marked_explored": 3, "promoted_confidence": 2},
  "next_round_plan": {
    "suggested_focus": ["supply_chain"],
    "reason": "竞对初版完成，转向产业链下游挖掘",
    "candidate_seeds": ["种子P", "种子Q"]
  },
  "convergence_check": {
    "new_entities_this_round": 12,
    "stale_rounds": 0,
    "should_stop": false
  }
}
```

## 9. raw/ — 原始数据

### 命名规范

| 来源 | 文件名格式 | 示例 |
|------|-----------|------|
| 搜索query | `qNN.txt` | `q01.txt`, `q02.txt`, ..., `q15.txt` |
| 百科查询 | `baike.txt` | 固定名称 |
| URL抓取 | `uNN.txt` | `u01.txt`, `u02.txt` |
| 从文件批量导入 | `fNN.txt` | `f01.txt` |

### 文件内容格式

```
===== q01 =====
Query: 搜索关键词
Engine: baidu-ai-search (默认)
Results: 10

1. 标题
   URL: https://...
   Snip: 摘要文本...
```

## 10. 数据复用机制

### 断点续跑流程

```
收到调查请求
  │
  ├─ data/{公司}/ 存在？
  │   ├─ 否 → Phase 0 开始全新调查
  │   └─ 是 ↓
  │
  ├─ status.json 存在？
  │   ├─ 否但有 raw/ → 扫描推断进度，补建 status.json
  │   └─ 是 → 读取进度 ↓
  │
  ├─ 检查收敛状态
  │   ├─ 已收敛 + report.pdf 存在
  │   │   ├─ 用户要求更新？→ 增量搜索 + 更新报告
  │   │   └─ 否则直接输出 ✅
  │   └─ 未收敛 → 从 next_round_suggestions 继续
  │
  └─ 复用已有JSON产物，不重复分析已处理数据
```

### 防重复规则

1. **实体去重**：新增实体先查 entity_pool.json，`normalized_name` 匹配则跳过（更新证据即可）
2. **Query去重**：记录已执行的query（status.json.search_stats 或独立文件），语义相似度>80%的不重复执行
3. **URL去重**：web_fetch前检查是否已抓取过相同URL

### 跨调查复用场景

| 场景 | 复用方式 |
|------|---------|
| 同一集团下不同子公司调查 | 复用母公司的资本图谱和部分供应链 |
| 同一赛道不同公司调查 | 复用行业榜单和通用产业链知识（手动参考） |
| 更新已有调查 | 增量搜索（聚焦最新动态），合并到现有JSON |
| 同一公司二次深入某维度 | 直接复用其他维度已有数据，只补缺口 |

---

*本文件定义 JSON 数据格式。报告撰写标准（§11 写作铁律/对比铁律/自检清单）见 `report-writing-guide.md`。*
