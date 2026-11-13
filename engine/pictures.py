#!/usr/bin/env python3
"""pictures.py (engine v1.4) — the listing pictures of a built product in the board design (board.py): real LibreOffice renders of the
recalculated English demo, in a window with the file's own tabs, with zoomed cells and one line on what each does. Every caption comes
from the spec (headline, tagline, signature services, table hints, chart and gauge titles): nothing is claimed that the file does not do.
Which pages: what the product has — the charts, the dashboard, its most telling sheets, its printables and tools, a floor plan of all its
sheets, and the 15 languages. make_images(spec, demo_recalc_xlsx, meta, outdir, workdir, lang) -> [png]
v1.4 (2026-11-08, the owner: «اجعله ينشئ صور بكل اللغات»): every language gets its own pictures — shot from that language's recalculated
demo, the product's words from its i18n, the fixed phrases from fixed_pic.json (written by Dar's copy team), right-to-left where it reads so."""
import os, sys, json, tempfile, html, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B
from images import render, pick_tables, languages
from common import sheet_names, FIXED, LANGS, tr, RTL
PIC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixed_pic.json'), encoding='utf8'))
SEP = {'zh': '、', 'ar': '، ', 'fa': '، ', 'ur': '، '}
FONT = {'ar': "'Noto Sans Arabic','Noto Naskh Arabic'", 'fa': "'Noto Sans Arabic','Noto Naskh Arabic'", 'ur': "'Noto Naskh Arabic','Noto Sans Arabic'",
        'hi': "'Noto Sans Devanagari'", 'zh': "'Noto Sans CJK SC','Noto Sans SC'"}


def lang_head(lang):
    """what a language adds to every page: its script's font, right-to-left text, and headings that keep the English line count"""
    h = ''
    if lang in FONT: h += f"<style>body,h1,.sub,.pt,.zoom p,.rm,.dim,.foot,.prod{{font-family:{FONT[lang]},'Inter',sans-serif}}</style>"
    if lang == 'ur': h += "<style>h1{font-family:'Noto Nastaliq Urdu','Noto Naskh Arabic',sans-serif;font-size:64px;line-height:1.75;letter-spacing:0}</style>"
    if lang in ('ar', 'fa', 'hi'): h += '<style>h1{line-height:1.2;letter-spacing:0}</style>'   # (2026-11-09: tall scripts overlapped their own lines, e.g. a Latin "CRM" inside an Arabic title)
    if lang in RTL: h += '<style>.l,.sub,.pts,.pt,.foot,.zoom p,.rm,.dim,h1{direction:rtl;text-align:right}.prod{direction:ltr}</style>'
    return h + ("<script>addEventListener('load',()=>document.fonts.ready.then(()=>{document.querySelectorAll('h1').forEach(h=>{"
                "const cs=getComputedStyle(h);let s=parseFloat(cs.fontSize);const lh=parseFloat(cs.lineHeight)/s||1;"
                "const max=(h.closest('.top')?2:4)*s*lh+6;while(h.getBoundingClientRect().height>max&&s>30){s-=2;h.style.fontSize=s+'px'}})}))</script>")
from openpyxl.utils import get_column_letter as CL, column_index_from_string as CI
E = lambda s: html.escape(str(s))


