#!/usr/bin/env python3
"""Suite packing (2026-11-11, the owner: «حزمة ملفات … مئات الصفحات … صور العرض شاملة لكل الصفحات وفيها شروحات … بكل اللغات»).
usage: suite_pack.py <suite.json> <parts_dir> <out_dir>
  suite.json  = {"key", "slug", "name": {lang: text}, "headline": {lang: text}, "parts": ["p1", …], "stats_note": {lang: text}}
  parts_dir/<part>/ = what suite-build pushed for each part: result.json, the part's ZIP, images/ (en) and images/<lang>/
  spec of each part: build/<suite>/<part>.json (for sheet names, hints and translations)
Writes out_dir/<Suite>-<n>-workbooks-15-languages.zip (one folder per part) and, for every language, out_dir/images/<lang>/:
  00-cover.png (the suite: its workbooks, page counts, a picture of each), 01-inside-<k>.png (every page of every workbook, named in that
  language, with what each workbook is for), then the parts' own pictures in the order Whop/Etsy show them: gallery.json lists 8 per language."""
import sys, os, json, zipfile, re, html, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ENGINE = os.path.join(os.path.dirname(HERE), 'engine'); sys.path.insert(0, ENGINE)
import board as B
from common import LANGS, RTL, FIXED, sheet_names
from pictures import lang_head
E = lambda s: html.escape(str(s))


def T_of(spec, lang):
    m = (spec.get('i18n') or {}).get(lang) or {}
    return (lambda s: s) if lang == 'en' else (lambda s: m.get(s, s))


