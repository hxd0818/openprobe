---
name: company-chain-investigate
description: >
  多路径OSINT企业调查：竞争对手、产业链上下游、资本关系追踪与市场地位评估。
  触发场景：企业背景调查、竞对分析、供应链图谱、股权/投资关系挖掘、
  产业图谱绘制、市场地位评估。Agent自主驱动螺旋迭代，
  脚本=纯搜索工具（百度/百科），输出结构化JSON+分析报告(PDF)。
---

# 企业产业链 OSINT 调查（v9.5 — 螺旋迭代+质量门禁+时效强制门槛架构）

> **核心**：Agent = 大脑（决定搜什么、何时停），脚本 = 纯工具（搜索+存文件）
> **方法论**：螺旋迭代 + 种子扩散（非线性四阶段）

## 架构

```
Agent（你）                          脚本（dumb tool）
┌──────────────────────┐            ┌──────────────────┐
│ 决定策略 → 设计query │ ──传入──→  │ 搜索 → 存raw/    │
│ 读结果 → 分析判断     │ ←返回───  │ 零业务逻辑       │
│ 更新种子池 → 下一轮   │            └──────────────────┘
│  ↑__循环直到收敛_____|               --query / --baike / --pdf
└──────────────────────┘
```

## 工具用法速查

```bash
# 基础搜索
python3 scripts/investigate-v7.py "公司名" --query "关键词"
python3 scripts/investigate-v7.py "公司名" --query "q1" "q2" "q3"
python3 scripts/investigate-v7.py "公司名" --query-file queries.txt

# 百科（快速起点）
python3 scripts/investigate-v7.py "公司名" --baike

# 引擎选择
--engine baidu      # 百度AI搜索（默认）
--engine baike      # 仅百科（快速起点）

# PDF报告（⭐reportlab方案，唯一可靠方式）
python3 scripts/gen_pdf.py data/公司名/report.md [output.pdf]
```

输出目录：`data/{公司名}/raw/*.txt` + `report.md` + `report.pdf`

> ⚠️ **PDF生成必须使用 `scripts/gen_pdf.py`（基于reportlab）**，禁止使用Chrome headless/weasyprint/browser tool的PDF功能（均不可靠：Chrome依赖HTTP服务存活+调试端口，weasyprint在Python 3.6有FFI bug）。gen_pdf.py自动提取中文字体(wqy-microhei.ttc→TTF)，支持Markdown表格/代码块/引用等完整语法。

## 限流规则（硬性）

| 规则 | 值 | 说明 |
|------|-----|------|
| 百度请求间隔 | ≥2.5s | API限流 |
| **web_fetch间隔** | **≥5秒** | 同域名连续请求必须遵守 |
| 全局并发 | ≤2 | 所有引擎 |

> ⚠️ web_fetch 对同一域名连续请求间隔必须 ≥5秒，否则触发反爬。

## 🌀 螺旋迭代 + 种子扩散方法论

```
Phase 0: 初始化（百科 + 泛化搜索3个 → 初始种子集 → status.json）
    ↓
Phase N: 迭代循环（每轮十步，详见 methodology.md §4）
    ① 读status.json   ② 回顾评估+决策   ③ 选种+设计query
    ④ 执行搜索         ⑤ 搜索质量自评     ⑥ 分析整合(提取新实体)
    ⑦ 更新种子池(去重, **新种子→下轮搜索起点=扩散链**)  ⑧ 更新PIR置信度    ⑨ 写回status.json
    ⑩ 收敛判断 ──未收敛→回到① / 已收敛→生成报告
```

**收敛标准（⭐v9.5 PIR唯一驱动，轮次仅作护栏）**：
- **唯一标准**：所有 CRITICAL/HIGH 级 PIR 达到 target_confidence（见 `pir-template.md`）
- **轮次下限**：有效轮次 < **6** 时**禁止收敛**（信息量不足，过早收敛=浅尝辄止）
- **轮次上限**：**15轮**强制停止（生成阶段性报告，标注未满足项）
- **安全阀**：连续3轮无效 / 种子池枯竭 → 强制评估是否 stalled
- **❌ 禁止**：因"已达N轮"而主动收敛（轮次是护栏，不是目标）

