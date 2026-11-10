#!/usr/bin/env python3
"""verify(spec, workdir) — builds and recalculates (LibreOffice) the template and the demo of all 15 languages, 4 at a time, and requires:
  1. status success and 0 formula errors in every file;
  2. every language's demo = the English demo, cell by cell (numbers, dates, empty or not) — proof that translated lists and
     settings still drive the formulas;
  3. on the English demo: every KPI and every calc column gives at least one non-empty, non-error value; the monthly table has a
     non-zero value;
  4. the English demo built without the IFERROR safety wrappers ("raw") has no error either (an error there is hidden as a blank
     in the delivered files, so it is reported with its real cause).
Each error is reported as  sheet!cell · spec path · error · formula · spec DSL  so the architect can repair the spec.
CLI: python3 verify.py spec.json workdir   -> prints the report as JSON (exit 1 when not ok)"""
import sys, os, json, shutil, subprocess, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LANGS, RECALC
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
CAUSE = {'#DIV/0!': 'division by zero on this data — guard it, e.g. IF(x=0,"",y/x)',
         '#VALUE!': 'a value of the wrong type (text or blank where a number or date is needed)',
         '#N/A': 'MATCH/INDEX found nothing — guard it with IF(..="","",..) or IFERROR',
         '#NAME?': 'unknown function or name for Excel/LibreOffice',
         '#REF!': 'reference outside its range (INDEX past the end?)',
         '#NUM!': 'impossible number (e.g. DATEDIF with the start after the end)',
         '#NULL!': 'empty intersection of ranges'}


ERRS = ('#DIV/0!', '#VALUE!', '#N/A', '#NAME?', '#REF!', '#NUM!', '#NULL!')
def is_err(v): return isinstance(v, str) and (v.strip() in ERRS or v.startswith('Err:'))


def kindof(v):
    if v is None or v == '': return 'empty'
    if isinstance(v, (dt.datetime, dt.date, dt.time)): return 'date'
    if isinstance(v, bool): return 'num'
    return 'num' if isinstance(v, (int, float)) else 'text'


def compare(a, b):
    """Numbers, dates and empty/non-empty of two recalculated workbooks, cell by cell (sheets by position)."""
    wa, wb = openpyxl.load_workbook(a, data_only=True), openpyxl.load_workbook(b, data_only=True); bad = []; n = 0
    if len(wa.worksheets) != len(wb.worksheets): return 0, ['sheet count differs']
    for sa, sb in zip(wa.worksheets, wb.worksheets):
        for row in sa.iter_rows():
            for c in row:
                v1, v2 = c.value, sb[c.coordinate].value; k1, k2 = kindof(v1), kindof(v2)
                if k1 in ('num', 'date') or k2 in ('num', 'date'):
                    n += 1
                    if k1 != k2 or (k1 == 'num' and abs(float(v1) - float(v2)) > 1e-6 * max(1, abs(float(v1)))) or (k1 == 'date' and v1 != v2):
                        bad.append(f'{sb.title}!{c.coordinate}: English {v1!r}, here {v2!r}')
                elif (k1 == 'empty') != (k2 == 'empty'):
                    n += 1; bad.append(f'{sb.title}!{c.coordinate}: English {v1!r}, here {v2!r}')
        for row in sb.iter_rows():                          # cells only the translated file has
            for c in row:
                if kindof(c.value) in ('num', 'date') and kindof(sa[c.coordinate].value) == 'empty': n += 1; bad.append(f'{sb.title}!{c.coordinate}: English empty, here {c.value!r}')
    return n, bad


