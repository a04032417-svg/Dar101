#!/usr/bin/env python3
"""xlfix.py — repairs what xlcheck.py finds in a ZIP of workbooks, without touching anything else (2026-11-09; the owner approved
fixing and replacing the two real-estate kits on sale). Standard library only, except `recalc` (LibreOffice + openpyxl).
  scan  <in.zip>... [--json out.json]   text left in English in each non-English workbook (same text, same cell as the English
                                        workbook), and whether a formula uses that text (then it must not be translated)
  fix   <in.zip> <out.zip> [--tr tr.json]  adds the missing _xlfn. prefix to post-2007 functions in every formula, and replaces
                                        English texts by their translation in each language ({"ar": {"English": "عربي"}, ...})
  recalc <zip>... [--json out.json]     recalculates every workbook in LibreOffice (engine/recalc.py, 4 at a time) and counts
                                        formula errors, plus the results of the formulas the fix touched"""
import os, re, sys, io, json, zipfile, tempfile, subprocess, html
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xlcheck import MODERN, FN, LANG_RE, KEEP_EN  # one list of functions for the check and the fix

FORMULA_EL = re.compile(r'<(f|formula|formula1|formula2|definedName)((?:\s[^>]*)?)(?<!/)>(.*?)</\1>', re.S)
SI = re.compile(r'<si>(.*?)</si>', re.S)
PLAIN_T = re.compile(r'^<t(\s[^>]*)?>(.*?)</t>$', re.S)
INLINE = re.compile(r'<is>\s*<t(\s[^>]*)?>(.*?)</t>\s*</is>', re.S)  # openpyxl writes texts inline, not as shared strings
MOD_RE = re.compile(r'_xlfn\.(' + '|'.join(re.escape(m) for m in sorted(MODERN, key=len, reverse=True)) + r')\(', re.I)


def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def prefix(f):
    """Insert _xlfn. before post-2007 functions written without it (outside text constants and quoted sheet names)."""
    out, i, n, changed = [], 0, len(f), 0
    while i < n:
        c = f[i]
        if c in '"\'':
            j = i + 1
            while j < n:
                if f[j] == c:
                    if j + 1 < n and f[j + 1] == c: j += 2; continue
                    break
                j += 1
            out.append(f[i:j + 1]); i = j + 1; continue
        m = FN.match(f, i) if (c.isalpha() or c == '_') and (i == 0 or not (f[i - 1].isalnum() or f[i - 1] in '_.')) else None
        if m:
            name = m.group(1)
            if name.upper() in MODERN: out.append('_xlfn.'); changed += 1
            out.append(m.group(0)); i += len(m.group(0)); continue
        out.append(c); i += 1
    return ''.join(out), changed


def fix_formulas(xml):
    count = [0]
    def one(m):
        new, k = prefix(html.unescape(m.group(3)))
        if not k: return m.group(0)
        count[0] += k; return f'<{m.group(1)}{m.group(2)}>{esc(new)}</{m.group(1)}>'
    return FORMULA_EL.sub(one, xml), count[0]


def strings(xml):
    """sharedStrings.xml -> list of plain texts (None for rich text)."""
    out = []
    for m in SI.finditer(xml):
        t = PLAIN_T.match(m.group(1).strip())
        out.append(html.unescape(t.group(2)) if t else None)
    return out


def translate(xml, tr):
    done = [0]
    def one(m):
        t = PLAIN_T.match(m.group(1).strip())
        if not t: return m.group(0)
        s = html.unescape(t.group(2))
        if s in tr and tr[s] and tr[s] != s:
            done[0] += 1; return f'<si><t xml:space="preserve">{esc(tr[s])}</t></si>'
        return m.group(0)
    return SI.sub(one, xml), done[0]


def translate_inline(xml, tr):
    done = [0]
    def one(m):
        s = html.unescape(m.group(2))
        if s in tr and tr[s] and tr[s] != s:
            done[0] += 1; return f'<is><t xml:space="preserve">{esc(tr[s])}</t></is>'
        return m.group(0)
    return INLINE.sub(one, xml), done[0]


def members(path):
    z = zipfile.ZipFile(path)
    return z, [i for i in z.infolist() if i.filename.lower().endswith('.xlsx')]


def lang_of(name):
    return (LANG_RE.findall(os.path.basename(name).rsplit('.', 1)[0]) or [''])[-1].lower()


def cells(book):
    """{sheet index: {cell: text}} for text cells, and the set of text constants used in formulas."""
    z = zipfile.ZipFile(io.BytesIO(book)); names = z.namelist()
    ss = strings(z.read('xl/sharedStrings.xml').decode('utf8')) if 'xl/sharedStrings.xml' in names else []
    wb = z.read('xl/workbook.xml').decode('utf8'); rels = z.read('xl/_rels/workbook.xml.rels').decode('utf8')
    target = {m.group(1): m.group(2) for m in re.finditer(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels)}
    target.update({m.group(2): m.group(1) for m in re.finditer(r'<Relationship[^>]*Target="([^"]+)"[^>]*Id="([^"]+)"', rels)})
    out, lits = {}, set()
    for si, m in enumerate(re.finditer(r'<sheet\b[^>]*?r:id="([^"]+)"', wb)):
        t = target.get(m.group(1), ''); part = t.lstrip('/') if t.startswith('/') else 'xl/' + t
        xml = z.read(part).decode('utf8'); d = out.setdefault(si, {})
        for c in re.finditer(r'<c r="([A-Z]+\d+)"([^>]*?)(?:/>|>(.*?)</c>)', xml, re.S):
            body = c.group(3) or ''
            if 't="s"' in c.group(2):
                v = re.search(r'<v>(\d+)</v>', body)
                if v and int(v.group(1)) < len(ss) and ss[int(v.group(1))] is not None: d[c.group(1)] = ss[int(v.group(1))]
            elif 't="inlineStr"' in c.group(2):
                v = INLINE.search(body)
                if v: d[c.group(1)] = html.unescape(v.group(2))
        for f in FORMULA_EL.finditer(xml): lits.update(re.findall(r'"((?:[^"]|"")*)"', html.unescape(f.group(3))))
    return out, lits


