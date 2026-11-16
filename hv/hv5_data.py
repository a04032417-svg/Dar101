"""HVAC suite part 5: demo rows from hv_core (row-level tables show recent samples, monthly tables are built from the full generators)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv5_lists import *
import collections, datetime as _dt

TD = TODAY
ST = story()
PH = {t['name']: t['phone'] for t in team}
ROLEPH = {t['role']: t['phone'] for t in team}
OWNER_PHONE, OFFICE_PHONE = PH[OWNER], PH[OFFICE_MANAGER]
PARTS_PHONE, SUP_PHONE, ACCT_PHONE, INS_PHONE = ROLEPH['Parts counter'], ROLEPH['Equipment supplier'], ROLEPH['Accountant'], ROLEPH['Insurance agent']
_sub = [t for t in team if t['role'] == 'Subcontractor']
ELEC_PHONE, SHEET_PHONE = _sub[0]['phone'], _sub[1]['phone']
CREW_PHONES = [PH[n] for n in TECH_NAMES]
VAN_PHONES = [PH[v['technician']] for v in vans]
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d2(x): return round(x, 2)

PU_ALL = parts_used_rows(); JOBS_ALL = job_rows(); SC_ALL = stock_count_rows(); VS_ALL = van_stock_rows(); RS_ALL = restock_rows()
COUNT_DATES = sorted({x['date'] for x in SC_ALL})
LATEST = COUNT_DATES[-1]
_pu365 = [x for x in PU_ALL if ago(365) <= x['date'] <= iso(TD)]

# ---- van stock
def van_stock_d():
    cnt = {}
    for x in SC_ALL: cnt[(x['van'], x['part_id'])] = x['date']
    out = []
    for x in VS_ALL:
        lc = cnt.get((x['van'], x['part_id']), COUNT_DATES[-2] if x['stock_id'] > 'ST-0090' else COUNT_DATES[-3])
        out.append(dict(stock_id=x['stock_id'], van=key('van', x['van']), part_id=x['part_id'], part=x['part'], category=key('partcat', x['category']), van_min=x['van_min'], van_max=x['van_max'],
                        on_hand=x['on_hand'], unit_cost=x['unit_cost'], last_counted=lc, supplier=key('supplier', x['supplier'])))
    # a complete record first (forms and documents open on it)
    i = next(i for i, r in enumerate(out) if r['van'] == 'van_1' and r['on_hand'] >= r['van_min'])
    out.insert(0, out.pop(i))
    return out
N_BELOW = sum(1 for x in VS_ALL if x['on_hand'] < x['van_min'])

def stock_counts_d():
    out = [dict(count_id=x['count_id'], date=x['date'], van=key('van', x['van']), part_id=x['part_id'], part=x['part'], expected=x['expected'], counted=x['counted'], unit_cost=x['unit_cost']) for x in SC_ALL]
    i = next(i for i, r in enumerate(out) if r['counted'] < r['expected'] and r['date'] == LATEST and r['van'] == 'van_4')
    out.insert(0, out.pop(i))
    return out

def restocks_d():
    rows = RS_ALL[-700:]
    out = [dict(restock_id=x['restock_id'], date=x['date'], week=x['week'], van=key('van', x['van']), part_id=x['part_id'], part=x['part'], qty=x['qty'], unit_cost=x['unit_cost'], cost=x['cost'], supplier=key('supplier', x['supplier'])) for x in rows]
    out.insert(0, out.pop(len(out) - 40))
    return out

def parts_used_d():
    rows = [x for x in PU_ALL if x['date'] >= ago(45)]
    jt = {j['job_id']: j['job_type'] for j in JOBS_ALL}
    out = [dict(use_id=x['use_id'], date=x['date'], month=x['month'], job_id=x['job_id'], job_type=key('jobtype', jt.get(x['job_id'], 'Heating repair')), van=key('van', x['van']), technician=key('tech', x['technician']), part_id=x['part_id'], part=x['part'],
                category=key('partcat', x['category']), qty=x['qty'], unit_cost=x['unit_cost'], cost=x['cost'], from_van=x['from_van'], billed=x['billed']) for x in rows]
    i = next(i for i, r in enumerate(out) if r['from_van'] and r['billed'] and r['date'] < iso(TD))
    out.insert(0, out.pop(i))
    return out

_UP = {}
for _x in _pu365:
    a = _UP.setdefault(_x['part_id'], [0, set()]); a[0] += _x['qty']; a[1].add(_x['job_id'])
def parts_d():
    old = TD - _dt.timedelta(days=365)
    return [dict(part_id=p['part_id'], part=p['part'], category=key('partcat', p['category']), unit_cost=p['unit_cost'], cost_year_ago=cost_at(p['part'], old), markup=p['markup'], van_min=p['van_min'], van_max=p['van_max'],
                 supplier=key('supplier', p['supplier']), year_qty=_UP.get(p['part_id'], [0, set()])[0], year_jobs=len(_UP.get(p['part_id'], [0, set()])[1])) for p in parts]

def price_changes_d():
    out = []
    for x in price_change_rows():
        cat = PART[x['part']]['category']
        out.append(dict(change_id=x['change_id'], date=x['date'], part_id=x['part_id'], part=x['part'], supplier=key('supplier', x['supplier']), category=key('pccat', cat), old_cost=x['old_cost'], new_cost=x['new_cost']))
    out.sort(key=lambda r: r['date'])
    i = next(i for i, r in enumerate(out) if r['part_id'] == 'PT-0064')
    out.insert(0, out.pop(i))
    return out

_JY = collections.Counter(j['task_id'] for j in JOBS_ALL if j['status'] != 'Cancelled' and ago(365) <= j['date'] <= iso(TD))
def price_book_d():
    old = TD - _dt.timedelta(days=365); out = []
    for p in price_book:
        pl = PB[p['pb_id']]['_parts']
        before = round(sum(cost_at(n, old) * q for n, q in pl), 2)
        out.append(dict(pb_id=p['pb_id'], job_type=key('jobtype', p['job_type']), task=p['task'], parts_cost=p['parts_cost'], parts_before=before, other_cost=d2(p['cost'] - p['parts_cost']), flat_price=p['flat_price'],
                        target_margin=p['target_margin'], jobs_year=_JY.get(p['pb_id'], 0)))
    i = next(i for i, r in enumerate(out) if r['pb_id'] == ST['margin_pb_id'])
    out.insert(0, out.pop(i))
    return out

def estimates_open_d():
    old_by_type = {}
    ests = [e for e in estimate_rows() if e['outcome'] == 'Open']
    out = []
    for e in ests:
        lines = PB_BY_TYPE.get(e['job_type'], [])
        if not lines: continue
        price = e['better_price'] or e['good_price'] or e['best_price']
        ln = min(lines, key=lambda p: abs(p['flat_price'] - price))
        pn = sum(cost_at(n, TD - _dt.timedelta(days=200)) * q for n, q in ln['_parts'])
        out.append(dict(estimate_id=e['estimate_id'], date=e['date'], job_type=key('jobtype', e['job_type']), value=price, parts_priced=d2(pn), parts_now=ln['parts_cost'], other_cost=d2(ln['cost'] - ln['parts_cost'])))
    extra = [('Air conditioner replacement', 4), ('Heat pump install', 9), ('Repipe', 13), ('Air conditioner replacement', 16), ('Furnace replacement', 6)]
    for i, (jt, dd) in enumerate(extra):
        lines = PB_BY_TYPE[jt]; ln = lines[min(1, len(lines) - 1)]
        pn = sum(cost_at(n, TD - _dt.timedelta(days=200)) * q for n, q in ln['_parts'])
        out.append(dict(estimate_id='ES-%05d' % (1108 + i), date=ago(dd), job_type=key('jobtype', jt), value=ln['flat_price'], parts_priced=d2(pn), parts_now=ln['parts_cost'], other_cost=d2(ln['cost'] - ln['parts_cost'])))
    out.sort(key=lambda r: r['date'])
    return out

def purchases_d():
    rows = purchase_rows()[-300:]
    out = [nb(dict(po_id=x['po_id'], date=x['date'], supplier=key('payee', x['supplier']), kind=key('pokind', x['kind']), job_id=x['job_id'], amount=x['amount'], due_date=x['due_date'], paid_on=x['paid_on'], status=key('postatus', x['status']))) for x in rows]
    i = next(i for i, r in enumerate(out) if r.get('paid_on') and r.get('job_id') and r['supplier'] == key('payee', 'Your equipment supplier'))
    out.insert(0, out.pop(i))
    return out

def vehicle_costs_d():
    out = [dict(vc_id=x['vc_id'], month=x['month'], van=key('van', x['van']), fuel=x['fuel'], repairs=x['repairs'], tyres=x['tyres'], lease=x['lease'], insurance=x['insurance'], working_days=x['working_days'], jobs=x['jobs']) for x in vehicle_cost_rows()]
    i = next(i for i, r in enumerate(out) if r['repairs'] > 0 and r['tyres'] > 0 and r['jobs'] > 0)
    out.insert(0, out.pop(i))
    return out

def vans_d(): return [dict(van=v['van'], technician=v['technician'], lease_monthly=v['lease_monthly']) for v in vans]
def techs_d(): return [dict(technician=t['name'], trade=t['trade'], van=t['van']) for t in techs[:6]]

def tools_d():
    out = [dict(tool_id=x['tool_id'], date=x['date'], item=x['item'], description=x['description'], technician=key('crew', x['technician']), cost=x['cost'], life_years=x['life_years'], replace_year=key('ryear', str(x['replace_year']))) for x in TOOLS_ADJ]
    i = next(i for i, r in enumerate(out) if r['life_years'] >= 6 and r['date'] > ago(300))
    out.insert(0, out.pop(i))
    return out

def restock_list_d(): return [dict(rank=k) for k in range(1, N_BELOW + 1)]
def supplier_runs_d():
    out, n = [], 1
    for s in SUPPLIERS:
        for v in VAN_NAMES:
            out.append(dict(run_id='SR-%02d' % n, supplier=key('supplier', s), van=key('van', v))); n += 1
    return out
_SC = {}
def shrink_van_d():
    last6, early = COUNT_DATES[-6:], COUNT_DATES[:-6]
    out, n = [], 1
    for per, fr, to, cn in (('Last 6 counts', last6[0], last6[-1], len(last6)), ('Earlier counts', early[0], early[-1], len(early))):
        for v in VAN_NAMES:
            out.append(dict(row_id='SV-%02d' % n, van=key('van', v), period=key('speriod', per), from_date=fr, to_date=to, counts=cn)); n += 1
    return out
N_UNBILLED = sum(1 for x in parts_used_d() if x['from_van'] and not x['billed'])
def unbilled_d(): return [dict(rank=k) for k in range(1, N_UNBILLED + 1)]
def vehicle_van_d():
    nxt = collections.Counter(j['van'] for j in JOBS_ALL if j['status'] == 'Scheduled' and iso(TD) < j['date'] <= ahead(7))
    dues = [11, 24, 52, 83, 38, 118]
    out, n = [], 1
    for per in CPERIOD:
        for v, dd in zip(VAN_NAMES, dues):
            out.append(dict(row_id='VV-%02d' % n, van=key('van', v), period=key('cperiod', per), service_due=ahead(dd), jobs_next_week=nxt.get(v, 0))); n += 1
    return out

def stock_month_d():
    months = months14(); seas = {s['month_no']: s['season'] for s in seasons}
    val = collections.defaultdict(float)
    for x in SC_ALL: val[x['date']] += x['counted'] * x['unit_cost']
    def stock_at(m):
        end = iso(add_months(m, 1)) if m < month_start(0) else iso(TD + _dt.timedelta(days=1))
        ds = [d for d in COUNT_DATES if d < end]
        v = val[ds[-1]] if ds else val[COUNT_DATES[0]] * (0.96 + 0.01 * (m.month % 4))
        return v / val[LATEST] * sum(x['value'] for x in VS_ALL)
    rs = collections.defaultdict(float); pc = collections.defaultdict(float); ub = collections.defaultdict(float); rev = collections.defaultdict(float); jb = collections.Counter()
    for x in RS_ALL: rs[x['date'][:7]] += x['cost']
    for x in PU_ALL:
        if x['date'] > iso(TD): continue
        pc[x['date'][:7]] += x['cost']
        if x['from_van'] and not x['billed']: ub[x['date'][:7]] += x['cost']
    for j in JOBS_ALL:
        if j['status'] == 'Completed' and j['date'] <= iso(TD): rev[j['date'][:7]] += j['price']; jb[j['date'][:7]] += 1
    out = []
    for m in months:
        k = iso(m)[:7]
        out.append(dict(month=iso(m), season=key('season', seas[m.month]), stock_value=round(stock_at(m)), restock_cost=round(rs[k]), parts_cost=round(pc[k]), unbilled_cost=round(ub[k]), revenue=round(rev[k]), jobs=jb[k]))
    return out

def tool_plan_d(): return [dict(year=TD.year + k) for k in range(12)]
def count_rows(): return dict(van_stock=len(VS_ALL), counts=len(SC_ALL), below=N_BELOW, unbilled=N_UNBILLED)

if __name__ == '__main__':
    print(count_rows(), len(parts_used_d()), len(restocks_d()), len(estimates_open_d()), len(purchases_d()), len(tools_d()), len(price_changes_d()))
    print(stock_month_d()[-3:]); print(vehicle_van_d()[:2]); print(estimates_open_d()[:2]); print(price_book_d()[0])
