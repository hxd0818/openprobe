#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
company-chain-investigate v7.1: OSINT 数据采集工具
==================================================
数据源（按优先级）：
  1. baidu-search (百度千帆AI Search) — 主力搜索引擎
  2. baidu-baike-data (百度百科) — 结构化企业信息
  3. web_fetch (直接抓取URL) — 补充数据源

核心约束：
  - 全局并发 ≤ 2（所有请求排队）
  - 百度请求间隔 ≥ 2.5s
  - web_fetch 间隔 ≥ 5s

用法:
  python3 investigate-v7.py "公司名" --query "关键词"
  python3 investigate-v7.py "公司名" --query-file queries.txt
  python3 investigate-v7.py "公司名" --baike
  python3 investigate-v7.py "公司名" --fetch-url "https://..."
  python3 investigate-v7.py "公司名" --query "q1" --baike --fetch-file urls.txt --pdf
"""

import argparse, json, os, sys, time, threading, subprocess
from datetime import datetime
from pathlib import Path

# ======================== 配置 ========================
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_SKILLS = SKILL_DIR.parent

BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "")
BAIDU_SCRIPT = WORKSPACE_SKILLS / "baidu-search" / "scripts" / "search.py"
BAIDU_BAIKE_SCRIPT = WORKSPACE_SKILLS / "baidu-baike-data" / "scripts" / "baidu_baike.py"
DATA_DIR_TEMPLATE = SKILL_DIR / "data"

# 全局并发控制
MAX_CONCURRENT = 2          # 所有请求最大并发数
BAIDU_INTERVAL = 2.5        # 百度搜索最小间隔(秒)
FETCH_INTERVAL = 5.0        # web_fetch 最小间隔(秒)


# ======================== 日志 ========================
def log(msg, level="INFO"):
    tag = {"INFO": "\033[92m[INFO]\033[0m", "OK": "\033[94m[OK]\033[0m",
           "WARN": "\033[93m[WARN]\033[0m", "ERR": "\033[91m[ERR]\033[0m"}.get(level, level)
    print("%s %s" % (tag, msg))


def save_raw(data_dir, filename, content):
    """保存原始数据到 data/{公司}/raw/"""
    out = data_dir / "raw" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# ==================== 全局请求队列 ====================
class RequestQueue:
    """
    全局请求队列 — 所有数据源请求必须通过此队列。
    并发 ≤ MAX_CONCURRENT，百度额外限速。
    支持三种请求类型：search / baike / fetch
    """

    def __init__(self):
        self.results = {}
        self.errors = {}
        self._semaphore = threading.Semaphore(MAX_CONCURRENT)
        self._lock = threading.Lock()
        self._last_baidu = 0      # 上次百度请求时间
        self._last_fetch = 0      # 上次web_fetch时间

    def submit_search(self, label, query, data_dir, filename, count=10):
        """提交一个百度搜索任务"""
        t = threading.Thread(target=self._do_search,
                             args=(label, query, data_dir, filename, count))
        t.daemon = True
        t.start()

    def submit_baike(self, company, data_dir):
        """提交一个百度百科查询任务"""
        t = threading.Thread(target=self._do_baike,
                             args=(company, data_dir))
        t.daemon = True
        t.start()

    def submit_fetch(self, label, url, data_dir, filename):
        """提交一个 web_fetch 任务"""
        t = threading.Thread(target=self._do_fetch,
                             args=(label, url, data_dir, filename))
        t.daemon = True
        t.start()

    # ---------- 内部实现 ----------

    def _wait_baidu(self):
        """百度限速等待"""
        with self._lock:
            elapsed = time.time() - self._last_baidu
            if elapsed < BAIDU_INTERVAL:
                wait = BAIDU_INTERVAL - elapsed + 0.1
                log("  [baidu] waiting %.1fs..." % wait)
                time.sleep(wait)
            self._last_baidu = time.time()

    def _wait_fetch(self):
        """web_fetch 限速等待"""
        with self._lock:
            elapsed = time.time() - self._last_fetch
            if elapsed < FETCH_INTERVAL:
                time.sleep(FETCH_INTERVAL - elapsed + 0.1)
            self._last_fetch = time.time()

    def _do_search(self, label, query, data_dir, filename, count):
        """执行百度搜索（排队+限速）"""
        self._semaphore.acquire()
        try:
            self._wait_baidu()
            results = _search_baidu(query, count)
            content = self._format_search_results(label, query, results)
            save_raw(data_dir, filename, content)
            self.results[label] = results
            log("  OK [search:%s]: %d results" % (label, len(results)), "OK")
        except Exception as e:
            log("[search:%s] Error: %s" % (label, e), "ERR")
            self.errors[label] = str(e)
        finally:
            self._semaphore.release()

    def _do_baike(self, company, data_dir):
        """执行百科查询（排队）"""
        self._semaphore.acquire()
        try:
            self._wait_baidu()  # 百度API也走限速
            data = search_baike(company)
            if data:
                content = format_baike_data(data)
                save_raw(data_dir, "baike.txt", content)
                self.results["baike"] = data
                title = data.get("lemma_title", company)
                log("  OK [baike]: %s" % title, "OK")
            else:
                log("  [baike] No result for '%s'" % company, "WARN")
        except Exception as e:
            log("[baike] Error: %s" % e, "ERR")
            self.errors["baike"] = str(e)
        finally:
            self._semaphore.release()

    def _do_fetch(self, label, url, data_dir, filename):
        """执行 web_fetch（排队+限速）"""
        self._semaphore.acquire()
        try:
            self._wait_fetch()
            result = _web_fetch(url)
            content = "===== %s =====\nURL: %s\nStatus: %s\nLength: %d chars\n---\n%s" % (
                label, url, result.get("status", "?"),
                len(result.get("text", "")), result.get("text", "")
            )
            save_raw(data_dir, filename, content)
            self.results[label] = result
            status = result.get("status", 0)
            ok = 200 <= status < 300
            log("  OK [fetch:%s]: HTTP %d (%d chars)" % (label, status, len(result.get("text", ""))), "OK" if ok else "WARN")
        except Exception as e:
            log("[fetch:%s] Error: %s" % (label, e), "ERR")
            self.errors[label] = str(e)
        finally:
            self._semaphore.release()

    @staticmethod
    def _format_search_results(label, query, results):
        lines = [
            "===== %s =====" % label,
            "Query: %s" % query,
            "Engine: baidu-ai-search",
            "Results: %d" % len(results),
            "---",
        ]
        for i, r in enumerate(results, 1):
            lines.append("")
            lines.append("%d. %s" % (i, r.get("title", "")))
            if r.get("url"):
                lines.append("   URL: %s" % r["url"])
            if r.get("snippet"):
                lines.append("   Snip: %s" % r["snippet"])
        return "\n".join(lines)

    def wait_all(self, timeout=600):
        start = time.time()
        while threading.active_count() > 1:
            if time.time() - start > timeout:
                log("Queue timeout after %ds" % timeout, "ERR")
                break
            time.sleep(0.2)


# ==================== 数据源实现 ====================

def _search_baidu(query, count=10):
    """百度千帆 AI Search — 通过 baidu-search skill 脚本调用"""
    if not BAIDU_API_KEY or not BAIDU_SCRIPT.exists():
        log("Baidu search unavailable (no API key or script)", "WARN")
        return []
    body = json.dumps({"query": query, "count": min(count, 50)}, ensure_ascii=False)
    try:
        env = dict(os.environ)
        env["BAIDU_API_KEY"] = BAIDU_API_KEY
        result = subprocess.run(
            ["python3", str(BAIDU_SCRIPT), body],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=25, env=env
        )
        lines = result.stdout.strip().split('\n')
        js_idx = None
        for i, l in enumerate(lines):
            if l.startswith('[') or l.startswith('{'):
                js_idx = i
                break
        if js_idx is None:
            return []
        data = json.loads('\n'.join(lines[js_idx:]))
        items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        return [{"title": r.get("title", ""), "url": r.get("url", ""),
                 "snippet": str(r.get("content", ""))[:300], "source": "baidu"}
                for r in items if isinstance(r, dict)]
    except subprocess.TimeoutExpired:
        log("Baidu search timeout (>25s)", "ERR")
        return []
    except Exception as e:
        log("Baidu search fail: %s" % e, "ERR")
        return []


def search_baike(company):
    """百度百科结构化查询 — 通过 baidu-baike-data skill 脚本调用

    注意: 百度百科API需要精确匹配词条名，建议使用公司全称。
         短名如'和沐智讯'可能查不到，需用'北京和沐智讯科技有限公司'。
    """
    if not BAIDU_API_KEY or not BAIDU_BAIKE_SCRIPT.exists():
        log("Baike unavailable (no API key or script)", "WARN")
        return {}
    try:
        env = dict(os.environ)
        env["BAIDU_API_KEY"] = BAIDU_API_KEY
        result = subprocess.run(
            ["python3", str(BAIDU_BAIKE_SCRIPT),
             "--search_type", "lemmaTitle",
             "--search_key", company],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=20, env=env
        )
        text = result.stdout.strip()
        if not text:
            return {}
        if text.startswith('{') or text.startswith('['):
            return json.loads(text)
        return {"raw_text": text, "company": company}
    except subprocess.TimeoutExpired:
        log("Baike timeout (>20s)", "ERR")
        return {}
    except Exception as e:
        log("Baike fail: %s" % e, "ERR")
        return {}


def format_baike_data(baike_data):
    """格式化百科数据为可读文本（完整版）"""
    if isinstance(baike_data, dict):
        lines = []
        # 基本信息
        if baike_data.get("lemma_title"):
            lines.append("Title: %s" % baike_data["lemma_title"])
        if baike_data.get("lemma_id"):
            lines.append("ID: %s" % baike_data["lemma_id"])
        if baike_data.get("lemma_desc"):
            lines.append("Desc: %s" % baike_data["lemma_desc"])
        if baike_data.get("url"):
            lines.append("URL: %s" % baike_data["url"])

        # 摘要
        abstract = baike_data.get("abstract_plain") or baike_data.get("lemma_abstract")
        if abstract:
            lines.append("\nAbstract:\n%s" % abstract)

        # 信息卡片（结构化字段）
        card = baike_data.get("card")
        if card and isinstance(card, list):
            lines.append("\nInfo Card:")
            for item in card:
                name = item.get("name", "")
                value = item.get("value", [])
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                if name and value:
                    lines.append("  %s: %s" % (name, value))

        return "\n".join(lines)
    return str(baike_data)


def _web_fetch(url, max_chars=8000):
    """直接抓取URL内容（轻量实现，替代browser web_fetch）"""
    try:
        import urllib.request as ur
        req = ur.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        with ur.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        # 简单提取文本（去除HTML标签）
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.S | re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S | re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "... [截断]"
        return {"status": resp.status, "text": text, "url": url}
    except Exception as e:
        return {"status": 0, "text": "ERROR: %s" % e, "url": url}


# ==================== PDF 报告 ====================
def generate_pdf_report(company, data_dir):
    """从 raw/ 数据生成 HTML → PDF 报告"""
    raw_dir = data_dir / "raw"
    raw_files = sorted(raw_dir.glob("*.txt")) if raw_dir.exists() else []
    if not raw_files:
        log("No raw files for PDF report", "WARN")
        return

    total_results = 0
    for rf in raw_files:
        content = rf.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("Results:"):
                try:
                    total_results += int(line.split(":")[-1].strip())
                except:
                    pass

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>%s OSINT Report v8</title>
<style>
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;max-width:960px;margin:0 auto;padding:30px 36px;background:#ffffff;color:#1f2937;line-height:1.75;font-size:13.5px}
h1{color:#2563eb;border-bottom:2.5px solid #e0e7ff;padding-bottom:12px;font-size:24px;font-weight:700}
h2{color:#374151;margin-top:40px;font-size:17px;border-left:4px solid #3b82f6;padding-left:14px;font-weight:600}
.meta{background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:16px 24px;margin:18px 0;display:inline-block;font-size:13px}
table{width:100%%;border-collapse:collapse;margin:14px 0;font-size:13px;border-radius:8px;overflow:hidden}
th,td{border:1px solid #e5e7eb;padding:10px 14px;text-align:left}
th{background:#f8fafc;font-weight:600;color:#374151}
tr:nth-child(even){background:#fafbfc}
tr:hover{background:#f0f9ff}
.raw-section{margin:16px 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.04)}
.raw-section summary{background:#f8fafc;padding:12px 16px;font-weight:600;cursor:pointer;color:#374151;border-bottom:1px solid #e5e7eb}
.raw-section pre{padding:14px;margin:0;white-space:pre-wrap;word-break:break-all;font-size:12px;background:#ffffff;color:#4b5563}
.footer{text-align:center;color:#9ca3af;font-size:11px;margin-top:45px;border-top:1px solid #e5e7eb;padding-top:18px}
</style></head><body>
<h1>🔍 %s — OSINT 调查报告 <small>v8</small></h1>
<div class="meta">📅 %s | 📊 %d 个数据文件 | 📈 约%d 条结果 | 数据源: 百度搜索 + 百度百科 + WebFetch</div>

<h2>1. 原始数据</h2>
""" % (company, company, datetime.now().strftime("%Y-%m-%d %H:%M"), len(raw_files), total_results)

    for rf in raw_files:
        content = rf.read_text(encoding="utf-8")
        if len(content) > 4000:
            content = content[:4000] + "\n... [截断]"
        html += '<details open class="raw-section"><summary>%s</summary><pre>%s</pre></details>\n' % (
            rf.name, content.replace("<", "&lt;").replace(">", "&gt;"))

    html += """
<h2>2. 调查统计</h2>
<table>
<tr><th>项目</th><th>数据</th></tr>
<tr><td>目标</td><td>%s</td></tr>
<tr><td>版本</td><td>v8 (百度+百科+WebFetch)</td></tr>
<tr><td>数据文件</td><td>%d 个</td></tr>
<tr><td>总结果</td><td>约%d 条</td></tr>
<tr><td>生成时间</td><td>%s</td></tr>
<tr><td>目录</td><td>%s</td></tr>
</table>
<div class="footer">
<p>OSINT Skill v8 | 数据源: baidu-search + baidu-baike + web_fetch | 全局并发≤2 | web_fetch间隔≥5s</p>
<p>⚠️ 原始数据汇总，分析由Agent完成</p>
</div></body></html>""" % (company, len(raw_files), total_results,
           datetime.now().strftime("%Y-%m-%d %H:%M"), data_dir)

    html_path = data_dir / "report.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = data_dir / "report.pdf"
    log("Generating PDF...")
    try:
        r = subprocess.run([
            "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
            "--print-to-pdf=%s" % str(pdf_path),
            "--print-to-pdf-no-header",
            "file://%s" % str(html_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if pdf_path.exists():
            size = pdf_path.stat().st_size
            log("✅ PDF: %s (%d KB)" % (pdf_path.name, size // 1024), "OK")
        else:
            log("PDF not created: %s" % r.stderr.decode()[:200], "ERR")
    except Exception as e:
        log("PDF fail: %s" % e, "ERR")


# ==================== Main ====================
def main():
    p = argparse.ArgumentParser(description="OSINT Data Collection Tool v7.1 (百度+百科+WebFetch)")
    p.add_argument("company", help="目标公司名称")

    # 搜索任务
    p.add_argument("--query", nargs="+", metavar="QUERY", help="百度搜索关键词（可多个）")
    p.add_argument("--query-file", type=str, metavar="FILE",
                   help="从文件读取查询列表（每行: label|query 或纯query），#开头为注释")

    # 百科任务
    p.add_argument("--baike", action="store_true", help="查询百度百科")

    # URL抓取任务
    p.add_argument("--fetch-url", nargs="+", metavar="URL", help="直接抓取URL（可多个）")
    p.add_argument("--fetch-file", type=str, metavar="FILE",
                   help="从文件读取URL列表（每行: label|url 或纯url），#开头为注释")

    # 输出控制
    p.add_argument("--data-dir", type=str, help="自定义数据输出目录")
    p.add_argument("--pdf", action="store_true", help="完成后自动生成PDF报告")

    args = p.parse_args()

    company = args.company
    data_dir = Path(args.data_dir) if args.data_dir else DATA_DIR_TEMPLATE / company
    data_dir.mkdir(parents=True, exist_ok=True)

    Q = RequestQueue()

    # 收集所有任务
    task_count = 0

    # 1. 搜索任务
    if args.query:
        for i, q in enumerate(args.query):
            label = "q%02d" % (i + 1)
            log("[Q] %s: %s" % (label, q))
            Q.submit_search(label, q, data_dir, "%s.txt" % label)
            task_count += 1

    if args.query_file:
        qf = Path(args.query_file)
        if qf.exists():
            for line in qf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" in line:
                    label, query = line.split("|", 1)
                    label, query = label.strip(), query.strip()
                else:
                    label = "f%02d" % task_count
                    query = line
                log("[Q] %s: %s" % (label, query))
                Q.submit_search(label, query, data_dir, "%s.txt" % label)
                task_count += 1

    # 2. 百科任务
    if args.baike:
        log("[Q] baike: %s" % company)
        Q.submit_baike(company, data_dir)
        task_count += 1

    # 3. URL抓取任务
    if args.fetch_url:
        for i, url in enumerate(args.fetch_url):
            label = "u%02d" % (i + 1)
            log("[Q] %s: %s" % (label, url[:80]))
            Q.submit_fetch(label, url, data_dir, "%s.txt" % label)
            task_count += 1

    if args.fetch_file:
        uf = Path(args.fetch_file)
        if uf.exists():
            for line in uf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" in line:
                    label, url = line.split("|", 1)
                    label, url = label.strip(), url.strip()
                else:
                    label = "u%02d" % task_count
                    url = line
                log("[Q] %s: %s" % (label, url[:80]))
                Q.submit_fetch(label, url, data_dir, "%s.txt" % label)
                task_count += 1

    if task_count == 0:
        log("No tasks specified. Use --query / --query-file / --baike / --fetch-url / --fetch-file")
        return

    # 打印计划
    print("\n" + "=" * 60)
    print("  OSINT v7.1 | Data Collection (百度+百科+WebFetch)")
    print("  Target: %s" % company)
    print("  Tasks: %d | Concurrency: ≤%d | Output: %s" % (task_count, MAX_CONCURRENT, data_dir))
    print("  Time: %s" % datetime.now().strftime('%Y-%m-%d %H:%M'))
    print("=" * 60 + "\n")

    # 执行（全局排队）
    Q.wait_all()

    # PDF
    if args.pdf:
        generate_pdf_report(company, data_dir)

    # 统计
    rc = len(list((data_dir / "raw").glob("*.txt")))
    ok = len(Q.results.keys())
    err = len(Q.errors.keys())
    print("\n" + "=" * 60)
    print("DONE! Files: %d | OK: %d | Errors: %d | Data: %s/raw/" % (rc, ok, err, data_dir))
    if Q.errors:
        for k, v in Q.errors.items():
            log("  ✗ %s: %s" % (k, v), "ERR")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