def make_images(spec, demo_xlsx, meta, outdir, workdir=None, lang='en'):
    workdir = workdir or tempfile.mkdtemp(prefix='fxpic-'); os.makedirs(workdir, exist_ok=True); B.SH = workdir
    i18n = (spec.get('i18n') or {}).get(lang) or {}
    T = (lambda s: s) if lang == 'en' else (lambda s: i18n.get(s, s) if isinstance(s, str) else s)  # (a word not translated stays English)
    ph = {**PIC['en'], **{k: v for k, v in (PIC.get(lang) or {}).items() if not k.startswith('_')}}
    F = lambda k, **kw: ph[k].format(**kw)
    J = lambda xs: SEP.get(lang, ', ').join(xs)
    low = lambda x: x.lower() if lang in ('en', 'fr', 'es', 'it', 'pt', 'nl', 'ru', 'id', 'tr') else x
    P, A = spec['colors']['primary'], spec['colors']['accent']; B.theme(P, A)
    fname = re.sub('-+', '-', ''.join(ch if ch.isalnum() else '-' for ch in spec['name'])).strip('-')[:48] + '.xlsx'
    names = [n for _, n in sheet_names(spec, T)]
    def tabs(on): i = names.index(on) if on in names else 0; a = max(0, min(i - 3, len(names) - 9)); return names[a:a + 10]
    sig = spec.get('signature') or []; L = spec['listing']; d = spec['dashboard']
    by_sheet = {}
    for x in sig: by_sheet.setdefault(x['where'].lower(), x); by_sheet.setdefault(T(x['where']).lower(), x)
    jobs = []; tabsel = pick_tables(spec, meta)[:4]
    cs = meta.get('charts_sheet')
    if cs:
        top = cs['top']; jobs += [('charts-top', cs['sheet'], f'A1:V{top + 17}', {'a3': True}), ('filters', cs['sheet'], f'B4:{cs["filters_to"]}4', {})]
        rings = [c for c in meta['charts'] if c['type'] in ('doughnut', 'pie')] or meta['charts'][1:2] or meta['charts'][:1]
        c0 = rings[0]; col = c0['at'][0]; r = c0['at'][1]; end = CL(CI(col) + 9)
        jobs.append(('chart-z', cs['sheet'], f'{col}{r}:{end}{r + 17}', {}))
    kpi_last = 5 + ((len(d['kpis']) + 3) // 4) * 3 - 2
    jobs += [('dash', meta['monthly']['sheet'], meta['dash_range'], {'chart': not cs, 'portrait': True}), ('dashk', meta['monthly']['sheet'], f'A1:M{kpi_last}', {})]
    mo = meta['monthly']; jobs.append(('dash-m', mo['sheet'], f'{CL(mo["cat"])}{mo["header_row"]}:{CL(mo["c2"])}{mo["r2"]}', {}))
    for t in tabsel:
        m = meta['tables'][t['key']]; cols = t['columns']; n = min(max(m['n_demo'], 3), 10)
        keep = [0] + [i for i, c in enumerate(cols) if c['type'] in ('calc', 'list', 'ref') or c.get('required')][:11]
        last = max(keep) + 1; drop = [CL(i + 1) for i in range(last) if i not in keep]
        jobs.append(('t-' + t['key'], m['sheet'], f'A1:{CL(last)}{4 + n}', {'a3': len(keep) > 8, 'drop': drop}))
        z = [0] + [i for i, c in enumerate(cols) if c['type'] == 'calc'][:4]; zl = max(z) + 1
        jobs.append(('z-' + t['key'], m['sheet'], f'A4:{CL(zl)}{4 + min(n, 6)}', {'drop': [CL(i + 1) for i in range(zl) if i not in z]}))
    prints = [('f', f) for f in spec.get('forms', [])][:1] + [('d', x) for x in spec.get('documents', [])][:1]
    for k, f in prints:
        m = meta['forms' if k == 'f' else 'documents'][f['key']]; jobs.append((f'{k}-{f["key"]}', m['sheet'], m['range'], {'portrait': True}))
    for x in spec.get('tools', [])[:2]: jobs.append(('tool-' + x['key'], meta['tools'][x['key']]['sheet'], meta['tools'][x['key']]['range'], {'portrait': True}))
    shots = render(demo_xlsx, meta, jobs, workdir)
    for k, p in shots.items(): shutil.copy(p, os.path.join(workdir, k + '.png'))
    have = set(shots)
    def why(sheet, fallback): x = by_sheet.get(sheet.lower()); return f'<b>{E(T(x["name"]))}</b> — {E(T(x["why"]))}' if x else fallback
    pts = [f'<b>{E(T(x["name"]))}</b>: {E(T(x["why"]))}' for x in sig[:4]] or [E(T(f)) for f in L['features'][:4]]
    NM = E(T(spec['name']))
    pages = []
    hero_win = 'charts-top' if cs else 'dash'
    if cs and tabsel and 't-' + tabsel[0]['key'] in have:     # engine 1.5: the hero is an overview of three different sheets, not a copy of picture 2
        hero_body = B.collage([('charts-top', tabs(cs['sheet']), cs['sheet']), ('t-' + tabsel[0]['key'], tabs(meta['tables'][tabsel[0]['key']]['sheet']), meta['tables'][tabsel[0]['key']]['sheet']),
                               ('dash', tabs(names[1]), names[1])], fname)
    else:
        hero_body = B.stack(hero_win, fname, tabs(cs['sheet'] if cs else names[1]), cs['sheet'] if cs else names[1],
                            [('dashk', F('dash_zoom', title=E(T(d['title']))))] + ([('z-' + tabsel[0]['key'], why(tabsel[0]['sheet'], F('table_zoom', title=E(T(tabsel[0]['title'])))))] if tabsel else []))
    pages.append(('01-hero', B.page(NM, E(T(L.get('headline') or spec['tagline'])), E(T(spec['tagline'])), pts, hero_body,
                  foot=['Excel', 'LibreOffice', F('foot_langs'), F('foot_download')])))   # (2026-11-09, the owner: «احذف التواريخ» — no Excel years on any picture: they were never tested in a real Excel)
    if cs:
        ins = spec['insights']; gt = [T(g['title']) for g in ins.get('gauges', [])]; ct = [T(c['title']) for c in ins['charts']]
        fl = [T(f['label']) for f in ins.get('filters', [])]
        cj = J(low(x[0]) + x[1:] for x in ct[:4])
        sub = F('charts_sub_g', gauges=J(low(x) for x in gt[:3]), charts=cj) if gt else F('charts_sub', charts=cj)
        pages.append((f'{len(pages) + 1:02d}-charts', B.page(NM, E(F('charts_h1')), E(sub),
                      ([E(F('charts_pick', filters=J(low(x) for x in fl)))] if fl else []) + [E(F('charts_nosetup')), E(F('charts_nomacro'))],
                      B.stack('charts-top', fname, tabs(cs['sheet']), cs['sheet'], ([('filters', F('filters_zoom'))] if fl else []) + [('chart-z', F('chart_zoom'))]))))
    pages.append((f'{len(pages) + 1:02d}-dashboard', B.page(NM, E(T(d['title'])), E(F('dash_sub', n=len(d['kpis']), monthly=low(T(d['monthly']['title'])))),
                  [E(T(k['label'])) for k in d['kpis'][:4]], B.stack('dash', fname, tabs(names[1]), names[1], [('dash-m', F('monthly_zoom', monthly=E(T(d['monthly']['title']))))]))))
    for t in tabsel[:3]:
        m = meta['tables'][t['key']]
        if 't-' + t['key'] not in have: continue
        calcs = [T(c['label']) for c in t['columns'] if c['type'] == 'calc'][:3]
        pages.append((f'{len(pages) + 1:02d}-{t["key"]}', B.page_wide(NM, E(T(t['title'])), E(T(t['hint'])), [('t-' + t['key'], fname, tabs(m['sheet']), m['sheet'])],
                      [('z-' + t['key'], why(t['sheet'], F('calc_zoom', calcs=E(J(calcs)))))])))
    pr = [k for k in have if k[:2] in ('f-', 'd-')] + [k for k in have if k.startswith('tool-')]
    if pr:
        main = pr[0]; rest = [(x, F('print_ready')) for x in pr[1:3]]
        sheet = jobs[[j[0] for j in jobs].index(main)][1]
        pages.append((f'{len(pages) + 1:02d}-print', B.page(NM, E(F('print_h1')), E(T(FIXED['form_hint'])),
                      [why(sheet, E(F('print_pt')))], B.stack(main, fname, tabs(sheet), sheet, rest))))
    # the floor plan: every sheet in its room
    tsh = [T(t['sheet']) for t in spec['tables']]
    groups = [(F('room_records'), F('room_records_d'), tsh),
              (F('room_desk'), F('room_desk_d'), [n for n in names[1:3] if n]),
              (F('room_tools'), F('room_tools_d'), [n for n in names[1:-1] if n not in tsh and n not in names[1:3]]),
              (F('room_settings'), F('room_settings_d'), [names[0], names[-1]])]
    groups = [g for g in groups if g[2]]
    hint = {T(t['sheet']): T(t['hint']) for t in spec['tables']}          # (2026-11-09: no hard cut — the card clamps to two lines with an ellipsis)
    for sg in spec.get('signature') or []:                                   # a tool / document / checklist sheet says what it does
        if isinstance(sg, dict) and sg.get('where') and sg.get('why'): hint.setdefault(T(sg['where']), T(sg['why']))
    rooms = []; x0 = 0
    widths = [1090, 1078] if len(groups) > 2 else [2168]
    lay = [(0, 0, 1090, 640), (1090, 0, 1078, 640), (0, 640, 1084, 598), (1084, 640, 1084, 598)]
    for (ttl, desc, sh), (x, y, w, h) in zip(groups, lay):
        rooms.append((x, y, w, h, ttl, desc, [('*' if s.lower() in by_sheet else '') + f'{s}|{hint.get(s, "")}' for s in sh[:9]]))
    pages.append((f'{len(pages) + 1:02d}-inside', B.plan_page(NM, E(F('plan_h1')), E(F('plan_sub')), rooms,
                  E(F('plan_note', n=len(names))))))
    pages.append((f'{len(pages) + 1:02d}-languages', languages(spec, P.lstrip('#'), A.lstrip('#'), h1=F('lang_h1'), sub=F('lang_sub'))))
    return B.shoot(pages, outdir, head=lang_head(lang))


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf8')); demo = sys.argv[2]
    meta = json.load(open(sys.argv[3], encoding='utf8'))
    print(json.dumps(make_images(spec, demo, meta, sys.argv[4]), indent=1))