def main(suite_json, parts_dir, out):
    S = json.load(open(suite_json, encoding='utf8')); os.makedirs(out, exist_ok=True)
    root = os.path.dirname(os.path.abspath(suite_json))
    parts = []
    for p in S['parts']:
        res = json.load(open(os.path.join(parts_dir, p, 'result.json'), encoding='utf8'))
        if not res.get('ok'): raise SystemExit(f'part {p} did not build: {res.get("stage")} {res.get("errors", [])[:3]}')
        spec = json.load(open(os.path.join(root, p + '.json'), encoding='utf8'))
        z = [f for f in os.listdir(os.path.join(parts_dir, p)) if f.endswith('.zip')][0]
        parts.append((p, spec, os.path.join(parts_dir, p, z), res))
    # 1. one ZIP, a folder per workbook
    zname = re.sub(r'[^A-Za-z0-9]+', '-', S['name']['en']).strip('-') + f'-{len(parts)}-workbooks-15-languages.zip'
    zp = os.path.join(out, zname)
    readme = [S['name']['en'], S['headline']['en'], '', 'WORKBOOKS']
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for i, (p, spec, z, res) in enumerate(parts, 1):
            folder = f'{i:02d} - ' + re.sub(r'[\\/:*?"<>|]+', '-', spec['name'])
            readme.append(f'  {folder}: {spec["tagline"]}')
            with zipfile.ZipFile(z) as zi:
                for n in zi.namelist():
                    if n.endswith('/'): continue
                    zo.writestr(folder + '/' + n.split('/')[-1], zi.read(n))
        readme += ['', 'Each folder holds the workbook in 15 languages and an English copy full of sample data.',
                   'Standard .xlsx files for Microsoft Excel and LibreOffice Calc. No macros. Personal use licence for one business.']
        zo.writestr('README.txt', '\r\n'.join(readme) + '\r\n')
    # 2. pictures, every language
    B.theme(parts[0][1]['colors']['primary'], parts[0][1]['colors']['accent'])
    gallery = {}
    for lang in LANGS:
        work = os.path.join(out, 'work', lang); os.makedirs(work, exist_ok=True); B.SH = work
        names, pages_total = [], 0
        for i, (p, spec, z, res) in enumerate(parts, 1):
            src = os.path.join(parts_dir, p, 'images', '' if lang == 'en' else lang)
            pic = next((os.path.join(src, f) for f in sorted(os.listdir(src)) if re.match(r'0[23]-', f)), None) if os.path.isdir(src) else None
            if pic: shutil.copy(pic, os.path.join(work, f'p{i}.png'))
            T = T_of(spec, lang); sh = sheet_names(spec, T); pages_total += len(sh)
            names.append((T(spec['name']), T(spec['tagline']), [n for _, n in sh], bool(pic)))
        title, head = S['name'].get(lang, S['name']['en']), S['headline'].get(lang, S['headline']['en'])
        note = S['stats_note'].get(lang, S['stats_note']['en']).format(files=len(parts), pages=pages_total)
        rtl = lang in RTL
        # 2026-11-13 (the owner): ONE big picture, like the single-workbook covers — a grid of six small windows is unreadable in store thumbnails
        nm, tg, shs, has = names[0]
        im = f'<img src="{B.img("p1")}">' if has else ''
        cards = (f'<div class="win" style="left:880px;top:150px;width:1420px;height:1440px"><div class="bar"><s></s><s></s><s></s><em>01 · {E(nm)}</em></div>'
                 f'<div class="sheet" style="padding:12px">{im}</div><div class="tabs" style="flex-basis:70px;font-size:26px;white-space:normal"><span class="on" style="white-space:normal;line-height:1.2">{E(tg)}</span></div></div>')
        pts = [f'<b>{E(nm)}</b> — {len(shs)}' for nm, tg, shs, h in names]
        cover = B.page(E(note), E(title), E(head), pts, cards)
        pages = [('00-cover', cover)]
        # every page of every workbook, three workbooks per picture
        for k in range(0, len(names), 3):
            body = ''
            for j, (nm, tg, shs, h) in enumerate(names[k:k + 3]):
                y = 110 + j * 570
                chips = ''.join(f'<span style="display:inline-block;margin:0 8px 8px 0;padding:3px 10px;border-radius:7px;background:#fff;border:1px solid #D5DDE6;font-size:16px;line-height:1.35">{E(s)}</span>' for s in shs)
                body += (f'<div style="position:absolute;left:880px;top:{y}px;width:1420px;height:540px;overflow:hidden;{"direction:rtl;text-align:right;" if rtl else ""}">'
                         f'<div style="font-size:36px;font-weight:800;color:#13233A">{k + j + 1:02d} · {E(nm)} <span style="font-weight:500;color:#5A6B80;font-size:26px">({len(shs)})</span></div>'
                         f'<div style="font-size:22px;color:#3E5068;margin:6px 0 12px">{E(tg)}</div><div>{chips}</div></div>')
            pages.append((f'01-inside-{k // 3 + 1}', B.page(E(title), E(S['inside_h1'].get(lang, S['inside_h1']['en'])), E(note), [], body)))
        imgs = B.shoot(pages, os.path.join(out, 'images', lang), lang_head(lang))
        # gallery: cover, inside, then each part's hero picture, 8 at most (Whop's limit)
        g = [os.path.relpath(x, out) for x in imgs]
        for i, (p, spec, z, res) in enumerate(parts, 1):
            src = os.path.join(parts_dir, p, 'images', '' if lang == 'en' else lang)
            if os.path.isdir(src):
                hero = next((f for f in sorted(os.listdir(src)) if f.startswith('01-')), None)
                if hero:
                    dst = os.path.join(out, 'images', lang, f'1{i}-part{i}-{hero}'); shutil.copy(os.path.join(src, hero), dst); g.append(os.path.relpath(dst, out))
        gallery[lang] = g[:2] + g[len(imgs):][:6]
        shutil.rmtree(work, ignore_errors=True)
    json.dump({'zip': zname, 'gallery': gallery}, open(os.path.join(out, 'gallery.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'ok': True, 'zip': zname, 'mb': round(os.path.getsize(zp) / 1e6, 1), 'languages': len(gallery)}))


if __name__ == '__main__': main(*sys.argv[1:4])
