#!/usr/bin/env python3
"""Arabic edition (owner 2026-11-21 «العربية والإنجليزية»): the English strings of one part that still need Arabic.
usage: python3 tools/ar_todo.py <x> <N>      (run from /home/claude/work; engine = /home/claude/d101/engine)
writes <x>/ar/<x>N.todo.json = [{"en","where","kind","max"}] for every string the Arabic workbook and pictures print that
<x>/<x>N.en.json i18n.ar does not have yet, and prints the count. kind: sheet (<= 31 chars, Excel sheet name), list
(drop-down value), message (WhatsApp text), document (letter/contract paragraph), title, label, sentence."""
import os, sys, json
os.environ['FX_EDITION'] = 'en'; os.environ['FX_ADD_LANGS'] = 'ar'
sys.path.insert(0, '/home/claude/d101/engine')
from common import texts, pic_texts

SHEET_FIX = ('engine/fixed_en.json:sheet_start', 'engine/fixed_en.json:sheet_lists', 'engine/fixed_en.json:sheet_messages', 'engine/fixed_en.json:sheet_charts')


def kind(where):
    if where in SHEET_FIX or where == 'dashboard.title' or where.endswith('.sheet') or (where.startswith('checklists[') and where.endswith('.title')): return 'sheet', 31
    if where.startswith('lists[') and '.values[' in where: return 'list', 40
    if where.startswith('messages[') and where.endswith('.text'): return 'message', None
    if where.startswith('documents[') and ('.paragraphs[' in where or '.sign[' in where): return 'document', None
    if where.endswith('.title') or where in ('name', 'tagline', 'listing.headline'): return 'title', None
    if where.startswith(('guide[', 'listing.features', 'engine/common.py:EN_TEXT.start_lines')) or where.endswith(('.hint', '.why', '.note')): return 'sentence', None
    return 'label', None


def todo(x, n):
    spec = json.load(open(f'{x}/{x}{n}.en.json', encoding='utf8'))
    have = ((spec.get('i18n') or {}).get('ar') or {})
    need = {**pic_texts(spec), **texts(spec)}          # texts() wins the "where" (its strings fail the build when missing)
    out = []
    for en, where in need.items():
        if isinstance(have.get(en), str) and have[en].strip(): continue
        k, mx = kind(where)
        out.append({'en': en, 'where': where, 'kind': k, **({'max': mx} if mx else {})})
    return out


def known(x, n):
    """Arabic already approved in this suite: the other parts' i18n.ar and their .ar.json/.add*.json files (same English -> same Arabic)."""
    import glob
    k = {}
    for f in sorted(glob.glob(f'{x}/{x}[1-8].en.json')):
        if f != f'{x}/{x}{n}.en.json': k.update(((json.load(open(f, encoding='utf8')).get('i18n') or {}).get('ar') or {}))
    for f in sorted(glob.glob(f'{x}/ar/{x}[1-8].ar.json')) + sorted(glob.glob(f'{x}/ar/{x}[1-8].add*.json')):
        if not os.path.basename(f).startswith(f'{x}{n}.'):
            try: k.update(json.load(open(f, encoding='utf8')))
            except Exception: pass
    k.update(json.load(open('tools/ar_common.json', encoding='utf8')))   # the engine's own words + Start-sheet instructions, same in every suite
    return {a: b for a, b in k.items() if isinstance(b, str) and b.strip()}


if __name__ == '__main__':
    x, n = sys.argv[1], sys.argv[2]
    os.makedirs(f'{x}/ar', exist_ok=True)
    t = todo(x, n)
    json.dump(t, open(f'{x}/ar/{x}{n}.todo.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    pre_p = f'{x}/ar/{x}{n}.ar.json'
    pre = json.load(open(pre_p, encoding='utf8')) if os.path.exists(pre_p) else {}
    K = known(x, n)
    for i in t:
        if i['en'] not in pre and i['en'] in K: pre[i['en']] = K[i['en']]
    json.dump(pre, open(pre_p, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    import glob
    add = {}
    for f in sorted(glob.glob(f'{x}/ar/{x}{n}.add*.json')):
        try: add.update(json.load(open(f, encoding='utf8')))
        except Exception as e: print('bad file', f, e)
    new = [i for i in t if i['en'] not in pre and i['en'] not in add]
    json.dump(new, open(f'{x}/ar/{x}{n}.new.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(f'{x}{n}: {len(t)} strings, {len(t) - len(new)} already in Arabic (other parts / earlier files), {len(new)} to translate '
          f'({sum(len(i["en"]) for i in new)} characters) -> {x}/ar/{x}{n}.new.json')
