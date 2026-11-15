#!/usr/bin/env python3
"""emptybars.py <part.en.json>... : any chart/breakdown grouped ('by'/'axis') by a list/ref column whose demo data leaves values unused (empty bars)."""
import json, sys
def walk(o, out):
    if isinstance(o, dict):
        for k in ('by', 'axis', 'group_by'):
            if isinstance(o.get(k), str) and '.' in o[k]: out.append((o.get('title', '?'), o[k]))
        for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)
for p in sys.argv[1:]:
    d = json.load(open(p)); T = {t['key']: t for t in d['tables']}; L = {l['key']: [v['key'] for v in l['values']] for l in d['lists']}
    found = []; walk({k: v for k, v in d.items() if k not in ('tables', 'lists', 'i18n')}, found); n = 0
    for title, ax in found:
        tk, ck = ax.split('.', 1); t = T.get(tk)
        if not t: continue
        col = next((c for c in t['columns'] if c['key'] == ck), None)
        if not col: continue
        used = {r.get(ck) for r in t.get('demo', []) if isinstance(r, dict)}
        if col['type'] == 'list': vals = L.get(col.get('list'), [])
        elif col['type'] == 'ref' and '.' in str(col.get('ref', '')):
            rt, rc = col['ref'].split('.', 1); vals = [r.get(rc) for r in T.get(rt, {}).get('demo', [])][:12]
        else: continue
        miss = [v for v in vals if v not in used]; n += 1
        if miss: print(p.split('/')[-1], '|', title, '|', ax, '| unused', f'{len(miss)}/{len(vals)}:', miss[:5])
    print(p.split('/')[-1], 'checked', n)
