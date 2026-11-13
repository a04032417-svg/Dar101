#!/usr/bin/env python3
"""validate(spec) -> [error, ...] — everything SPEC.md requires before a build: structure and limits, keys, sheet names in every
language, DSL tokens that point at real tables/columns/settings/lists, only the allowed functions, calc columns that only read their
own row, no circular references, demo rows of the right type, complete translations, Etsy listing limits.
CLI: python3 validate.py spec.json   -> prints {"ok": bool, "errors": [...]} (exit 1 when not ok)"""
import sys, os, re, json, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (LANGS, TR_LANGS, ALLOWED, XLFN, COL_TYPES, FORMATS, NUMERIC, SET_TYPES, YESNO, KEY_RE, FIXED, tokens, normalize,
                    substitute, segments, find_col, col_format, main_date, texts, sheet_names, bad_sheet_name, parse_date, parse_time,
                    list_by_key, series_date, tr, STEPSTAT, PH, TOK, FIXED)
from openpyxl.formula import Tokenizer

TOP = {'fx', 'id', 'slug', 'profession', 'name', 'tagline', 'price_usd', 'colors', 'settings', 'lists', 'tables', 'dashboard', 'forms', 'guide', 'listing', 'i18n'}
OPT_TOP = {'forms', 'signature', 'competitors', 'tools', 'messages', 'documents', 'checklists', 'suite', 'insights'}  # suite: contract v1.2 (Dar 3.34.0) — one file of a field's suite
TOP |= OPT_TOP
COLUMN_KEYS = {'key', 'label', 'type', 'width', 'list', 'ref', 'format', 'formula', 'required', 'visual'}
TEXT_OK = re.compile(r'^"(?:[^A-Za-zÀ-￿]*|Y|M|D|MD|YM|YD|(?:https?://|mailto:|tel:)[^"\s]*)"$')
LABEL_BAD = re.compile(r'^[=<>+@-]|[*?~]')


