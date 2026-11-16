from openpyxl import load_workbook
import datetime as dt
wb=load_workbook('out6/work/v/en-demo.xlsx',data_only=True)
def tab(n):
    rows=list(wb[n].iter_rows(values_only=True))
    h=max(range(min(15,len(rows))),key=lambda i:sum(isinstance(x,str) for x in rows[i]))
    hd=list(rows[h]); out=[dict(zip(hd,r)) for r in rows[h+1:] if r[0] not in (None,'')]
    return hd,out
if __name__=='__main__':
    for n in ['Customer Sites','Agreements','Renewals','Tune-up Visits','Agreement Plans','Campaign List','Aged Equipment','Member Revenue','Agreement Profit']:
        h,r=tab(n); print(n,len(r),[x for x in h if x])
