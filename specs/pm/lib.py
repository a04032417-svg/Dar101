"""Compact helpers for writing fx specs (SPEC v1.1 + v1.3 insights), one workbook per call to spec()."""
import json, random, datetime as dt

TODAY = dt.date.today()
R = random.Random(20261111)


def iso(d): return d.isoformat()
def ago(days): return iso(TODAY - dt.timedelta(days=days))
def ahead(days): return iso(TODAY + dt.timedelta(days=days))
def month_start(k):  # 1st of the month k months before this month (k=0 this month)
    y, m = TODAY.year, TODAY.month - k
    while m <= 0: m += 12; y -= 1
    return dt.date(y, m, 1)
def add_months(d, n):
    y, m = d.year, d.month + n
    while m > 12: m -= 12; y += 1
    while m <= 0: m += 12; y -= 1
    import calendar
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def L(key, label, vals): return {"key": key, "label": label, "values": [{"key": k, "label": v} for k, v in vals]}
def LV(l, k): return "{list:%s.%s}" % (l, k)
def S(key, label, typ, default, **kw): d = {"key": key, "label": label, "type": typ, "default": default}; d.update(kw); return d


def C(key, label, typ='text', w=12, **kw):
    d = {"key": key, "label": label, "type": typ, "width": w}; d.update(kw); return d
def LST(key, label, lst, w=13, **kw): return C(key, label, 'list', w, list=lst, **kw)
def REF(key, label, ref, w=12, **kw): return C(key, label, 'ref', w, ref=ref, **kw)
def CALC(key, label, fmt, formula, w=12, **kw): return C(key, label, 'calc', w, format=fmt, formula=formula, **kw)


def LOOK(src, key_col, my_col):
    """value of src (t.c) in the row whose key_col (t.c) equals this row's my_col"""
    return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my_col, key_col)


def T(key, sheet, title, hint, cols, demo, rows=500, alerts=None, explain=None):
    d = {"key": key, "sheet": sheet, "title": title, "hint": hint, "rows": rows, "columns": cols, "demo": demo}
    if alerts: d["alerts"] = alerts
    return d
def A(col, when, style): return {"column": col, "when": when, "style": style}


def IN(key, label, typ, default, **kw): d = {"key": key, "label": label, "type": typ, "default": default}; d.update(kw); return d
def OUT(label, fmt, formula): return {"label": label, "format": fmt, "formula": formula}
def TOOL(key, sheet, title, hint, inputs, outputs, grid=None):
    d = {"key": key, "sheet": sheet, "title": title, "hint": hint, "inputs": inputs, "outputs": outputs}
    if grid: d["grid"] = grid
    return d


def DOC(key, sheet, title, pick, paragraphs, sign, note="Sample wording: adapt it to your country's law and your own practice."):
    return {"key": key, "sheet": sheet, "title": title, "pick": pick, "paragraphs": paragraphs, "sign": sign, "note": note}
def CHK(key, title, table, start, steps): return {"key": key, "title": title, "table": table, "start": start, "steps": [{"label": l, "days": d} for l, d in steps]}
def MSG(key, moment, table, phone, text): return {"key": key, "moment": moment, "table": table, "phone": phone, "text": text}
def FORM(key, sheet, title, pick, fields, lines=None):
    d = {"key": key, "sheet": sheet, "title": title, "pick": pick, "fields": fields}
    if lines: d["lines"] = lines
    return d
def FV(label, value): return {"label": label, "value": value}
def FF(label, formula, fmt): return {"label": label, "formula": formula, "format": fmt}


def KPI(label, formula, fmt, **kw): d = {"label": label, "formula": formula, "format": fmt}; d.update(kw); return d
def AGG(agg, table, value=None, date=None, where=None, label=None):
    d = {"agg": agg, "table": table}
    if value: d["value"] = value
    if date: d["date"] = date
    if where: d["where"] = [{"column": c, "op": o, "value": v} for c, o, v in where]
    if label: d["label"] = label
    return d
def CHART(title, typ, by, series, line=None):
    d = {"title": title, "type": typ, "by": by, "series": series}
    if line is not None: d["line"] = line
    return d


def spec(**k):
    s = {"fx": 1}
    s.update(k)
    return s


def dump(s, path):
    json.dump(s, open(path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    return path