def scan(paths):
    res = {}
    for p in paths:
        z, items = members(p); books = {i.filename: z.read(i) for i in items}
        en = next((n for n in books if lang_of(n) == 'en' and 'demo' not in n.lower()), None)
        if not en: continue
        en_cells, _ = cells(books[en]); kit = res.setdefault(os.path.basename(p), {})
        for n, b in books.items():
            l = lang_of(n)
            if l in ('', 'en') or 'demo' in n.lower(): continue
            cs, lits = cells(b); found = {}
            for si, d in cs.items():
                for ref, t in d.items():
                    words = re.findall(r'[A-Za-z]{3,}', t)
                    if t == en_cells.get(si, {}).get(ref) and words and not re.match(r'^(https?://|www\.|\S+@\S+)', t) and not all(w.lower() in KEEP_EN for w in words):
                        e = found.setdefault(t, {'cells': [], 'in_formula': t in lits}); e['cells'].append(f'{si + 1}:{ref}')
            if found: kit[l] = found
    return res


def fix(src, dst, tr):
    z, _ = members(src); report = {}
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for info in z.infolist():
            data = z.read(info)
            if info.filename.lower().endswith('.xlsx'):
                data, report[info.filename] = fix_book(data, tr.get(lang_of(info.filename), {}) if 'demo' not in info.filename.lower() else {})
            out.writestr(info, data)
    return report


def fix_book(data, tr):
    if tr:  # a text that a formula compares with stays as it is, or the formula would stop matching it
        _, lits = cells(data); tr = {k: v for k, v in tr.items() if k not in lits}
    zin = zipfile.ZipFile(io.BytesIO(data)); buf = io.BytesIO(); nf = nt = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            b = zin.read(info); n = info.filename
            if n == 'xl/workbook.xml' or (n.startswith('xl/worksheets/') and n.endswith('.xml')):
                x, k = fix_formulas(b.decode('utf8')); k2 = 0
                if tr and n != 'xl/workbook.xml': x, k2 = translate_inline(x, tr)
                if k or k2: b = x.encode('utf8'); nf += k; nt += k2
            elif n == 'xl/sharedStrings.xml' and tr:
                x, k = translate(b.decode('utf8'), tr)
                if k: b = x.encode('utf8'); nt += k
            zout.writestr(info, b)
    return buf.getvalue(), {'formulas_prefixed': nf, 'texts_translated': nt}


def recalc_all(paths):
    from openpyxl import load_workbook
    work = tempfile.mkdtemp(prefix='xlfix-'); jobs = []
    for p in paths:
        z, items = members(p)
        for i in items:
            f = os.path.join(work, os.path.basename(p) + '__' + os.path.basename(i.filename)); open(f, 'wb').write(z.read(i)); jobs.append((p, i.filename, f))
    def one(job):
        p, name, f = job; touched = []
        wb = load_workbook(f)
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith('=') and MOD_RE.search(c.value): touched.append((ws.title, c.coordinate))
        r = subprocess.run([sys.executable, os.path.join(HERE, '..', 'engine', 'recalc.py'), f, '600'], capture_output=True, text=True)
        try: j = json.loads(r.stdout)
        except Exception: return p, name, {'error': (r.stdout + r.stderr)[-300:]}
        wv = load_workbook(f, data_only=True); nums = errs = empty = 0
        for t, ref in touched:
            v = wv[t][ref].value
            if isinstance(v, (int, float)): nums += 1
            elif isinstance(v, str) and v.startswith('#'): errs += 1
            else: empty += 1
        return p, name, {'formulas': j.get('total_formulas'), 'errors': j.get('total_errors'), 'error_summary': {k: v['count'] for k, v in (j.get('error_summary') or {}).items()},
                         'modern_cells': len(touched), 'modern_numbers': nums, 'modern_errors': errs, 'modern_blank': empty, 'seconds': j.get('seconds')}
    res = {}
    with ThreadPoolExecutor(4) as ex:
        for p, name, r in ex.map(one, jobs): res.setdefault(os.path.basename(p), {})[name] = r
    return res


if __name__ == '__main__':
    a = sys.argv[1:]; out = tr = None
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--tr' in a: i = a.index('--tr'); tr = json.load(open(a[i + 1], encoding='utf8')); a = a[:i] + a[i + 2:]
    mode, a = a[0], a[1:]
    r = scan(a) if mode == 'scan' else fix(a[0], a[1], tr or {}) if mode == 'fix' else recalc_all(a)
    if out: json.dump(r, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False)[:3000])
