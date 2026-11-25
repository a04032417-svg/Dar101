#!/usr/bin/env python3
"""Listing pictures (2400x1800 PNG) of a built product: real LibreOffice renders of the recalculated English demo (every number
on them was calculated by the spreadsheet), composed with captions taken from the spec (listing.features, table and form titles).
01-hero · 02-dashboard · 03..05 the most important sheets and forms · last = the 15 languages.
make_images(spec, demo_recalc_xlsx, meta, outdir) -> [png paths]
CLI: python3 images.py spec.json demo_recalculated.xlsx outdir   (meta read from <demo>.meta.json)"""
import os, sys, json, glob, shutil, tempfile, subprocess, base64, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LANGS, LANG_NAMES, RTL, FIXED, RECALC, tr, sheet_names
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter, column_index_from_string
from PIL import Image, ImageOps
sys.path.insert(0, os.path.dirname(RECALC))
try: from office.soffice import run_soffice
except Exception:  # (the verification worker: no skill helpers — LibreOffice is called directly, with a private profile)
    def run_soffice(args, **kw):
        import shutil as _sh
        exe = _sh.which('soffice') or _sh.which('libreoffice') or 'soffice'
        prof = 'file://' + os.path.join(tempfile.gettempdir(), f'fx-lo-img-{os.getpid()}')
        return subprocess.run([exe, f'-env:UserInstallation={prof}'] + list(args), **kw)

W, H = 2400, 1800
FONTS = "'Liberation Sans','DejaVu Sans','FreeSans','Noto Sans CJK SC',sans-serif"


def _ungroup_columns(ws):
    """split every grouped column entry (min..max) into one entry per column, same width/style, so one column can be hidden alone"""
    from openpyxl.worksheet.dimensions import ColumnDimension
    from openpyxl.utils import get_column_letter as _L
    for k, d in list(ws.column_dimensions.items()):
        lo, hi = (d.min or 0), (d.max or 0)
        if lo and hi and hi > lo:
            for i in range(lo, hi + 1):
                L = _L(i)
                nd = ColumnDimension(ws, index=L, width=d.width, hidden=d.hidden, bestFit=d.bestFit, customWidth=d.customWidth, outlineLevel=d.outlineLevel)
                nd.min = nd.max = i; ws.column_dimensions[L] = nd