class V:
    def __init__(self, spec):
        self.s = spec; self.err = []
    def e(self, where, msg): self.err.append(f'{where}: {msg}')

    # ---------- small checkers
    def obj(self, d, where, req, opt=()):
        if not isinstance(d, dict): self.e(where, f'must be an object, got {type(d).__name__}'); return False
        for k in req:
            if k not in d: self.e(where, f'missing "{k}"')
        extra = set(d) - set(req) - set(opt)
        if extra: self.e(where, f'unknown field(s) {sorted(extra)} — allowed: {sorted(set(req) | set(opt))}')
        return all(k in d for k in req)
    def text(self, v, where, mx, mn=1):
        if not isinstance(v, str) or len(v.strip()) < mn: self.e(where, f'must be a text of at least {mn} character(s)'); return False
        if len(v) > mx: self.e(where, f'{len(v)} characters, {mx} at most: {v[:60]!r}'); return False
        if v.lstrip().startswith('='): self.e(where, 'must not start with "=" (it would become a formula)'); return False
        return True
    def arr(self, v, where, mn, mx):
        if not isinstance(v, list): self.e(where, 'must be a list'); return False
        if not mn <= len(v) <= mx: self.e(where, f'{len(v)} items, {mn}..{mx} required'); return False
        return True
    def key(self, v, where, seen):
        if not isinstance(v, str) or not KEY_RE.match(v): self.e(where, f'key {v!r} must match [a-z][a-z0-9_]{{1,20}}'); return
        if v in seen: self.e(where, f'key {v!r} is used twice')
        seen.add(v)

    # ---------- formulas
    def formula(self, f, where, allow, table=None, ins=None):
        """allow: set of token kinds allowed here; table: the own table (for {col:}); ins: tool input keys (for {in:})."""
        if not isinstance(f, str) or not f.strip().lstrip('='): self.e(where, 'formula is empty'); return []
        for is_s, s in segments(f.strip().lstrip('=')):
            if is_s and re.search(r'\{(col|range|set|list|in|today|pick)', s): self.e(where, f'token inside a text literal {s} — tokens must stay outside quotes')
        if f.count('"') % 2: self.e(where, 'unbalanced double quotes'); return []
        g = normalize(f); refs = []
        for kind, arg in tokens(g):
            tag = '{' + kind + (':' + arg if arg else '') + '}'
            if kind not in allow: self.e(where, f'{tag} is not allowed here (allowed: {", ".join("{" + a + "}" for a in sorted(allow))})'); continue
            if kind == 'in':
                if arg not in (ins or ()): self.e(where, f'unknown input {tag} — this tool has: {", ".join(ins or [])}')
                continue
            if kind == 'col':
                cols = {c.get('key'): c for c in table.get('columns', []) if isinstance(c, dict)} if table else {}
                if arg not in cols: self.e(where, f'unknown column {tag} — table {table.get("key") if table else "?"} has: {", ".join(cols)}')
                else: refs.append((table['key'], arg))
            elif kind == 'range':
                tb, c = find_col(self.s, arg)
                if tb is None: self.e(where, f'unknown table in {tag} — tables: {", ".join(t.get("key", "?") for t in self.s.get("tables", []) if isinstance(t, dict))}')
                elif c is None: self.e(where, f'unknown column in {tag} — table {tb["key"]} has: {", ".join(c.get("key", "?") for c in tb.get("columns", []) if isinstance(c, dict))}')
                else: refs.append((tb['key'], c['key']))
            elif kind == 'set':
                if arg not in {s.get('key') for s in self.s.get('settings', []) if isinstance(s, dict)}: self.e(where, f'unknown setting {tag}')
            elif kind == 'list':
                l, _, v = arg.partition('.'); L = list_by_key(self.s, l)
                if L is None: self.e(where, f'unknown list in {tag}')
                elif v not in [x.get('key') for x in L.get('values', []) if isinstance(x, dict)]: self.e(where, f'unknown value in {tag} — list {l} has: {", ".join(x.get("key", "?") for x in L.get("values", []))}')
        # functions, names and literals, on a tokenized copy where every DSL token is a harmless name
        ph = substitute(g, lambda k, a: '_tok_')
        try: items = Tokenizer('=' + ph).items
        except Exception as x: self.e(where, f'formula does not parse ({x}): {f}'); return refs
        depth = 0
        for it in items:
            if it.type == 'FUNC' and it.subtype == 'OPEN':
                depth += 1; name = it.value[:-1].upper().replace('_XLFN.', '')
                if name not in ALLOWED: self.e(where, f'function {name} is not allowed — allowed: {" ".join(sorted(ALLOWED))}')
            elif it.type in ('FUNC', 'PAREN') and it.subtype == 'CLOSE': depth -= 1
            elif it.type == 'PAREN' and it.subtype == 'OPEN': depth += 1
            elif it.type == 'OPERAND' and it.subtype == 'RANGE' and it.value != '_tok_':
                self.e(where, f'{it.value!r} is not allowed: no cell addresses, sheet names or named ranges — use {{col:..}} / {{range:t.c}} / {{set:..}}')
            elif it.type == 'OPERAND' and it.subtype == 'TEXT' and not TEXT_OK.match(it.value):
                self.e(where, f'text literal {it.value} is language-specific — refer to a list label with {{list:list.value}} instead')
            elif it.type == 'OPERAND' and it.subtype == 'ERROR': self.e(where, f'error literal {it.value} in the formula')
            if depth < 0: break
        if depth != 0: self.e(where, 'unbalanced parentheses')
        return refs

    # ---------- the sections
    def run(self):
        s = self.s
        if not self.obj(s, 'spec', sorted(TOP - OPT_TOP), OPT_TOP):
            if not isinstance(s, dict): return self.err
        if s.get('fx') != 1: self.e('fx', 'must be 1')
        su = s.get('suite')
        if su is not None and not (isinstance(su, dict) and set(su) <= {'key', 'part', 'of', 'focus'} and isinstance(su.get('key'), str) and isinstance(su.get('part'), int) and isinstance(su.get('of'), int) and 1 <= su['part'] <= su['of'] <= 8 and isinstance(su.get('focus'), str)):
            self.e('suite', 'must be {"key","part","of","focus"} with 1 <= part <= of <= 8')
        if not (isinstance(s.get('id'), str) and re.fullmatch(r'[a-z0-9-]{1,60}', s['id'])): self.e('id', 'must match [a-z0-9-], 60 characters at most')
        if not (isinstance(s.get('slug'), str) and re.fullmatch(r'[a-z0-9-]{1,50}', s['slug'])): self.e('slug', 'must match [a-z0-9-], 50 characters at most')
        self.text(s.get('profession'), 'profession', 80); self.text(s.get('name'), 'name', 40); self.text(s.get('tagline'), 'tagline', 80)
        p = s.get('price_usd')
        if not (isinstance(p, (int, float)) and not isinstance(p, bool) and 9 <= p <= 49): self.e('price_usd', 'must be a number 9..49')
        c = s.get('colors')
        if self.obj(c, 'colors', ['primary', 'accent']):
            for k in ('primary', 'accent'):
                if not (isinstance(c[k], str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', c[k])): self.e(f'colors.{k}', 'must be #RRGGBB')
            if isinstance(c.get('primary'), str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', c['primary']):
                r, g_, b = (int(c['primary'][i:i + 2], 16) / 255 for i in (1, 3, 5))
                lum = 0.2126 * r + 0.7152 * g_ + 0.0722 * b
                if lum > 0.45: self.e('colors.primary', f'too light for white header text (luminance {lum:.2f}, 0.45 at most)')
        self.settings(); self.lists(); self.tables(); self.dashboard(); self.forms(); self.guide(); self.listing()
        self.tools(); self.messages(); self.documents(); self.checklists(); self.signature(); self.insights(); self.visuals()
        self.cycles(); self.sheets_en()
        if not self.err: self.i18n()
        return self.err

    def settings(self):
        st = self.s.get('settings'); seen = set()
        if not self.arr(st, 'settings', 3, 20): return
        for i, x in enumerate(st):
            w = f'settings[{x.get("key", i) if isinstance(x, dict) else i}]'
            if not self.obj(x, w, ['key', 'label', 'type', 'default'], ['list']): continue
            self.key(x['key'], w + '.key', seen); self.text(x['label'], w + '.label', 60)
            t, v = x['type'], x['default']
            if t not in SET_TYPES: self.e(w + '.type', f'{t!r} not one of {SET_TYPES}'); continue
            if t == 'list':
                L = list_by_key(self.s, x.get('list'))
                if L is None: self.e(w + '.list', f'unknown list {x.get("list")!r}')
                elif v not in [y.get('key') for y in L.get('values', [])]: self.e(w + '.default', f'{v!r} is not a value key of list {x["list"]}')
            elif 'list' in x: self.e(w + '.list', 'only for type list')
            if t in ('pct', 'money', 'int', 'num') and not (isinstance(v, (int, float)) and not isinstance(v, bool)): self.e(w + '.default', f'must be a number for type {t}')
            if t == 'int' and isinstance(v, float) and not v.is_integer(): self.e(w + '.default', 'must be a whole number')
            if t == 'pct' and isinstance(v, (int, float)) and not -1 <= v <= 10: self.e(w + '.default', 'a percentage is a fraction: 0.15 for 15%')
            if t == 'text' and not isinstance(v, str): self.e(w + '.default', 'must be a text')
            if t == 'text' and isinstance(v, str) and v.startswith('='): self.e(w + '.default', 'must not start with "="')
            if t == 'date' and parse_date(v, dt.date.today()) is None: self.e(w + '.default', 'must be "YYYY-MM-DD" or "today", "today-N", "today+N"')

    def lists(self):
        ls = self.s.get('lists'); seen = set()
        if not self.arr(ls, 'lists', 1, 30): return
        for i, l in enumerate(ls):
            w = f'lists[{l.get("key", i) if isinstance(l, dict) else i}]'
            if not self.obj(l, w, ['key', 'label', 'values']): continue
            self.key(l['key'], w + '.key', seen)
            if l['key'] in (YESNO, STEPSTAT): self.e(w + '.key', f'"{l["key"]}" is a built-in list name')
            self.text(l['label'], w + '.label', 40)
            if not self.arr(l['values'], w + '.values', 2, 30): continue
            vk = set(); labels = set()
            for j, v in enumerate(l['values']):
                wv = f'{w}.values[{j}]'
                if not self.obj(v, wv, ['key', 'label']): continue
                self.key(v['key'], wv + '.key', vk)
                if self.text(v['label'], wv + '.label', 40):
                    if LABEL_BAD.search(v['label']): self.e(wv + '.label', f'{v["label"]!r}: a list label must not start with = < > + - @ nor contain * ? ~ (formulas compare with it)')
                    if v['label'].lower() in labels: self.e(wv + '.label', f'{v["label"]!r} is used twice in this list')
                    labels.add(v['label'].lower())

    def tables(self):
        tb = self.s.get('tables'); seen = set()
        if not self.arr(tb, 'tables', 3, 20): return
        for i, t in enumerate(tb):
            w = f'tables[{t.get("key", i) if isinstance(t, dict) else i}]'
            if not self.obj(t, w, ['key', 'sheet', 'title', 'hint', 'rows', 'columns', 'demo'], ['alerts']): continue
            self.key(t['key'], w + '.key', seen); self.text(t['title'], w + '.title', 60); self.text(t['hint'], w + '.hint', 200)
            bad = bad_sheet_name(t['sheet'])
            if bad: self.e(w + '.sheet', f'{t["sheet"]!r}: {bad}')
            if not (isinstance(t['rows'], int) and not isinstance(t['rows'], bool) and 50 <= t['rows'] <= 3000): self.e(w + '.rows', 'must be a whole number 50..3000')
            if not self.arr(t['columns'], w + '.columns', 2, 40): continue
            ck = set()
            for j, c in enumerate(t['columns']):
                wc = f'{w}.columns[{c.get("key", j) if isinstance(c, dict) else j}]'
                if not self.obj(c, wc, ['key', 'label', 'type'], COLUMN_KEYS - {'key', 'label', 'type'}): continue
                self.key(c['key'], wc + '.key', ck); self.text(c['label'], wc + '.label', 40)
                ty = c['type']
                if ty not in COL_TYPES: self.e(wc + '.type', f'{ty!r} not one of {COL_TYPES}'); continue
                if 'width' in c and not (isinstance(c['width'], (int, float)) and 4 <= c['width'] <= 80): self.e(wc + '.width', 'must be 4..80')
                if ty == 'list':
                    if list_by_key(self.s, c.get('list')) is None: self.e(wc + '.list', f'unknown list {c.get("list")!r}')
                elif 'list' in c: self.e(wc + '.list', 'only for type list')
                if ty == 'ref':
                    rt, rc = find_col(self.s, c.get('ref'))
                    if rc is None: self.e(wc + '.ref', f'{c.get("ref")!r} is not an existing "table.column"')
                elif 'ref' in c: self.e(wc + '.ref', 'only for type ref')
                if ty == 'calc':
                    if c.get('format') not in FORMATS: self.e(wc + '.format', f'{c.get("format")!r} not one of {FORMATS}')
                    if c.get('required'): self.e(wc + '.required', 'a calc column cannot be required')
                else:
                    for k in ('format', 'formula'):
                        if k in c: self.e(wc + '.' + k, 'only for type calc')
                if 'required' in c and not isinstance(c['required'], bool): self.e(wc + '.required', 'must be true or false')
            if not any(isinstance(c, dict) and c.get('required') and c.get('type') != 'calc' for c in t['columns']): self.e(w, 'at least one input column must be "required": true')
            for c in t['columns']:
                if isinstance(c, dict) and c.get('type') == 'calc' and isinstance(c.get('key'), str):
                    c['_refs'] = self.formula(c.get('formula'), f'{w}.columns[{c["key"]}].formula', {'col', 'range', 'set', 'list', 'today'}, t)
            for j, a in enumerate(t.get('alerts', []) if isinstance(t.get('alerts', []), list) else []):
                wa = f'{w}.alerts[{j}]'
                if not self.obj(a, wa, ['column', 'when', 'style']): continue
                if a['column'] not in ck: self.e(wa + '.column', f'unknown column {a["column"]!r}')
                if a['style'] not in ('bad', 'warn', 'good'): self.e(wa + '.style', 'must be bad, warn or good')
                self.when(a['when'], wa + '.when', t)
            if 'alerts' in t and not isinstance(t['alerts'], list): self.e(w + '.alerts', 'must be a list')
            self.demo(t, w)

    def when(self, when, where, table):
        m = re.match(r'^\s*(<=|>=|<>|=|<|>)\s*(.+)$', when or '') if isinstance(when, str) else None
        if not m: self.e(where, 'must be "<op> <value>" with op one of = <> < <= > >= (e.g. "> 0", "< {today}", "= {list:status.lost}")'); return
        self.formula(m.group(2), where, {'col', 'set', 'list', 'today'}, table)

    def demo(self, t, w):
        rows = t['demo']
        if not self.arr(rows, w + '.demo', 5, 3000): return  # 2026-11-11: realistic volumes (a year of bookings, a full rent roll)
        cols = {c['key']: c for c in t['columns'] if isinstance(c, dict) and isinstance(c.get('key'), str)}
        req = next((c for c in t['columns'] if isinstance(c, dict) and c.get('required') and c.get('type') != 'calc'), None)
        today = dt.date.today()
        for j, r in enumerate(rows):
            wr = f'{w}.demo[{j}]'
            if not isinstance(r, dict): self.e(wr, 'must be an object'); continue
            if req and r.get(req['key']) in (None, ''): self.e(wr, f'the required column {req["key"]!r} is empty (the row would not count)')
            for k, v in r.items():
                c = cols.get(k)
                if c is None: self.e(wr, f'unknown column {k!r}'); continue
                if c['type'] == 'calc': self.e(wr, f'{k!r} is a calc column — demo rows hold input columns only'); continue
                if v is None or v == '': continue
                self.demo_value(c, v, f'{wr}.{k}', today)

    def demo_value(self, c, v, w, today):
        ty = c['type']; num = isinstance(v, (int, float)) and not isinstance(v, bool)
        if ty in ('int', 'num', 'money', 'pct') and not num: self.e(w, f'{v!r} must be a number')
        elif ty == 'int' and isinstance(v, float) and not v.is_integer(): self.e(w, f'{v!r} must be a whole number')
        elif ty == 'date' and parse_date(v, today) is None: self.e(w, f'{v!r} must be "YYYY-MM-DD" or "today", "today-N", "today+N"')
        elif ty == 'time' and parse_time(v) is None: self.e(w, f'{v!r} must be "HH:MM"')
        elif ty == 'bool' and v not in (True, False, 'yes', 'no'): self.e(w, f'{v!r} must be true/false or "yes"/"no"')
        elif ty == 'list':
            L = list_by_key(self.s, c.get('list'))
            if L and v not in [x.get('key') for x in L.get('values', [])]: self.e(w, f'{v!r} is not a value key of list {c["list"]} ({", ".join(x.get("key", "?") for x in L["values"])})')
        elif ty == 'ref':
            rt, rc = find_col(self.s, c.get('ref'))
            if rc is not None and rc.get('type') != 'calc':
                pool = [r.get(rc['key']) for r in rt.get('demo', []) if isinstance(r, dict)]
                if v not in pool: self.e(w, f'{v!r} is not a {c["ref"]} value of the demo rows')
        elif ty in ('text', 'link'):
            if not isinstance(v, (str, int, float)) or isinstance(v, bool): self.e(w, f'{v!r} must be a text')
            elif isinstance(v, str) and v.startswith('='): self.e(w, 'must not start with "="')

    def dashboard(self):
        d = self.s.get('dashboard')
        if not self.obj(d, 'dashboard', ['title', 'kpis', 'monthly'], ['breakdowns']): return
        bad = bad_sheet_name(d['title'])
        if bad: self.e('dashboard.title', f'{d["title"]!r} (it is also the sheet name): {bad}')
        if self.arr(d['kpis'], 'dashboard.kpis', 6, 30):
            for i, k in enumerate(d['kpis']):
                w = f'dashboard.kpis[{i}]'
                if not self.obj(k, w, ['label', 'formula', 'format'], ['alert']): continue
                self.text(k['label'], w + '.label', 40)
                if k['format'] not in FORMATS: self.e(w + '.format', f'{k["format"]!r} not one of {FORMATS}')
                self.formula(k['formula'], w + '.formula', {'range', 'set', 'list', 'today'})
                if 'alert' in k and self.obj(k['alert'], w + '.alert', ['when', 'style']):
                    if k['alert']['style'] not in ('bad', 'warn', 'good'): self.e(w + '.alert.style', 'must be bad, warn or good')
                    m = re.match(r'^\s*(<=|>=|<>|=|<|>)\s*(.+)$', k['alert']['when']) if isinstance(k['alert']['when'], str) else None
                    if not m: self.e(w + '.alert.when', 'must be "<op> <value>"')
                    else: self.formula(m.group(2), w + '.alert.when', {'set', 'list', 'today'})
        m = d['monthly']
        if self.obj(m, 'dashboard.monthly', ['title', 'date', 'series']):
            self.text(m['title'], 'dashboard.monthly.title', 60)
            tb, c = find_col(self.s, m['date'])
            if c is None or col_format(c) != 'date': self.e('dashboard.monthly.date', f'{m["date"]!r} must be an existing date column "table.column"')
            if self.arr(m['series'], 'dashboard.monthly.series', 1, 4):
                for i, x in enumerate(m['series']):
                    w = f'dashboard.monthly.series[{i}]'
                    if not self.obj(x, w, ['label', 'sum'], ['date']): continue
                    self.text(x['label'], w + '.label', 30)
                    tb, c = find_col(self.s, x['sum'])
                    if c is None: self.e(w + '.sum', f'{x["sum"]!r} is not an existing "table.column"'); continue
                    if col_format(c) not in NUMERIC: self.e(w + '.sum', f'{x["sum"]!r} is not a number column')
                    dc = series_date(self.s, x)
                    if dc is None: self.e(w, f'table {tb["key"]} has no date column to place {x["sum"]} in months (add "date": "table.column")')
                    else:
                        t2, c2 = find_col(self.s, dc)
                        if c2 is None or col_format(c2) != 'date' or t2['key'] != tb['key']: self.e(w + '.date', f'{dc!r} must be a date column of table {tb["key"]}')
        bd = d.get('breakdowns', [])
        if self.arr(bd, 'dashboard.breakdowns', 0, 4):
            for i, b in enumerate(bd):
                w = f'dashboard.breakdowns[{i}]'
                if not self.obj(b, w, ['title', 'by', 'agg'], ['value']): continue
                self.text(b['title'], w + '.title', 50)
                tb, c = find_col(self.s, b['by'])
                if c is None: self.e(w + '.by', f'{b["by"]!r} is not an existing "table.column"'); continue
                if c['type'] not in ('list', 'ref', 'bool'): self.e(w + '.by', f'{b["by"]!r} must be a list, ref or bool column (one row per value)')
                if b['agg'] not in ('sum', 'count'): self.e(w + '.agg', 'must be sum or count')
                if b['agg'] == 'sum' or 'value' in b:
                    t2, c2 = find_col(self.s, b.get('value'))
                    if c2 is None: self.e(w + '.value', f'{b.get("value")!r} is not an existing "table.column"')
                    elif t2['key'] != tb['key']: self.e(w + '.value', f'must be a column of table {tb["key"]} like "by"')
                    elif b['agg'] == 'sum' and not is_num(c2): self.e(w + '.value', f'{b["value"]!r} is not a number column')

    def forms(self):
        fs = self.s.get('forms', []); seen = set()
        if not self.arr(fs, 'forms', 0, 10): return
        for i, f in enumerate(fs):
            w = f'forms[{f.get("key", i) if isinstance(f, dict) else i}]'
            if not self.obj(f, w, ['key', 'sheet', 'title', 'pick', 'fields'], ['lines']): continue
            self.key(f['key'], w + '.key', seen); self.text(f['title'], w + '.title', 50)
            bad = bad_sheet_name(f['sheet'])
            if bad: self.e(w + '.sheet', f'{f["sheet"]!r}: {bad}')
            pt, pc = find_col(self.s, f['pick'])
            if pc is None: self.e(w + '.pick', f'{f["pick"]!r} is not an existing "table.column"'); continue
            if self.arr(f['fields'], w + '.fields', 1, 20):
                for j, x in enumerate(f['fields']):
                    wf = f'{w}.fields[{j}]'
                    if not self.obj(x, wf, ['label'], ['value', 'formula', 'format']): continue
                    self.text(x['label'], wf + '.label', 40)
                    if ('value' in x) == ('formula' in x): self.e(wf, 'needs exactly one of "value" or "formula"'); continue
                    if 'value' in x:
                        t2, c2 = find_col(self.s, x['value'])
                        if c2 is None: self.e(wf + '.value', f'{x["value"]!r} is not an existing "table.column"')
                        elif t2['key'] != pt['key']: self.e(wf + '.value', f'must be a column of {pt["key"]} (the table of "pick")')
                        if 'format' in x: self.e(wf + '.format', 'only with "formula" (a value keeps its column format)')
                    else:
                        if x.get('format') not in FORMATS: self.e(wf + '.format', f'{x.get("format")!r} not one of {FORMATS}')
                        self.formula(x['formula'], wf + '.formula', {'range', 'set', 'list', 'today', 'pick'})
            if 'lines' in f and self.obj(f['lines'], w + '.lines', ['from', 'match', 'columns'], ['max']):
                L = f['lines']; lt = next((t for t in self.s.get('tables', []) if isinstance(t, dict) and t.get('key') == L['from']), None)
                if lt is None: self.e(w + '.lines.from', f'unknown table {L["from"]!r}'); continue
                mt, mc = find_col(self.s, L['match'])
                if mc is None or mt['key'] != lt['key']: self.e(w + '.lines.match', f'must be a column of {L["from"]}')
                ks = [c.get('key') for c in lt['columns']]
                if self.arr(L['columns'], w + '.lines.columns', 1, 6):
                    for k in L['columns']:
                        if k not in ks: self.e(w + '.lines.columns', f'unknown column {k!r} of {L["from"]}')
                if 'max' in L and not (isinstance(L['max'], int) and 1 <= L['max'] <= 40): self.e(w + '.lines.max', 'must be 1..40')

    def guide(self):
        g = self.s.get('guide')
        if self.arr(g, 'guide', 5, 20):
            for i, x in enumerate(g): self.text(x, f'guide[{i}]', 240)

    def listing(self):
        L = self.s.get('listing')
        if not self.obj(L, 'listing', ['title', 'headline', 'tags', 'description', 'features']): return
        if self.text(L['title'], 'listing.title', 140):
            if re.search(r'[$^`]', L['title']): self.e('listing.title', 'Etsy titles cannot contain $ ^ `')
            if L['title'].count('&') > 1: self.e('listing.title', 'Etsy allows "&" only once in a title')
        self.text(L['headline'], 'listing.headline', 80)
        if self.arr(L['tags'], 'listing.tags', 13, 13):
            seen = set()
            for i, t in enumerate(L['tags']):
                if not isinstance(t, str) or not 1 <= len(t) <= 20: self.e(f'listing.tags[{i}]', f'{t!r}: 1..20 characters'); continue
                if not re.fullmatch(r"[A-Za-z0-9 '\-]+", t): self.e(f'listing.tags[{i}]', f'{t!r}: letters, digits, spaces, - and \' only')
                if t.lower() in seen: self.e(f'listing.tags[{i}]', f'{t!r} is used twice')
                seen.add(t.lower())
        d = L['description']
        if not isinstance(d, str) or not 900 <= len(d) <= 2500: self.e('listing.description', f'{len(d) if isinstance(d, str) else "?"} characters, 900..2500 required')
        if self.arr(L['features'], 'listing.features', 6, 14):
            for i, x in enumerate(L['features']): self.text(x, f'listing.features[{i}]', 70)

    def cycles(self):
        """Calc columns must not depend on themselves through {col:} or {range:} (that is a circular reference)."""
        g = {}
        for t in self.s.get('tables', []) if isinstance(self.s.get('tables'), list) else []:
            for c in t.get('columns', []) if isinstance(t, dict) else []:
                if isinstance(c, dict) and c.get('type') == 'calc': g[(t['key'], c['key'])] = [r for r in c.pop('_refs', []) or []]
        state, seen = {}, set()
        def dfs(n, path):
            state[n] = 1
            for m in g.get(n, []):
                if m not in g: continue
                if state.get(m) == 1:                       # back edge: the cycle is the path from m to n
                    cyc = path[path.index(m):] + [m]
                    key = frozenset(cyc)
                    if key not in seen:
                        seen.add(key); self.e(f'tables[{cyc[0][0]}].columns[{cyc[0][1]}].formula', 'circular reference: ' + ' -> '.join(f'{x}.{y}' for x, y in cyc))
                elif state.get(m) is None: dfs(m, path + [m])
            state[n] = 2
        for n in g:
            if state.get(n) is None: dfs(n, [n])

    def i18n(self):
        s = self.s; m = s.get('i18n')
        if not isinstance(m, dict): self.e('i18n', 'must be an object with the 14 languages'); return
        miss = [l for l in TR_LANGS if l not in m]; extra = [l for l in m if l not in ('ar', 'fr', 'es', 'de', 'it', 'pt', 'tr', 'nl', 'ru', 'fa', 'ur', 'hi', 'zh', 'id')]
        if miss: self.e('i18n', f'missing languages {miss}')
        if extra: self.e('i18n', f'unknown languages {extra} (the 14 are {" ".join(TR_LANGS)})')
        need = texts(s)
        for lang in TR_LANGS:
            d = m.get(lang)
            if not isinstance(d, dict): continue
            gone = [e for e in need if not isinstance(d.get(e), str) or not d[e].strip()]
            if gone:
                self.e(f'i18n.{lang}', f'{len(gone)} missing or empty translation(s): ' + '; '.join(f'{e!r} ({need[e]})' for e in gone[:25]) + (' ...' if len(gone) > 25 else ''))
                continue
            for e in need:
                if d[e].lstrip().startswith('='): self.e(f'i18n.{lang}[{e!r}]', 'must not start with "="')
            T = tr(s, lang); names = sheet_names(s, T); low = {}
            for sid, n in names:
                bad = bad_sheet_name(n)
                if bad: self.e(f'i18n.{lang}', f'sheet name {n!r} ({sid}): {bad}')
                if n.lower() in low: self.e(f'i18n.{lang}', f'two sheets are both named {n!r} ({low[n.lower()]}, {sid})')
                low[n.lower()] = sid
            for m_ in s.get('messages', []):
                a, b = sorted(PH.findall(m_['text'])), sorted(PH.findall(T(m_['text'])))
                if a != b: self.e(f'i18n.{lang}', f'message {m_["key"]}: the translation must keep the placeholders {a} exactly, got {b}')
            for d_ in s.get('documents', []):
                for p_ in d_['paragraphs']:
                    a, b = sorted(m.group() for m in TOK.finditer(p_)), sorted(m.group() for m in TOK.finditer(T(p_)))
                    if a != b: self.e(f'i18n.{lang}', f'document {d_["key"]}: the translation of {p_[:40]!r}... must keep the tokens {a} exactly, got {b}')
            for l in s['lists'] + [list_by_key(s, YESNO)] + ([list_by_key(s, STEPSTAT)] if s.get('checklists') else []):
                seen = {}
                for v in l['values']:
                    x = T(v['label'])
                    if LABEL_BAD.search(x): self.e(f'i18n.{lang}', f'list label {x!r} ({l["key"]}.{v["key"]}) must not start with = < > + - @ nor contain * ? ~')
                    if x.lower() in seen: self.e(f'i18n.{lang}', f'list {l["key"]}: {seen[x.lower()]} and {v["key"]} are both translated {x!r} (formulas could not tell them apart)')
                    seen[x.lower()] = v['key']


def is_num(c): return col_format(c) in NUMERIC


def _ext(V):
    """v1.1: profession-specific services."""
    def sheets_en(self):
        try: names = sheet_names(self.s, lambda x: x)
        except Exception: return
        low = {}
        for sid, n in names:
            if isinstance(n, str) and n.lower() in low: self.e('sheets', f'two sheets are both named {n!r} ({low[n.lower()]}, {sid})')
            if isinstance(n, str): low[n.lower()] = sid
        self._sheet_names = [n for _, n in names]

    def signature(self):
        s = self.s
        if 'competitors' in s and self.arr(s['competitors'], 'competitors', 3, 8):
            for i, c in enumerate(s['competitors']):
                if self.obj(c, f'competitors[{i}]', ['what', 'lacks']): self.text(c['what'], f'competitors[{i}].what', 80); self.text(c['lacks'], f'competitors[{i}].lacks', 160)
        if 'signature' not in s: return
        if not self.arr(s['signature'], 'signature', 5, 16): return
        try: names = {n.lower() for _, n in sheet_names(s, lambda x: x)}
        except Exception: names = set()
        seen = set()
        for i, x in enumerate(s['signature']):
            w = f'signature[{i}]'
            if not self.obj(x, w, ['name', 'why', 'where']): continue
            self.text(x['name'], w + '.name', 50); self.text(x['why'], w + '.why', 160)
            if isinstance(x['where'], str) and names and x['where'].lower() not in names: self.e(w + '.where', f'{x["where"]!r} is not a sheet of this spec')
            if str(x['name']).lower() in seen: self.e(w + '.name', 'used twice')
            seen.add(str(x['name']).lower())

    def tools(self):
        ts = self.s.get('tools', []); seen = set()
        if not self.arr(ts, 'tools', 0, 14): return
        for i, t in enumerate(ts):
            w = f'tools[{t.get("key", i) if isinstance(t, dict) else i}]'
            if not self.obj(t, w, ['key', 'sheet', 'title', 'hint', 'inputs', 'outputs'], ['grid']): continue
            self.key(t['key'], w + '.key', seen); self.text(t['title'], w + '.title', 60); self.text(t['hint'], w + '.hint', 200)
            bad = bad_sheet_name(t['sheet'])
            if bad: self.e(w + '.sheet', f'{t["sheet"]!r}: {bad}')
            ins = []
            if self.arr(t['inputs'], w + '.inputs', 1, 20):
                ik = set()
                for x in t['inputs']:
                    wi = f'{w}.inputs[{x.get("key") if isinstance(x, dict) else "?"}]'
                    if not self.obj(x, wi, ['key', 'label', 'type', 'default'], ['list']): continue
                    self.key(x['key'], wi + '.key', ik); self.text(x['label'], wi + '.label', 60); ins.append(x['key'])
                    ty, v = x['type'], x['default']
                    if ty not in ('int', 'num', 'money', 'pct', 'date', 'list', 'text'): self.e(wi + '.type', f'{ty!r} not one of int num money pct date list text'); continue
                    if ty == 'list':
                        L = list_by_key(self.s, x.get('list'))
                        if L is None: self.e(wi + '.list', f'unknown list {x.get("list")!r}')
                        elif v not in [y.get('key') for y in L['values']]: self.e(wi + '.default', f'{v!r} is not a value key of list {x["list"]}')
                    elif 'list' in x: self.e(wi + '.list', 'only for type list')
                    if ty in ('int', 'num', 'money', 'pct') and not (isinstance(v, (int, float)) and not isinstance(v, bool)): self.e(wi + '.default', 'must be a number')
                    if ty == 'date' and parse_date(v, dt.date.today()) is None: self.e(wi + '.default', 'must be "YYYY-MM-DD" or "today", "today-N", "today+N"')
                    if ty == 'text' and (not isinstance(v, str) or v.startswith('=')): self.e(wi + '.default', 'must be a text not starting with "="')
            if self.arr(t['outputs'], w + '.outputs', 1, 20):
                for j, o in enumerate(t['outputs']):
                    wo = f'{w}.outputs[{j}]'
                    if not self.obj(o, wo, ['label', 'formula', 'format']): continue
                    self.text(o['label'], wo + '.label', 60)
                    if o['format'] not in FORMATS: self.e(wo + '.format', f'{o["format"]!r} not one of {FORMATS}')
                    self.formula(o['formula'], wo + '.formula', {'in', 'set', 'range', 'list', 'today'}, ins=ins)
            if 'grid' in t and self.obj(t['grid'], w + '.grid', ['title', 'rows']):
                self.text(t['grid']['title'], w + '.grid.title', 60)
                if self.arr(t['grid']['rows'], w + '.grid.rows', 1, 12):
                    for j, r in enumerate(t['grid']['rows']):
                        wr = f'{w}.grid.rows[{j}]'
                        if not self.obj(r, wr, ['label', 'values']): continue
                        self.text(r['label'], wr + '.label', 40)
                        if not isinstance(r['values'], dict) or not r['values']: self.e(wr + '.values', 'must be an object {input key: number or "=formula"}'); continue
                        for k, v in r['values'].items():
                            if k not in ins: self.e(wr + '.values', f'unknown input {k!r}')
                            elif isinstance(v, str) and v.strip().startswith('='): self.formula(v, f'{wr}.values.{k}', {'in', 'set', 'range', 'list', 'today'}, ins=ins)
                            elif not (isinstance(v, (int, float)) and not isinstance(v, bool)): self.e(f'{wr}.values.{k}', 'must be a number or a "=formula" text')

    def messages(self):
        ms = self.s.get('messages', []); seen = set()
        if not self.arr(ms, 'messages', 0, 30): return
        for i, m in enumerate(ms):
            w = f'messages[{m.get("key", i) if isinstance(m, dict) else i}]'
            if not self.obj(m, w, ['key', 'moment', 'text', 'table', 'phone']): continue
            self.key(m['key'], w + '.key', seen); self.text(m['moment'], w + '.moment', 40); self.text(m['text'], w + '.text', 500)
            tb = next((t for t in self.s.get('tables', []) if isinstance(t, dict) and t.get('key') == m['table']), None)
            if tb is None: self.e(w + '.table', f'unknown table {m["table"]!r}'); continue
            keys = [c.get('key') for c in tb['columns']]
            for p_ in PH.findall(m['text'] if isinstance(m['text'], str) else ''):
                if p_ not in keys: self.e(w + '.text', f'placeholder {{{p_}}} is not a column of {m["table"]} ({", ".join(keys)})')
            pt, pc = find_col(self.s, m['phone'])
            if pc is None: self.e(w + '.phone', f'{m["phone"]!r} is not an existing "table.column"'); continue
            if pt['key'] != tb['key'] and not any(c.get('type') == 'ref' and str(c.get('ref', '')).split('.')[0] == pt['key'] for c in tb['columns']):
                self.e(w + '.phone', f'{m["phone"]!r} is in another table and {m["table"]} has no ref column to {pt["key"]} to look it up')

    def documents(self):
        ds = self.s.get('documents', []); seen = set()
        if not self.arr(ds, 'documents', 0, 10): return
        sets = {x.get('key') for x in self.s.get('settings', []) if isinstance(x, dict)}
        for i, d in enumerate(ds):
            w = f'documents[{d.get("key", i) if isinstance(d, dict) else i}]'
            if not self.obj(d, w, ['key', 'sheet', 'title', 'pick', 'paragraphs'], ['sign', 'note']): continue
            self.key(d['key'], w + '.key', seen); self.text(d['title'], w + '.title', 60)
            bad = bad_sheet_name(d['sheet'])
            if bad: self.e(w + '.sheet', f'{d["sheet"]!r}: {bad}')
            pt, pc = find_col(self.s, d['pick'])
            if pc is None: self.e(w + '.pick', f'{d["pick"]!r} is not an existing "table.column"'); continue
            if self.arr(d['paragraphs'], w + '.paragraphs', 1, 15):
                for j, p_ in enumerate(d['paragraphs']):
                    wp = f'{w}.paragraphs[{j}]'
                    if not self.text(p_, wp, 1500): continue
                    for m in TOK.finditer(p_):
                        kind, arg = m.group(1) or m.group(3), m.group(2) or ''
                        if kind == 'col':
                            t2, c2 = find_col(self.s, arg)
                            if c2 is None or t2['key'] != pt['key']: self.e(wp, f'{m.group()} must be a column of {pt["key"]} (the table of "pick"), as {{col:{pt["key"]}.column}}')
                        elif kind == 'set':
                            if arg not in sets: self.e(wp, f'unknown setting {m.group()}')
                        elif kind != 'today': self.e(wp, f'{m.group()} is not allowed in a document (use {{col:t.c}}, {{set:k}}, {{today}})')
            if 'sign' in d and self.arr(d['sign'], w + '.sign', 0, 4):
                for j, x in enumerate(d['sign']): self.text(x, f'{w}.sign[{j}]', 40)
            if 'note' in d: self.text(d['note'], w + '.note', 300)

    def checklists(self):
        cs = self.s.get('checklists', []); seen = set()
        if not self.arr(cs, 'checklists', 0, 10): return
        for i, c in enumerate(cs):
            w = f'checklists[{c.get("key", i) if isinstance(c, dict) else i}]'
            if not self.obj(c, w, ['key', 'title', 'table', 'start', 'steps']): continue
            self.key(c['key'], w + '.key', seen)
            bad = bad_sheet_name(c['title'])
            if bad: self.e(w + '.title', f'{c["title"]!r} (it is also the sheet name): {bad}')
            st, sc = find_col(self.s, c['start'])
            if sc is None or st.get('key') != c['table'] or col_format(sc) != 'date': self.e(w + '.start', f'{c["start"]!r} must be a date column of table {c["table"]!r}')
            if self.arr(c['steps'], w + '.steps', 2, 40):
                for j, x in enumerate(c['steps']):
                    ws_ = f'{w}.steps[{j}]'
                    if not self.obj(x, ws_, ['label', 'days']): continue
                    self.text(x['label'], ws_ + '.label', 120)
                    if not (isinstance(x['days'], int) and not isinstance(x['days'], bool) and -3650 <= x['days'] <= 3650): self.e(ws_ + '.days', 'must be a whole number of days (-3650..3650)')

    for f in (sheets_en, signature, tools, messages, documents, checklists): setattr(V, f.__name__, f)
_ext(V)



def _v13(V):
    """v1.3 (Dar 3.34.1, 2026-11-07 — the owner: «ركز على الجداول والرسوم البيانية المتحركة والمؤشرات … يتفوق على المنافسين بأضعاف»):
    the «Charts» sheet — filters the buyer picks (they redraw every chart and gauge), gauges and live charts — and visual indicators on columns.
    As many charts and gauges as the field needs: the limits here are only what one sheet can hold."""
    OPS = ('=', '<>', '>', '<', '>=', '<=')
    def table_of(self, k): return next((t for t in self.s.get('tables') or [] if isinstance(t, dict) and t.get('key') == k), None)
    def col_of(self, t, c): return next((x for x in (t or {}).get('columns') or [] if isinstance(x, dict) and x.get('key') == c), None)
    def tc(self, ref, where):
        if not isinstance(ref, str) or ref.count('.') != 1: self.e(where, f'must be "table.column", got {ref!r}'); return None, None
        t, c = ref.split('.'); T_ = self.table_of(t)
        if not T_: self.e(where, f'unknown table {t!r}'); return None, None
        C = self.col_of(T_, c)
        if not C: self.e(where, f'table {t!r} has no column {c!r}'); return T_, None
        return T_, C
    def agg(self, x, where, need_label, month, table=None):
        keys = ['agg', 'table'] + (['label'] if need_label else [])
        if not self.obj(x, where, keys, ['value', 'date', 'where'] + ([] if need_label else ['label'])): return
        if need_label: self.text(x['label'], where + '.label', 40)
        if x['agg'] not in ('sum', 'count', 'avg'): self.e(where + '.agg', 'must be sum, count or avg')
        T_ = self.table_of(x['table'])
        if not T_: self.e(where + '.table', f'unknown table {x["table"]!r}'); return
        if table and x['table'] != table: self.e(where + '.table', f'must be {table!r}: every series of a chart grouped by a column counts the rows of that column\'s table')
        if x['agg'] in ('sum', 'avg'):
            if 'value' not in x: self.e(where, 'sum and avg need "value": "table.column" (a number column of the same table)')
            else:
                T2, C = self.tc(x['value'], where + '.value')
                if C is not None and (T2 is not T_ or not is_num(C)): self.e(where + '.value', 'must be a number column of the series table')
        if month and 'date' not in x: self.e(where, 'a chart by month needs "date": "table.column" (a date column of the series table)')
        if 'date' in x:
            T2, C = self.tc(x['date'], where + '.date')
            if C is not None and (T2 is not T_ or col_format(C) != 'date'): self.e(where + '.date', 'must be a date column of the series table')
        for i, w in enumerate(x.get('where') or []):
            ww = f'{where}.where[{i}]'
            if not self.obj(w, ww, ['column', 'op', 'value']): continue
            if not self.col_of(T_, w['column']): self.e(ww + '.column', f'table {x["table"]!r} has no column {w["column"]!r}')
            if w['op'] not in OPS: self.e(ww + '.op', f'must be one of {OPS}')
            v = w['value']
            if isinstance(v, bool) or not (isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r'\{(list:[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*|set:[a-z][a-z0-9_]*|today)\}', v))):
                self.e(ww + '.value', 'must be a number, {list:l.v}, {set:k} or {today}')
            elif isinstance(v, str) and v.startswith('{list:'):
                l, val = v[6:-1].split('.'); L = list_by_key(self.s, l)
                if not L or val not in [y.get('key') for y in L.get('values', [])]: self.e(ww + '.value', f'unknown list value {v}')
            elif isinstance(v, str) and v.startswith('{set:') and v[5:-1] not in [y.get('key') for y in self.s.get('settings') or [] if isinstance(y, dict)]: self.e(ww + '.value', f'unknown setting {v}')
        if 'where' in x and not self.arr(x['where'], where + '.where', 0, 4): return
    def insights(self):
        ins = self.s.get('insights')
        if ins is None: return
        if not self.obj(ins, 'insights', ['charts'], ['filters', 'gauges']): return
        fl = ins.get('filters') or []
        if self.arr(fl, 'insights.filters', 0, 3):
            for i, f in enumerate(fl):
                w = f'insights.filters[{i}]'
                if not self.obj(f, w, ['label'], ['ref', 'list']): continue
                self.text(f['label'], w + '.label', 30)
                if ('ref' in f) == ('list' in f): self.e(w, 'needs exactly one of "ref": "table.column" (a column whose values the buyer picks, e.g. staff.name) or "list": "<list key>"')
                elif 'ref' in f: self.tc(f['ref'], w + '.ref')
                elif not list_by_key(self.s, f['list']): self.e(w + '.list', f'unknown list {f["list"]!r}')
        gs = ins.get('gauges') or []
        if self.arr(gs, 'insights.gauges', 0, 6):
            for i, g in enumerate(gs):
                w = f'insights.gauges[{i}]'
                if not self.obj(g, w, ['title', 'num', 'den']): continue
                self.text(g['title'], w + '.title', 40); self.agg(g['num'], w + '.num', False, False); self.agg(g['den'], w + '.den', False, False)
        ch = ins.get('charts')
        if not self.arr(ch, 'insights.charts', 1, 20): return
        seen = set()
        for i, c in enumerate(ch):
            w = f'insights.charts[{i}]'
            if not self.obj(c, w, ['title', 'type', 'by', 'series'], ['line']): continue
            self.text(c['title'], w + '.title', 60)
            if c['title'] in seen: self.e(w + '.title', 'two charts have the same title')
            seen.add(c['title'])
            if c['type'] not in ('column', 'bar', 'line', 'stacked', 'doughnut', 'pie', 'combo'): self.e(w + '.type', 'must be column, bar, line, stacked, doughnut, pie or combo'); continue
            month = c['by'] == 'month'; table = None
            if not month:
                T_, C = self.tc(c['by'], w + '.by')
                if C is not None and C.get('type') not in ('list', 'ref'): self.e(w + '.by', 'must be "month" or a list or ref column (its values become the categories)')
                table = T_.get('key') if T_ else None
            if not self.arr(c['series'], w + '.series', 1, 4): continue
            if c['type'] in ('doughnut', 'pie') and (len(c['series']) != 1 or month): self.e(w, 'a doughnut or pie has exactly one series and is grouped by a list or ref column')
            if c['type'] == 'combo':
                if len(c['series']) < 2 or not isinstance(c.get('line'), int) or not 0 <= c['line'] < len(c['series']): self.e(w + '.line', 'a combo chart has 2..4 series and "line": the index of the series drawn as a line')
            for j, x in enumerate(c['series']): self.agg(x, f'{w}.series[{j}]', True, month, table)
    def visuals(self):
        for t in self.s.get('tables') or []:
            if not isinstance(t, dict): continue
            for c in t.get('columns') or []:
                if isinstance(c, dict) and 'visual' in c:
                    w = f'tables[{t.get("key")}].columns[{c.get("key")}].visual'
                    if c['visual'] not in ('bar', 'up', 'down'): self.e(w, 'must be bar (a data bar), up (green when high) or down (green when low)')
                    elif not is_num(c): self.e(w, 'only on a number column')
    for f in (table_of, col_of, tc, agg, insights, visuals): setattr(V, f.__name__, f)
_v13(V)

def validate(spec):
    """-> list of error strings (empty when the spec can be built)."""
    import copy
    try: errs = V(copy.deepcopy(spec)).run()
    except Exception as x:  # a malformed spec must give a message, never a crash
        return [f'spec: could not be checked ({type(x).__name__}: {x})']
    if not os.environ.get('FX_NO_DEPTH'):  # 2026-11-09 quality gate (depth.py): services, demo realism, names, picture texts
        try:
            from depth import depth
            errs = list(errs) + depth(spec)
        except Exception as x: errs = list(errs) + [f'depth: could not be checked ({type(x).__name__}: {x})']
    return errs


if __name__ == '__main__':
    try: spec = json.load(open(sys.argv[1], encoding='utf8'))
    except Exception as x: print(json.dumps({'ok': False, 'errors': [f'json: {x}']})); sys.exit(1)
    errs = validate(spec)
    print(json.dumps({'ok': not errs, 'errors': errs}, ensure_ascii=False, indent=1))
    sys.exit(0 if not errs else 1)
