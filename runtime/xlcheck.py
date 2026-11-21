#!/usr/bin/env python3
"""xlcheck.py — the Excel rules LibreOffice does not enforce (2026-11-09; the owner: «تأكد ان ملفات اكسل تعمل فعلا بلا اي اخطاء»).
verify.py recalculates every workbook in LibreOffice and finds every formula error there. But LibreOffice accepts things Microsoft
Excel rejects or shows as #NAME? / «We found a problem with some content». This script reads each .xlsx as Excel would (the raw
OOXML, standard library only, so it runs before any tool is installed) and reports, per file:
  problems (Excel breaks):  a part that does not parse; a post-2007 function stored without its _xlfn. prefix (#NAME? in Excel);
    a formula longer than 8192 characters, nested deeper than 64 functions, or with a text constant longer than 255 characters;
    an in-cell list (data validation) longer than 255 characters; #REF! anywhere (cells, names, lists, rules, charts); a bad sheet
    name; a text longer than 32767 characters; formulas without saved values and without fullCalcOnLoad (Excel shows them empty);
    an Arabic/Persian/Urdu workbook with a sheet not right-to-left.
  warnings (worth a look):  a function this checker does not know; a function that needs Excel 2019/365; a demo workbook whose
    formulas have no saved values (Excel's Protected View shows them empty until «Enable Editing»); text left in English in
    another language's workbook (compared cell by cell with the English workbook of the same set).
usage: xlcheck.py <dir|file.xlsx|file.zip>... [--json out.json] [--detail]     exit 0 always; the JSON says what failed."""
import os, re, sys, json, zipfile, io
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
# Functions that Excel stores as _xlfn.NAME (added after the file format's standard). Written without the prefix, Excel shows #NAME?.
# Checked 2026-11-09 against the standard's own list (openpyxl FORMULAE) and LibreOffice: NETWORKDAYS.INTL and WORKDAY.INTL are in the
# standard and are written WITHOUT the prefix (with it, LibreOffice shows #NAME?) — the first audit flagged them by mistake.
MODERN = set('''AGGREGATE ARABIC BASE BITAND BITLSHIFT BITOR BITRSHIFT BITXOR BYCOL BYROW CEILING.MATH CEILING.PRECISE CHOOSECOLS
CHOOSEROWS CONCAT COT COTH CSC CSCH DAYS DECIMAL DROP ENCODEURL EXPAND FILTER FILTERXML FLOOR.MATH FLOOR.PRECISE FORMULATEXT HSTACK
IFNA IFS IMAGE ISFORMULA ISOMITTED ISOWEEKNUM LAMBDA LET MAKEARRAY MAP MAXIFS MINIFS MODE.MULT MODE.SNGL NUMBERVALUE
PERCENTILE.EXC PERCENTILE.INC QUARTILE.EXC QUARTILE.INC RANDARRAY RANK.AVG RANK.EQ REDUCE SCAN SEC SECH SEQUENCE SHEET SHEETS SORT
SORTBY STDEV.P STDEV.S SWITCH TAKE TEXTAFTER TEXTBEFORE TEXTJOIN TEXTSPLIT TOCOL TOROW UNIQUE VALUETOTEXT ARRAYTOTEXT VAR.P VAR.S
VSTACK WEBSERVICE WRAPCOLS WRAPROWS XLOOKUP XMATCH XOR'''.split())
NEEDS_365 = set('''BYCOL BYROW CHOOSECOLS CHOOSEROWS DROP EXPAND FILTER HSTACK IMAGE ISOMITTED LAMBDA LET MAKEARRAY MAP RANDARRAY REDUCE
SCAN SEQUENCE SORT SORTBY TAKE TEXTAFTER TEXTBEFORE TEXTSPLIT TOCOL TOROW UNIQUE VSTACK WRAPCOLS WRAPROWS XLOOKUP XMATCH ARRAYTOTEXT
VALUETOTEXT'''.split())
NEEDS_2019 = set('CONCAT IFS MAXIFS MINIFS SWITCH TEXTJOIN'.split())
CLASSIC = set('''ABS ACOS ADDRESS AND AREAS ASIN ATAN ATAN2 AVERAGE AVERAGEA AVERAGEIF AVERAGEIFS CEILING CELL CHAR CHOOSE CLEAN CODE
COLUMN COLUMNS CONCATENATE COS COUNT COUNTA COUNTBLANK COUNTIF COUNTIFS CUMIPMT CUMPRINC DATE DATEDIF DATEVALUE DAY DAYS360 DEGREES
DOLLAR EDATE EOMONTH ERROR.TYPE EVEN EXACT EXP FACT FALSE FIND FIXED FLOOR FREQUENCY FV GCD GETPIVOTDATA HLOOKUP HOUR HYPERLINK IF
IFERROR INDEX INDIRECT INFO INT IPMT IRR ISBLANK ISERR ISERROR ISEVEN ISLOGICAL ISNA ISNONTEXT ISNUMBER ISODD ISREF ISTEXT LARGE LCM
LEFT LEN LN LOG LOG10 LOOKUP LOWER MATCH MAX MAXA MEDIAN MID MIN MINA MINUTE MMULT MOD MODE MONTH MROUND N NA NETWORKDAYS NOT NOW
NPER NPV ODD OFFSET OR PERCENTILE PI PMT POWER PPMT PRODUCT PROPER PV QUARTILE QUOTIENT RADIANS RAND RANDBETWEEN RANK RATE REPLACE
REPT RIGHT ROMAN ROUND ROUNDDOWN ROUNDUP ROW ROWS SEARCH SECOND SIGN SIN SMALL SQRT STDEV STDEVA STDEVP SUBSTITUTE SUBTOTAL SUM SUMIF
SUMIFS SUMPRODUCT SUMSQ T TAN TEXT TIME TIMEVALUE TODAY TRANSPOSE TRIM TRUE TRUNC TYPE UPPER VALUE VAR VARA VARP VLOOKUP WEEKDAY
WEEKNUM WORKDAY YEAR YEARFRAC NETWORKDAYS.INTL WORKDAY.INTL ISO.CEILING'''.split())
RTL = ('ar', 'fa', 'ur')
LANG_RE = re.compile(r'(?:^|[_\-./])(en|ar|fr|es|de|it|pt|tr|nl|ru|fa|ur|hi|zh|id)(?=$|[_\-.])', re.I)
DETAIL = False  # --detail adds formula and text excerpts (kept out of the public branch by default)
KEEP_EN = set('excel whatsapp pro crm kpi email e-mail id url pdf vat iban swift sku qr ok'.split())