def render(xlsx, meta, jobs, workdir, dpi=170, pad=26):
    """jobs: [(name, sheet, range, {'chart':bool,'a3':bool,'portrait':bool})] -> {name: png}. One LibreOffice run prints every job on its own page."""
    wb = load_workbook(xlsx, data_only=True)
    keep = []
    for name, sheet, rng, opt in jobs:
        src = wb[sheet]
        if sheet in [k[1] for k in keep]:                      # the same sheet twice: copy it (conditional colours too)
            ws = wb.copy_worksheet(src); ws.sheet_view.rightToLeft = src.sheet_view.rightToLeft
            for cf in src.conditional_formatting:
                for rule in cf.rules: ws.conditional_formatting.add(str(cf.sqref), rule)
            import copy as _cp                                  # (and its charts: a copy without them prints an empty page — v1.3)
            for ch in getattr(src, '_charts', []): ws.add_chart(_cp.deepcopy(ch))
            for im in getattr(src, '_images', []): ws.add_image(_cp.deepcopy(im))
        else: ws = src
        keep.append((name, ws.title, rng, opt, ws))
    titles = [k[1] for k in keep]
    for w in list(wb.worksheets):
        if w.title not in titles: wb.remove(w)
    wb._sheets = [k[4] for k in keep]
    for name, title, rng, opt, ws in keep:
        ws.data_validations.dataValidation = []; ws.freeze_panes = None; ws.print_area = rng; ws.print_title_rows = None
        ps = ws.page_setup; ps.orientation = 'portrait' if opt.get('portrait') else 'landscape'; ps.paperSize = 8 if opt.get('a3') else 9
        ps.fitToWidth = 1; ps.fitToHeight = 1; ws.sheet_properties.pageSetUpPr.fitToPage = True; ws.print_options.gridLines = False
        m = ws.page_margins; m.left = m.right = m.top = m.bottom = 0.2; m.header = m.footer = 0
        ws.oddHeader.center.text = ''; ws.oddFooter.center.text = ''
        ws.auto_filter.ref = None
        if opt.get('drop'): _ungroup_columns(ws)          # (engine 1.5: openpyxl keeps neighbours of one width as ONE entry D:F — hiding 'D' hid F too, so a table lost its calculated column)
        for L in opt.get('drop', ()): ws.column_dimensions[L].hidden = True
        if opt.get('chart'):
            mo = meta['monthly']; ch = BarChart(); ch.type = 'col'; ch.title = mo['title']; ch.style = 10; ch.height = 7.6; ch.width = 15.5
            ch.add_data(Reference(ws, min_col=mo['c1'], max_col=mo['c2'], min_row=mo['header_row'], max_row=mo['r2']), titles_from_data=True)
            ch.set_categories(Reference(ws, min_col=mo['cat'], min_row=mo['r1'], max_row=mo['r2'])); ch.y_axis.numFmt = '#,##0'
            ch.y_axis.delete = False; ch.x_axis.delete = False; ch.legend.position = 'b'
            for sr, col in zip(ch.series, mo['colors']): sr.graphicalProperties.solidFill = col; sr.graphicalProperties.line.solidFill = col
            ws.add_chart(ch, mo['at'])
    d = tempfile.mkdtemp(prefix='fxshot-', dir=workdir); x = os.path.join(d, 'p.xlsx'); wb.save(x)
    r = run_soffice(['--headless', '--convert-to', 'pdf', '--outdir', d, x], capture_output=True, text=True, timeout=300)
    pdf = os.path.join(d, 'p.pdf')
    if not os.path.exists(pdf): raise RuntimeError(f'LibreOffice made no PDF: {r.stdout[-300:]} {r.stderr[-300:]}')
    subprocess.run(['pdftoppm', '-r', str(dpi), '-png', pdf, os.path.join(d, 'pg')], check=True)
    pages = sorted(glob.glob(os.path.join(d, 'pg*.png')))
    if len(pages) != len(keep): raise RuntimeError(f'{len(pages)} pages printed for {len(keep)} pictures')
    out = {}
    for (name, *_), pg in zip(keep, pages):
        im = Image.open(pg).convert('RGB')
        bb = ImageOps.invert(im.convert('L')).point(lambda v: 255 if v > 10 else 0).getbbox()
        if bb: im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.size[0], bb[2] + pad), min(im.size[1], bb[3] + pad)))
        p = os.path.join(workdir, f'shot-{name}.png'); im.save(p); out[name] = p
    shutil.rmtree(d, ignore_errors=True)
    return out


def b64(p): return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
E = html.escape


def css(P, A):
    return f"""*{{box-sizing:border-box;margin:0}}body{{width:{W}px;height:{H}px;font-family:{FONTS};background:#F4F6FA;color:#14213D;overflow:hidden;display:flex;flex-direction:column}}
.top{{background:#{P};color:#fff;padding:58px 90px 52px}}.top h1{{font-size:78px;line-height:1.08;letter-spacing:-1px}}.top p{{font-size:36px;opacity:.9;margin-top:16px;line-height:1.3}}
.chips{{display:flex;gap:18px;flex-wrap:wrap;margin:34px 90px 0}}.chip{{background:#fff;border:3px solid #{P};color:#{P};border-radius:60px;padding:14px 30px;font-size:32px;font-weight:700}}
.chip.g{{border-color:#{A};color:#{P};background:#{A}22}}
.grid{{position:relative;flex:1;min-height:0;margin:30px 70px 56px;display:grid;gap:30px}}
.card{{background:#fff;border-radius:20px;box-shadow:0 16px 50px rgba(20,33,61,.16);padding:22px;display:flex;align-items:center;justify-content:center;overflow:hidden;width:100%;height:100%}}
.card img{{display:block;width:100%;height:100%;object-fit:contain}}"""


