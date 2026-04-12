# 🏢 Company Chain Investigate — OSINT 企业调查 Skill

> **多路径 OSINT 企业调查**：竞争对手分析、产业链上下游追踪、资本关系挖掘与市场地位智能评估

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-9.5-blue.svg)](https://github.com/hxd0818/company-chain-investigate)

---

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🎯 **企业背景调查** | 基础信息、工商数据、经营状况全方位画像 |
| ⚔️ **竞争对手分析** | Agent 自主推导竞争全域，发现直接/间接竞对 |
| 🔗 **产业链图谱** | 上游供应商 + 下游客户，自主规划搜索策略 |
| 💰 **资本关系追踪** | 股权结构、融资历史、投资事件、关联交易 |
| 👤 **关键人物调研** | 高管团队、实际控制人、关联人物网络 |
| 📊 **市场地位评估** | 六维度 30+ 指标 PIR 评分体系 |

## 🏗️ 架构设计

```
┌──────────────────────────────────────┐
│           AI Agent (大脑)             │
│  决定策略 → 设计查询 → 分析判断        │
│  种子池管理 → 收敛判断 → 报告生成      │
│                                      │
│  ┌──────────────────────────────┐     │
│  │   🌀 螺旋迭代引擎 (v9.5)      │     │
│  │  Phase 0: 初始化(百科+泛搜)    │     │
│  │  Phase N: 十步迭代循环         │     │
│  │  → 实体提取 → 去重 → 扩散链    │     │
│  │  → PIR 驱动收敛 (非轮次驱动)   │     │
│  └──────────────────────────────┘     │
└──────────────┬───────────────────────┘
               │ query / baike / pdf
               ▼
┌──────────────────────────────────────┐
│       investigate-v7.py (工具)        │
│  纯搜索脚本 · 零业务逻辑              │
│  百度AI搜索 / 百度百科 / PDF生成      │
└──────────────────────────────────────┘
```

**核心设计原则：**
- **Agent = 大脑**（决定搜什么、什么顺序、何时停）
- **脚本 = 纯工具**（只负责搜索和存文件）
- **状态铁律**：`status.json` 是迭代的唯一真相源

## 🚀 快速开始

### 环境要求

- Python 3.10+
- OpenClaw Agent Runtime（或兼容的 AI Agent 平台）

### 安装

```bash
# 克隆仓库
git clone https://github.com/hxd0818/company-chain-investigate.git
cd company-chain-investigate

# 安装依赖
pip install -r requirements.txt  # 如有
```

### 使用方式

作为 **OpenClaw Skill** 使用时，Agent 会自动加载 `SKILL.md` 并按方法论自主执行。

手动调用脚本：

```bash
# 基础搜索
python3 scripts/investigate-v7.py "公司名" --query "关键词"

# 多关键词批量搜索
python3 scripts/investigate-v7.py "公司名" --query "q1" "q2" "q3"

# 从文件读取查询词
python3 scripts/investigate-v7.py "公司名" --query-file queries.txt

# 百科快速起点（推荐第一步）
python3 scripts/investigate-v7.py "公司名" --baike

# 生成 PDF 报告
python3 scripts/investigate-v7.py "公司名" --query "q1" "q2" --pdf
```

## 📁 项目结构

```
company-chain-investigate/
├── SKILL.md                          # Skill 主文件（Agent 入口）
├── README.md                         # 本文件
├── .gitignore                        # 排除运行时 data/
│
├── scripts/
│   ├── investigate-v7.py             # v7 搜索脚本（纯工具，~430行）
│   └── md2pdf.py                     # Markdown → PDF 报告生成器
│
├── references/                       # 方法论文档集
│   ├── methodology.md                # 螺旋迭代状态机与收敛框架
│   ├── entity-tier-strategy.md       # 种子池管理 + 实体分层策略
│   ├── data-quality-gate.md          # 数据质量门禁（时效门槛+分级）
│   ├── pir-template.md               # PIR 模板与需求驱动收敛
│   ├── competitor-research.md        # 竞争对手调研方法
│   ├── supply-chain.md               # 产业链上下游调研方法
│   ├── capital-research.md           # 资本关系调研方法
│   ├── people-research.md            # 关键人物调研方法
│   ├── output-specs.md               # 产出物 JSON 格式规范
│   ├── report-writing-guide.md       # 报告撰写标准与自检清单
│   └── analyst-identity.md           # 分析师身份与职业规范
│
├── templates/                         # 报告模板（预留）
│
└── data/                             # 运行时产出（git 忽略）
    └── {公司名}/
        ├── raw/                      # 原始搜索结果
        ├── status.json               # 迭代状态（唯一真相源）
        ├── report_v94.md             # Markdown 报告
        ├── report_styled.html        # HTML 报告
        └── report_v94.pdf            # PDF 报告
```

## 🌀 方法论详解

### 螺旋迭代流程

```
Phase 0: 初始化
  百科查询 + 泛化搜索(3个) → 初始种子集 → status.json
      ↓
Phase N: 十步迭代循环
  ① 读status.json → ② 回顾评估决策 → ③ 选种+设计query
  ④ 执行搜索 → ⑤ 搜索质量自评 → ⑥ 分析整合(提取新实体)
  ⑦ 更新种子池(去重+扩散) → ⑧ 更新PIR置信度
  ⑨ 写回status.json → ⑩ 收敛判断
      ↓ 未收敛 → 回到①
      ↓ 已收敛 → 生成报告
```

### 收敛机制（PIR 驱动）

- **唯一标准**：所有 CRITICAL/HIGH 级 PIR 达到目标置信度
- **轮次下限**：< 6 轮禁止收敛（信息量不足）
- **轮次上限**：15 轮强制停止（生成阶段性报告）
- **安全阀**：连续 3 轮无效 / 种子池枯竭 → 强制评估

### 四大并行维度

| 维度 | 调研内容 |
|------|---------|
| ⚔️ 竞争对手 | 商业边界→竞争域→自适应发现 |
| 🔗 产业链 | 图谱→节点→上游供应商/下游客户 |
| 💰 资本关系 | 股权/高管/投资事件追踪 |
| 👤 关键人物 | 决策者/投资者/关联人物网络 |

### 三级质量门禁

1. **数据对比铁律** — 跨实体数值对比必须时间口径对齐
2. **数据质量门禁** — 时效分级(🟢🟡🟠🔴) + 缺口决策树 + 推算闭环
3. **PIR 驱动收敛** — 终止条件是"关键问题是否已答"，非数轮次

## 📊 评估体系

### 六维度 PIR 评分模型

| 维度 | 权重 | 示例指标 |
|------|------|---------|
| 🏢 基础实力 | ★★★★ | 注册资本、员工规模、营收、资质 |
| 💰 资本健康 | ★★★★ | 融资额、估值、负债率、现金流 |
| 👥 团队背景 | ★★★★ | 高管履历、技术基因、稳定性 |
| 🔗 供应链地位 | ★★★ | 上游依赖度、下游集中度、替代性 |
| ⚔️ 竞争格局 | ★★★ | 市场份额、护城河、差异化 |
| 📈 舆情风险 | ★★ | 负面事件、合规风险、声誉 |

每项 PIR 设定目标置信度，通过螺旋迭代逐项验证。

## ⚙️ 配置与限流

| 参数 | 值 | 说明 |
|------|-----|------|
| 百度请求间隔 | ≥2.5s | API 限流 |
| web_fetch 间隔 | ≥5s | 同域名连续请求 |
| 全局并发 | ≤2 | 所有引擎 |
| 最小有效轮次 | 6 | 过早收敛防护 |
| 最大轮次 | 15 | 强制停止 |

## 🔧 开发指南

### 扩展搜索引擎

在 `scripts/investigate-v7.py` 中添加新的 engine 函数即可。脚本采用插件式设计。

### 添加新维度

1. 在 `references/` 下创建新的方法论文档
2. 在 `pir-template.md` 中添加对应 PIR 条目
3. 在 `SKILL.md` 的导航索引中注册

### 输出格式

所有产出遵循 `references/output-specs.md` 规范：
- JSON 结构化数据 + Markdown 分析报告
- 支持 PDF 导出（通过 `md2pdf.py`）

## 📝 已验证案例

| 企业 | PIR 达标数 | 关键发现 |
|------|-----------|---------|
| KK集团（广东快客） | 3/5 | 负债135亿资不抵债，四度IPO失效 |
| 赛迪顾问 | 78/100 | 工信部CCID旗下上市咨询公司 |
| 和沐智讯 | 75/100 | 工业互联网科创服务商，微型企业 |
| 泛联信息科技(UBIX) | 82/100 | 华为系分布式存储，MLPerf 7项全球第一 |

## 📄 License

MIT License — 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎 Issue 和 PR！本项目为 [OpenClaw](https://github.com/openclaw/openclaw) 生态 Skill。

---

<p align="center">
  Built with ❤️ for <a href="https://docs.openclaw.ai">OpenClaw</a>
</p>