FN = re.compile(r'([A-Za-z_][A-Za-z0-9_.]*)\(')
CACHE = {}  # the same formula with other row numbers scans the same (a column of 3000 rows is one scan)


def scan(f):
    key = re.sub(r'\d+', '#', f)
    if key not in CACHE: CACHE[key] = _scan(f)
    return CACHE[key]


def _scan(f):
    """-> (functions [(name, has_prefix)], max nesting, longest text constant). Skips text and quoted sheet names."""
    funcs, depth, deep, longest, i, n, stack = [], 0, 0, 0, 0, len(f), []
    while i < n:
        c = f[i]
        if c == '"':
            j, s = i + 1, 0
            while j < n:
                if f[j] == '"':
                    if j + 1 < n and f[j + 1] == '"': j += 2; s += 1; continue
                    break
                j += 1; s += 1
            longest = max(longest, s); i = j + 1; continue
        if c == "'":
            j = i + 1
            while j < n and not (f[j] == "'" and (j + 1 >= n or f[j + 1] != "'")): j += 2 if f[j] == "'" else 1
            i = j + 1; continue
        m = FN.match(f, i) if (c.isalpha() or c == '_') and (i == 0 or not (f[i - 1].isalnum() or f[i - 1] in '_.')) else None
        if m:
            name = m.group(1).upper(); pre = name.startswith('_XLFN.') or name.startswith('_XLWS.')
            name = re.sub(r'^(_XLFN\.|_XLWS\.|_XLPM\.)+', '', name)
            funcs.append((name, pre)); stack.append(True); depth += 1; deep = max(deep, depth); i += len(m.group(0)); continue
        if c == '(': stack.append(False)
        elif c == ')' and stack:
            if stack.pop(): depth -= 1
        i += 1
    return funcs, deep, longest