def page(P, A, title, sub, chips, items, cols='1fr', rows='1fr'):
    ch = ''.join(f'<span class="chip{" g" if i == 0 else ""}">{E(c)}</span>' for i, c in enumerate(chips))
    grid = ''.join(f'<div class="card" style="grid-area:{a}"><img src="{b64(p)}"></div>' for p, a in items)
    return (f'<html><head><meta charset="utf-8"><style>{css(P, A)}</style></head><body><div class="top"><h1>{E(title)}</h1><p>{E(sub)}</p></div>'
            f'<div class="chips">{ch}</div><div class="grid" style="grid-template-columns:{cols};grid-template-rows:{rows}">{grid}</div></body></html>')


def arrange(paths):
    """Grid template for 1-2 renders: side by side when they are tall, one above the other when they are wide."""
    if len(paths) < 2: return {'cols': '1fr', 'rows': '1fr', 'areas': ['1/1']}
    ar = [Image.open(p).size[0] / Image.open(p).size[1] for p in paths]
    if sum(ar) / len(ar) > 1.15:
        h = [1 / a for a in ar]; return {'cols': '1fr', 'rows': ' '.join(f'{x / sum(h):.2f}fr' for x in h), 'areas': [f'{i + 1}/1' for i in range(len(paths))]}
    return {'cols': ' '.join(f'{a / sum(ar):.2f}fr' for a in ar), 'rows': '1fr', 'areas': [f'1/{i + 1}' for i in range(len(paths))]}


def hero(P, A, name, tagline, feats, shot, badge, shot2=None):
    li = ''.join(f'<li><b>{E(a)}</b>' + (f'<small>{E(b)}</small>' if b else '') + '</li>' for a, b in feats)
    return f"""<html><head><meta charset="utf-8"><style>{css(P, A)}
body{{flex-direction:row}}.l{{width:980px;background:#{P};color:#fff;padding:100px 76px;display:flex;flex-direction:column}}.l h1{{font-size:{94 if len(name) <= 26 else 78}px;line-height:1.04;letter-spacing:-2px}}
.l p{{font-size:38px;opacity:.9;margin-top:30px;line-height:1.35}}.l ul{{list-style:none;margin-top:40px}}.l li{{font-size:34px;margin:18px 0;padding-left:58px;position:relative;line-height:1.25}}
.l li:before{{content:'✓';position:absolute;left:0;color:#{A};font-weight:700}}.l li small{{display:block;font-size:25px;opacity:.78;margin-top:4px;line-height:1.3}}.big{{align-self:flex-start;margin-top:auto;background:#{A};color:#{P};font-weight:800;font-size:38px;padding:18px 34px;border-radius:16px}}
.r{{flex:1;padding:70px 60px;display:flex;flex-direction:column;gap:46px;align-items:center;justify-content:center}}.r img{{max-width:100%;max-height:{780 if shot2 else 1640}px;border-radius:18px;box-shadow:0 24px 70px rgba(20,33,61,.25);background:#fff;padding:18px}}</style></head>
<body><div class="l"><h1>{E(name)}</h1><p>{E(tagline)}</p><ul>{li}</ul><div class="big">{E(badge)}</div></div><div class="r"><img src="{b64(shot)}">{f'<img src="{b64(shot2)}">' if shot2 else ''}</div></body></html>"""


