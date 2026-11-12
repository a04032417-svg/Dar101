#!/usr/bin/env python3
"""build(spec, lang, out_path, demo=False) — one workbook of a spec in one language.
Start (title, guide, settings, contents, colour key) · Dashboard (year, KPI cards, months + bar chart, breakdowns) · one sheet per
table (typed columns, drop-downs, calc columns on every prepared row, alerts) · printable forms · Lists. Formulas never contain a
translated word: list labels and settings are cell references, so every language computes the same numbers.
raw=True leaves out the IFERROR safety wrappers (verify uses it to find the exact cause of a hidden error).
CLI: python3 build.py spec.json <lang> <out.xlsx> [--demo] [--raw] [--today YYYY-MM-DD]   (also writes <out.xlsx>.meta.json)"""
import sys, os, json, math, unicodedata, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (RTL, FIXED, YESNO, STEPSTAT, NUMFMT, PH, TOK, tr, normalize, substitute, find_col, col_format, main_date, first_required,
                    record_key, series_date, brand_setting, sheet_names, parse_date, parse_time, list_by_key)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.formatting.rule import FormulaRule, DataBarRule, ColorScaleRule
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter as CL
from openpyxl.workbook.properties import CalcProperties

INK, GRAY, AUTO, LINE, CREAM, CARD, BLUE = '1A1A1A', '6B7280', 'EEF1F5', 'D5DAE1', 'FFF8E1', 'F4F6FA', '1F4FBF'
STYLE = {'bad': ('FDE2E1', '9B1C1C'), 'warn': ('FFF1C2', '7A4B00'), 'good': ('DDF3E4', '1E6B3A')}
TABS = ['2E6DB4', '2E8B57', '7A5AA8', 'C0504D', 'D97706', '1B8A9A', '8A6D3B', '41597A', '6B7280', '0F766E', 'B45309', '6D28D9', 'BE123C', '334155']
WIDTH = {'text': 22, 'link': 26, 'date': 12, 'time': 9, 'int': 9, 'num': 11, 'money': 13, 'pct': 9, 'list': 16, 'ref': 22, 'bool': 9}
CWIDTH = {'money': 13, 'date': 12, 'int': 10, 'num': 11, 'pct': 9, 'text': 18, 'hours': 9, 'time': 9}
FIRST = 5
fill = lambda c: PatternFill('solid', start_color=c, end_color=c)
thin = Side(style='thin', color=LINE); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
X = lambda s: '"' + str(s).replace('"', '""') + '"'


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (0, 2, 4)]; pb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return ''.join(f'{round(x + (y - x) * t):02X}' for x, y in zip(pa, pb))


def vlen(s):
    """Visual length of a text (wide East Asian characters count twice)."""
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in str(s))


def lines(s, width):
    return max(1, math.ceil(vlen(s) * 1.08 / max(1, width - 1)))


