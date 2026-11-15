import sys, openpyxl, datetime
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
bad = 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if isinstance(v, datetime.datetime) and v.year < 1901:
                bad += 1
                if bad <= 10: print(ws.title, c.coordinate, v)
print(bad)
