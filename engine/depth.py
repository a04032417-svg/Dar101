"""depth.py — Dar's quality gate (2026-11-09; the owner: «لا يجب أن تكرر المنظومة عدم الاتقان هذا» after a Photographer pack shipped with
no profession-specific services, 12 near-identical demo rows and untranslated pictures).

`depth(spec)` returns a list of error strings; validate.validate() appends them, so a file that fails goes back to Dar's architect through the
same repair loop as any other build error — each message says exactly what to add. Rules (all measured on the spec, nothing guessed):
  1  services     >= 6 signature services, >= 3 competitors, >= 2 tools, >= 3 messages, >= 1 document, >= 1 checklist (SPEC.md v1.1)
  2  demo size    every table with 4+ columns has >= 12 demo rows; two tables have >= 24; the demo covers >= 270 days on one date column
  3  demo variety a list column uses >= 3 of its values; a money column has >= 3 distinct values and no value in more than 60% of the rows;
                  a first (id) column is unique; a month column holds the 1st of each month (an absolute date, not "today-N")
  4  names        no sheet or column name with an underscore (it prints as a machine name)
  5  pictures     every text the pictures print (headline, tagline, signature name+why, dashboard title) is translated in all 14 languages
"""
import re, datetime

from common import TR_LANGS as LANGS
REL = re.compile(r'^today\s*([+-]\s*\d+)?$')
ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


def day(v, today=datetime.date(2026, 1, 1)):
    """A demo date as a day number (relative dates against a fixed day, so the span does not depend on when the check runs)."""
    if not isinstance(v, str): return None
    v = v.strip(); m = REL.match(v)
    if m: return (today + datetime.timedelta(days=int((m.group(1) or '0').replace(' ', '')))).toordinal()
    m = ISO.match(v)
    if m:
        try: return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).toordinal()
        except ValueError: return None
    return None


def depth(s):
    E = []
    if not isinstance(s, dict): return E
    g = lambda k: s.get(k) if isinstance(s.get(k), list) else []
    need = (('signature', 6, 'services only this profession needs (a planner, a calculator, a checklist, a printable document …), each with a `where` sheet'),
            ('competitors', 3, 'named competitors with what each lacks'),
            ('tools', 2, 'calculators / planners (what-if grids included)'),
            ('messages', 3, 'ready WhatsApp texts for the profession\'s real moments'),
            ('documents', 1, 'printable letters or contracts filled from a record'),
            ('checklists', 1, 'stage checklists whose steps get due dates'))
    for k, n, what in need:
        if len(g(k)) < n: E.append(f'depth.services: `{k}` has {len(g(k))}, a specialised file needs at least {n} — {what}')
    tables = [t for t in g('tables') if isinstance(t, dict)]
    big = 0; spans = []
    for t in tables:
        k = t.get('key', '?'); cols = [c for c in t.get('columns', []) if isinstance(c, dict)]; rows = t.get('demo') if isinstance(t.get('demo'), list) else []
        n = len(rows)
        if len(cols) >= 4 and n < 12: E.append(f'depth.demo: table {k} has {n} demo rows, at least 12 realistic rows are needed (24+ in the main tables)')
        if n >= 24: big += 1
        for c in cols:
            ck = c.get('key', '?'); vals = [r.get(ck) for r in rows if isinstance(r, dict) and r.get(ck) not in (None, '')]
            if '_' in str(c.get('label', '')): E.append(f'depth.names: column label {c.get("label")!r} of {k} contains an underscore')
            if c.get('type') == 'date' and vals:
                ds = [day(v) for v in vals]
                if all(d is not None for d in ds) and len(ds) >= 6: spans.append(max(ds) - min(ds))
                if 'month' in ck:
                    bad = [v for v in vals if not (isinstance(v, str) and ISO.match(v) and v.endswith('-01'))]
                    if bad: E.append(f'depth.demo: {k}.{ck} must hold the 1st of each month as an absolute date (YYYY-MM-01), found {bad[:2]}')
            if n >= 12 and c.get('type') == 'list' and vals:
                used = len(set(vals)); lst = next((l for l in g('lists') if isinstance(l, dict) and l.get('key') == c.get('list')), None)
                if lst and len(lst.get('values', [])) >= 3 and used < 3: E.append(f'depth.demo: {k}.{ck} uses {used} of the list\'s values, use at least 3')
            if n >= 12 and c.get('type') == 'money' and vals:
                nums = [v for v in vals if isinstance(v, (int, float))]
                if nums:
                    top = max(nums.count(v) for v in set(nums))
                    if len(set(nums)) < 3 or top > 0.6 * len(nums): E.append(f'depth.demo: {k}.{ck} is near-identical ({len(set(nums))} distinct values, the commonest in {round(100 * top / len(nums))}% of {len(nums)} rows)')
        fc = cols[0] if cols else None
        if fc and fc.get('type') == 'text' and n >= 5:
            ids = [r.get(fc['key']) for r in rows if isinstance(r, dict)]
            if len(set(ids)) < len(ids): E.append(f'depth.demo: the first column {k}.{fc["key"]} repeats values, it must be unique')
        if '_' in str(t.get('sheet', '')): E.append(f'depth.names: sheet name {t.get("sheet")!r} contains an underscore, write it with spaces')
    if big < 2: E.append(f'depth.demo: {big} table(s) have 24+ demo rows, at least 2 are needed so the dashboard and charts show a real year')
    if spans and max(spans) < 270: E.append(f'depth.demo: the widest demo date column covers {max(spans)} days, spread the demo over at least 270 days')
    elif not spans: E.append('depth.demo: no date column has 6+ dated demo rows')
    for x in g('tools') + g('documents') + g('checklists'):
        if isinstance(x, dict) and '_' in str(x.get('sheet', x.get('title', ''))): E.append(f'depth.names: {x.get("sheet", x.get("title"))!r} contains an underscore')
    # pictures print these texts in every language
    L = s.get('listing') if isinstance(s.get('listing'), dict) else {}
    pic = [L.get('headline'), s.get('tagline'), (s.get('dashboard') or {}).get('title')]
    for x in g('signature'):
        if isinstance(x, dict): pic += [x.get('name'), x.get('why')]
    pic = [p for p in pic if isinstance(p, str) and p.strip()]
    i18n = s.get('i18n') if isinstance(s.get('i18n'), dict) else {}
    for lg in LANGS:
        d = i18n.get(lg) if isinstance(i18n.get(lg), dict) else {}
        gone = [p for p in dict.fromkeys(pic) if not isinstance(d.get(p), str) or not d[p].strip()]
        if gone: E.append(f'depth.pictures: i18n.{lg} lacks {len(gone)} text(s) the pictures print, e.g. {gone[0][:60]!r} — every picture would show English in {lg}')
    return E
