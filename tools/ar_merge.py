#!/usr/bin/env python3
"""Arabic edition: check <x>/ar/<x>N.ar.json ({"<English>": "<Arabic>"}) and merge it into <x>/<x>N.en.json i18n.ar.
usage: python3 tools/ar_merge.py <x> <N> [--check]     (run from /home/claude/work)
Checks every string of <x>/ar/<x>N.todo.json: present, not empty, placeholders {..} and document tokens kept exactly,
no Latin words left (except WhatsApp, Excel, Google Sheets, LibreOffice, PDF, ID codes...), sheet names <= 31 chars without
[ ] : * ? / \\ and unique, drop-down labels unique per list and not starting with = < > + - @ nor holding * ? ~, never the word
for "compatible". Then merges (unless --check) and runs the engine's validate with FX_EDITION=en FX_ADD_LANGS=ar.
Prints 'errors 0' when the part is clean; otherwise one line per problem (fix the .ar.json and run again)."""
import os, sys, re, json
os.environ['FX_EDITION'] = 'en'; os.environ['FX_ADD_LANGS'] = 'ar'
sys.path.insert(0, '/home/claude/d101/engine')
from common import list_by_key, YESNO, STEPSTAT, sheet_names
from validate import validate

ANY_PH = re.compile(r'\{[^{}]*\}')
KEEP = {'whatsapp', 'excel', 'google', 'sheets', 'drive', 'libreoffice', 'calc', 'pdf', 'id', 'ok', 'xlsx', 'iban', 'vat', 'gps', 'sms', 'url', 'qr', 'kpi', 'ein', 'faq'}
LABEL_BAD = re.compile(r'^[=<>+@-]|[*?~]')


def main():
    x, n = sys.argv[1], sys.argv[2]; only_check = '--check' in sys.argv
    sp_path = f'{x}/{x}{n}.en.json'; spec = json.load(open(sp_path, encoding='utf8'))
    todo = json.load(open(f'{x}/ar/{x}{n}.todo.json', encoding='utf8'))
    import glob
    ar = json.load(open(f'{x}/ar/{x}{n}.ar.json', encoding='utf8')) if os.path.exists(f'{x}/ar/{x}{n}.ar.json') else {}
    for f in sorted(glob.glob(f'{x}/ar/{x}{n}.add*.json')):
        try: ar.update(json.load(open(f, encoding='utf8')))
        except Exception as e: print(f'bad JSON {f}: {e}'); sys.exit(1)
    errs = []
    for t in todo:
        en = t['en']; v = ar.get(en)
        if not isinstance(v, str) or not v.strip(): errs.append(f'missing: {en[:70]!r} ({t["where"]})'); continue
        # (the engine's own hint 'words in {braces}' is plain text, not a placeholder)
        if not t['where'].startswith('engine/') and sorted(ANY_PH.findall(en)) != sorted(ANY_PH.findall(v)): errs.append(f'placeholders differ: {en[:50]!r} needs {sorted(ANY_PH.findall(en))}, got {sorted(ANY_PH.findall(v))}')
        if v.lstrip().startswith('='): errs.append(f'starts with "=": {v[:40]!r}')
        if t.get('max') and len(v) > t['max']: errs.append(f'too long ({len(v)} > {t["max"]}): {v!r} ({t["where"]})')
        if t['kind'] == 'sheet' and re.search(r'[\[\]:*?/\\]', v): errs.append(f'sheet name with [ ] : * ? / \\: {v!r}')
        lat = [w for w in re.findall(r'[A-Za-z][A-Za-z]+', ANY_PH.sub('', v)) if w.lower() not in KEEP and not w.isupper()]
        if lat: errs.append(f'Latin words left {lat[:4]}: {v[:60]!r}')
        if re.search(r'متوافق|compat', v, re.I): errs.append(f'the word for "compatible": {v[:60]!r}')
    extra = [k for k in ar if k not in {t['en'] for t in todo} and k not in ((spec.get('i18n') or {}).get('ar') or {})]
    if extra: print(f'note: {len(extra)} extra keys ignored (not printed by this part)')
    merged = {**((spec.get('i18n') or {}).get('ar') or {}), **{t['en']: ar[t['en']] for t in todo if isinstance(ar.get(t['en']), str) and ar[t['en']].strip()}}
    # sheet names and list labels of the whole Arabic workbook
    if not [e for e in errs if e.startswith('missing')]:
        T = lambda s: merged.get(s, s)
        low = {}
        for sid, nm in sheet_names(spec, T):
            if len(nm) > 31: errs.append(f'sheet {sid} name {nm!r}: {len(nm)} > 31')
            if nm.lower() in low: errs.append(f'two sheets named {nm!r}: {low[nm.lower()]} and {sid}')
            low[nm.lower()] = sid
        for l in spec['lists'] + [list_by_key(spec, YESNO)] + ([list_by_key(spec, STEPSTAT)] if spec.get('checklists') else []):
            seen = {}
            for val in l['values']:
                lab = T(val['label'])
                if LABEL_BAD.search(lab): errs.append(f'list {l["key"]}: label {lab!r} starts with = < > + - @ or holds * ? ~')
                if lab.lower() in seen: errs.append(f'list {l["key"]}: {seen[lab.lower()]} and {val["key"]} both {lab!r}')
                seen[lab.lower()] = val['key']
    # a rank tie-break that compares translated drop-down labels ({range:t.c}<{col:c} on a list column) orders rows differently
    # in Arabic, and the build then fails "ar-demo differs from the English demo": compare a language-independent column instead
    types = {(t['key'], c['key']): c['type'] for t in spec['tables'] for c in t['columns']}
    for t in spec['tables']:
        for c in t['columns']:
            f = c.get('formula') or ''
            for m in re.finditer(r'\{range:(\w+)\.(\w+)\}\s*,\s*"[<>]=?"\s*&\s*\{(?:col|in):(\w+)\}', f):   # COUNTIFS(range,"<"&label)
                if types.get((m.group(1), m.group(2))) == 'list':
                    errs.append(f'order by translated labels in {t["key"]}.{c["key"]}: {m.group(0)} -> order by a position column (PIPELINE.md section 6, step 4b)')
            for m in re.finditer(r'\{range:(\w+)\.(\w+)\}\s*[<>]=?\s*\{col:(\w+)\}', f):
                if types.get((m.group(1), m.group(2))) == 'list':
                    errs.append(f'tie-break on translated labels in {t["key"]}.{c["key"]}: {m.group(0)} -> compare an ID column or a MATCH position (PIPELINE.md section 6, step 4b)')
    if not errs and not only_check:
        spec.setdefault('i18n', {})['ar'] = merged
        json.dump(spec, open(sp_path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
        errs += [f'validate: {e}' for e in validate(json.load(open(sp_path, encoding='utf8')))]
    for e in errs[:80]: print(e)
    print('errors', len(errs))


main()
