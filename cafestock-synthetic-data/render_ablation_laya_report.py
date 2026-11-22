"""Render the measured ablation report using the bundled ReportLab runtime."""
from pathlib import Path
import csv
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'reports/ablation_forecast_laya/report.md'
TARGET = ROOT / 'output/pdf/laporan_ablation_prediksi_bahan_laya.pdf'


def markup(text):
    text = escape(text).replace('–', '-').replace('—', '-').replace('→', '-&gt;')
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#CFDCD8'))
    canvas.line(42, 38, A4[0]-42, 38)
    canvas.setFillColor(colors.HexColor('#536861'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(42, 25, 'CAFESTOCK INTELLIGENCE | Eksperimen retrospektif | 8 November 2026')
    canvas.drawRightString(A4[0]-42, 25, str(doc.page))
    canvas.restoreState()


def comparison_chart():
    with (SOURCE.parent / 'metrics_per_ingredient.csv').open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['split'] == 'test']
    ids = sorted({int(r['ingredient_id']) for r in rows})
    values = {(int(r['ingredient_id']), r['version']): float(r['mae']) for r in rows}
    drawing = Drawing(510, 240)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 38, 58, 460, 150
    chart.data = [[values[i, v]/values[i, 'A'] for i in ids] for v in 'ABCD']
    chart.categoryAxis.categoryNames = [str(i) for i in ids]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(max(v) for v in chart.data)*1.15
    chart.valueAxis.labelTextFormat = '%.1f'
    chart.valueAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontSize = 8
    palette = ['#8B9690', '#3B7A9E', '#D49B43', '#25694F']
    for n, color in enumerate(palette):
        chart.bars[n].fillColor = colors.HexColor(color)
        chart.bars[n].strokeColor = None
        drawing.add(String(80+n*100, 224, 'Versi '+ 'ABCD'[n], fontName='Helvetica',
                           fontSize=9, fillColor=colors.HexColor(color)))
    drawing.add(chart)
    drawing.add(String(145, 36, 'ID bahan (nama pada tabel hasil)', fontSize=9))
    drawing.add(String(38, 12, 'Rasio MAE terhadap A: nilai < 1 lebih baik; baseline A = 1.', fontSize=9))
    return drawing


def run():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', fontName='Helvetica-Bold', fontSize=21,
                             leading=25, textColor=colors.HexColor('#173F35'), spaceAfter=15))
    styles.add(ParagraphStyle(name='ReportBody', fontName='Helvetica', fontSize=9.5,
                             leading=14, spaceAfter=8))
    styles.add(ParagraphStyle(name='ReportSection', fontName='Helvetica-Bold', fontSize=12,
                             leading=16, textColor=colors.HexColor('#173F35'), spaceBefore=13,
                             spaceAfter=7, keepWithNext=True))
    styles.add(ParagraphStyle(name='Cell', fontName='Helvetica', fontSize=7,
                             leading=9.2, alignment=TA_LEFT))
    story = []
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    i = 0
    code = False
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            code = not code
            i += 1
            continue
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [v.strip() for v in lines[i].strip('|').split('|')]
                if not all(re.fullmatch('[-: ]+', v) for v in cells):
                    rows.append(cells)
                i += 1
            n = len(rows[0])
            width = A4[0] - 84
            widths = ({2: [45, width-45], 4: [60, 40, (width-100)/2, (width-100)/2],
                       9: [83, 48, 49, 49, 49, 49, 65, 59, width-551]}.get(n))
            # Keep all numeric columns wide enough on portrait A4.
            if n == 9:
                widths = [78, 43] + [(width-121)/7]*7
            table = Table([[Paragraph(markup('Satuan' if c == 'Satuan/hari' else c), styles['Cell']) for c in row] for row in rows],
                          colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#DFECE5')),
                ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, colors.HexColor('#F4F7F5')]),
                ('VALIGN', (0,0),(-1,-1), 'TOP'),
                ('LINEBELOW', (0,0),(-1,0), .6, colors.HexColor('#91AEA0')),
                ('BOTTOMPADDING', (0,0),(-1,-1), 7), ('TOPPADDING', (0,0),(-1,-1), 7),
                ('LEFTPADDING', (0,0),(-1,-1), 5), ('RIGHTPADDING', (0,0),(-1,-1), 5)]))
            story += [table, Spacer(1, 9)]
            continue
        if line.startswith('# '):
            story.append(Paragraph(markup(line[2:]), styles['ReportTitle']))
        elif line.startswith('## '):
            story.append(Paragraph(markup(line[3:]), styles['ReportSection']))
            if line == '## Interpretasi':
                story.append(comparison_chart())
                with (SOURCE.parent / 'metrics_per_ingredient.csv').open(encoding='utf-8', newline='') as stream:
                    names = sorted((int(r['ingredient_id']), r['ingredient']) for r in csv.DictReader(stream)
                                   if r['split'] == 'test' and r['version'] == 'A')
                story.append(Paragraph('; '.join(f'{i}: {escape(name)}' for i, name in names), styles['ReportBody']))
                story.append(Paragraph('Pembanding rata-rata konsumsi historis 14 hari', styles['ReportSection']))
                with (SOURCE.parent / 'metrics_per_ingredient.csv').open(encoding='utf-8', newline='') as stream:
                    baseline_rows = [r for r in csv.DictReader(stream) if r['split'] == 'test' and r['version'] == 'D']
                comparison = [['Bahan', 'MAE historis', 'MAE versi D']]
                comparison += [[r['ingredient'], f"{float(r['historical_mae']):.3f}", f"{float(r['mae']):.3f}"] for r in baseline_rows]
                t = Table([[Paragraph(escape(c), styles['Cell']) for c in row] for row in comparison],
                          colWidths=[250, 130, A4[0]-84-380], repeatRows=1)
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFECE5')),
                                      ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
                                      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7F5')])]))
                story += [t, Spacer(1, 10)]
        elif line.startswith('- '):
            story.append(Paragraph(markup(line[2:]), styles['ReportBody'], bulletText='-'))
        else:
            story.append(Paragraph(markup(line), styles['ReportBody']))
        i += 1
    SimpleDocTemplate(str(TARGET), pagesize=A4, leftMargin=42, rightMargin=42,
                      topMargin=42, bottomMargin=52, title='Ablation Prediksi Kebutuhan Bahan - Laya',
                      author='CafeStock Intelligence').build(story, onFirstPage=footer, onLaterPages=footer)
    print(TARGET)


if __name__ == '__main__':
    run()
