import json, sys
from openpyxl import load_workbook
wb = load_workbook('/home/claude/work/hv/out5/work/v/en-demo.xlsx', data_only=True)
spec = json.load(open('/home/claude/work/hv/hv5.en.json'))
def find(ws, label):
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and (c.value == label or c.value.startswith(label + ' (')): return c
def vals(t):
    ws = wb[t['sheet']]; out = {}
    for o in t['outputs']:
        hit = find(ws, o['label'])
        if hit:
            v = [ws.cell(row=hit.row, column=hit.column + k).value for k in range(1, 7)]
            out[o['label']] = next((x for x in v if x is not None), None)
    return out
if __name__ == '__main__':
    bad = 0
    for t in spec['tools']:
        v = vals(t); print('==', t['sheet'])
        for k, x in v.items(): print('   ', k, '=', round(x, 3) if isinstance(x, float) else x)
        for o in t['outputs']:
            x = v.get(o['label'])
            if x in (None, '') or (isinstance(x, str) and x.startswith('#')): print('  EMPTY/ERR', o['label'], x); bad += 1
    print('bad', bad)