class Builder:
    def __init__(self, spec, lang, demo=False, raw=False, today=None):
        self.s, self.lang, self.demo, self.raw = spec, lang, demo, raw
        self.T = tr(spec, lang); self.today = today or dt.date.today(); self.rtl = lang in RTL
        self.P = spec['colors']['primary'].lstrip('#').upper(); self.A = spec['colors']['accent'].lstrip('#').upper()
        self.PC = mix(self.P, '7A8699', 0.45)
        self.meta = {'lang': lang, 'demo': demo, 'raw': raw, 'today': self.today.isoformat(), 'origin': {}, 'dsl': {}, 'calc_cols': [], 'kpis': [],
                     'tables': {}, 'forms': {}, 'form_fields': [], 'tool_cells': [], 'tools': {}, 'checks': [], 'checklists': {}, 'msg_cols': [],
                     'documents': {}, 'doc_cells': [], 'widths': {}, 'charts': [], 'gauges': []}
        self.wb = Workbook(); self.wb.remove(self.wb.active)
        self.names = dict(sheet_names(spec, self.T)); self.ws = {}
        for sid, n in sheet_names(spec, self.T):
            w = self.wb.create_sheet(n); self.ws[sid] = w
            w.sheet_view.rightToLeft = self.rtl; w.sheet_view.showGridLines = False; w.sheet_view.zoomScale = 110
        self.meta['sheets'] = self.names
        self.tables = {t['key']: t for t in spec['tables']}
        self.let = {t['key']: {c['key']: CL(i + 1) for i, c in enumerate(t['columns'])} for t in spec['tables']}
        self.last = {t['key']: FIRST + t['rows'] - 1 for t in spec['tables']}
        # Lists sheet layout: one column per list, the built-in Yes/No last
        self.lists = list(spec['lists']) + [list_by_key(spec, YESNO)] + ([list_by_key(spec, STEPSTAT)] if spec.get('checklists') else [])
        self.lcol = {l['key']: CL(i + 1) for i, l in enumerate(self.lists)}
        # Start sheet layout
        self.r_how = 5; self.r_steps = 6; self.r_set = self.r_steps + len(spec['guide']) + 1
        self.setrow = {x['key']: self.r_set + 1 + i for i, x in enumerate(spec['settings'])}
        # WhatsApp message columns: visible link columns right after a table's columns, then hidden helpers (phone digits, url)
        self.msg_layout = {}
        for t in spec['tables']:
            ms = [m for m in spec.get('messages', []) if m['table'] == t['key']]
            n = len(t['columns']); links = {m['key']: CL(n + 1 + i) for i, m in enumerate(ms)}; nxt = n + 1 + len(ms)
            phones = {}
            for m in ms:
                if m['phone'] not in phones: phones[m['phone']] = CL(nxt); nxt += 1
            urls = {}
            for m in ms: urls[m['key']] = CL(nxt); nxt += 1
            self.msg_layout[t['key']] = {'msgs': ms, 'links': links, 'phones': phones, 'urls': urls, 'next': nxt}
        self.msgrow = {m['key']: 5 + i for i, m in enumerate(spec.get('messages', []))}

    # ---------- references
    def Q(self, sid): return "'" + self.names[sid].replace("'", "''") + "'"
    def RG(self, t, c): L = self.let[t][c]; return f"{self.Q('t:' + t)}!${L}${FIRST}:${L}${self.last[t]}"
    def SET(self, k): return f"{self.Q('start')}!$C${self.setrow[k]}"
    def LI(self, l, v):
        L = list_by_key(self.s, l); j = [x['key'] for x in L['values']].index(v)
        return f"{self.Q('lists')}!${self.lcol[l]}${4 + j}"
    def LR(self, l):
        n = len(list_by_key(self.s, l)['values']); c = self.lcol[l]
        return f"{self.Q('lists')}!${c}$4:${c}${3 + n}"
    def res(self, f, table=None, row=None, pick=None, col_abs=False, mirror=None, ins=None):
        """DSL -> Excel formula text (without '=')."""
        def fn(kind, arg):
            if kind == 'in': return ins[arg]
            if kind == 'col': return (f'${self.let[table][arg]}' if col_abs else self.let[table][arg]) + str(row)
            if kind == 'range': t, c = arg.split('.'); return self.RG(t, c)
            if kind in ('set', 'list') and mirror: return mirror(kind, arg)
            if kind == 'set': return self.SET(arg)
            if kind == 'list': l, v = arg.split('.'); return self.LI(l, v)
            if kind == 'today': return 'TODAY()'
            if kind == 'pick': return pick
        return substitute(normalize(f), fn)
    def safe(self, expr): return expr if self.raw else f'IFERROR({expr},"")'

    # ---------- styles
    def F(self, **k): return Font(name='Arial', **({'size': 10, 'color': INK} | k))
    def AL(self, h=None, v='center', wrap=False, indent=None):
        if h is None: h = 'right' if self.rtl else 'left'
        if indent is None: indent = 1 if h in ('left', 'right') else 0
        return Alignment(horizontal=h, vertical=v, wrap_text=wrap, indent=indent, readingOrder=2 if self.rtl else 0)
    def ALN(self): return Alignment(horizontal='left' if self.rtl else 'right', vertical='center', indent=1, readingOrder=2 if self.rtl else 0)
    def put(self, ws, ref, value, font=None, fill_=None, align=None, fmt=None, border=None):
        c = ws[ref]; c.value = value
        if font: c.font = font
        if fill_: c.fill = fill(fill_)
        c.alignment = align or self.AL()
        if fmt: c.number_format = fmt
        if border: c.border = border
        return c
    def section(self, ws, ref, text): self.put(ws, ref, text, self.F(size=13, bold=True, color=self.P))
    def cf(self, ws, rng, formula, style):
        bg, fg = STYLE[style]
        ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], fill=fill(bg), font=Font(color=fg, bold=True), stopIfTrue=False))
    def dv(self, ws, rng, src):
        d = DataValidation(type='list', formula1='=' + src, allow_blank=True, showErrorMessage=True, errorStyle='warning'); d.add(rng); ws.add_data_validation(d)
    def origin(self, sheet, where, org, dsl=None):
        self.meta['origin'].setdefault(sheet, {})[where] = org
        if dsl is not None: self.meta['dsl'][org] = dsl
    def label_of(self, l, k): return self.T(next(x['label'] for x in list_by_key(self.s, l)['values'] if x['key'] == k))

    # ---------- v1.3: a column as wide as its longest real value (nothing overlaps or is cut, no "####")
    def fit_width(self, t, c, head):
        ty = c['type']; fk = col_format(c)
        base = c.get('width') or (CWIDTH.get(fk, 12) if ty == 'calc' else WIDTH.get(ty, 14))
        words = head.split(); hw = max(max((vlen(x) for x in words), default=4) + 3, vlen(head) / 2 + 3)
        vals = []
        for row in t.get('demo') or []:
            v = row.get(c['key'])
            if v is None or v == '': continue
            if isinstance(v, (int, float)) and not isinstance(v, bool): vals.append(f'{v:,.2f}' if fk == 'money' and v != int(v) else f'{v:,.0f}' if abs(v) >= 1000 else str(v))
            else: vals.append(str(v))
        if ty == 'list':
            L = list_by_key(self.s, c['list']); vals += [self.T(x['label']) for x in L['values']] if L else []
        vw = max((vlen(x) for x in vals), default=0) * 1.12 + 3
        big = 17 if self.lang in ('id',) else 15 if self.lang in ('ur', 'hi', 'fa', 'tr', 'ru') else 13  # money in a large currency
        mw = big if fk == 'money' else 12 if fk == 'date' else 0
        return round(min(46, max(8, base if ty in ('text', 'link', 'ref') else 0, hw, vw, mw)), 1)

    # ---------- demo values
    def demo_value(self, c, v):
        if v is None or v == '': return None
        t = c['type']
        if t == 'list': return self.label_of(c['list'], v)
        if t == 'bool': return self.T(FIXED['yes'] if v in (True, 'yes') else FIXED['no'])
        if t == 'date': return parse_date(v, self.today)
        if t == 'time': return parse_time(v)
        if t == 'ref':
            _, rc = find_col(self.s, c['ref'])
            if rc is not None and rc['type'] == 'list': return self.label_of(rc['list'], v)
            if rc is not None and rc['type'] == 'bool': return self.T(FIXED['yes'] if v in (True, 'yes') else FIXED['no'])
        return v

    # ---------- sheets
    def build(self, out):
        self.lists_sheet(); self.start();
        for i, t in enumerate(self.s['tables']): self.table(t, i)
        self.dashboard()
        if self.s.get('insights'): self.insights()
        for x in self.s.get('tools', []): self.tool(x)
        for f in self.s.get('forms', []): self.form(f)
        for d in self.s.get('documents', []): self.document(d)
        for c in self.s.get('checklists', []): self.checklist(c)
        if self.s.get('messages'): self.messages_sheet()
        ws = self.ws
        ws['start'].sheet_properties.tabColor = self.A; ws['dash'].sheet_properties.tabColor = self.P; ws['lists'].sheet_properties.tabColor = '9AA3AE'
        if 'charts' in ws: ws['charts'].sheet_properties.tabColor = self.P
        for i, t in enumerate(self.s['tables']): ws['t:' + t['key']].sheet_properties.tabColor = TABS[i % len(TABS)]
        for f in self.s.get('forms', []) + self.s.get('documents', []): ws[('f:' if 'fields' in f else 'd:') + f['key']].sheet_properties.tabColor = mix(self.A, '000000', 0.25)
        for x in self.s.get('tools', []): ws['x:' + x['key']].sheet_properties.tabColor = '0F766E'
        for c in self.s.get('checklists', []): ws['c:' + c['key']].sheet_properties.tabColor = '6D28D9'
        if 'msgs' in ws: ws['msgs'].sheet_properties.tabColor = '128C7E'
        self.wb.active = 0
        self.wb.properties.title = self.T(self.s['name']); self.wb.properties.creator = ''; self.wb.properties.language = self.lang
        self.wb.calculation = CalcProperties(fullCalcOnLoad=True)
        self.wb.save(out)
        return self.meta

    def lists_sheet(self):
        ws = self.ws['lists']
        self.put(ws, 'A1', self.names['lists'], self.F(size=16, bold=True, color=self.P))
        self.put(ws, 'A2', self.T(FIXED['lists_hint']), self.F(color=GRAY))
        for l in self.lists:
            c = self.lcol[l['key']]
            self.put(ws, f'{c}3', self.T(l['label']), self.F(bold=True, color='FFFFFF'), self.P, self.AL('center', wrap=True), border=BOX)
            for j, v in enumerate(l['values']): self.put(ws, f'{c}{4 + j}', self.T(v['label']), self.F(), align=self.AL(), border=BOX)
            ws.column_dimensions[c].width = max(18, min(34, max(vlen(self.T(v['label'])) for v in l['values']) + 3))
        ws.row_dimensions[3].height = 32; ws.freeze_panes = 'A4'

    def start(self):
        s, ws, T = self.s, self.ws['start'], self.T
        for c, w in zip('ABCDEF', [3, 46, 22, 16, 16, 16]): ws.column_dimensions[c].width = w
        self.put(ws, 'B1', T(s['name']), self.F(size=24, bold=True, color=self.P)); ws.row_dimensions[1].height = 36
        self.put(ws, 'B2', T(s['tagline']), self.F(size=12, color=GRAY)); ws.row_dimensions[2].height = 20
        for c in 'BCDEF': ws[f'{c}3'].fill = fill(self.A)
        ws.row_dimensions[3].height = 5
        self.section(ws, f'B{self.r_how}', T(FIXED['how']))
        for i, step in enumerate(s['guide']):
            r = self.r_steps + i; txt = f'{i + 1}.  {T(step)}'
            self.put(ws, f'B{r}', txt, self.F(size=11), align=self.AL(v='top', wrap=True)); ws.merge_cells(f'B{r}:F{r}')
            ws.row_dimensions[r].height = 16 * lines(txt, 112) + 6
        self.section(ws, f'B{self.r_set}', T(FIXED['settings']))
        for x in s['settings']:
            r = self.setrow[x['key']]; t = x['type']
            self.put(ws, f'B{r}', T(x['label']), self.F(size=11), align=self.AL(wrap=True))
            v = x['default']; fmt = {'pct': '0.0%', 'money': '#,##0.00', 'int': '0', 'num': '#,##0.00', 'date': 'yyyy-mm-dd', 'text': '@'}.get(t)
            if t == 'list': v = self.label_of(x['list'], v)
            if t == 'date': v = parse_date(v, self.today)
            self.put(ws, f'C{r}', v, self.F(size=11, bold=True, color=BLUE), CREAM, self.ALN() if t not in ('text', 'list') else self.AL(), fmt, BOX)
            if t == 'list': self.dv(ws, f'C{r}', self.LR(x['list']))
            ws.row_dimensions[r].height = max(20, 16 * lines(T(x['label']), 46) + 4)
        r = self.r_set + len(s['settings']) + 2
        self.section(ws, f'B{r}', T(FIXED['inside'])); r += 1
        items = [('dash', T(FIXED['dash_hint']))] + [('t:' + t['key'], T(t['hint'])) for t in s['tables']] + \
                [('x:' + x['key'], T(x['hint'])) for x in s.get('tools', [])] + \
                [('f:' + f['key'], T(FIXED['form_hint'])) for f in s.get('forms', [])] + [('d:' + d['key'], T(FIXED['form_hint'])) for d in s.get('documents', [])] + \
                [('c:' + c['key'], T(FIXED['chk_hint'])) for c in s.get('checklists', [])] + \
                ([('msgs', T(FIXED['msg_hint']))] if s.get('messages') else []) + [('lists', T(FIXED['lists_hint']))]
        for sid, hint in items:
            c = self.put(ws, f'B{r}', self.names[sid], self.F(size=11, bold=True, color=BLUE, underline='single'))
            c.hyperlink = Hyperlink(ref=f'B{r}', location=f"{self.Q(sid)}!A1", display=self.names[sid])
            self.put(ws, f'C{r}', hint, self.F(color=GRAY), align=self.AL(wrap=True)); ws.merge_cells(f'C{r}:F{r}')
            ws.row_dimensions[r].height = max(18, 14 * lines(hint, 68) + 4); r += 1
        r += 1; self.section(ws, f'B{r}', T(FIXED['legend'])); r += 1
        for key, col in (('type_here', 'FFFFFF'), ('calculated', AUTO), ('bad', STYLE['bad'][0]), ('warn', STYLE['warn'][0]), ('good', STYLE['good'][0])):
            self.put(ws, f'B{r}', T(FIXED[key]), self.F(size=11)); ws[f'C{r}'].fill = fill(col); ws[f'C{r}'].border = BOX; r += 1
        self.put(ws, f'B{r + 1}', f'fx1 · {s["id"]} · {self.lang.upper()}', self.F(size=8, color=GRAY))
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True

    def table(self, t, idx):
        s, T, k = self.s, self.T, t['key']; sid = 't:' + k; ws = self.ws[sid]; last = self.last[k]; let = self.let[k]
        name = self.names[sid]
        self.put(ws, 'A1', T(t['title']), self.F(size=18, bold=True, color=self.P)); ws.row_dimensions[1].height = 30
        self.put(ws, 'A2', T(t['hint']), self.F(color=GRAY)); ws.row_dimensions[3].height = 6
        req = first_required(t); RQ = let[req['key']]
        rows = t['demo'] if self.demo else []
        hmax = 2
        f_in, f_calc, f_link = self.F(), self.F(color='374151'), self.F(color=BLUE, underline='single')
        a_txt = a_num = self.AL('center', wrap=True)  # v1.3 (the owner: «الأرقام والكتابة في المنتصف لا متداخلة»): every cell centered and wrapping
        for c in t['columns']:
            L = let[c['key']]; ty = c['type']; fmtk = col_format(c)
            head = T(c['label']); w = self.fit_width(t, c, head); ws.column_dimensions[L].width = w; self.meta['widths'].setdefault(name, {})[L] = w
            hmax = max(hmax, lines(head, w))
            self.put(ws, f'{L}4', head, self.F(bold=True, color='FFFFFF'), self.P if ty != 'calc' else self.PC, self.AL('center', wrap=True), border=BOX)
            num = fmtk in ('int', 'num', 'money', 'pct', 'date', 'time', 'hours')
            fmt = NUMFMT[fmtk] if ty != 'text' and ty != 'link' else '@'
            if ty == 'calc' and fmtk == 'money': fmt = '#,##0.00;[Red]-#,##0.00'
            if ty == 'calc':
                expr = self.res(c['formula'], table=k, row='\x00')
                tpl = f'=IF(${RQ}\x00="","",{self.safe(expr)})'
                org = f'tables[{k}].columns[{c["key"]}]'; self.origin(name, L, org, c['formula'])
                self.meta['calc_cols'].append({'sheet': name, 'col': L, 'first': FIRST, 'last': last, 'origin': org, 'label': c['label']})
                for r in range(FIRST, last + 1):
                    x = ws[f'{L}{r}']; x.value = tpl.replace('\x00', str(r)); x.fill = fill(AUTO); x.font = f_calc; x.border = BOX
                    x.alignment = a_num if num else a_txt; x.number_format = fmt
            else:
                for r in range(FIRST, last + 1):
                    x = ws[f'{L}{r}']; x.border = BOX; x.font = f_link if ty == 'link' else f_in; x.alignment = a_num if num else a_txt; x.number_format = fmt
                for j, row in enumerate(rows):
                    v = self.demo_value(c, row.get(c['key']))
                    if v is not None: ws[f'{L}{FIRST + j}'].value = v
                if ty == 'list': self.dv(ws, f'{L}{FIRST}:{L}{last}', self.LR(c['list']))
                elif ty == 'bool': self.dv(ws, f'{L}{FIRST}:{L}{last}', self.LR(YESNO))
                elif ty == 'ref': rt, rc = c['ref'].split('.'); self.dv(ws, f'{L}{FIRST}:{L}{last}', self.RG(rt, rc))
        ws.row_dimensions[4].height = max(30, 13 * hmax + 6)
        for c in t['columns']:  # v1.3: indicators where a number means more than its digits
            v = c.get('visual'); L = let[c['key']]; rng = f'{L}{FIRST}:{L}{last}'
            if v == 'bar': ws.conditional_formatting.add(rng, DataBarRule(start_type='num', start_value=0, end_type='max', color=self.A, showValue=True))
            elif v in ('up', 'down'):
                lo, hi = ('F8696B', '63BE7B') if v == 'up' else ('63BE7B', 'F8696B')
                ws.conditional_formatting.add(rng, ColorScaleRule(start_type='min', start_color=lo, mid_type='percentile', mid_value=50, mid_color='FFEB84', end_type='max', end_color=hi))
        self.message_columns(t, ws)
        lastL = CL(len(t['columns']) + len(self.msg_layout[k]['msgs']))
        # alerts: conditional colours; settings and list labels are mirrored on this sheet (row 3, hidden columns)
        mi = [self.msg_layout[k]['next'] + 1]; mirrors = {}
        def mirror(kind, arg):
            if (kind, arg) not in mirrors:
                L = CL(mi[0]); mi[0] += 1
                ws[f'{L}3'] = '=' + (self.SET(arg) if kind == 'set' else self.LI(*arg.split('.'))); ws[f'{L}3'].number_format = ';;;'
                ws.column_dimensions[L].hidden = True; mirrors[(kind, arg)] = f'${L}$3'
            return mirrors[(kind, arg)]
        for a in t.get('alerts', []):
            L = let[a['column']]; op, rhs = parse_when(a['when'])
            rhs = self.res(rhs, table=k, row=FIRST, col_abs=True, mirror=mirror)
            self.cf(ws, f'{L}{FIRST}:{L}{last}', f'AND(${L}{FIRST}<>"",${L}{FIRST}{op}({rhs}))', a['style'])
        ws.freeze_panes = f'B{FIRST}'; ws.auto_filter.ref = f'A4:{lastL}{last}'
        ws.print_title_rows = '4:4'; ws.print_area = f'A1:{lastL}{last}'
        ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        self.meta['tables'][k] = {'sheet': name, 'last_col': lastL, 'ncols': len(t['columns']) + len(self.msg_layout[k]['msgs']), 'first': FIRST, 'last': last, 'n_demo': len(rows),
                                  'calc': sum(1 for c in t['columns'] if c['type'] == 'calc'), 'alerts': len(t.get('alerts', []))}

    def dashboard(self):
        s, T, d = self.s, self.T, self.s['dashboard']; ws = self.ws['dash']; name = self.names['dash']
        ws.column_dimensions['A'].width = 2
        for i in range(2, 14): ws.column_dimensions[CL(i)].width = 12.5
        self.put(ws, 'B1', T(d['title']), self.F(size=22, bold=True, color=self.P)); ws.row_dimensions[1].height = 34
        b = brand_setting(s)
        if b: self.put(ws, 'B2', f'={self.SET(b["key"])}&""', self.F(size=11, bold=True, color=GRAY))
        self.put(ws, 'B3', T(FIXED['dash_hint']), self.F(size=9, color=GRAY))
        self.put(ws, 'J2', T(FIXED['year']), self.F(color=GRAY), align=self.AL('left' if self.rtl else 'right')); ws.merge_cells('J2:K2')
        yv = self.demo_year() if self.demo else '=YEAR(TODAY())'
        self.put(ws, 'L2', yv, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL('center'), '0', BOX)
        d2 = DataValidation(type='whole', operator='between', formula1='1990', formula2='2100', allow_blank=False); d2.add('L2'); ws.add_data_validation(d2)
        Y = '$L$2'
        # KPI cards: 4 per row, each 3 columns wide
        top = Side(style='medium', color=self.P); white = Side(style='medium', color='FFFFFF')
        for i, kp in enumerate(d['kpis']):
            r = 5 + (i // 4) * 3; c0 = 2 + (i % 4) * 3; L0, L2 = CL(c0), CL(c0 + 2)
            fmt = {'money': '#,##0;[Red]-#,##0', 'num': '#,##0.0', 'int': '#,##0;[Red]-#,##0'}.get(kp['format'], NUMFMT[kp['format']])
            self.put(ws, f'{L0}{r}', T(kp['label']), self.F(size=9, bold=True, color=GRAY), CARD, self.AL('center', 'bottom', True))
            expr = self.res(kp['formula'])
            self.put(ws, f'{L0}{r + 1}', '=' + self.safe(expr), self.F(size=20, bold=True, color=self.P), CARD, self.AL('center'), fmt)
            for cc in range(c0, c0 + 3):
                for rr in (r, r + 1):
                    x = ws[f'{CL(cc)}{rr}']; x.fill = fill(CARD)
                    x.border = Border(top=top if rr == r else None, bottom=thin if rr == r + 1 else None, left=white if cc == c0 else None, right=white if cc == c0 + 2 else None)
            ws.merge_cells(f'{L0}{r}:{L2}{r}'); ws.merge_cells(f'{L0}{r + 1}:{L2}{r + 1}')
            ws.row_dimensions[r].height = 28; ws.row_dimensions[r + 1].height = 36; ws.row_dimensions[r + 2].height = 8
            org = f'dashboard.kpis[{i}]'; self.origin(name, f'{L0}{r + 1}', org, kp['formula'])
            self.meta['kpis'].append({'sheet': name, 'cell': f'{L0}{r + 1}', 'label': kp['label'], 'origin': org})
            if kp.get('alert'):
                op, rhs = parse_when(kp['alert']['when']); cell = f'{L0}{r + 1}'
                self.cf(ws, cell, f'AND({cell}<>"",{cell}{op}({self.res(rhs)}))', kp['alert']['style'])
        r = 5 + math.ceil(len(d['kpis']) / 4) * 3 + 1
        # month by month table + chart
        m = d['monthly']; M0 = r; ser = m['series']
        self.put(ws, f'B{M0}', f'={X(T(m["title"]) + " · ")}&{Y}', self.F(size=13, bold=True, color=self.P))
        heads = [T(FIXED['month'])] + [T(x['label']) for x in ser]
        for j, h in enumerate(heads): self.put(ws, f'{CL(2 + j)}{M0 + 1}', h, self.F(bold=True, color='FFFFFF'), self.P, self.AL('center', wrap=True), border=BOX)
        ws.row_dimensions[M0 + 1].height = 30
        for mm in range(1, 13):
            rr = M0 + 1 + mm
            self.put(ws, f'B{rr}', T(FIXED[f'm{mm}']), self.F(), align=self.AL(), border=BOX)
            for j, x in enumerate(ser):
                dc = series_date(s, x); dt_, dcol = dc.split('.'); st, scol = x['sum'].split('.')
                a_, b_ = f'DATE({Y},{mm},1)', f'DATE({Y},{mm + 1},1)'
                f = f'=SUMIFS({self.RG(st, scol)},{self.RG(dt_, dcol)},">="&{a_},{self.RG(dt_, dcol)},"<"&{b_})'
                self.put(ws, f'{CL(3 + j)}{rr}', f, self.F(), align=self.ALN(), fmt='#,##0;[Red]-#,##0', border=BOX)
                self.origin(name, f'{CL(3 + j)}{rr}', f'dashboard.monthly.series[{j}]')
        rt = M0 + 14
        self.put(ws, f'B{rt}', T(FIXED['total']), self.F(bold=True), align=self.AL(), border=BOX)
        for j in range(len(ser)):
            L = CL(3 + j); self.put(ws, f'{L}{rt}', f'=SUM({L}{M0 + 2}:{L}{M0 + 13})', self.F(bold=True), AUTO, self.ALN(), '#,##0;[Red]-#,##0', BOX)
        ch = BarChart(); ch.type = 'col'; ch.title = T(m['title']); ch.style = 10; ch.height = 7.6; ch.width = 14.2
        ch.add_data(Reference(ws, min_col=3, max_col=2 + len(ser), min_row=M0 + 1, max_row=M0 + 13), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=2, min_row=M0 + 2, max_row=M0 + 13))
        ch.y_axis.numFmt = '#,##0'; ch.y_axis.delete = False; ch.x_axis.delete = False; ch.legend.position = 'b'
        for sr, col in zip(ch.series, [self.P, self.A, '7A8CA5', '2E8B57']): sr.graphicalProperties.solidFill = col; sr.graphicalProperties.line.solidFill = col
        ws.add_chart(ch, f'H{M0}')
        self.meta['monthly'] = {'sheet': name, 'header_row': M0 + 1, 'r1': M0 + 2, 'r2': M0 + 13, 'c1': 3, 'c2': 2 + len(ser), 'cat': 2, 'at': f'H{M0}',
                                'title': T(m['title']), 'colors': [self.P, self.A, '7A8CA5', '2E8B57'][:len(ser)]}
        # breakdowns, two side by side
        r = rt + 3; bd = d.get('breakdowns', []); bottom = rt
        for p in range(0, len(bd), 2):
            hmax = 0
            for q, bk in enumerate(bd[p:p + 2]):
                hmax = max(hmax, self.breakdown(ws, r, 2 if q == 0 else 8, bk, p + q, Y))
            r += hmax + 2; bottom = r
        ws.freeze_panes = 'A4'
        ws.print_area = f'A1:M{max(bottom, rt + 1)}'
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        self.meta['dash_range'] = f'A1:M{max(bottom - 1, rt + 1)}'

    # ---------- v1.3: the «Charts» sheet — the buyer's filters, gauges and live charts, each fed by a visible table of formulas
    def crit(self, t, x, Y, fil):
        """the criteria of one aggregation of table t: its own rows only, its where-conditions, the filters that reach this table, the year."""
        req = first_required(self.table_by(t)); cr = [(self.RG(t, req['key']), '"<>"')]
        for w in x.get('where') or []:
            v = w['value']; op = w['op']
            if isinstance(v, (int, float)): val = repr(v) if not isinstance(v, bool) else '0'
            elif v == '{today}': val = 'TODAY()'
            elif v.startswith('{list:'): l, k = v[6:-1].split('.'); val = self.LI(l, k)
            else: val = self.SET(v[5:-1])
            cr.append((self.RG(t, w['column']), val if op == '=' else f'"{op}"&{val}'))
        for f, cell in fil:
            col = self.filter_col(t, f)
            if col: cr.append((self.RG(t, col), f'IF(OR({cell}="",{cell}={X(self.T(FIXED["all"]))}),"<>|",{cell})'))
        if x.get('date') and Y:
            dcol = x['date'].split('.')[1]
            cr += [(self.RG(t, dcol), f'">="&DATE({Y[0]},{Y[1]},1)'), (self.RG(t, dcol), f'"<"&DATE({Y[0]},{Y[2]},1)')]
        return cr
    def table_by(self, k): return next(t for t in self.s['tables'] if t['key'] == k)
    def filter_col(self, t, f):
        tb = self.table_by(t)
        if 'ref' in f:
            rt, rc = f['ref'].split('.')
            if t == rt and any(c['key'] == rc for c in tb['columns']): return rc
            return next((c['key'] for c in tb['columns'] if c['type'] == 'ref' and c.get('ref') == f['ref']), None)
        return next((c['key'] for c in tb['columns'] if c['type'] == 'list' and c.get('list') == f['list']), None)
    def agg(self, x, cr):
        t = x['table']; c = ','.join(f'{a},{b}' for a, b in cr)
        if x['agg'] == 'count': return f'COUNTIFS({c})'
        vt, vc = x['value'].split('.')
        if x['agg'] == 'sum': return f'SUMIFS({self.RG(vt, vc)},{c})'
        return f'IFERROR(AVERAGEIFS({self.RG(vt, vc)},{c}),0)'
    def insights(self):
        import charts as CK
        T, ins = self.T, self.s['insights']; ws = self.ws['charts']; name = self.names['charts']; sid = 'charts'
        K = CK.Sheet(ws, self.F, T(FIXED['sheet_charts']), T(FIXED['charts_hint']), T(FIXED['charts_data']), dc=24)
        ws['B1'].font = self.F(size=22, bold=True, color=self.P)
        ALL = T(FIXED['all']); yv = self.demo_year() if self.demo else '=YEAR(TODAY())'
        self.put(ws, 'B4', T(FIXED['year']), self.F(bold=True, color=self.P), align=self.AL('center'))
        self.put(ws, 'C4', yv, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL('center'), '0', BOX); Y = '$C$4'
        fil = []; opt_c = K.dc + 8
        for i, f in enumerate(ins.get('filters') or []):
            lab, cell = CL(5 + i * 5), CL(6 + i * 5); end = CL(8 + i * 5)
            self.put(ws, f'{lab}4', T(f['label']), self.F(bold=True, color=self.P), align=self.AL('center'))
            ws.merge_cells(f'{cell}4:{end}4'); self.put(ws, f'{cell}4', ALL, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL('center'), border=BOX)
            oc = CL(opt_c + i); self.put(ws, f'{oc}5', T(f['label']), self.F(size=9, bold=True, color=self.P)); self.put(ws, f'{oc}6', f'={X(ALL)}', self.F(size=9))
            if 'ref' in f:
                rt, rc = f['ref'].split('.')
                for j in range(40): self.put(ws, f'{oc}{7 + j}', f'=IF(INDEX({self.RG(rt, rc)},{j + 1})="","",INDEX({self.RG(rt, rc)},{j + 1}))', self.F(size=9))
                n = 40
            else:
                vals = list_by_key(self.s, f['list'])['values']; n = len(vals)
                for j, v in enumerate(vals): self.put(ws, f'{oc}{7 + j}', f'={self.LI(f["list"], v["key"])}', self.F(size=9))
            ws.column_dimensions[oc].width = 16; self.dv(ws, f'{cell}4', f'${oc}$6:${oc}${6 + n}'); fil.append((f, f'${cell}$4'))
        ws.row_dimensions[4].height = 26
        from openpyxl.chart import DoughnutChart
        from openpyxl.chart.series import DataPoint
        gs = ins.get('gauges') or []
        for gi, g in enumerate(gs):
            num = self.agg(g['num'], self.crit(g['num']['table'], g['num'], ('$C$4', 1, 13), fil)); den = self.agg(g['den'], self.crit(g['den']['table'], g['den'], ('$C$4', 1, 13), fil))
            r1, r2 = K.block(T(g['title']), [T(FIXED['gauge']), T(FIXED['share'])], [[T(FIXED['g_done']), f'=IFERROR(MIN(1,MAX(0,({num})/({den}))),0)'], [T(FIXED['g_left']), None], [T(FIXED['g_base']), 1]], [None, '0%'])
            ws.cell(r1 + 1, K.dc + 1).value = f'=1-{CL(K.dc + 1)}{r1}'
            ch = DoughnutChart(holeSize=58); ch.firstSliceAng = 270; ch.title = T(g['title']); ch.style = 10; ch.legend = None
            ch.add_data(K.ref(1, r1, r2), titles_from_data=True); ch.set_categories(K.ref(0, r1, r2, head=False))
            for i, col in enumerate([[self.A, CK.GREEN, CK.TEAL, self.P, CK.PLUM, CK.SKY][gi % 6], 'E5E7EB', None]):
                p = DataPoint(idx=i)
                if col: p.graphicalProperties.solidFill = col; p.graphicalProperties.line.solidFill = 'FFFFFF'
                else: p.graphicalProperties.noFill = True; p.graphicalProperties.line.noFill = True
                ch.series[0].dPt.append(p)
            # a card per gauge (v1.3.1): the chart drawn on a transparent ground over a filled card, its share written in the cells under the
            # arc so it reads inside the gauge; a row of fewer than three gauges is centred
            in_row = min(3, len(gs) - (gi // 3) * 3); col0 = 2 + (3 - in_row) * 3 + (gi % 3) * 6; row0 = 6 + (gi // 3) * 12
            from openpyxl.chart.shapes import GraphicalProperties as _GP
            from openpyxl.drawing.line import LineProperties as _LP
            from openpyxl.styles import PatternFill as _PF, Border as _BD, Side as _SD
            ch.graphical_properties = _GP(noFill=True, ln=_LP(noFill=True)); ch.plot_area.graphicalProperties = _GP(noFill=True, ln=_LP(noFill=True))
            card, edge = _PF('solid', fgColor='F7F9FC'), _SD(style='thin', color='D9DEE7')
            for rr in range(row0, row0 + 10):
                for cc in range(col0, col0 + 6):
                    cl = ws.cell(rr, cc); cl.fill = card
                    cl.border = _BD(left=edge if cc == col0 else None, right=edge if cc == col0 + 5 else None, top=edge if rr == row0 else None, bottom=edge if rr == row0 + 9 else None)
            ch.width, ch.height = 10.4, 5.2; ws.add_chart(ch, f'{CL(col0)}{row0}')
            big = f'{CL(col0)}{row0 + 7}'; ws.merge_cells(f'{big}:{CL(col0 + 5)}{row0 + 7}')
            self.put(ws, big, f'={CL(K.dc + 1)}{r1}', self.F(size=24, bold=True, color=self.P), 'F7F9FC', self.AL('center'), '0%')
            ws.cell(row0 + 7, col0 + 5).border = _BD(right=edge); ws.cell(row0 + 7, col0).border = _BD(left=edge); ws.row_dimensions[row0 + 7].height = 30
            self.meta['gauges'].append({'title': g['title'], 'sheet': name, 'cell': f'{CL(K.dc + 1)}{r1}', 'origin': f'insights.gauges[{gi}]'})
        K.top = 6 + ((len(gs) + 2) // 3) * 12 if gs else 6
        PAL = [self.P, self.A, CK.TEAL, CK.RED, CK.PLUM, CK.GREEN]
        for ci, c in enumerate(ins['charts']):
            ser = c['series']; rows = []
            if c['by'] == 'month':
                for m in range(1, 13):
                    rows.append([T(FIXED[f'm{m}'])] + [f'={self.agg(x, self.crit(x["table"], x, (Y, m, m + 1), fil))}' for x in ser])
            else:
                bt, bc = c['by'].split('.'); bcol = next(x for x in self.table_by(bt)['columns'] if x['key'] == bc)
                if bcol['type'] == 'list':
                    for v in list_by_key(self.s, bcol['list'])['values']:
                        cat = self.LI(bcol['list'], v['key'])
                        rows.append([f'={cat}'] + [f'={self.agg(x, self.crit(x["table"], x, (Y, 1, 13), fil) + [(self.RG(bt, bc), cat)])}' for x in ser])
                else:
                    rt, rc = bcol['ref'].split('.'); k = min(12, max(4, len(self.table_by(rt).get('demo') or [])))
                    for j in range(k):
                        cat = f'INDEX({self.RG(rt, rc)},{j + 1})'
                        rows.append([f'=IF({cat}="","",{cat})'] + [f'=IF({cat}="","",{self.agg(x, self.crit(x["table"], x, (Y, 1, 13), fil) + [(self.RG(bt, bc), cat)])})' for x in ser])
            fmts = [None] + ['0' if x['agg'] == 'count' else '#,##0' for x in ser]
            r1, r2 = K.block(T(c['title']), [''] + [T(x['label']) for x in ser], rows, fmts)
            num = '0' if all(x['agg'] == 'count' for x in ser) else '#,##0'; ty = c['type']
            if ty in ('doughnut', 'pie'): K.ring(T(c['title']), (r1, r2), doughnut=ty == 'doughnut')
            elif ty == 'combo':
                li = c['line']; bars_ = [j + 1 for j in range(len(ser)) if j != li]
                K.bars(T(c['title']), (r1, r2), bars_, PAL[:len(bars_)], line=(li + 1, CK.GOLD), num=num)
            elif ty == 'line':
                from openpyxl.chart import LineChart
                ch = LineChart(); ch.title = T(c['title']); ch.style = 10
                for j in range(len(ser)):
                    ch.add_data(K.ref(j + 1, r1, r2), titles_from_data=True); CK._color(ch.series[-1], PAL[j % len(PAL)], line=True)
                ch.set_categories(K.ref(0, r1, r2, head=False)); CK._axes(ch, num); K.place(ch)
            else: K.bars(T(c['title']), (r1, r2), [j + 1 for j in range(len(ser))], PAL[:len(ser)], horizontal=ty == 'bar', stacked=ty == 'stacked', num=num, labels=len(ser) == 1 and ty == 'bar')
            self.origin(name, f'{CL(K.dc + 1)}{r1}', f'insights.charts[{ci}]')
            self.meta['charts'].append({'title': c['title'], 'sheet': name, 'r1': r1, 'r2': r2, 'c1': K.dc + 1, 'c2': K.dc + len(ser), 'cat': K.dc, 'origin': f'insights.charts[{ci}]', 'by': c['by'],
                                        'at': list(K.anchors[-1]), 'type': c['type']})
        ws.freeze_panes = 'A5'; self.meta['charts_sheet'] = {'sheet': name, 'top': K.top, 'filters_to': CL(8 + 5 * (len(ins.get('filters') or []) - 1)) if ins.get('filters') else 'C'}
        ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True

    def breakdown(self, ws, r0, c0, bk, i, Y):
        T = self.T; name = self.names['dash']; tb, byc = find_col(self.s, bk['by']); t = tb['key']
        Lb, Lb2, Lv, Ls = CL(c0), CL(c0 + 1), CL(c0 + 2), CL(c0 + 3)
        dcol = main_date(tb)
        title = T(bk['title'])
        self.put(ws, f'{Lb}{r0}', f'={X(title + " · ")}&{Y}' if dcol else title, self.F(size=12, bold=True, color=self.P))
        vt, vc = find_col(self.s, bk.get('value')) if bk.get('value') else (None, None)
        vh = T(vc['label']) if (bk['agg'] == 'sum' and vc) else T(FIXED['count'])
        for L, h in ((Lb, T(byc['label'])), (Lv, vh), (Ls, T(FIXED['share']))):
            self.put(ws, f'{L}{r0 + 1}', h, self.F(bold=True, color='FFFFFF'), self.P, self.AL('center', wrap=True), border=BOX)
        ws[f'{Lb2}{r0 + 1}'].fill = fill(self.P); ws[f'{Lb2}{r0 + 1}'].border = BOX; ws.merge_cells(f'{Lb}{r0 + 1}:{Lb2}{r0 + 1}')
        ws.row_dimensions[r0 + 1].height = max(ws.row_dimensions[r0 + 1].height or 0, 30)
        if byc['type'] in ('list', 'bool'):
            l = byc['list'] if byc['type'] == 'list' else YESNO
            labels = [f'={self.LI(l, v["key"])}' for v in list_by_key(self.s, l)['values']]
        else:
            rt, rc = byc['ref'].split('.'); rg = self.RG(rt, rc); n = min(20, self.tables[rt]['rows'])
            labels = [f'=IF(INDEX({rg},{j + 1})="","",INDEX({rg},{j + 1}))' for j in range(n)]
        crit = f'{self.RG(t, byc["key"])},${Lb}\x00'
        if dcol:
            D = self.RG(t, dcol['key']); crit += f',{D},">="&DATE({Y},1,1),{D},"<"&DATE({Y}+1,1,1)'
        val = (f'SUMIFS({self.RG(t, vc["key"])},{crit})' if bk['agg'] == 'sum' else f'COUNTIFS({crit})')
        fmtv = '#,##0;[Red]-#,##0'
        fixed = byc['type'] in ('list', 'bool')      # a known set of rows: total last; values of another table: total first, rows show when used
        rT = r0 + 2 + len(labels) if fixed else r0 + 2
        first = r0 + 2 if fixed else r0 + 3
        for j, lab in enumerate(labels):
            rr = first + j; bx = BOX if fixed else None
            self.put(ws, f'{Lb}{rr}', lab, self.F(), align=self.AL(), border=bx); ws.merge_cells(f'{Lb}{rr}:{Lb2}{rr}')
            if fixed: ws[f'{Lb2}{rr}'].border = BOX
            self.put(ws, f'{Lv}{rr}', f'=IF(${Lb}{rr}="","",{val.replace(chr(0), str(rr))})', self.F(), align=self.ALN(), fmt=fmtv, border=bx)
            self.put(ws, f'{Ls}{rr}', f'=IF(OR({Lv}{rr}="",N({Lv}${rT})=0),"",{Lv}{rr}/{Lv}${rT})', self.F(color=GRAY), align=self.ALN(), fmt='0%', border=bx)
            self.origin(name, f'{Lv}{rr}', f'dashboard.breakdowns[{i}]')
        last = first + len(labels) - 1
        if not fixed:
            ws.conditional_formatting.add(f'{Lb}{first}:{Ls}{last}', FormulaRule(formula=[f'${Lb}{first}<>""'], border=BOX, stopIfTrue=False))
        self.put(ws, f'{Lb}{rT}', T(FIXED['total']), self.F(bold=True), AUTO if not fixed else None, align=self.AL(), border=BOX)
        ws[f'{Lb2}{rT}'].border = BOX; ws.merge_cells(f'{Lb}{rT}:{Lb2}{rT}')
        if not fixed: ws[f'{Lb2}{rT}'].fill = fill(AUTO)
        self.put(ws, f'{Lv}{rT}', f'=SUM({Lv}{first}:{Lv}{last})', self.F(bold=True), AUTO, self.ALN(), fmtv, BOX)
        self.put(ws, f'{Ls}{rT}', None, fill_=AUTO if not fixed else None, border=BOX)
        return len(labels) + 3

    def demo_year(self):
        """The demo opens on the year that holds most of the monthly rows (relative demo dates can cross a new year)."""
        years = {}
        for x in self.s['dashboard']['monthly']['series']:
            dc = series_date(self.s, x); tb, c = find_col(self.s, dc)
            if c and c['type'] == 'date':
                for row in tb['demo']:
                    d_ = parse_date(row.get(c['key']), self.today)
                    if d_: years[d_.year] = years.get(d_.year, 0) + 1
        return max(years, key=lambda y: (years[y], y)) if years else self.today.year

    def form(self, f):
        s, T = self.s, self.T; sid = 'f:' + f['key']; ws = self.ws[sid]; name = self.names[sid]
        for c, w in zip('ABCDEFGHIJ', [3, 22, 15, 15, 15, 15, 15, 3, 3, 6]): ws.column_dimensions[c].width = w
        ws.column_dimensions['J'].hidden = True
        self.put(ws, 'B1', T(f['title']), self.F(size=22, bold=True, color=self.P)); ws.row_dimensions[1].height = 34
        b = brand_setting(s)
        if b: self.put(ws, 'E1', f'={self.SET(b["key"])}&""', self.F(size=12, bold=True, color=GRAY), align=self.AL('left' if self.rtl else 'right')); ws.merge_cells('E1:G1')
        self.put(ws, 'B2', T(FIXED['form_hint']), self.F(size=9, color=GRAY))
        for c in 'BCDEFG': ws[f'{c}3'].fill = fill(self.A)
        ws.row_dimensions[3].height = 4
        pt, pc = f['pick'].split('.'); PR = self.RG(pt, pc); ptb, pcol = find_col(s, f['pick'])
        self.put(ws, 'B4', T(pcol['label']), self.F(size=11, bold=True))
        pv = self.form_pick(f) if self.demo else None
        pfmt = NUMFMT[col_format(pcol)] if col_format(pcol) in ('date', 'int', 'num', 'money') else None
        self.put(ws, 'C4', pv, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL(), pfmt, BOX)
        ws['D4'].fill = fill(CREAM); ws['D4'].border = BOX; ws.merge_cells('C4:D4'); self.dv(ws, 'C4', PR)
        ws.row_dimensions[4].height = 24
        ws['J4'] = f'=IF($C$4="","",IFERROR(MATCH($C$4,{PR},0),""))'
        self.put(ws, 'E4', f'=IF(AND($C$4<>"",$J$4=""),{X(T(FIXED["not_found"]))},"")', self.F(bold=True, color='9B1C1C'))
        has_lines = bool(f.get('lines'))
        top, summ = [], []
        for j, x in enumerate(f['fields']):
            numeric = False
            if 'value' in x:
                _, vc = find_col(s, x['value']); numeric = col_format(vc) in ('money', 'num', 'int', 'pct', 'hours')
            (summ if has_lines and ('formula' in x or numeric) else top).append((j, x))
        def value_cell(ref, j, x, big=False, left=False):
            if 'value' in x:
                vt, vc = x['value'].split('.'); _, col = find_col(s, x['value']); rg = self.RG(vt, vc); fk = col_format(col)
                fv = f'=IF($J$4="","",IF(INDEX({rg},$J$4)="","",INDEX({rg},$J$4)))'
            else:
                fk = x['format']; fv = f'=IF($C$4="","",{self.safe(self.res(x["formula"], pick="$C$4"))})'
                self.origin(name, ref, f'forms[{f["key"]}].fields[{j}]', x['formula'])
            fmt = {'money': '#,##0.00;[Red]-#,##0.00'}.get(fk, NUMFMT.get(fk))
            num = fk in ('int', 'num', 'money', 'pct', 'date', 'time', 'hours')
            self.put(ws, ref, fv, self.F(size=13 if big else 11, bold=True, color=self.P if big else INK), align=self.ALN() if num and not left else self.AL(), fmt=fmt)
            self.meta['form_fields'].append({'sheet': name, 'cell': ref, 'label': x['label'], 'origin': f'forms[{f["key"]}].fields[{j}]'})
        under = Border(bottom=thin)
        r = 6
        for n, (j, x) in enumerate(top):
            rr = r + n // 2; lc, v1, v2 = (('B', 'C', 'D') if n % 2 == 0 else ('E', 'F', 'G'))
            self.put(ws, f'{lc}{rr}', T(x['label']), self.F(color=GRAY), align=self.AL(wrap=True))
            value_cell(f'{v1}{rr}', j, x, left=True); ws.merge_cells(f'{v1}{rr}:{v2}{rr}')
            for c in (v1, v2): ws[f'{c}{rr}'].border = under
            ws.row_dimensions[rr].height = 22
        r = r + (len(top) + 1) // 2 + 1
        if has_lines:
            L = f['lines']; lt = L['from']; mt, mc = L['match'].split('.'); MR = self.RG(mt, mc); mlast = f"{self.Q('t:' + mt)}!${self.let[mt][mc]}${self.last[mt]}"
            cols = L['columns']; mx = L.get('max', 15)
            for j, ck in enumerate(cols):
                _, col = find_col(s, f'{lt}.{ck}')
                self.put(ws, f'{CL(2 + j)}{r}', T(col['label']), self.F(bold=True, color='FFFFFF'), self.P, self.AL('center', wrap=True), border=BOX)
            ws.row_dimensions[r].height = 30
            for i in range(mx):
                rr = r + 1 + i
                ws[f'J{rr}'] = (f'=IF($J$4="","",IFERROR(MATCH($C$4,{MR},0),""))' if i == 0 else
                                f'=IF(N(J{rr - 1})=0,"",IFERROR(MATCH($C$4,INDEX({MR},J{rr - 1}+1):{mlast},0)+J{rr - 1},""))')
                for j, ck in enumerate(cols):
                    _, col = find_col(s, f'{lt}.{ck}'); fk = col_format(col); rg = self.RG(lt, ck)
                    num = fk in ('int', 'num', 'money', 'pct', 'date', 'time', 'hours')
                    self.put(ws, f'{CL(2 + j)}{rr}', f'=IF($J{rr}="","",IF(INDEX({rg},$J{rr})="","",INDEX({rg},$J{rr})))', self.F(),
                             'F7F9FC' if i % 2 else None, self.ALN() if num else self.AL(), NUMFMT[fk] if fk != 'text' else None, BOX)
            r = r + mx + 2
            for n, (j, x) in enumerate(summ):
                rr = r + n; big = n == len(summ) - 1
                self.put(ws, f'E{rr}', T(x['label']), self.F(size=13 if big else 11, bold=True, color=self.P if big else INK), align=self.AL(wrap=True))
                value_cell(f'F{rr}', j, x, big); ws.merge_cells(f'F{rr}:G{rr}')
                if big:
                    for c in 'EFG': ws[f'{c}{rr}'].border = Border(top=Side(style='medium', color=self.P))
                ws.row_dimensions[rr].height = 26 if big else 20
            r = r + len(summ) + 1
        r += 2
        self.put(ws, f'B{r}', T(FIXED['signature']) + ':  ______________________', self.F(color=GRAY))
        ws.print_area = f'A1:G{r + 1}'
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_margins.left = ws.page_margins.right = 0.5
        self.meta['forms'][f['key']] = {'sheet': name, 'range': f'A1:G{r + 1}'}

    def form_pick(self, f):
        """The record the demo form shows: the one with the most lines (or the first)."""
        s = self.s; ptb, pcol = find_col(s, f['pick']); rows = ptb['demo']
        best = 0
        if f.get('lines'):
            mt, mc = f['lines']['match'].split('.'); _, mcol = find_col(s, f['lines']['match'])
            if mcol['type'] != 'calc' and pcol['type'] != 'calc':
                cnt = [sum(1 for x in self.tables[mt]['demo'] if x.get(mc) == r.get(pcol['key'])) for r in rows]
                best = max(range(len(rows)), key=lambda i: (cnt[i], -i))
        if pcol['type'] == 'calc': return f'=INDEX({self.RG(ptb["key"], pcol["key"])},{best + 1})'
        return self.demo_value(pcol, rows[best].get(pcol['key']))


    # ---------- v1.1: values as text (messages, documents)
    def as_text(self, x, fk):
        if fk == 'date': return f'IF(N({x})=0,"",YEAR({x})&"-"&RIGHT("0"&MONTH({x}),2)&"-"&RIGHT("0"&DAY({x}),2))'
        if fk == 'time': return f'IF({x}="","",HOUR({x})&":"&RIGHT("0"&MINUTE({x}),2))'
        if fk in ('money', 'num'): return f'IF({x}="","",FIXED({x},2))'
        if fk == 'int': return f'IF({x}="","",FIXED({x},0))'
        if fk == 'hours': return f'IF({x}="","",FIXED({x},1))'
        if fk == 'pct': return f'IF({x}="","",FIXED({x}*100,0)&"%")'
        return f'{x}&""'

    def set_text(self, k):
        x = next(s for s in self.s['settings'] if s['key'] == k)
        return self.as_text(self.SET(k), {'pct': 'pct', 'money': 'money', 'int': 'int', 'num': 'num', 'date': 'date'}.get(x['type'], 'text'))

    def message_columns(self, t, ws):
        """«Send on WhatsApp» columns: wa.me link with the wording of the Messages sheet filled from the row (url-encoded; a text too
        long for HYPERLINK's 255 characters opens the chat without the text)."""
        k = t['key']; lay = self.msg_layout[k]
        if not lay['msgs']: return
        last = self.last[k]; RQ = self.let[k][first_required(t)['key']]
        cc = next((x for x in self.s['settings'] if x['key'] in ('cc', 'country_code', 'phone_code', 'dial_code', 'calling_code')), None)
        for ph, L in lay['phones'].items():
            pt, pc = ph.split('.')
            if pt == k: p = f'{self.let[k][pc]}\x00&""'
            else:
                rc = next(c for c in t['columns'] if c['type'] == 'ref' and c['ref'].split('.')[0] == pt)
                tt, tc = rc['ref'].split('.')
                p = f'IFERROR(INDEX({self.RG(pt, pc)},MATCH({self.let[k][rc["key"]]}\x00,{self.RG(tt, tc)},0))&"","")'
            for ch in (' ', '+', '-', '(', ')', '.'): p = f'SUBSTITUTE({p},{X(ch)},"")'
            d = f'IF(LEFT({p},2)="00",MID({p},3,30),' + (f'IF(AND({self.SET(cc["key"])}<>"",LEFT({p},1)="0"),{self.SET(cc["key"])}&MID({p},2,30),{p}))' if cc else f'{p})')
            for r in range(FIRST, last + 1): ws[f'{L}{r}'] = f'=IF(${RQ}{r}="","",{d.replace(chr(0), str(r))})'
            ws.column_dimensions[L].hidden = True
        label = f"{self.Q('msgs')}!$B$3"
        for m in lay['msgs']:
            L, U, D = lay['links'][m['key']], lay['urls'][m['key']], lay['phones'][m['phone']]
            txt = f"{self.Q('msgs')}!$D${self.msgrow[m['key']]}"
            cols = {c['key']: c for c in t['columns']}
            for ph in dict.fromkeys(PH.findall(m['text'])):
                txt = f'SUBSTITUTE({txt},"{{{ph}}}",{self.as_text(self.let[k][ph] + chr(0), col_format(cols[ph]))})'
            for a, b in (('"%"', '"%25"'), ('" "', '"%20"'), ('CHAR(10)', '"%0A"'), ('"&"', '"%26"'), ('"#"', '"%23"'), ('"?"', '"%3F"'), ('"+"', '"%2B"'), ('""""', '"%22"')):
                txt = f'SUBSTITUTE({txt},{a},{b})'
            url = f'=IF(OR(${RQ}\x00="",${D}\x00=""),"","https://wa.me/"&${D}\x00&"?text="&{txt})'
            self.put(ws, f'{L}4', self.T(m['moment']), self.F(bold=True, color='FFFFFF'), '128C7E', self.AL('center', wrap=True), border=BOX)
            ws.column_dimensions[L].width = max(19, vlen(self.T(FIXED['wa_send'])) + 3); ws.column_dimensions[U].hidden = True
            f_link = self.F(bold=True, color='128C7E', underline='single'); al = self.AL('center')
            for r in range(FIRST, last + 1):
                ws[f'{U}{r}'] = url.replace('\x00', str(r))
                x = ws[f'{L}{r}']; x.value = (f'=IF(${U}{r}="","",IF(LEN(${U}{r})<=255,HYPERLINK(${U}{r},{label}),HYPERLINK("https://wa.me/"&${D}{r},{label})))')
                x.font = f_link; x.alignment = al; x.border = BOX
            self.meta['msg_cols'].append({'sheet': self.names['t:' + k], 'col': L, 'first': FIRST, 'last': last, 'origin': f'messages[{m["key"]}]', 'label': m['moment']})
            self.origin(self.names['t:' + k], L, f'messages[{m["key"]}]'); self.origin(self.names['t:' + k], U, f'messages[{m["key"]}]')

    def messages_sheet(self):
        ws = self.ws['msgs']; T = self.T
        for c, w in zip('ABCD', [3, 26, 20, 90]): ws.column_dimensions[c].width = w
        self.put(ws, 'B1', self.names['msgs'], self.F(size=18, bold=True, color=self.P)); ws.row_dimensions[1].height = 30
        self.put(ws, 'B2', T(FIXED['msg_hint']), self.F(color=GRAY))
        self.put(ws, 'B3', T(FIXED['wa_send']), self.F(bold=True, color='128C7E', underline='single'), CREAM, border=BOX)
        for c, h in zip('BCD', (T(FIXED['moment']), T(FIXED['sheet']), T(FIXED['text']))):
            self.put(ws, f'{c}4', h, self.F(bold=True, color='FFFFFF'), '128C7E', self.AL('center'), border=BOX)
        for m in self.s['messages']:
            r = self.msgrow[m['key']]; txt = T(m['text'])
            self.put(ws, f'B{r}', T(m['moment']), self.F(bold=True), align=self.AL(v='top', wrap=True), border=BOX)
            self.put(ws, f'C{r}', self.names['t:' + m['table']], self.F(color=GRAY), align=self.AL(v='top', wrap=True), border=BOX)
            self.put(ws, f'D{r}', txt, self.F(color=BLUE), CREAM, self.AL(v='top', wrap=True), border=BOX)
            ws.row_dimensions[r].height = max(30, 15 * lines(txt, 88) + 6)
        ws.freeze_panes = 'A5'

    # ---------- v1.1: tools (calculators / planners)
    def tool(self, x):
        T = self.T; sid = 'x:' + x['key']; ws = self.ws[sid]; name = self.names[sid]
        for c, w in zip('AB', [3, 36]): ws.column_dimensions[c].width = w
        for i in range(3, 12): ws.column_dimensions[CL(i)].width = 15
        self.put(ws, 'B1', T(x['title']), self.F(size=22, bold=True, color=self.P)); ws.row_dimensions[1].height = 34
        self.put(ws, 'B2', T(x['hint']), self.F(color=GRAY))
        for c in 'BCDEFG': ws[f'{c}3'].fill = fill(self.A)
        ws.row_dimensions[3].height = 4
        self.section(ws, 'B5', T(FIXED['inputs']))
        ins = {}; r = 6
        for i_ in x['inputs']:
            ty = i_['type']; v = i_['default']; fmt = {'pct': '0.0%', 'money': '#,##0.00', 'int': '#,##0', 'num': '#,##0.00', 'date': 'yyyy-mm-dd', 'text': '@'}.get(ty)
            if ty == 'list': v = self.label_of(i_['list'], v)
            if ty == 'date': v = self.date_default(v)
            if ty == 'text' and isinstance(v, str) and v.strip():
                # 2026-11-12: a text default (e.g. a person's name) is matched against the demo rows, which are translated -> translate it too when a translation exists
                try: v = T(v)
                except KeyError: pass
            self.put(ws, f'B{r}', T(i_['label']), self.F(size=11), align=self.AL(wrap=True))
            self.put(ws, f'C{r}', v, self.F(size=11, bold=True, color=BLUE), CREAM, self.ALN() if ty not in ('text', 'list') else self.AL(), fmt, BOX)
            if ty == 'list': self.dv(ws, f'C{r}', self.LR(i_['list']))
            ins[i_['key']] = f'$C${r}'; ws.row_dimensions[r].height = 20; r += 1
        r += 1; self.section(ws, f'B{r}', T(FIXED['results'])); r += 1
        outs = x['outputs']
        for j, o in enumerate(outs):
            big = j == len(outs) - 1; fk = o['format']
            fmt = {'money': '#,##0.00;[Red]-#,##0.00'}.get(fk, NUMFMT[fk])
            self.put(ws, f'B{r}', T(o['label']), self.F(size=12 if big else 11, bold=big), align=self.AL(wrap=True))
            self.put(ws, f'C{r}', '=' + self.safe(self.res(o['formula'], ins=ins)), self.F(size=14 if big else 11, bold=True, color=self.P if big else INK),
                     AUTO, self.ALN() if fk not in ('text',) else self.AL(), fmt, BOX)
            org = f'tools[{x["key"]}].outputs[{j}]'; self.origin(name, f'C{r}', org, o['formula'])
            self.meta['tool_cells'].append({'sheet': name, 'cell': f'C{r}', 'label': o['label'], 'origin': org})
            ws.row_dimensions[r].height = 26 if big else 20; r += 1
        g = x.get('grid'); last = r
        if g:
            r += 1; self.section(ws, f'B{r}', T(g['title'])); r += 1
            over = [i_ for i_ in x['inputs'] if any(i_['key'] in row['values'] for row in g['rows'])]
            outs = [o for o in outs if any('{in:' + i_['key'] + '}' in o['formula'] for i_ in over)] or outs   # only what the scenarios change
            heads = [''] + [T(i_['label']) for i_ in over] + [T(o['label']) for o in outs]
            for j, h in enumerate(heads):
                self.put(ws, f'{CL(2 + j)}{r}', h, self.F(bold=True, color='FFFFFF'), self.P if j <= len(over) else self.PC, self.AL('center', wrap=True), border=BOX)
            ws.row_dimensions[r].height = max(32, 13 * max(lines(h, 16) for h in heads if h) + 8)
            for gi, row in enumerate(g['rows']):
                rr = r + 1 + gi; rins = dict(ins)
                self.put(ws, f'B{rr}', T(row['label']), self.F(bold=True), align=self.AL(), border=BOX)
                for j, i_ in enumerate(over):
                    L = CL(3 + j); v = row['values'].get(i_['key'])
                    if v is None: val, font = f'={ins[i_["key"]]}', self.F(color=GRAY)
                    elif isinstance(v, str): val, font = '=' + self.safe(self.res(v, ins=ins)), self.F(bold=True, color=BLUE)
                    else: val, font = v, self.F(bold=True, color=BLUE)
                    fmt = {'pct': '0.0%', 'money': '#,##0.00', 'int': '#,##0', 'num': '#,##0.00', 'date': 'yyyy-mm-dd'}.get(i_['type'])
                    self.put(ws, f'{L}{rr}', val, font, CREAM if v is not None else None, self.ALN() if i_['type'] not in ('text', 'list') else self.AL(), fmt, BOX)
                    rins[i_['key']] = f'${L}{rr}'
                    if isinstance(v, str): self.origin(name, f'{L}{rr}', f'tools[{x["key"]}].grid.rows[{gi}].values.{i_["key"]}', v)
                for j, o in enumerate(outs):
                    L = CL(3 + len(over) + j); fk = o['format']
                    self.put(ws, f'{L}{rr}', '=' + self.safe(self.res(o['formula'], ins=rins)), self.F(), AUTO, self.ALN() if fk != 'text' else self.AL(),
                             {'money': '#,##0.00;[Red]-#,##0.00'}.get(fk, NUMFMT[fk]), BOX)
                    org = f'tools[{x["key"]}].grid.rows[{gi}]'; self.origin(name, f'{L}{rr}', org, o['formula'])
                    self.meta['tool_cells'].append({'sheet': name, 'cell': f'{L}{rr}', 'label': f'{row["label"]} · {o["label"]}', 'origin': org})
            last = r + len(g['rows'])
            lc = CL(2 + len(over) + len(outs))
        else: lc = 'C'
        from openpyxl.utils import column_index_from_string as CI
        rng = f'A1:{CL(max(CI(lc), 7))}{last + 1}'; ws.print_area = rng
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        self.meta['tools'][x['key']] = {'sheet': name, 'range': rng}

    def date_default(self, v):
        """A relative default ("today+30") stays relative in the file: =TODAY()+30."""
        import re as _re
        m = _re.match(r'^today\s*(?:([+-])\s*(\d+))?$', str(v).strip().lower())
        if m: return '=TODAY()' + (f'{m.group(1)}{m.group(2)}' if m.group(1) else '')
        return parse_date(v, self.today)

    # ---------- v1.1: documents (letters / contracts filled from a record)
    def pick_block(self, ws, pick, demo_value):
        """Row 4: the record to choose (label, yellow cell with its drop-down, 'not found'); J4 = its row in the table."""
        pt, pc = pick.split('.'); PR = self.RG(pt, pc); _, pcol = find_col(self.s, pick)
        self.put(ws, 'B4', self.T(pcol['label']), self.F(size=11, bold=True))
        pfmt = NUMFMT[col_format(pcol)] if col_format(pcol) in ('date', 'int', 'num', 'money') else None
        self.put(ws, 'C4', demo_value, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL(), pfmt, BOX)
        ws['D4'].fill = fill(CREAM); ws['D4'].border = BOX; ws.merge_cells('C4:D4'); self.dv(ws, 'C4', PR)
        ws.row_dimensions[4].height = 24
        ws['J4'] = f'=IF($C$4="","",IFERROR(MATCH($C$4,{PR},0),""))'
        self.put(ws, 'E4', f'=IF(AND($C$4<>"",$J$4=""),{X(self.T(FIXED["not_found"]))},"")', self.F(bold=True, color='9B1C1C'))

    def head(self, ws, title, hint):
        self.put(ws, 'B1', title, self.F(size=22, bold=True, color=self.P)); ws.row_dimensions[1].height = 34
        b = brand_setting(self.s)
        if b: self.put(ws, 'E1', f'={self.SET(b["key"])}&""', self.F(size=12, bold=True, color=GRAY), align=self.AL('left' if self.rtl else 'right')); ws.merge_cells('E1:G1')
        self.put(ws, 'B2', hint, self.F(size=9, color=GRAY))
        for c in 'BCDEFG': ws[f'{c}3'].fill = fill(self.A)
        ws.row_dimensions[3].height = 4

    def document(self, d):
        T = self.T; sid = 'd:' + d['key']; ws = self.ws[sid]; name = self.names[sid]
        for c, w in zip('ABCDEFGHIJKL', [3, 22, 15, 15, 15, 15, 15, 3, 3, 6, 3, 70]): ws.column_dimensions[c].width = w
        ws.column_dimensions['J'].hidden = True
        self.head(ws, T(d['title']), T(FIXED['form_hint']))
        self.pick_block(ws, d['pick'], self.form_pick({'pick': d['pick']}) if self.demo else None)
        self.put(ws, 'F5', T(FIXED['date']), self.F(color=GRAY), align=self.AL('left' if self.rtl else 'right'))
        self.put(ws, 'G5', '=TODAY()', self.F(bold=True, color=BLUE), CREAM, self.AL(), 'yyyy-mm-dd', BOX)
        self.put(ws, 'L5', T(FIXED['wording']), self.F(bold=True, color='FFFFFF'), GRAY, self.AL(), border=BOX)
        pt = d['pick'].split('.')[0]
        r = 7
        for j, p_ in enumerate(d['paragraphs']):
            txt = T(p_)
            self.put(ws, f'L{r}', txt, self.F(size=9, color=BLUE), CREAM, self.AL(v='top', wrap=True), border=BOX)
            f = f'$L{r}'
            for m in dict.fromkeys(mm.group() for mm in TOK.finditer(p_)):
                mm = TOK.match(m); kind, arg = mm.group(1) or mm.group(3), mm.group(2) or ''
                if kind == 'col':
                    _, col = find_col(self.s, arg); rg = self.RG(*arg.split('.'))
                    v = self.as_text(f'INDEX({rg},$J$4)', col_format(col))
                elif kind == 'set': v = self.set_text(arg)
                else: v = self.as_text('$G$5', 'date')
                f = f'SUBSTITUTE({f},{X(m)},{v})'
            self.put(ws, f'B{r}', f'=IF($J$4="","",{f})', self.F(size=11), align=self.AL(v='top', wrap=True)); ws.merge_cells(f'B{r}:G{r}')
            ws.row_dimensions[r].height = max(18, 16 * lines(txt, 108) + 6)
            self.origin(name, f'B{r}', f'documents[{d["key"]}].paragraphs[{j}]')
            self.meta['doc_cells'].append({'sheet': name, 'cell': f'B{r}', 'label': f'{d["title"]} ¶{j + 1}', 'origin': f'documents[{d["key"]}].paragraphs[{j}]'})
            r += 1
        r += 2
        signs = d.get('sign', [])
        for j in range(0, len(signs), 2):
            for q, lab in enumerate(signs[j:j + 2]):
                c = 'B' if q == 0 else 'E'
                self.put(ws, f'{c}{r}', T(lab), self.F(bold=True))
                self.put(ws, f'{c}{r + 2}', T(FIXED['signature']) + ':  ____________________', self.F(color=GRAY))
                self.put(ws, f'{c}{r + 3}', T(FIXED['date']) + ':  ______________', self.F(color=GRAY))
            r += 5
        if d.get('note'):
            self.put(ws, f'B{r}', T(d['note']), self.F(size=8, italic=True, color=GRAY), align=self.AL(v='top', wrap=True)); ws.merge_cells(f'B{r}:G{r}')
            ws.row_dimensions[r].height = max(14, 12 * lines(T(d['note']), 110) + 4); r += 1
        ws.print_area = f'A1:G{r}'
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        self.meta['documents'][d['key']] = {'sheet': name, 'range': f'A1:G{r}'}

    # ---------- v1.1: checklists (steps dated from a record's start date)
    def checklist(self, c):
        T = self.T; sid = 'c:' + c['key']; ws = self.ws[sid]; name = self.names[sid]; tb = self.tables[c['table']]
        for col, w in zip('ABCDEFGHIJK', [3, 6, 46, 8, 13, 10, 13, 14, 3, 6, 6]): ws.column_dimensions[col].width = w
        ws.column_dimensions['J'].hidden = True; ws.column_dimensions['K'].hidden = True
        self.put(ws, 'B1', T(c['title']), self.F(size=22, bold=True, color=self.P)); ws.row_dimensions[1].height = 34
        self.put(ws, 'B2', T(FIXED['chk_hint']), self.F(size=9, color=GRAY))
        for col in 'BCDEFGH': ws[f'{col}3'].fill = fill(self.A)
        ws.row_dimensions[3].height = 4
        rk = record_key(tb); PR = self.RG(tb['key'], rk['key']); st, sc = c['start'].split('.')
        steps = c['steps']; n = len(steps); H0 = 9
        pick = None; best = None
        if self.demo:
            today = self.today; cand = []
            for i, row in enumerate(tb['demo']):
                d0 = parse_date(row.get(sc), today) if find_col(self.s, c['start'])[1]['type'] == 'date' else None
                if d0 and row.get(rk['key']) not in (None, ''): cand.append((abs((today - d0).days - 12), i, d0))
            if cand:
                _, best, d0 = min(cand); pick = self.demo_value(rk, tb['demo'][best][rk['key']]); best = d0
        self.put(ws, 'B4', T(rk['label']), self.F(size=11, bold=True))
        self.put(ws, 'D4', pick, self.F(size=12, bold=True, color=BLUE), CREAM, self.AL(), None, BOX)
        for col in 'EF': ws[f'{col}4'].fill = fill(CREAM); ws[f'{col}4'].border = BOX
        ws.merge_cells('D4:F4'); self.dv(ws, 'D4', PR); ws.row_dimensions[4].height = 24
        ws['J4'] = f'=IF($D$4="","",IFERROR(MATCH($D$4,{PR},0),""))'
        self.put(ws, 'G4', f'=IF(AND($D$4<>"",$J$4=""),{X(T(FIXED["not_found"]))},"")', self.F(bold=True, color='9B1C1C'))
        _, scol = find_col(self.s, c['start'])
        self.put(ws, 'B5', T(scol['label']), self.F(size=11))
        self.put(ws, 'D5', f'=IF($J$4="","",IF(INDEX({self.RG(st, sc)},$J$4)="","",INDEX({self.RG(st, sc)},$J$4)))', self.F(size=11, bold=True), AUTO, self.AL(), 'yyyy-mm-dd', BOX)
        for rr in (5, 6):
            for col in 'EF': ws[f'{col}{rr}'].fill = fill(AUTO); ws[f'{col}{rr}'].border = BOX
            ws.merge_cells(f'D{rr}:F{rr}')
        self.put(ws, 'B6', T(FIXED['progress']), self.F(size=11))
        YES, DONE, LATE, TODO = self.LI(YESNO, 'yes'), self.LI(STEPSTAT, 'done'), self.LI(STEPSTAT, 'late'), self.LI(STEPSTAT, 'todo')
        self.put(ws, 'D6', f'=IF($D$5="","",COUNTIF($F${H0 + 1}:$F${H0 + n},{YES})/{n})', self.F(size=14, bold=True, color=self.P), AUTO, self.AL(), '0%', BOX)
        for col, h in zip('BCDEFGH', ['#', T(FIXED['step']), T(FIXED['days']), T(FIXED['due']), T(FIXED['done']), T(FIXED['done_on']), T(FIXED['stepstat'])]):
            self.put(ws, f'{col}{H0}', h, self.F(bold=True, color='FFFFFF'), self.P if col not in 'EH' else self.PC, self.AL('center', wrap=True), border=BOX)
        ws.row_dimensions[H0].height = 30
        yes_l = self.T(FIXED['yes'])
        for i, s_ in enumerate(steps):
            r = H0 + 1 + i; txt = T(s_['label'])
            self.put(ws, f'B{r}', i + 1, self.F(color=GRAY), align=self.AL('center'), border=BOX)
            self.put(ws, f'C{r}', txt, self.F(), align=self.AL(wrap=True), border=BOX)
            self.put(ws, f'D{r}', s_['days'], self.F(color=BLUE), align=self.ALN(), fmt='0', border=BOX)
            self.put(ws, f'E{r}', f'=IF($D$5="","",$D$5+D{r})', self.F(bold=True), AUTO, self.ALN(), 'yyyy-mm-dd', BOX)
            done = done_on = None
            if self.demo and best is not None:
                due = best + dt.timedelta(days=s_['days'])
                late_ones = [j for j, x in enumerate(steps) if best + dt.timedelta(days=x['days']) < self.today]
                if due < self.today and i != (late_ones[-1] if late_ones else -1): done, done_on = yes_l, due
            self.put(ws, f'F{r}', done, self.F(bold=True), align=self.AL('center'), border=BOX)
            self.put(ws, f'G{r}', done_on, self.F(), align=self.ALN(), fmt='yyyy-mm-dd', border=BOX)
            self.put(ws, f'H{r}', f'=IF(E{r}="","",IF(F{r}={YES},{DONE},IF(E{r}<TODAY(),{LATE},{TODO})))', self.F(bold=True), AUTO, self.AL('center'), border=BOX)
            ws.row_dimensions[r].height = max(20, 15 * lines(txt, 54) + 5)
        last = H0 + n
        self.dv(ws, f'F{H0 + 1}:F{last}', self.LR(YESNO))
        for j, (key, style) in enumerate((('late', 'bad'), ('done', 'good'), ('todo', None))):
            ws[f'K{1 + j}'] = f'={self.LI(STEPSTAT, key)}'; ws[f'K{1 + j}'].number_format = ';;;'
            if style: self.cf(ws, f'H{H0 + 1}:H{last}', f'H{H0 + 1}=$K${1 + j}', style)
        ws.freeze_panes = f'A{H0 + 1}'
        ws.print_area = f'A1:H{last}'
        ws.page_setup.orientation = 'portrait'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
        self.meta['checklists'][c['key']] = {'sheet': name, 'range': f'A1:H{last}'}
        self.meta['checks'].append({'sheet': name, 'col': 'E', 'first': H0 + 1, 'last': last, 'origin': f'checklists[{c["key"]}]', 'label': c['title']})
        self.origin(name, 'E', f'checklists[{c["key"]}]')

def parse_when(w):
    import re
    m = re.match(r'^\s*(<=|>=|<>|=|<|>)\s*(.+)$', w)
    return m.group(1), m.group(2)


def build(spec, lang, out_path, demo=False, raw=False, today=None):
    meta = Builder(spec, lang, demo, raw, today).build(out_path)
    return meta


if __name__ == '__main__':
    a = sys.argv[1:]
    spec = json.load(open(a[0], encoding='utf8')); lang, out = a[1], a[2]
    today = dt.date.fromisoformat(a[a.index('--today') + 1]) if '--today' in a else None
    meta = build(spec, lang, out, demo='--demo' in a, raw='--raw' in a, today=today)
    json.dump(meta, open(out + '.meta.json', 'w', encoding='utf8'), ensure_ascii=False)
    print(json.dumps({'lang': lang, 'out': out, 'sheets': len(meta['sheets'])}, ensure_ascii=False))