def languages(spec, P, A, h1='15 languages — one purchase', sub='Every version is translated: sheet names, columns, drop-down lists, messages and the guide. Arabic, Persian and Urdu open right-to-left.'):
    cards = ''
    names = {n for _, n in sheet_names(spec, lambda x: x)}
    tk = [x['where'] for x in spec.get('signature', []) if x['where'] in names][:4] or [t['sheet'] for t in spec['tables']][:4]
    for l in LANGS:
        T = tr(spec, l); rtl = l in RTL
        sh = ' · '.join(T(x) if x != FIXED['sheet_messages'] else T(FIXED['sheet_messages']) for x in tk)
        cards += f'<div class="c" dir="{"rtl" if rtl else "ltr"}"><b>{E(LANG_NAMES[l])}</b><i>{E(T(spec["name"]))}</i><s>{E(sh)}</s></div>'
    extra = f""".g{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin:40px 80px 0}}.c{{background:#fff;border-radius:18px;padding:26px 30px;box-shadow:0 8px 26px rgba(20,33,61,.10);min-height:250px}}
.c b{{display:block;font-size:38px;color:#{P}}}.c i{{display:block;font-style:normal;font-size:30px;margin-top:8px;color:#14213D;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.c s{{display:block;text-decoration:none;font-size:26px;color:#6B7280;margin-top:14px;line-height:1.35;max-height:72px;overflow:hidden}}"""
    return f"""<html><head><meta charset="utf-8"><style>{css(P, A)}{extra}</style></head><body>
<div class="top"><h1>{html.escape(h1)}</h1><p>{html.escape(sub)}</p></div>
<div class="g">{cards}</div></body></html>"""


def pick_tables(spec, meta):
    """The most telling data sheets: named by a signature service first, then most calculated columns and colour alerts."""
    sig = {x['where'].lower() for x in spec.get('signature', [])}
    sc = []
    for i, t in enumerate(spec['tables']):
        m = meta['tables'][t['key']]
        sc.append((10 * (t['sheet'].lower() in sig) + m['calc'] * 2 + m['alerts'] + (1 if m['n_demo'] >= 10 else 0), -i, t))
    return [t for *_, t in sorted(sc, key=lambda x: (x[0], x[1]), reverse=True)]


def table_job(meta, t, maxrows=16):
    m = meta['tables'][t['key']]; n = min(max(m['n_demo'], 3), maxrows); ncol = min(m['ncols'], 14)
    return (t['key'], m['sheet'], f'A1:{get_column_letter(ncol)}{4 + n}', {'a3': ncol > 9})