class Verify:
    def __init__(self, spec, workdir, today=None, threads=4, langs=None):
        self.spec = spec; self.wd = os.path.abspath(workdir); self.today = today or dt.date.today(); self.threads = threads
        self.langs = langs or LANGS
        for d in ('build', 'v'): os.makedirs(os.path.join(self.wd, d), exist_ok=True)
        self.spec_path = os.path.join(self.wd, 'spec.json'); json.dump(spec, open(self.spec_path, 'w', encoding='utf8'), ensure_ascii=False)
        self.errors, self.warnings, self.jobs = [], [], {}
        self._wbf = {}

    def name(self, lang, demo, raw=False): return f'{lang}{"-raw" if raw else "-demo" if demo else ""}'
    def path(self, kind, n): return os.path.join(self.wd, kind, n + '.xlsx')

    def job(self, lang, demo, raw=False):
        n = self.name(lang, demo, raw); b, v = self.path('build', n), self.path('v', n); t0 = time.time()
        cmd = [sys.executable, os.path.join(HERE, 'build.py'), self.spec_path, lang, b, '--today', self.today.isoformat()] + (['--demo'] if demo else []) + (['--raw'] if raw else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: return n, {'fail': f'build failed: {r.stderr.strip()[-900:]}'}
        shutil.copyfile(b, v)
        r = subprocess.run([sys.executable, RECALC, v, '600'], capture_output=True, text=True)
        try: j = json.loads(r.stdout)
        except Exception: return n, {'fail': f'recalc failed: {r.stdout[-400:]} {r.stderr[-400:]}'}
        if j.get('error'): return n, {'fail': 'recalc: ' + j['error']}
        return n, {'status': j.get('status'), 'formulas': j.get('total_formulas'), 'n_errors': j.get('total_errors', 0),
                   'errors': {k: x.get('locations', []) for k, x in (j.get('error_summary') or {}).items()}, 'seconds': round(time.time() - t0, 1)}

    def meta(self, n): return json.load(open(self.path('build', n) + '.meta.json', encoding='utf8'))
    def formula_at(self, n, sheet, cell):
        if n not in self._wbf: self._wbf[n] = openpyxl.load_workbook(self.path('build', n))
        try: return str(self._wbf[n][sheet][cell].value)
        except Exception: return '?'

    def explain(self, n, loc, err, where=''):
        sheet, _, cell = loc.rpartition('!'); sheet = sheet.strip("'")
        m = self.meta(n); org = m['origin'].get(sheet, {})
        col = ''.join(ch for ch in cell if ch.isalpha())
        o = org.get(cell) or org.get(col) or 'built by the engine'
        dsl = m['dsl'].get(o)
        return {'file': n, 'where': f'{sheet}!{cell}', 'spec': o, 'error': err, 'cause': CAUSE.get(err, ''), 'formula': self.formula_at(n, sheet, cell)[:400],
                **({'dsl': dsl} if dsl else {}), 'when': where}

    def run(self):
        t0 = time.time()
        todo = [('en', True, True), ('en', True, False)] + [(l, d, False) for l in self.langs for d in (False, True) if (l, d) != ('en', True)]
        with ThreadPoolExecutor(self.threads) as ex:
            for n, res in ex.map(lambda a: self.job(*a), todo): self.jobs[n] = res
        details = []
        for n, res in self.jobs.items():
            if 'fail' in res: self.errors.append(f'{n}: {res["fail"]}'); continue
            if res['status'] != 'success' or res['n_errors']:
                when = 'on the demo data without the IFERROR safety net' if n.endswith('-raw') else ('on the demo data' if n.endswith('-demo') else 'on the empty template')
                for err, locs in res['errors'].items():
                    for loc in locs[:20]: details.append(self.explain(n, loc, err, when))
                if res['status'] != 'success' and not res['errors']: self.errors.append(f'{n}: recalc status {res["status"]}')
        self.details = details; self.group(details)
        ok_en = 'fail' not in self.jobs.get('en-demo', {'fail': 1})
        self.checks = {}
        if ok_en: self.check_demo()
        self.compare = {}
        if ok_en:
            def cmp(l):
                n = self.name(l, True)
                if 'fail' in self.jobs.get(n, {'fail': 1}): return l, None
                return l, compare(self.path('v', 'en-demo'), self.path('v', n))
            with ThreadPoolExecutor(self.threads) as ex:
                for l, r in ex.map(cmp, [l for l in self.langs if l != 'en']):
                    if r is None: continue
                    nn, bad = r; self.compare[l] = {'compared': nn, 'different': len(bad)}
                    for b in bad[:15]: self.errors.append(f'{l}-demo differs from the English demo: {b}')
        self.seconds = round(time.time() - t0, 1)
        return self.report()

    def group(self, details):
        """One message per (when, spec element, error): languages and cells collapsed; an element that only fails because an element it
        reads fails is reported as a consequence, so the architect repairs the root."""
        import re
        g = {}
        for d in details:
            lang, _, kind = d['file'].partition('-')
            k = (d['when'], d['spec'], d['error']); x = g.setdefault(k, {'langs': [], 'cells': [], 'd': d})
            if lang not in x['langs']: x['langs'].append(lang)
            if d['where'] not in x['cells']: x['cells'].append(d['where'])
        failing = {k[1] for k in g}
        def deps(dsl):
            out = set()
            for kind, arg in re.findall(r'\{(col|range):([^{}]*)\}', dsl or ''):
                if kind == 'range' and '.' in arg: t, c = arg.split('.'); out.add(f'tables[{t}].columns[{c}]')
            return out
        for (when, spec, err), x in sorted(g.items(), key=lambda kv: kv[0]):
            d = x['d']; m = re.match(r'tables\[(\w+)\]', spec)
            dd = deps(d.get('dsl'))
            if m: dd |= {f'tables[{m.group(1)}].columns[{c}]' for c in re.findall(r'\{col:(\w+)\}', d.get('dsl') or '')}
            up = sorted(dd & failing - {spec})
            langs = 'all languages' if len(x['langs']) == len(self.langs) > 1 else ', '.join(x['langs'])
            cells = ', '.join(x['cells'][:4]) + (f' and {len(x["cells"]) - 4} more' if len(x['cells']) > 4 else '')
            if up: self.errors.append(f"{spec} = {err} {when} ({langs}; {cells}) — only because {', '.join(up)} fails")
            else: self.errors.append(f"{spec} = {err} {when} ({langs}; {cells}) — {d['cause']} — formula {d['formula']}" + (f" — spec: {d['dsl']}" if d.get('dsl') else ''))

    def check_demo(self):
        n = 'en-demo'; m = self.meta(n); wb = openpyxl.load_workbook(self.path('v', n), data_only=True)
        k_ok = 0
        for k in m['kpis']:
            v = wb[k['sheet']][k['cell']].value
            if v is None or v == '' or is_err(v): self.errors.append(f"en-demo: KPI '{k['label']}' ({k['sheet']}!{k['cell']}, {k['origin']}) is {'an error ' + str(v) if is_err(v) else 'empty'} on the demo data — spec: {m['dsl'].get(k['origin'])}")
            else: k_ok += 1
        c_ok = 0
        for c in m['calc_cols']:
            ws = wb[c['sheet']]; vals = [ws[f"{c['col']}{r}"].value for r in range(c['first'], c['last'] + 1)]
            good = [v for v in vals if v not in (None, '') and not is_err(v)]
            if good: c_ok += 1
            else: self.errors.append(f"en-demo: calc column '{c['label']}' ({c['sheet']}!{c['col']}, {c['origin']}) has no value on any demo row — spec: {m['dsl'].get(c['origin'])}")
        mo = m['monthly']; ws = wb[mo['sheet']]
        nz = sum(1 for r in range(mo['r1'], mo['r2'] + 1) for cc in range(mo['c1'], mo['c2'] + 1) if isinstance(ws.cell(r, cc).value, (int, float)) and ws.cell(r, cc).value != 0)
        if not nz: self.errors.append(f"en-demo: the monthly table ({mo['sheet']}) has no non-zero value for the demo year — put demo dates of the series tables in that year")
        nser = mo['c2'] - mo['c1'] + 1
        for j in range(nser):
            if not any(isinstance(ws.cell(r, mo['c1'] + j).value, (int, float)) and ws.cell(r, mo['c1'] + j).value != 0 for r in range(mo['r1'], mo['r2'] + 1)):
                self.warnings.append(f"en-demo: monthly series {j + 1} is zero in every month of the demo year")
        t_ok = 0
        for x in m.get('tool_cells', []):
            v = wb[x['sheet']][x['cell']].value
            if v is None or v == '' or is_err(v): self.errors.append(f"en-demo: tool output '{x['label']}' ({x['sheet']}!{x['cell']}, {x['origin']}) is {'an error ' + str(v) if is_err(v) else 'empty'} — spec: {m['dsl'].get(x['origin'])}")
            else: t_ok += 1
        ck_ok = 0
        for x in m.get('checks', []):
            ws = wb[x['sheet']]; vals = [ws[f"{x['col']}{r}"].value for r in range(x['first'], x['last'] + 1)]
            bad = [f"{x['col']}{x['first'] + i}" for i, v in enumerate(vals) if v in (None, '') or is_err(v) or not isinstance(v, (dt.date, dt.datetime))]
            if bad: self.errors.append(f"en-demo: checklist '{x['label']}' ({x['sheet']}) has no due date in {', '.join(bad[:5])} — does the demo table hold a start date for the chosen record? ({x['origin']})")
            else: ck_ok += 1
        mg_ok = 0
        for x in m.get('msg_cols', []):
            ws = wb[x['sheet']]
            if any(ws[f"{x['col']}{r}"].value not in (None, '') and not is_err(ws[f"{x['col']}{r}"].value) for r in range(x['first'], x['last'] + 1)): mg_ok += 1
            else: self.errors.append(f"en-demo: message '{x['label']}' ({x['sheet']}!{x['col']}, {x['origin']}) gives no WhatsApp link on any demo row — are the phone numbers in the demo?")
        d_empty = [f"{x['sheet']}!{x['cell']}" for x in m.get('doc_cells', []) if wb[x['sheet']][x['cell']].value in (None, '')]
        if d_empty: self.warnings.append('en-demo: document paragraphs empty for the demo record: ' + ', '.join(d_empty[:6]))
        f_empty = [f"{f['sheet']}!{f['cell']} '{f['label']}'" for f in m['form_fields'] if wb[f['sheet']][f['cell']].value in (None, '')]
        if f_empty: self.warnings.append('en-demo: form fields empty for the demo record: ' + ', '.join(f_empty))
        # v1.3: charts that show something, gauges that hold a share, numbers that fit their column (no "####" in Excel)
        ch_ok = 0
        for x in m.get('charts', []):
            ws = wb[x['sheet']]
            vals = [ws.cell(r, cc).value for r in range(x['r1'], x['r2'] + 1) for cc in range(x['c1'], x['c2'] + 1)]
            if any(is_err(v) for v in vals): self.errors.append(f"en-demo: chart '{x['title']}' ({x['origin']}) has an error in its numbers")
            elif not any(isinstance(v, (int, float)) and v != 0 for v in vals): self.errors.append(f"en-demo: chart '{x['title']}' ({x['origin']}) shows nothing on the demo data — its series need demo rows in the chosen year (and its categories)")
            else: ch_ok += 1
        g_ok = 0
        for x in m.get('gauges', []):
            v = wb[x['sheet']][x['cell']].value
            if not isinstance(v, (int, float)) or is_err(v) or not 0 <= v <= 1: self.errors.append(f"en-demo: gauge '{x['title']}' ({x['origin']}) is {v!r}, not a share between 0 and 1")
            elif v == 0: self.errors.append(f"en-demo: gauge '{x['title']}' ({x['origin']}) is 0% on the demo data — the demo must show what it measures")
            else: g_ok += 1
        narrow = []
        for sheet, cols in m.get('widths', {}).items():
            ws = wb[sheet]
            for L, w in cols.items():
                for r in range(5, min(ws.max_row, 400) + 1):
                    v = ws[f'{L}{r}'].value
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        need = len(f'{v:,.0f}') + (3 if isinstance(v, float) and v != int(v) and abs(v) < 1000 else 0) + 2
                        if need > w: narrow.append(f'{sheet}!{L}{r} ({need} > {w})'); break
        for n_ in narrow[:10]: self.errors.append(f'en-demo: a number does not fit its column, Excel would show #### — {n_}')
        self.checks = {'charts_ok': ch_ok, 'charts': len(m.get('charts', [])), 'gauges_ok': g_ok, 'gauges': len(m.get('gauges', [])), 'kpis_ok': k_ok, 'kpis': len(m['kpis']), 'calc_cols_ok': c_ok, 'calc_cols': len(m['calc_cols']), 'monthly_nonzero_cells': nz,
                       'form_fields_filled': len(m['form_fields']) - len(f_empty), 'form_fields': len(m['form_fields']),
                       'tool_outputs_ok': t_ok, 'tool_outputs': len(m.get('tool_cells', [])), 'checklists_ok': ck_ok, 'checklists': len(m.get('checks', [])),
                       'message_columns_ok': mg_ok, 'message_columns': len(m.get('msg_cols', [])),
                       'document_paragraphs_filled': len(m.get('doc_cells', [])) - len(d_empty), 'document_paragraphs': len(m.get('doc_cells', []))}

    def report(self):
        files = {l: self.path('build', l) for l in self.langs}
        return {'ok': not self.errors, 'errors': self.errors, 'warnings': self.warnings, 'checks': self.checks, 'compare': self.compare,
                'jobs': {n: {k: v for k, v in r.items() if k != 'errors'} for n, r in sorted(self.jobs.items())},
                'files': {'templates': files, 'demo_en': self.path('build', 'en-demo'), 'demo_en_recalc': self.path('v', 'en-demo'),
                          'meta_demo_en': self.path('build', 'en-demo') + '.meta.json',
                          # v1.4: every language's recalculated demo, for its own pictures
                          'demo_recalc': {l: self.path('v', self.name(l, True)) for l in self.langs if 'fail' not in self.jobs.get(self.name(l, True), {'fail': 1})},
                          'meta_demo': {l: self.path('build', self.name(l, True)) + '.meta.json' for l in self.langs}}, 'seconds': self.seconds, 'today': self.today.isoformat()}


def verify(spec, workdir, today=None, threads=4, langs=None):
    return Verify(spec, workdir, today, threads, langs).run()


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf8'))
    rep = verify(spec, sys.argv[2], langs=sys.argv[3].split(',') if len(sys.argv) > 3 else None)
    short = {k: rep[k] for k in ('ok', 'checks', 'compare', 'seconds')} | {'errors': rep['errors'][:40], 'n_errors': len(rep['errors']), 'warnings': rep['warnings'][:10],
             'formulas': {n: j.get('formulas') for n, j in rep['jobs'].items()}}
    print(json.dumps(short, ensure_ascii=False, indent=1))
    sys.exit(0 if rep['ok'] else 1)
