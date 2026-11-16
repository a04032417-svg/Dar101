import json, sys
from openpyxl import load_workbook
wb = load_workbook('/home/claude/work/hv/out2/work/v/en-demo.xlsx', data_only=True)
spec = json.load(open('/home/claude/work/hv/hv2.en.json'))
def vals(t):
    ws = wb[t['sheet']]; out = {}
    for o in t['outputs']:
        for row in ws.iter_rows():
            hit = next((c for c in row if isinstance(c.value, str) and (c.value == o['label'] or c.value.startswith(o['label'] + ' ('))), None)
            if hit:
                v = [ws.cell(row=hit.row, column=hit.column + k).value for k in range(1, 7)]
                out[o['label']] = next((x for x in v if x is not None), None); break
    return out
if __name__ == '__main__':
    bad = 0
    for t in spec['tools']:
        v = vals(t)
        print('==', t['sheet'], {k: (round(x, 3) if isinstance(x, float) else x) for k, x in v.items()})
        for o in t['outputs']:
            x = v.get(o['label'])
            if x in (None, '') or (isinstance(x, str) and x.startswith('#')): print('  EMPTY/ERR', o['label'], x); bad += 1
    print('bad', bad)
