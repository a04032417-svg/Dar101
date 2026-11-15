import re, sys
t = open('/home/claude/work/pg/BLUEPRINT.md').read()
want = dict(Tables=20, Tools=18, Forms=12, Documents=12, Checklists=12, Messages=34, KPIs=30, Charts=22, Gauges=6)
parts = re.split(r'^## Part ', t, flags=re.M)[1:]
ok = True
for p in parts:
    title = p.split('\n')[0]
    got = {}
    for m in re.finditer(r'\*\*(Tables|Tools|Forms|Documents|Checklists|Messages|KPIs|Charts|Gauges) \((\d+)\):\*\* (.*)', p):
        depth = 0; items = []; cur = ''
        for ch in m.group(3):
            if ch in '([': depth += 1
            if ch in ')]': depth -= 1
            if ch == ';' and depth == 0: items.append(cur); cur = ''
            else: cur += ch
        if cur.strip(' .'): items.append(cur)
        got[m.group(1)] = (int(m.group(2)), len(items))
    bad = [k for k, v in want.items() if got.get(k) != (v, v)]
    print(title[:60], 'OK' if not bad else 'BAD %s' % {k: got.get(k) for k in bad})
    ok = ok and not bad
print('parts', len(parts), 'ALL OK' if ok and len(parts) else 'PROBLEMS')
