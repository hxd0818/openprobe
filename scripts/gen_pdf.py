#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenProbe PDF生成器 — 基于reportlab的可靠MD→PDF转换
用法: python3 gen_pdf.py <report.md> [output.pdf]
依赖: pip install reportlab fontTools
字体: 自动从系统提取wqy-microhei.ttc → TTF
"""

import re, os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

# ========== 字体初始化 ==========
FONT_TTF = '/tmp/wqy-microhei.ttf'
FONT_SRC = '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc'

if not os.path.exists(FONT_TTF):
    from fontTools.ttLib import TTFont as FTool
    _f = FTool(FONT_SRC, fontNumber=0)
    _f.save(FONT_TTF)

pdfmetrics.registerFont(TTFont('WQY', FONT_TTF))

# ========== 样式定义 ==========
S = getSampleStyleSheet()
S.add(ParagraphStyle(name='H1C', fontName='WQY', fontSize=17, leading=24,
    textColor=colors.HexColor('#1565C0'), alignment=TA_CENTER, spaceAfter=8))
S.add(ParagraphStyle(name='H2S', fontName='WQY', fontSize=13, leading=18,
    textColor=colors.HexColor('#1565C0'), spaceBefore=14, spaceAfter=6))
S.add(ParagraphStyle(name='H3S', fontName='WQY', fontSize=11, leading=15,
    textColor=colors.HexColor('#333333'), spaceBefore=10, spaceAfter=4))
S.add(ParagraphStyle(name='Body', fontName='WQY', fontSize=9.5, leading=15,
    spaceBefore=2, spaceAfter=2))
S.add(ParagraphStyle(name='Quote', fontName='WQY', fontSize=9, leading=13,
    textColor=colors.HexColor('#555555'), leftIndent=12, spaceBefore=3, spaceAfter=3))
S.add(ParagraphStyle(name='CodeB', fontName='WQY', fontSize=7.5, leading=10,
    textColor=colors.HexColor('#666666'), backColor=colors.HexColor('#f5f5f5'),
    leftIndent=6, spaceBefore=2, spaceAfter=2))

# ========== 解析Markdown → ReportLab Elements ==========
def _safe_bold(text):
    """将 **text** 转为 <b>text</b>，同时安全转义其余HTML特殊字符"""
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    parts = re.split(r'(</?b>)', t)
    out = []
    for p in parts:
        if p in ('<b>', '</b>'):
            out.append(p)
        else:
            out.append(p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    return ''.join(out)


def md_to_elements(md_path):
    """将Markdown文件解析为ReportLab可渲染元素列表"""
    md_text = open(md_path, encoding='utf-8').read()
    lines = md_text.split('\n')
    story = []
    in_code = False
    code_buf = []
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if len(table_rows) >= 2:
            clean_rows = []
            for row in table_rows:
                clean_row = [re.sub(r'\*\*(.+?)\*\*', r'\1', c).replace('|', '')[:40] for c in row]
                clean_rows.append(clean_row)
            try:
                t = Table(clean_rows, repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'WQY'),
                    ('FONTSIZE', (0,0), (-1,-1), 7.5),
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8e8e8')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#999999')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f7f7')]),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t)
                story.append(Spacer(1, 4))
            except Exception as e:
                print(f"[WARN] Table render error: {e}")
        table_rows = []

    for line in lines:
        line = line.rstrip()

        # Code block
        if line.startswith('```'):
            if in_code and code_buf:
                flush_table()
                story.append(Paragraph('<br/>'.join(code_buf), S['CodeB']))
                code_buf = []
            in_code = not in_code
            continue

        if in_code:
            code_buf.append(line.replace('<', '&lt;').replace('>', '&gt;'))
            continue

        # Flush pending table on non-table content
        if table_rows and not line.startswith('|'):
            flush_table()

        # HR
        if line.strip() == '---':
            story.append(Spacer(1, 4))
            continue

        # H1
        if line.startswith('# ') and not line.startswith('## '):
            flush_table()
            t = _safe_bold(line[2:].strip())
            story.append(Paragraph(t, S['H1C']))
            continue

        # H2
        if line.startswith('## '):
            flush_table()
            t = _safe_bold(line[3:].strip())
            story.append(Paragraph(t, S['H2S']))
            continue

        # H3
        if line.startswith('### '):
            flush_table()
            t = _safe_bold(line[4:].strip())
            story.append(Paragraph(t, S['H3S']))
            continue

        # Table row
        if line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if cells and all(set(c) <= set('- :') for c in cells):
                continue  # separator
            table_rows.append(cells)
            continue

        # Blockquote
        if line.startswith('> '):
            t = _safe_bold(line[2:])
            story.append(Paragraph(t, S['Quote']))
            continue

        # Body text
        if line.strip():
            clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            # 先保护<b>标签，再转义其余HTML特殊字符，最后恢复<b>
            clean = clean.replace('&', '&amp;')
            _bold_parts = []
            for part in re.split(r'(</?b>)', clean):
                if part in ('<b>', '</b>'):
                    _bold_parts.append(part)
                else:
                    _bold_parts.append(part.replace('<', '&lt;').replace('>', '&gt;'))
            clean = ''.join(_bold_parts)
            story.append(Paragraph(clean, S['Body']))
        else:
            story.append(Spacer(1, 3))

    flush_table()
    return story


# ========== 主入口 ==========
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gen_pdf.py <report.md> [output.pdf]")
        sys.exit(1)

    md_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else md_path.rsplit('.', 1)[0] + '.pdf'

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )

    elements = md_to_elements(md_path)
    doc.build(elements)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"PDF generated: {out_path} ({size_kb:.0f}KB)")


if __name__ == '__main__':
    main()
