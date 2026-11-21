"""charts.py (engine v1.3, from the real-estate kits' charts_kit.py) — the «Charts» sheet (v3, 2026-11-07: «ركز على الجداول والرسوم البيانية والمؤشرات … يتفوق
على المنافسين بأضعاف»). Live charts in a two-column grid (as many as the work needs), each fed by a small table of formulas at the right of the sheet
(«The numbers behind the charts»), plus the visual indicators (data bars, colour scales) the data sheets use.
Rules learnt the hard way, kept here so they are never broken again:
- every axis is set delete=False (openpyxl 3.1 otherwise hides the axes in current Excel);
- a chart reads only visible cells (Excel skips hidden rows/columns), so its numbers stay visible beside it;
- category labels come from the Lists or the data sheets by formula, never typed, so every language works;
- colours are fixed per meaning (money in, money out, net, warning) across both workbooks."""
from openpyxl.chart import BarChart, LineChart, PieChart, DoughnutChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.drawing.line import LineProperties
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

NAVY, GOLD, GREEN, RED, TEAL, PLUM, SKY, SAND, SLATE = '1F3A5F', 'C9962B', '2E8B57', 'C0504D', '1B8A9A', '7A5AA8', '5B9BD5', 'E8C872', '8A94A6'
PALETTE = [NAVY, GOLD, TEAL, RED, PLUM, GREEN, SKY, SAND, SLATE, '9C6644', '4F6D7A', 'B5838D']
thin = Side(style='thin', color='D5DAE1'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
fill = lambda c: PatternFill('solid', start_color=c, end_color=c)
ACC = Alignment(horizontal='center', vertical='center', wrap_text=True)
CW, CH = 17.2, 8.6     # chart size in cm
ROWS_PER = 19          # rows between chart tops (rows of 15 pt)


def _axes(ch, num='#,##0'):
    for ax in (ch.x_axis, ch.y_axis):
        ax.delete = False
    ch.y_axis.numFmt = num; ch.y_axis.majorGridlines = None
    ch.legend.position = 'b'
    return ch


def _labels(val=False, pct=False):
    d = DataLabelList(); d.showVal = val; d.showPercent = pct; d.showCatName = False; d.showSerName = False; d.showLegendKey = False; d.showLeaderLines = False
    return d


def _color(s, c, line=False):
    if line:
        s.graphicalProperties.line.solidFill = c; s.graphicalProperties.line.width = 28000; s.smooth = False
        s.marker.symbol = 'circle'; s.marker.size = 6; s.marker.graphicalProperties = GraphicalProperties(solidFill=c); s.marker.graphicalProperties.line.solidFill = c
    else:
        s.graphicalProperties.solidFill = c; s.graphicalProperties.line.solidFill = c


class Sheet:
    """A charts sheet: data blocks at column `dc` (stacked downwards) and charts in two columns at B and L."""
    def __init__(self, ws, font, title, hint, data_title, dc=24):
        self.ws, self.F, self.dc, self.dr, self.n, self.top = ws, font, dc, 6, 0, 6; self.anchors = []
        ws.sheet_view.showGridLines = False
        ws['B1'] = title; ws['B1'].font = font(size=22, bold=True, color=NAVY)
        ws['B2'] = hint; ws['B2'].font = font(size=10, color='6B7280')
        for c in range(1, dc - 1): ws.column_dimensions[get_column_letter(c)].width = 8.6
        ws.column_dimensions['A'].width = 2
        h = ws.cell(4, dc, data_title); h.font = font(size=13, bold=True, color=NAVY)

    def block(self, title, heads, rows, fmts):
        """rows: list of lists of formulas; returns (first data row, last data row) of the block."""
        ws, c0, r0 = self.ws, self.dc, self.dr
        ws.cell(r0, c0, title).font = self.F(size=10, bold=True, color=NAVY)
        for j, h in enumerate(heads):
            x = ws.cell(r0 + 1, c0 + j, h); x.font = self.F(bold=True, color='FFFFFF', size=9); x.fill = fill(NAVY); x.alignment = ACC; x.border = BOX
            ws.column_dimensions[get_column_letter(c0 + j)].width = 16 if j == 0 else 13
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                x = ws.cell(r0 + 2 + i, c0 + j, v); x.font = self.F(size=9); x.alignment = ACC; x.border = BOX
                if fmts[j]: x.number_format = fmts[j]
        self.dr = r0 + 2 + len(rows) + 2
        return r0 + 2, r0 + 1 + len(rows)

    def ref(self, col, r1, r2, head=True):
        return Reference(self.ws, min_col=self.dc + col, min_row=r1 - (1 if head else 0), max_row=r2)

    def place(self, ch):
        slot = self.n; self.n += 1
        ch.width, ch.height = CW, CH
        at = (f'{"B" if slot % 2 == 0 else "L"}', self.top + (slot // 2) * ROWS_PER); self.anchors.append(at)
        self.ws.add_chart(ch, f'{at[0]}{at[1]}')

    # ---- chart makers
    def bars(self, title, rr, series, colors, horizontal=False, stacked=False, line=None, num='#,##0', labels=False):
        r1, r2 = rr; ch = BarChart(); ch.type = 'bar' if horizontal else 'col'; ch.title = title; ch.style = 10
        ch.grouping = 'stacked' if stacked else 'clustered'
        if stacked: ch.overlap = 100
        ch.gapWidth = 60
        for j, c in zip(series, colors):
            ch.add_data(self.ref(j, r1, r2), titles_from_data=True); _color(ch.series[-1], c)
        ch.set_categories(self.ref(0, r1, r2, head=False)); _axes(ch, num)
        if labels: ch.dataLabels = _labels(val=True)
        if len(series) == 1 and line is None: ch.legend = None
        ch.x_axis.tickLblPos = 'low'
        if line is not None:
            j, c = line; ln = LineChart(); ln.add_data(self.ref(j, r1, r2), titles_from_data=True); _color(ln.series[-1], c, line=True)
            ln.y_axis.axId = ch.y_axis.axId
            ch += ln
        if horizontal: ch.x_axis.scaling.orientation = 'maxMin'; ch.y_axis.crosses = 'max'
        self.place(ch); return ch

    def ring(self, title, rr, col=1, doughnut=True):
        r1, r2 = rr; ch = DoughnutChart(holeSize=55) if doughnut else PieChart(); ch.title = title; ch.style = 10
        ch.add_data(self.ref(col, r1, r2), titles_from_data=True); ch.set_categories(self.ref(0, r1, r2, head=False))
        s = ch.series[0]
        for i in range(r2 - r1 + 1):
            p = DataPoint(idx=i); p.graphicalProperties.solidFill = PALETTE[i % len(PALETTE)]; p.graphicalProperties.line.solidFill = 'FFFFFF'; s.dPt.append(p)
        ch.dataLabels = _labels(pct=True)
        ch.legend.position = 'r'
        self.place(ch); return ch


# ---- indicators on the data sheets
def databar(ws, rng, color=NAVY):
    ws.conditional_formatting.add(rng, DataBarRule(start_type='num', start_value=0, end_type='max', color=color, showValue=True))


def scale3(ws, rng, low='F8696B', mid='FFFFFF', high='63BE7B', mid_value=None):
    if mid_value is None:
        ws.conditional_formatting.add(rng, ColorScaleRule(start_type='min', start_color=low, mid_type='percentile', mid_value=50, mid_color=mid, end_type='max', end_color=high))
    else:
        ws.conditional_formatting.add(rng, ColorScaleRule(start_type='min', start_color=low, mid_type='num', mid_value=mid_value, mid_color=mid, end_type='max', end_color=high))
