# 🔍 OpenProbe — OSINT Deep Enterprise Investigation

> **Data Mining from Public Sources**: Corporate background checks, competitor analysis, upstream/downstream supply chain tracking, capital relationship mining, and intelligent market position assessment

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-9.5-blue.svg)](https://github.com/hxd0818/openprobe)

---

## ✨ Core Capabilities

| Capability | Description |
|------------|-------------|
| 🎯 **Corporate Background** | Full profiling: basic info, business registration, operational status |
| ⚔️ **Competitor Analysis** | Agent autonomously derives competitive landscape, discovers direct/indirect rivals |
| 🔗 **Supply Chain Mapping** | Upstream suppliers + downstream customers, self-planned search strategy |
| 💰 **Capital Relationship Tracking** | Equity structure, financing history, investment events, related-party transactions |
| 👤 **Key Person Research** | Executive team, ultimate beneficial owners,关联人物 network |
| 📊 **Market Position Assessment** | Six-dimension 30+ indicator PIR scoring system |

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│           AI Agent (Brain)            │
│  Decide strategy → Design queries    │
│  Seed pool management → Convergence  │
│  judgment → Report generation        │
│                                      │
│  ┌──────────────────────────────┐     │
│  │   🌀 Spiral Engine (v9.5)     │     │
│  │  Phase 0: Init (Baike+Broad)  │     │
│  │  Phase N: 10-Step Loop        │     │
│  │  → Entity extract → Dedup     │     │
│  │  → Diffusion chain → PIR      │     │
│  │  driven convergence           │     │
│  └──────────────────────────────┘     │
└──────────────┬───────────────────────┘
               │ query / baike / pdf
               ▼
┌──────────────────────────────────────┐
│       investigate-v7.py (Tool)        │
│  Pure search script · Zero business  │
│  logic · Baidu AI Search / Baike /   │
│  PDF generation                      │
└──────────────────────────────────────┘
```

**Core Design Principles:**
- **Agent = Brain** (decides what to search, in what order, when to stop)
- **Script = Pure Tool** (only handles search & file I/O)
- **State Iron Rule**: `status.json` is the single source of truth for iteration state

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenClaw Agent Runtime (or compatible AI Agent platform)

### Installation

```bash
# Clone the repo
git clone https://github.com/hxd0818/openprobe.git
cd openprobe

# Install dependencies
pip install -r requirements.txt  # if applicable
```

### Usage

When used as an **OpenClaw Skill**, the Agent automatically loads `SKILL.md` and executes autonomously per the methodology.

Manual script invocation:

```bash
# Basic search
python3 scripts/investigate-v7.py "Company Name" --query "keyword"

# Multi-keyword batch search
python3 scripts/investigate-v7.py "Company Name" --query "q1" "q2" "q3"

# Read queries from file
python3 scripts/investigate-v7.py "Company Name" --query-file queries.txt

# Encyclopedia quick start (recommended first step)
python3 scripts/investigate-v7.py "Company Name" --baike

# Generate PDF report
python3 scripts/investigate-v7.py "Company Name" --query "q1" "q2" --pdf
```

## 📁 Project Structure

```
openprobe/
├── SKILL.md                          # Skill main file (Agent entry point)
├── README.md                         # This file (Chinese)
├── README_EN.md                      # English version
├── .gitignore                        # Excludes runtime data/
│
├── scripts/
│   ├── investigate-v7.py             # v7 search script (pure tool, ~430 lines)
│   └── md2pdf.py                     # Markdown → PDF report generator
│
├── references/                       # Methodology document set
│   ├── methodology.md                # Spiral iteration state machine & convergence framework
│   ├── entity-tier-strategy.md       # Seed pool management + entity tiering strategy
│   ├── data-quality-gate.md          # Data quality gate (freshness threshold + grading)
│   ├── pir-template.md               # PIR template & requirement-driven convergence
│   ├── competitor-research.md        # Competitor research methodology
│   ├── supply-chain.md               # Supply chain upstream/downstream methodology
│   ├── capital-research.md           # Capital relationship research methodology
│   ├── people-research.md            # Key person research methodology
│   ├── output-specs.md               # Output JSON format specification
│   ├── report-writing-guide.md       # Report writing standards & self-checklist
│   └── analyst-identity.md           # Analyst identity & professional standards
│
├── templates/                        # Report templates (reserved)
│
└── data/                             # Runtime outputs (git ignored)
    └── {CompanyName}/
        ├── raw/                      # Raw search results
        ├── status.json               # Iteration state (single source of truth)
        ├── report_v94.md             # Markdown report
        ├── report_styled.html        # HTML report
        └── report_v94.pdf            # PDF report
```

## 🌀 Methodology Deep Dive

### Spiral Iteration Flow

```
Phase 0: Initialization
  Encyclopedia query + Broad search(3) → Initial seed set → status.json
      ↓
Phase N: 10-Step Iteration Loop
  ① Read status.json → ② Review & assess decisions → ③ Select seed + design query
  ④ Execute search → ⑤ Self-assess search quality → ⑥ Analyze & integrate (extract new entities)
  ⑦ Update seed pool (dedup + diffusion) → ⑧ Update PIR confidence
  ⑨ Write back status.json → ⑩ Convergence check
      ↓ Not converged → Back to ①
      ↓ Converged → Generate report
```

### Convergence Mechanism (PIR Driven)

- **Single criterion**: All CRITICAL/HIGH-level PIRs reach target confidence
- **Minimum rounds**: < 6 rounds forbidden from converging (insufficient information)
- **Maximum rounds**: 15 rounds forced stop (generate interim report)
- **Safety valve**: 3 consecutive无效 rounds / seed pool exhausted → forced assessment

### Four Parallel Dimensions

| Dimension | Research Scope |
|-----------|---------------|
| ⚔️ Competitors | Business boundary → Competitive domain → Adaptive discovery |
| 🔗 Supply Chain | Graph → Nodes → Upstream suppliers / Downstream customers |
| 💰 Capital | Equity / executives / investment event tracking |
| 👤 Key Persons | Decision makers / investors / 关联人物 network |

### Three-Level Quality Gates

1. **Cross-entity comparison iron rule** — Numerical comparisons across entities must use time-aligned data
2. **Data quality gate** — Freshness grading (🟢🟡🟠🔴) + gap decision tree + estimation closed-loop
3. **PIR-driven convergence** — Termination condition is "have key questions been answered?", not round counting

## 📊 Assessment Framework

### Six-Dimension PIR Scoring Model

| Dimension | Weight | Example Indicators |
|-----------|--------|-------------------|
| 🏢 Basic Strength | ★★★★ | Registered capital, headcount, revenue, qualifications |
| 💰 Capital Health | ★★★★ | Financing amount, valuation, debt ratio, cash flow |
| 👥 Team Background | ★★★★ | Executive resumes, technical DNA, stability |
| 🔗 Supply Chain Position | ★★★ | Upstream dependency, downstream concentration, substitutability |
| ⚔️ Competitive Landscape | ★★★ | Market share, moat, differentiation |
| 📈 Reputation Risk | ★★ | Negative events, compliance risk, reputation |

Each PIR item has a target confidence level, verified progressively through spiral iteration.

## ⚙️ Configuration & Rate Limiting

| Parameter | Value | Description |
|-----------|-------|-------------|
| Baidu request interval | ≥2.5s | API rate limiting |
| web_fetch interval | ≥5s | Same-domain consecutive requests |
| Global concurrency | ≤2 | All engines |
| Minimum valid rounds | 6 | Early convergence protection |
| Maximum rounds | 15 | Forced stop |

## 🔧 Development Guide

### Extending Search Engines

Add a new engine function in `scripts/investigate-v7.py`. The script uses a plugin-style design.

### Adding a New Dimension

1. Create a new methodology doc under `references/`
2. Add corresponding PIR entries in `pir-template.md`
3. Register in the navigation index of `SKILL.md`

### Output Format

All outputs follow `references/output-specs.md`:
- Structured JSON data + Markdown analysis report
- PDF export supported (via `md2pdf.py`)

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE)

## 🤝 Contributing

Issues and PRs welcome! This project is an [OpenClaw](https://github.com/openclaw/openclaw) ecosystem Skill.

---

<p align="center">
  Built with ❤️ for <a href="https://docs.openclaw.ai">OpenClaw</a>
</p>
