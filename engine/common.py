#!/usr/bin/env python3
"""Shared definitions of the fx engine (spec contract v1, see ../SPEC.md): languages, the formula DSL, the texts a spec makes
the builder print, demo values. Imported by validate, build, verify, images, package and run."""
import os, re, json, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ['en', 'ar', 'fr', 'es', 'de', 'it', 'pt', 'tr', 'nl', 'ru', 'fa', 'ur', 'hi', 'zh', 'id']
if os.environ.get('FX_LANGS'):  # test builds only (e.g. FX_LANGS=en,ar): a release build always has all 15
    LANGS = ['en'] + [l for l in LANGS[1:] if l in os.environ['FX_LANGS'].split(',')]
TR_LANGS = LANGS[1:]
RTL = {'ar', 'fa', 'ur'}
LANG_NAMES = {'en': 'English', 'ar': 'العربية', 'fr': 'Français', 'es': 'Español', 'de': 'Deutsch', 'it': 'Italiano', 'pt': 'Português',
              'tr': 'Türkçe', 'nl': 'Nederlands', 'ru': 'Русский', 'fa': 'فارسی', 'ur': 'اردو', 'hi': 'हिन्दी', 'zh': '中文', 'id': 'Bahasa Indonesia'}
import glob as _glob
# the LibreOffice recalculation script of the xlsx skill — wherever this workspace keeps it (its folder's name changes per account)
RECALC = os.environ.get('FX_RECALC') or next(iter([p for p in sorted(_glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')) + ['/mnt/skills/public/xlsx/scripts/recalc.py'] if os.path.exists(p)]), os.path.join(HERE, 'recalc.py'))  # (the engine's own on the verification worker)
FIXED = json.load(open(os.path.join(HERE, 'fixed_en.json'), encoding='utf8'))

ALLOWED = set(('SUM SUMIFS COUNTIFS COUNTA COUNT AVERAGEIFS AVERAGE MIN MAX MAXIFS MINIFS IF IFERROR AND OR NOT INDEX MATCH ROUND ROUNDUP '
               'ROUNDDOWN ABS DATE YEAR MONTH DAY EDATE EOMONTH TODAY NETWORKDAYS DATEDIF TEXTJOIN LEFT RIGHT MID LEN TRIM UPPER LOWER '
               'SUMPRODUCT ISNUMBER ISBLANK VALUE MOD INT HYPERLINK '
               # 2026-11-11: finance and statistics that every Excel and LibreOffice reads without a prefix (rents, mortgages, DCF, yields)
               'PMT PV FV NPV IRR RATE NPER SUMIF COUNTIF AVERAGEIF MEDIAN LARGE SMALL WEEKDAY WORKDAY CHOOSE POWER SQRT ISERROR').split())
XLFN = ('MAXIFS', 'MINIFS', 'TEXTJOIN')          # stored as _xlfn.NAME in the file (Excel 2019+, LibreOffice)
COL_TYPES = ('text', 'int', 'num', 'money', 'pct', 'date', 'time', 'list', 'ref', 'bool', 'calc', 'link')
FORMATS = ('int', 'num', 'money', 'pct', 'date', 'time', 'text', 'hours')
NUMERIC = {'int', 'num', 'money', 'pct', 'hours'}
SET_TYPES = ('pct', 'money', 'int', 'num', 'text', 'date', 'list')
YESNO = 'yesno'                                   # built-in list behind bool columns: {list:yesno.yes} / {list:yesno.no}
STEPSTAT = 'stepstat'                             # built-in list of checklist step states (completed / late / to do)
# fixed words printed only when the spec has that part (the i18n must translate a word only when the build prints it)
FIXED_GROUP = {'inputs': ('tools',), 'results': ('tools',), 'form_hint': ('forms', 'documents'), 'not_found': ('forms', 'documents', 'checklists'),
               'signature': ('forms', 'documents'), 'wording': ('documents',), 'date': ('documents',),
               **{k: ('messages',) for k in ('sheet_messages', 'msg_hint', 'moment', 'sheet', 'text', 'wa_send')},
               **{k: ('checklists',) for k in ('chk_hint', 'step', 'days', 'due', 'done', 'done_on', 'progress', 'stepstat', 'st_done', 'st_late', 'st_todo')},
               **{k: ('insights',) for k in ('sheet_charts', 'charts_hint', 'charts_data', 'all', 'g_done', 'g_left', 'g_base', 'gauge')}}  # v1.3
PH = re.compile(r'\{([a-z][a-z0-9_]*)\}')          # message placeholders: {column_key}
KEY_RE = re.compile(r'^[a-z][a-z0-9_]{1,20}$')
TOK = re.compile(r'\{(col|range|set|list|in):([^{}]*)\}|\{(today|pick)\}')
STRLIT = re.compile(r'"(?:[^"]|"")*"')
NUMFMT = {'int': '#,##0', 'num': '#,##0.00', 'money': '#,##0.00', 'pct': '0.0%', 'date': 'yyyy-mm-dd', 'time': 'hh:mm', 'hours': '0.0', 'text': 'General'}


def tr(spec, lang):
    """The translate function of one language: English text -> the text to print (KeyError when a translation is missing)."""
    if lang == 'en': return lambda s: s
    m = spec['i18n'][lang]
    return lambda s: m[s]


def segments(f):
    """Split a formula into (is_string_literal, text) pieces so tokens and names are only touched outside text literals."""
    out, i = [], 0
    for m in STRLIT.finditer(f):
        if m.start() > i: out.append((False, f[i:m.start()]))
        out.append((True, m.group())); i = m.end()
    if i < len(f): out.append((False, f[i:]))
    return out


def normalize(f):
    """DSL text -> canonical text: no leading '=', function names in capitals, _xlfn. prefix where Excel needs it."""
    f = f.strip()
    if f.startswith('='): f = f[1:].strip()
    parts = []
    for is_s, s in segments(f):
        if not is_s:
            s = re.sub(r'(?<![\w.{:])([A-Za-z_][A-Za-z0-9_.]*)(\s*\()', lambda m: m.group(1).upper() + m.group(2), s)
            s = re.sub(r'(?<![\w.])_XLFN\.', '', s)
            s = re.sub(r'(?<![\w.])(' + '|'.join(XLFN) + r')(\s*\()', r'_xlfn.\1\2', s)
        parts.append(s)
    return ''.join(parts)


def tokens(f):
    """[(kind, arg)] of every DSL token outside text literals; kind in col range set list today pick."""
    out = []
    for is_s, s in segments(f):
        if is_s: continue
        for m in TOK.finditer(s): out.append((m.group(1) or m.group(3), m.group(2) or ''))
    return out


def substitute(f, fn):
    """Replace every DSL token (outside text literals) by fn(kind, arg)."""
    return ''.join(s if is_s else TOK.sub(lambda m: fn(m.group(1) or m.group(3), m.group(2) or ''), s) for is_s, s in segments(f))


def find_col(spec, ref):
    """'table.column' -> (table, column) or (None, None)."""
    if not isinstance(ref, str) or ref.count('.') != 1: return None, None
    t, c = ref.split('.')
    for tb in spec.get('tables', []):
        if isinstance(tb, dict) and tb.get('key') == t:
            for col in tb.get('columns', []):
                if isinstance(col, dict) and col.get('key') == c: return tb, col
            return tb, None
    return None, None


def col_format(col):
    """How a column's values look: its type for inputs, its format for calc columns."""
    t = col.get('type')
    if t == 'calc': return col.get('format', 'num')
    return {'int': 'int', 'num': 'num', 'money': 'money', 'pct': 'pct', 'date': 'date', 'time': 'time'}.get(t, 'text')


def is_numeric(col): return col_format(col) in NUMERIC
def is_date(col): return col_format(col) == 'date'


def main_date(table):
    """The date column that places a row in time: a required input date, any input date, else a calc column shown as a date."""
    cols = [c for c in table.get('columns', []) if isinstance(c, dict)]
    for pick in (lambda c: c.get('type') == 'date' and c.get('required'), lambda c: c.get('type') == 'date', lambda c: c.get('type') == 'calc' and c.get('format') == 'date'):
        for c in cols:
            if pick(c): return c
    return None


def record_key(table):
    """The column that names a record when a sheet asks to choose one (checklists): the first required input column."""
    return first_required(table) or table['columns'][0]


def first_required(table):
    for c in table.get('columns', []):
        if isinstance(c, dict) and c.get('required') and c.get('type') != 'calc': return c
    return None


def series_date(spec, s):
    """The date column a monthly series is placed by: series.date, else monthly.date when the same table, else the table's main date."""
    m = spec['dashboard']['monthly']; t = s['sum'].split('.')[0]
    if s.get('date'): return s['date']
    if m.get('date', '').split('.')[0] == t: return m['date']
    tb, _ = find_col(spec, s['sum'] if '.' in s['sum'] else s['sum'] + '.x')
    d = main_date(tb) if tb else None
    return f'{t}.{d["key"]}' if d else None


BRAND_KEYS = ('name', 'business', 'company', 'clinic', 'shop', 'office', 'agency', 'firm', 'store', 'studio', 'salon', 'practice', 'school', 'restaurant', 'hotel', 'center', 'centre')
def brand_setting(spec):
    """The text setting that holds the business name (shown on the dashboard and printed forms), if the spec has one."""
    for s in spec.get('settings', []):
        if isinstance(s, dict) and s.get('type') == 'text' and any(k in s.get('key', '') for k in BRAND_KEYS): return s
    return None


def texts(spec):
    """Every English string the build prints -> where it first comes from (the i18n of every language must translate all of them)."""
    out = {}
    def add(s, where):
        if isinstance(s, str) and s.strip() and s not in out: out[s] = where
    g = lambda d, k: d.get(k) if isinstance(d, dict) else None
    add(spec.get('name'), 'name'); add(spec.get('tagline'), 'tagline')
    for s in spec.get('settings') or []: add(g(s, 'label'), f'settings[{g(s, "key")}].label')
    for l in spec.get('lists') or []:
        add(g(l, 'label'), f'lists[{g(l, "key")}].label')
        for v in g(l, 'values') or []: add(g(v, 'label'), f'lists[{g(l, "key")}].values[{g(v, "key")}]')
    for t in spec.get('tables') or []:
        k = g(t, 'key')
        for f in ('sheet', 'title', 'hint'): add(g(t, f), f'tables[{k}].{f}')
        for c in g(t, 'columns') or []: add(g(c, 'label'), f'tables[{k}].columns[{g(c, "key")}].label')
    d = spec.get('dashboard') or {}
    add(g(d, 'title'), 'dashboard.title')
    for i, k in enumerate(g(d, 'kpis') or []): add(g(k, 'label'), f'dashboard.kpis[{i}].label')
    m = g(d, 'monthly') or {}
    add(g(m, 'title'), 'dashboard.monthly.title')
    for i, s in enumerate(g(m, 'series') or []): add(g(s, 'label'), f'dashboard.monthly.series[{i}].label')
    for i, b in enumerate(g(d, 'breakdowns') or []): add(g(b, 'title'), f'dashboard.breakdowns[{i}].title')
    for fm in spec.get('forms') or []:
        k = g(fm, 'key')
        for f in ('sheet', 'title'): add(g(fm, f), f'forms[{k}].{f}')
        for i, fl in enumerate(g(fm, 'fields') or []): add(g(fl, 'label'), f'forms[{k}].fields[{i}].label')
    for t in spec.get('tools') or []:
        k = g(t, 'key')
        for f in ('sheet', 'title', 'hint'): add(g(t, f), f'tools[{k}].{f}')
        for x in g(t, 'inputs') or []: add(g(x, 'label'), f'tools[{k}].inputs[{g(x, "key")}].label')
        for i, x in enumerate(g(t, 'outputs') or []): add(g(x, 'label'), f'tools[{k}].outputs[{i}].label')
        gr = g(t, 'grid') or {}
        add(g(gr, 'title'), f'tools[{k}].grid.title')
        for i, x in enumerate(g(gr, 'rows') or []): add(g(x, 'label'), f'tools[{k}].grid.rows[{i}].label')
    for m in spec.get('messages') or []:
        add(g(m, 'moment'), f'messages[{g(m, "key")}].moment'); add(g(m, 'text'), f'messages[{g(m, "key")}].text')
    for d_ in spec.get('documents') or []:
        k = g(d_, 'key')
        for f in ('sheet', 'title', 'note'): add(g(d_, f), f'documents[{k}].{f}')
        for i, x in enumerate(g(d_, 'paragraphs') or []): add(x, f'documents[{k}].paragraphs[{i}]')
        for i, x in enumerate(g(d_, 'sign') or []): add(x, f'documents[{k}].sign[{i}]')
    for c in spec.get('checklists') or []:
        k = g(c, 'key'); add(g(c, 'title'), f'checklists[{k}].title')
        for i, x in enumerate(g(c, 'steps') or []): add(g(x, 'label'), f'checklists[{k}].steps[{i}].label')
    ins = spec.get('insights') or {}
    for i, x in enumerate(g(ins, 'filters') or []): add(g(x, 'label'), f'insights.filters[{i}].label')
    for i, x in enumerate(g(ins, 'gauges') or []): add(g(x, 'title'), f'insights.gauges[{i}].title')
    for i, x in enumerate(g(ins, 'charts') or []):
        add(g(x, 'title'), f'insights.charts[{i}].title')
        for j, y in enumerate(g(x, 'series') or []): add(g(y, 'label'), f'insights.charts[{i}].series[{j}].label')
    for i, s in enumerate(spec.get('guide') or []): add(s, f'guide[{i}]')
    for k, v in fixed_needed(spec).items(): add(v, f'engine/fixed_en.json:{k}')
    return out


def fixed_needed(spec):
    return {k: v for k, v in FIXED.items() if k not in FIXED_GROUP or any(spec.get(p) for p in FIXED_GROUP[k])}


def sheet_names(spec, T):
    """Ordered [(id, printed sheet name)] of one language."""
    out = [('start', T(FIXED['sheet_start'])), ('dash', T(spec['dashboard']['title']))]
    if spec.get('insights'): out.append(('charts', T(FIXED['sheet_charts'])))  # v1.3: the live charts, right after the dashboard
    out += [('t:' + t['key'], T(t['sheet'])) for t in spec['tables']]
    out += [('x:' + t['key'], T(t['sheet'])) for t in spec.get('tools', [])]
    out += [('f:' + f['key'], T(f['sheet'])) for f in spec.get('forms', [])]
    out += [('d:' + d['key'], T(d['sheet'])) for d in spec.get('documents', [])]
    out += [('c:' + c['key'], T(c['title'])) for c in spec.get('checklists', [])]
    if spec.get('messages'): out.append(('msgs', T(FIXED['sheet_messages'])))
    out.append(('lists', T(FIXED['sheet_lists'])))
    return out


def bad_sheet_name(n):
    if not isinstance(n, str) or not n.strip(): return 'empty'
    if len(n) > 31: return f'{len(n)} characters (31 at most)'
    if any(c in n for c in '[]:*?/\\'): return 'contains one of [ ] : * ? / \\'
    if n.startswith("'") or n.endswith("'"): return "starts or ends with an apostrophe"
    if n.strip().lower() == 'history': return '"History" is reserved by Excel'
    return None


REL = re.compile(r'^today\s*(?:([+-])\s*(\d{1,5}))?$')
def parse_date(v, today):
    """'YYYY-MM-DD' or 'today', 'today-12', 'today+30' -> date; None when not a date text."""
    if not isinstance(v, str): return None
    s = v.strip().lower(); m = REL.match(s)
    if m: return today + dt.timedelta(days=(int(m.group(2)) * (1 if m.group(1) == '+' else -1)) if m.group(1) else 0)
    try: return dt.date.fromisoformat(s) if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s) else None
    except ValueError: return None


def parse_time(v):
    if not isinstance(v, str) or not re.fullmatch(r'\d{1,2}:\d{2}', v.strip()): return None
    h, m = map(int, v.strip().split(':'))
    return dt.time(h, m) if h < 24 and m < 60 else None


def list_by_key(spec, k):
    if k == YESNO: return {'key': YESNO, 'label': FIXED['yesno'], 'values': [{'key': 'yes', 'label': FIXED['yes']}, {'key': 'no', 'label': FIXED['no']}]}
    if k == STEPSTAT: return {'key': STEPSTAT, 'label': FIXED['stepstat'], 'values': [{'key': x, 'label': FIXED['st_' + x]} for x in ('done', 'late', 'todo')]}
    for l in spec.get('lists', []):
        if isinstance(l, dict) and l.get('key') == k: return l
    return None


def file_base(spec):
    """'Dental Clinic Manager' -> 'Dental-Clinic-Manager' (file names inside the buyer's ZIP)."""
    return re.sub(r'-+', '-', re.sub(r'[^A-Za-z0-9]+', '-', spec['name'])).strip('-') or spec['slug']