class Book:
    def __init__(self, name, z):
        self.name, self.z, self.problems, self.warnings, self.formulas, self.nocache = name, z, [], [], 0, 0
        self.cells = {}  # sheet index -> {cell: text} (visible text, for the untranslated check)
        self.lang = (LANG_RE.findall(os.path.basename(name).rsplit('.', 1)[0]) or [''])[-1].lower()
        self.demo = 'demo' in os.path.basename(name).lower()

    def p(self, where, msg, detail=''): self.problems.append(f'{where}: {msg}' + (f' — {detail}' if DETAIL and detail else ''))
    def w(self, where, msg, detail=''): self.warnings.append(f'{where}: {msg}' + (f' — {detail}' if DETAIL and detail else ''))

    def xml(self, part):
        try: return ET.fromstring(self.z.read(part))
        except KeyError: return None
        except Exception as x: self.p(part, f'does not parse ({str(x)[:80]}) — Excel would ask to repair the file'); return None

    def formula(self, where, f):
        if not f: return
        if '#REF!' in f: self.p(where, '#REF! in the formula', f[:120])
        if len(f) > 8192: self.p(where, f'formula of {len(f)} characters (Excel allows 8192)')
        funcs, deep, longest = scan(f)
        if deep > 64: self.p(where, f'functions nested {deep} deep (Excel allows 64)')
        if longest > 255: self.p(where, f'a text constant of {longest} characters in the formula (Excel allows 255)', f[:100])
        for name, pre in funcs:
            if name in MODERN and not pre: self.p(where, f'{name} written without _xlfn. — Excel shows #NAME?')
            elif name in NEEDS_365: self.w('functions', f'{name} needs Excel 365/2021 (#NAME? in older Excel)')
            elif name in NEEDS_2019: self.w('functions', f'{name} needs Excel 2019 or later')
            elif name not in CLASSIC and name not in MODERN: self.w('functions', f'{name} is not a function this checker knows — check it opens in Excel')

    def run(self):
        try: bad = self.z.testzip()
        except Exception as x: self.p('zip', f'unreadable ({x})'); return self
        if bad: self.p('zip', f'corrupt part {bad}'); return self
        for part in self.z.namelist():
            if part.endswith('.xml') or part.endswith('.rels'):
                try: ET.fromstring(self.z.read(part))
                except Exception as x: self.p(part, f'does not parse ({str(x)[:80]}) — Excel would ask to repair the file')
        wb = self.xml('xl/workbook.xml')
        if wb is None: self.p('workbook', 'xl/workbook.xml missing'); return self
        rels = self.xml('xl/_rels/workbook.xml.rels'); target = {}
        for r in (rels if rels is not None else []):
            t = r.get('Target', ''); target[r.get('Id')] = t.lstrip('/') if t.startswith('/') else 'xl/' + t
        ss = self.xml('xl/sharedStrings.xml'); strings = []
        for si in (ss.findall('m:si', NS) if ss is not None else []):
            strings.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
        for k, s in enumerate(strings):
            if len(s) > 32767: self.p('sharedStrings', f'text #{k} has {len(s)} characters (Excel allows 32767)')
        seen = set(); RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        sheets = wb.findall('m:sheets/m:sheet', NS)
        for s in sheets:
            nm = s.get('name', '')
            if not nm or len(nm) > 31 or re.search(r'[\[\]:*?/\\]', nm) or nm.lower() == 'history' or nm.startswith("'") or nm.endswith("'"):
                self.p('sheets', f'sheet name {nm!r} is not allowed in Excel')
            if nm.lower() in seen: self.p('sheets', f'two sheets named {nm!r} (Excel ignores case)')
            seen.add(nm.lower())
        for d in wb.findall('m:definedNames/m:definedName', NS): self.formula(f"name {d.get('name')}", d.text or '')
        calc = wb.find('m:calcPr', NS); full = calc is not None and calc.get('fullCalcOnLoad') in ('1', 'true')
        for si, s in enumerate(sheets):
            nm = s.get('name'); ws = self.xml(target.get(s.get(RID), ''))
            if ws is None: continue
            if self.lang in RTL:
                views = ws.findall('m:sheetViews/m:sheetView', NS)
                if not views or any(v.get('rightToLeft') not in ('1', 'true') for v in views): self.p(nm, 'not right-to-left in a right-to-left language')
            cells = self.cells.setdefault(si, {})
            for c in ws.iter('{%s}c' % NS['m']):
                f = c.find('m:f', NS); v = c.find('m:v', NS); ref = c.get('r', '?')
                if f is not None:
                    self.formulas += 1
                    if f.text: self.formula(f'{nm}!{ref}', f.text)
                    if v is None: self.nocache += 1
                    continue
                if c.get('t') == 's' and v is not None and v.text and v.text.isdigit() and int(v.text) < len(strings): cells[ref] = strings[int(v.text)]
                elif c.get('t') == 'inlineStr':
                    t = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
                    if len(t) > 32767: self.p(f'{nm}!{ref}', f'text of {len(t)} characters (Excel allows 32767)')
                    cells[ref] = t
            for dv in ws.iter('{%s}dataValidation' % NS['m']):
                f1 = dv.find('m:formula1', NS); t = (f1.text or '') if f1 is not None else ''
                if dv.get('type') == 'list' and t.startswith('"') and len(t) - 2 > 255: self.p(f"{nm} list {dv.get('sqref')}", f'in-cell list of {len(t) - 2} characters (Excel allows 255)')
                for fx in dv.findall('m:formula1', NS) + dv.findall('m:formula2', NS):
                    if not (dv.get('type') == 'list' and (fx.text or '').startswith('"')): self.formula(f"{nm} list {dv.get('sqref')}", fx.text or '')
            for cf in ws.iter('{%s}cfRule' % NS['m']):
                for fx in cf.findall('m:formula', NS): self.formula(f'{nm} rule', fx.text or '')
            for x in ws.iter():  # x14 extension lists and rules: <xm:f>
                if x.tag.endswith('}f') and x.tag != '{%s}f' % NS['m'] and x.text and '#REF!' in x.text: self.p(f'{nm} extension', '#REF!', x.text[:100])
        names = {s.get('name') for s in sheets}
        for part in self.z.namelist():
            if part.startswith('xl/charts/chart') and part.endswith('.xml'):
                ch = self.xml(part)
                for x in (ch.iter() if ch is not None else []):
                    if x.tag.endswith('}f') and x.text:
                        if '#REF!' in x.text: self.p(part, '#REF! in the chart data', x.text[:80])
                        m = re.match(r"^\(?'?((?:[^'!]|'')+)'?!", x.text)
                        if m and m.group(1).replace("''", "'") not in names: self.p(part, f'chart refers to a missing sheet {m.group(1)!r}')
        if self.nocache and not full: self.p('workbook', f'{self.nocache} formulas without saved values and without fullCalcOnLoad — Excel shows them empty')
        elif self.nocache and self.demo: self.w('demo', f'{self.nocache} formulas without saved values — in Excel Protected View the demo looks empty until «Enable Editing»')
        return self


