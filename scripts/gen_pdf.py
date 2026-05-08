#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenProbe PDF生成器 v2 — 基于reportlab的可靠MD→PDF转换
v2变更：表格自适应宽度（列宽智能分配+横向模式+自动换行+去除硬截断）

用法: python3 gen_pdf.py <report.md> [output.pdf]
依赖: pip install reportlab fontTools
字体: 自动从系统提取wqy-microhei.ttc → TTF
"""

import re, os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ========== 字体初始化 ==========
FONT_TTF = '/tmp/wqy-microhei.ttf'
FONT_SRC = '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc'

if not os.path.exists(FONT_TTF):
    from fontTools.ttLib import TTFont as FTool
    _f = FTool(FONT_SRC, fontNumber=0)
    _f.save(FONT_TTF)

pdfmetrics.registerFont(TTFont('WQY', FONT_TTF))

# ========== 页面参数 ==========
A4_W, A4_H = A4  # 595.28 x 841.89 pt
LANDSCAPE_W, LANDSCAPE_H = landscape(A4)  # 841.89 x 595.28 pt
MARGIN = 16 * mm  # 左右边距
BODY_WIDTH_PORTRAIT = A4_W - 2 * MARGIN   # ~559pt 可用宽度
BODY_WIDTH_LANDSCAPE = LANDSCAPE_W - 2 * MARGIN  # ~806pt 可用宽度

# 横向切换阈值：当估算的表格最小需要宽度超过此值时用横向
LANDSCAPE_THRESHOLD = BODY_WIDTH_PORTRAIT * 0.85  # ~475pt

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

# 表格单元格样式（用于支持自动换行）
S.add(ParagraphStyle(name='TableCell', fontName='WQY', fontSize=7.5, leading=10,
    textColor=colors.HexColor('#333333'), alignment=TA_LEFT,
    wordWrap='CJK'))  # CJK自动换行

S.add(ParagraphStyle(name='TableHeader', fontName='WQY', fontSize=7.5, leading=10,
    textColor=colors.HexColor('#ffffff'), alignment=TA_CENTER,
    wordWrap='CJK'))

S.add(ParagraphStyle(name='TableCellSmall', fontName='WQY', fontSize=7, leading=9,
    textColor=colors.HexColor('#333333'), alignment=TA_LEFT, wordWrap='CJK'))

# ========== 表格工具函数 ==========

def _estimate_text_width(text, font_size=7.5):
    """估算文本渲染宽度（中文字符≈1em，英文≈0.55em）"""
    if not text:
        return 0
    cjk_count = len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f]', text))
    ascii_count = len(text) - cjk_count
    return (cjk_count * font_size) + (ascii_count * font_size * 0.55)


def _calc_col_widths(rows, available_width, min_col_width=28*mm, max_col_width=None):
    """
    智能计算列宽：
    - 扫描每列最长内容，按比例分配可用宽度
    - 每列有最小宽度保障
    - 超宽表格返回None（表示需要横向模式）
    """
    if not rows or len(rows[0]) == 0:
        return []

    ncols = len(rows[0])
    
    # 计算每列的最大内容宽度估算值
    col_max_widths = []
    for ci in range(ncols):
        max_w = 0
        for row in rows:
            if ci < len(row):
                w = _estimate_text_width(row[ci], font_size=7.5)
                max_w = max(max_w, w)
        # 表头加成（表头通常更重要）
        if len(rows) > 0 and ci < len(rows[0]):
            header_w = _estimate_text_width(rows[0][ci], font_size=7.5)
            max_w = max(max_w, header_w * 1.1)
        col_max_widths.append(max_w)

    total_estimated = sum(col_max_widths)
    
    # 如果总估算宽度超过可用宽度很多，可能需要横向
    if total_estimated > available_width * 1.8 and ncols >= 5:
        return None  # 信号：建议使用横向
    
    # 按比例分配
    if total_estimated > 0:
        ratios = [w / total_estimated for w in col_max_widths]
    else:
        ratios = [1.0 / ncols] * ncols
    
    raw_widths = [r * available_width for r in ratios]
    
    # 应用最小宽度约束，并重新分配剩余空间
    final_widths = []
    deficit = 0
    for i, rw in enumerate(raw_widths):
        if rw < min_col_width:
            deficit += (min_col_width - rw)
            final_widths.append(min_col_width)
        else:
            final_widths.append(rw)
    
    # 将被约束列多出的空间重新分配给其他列
    if deficit > 0:
        flexible = [(i, w) for i, w in enumerate(final_widths) if w > min_col_width]
        if flexible:
            per_extra = deficit / len(flexible)
            for i, _ in flexible:
                final_widths[i] += per_extra
    
    return final_widths


def _make_paragraph_cell(text, style_name='TableCell'):
    """将文本转为Paragraph以支持自动换行"""
    clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', str(text))
    # 安全转义HTML（保护b标签）
    parts = re.split(r'(</?b>)', clean)
    out = []
    for p in parts:
        if p in ('<b>', '</b>'):
            out.append(p)
        else:
            out.append(p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    return Paragraph(''.join(out), S[style_name])


def _build_table(table_rows, body_width):
    """
    构建自适应表格：
    - 自动检测是否需要横向模式
    - 列宽智能分配
    - 单元格内容自动换行（Paragraph包装）
    - 表头深色背景+白字
    """
    if len(table_rows) < 2:
        return None, False

    ncols = len(table_rows[0])
    
    # 清理数据：去除markdown格式符，但保留完整内容（不再截断！）
    clean_rows = []
    for ri, row in enumerate(table_rows):
        clean_row = []
        for ci, cell in enumerate(row):
            c = re.sub(r'\*\*(.+?)\*\*', r'\1', cell).strip()
            clean_row.append(c)
        # 补齐缺失列
        while len(clean_row) < ncols:
            clean_row.append('')
        clean_rows.append(clean_row[:ncols])

    # 先尝试纵向模式的列宽计算
    col_widths = _calc_col_widths(clean_rows, body_width)
    
    use_landscape = False
    actual_body_width = body_width
    actual_page_size = A4
    
    if col_widths is None:
        # 需要横向模式
        use_landscape = True
        actual_body_width = BODY_WIDTH_LANDSCAPE
        col_widths = _calc_col_widths(clean_rows, actual_body_width)
        if col_widths is None:
            # 即使横向也放不下，强制按比例压缩到横向宽度
            col_widths = [actual_body_width / ncols] * ncols
    
    # 如果列数过多或单列内容过长导致总宽超限，二次调整
    if col_widths and sum(col_widths) > actual_body_width * 1.05:
        scale = actual_body_width / sum(col_widths)
        col_widths = [w * scale for w in col_widths]

    # 将所有单元格转为Paragraph（支持自动换行）
    is_header = True
    para_rows = []
    for ri, row in enumerate(clean_rows):
        if ri == 0:
            para_rows.append([_make_paragraph_cell(c, 'TableHeader') for c in row])
        else:
            # 根据列宽决定字体大小（窄列用小字）
            para_rows.append([
                _make_paragraph_cell(c, 'TableCellSmall' if (col_widths and col_widths[ci] < 35*mm) else 'TableCell')
                for ci, c in enumerate(row)
            ])

    try:
        t = Table(para_rows, colWidths=col_widths, repeatRows=1)
        
        base_style = [
            ('FONTNAME', (0,0), (-1,-1), 'WQY'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1976D2')),  # 表头深蓝底白字
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bbbbbb')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),  # 表头居中
        ]
        t.setStyle(TableStyle(base_style))
        return t, use_landscape
        
    except Exception as e:
        print(f"[WARN] Table render error: {e}")
        return None, False


# ========== 解析Markdown → ReportLab Elements ==========
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
            t, use_landscape = _build_table(table_rows, BODY_WIDTH_PORTRAIT)
            if t:
                story.append(t)
                story.append(Spacer(1, 4))
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

        # # H3
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


# ========== 主入口 ==========
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gen_pdf.py <report.md> [output.pdf]")
        sys.exit(1)

    md_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else md_path.rsplit('.', 1)[0] + '.pdf'

    # 第一遍扫描：检查是否有需要横向的大表
    # （简单策略：如果表格列数>=6，默认用横向页面）
    md_text = open(md_path, encoding='utf-8').read()
    has_wide_table = False
    for line in md_text.split('\n'):
        if line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 6:
                has_wide_table = True
                break

    # 选择页面尺寸
    if has_wide_table:
        page_size = landscape(A4)
        body_width = BODY_WIDTH_LANDSCAPE
    else:
        page_size = A4
        body_width = BODY_WIDTH_PORTRAIT

    doc = SimpleDocTemplate(
        out_path,
        pagesize=page_size,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16*mm, bottomMargin=16*mm
    )

    elements = md_to_elements(md_path)
    doc.build(elements)

    size_kb = os.path.getsize(out_path) / 1024
    orientation = "Landscape" if has_wide_table else "Portrait"
    print(f"PDF generated: {out_path} ({size_kb:.0f}KB, {orientation})")


if __name__ == '__main__':
    main()