> **🔒 状态铁律**：`status.json` 是迭代的**唯一状态真相源**。每轮**必须**①读取→⑨写回（缺一不可）。断点续跑、收敛判断、PIR追踪全部依赖它。（详见 `methodology.md` §2）

**四大并行维度**：
1. **竞争对手** — 谁在做同样的事？（详见 `references/competitor-research.md`）
2. **产业链** — 谁是上游供应商/下游客户？（详见 `references/supply-chain.md`）
3. **资本关系** — 谁控股/谁投资/谁兼任？（详见 `references/capital-research.md`）
4. **关键人物** — 谁在决策？谁在投资？谁有关联？（详见 `references/people-research.md`）⭐v9新增

**⭐ 基础信息增强（每轮必做）**：
- **联系方式采集**（PIR-CONTACT，CRITICAL级）：Phase 0百科查询后即开始收集，后续每轮持续补充
  - 优先级：官网 > 百科 > 招聘页 > 社交媒体 > 工商信息 > 新闻稿
  - 必采字段：电话、邮箱(≥1个)、详细地址、官网URL、社交媒体账号
  - 加分项：客服渠道、投资者关系联系方式、商务合作入口
  - 搜索关键词示例：`"{公司名} 联系方式 电话"` `"{公司名} 官网 邮箱"` `"{公司名} 招聘 联系我们"` `"{公司名} 微信公众号 官方"`
  - 输出位置：`profile.json` 的 `contact_info` 字段 + 报告「企业画像」章节

每轮根据缺口选重点，不必每轮都覆盖三个维度。

## 导航索引

| 文件 | 内容 |
|------|------|
| `references/methodology.md` | 螺旋迭代状态机（Phase 0/十步迭代/收敛/行业自适应） |
| `references/entity-tier-strategy.md` | ⭐⭐ **种子池管理 + 实体分层策略 v9.5**（Tier 1深挖/Tier2快照/Tier3占位） |
| `references/data-quality-gate.md` | ⭐⭐⭐ **数据质量门禁 v9.3**（时效强制门槛+时效分级+缺口决策树+推算规范） |
| `references/people-research.md` | 高管与关键人物调研（v9新增） |
| `references/competitor-research.md` | 竞争对手调研（v9.3 Agent自主推理：商业边界→竞争域→自适应发现） |
| `references/supply-chain.md` | 产业链上下游调研（v9.2 Agent自主推理：图谱→节点→自主规划策略） |
| `references/capital-research.md` | 资本关系调研（股权/高管/投资事件） |
| `references/pir-template.md` | ⭐⭐ **PIR模板与收敛框架**（v9.1核心，需求驱动收敛） |
| `references/output-specs.md` | 产出物JSON格式规范（§1-10：目录结构/JSON模板/复用机制） |
| `references/report-writing-guide.md` | ⭐⭐ 报告撰写标准与自检清单（写作铁律+对比铁律+v9.2数据质量门禁检查） |
| `references/analyst-identity.md` | ⭐⭐ 分析师身份与职业规范（Agent身份定义，必读） |

> ⚠️ **质量门禁体系（三级，违反任一 = 报告不合格）**：
> 1. **v9.1 数据对比铁律**：跨实体数值对比必须时间口径对齐（→ `output-specs.md` §11.6）
> 2. **v9.2 数据质量门禁**：时效分级(🟢🟡🟠🔴) + 缺口决策树 + 推算闭环（→ `data-quality-gate.md`；自检项 → `report-writing-guide.md` §8.7）
> 3. **v9 PIR驱动收敛**：终止条件是"关键问题是否已答"，非数轮次/数实体（→ `pir-template.md` + `methodology.md` §5）

> 🎓 **执行前必读**：`references/analyst-identity.md` — 以"资深产业研究员"身份开展工作。
> 📋 **完整文件导航**：见上方「导航索引」表（11个reference文件，按需加载）。