def compare(books):
    """Text left in English: the same text in the same cell of the same sheet as the English workbook of the set."""
    groups = {}
    for b in books:
        key = LANG_RE.sub('_', os.path.basename(b.name).rsplit('.', 1)[0]).lower(); groups.setdefault((os.path.dirname(b.name), key), []).append(b)
    for g in groups.values():
        en = next((b for b in g if b.lang == 'en' and not b.demo), None) or next((b for b in g if b.lang == 'en'), None)
        if not en: continue
        for b in g:
            if b is en or b.lang in ('', 'en') or b.demo != en.demo: continue
            same = []
            # a text every other language also kept (a helper-column key, a code, a currency) is by design, not an oversight
            others = [o for o in g if o is not b and o.lang not in ('', 'en') and o.demo == en.demo]
            for si, cells in b.cells.items():
                ref_cells = en.cells.get(si, {})
                for ref, t in cells.items():
                    words = re.findall(r'[A-Za-z]{3,}', t or '')
                    if others and all(o.cells.get(si, {}).get(ref) == t for o in others): continue
                    if t == ref_cells.get(ref) and words and not re.match(r'^(https?://|www\.|\S+@\S+)', t) and not all(w.lower() in KEEP_EN for w in words):
                        if b.lang in ('ar', 'fa', 'ur', 'ru', 'hi', 'zh') or len(words) >= 3: same.append(f'{si + 1}:{ref} {t[:40]!r}')
            if same: b.w('language', f'{len(same)} text cell(s) still in English, e.g. ' + ', '.join(x.split(' ')[0] for x in same[:6]), '; '.join(same[:4]))