def make_images(spec, demo_xlsx, meta, outdir, workdir=None):
    from playwright.sync_api import sync_playwright
    os.makedirs(outdir, exist_ok=True); workdir = workdir or tempfile.mkdtemp(prefix='fximg-'); os.makedirs(workdir, exist_ok=True)
    P, A = spec['colors']['primary'].lstrip('#'), spec['colors']['accent'].lstrip('#')
    d = spec['dashboard']; L = spec['listing']; sig = spec.get('signature', [])
    kpi_last = 5 + ((len(d['kpis']) + 3) // 4) * 3 - 2
    tabs = pick_tables(spec, meta); tools = spec.get('tools', [])[:2]
    printables = [('f', f) for f in spec.get('forms', [])] + [('d', x) for x in spec.get('documents', [])]
    if len(printables) > 2 and spec.get('documents') and spec.get('forms'): printables = [('f', spec['forms'][0]), ('d', spec['documents'][0])]
    printables = printables[:2]; chk = (spec.get('checklists') or [None])[0]; msgs = spec.get('messages', [])
    jobs = [('dash', meta['monthly']['sheet'], meta['dash_range'], {'chart': True, 'portrait': True}),
            ('dashk', meta['monthly']['sheet'], f'A1:M{kpi_last}', {'portrait': False})]
    jobs += [table_job(meta, t) for t in tabs[:3]]
    jobs += [('tool-' + x['key'], meta['tools'][x['key']]['sheet'], meta['tools'][x['key']]['range'], {'portrait': True}) for x in tools]
    for kind, f in printables:
        m = meta['forms' if kind == 'f' else 'documents'][f['key']]; jobs.append((f'{kind}-{f["key"]}', m['sheet'], m['range'], {'portrait': True}))
    if chk: m = meta['checklists'][chk['key']]; jobs.append(('chk', m['sheet'], m['range'], {'portrait': True}))
    if msgs: jobs.append(('msgs', meta['sheets']['msgs'], f'A1:D{4 + len(msgs)}', {'portrait': False}))
    shots = render(demo_xlsx, meta, jobs, workdir)
    def chips(sheets, fallback, n=3):
        low = [x.lower() for x in sheets]
        out = [x['name'] for x in sig if x['where'].lower() in low]
        for x in fallback:
            if x not in out: out.append(x)
        return out[:n]
    calcs = lambda t: [c['label'] for c in t['columns'] if c['type'] == 'calc']
    feats = [(x['name'], x['why']) for x in sig[:6]] if sig else [(x, '') for x in L['features'][:6]]
    pages = [('01-hero', hero(P, A, spec['name'], spec['tagline'], feats, shots['dashk'], 'Excel .xlsx · 15 languages', shots[tabs[0]['key']]))]
    pages.append(('02-dashboard', page(P, A, f'{d["title"]}: everything at a glance',
                  f'{len(d["kpis"])} numbers that update themselves, {d["monthly"]["title"].lower()} for the year you choose'
                  + (', ' + ', '.join(b['title'].lower() for b in d.get('breakdowns', [])) if d.get('breakdowns') else '') + '.',
                  [k['label'] for k in d['kpis'][:4]], [(shots['dash'], '1/1')])))
    t1 = tabs[0]
    pages.append(('03-' + t1['key'], page(P, A, t1['title'], t1['hint'], chips([t1['sheet']], calcs(t1)), [(shots[t1['key']], '1/1')])))
    if tools:
        ps = [shots['tool-' + x['key']] for x in tools]; g = arrange(ps)
        pages.append(('04-tools', page(P, A, ' and '.join(x['title'] for x in tools), tools[0]['hint'],
                      chips([x['sheet'] for x in tools], [o['label'] for x in tools for o in x['outputs']]), list(zip(ps, g['areas'])), cols=g['cols'], rows=g['rows'])))
    if printables:
        ps = [shots[f'{k}-{f["key"]}'] for k, f in printables]; g = arrange(ps)
        pages.append(('05-print', page(P, A, ' and '.join(f['title'] for _, f in printables) + ', ready to print', FIXED['form_hint'],
                      chips([f['sheet'] for _, f in printables], [f['title'] for _, f in printables]), list(zip(ps, g['areas'])), cols=g['cols'], rows=g['rows'])))
    if len(tabs) > 2:
        t2, t3 = tabs[1], tabs[2]
        pages.append((f'06-{t2["key"]}', page(P, A, f'{t2["title"]} and {t3["title"]}', f'{t2["hint"]} {t3["hint"]}',
                      chips([t2['sheet'], t3['sheet']], calcs(t2) + calcs(t3)), [(shots[t2['key']], '1/1'), (shots[t3['key']], '2/1')], rows='1fr 1fr')))
    if chk or msgs:
        items = ([(shots['chk'], '1/1')] if chk else []) + ([(shots['msgs'], f'{2 if chk else 1}/1')] if msgs else [])
        title = ' and '.join(([chk['title'] + ' checklist'] if chk else []) + (['WhatsApp messages'] if msgs else []))
        sub = ('Steps dated from the record you choose, with done and late status. ' if chk else '') + \
              (f'{len(msgs)} ready messages ({", ".join(m["moment"].lower() for m in msgs[:5])}) open WhatsApp with the details filled in.' if msgs else '')
        pages.append((f'{len(pages) + 1:02d}-workflow', page(P, A, title, sub, chips(([chk['title']] if chk else []) + (['Messages'] if msgs else []), [m['moment'] for m in msgs]),
                      items, rows='1.3fr 1fr' if len(items) == 2 else '1fr')))
    pages.append((f'{len(pages) + 1:02d}-languages', languages(spec, P, A)))
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        for name, htm in pages:
            f = os.path.join(workdir, name + '.html'); open(f, 'w', encoding='utf8').write(htm)
            pg.goto('file://' + f); pg.wait_for_timeout(250); o = os.path.join(outdir, name + '.png'); pg.screenshot(path=o); out.append(o)
        b.close()
    return out


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf8')); demo = sys.argv[2]
    meta = json.load(open(demo + '.meta.json', encoding='utf8')) if os.path.exists(demo + '.meta.json') else json.load(open(sys.argv[2].replace('/v/', '/build/') + '.meta.json'))
    print(json.dumps(make_images(spec, demo, meta, sys.argv[3]), indent=1))
