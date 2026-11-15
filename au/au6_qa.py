import sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1], data_only=True)
names = sys.argv[2:] or wb.sheetnames
ERR = ('#VALUE!', '#DIV/0!', '#N/A', '#REF!', '#NAME?', '#NUM!')
for n in names:
    ws = wb[n]; print('=====', n)
    for r in ws.iter_rows(max_row=70):
        v = [(c.coordinate, c.value if not isinstance(c.value, float) else round(c.value, 4)) for c in r if c.value not in (None, '')]
        if v: print(v)