def books_in(path):
    out = []
    if path.lower().endswith('.zip'):
        outer = zipfile.ZipFile(path)
        for n in outer.namelist():
            if n.lower().endswith('.xlsx') and not os.path.basename(n).startswith('~$'):
                out.append(Book(os.path.join(os.path.basename(path), n), zipfile.ZipFile(io.BytesIO(outer.read(n)))))
            elif n.lower().endswith('.zip'):
                inner = zipfile.ZipFile(io.BytesIO(outer.read(n)))
                for m in inner.namelist():
                    if m.lower().endswith('.xlsx'): out.append(Book(os.path.join(os.path.basename(path), n, m), zipfile.ZipFile(io.BytesIO(inner.read(m)))))
    elif path.lower().endswith('.xlsx'):
        try: out.append(Book(path, zipfile.ZipFile(path)))
        except Exception as x: b = Book(path, None); b.p('zip', f'unreadable ({x})'); out.append(b)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            if os.path.basename(root) == 'v': continue  # LibreOffice's recalculated copies, not what ships
            for fn in sorted(files):
                if fn.lower().endswith(('.xlsx', '.zip')) and not fn.startswith('~$'): out += books_in(os.path.join(root, fn))
    return out


def check(paths):
    books = []
    for p in paths: books += books_in(p)
    for b in books:
        if b.z is not None: b.run()
    compare(books)
    files = {b.name: {'lang': b.lang, 'formulas': b.formulas, 'problems': b.problems[:30], 'warnings': sorted(set(b.warnings))[:15]}
             for b in books if b.problems or b.warnings}
    return {'files': len(books), 'formulas': sum(b.formulas for b in books), 'problems': sum(len(b.problems) for b in books),
            'warnings': sum(len(set(b.warnings)) for b in books), 'by_file': files}


if __name__ == '__main__':
    a = sys.argv[1:]; out = None
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--detail' in a: a.remove('--detail'); DETAIL = True
    r = check(a)
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); json.dump(r, open(out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: r[k] for k in ('files', 'formulas', 'problems', 'warnings')}))
    for n, x in list(r['by_file'].items())[:20]:
        for m in x['problems'][:5]: print('PROBLEM', n, '|', m)
        for m in x['warnings'][:3]: print('warning', n, '|', m)
