import json, sys
from openpyxl import load_workbook
wb = load_workbook('/home/claude/work/hv/out6/work/v/en-demo.xlsx', data_only=True)
spec = json.load(open('/home/claude/work/hv/hv6.en.json'))
def vals(t):
    ws = wb[t['sheet']]; out = {}
    for o in t['outputs']:
        for row in ws.iter_rows():
            hit = next((c for c in row if isinstance(c.value, str) and (c.value == o['label'] or c.value.startswith(o['label'] + ' ('))), None)
            if hit:
                v = [ws.cell(row=hit.row, column=hit.column + k).value for k in range(1, 7)]
                out[o['label']] = next((x for x in v if x is not None), None); break
    return out
def kpis():
    ws = wb[spec['dashboard']['title']] if spec['dashboard']['title'] in wb.sheetnames else None
    out = {}
    if ws is None: return out
    for k in spec['dashboard']['kpis']:
        for row in ws.iter_rows():
            hit = next((c for c in row if c.value == k['label']), None)
            if hit:
                v = [ws.cell(row=hit.row + d, column=hit.column + e).value for d, e in ((1, 0), (0, 1), (0, 2), (1, 1))]
                out[k['label']] = next((x for x in v if isinstance(x, (int, float))), v); break
    return out
if __name__ == '__main__':
    if 'k' in sys.argv:
        for k, v in kpis().items(): print(k, '=', v)
    else:
        for t in spec['tools']:
            if len(sys.argv) > 1 and t['key'] not in sys.argv[1:]: continue
            v = vals(t); print('==', t['sheet'])
            for k, x in v.items(): print('   ', k, '=', round(x, 3) if isinstance(x, float) else x)
