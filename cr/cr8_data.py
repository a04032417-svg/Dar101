"""Car rental suite part 8: demo rows from cr_core (aggregated tables built from the full generator output, row-level tables thinned)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr8_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

TEAM = {t['name']: t for t in team}
def _ph(role): return [t for t in team if t['role'] == role][0]['phone']
PHONES = {'owner': _ph('Owner-operator'), 'manager': _ph('Manager'), 'bookkeeper': _ph('Bookkeeper'), 'accountant': _ph('Accountant'), 'lender': _ph('Lender'),
          'broker': _ph('Insurance broker'), 'mechanic': _ph('Mechanic'), 'tyres': _ph('Tyre supplier')}

VEH = vehicle_rows(); VEHD = {v['vehicle_id']: v for v in VEH}
FIN = financing_rows(); EXPF = expense_rows(); EXP = expense_rows(n=700)
PNL = pnl_rows(); CASH = cash_rows(); TAX = tax_rows(); PAY = pay_rows(); REN = renewal_rows(); VM = vehicle_month_rows()
CK = K(CLASSES)


def pnl_d():
    return [dict(row_id=r['row_id'], month=r['month'], vehicles=r['vehicles'], rented_days=r['rented_days'], utilisation=r['utilisation'], revenue=r['revenue'], channel_fees=r['channel_fees'],
                 financing=r['financing'], insurance=r['insurance'], maintenance=r['maintenance'], fuel_charge=r['fuel_charging'], staff=r['staff'], overhead=r['overhead'], depreciation=r['depreciation']) for r in PNL]


def class_month_d():
    agg = {}
    for r in VM:
        a = agg.setdefault((r['class'], r['month']), dict(available_days=0, rented_days=0, revenue=0.0, costs=0.0))
        a['available_days'] += r['available_days']; a['rented_days'] += r['rented_days']; a['revenue'] += r['revenue']
        a['costs'] += r['channel_fees'] + r['financing'] + r['insurance'] + r['maintenance'] + r['cleaning'] + r['fuel_charge'] + r['depreciation']
    out = []
    for (c, m), a in sorted(agg.items(), key=lambda kv: (kv[0][1], CLASSES.index(kv[0][0]))):
        out.append(dict(**{'class': CK[c]}, month=m, available_days=a['available_days'], rented_days=a['rented_days'], revenue=R2(a['revenue']), costs=R2(a['costs'])))
    return out


def class_profit_d(): return [{'class': CK[c]} for c in CLASSES]


def vehicles_d():
    rows = []
    for v in VEH:
        rows.append(nb(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], **{'class': CK[v['class']]}, purchase_date=v['purchase_date'], purchase_price=v['purchase_price'], financed=v['financed'],
                            loan_amount=v['loan_amount'], loan_rate=v['loan_rate'], loan_months=v['loan_months'], monthly_payment=v['monthly_payment'], odometer=v['odometer'],
                            status=key('vstatus', v['status']), sold_date=v['sold_date'], resale_estimate=v['resale_estimate'], insurance_year=v['insurance_year'])))
    low = [r for r in rows if r['vehicle_id'] == ST['low_vehicle']]
    return low + [r for r in rows if r['vehicle_id'] != ST['low_vehicle']]


def financing_d():
    rows = [dict(fin_id=f['fin_id'], date=f['date'], month=f['month'], vehicle=f['vehicle'], **{'class': CK[VEHD[f['vehicle_id']]['class']]}, payment=f['payment'], interest=f['interest'],
                 principal=f['principal'], balance_after=f['balance_after']) for f in FIN]
    low = [r for r in rows if r['vehicle'] == ST['low_vehicle_name']][-1:]
    return low + [r for r in rows if r not in low]


def loan_view_d():
    return [dict(vehicle=v['vehicle'], **{'class': CK[v['class']]}) for v in VEH if v['financed'] and v['status'] != 'Sold']


def expenses_d():
    return [nb(dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('expcat', e['category']), vendor=key('vendor', e['vendor']), vehicle_id=e['vehicle_id'], amount=e['amount'])) for e in EXP]


def cost_cat_d():
    lo = iso(month_start(11)); agg = {}
    for e in EXPF:
        if e['month'] >= lo: agg[(e['category'], e['month'])] = agg.get((e['category'], e['month']), 0.0) + e['amount']
    return [dict(category=key('expcat', c), month=m, amount=R2(a)) for (c, m), a in sorted(agg.items(), key=lambda kv: (kv[0][1], EXPENSE_CATEGORIES.index(kv[0][0])))]


def cash_d():
    return [dict(row_id=r['row_id'], month=r['month'], opening=r['opening'], receipts=r['receipts'], operating_costs=r['operating_costs'], vehicle_purchases=r['vehicle_purchases'],
                 vehicle_sales=r['vehicle_sales'], owner_draw=r['owner_draw'], tax_set_aside=r['tax_set_aside']) for r in CASH]


def tax_d():
    out = []
    for i, r in enumerate(TAX):
        paid = r['paid_to_tax']
        if r['month'] == iso(month_start(1)): paid = 2500.0     # the last quarterly payment was part only: a balance stays in the account
        out.append(dict(row_id=r['row_id'], month=r['month'], set_aside=r['set_aside'], paid_to_tax=paid))
    k = next((i for i, r in enumerate(out) if r['paid_to_tax'] > 0 and r['set_aside'] > 0 and r['month'] >= iso(month_start(24))), 0)
    out.insert(0, out.pop(k))                             # the first demo row feeds the sheet: a month with a payment
    return out


def draw_d():
    out = []
    for i, r in enumerate(CASH, 1):
        out.append(dict(draw_id='OD-%03d' % i, month=r['month'], regular_draw=OWNER_DRAW, extra_draw=R2(r['owner_draw'] - OWNER_DRAW), status=key('paystatus', 'Accruing' if r['month'] == iso(month_start(0)) else 'Paid')))
    return out


def draw_plan_d(): return [dict(month=iso(month_start(-k)), ahead=k) for k in range(1, 13)]


def known_costs_d():
    out = []; n = 0
    nxt = iso(add_months(month_start(0), 1).replace(day=5)) if T0.day > 5 else iso(T0.replace(day=5))
    def add(item, kind, date, amount):
        nonlocal n; n += 1; out.append(dict(cost_id='KC-%02d' % n, item=item, kind=key('costkind', kind), date=date, amount=R2(amount)))
    for v in VEH:
        if v['financed'] and v['status'] != 'Sold': add('Loan payment, ' + v['vehicle'], 'Loan payment', nxt, v['monthly_payment'])
    for r in REN:
        if r['status'] != 'Done' and ago(0) <= r['due_date'] <= ahead(30): add('%s, %s' % (r['kind'], r['vehicle']), 'Renewal', r['due_date'], r['cost'])
    last3 = [iso(month_start(k)) for k in (1, 2, 3)]
    staff = sum(p['total'] for p in PAY if p['month'] in last3 and p['pay_type'] != 'Owner draw') / 3.0
    add('Payroll, second half of the month', 'Payroll', iso(add_months(month_start(0), 1) - _dt.timedelta(days=1)), staff * 0.5)
    def avg(cats): return sum(e['amount'] for e in EXPF if e['month'] in last3 and e['category'] in cats) / 3.0
    add('Rent of the main lot', 'Rent and lot', iso(add_months(month_start(0), 1)), avg(['Rent and lot']))
    add('Utilities', 'Other bills', iso(T0 + _dt.timedelta(days=9)), avg(['Utilities']))
    add('Booking software and card fees', 'Other bills', iso(T0 + _dt.timedelta(days=14)), avg(['Booking software', 'Card fees']))
    add('Cleaning supplies', 'Other bills', iso(T0 + _dt.timedelta(days=6)), avg(['Cleaning supplies']))
    add('Marketing', 'Other bills', iso(T0 + _dt.timedelta(days=20)), avg(['Marketing']))
    add('Accounting fee', 'Other bills', iso(T0 + _dt.timedelta(days=22)), avg(['Accounting']))
    return out


def replace_d():
    newest = {}
    for v in sorted(VEH, key=lambda x: x['purchase_date']): newest[v['class']] = v['purchase_price']
    out = []; k = 0
    for v in VEH:
        if v['status'] == 'Sold': continue
        vp = vehicle_profit(v['vehicle_id'], 12); k += 1
        out.append(dict(vehicle=v['vehicle'], new_cost=round(newest[v['class']] * 1.03 / 50) * 50, profit_12m=R2(vp['profit']), rev_12m=R2(vp['revenue']), review_on=iso(T0 + _dt.timedelta(days=3 + 2 * k))))
    low = [r for r in out if r['vehicle'] == ST['low_vehicle_name']]
    return low + [r for r in out if r['vehicle'] != ST['low_vehicle_name']]


def keep_replace_d(): return [dict(vehicle=r['vehicle']) for r in replace_d()]


SC_CHANGE = ['Your last months continued', 'Fewer rented days: set the points in the settings', 'Extra cars added with a loan: set the number', 'Loans cost more: set the points',
             'Channel fees rise: set the share', 'Rates rise: set the share']
def scenarios_d():
    r = [dict(scenario=key('scen', s), change=c) for s, c in zip(SCENARIOS, SC_CHANGE)]
    return r[1:2] + r[:1] + r[2:]
def scenario_months_d(): return [dict(scenario=key('scen', s), ahead=k) for s in SCENARIOS for k in range(1, 13)]

CASES = [('Economy', 11800, 0.8, .88, .74, .55, 45, .5), ('Compact', 16200, 0.8, .86, .72, .55, 54, .5), ('Midsize SUV', 26500, 0.8, .85, .70, .52, 86, .5),
         ('7-seat Van', 24800, 0.8, .86, .68, .50, 109, .5), ('Premium', 39000, 0.8, .78, .55, .38, 150, .5), ('Electric', 33000, 0.75, .84, .70, .54, 99, .5),
         ('Economy', 11800, 0.0, .88, .74, .55, 45, .5), ('Midsize SUV', 27200, 0.9, .78, .62, .45, 86, .6), ('Compact', 16200, 0.8, .75, .60, .45, 54, .6),
         ('Premium', 39000, 0.8, .90, .72, .55, 150, .5), ('Electric', 33000, 1.0, .80, .66, .50, 99, .5), ('7-seat Van', 24800, 0.7, .80, .60, .42, 109, .6)]
def cases_d():
    return [dict(case_id='BC-%02d' % i, **{'class': CK[c]}, price=p, financing_share=f, util_peak=a, util_shoulder=b, util_off=o, day_rate=r, overhead_load=ol, plan_date=iso(T0 + _dt.timedelta(days=4 + 5 * i)))
            for i, (c, p, f, a, b, o, r, ol) in enumerate(CASES, 1)]


def fleet_value_d(): return [{'class': CK[c]} for c in CLASSES]


def purchases_d():
    last = {}
    for f in FIN: last[f['vehicle_id']] = f
    ev = []
    for v in VEH:
        if v['purchase_date'] >= iso(HISTORY_START): ev.append((v['purchase_date'], 'Purchase', v, v['purchase_price'], v['loan_amount']))
        if v['status'] == 'Sold': ev.append((v['sold_date'], 'Sale', v, v['sold_price'], last[v['vehicle_id']]['balance_after'] if v['vehicle_id'] in last else 0.0))
    ev.sort(key=lambda e: (e[0], e[1] != 'Purchase'))
    return [dict(event_id='PS-%02d' % i, vehicle=v['vehicle'], event=key('vevent', e), date=d, amount=a, loan=l) for i, (d, e, v, a, l) in enumerate(ev, 1)]
