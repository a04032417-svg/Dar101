"""Short-term rental host suite part 8: demo rows from sr_core (full generator output for the monthly tables, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr8_lists import *
from sr_core import _by_month_unit
import collections, calendar

dd = to_date
R = rng('sr8')
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
ST = story()
AGG = _by_month_unit()
UMR = {(r['unit_id'], r['month'][:7]): r for r in unit_month_rows()}
CASH = cash_rows(); EXP = expense_rows(); BK = booking_rows(); PO = payout_rows()
DIM = lambda ym: calendar.monthrange(int(ym[:4]), int(ym[5:7]))[1]
CUR = TODAY.isoformat()[:7]
FRAC = TODAY.day / float(DIM(CUR))
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def r2(x): return round(x + 1e-9, 2)

# ---------- unit profit by month (every unit and month with activity, rent and bills prorated in the month in progress)
RENT = collections.defaultdict(float); OTH = collections.defaultdict(float)
for e in EXP:
    if e['unit_id']:
        if e['category'] == 'Rent or mortgage': RENT[(e['unit_id'], e['month'][:7])] += e['amount']
        elif e['category'] not in ('Utilities', 'Internet and TV'): OTH[(e['unit_id'], e['month'][:7])] += e['amount']
def pl_d():
    out = []; keys = sorted(AGG, key=lambda k: (k[1], k[0]))
    for i, (uid, ym) in enumerate(keys, 1):
        x = AGG[(uid, ym)]; u = UNI[uid]; f = FRAC if ym == CUR else 1.0
        um = UMR.get((uid, ym)); av = (um['available_nights'] if um and ym != CUR else DIM(ym) if ym != CUR else TODAY.day)
        nights = min(x['nights'], av)
        out.append(dict(pl_id='PL-%04d' % i, month=ym + '-01', unit=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), available_nights=av, nights=nights,
                        revenue=r2(x['revenue']), platform_fees=r2(x['fees']), cleaning=r2(x['cleaning']), supplies=r2(x['supplies']), maintenance=r2(x['maintenance']),
                        rent=r2(RENT[(uid, ym)] * f), utilities=r2(x['utilities'] * f), other=r2(OTH[(uid, ym)] * f) or None))
    return [nb(r) for r in out]
PL = pl_d()

# ---------- units
UREV = {}
def units_d():
    out = []
    for i, u in enumerate(units):
        p = unit_profit(u['unit_id'])
        out.append(nb(dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], owner=u['owner'], owner_phone=OWNP[u['owner']],
                           base_rate=u['base_rate'], rent=u['rent'], utilities=u['utilities'], internet=u['internet'], since=u['since'], mgmt_pct=u['mgmt_pct'],
                           review_on=ago(int(R.uniform(12, 150))) if i % 3 else ahead(int(R.uniform(5, 40))))))
    return out

# ---------- bookings (every 4th booking, the story booking always in), payouts of those bookings
def bookings_d():
    out = []
    for i, b in enumerate(BK):
        if i % 4 == 0 or b['booking_id'] == ST['missing_booking']:
            out.append(nb(dict(booking_id=b['booking_id'], unit=b['unit'], city=key('city', b['city']), channel=key('chan', b['channel']), guest=b['guest'], guest_country=b['guest_country'],
                               check_in=b['check_in'], check_out=b['check_out'], nights=b['nights'], room_revenue=b['room_revenue'], cleaning_fee=b['cleaning_fee'], earned=b['earned'],
                               platform_fee=b['platform_fee'], status=key('bstatus', b['status']))))
    out.sort(key=lambda r: (r['check_out'], r['booking_id']))
    return out
BKS = bookings_d(); BKIDS = {b['booking_id'] for b in BKS}
def payouts_d():
    out = []
    for p in PO:
        if p['booking_id'] in BKIDS:
            out.append(nb(dict(payout_id=p['payout_id'], booking_id=p['booking_id'], channel=key('chan', p['channel']), unit=p['unit'], expected_date=p['expected_date'], paid_on=p['paid_on'],
                               expected_amount=p['expected_amount'], received_amount=p['received_amount'] if p['paid_on'] else None, status=key('payst', p['status']))))
    out.sort(key=lambda r: (r['expected_date'], r['payout_id']))
    return out

# ---------- expenses (all overheads, every second unit cost)
def expenses_d():
    out = []; k = 0
    for e in EXP:
        if not e['unit_id']: keep = True
        else: k += 1; keep = k % 2 == 0
        if keep: out.append(dict(expense_id=e['expense_id'], date=e['date'], unit=e['unit'], category=key('ecat', e['category']), description=e['description'], amount=e['amount'], paid_to=e['paid_to']))
    return out

# ---------- cash months with my own draws (the chain is recomputed, the minimum stays 9000)
DRAWS = [7000, 6000, 7000, 8000, 7000, 5000, 6500, 7000, 9000, 7500, 7000, 6000, 8000, 3000]
DRAW_WHY = ['Monthly draw', 'Monthly draw', 'Monthly draw', 'Holiday top-up', 'Monthly draw', 'Reduced draw, cash tight', 'Monthly draw', 'Monthly draw', 'Extra draw after peak season',
            'Draw for a personal cost', 'Monthly draw', 'Monthly draw', 'Extra draw after peak season', 'Monthly draw']
def cash_calc():
    rows = []; run = 0.0; mn = 0.0
    for c, dr in zip(CASH, DRAWS):
        out = c['expenses'] + c['cleaners'] + c['supplies'] + c['maintenance'] + c['cohost_fees'] + c['owner_payouts'] + c['local_taxes'] + dr
        run += c['cash_in'] - out; mn = min(mn, run); rows.append((c, dr))
    op = 9000 - mn
    return op, rows
def cash_d():
    op, rows = cash_calc(); out = []; bal = op
    for i, (c, dr) in enumerate(rows):
        out.append(nb(dict(cash_id='CM-%02d' % (i + 1), month=c['month'], opening=r2(bal), cash_in=c['cash_in'], expenses=c['expenses'], cleaners=c['cleaners'], supplies=c['supplies'], maintenance=c['maintenance'],
                           cohost_fees=c['cohost_fees'], owner_payouts=c['owner_payouts'] or None, local_taxes=c['local_taxes'] or None, owner_draw=dr)))
        bal += c['cash_in'] - (c['expenses'] + c['cleaners'] + c['supplies'] + c['maintenance'] + c['cohost_fees'] + c['owner_payouts'] + c['local_taxes'] + dr)
    return out
CASHD = cash_d()
def draws_d():
    return [dict(draw_id='DR-%02d' % (i + 1), month=c['month'], amount=a, reason=key('dreason', w)) for i, (c, a, w) in enumerate(zip(CASH, DRAWS, DRAW_WHY))]

# ---------- cash forecast (13 weeks from this week's Monday)
def forecast_d():
    mon = week_start(TODAY); sched = collections.defaultdict(float)
    for p in PO:
        if p['status'] == 'Scheduled': sched[p['expected_date']] += p['expected_amount']
    last = CASHD[-2]; costs_wk = (last['cleaners'] + last['supplies'] + last['maintenance'] + last['cohost_fees']) / 4.35
    lump = last['expenses']; ownpay = sum(s['net_to_owner'] for s in owner_statement_rows() if s['month'] == iso(month_start(1)))
    taxm = sum(t['collected_by_host'] for t in tax_rows() if t['month'] == iso(month_start(1)))
    out = []; drawn = 0
    for i in range(13):
        m = mon + day(7 * i); days = [m + day(k) for k in range(7)]
        known = sum(sched[iso(d)] for d in days); ym = '%d-%02d' % (m.year - 1, m.month)
        typ = sum(x['revenue'] for (u, mm), x in AGG.items() if mm == ym) * 0.88 / 4.35
        first = any(d.day == 1 for d in days); tenth = any(d.day == 10 for d in days); twenty = any(d.day == 20 for d in days)
        wob = 0.92 + 0.16 * R.random(); drawn += 1 if first else 0
        out.append(nb(dict(fc_id='FC-%02d' % (i + 1), week=iso(m), expected_payouts=r2(max(known, typ * 0.85 * wob)), expected_costs=r2(costs_wk * (0.9 + 0.2 * R.random()) + (lump if first else 0)),
                           owner_payments=r2(ownpay * (0.7 + 0.2 * R.random())) if tenth else None, local_tax=r2(taxm * (0.9 + 0.25 * R.random())) if twenty else None, owner_draw=[6500, 7000, 7500][drawn % 3] if first else None)))
    return out

# ---------- cleaner pay, supplies, maintenance
def cleaner_pay_d():
    return [dict(pay_id=c['pay_id'], month=c['month'], cleaner=c['cleaner'], turnovers=c['turnovers'], hours=c['hours'], amount=c['amount']) for c in cleaner_pay_rows()]
def supplies_d():
    return [dict(purchase_id=p['purchase_id'], date=p['date'], item=p['item'], category=key('scat', p['category']), qty=p['qty'], unit_cost=p['unit_cost'], amount=p['amount'], supplier=p['supplier'])
            for p in supply_purchase_rows(n=200)]
def maint_d():
    rows = [t for t in maintenance_rows() if t['done_on'] and t['cost'] > 0]; step = len(rows) / 150.0; rows = [rows[int(i * step)] for i in range(150)]
    return [dict(ticket_id=t['ticket_id'], unit=t['unit'], kind=t['kind'], done_on=t['done_on'], handyperson=t['handyperson'], parts_cost=t['parts_cost'], labour_cost=t['labour_cost'], cost=t['cost']) for t in rows]

# ---------- owner statements, co-host fees, local tax
def statements_d():
    return [nb(dict(statement_id=s['statement_id'], month=s['month'], owner=s['owner'], owner_phone=OWNP[s['owner']], revenue=s['revenue'], platform_fees=s['platform_fees'], mgmt_pct=s['mgmt_pct'], mgmt_fee=s['mgmt_fee'],
                    net_to_owner=s['net_to_owner'], status=key('stmst', s['status']), paid_on=s['paid_on'])) for s in owner_statement_rows()]
def cohost_d():
    return [nb(dict(fee_id=c['fee_id'], month=c['month'], units=c['units'], net_revenue=c['net_revenue'], fee_pct=c['fee_pct'], fee_amount=c['fee_amount'], status=key('stmst', 'Paid' if c['status'] == 'Paid' and c['month'] != iso(month_start(1)) else 'Sent' if c['month'] == iso(month_start(1)) else 'Draft'),
                    paid_on=c['paid_on'] if c['month'] != iso(month_start(1)) else '')) for c in cohost_fee_rows()]
def tax_d():
    return [nb(dict(tax_id=t['tax_id'], month=t['month'], city=key('city', t['city']), nights=t['nights'], room_revenue=t['room_revenue'], tax_pct=t['tax_pct'], tax_collected=t['tax_collected'],
                    collected_by_host=t['collected_by_host'], remitted=t['remitted'] or None, due_date=t['due_date'], status=key('taxst', t['status']), paid_on=t['paid_on'])) for t in tax_rows()]

# ---------- income tax set-aside (monthly), business profit = own units + management fees - co-host fees - overheads
def taxset_d():
    prof = collections.defaultdict(float)
    for r in PL:
        if UNN[r['unit']]['rent'] > 0 or UNN[r['unit']]['owner'] == OWNER: prof[r['month'][:7]] += (r['revenue'] - r['platform_fees'] - r['cleaning'] - r['supplies'] - r['maintenance'] - r['rent'] - r['utilities'] - r.get('other', 0))
    for s in owner_statement_rows(): prof[s['month'][:7]] += s['mgmt_fee']
    for c in cohost_fee_rows(): prof[c['month'][:7]] -= c['fee_amount']
    for e in EXP:
        if not e['unit_id']: prof[e['month'][:7]] -= e['amount']
    out = []; held = 0.0; ms = [c['month'] for c in CASH]
    for i, m in enumerate(ms):
        p = r2(prof[m[:7]]); u = [0.97, 1.0, 0.9, 1.02, 0.85, 0.95, 1.0, 1.05, 0.9, 0.97, 1.0, 0.8, 0.95, 1.0][i]
        s = r2(max(p, 0) * 0.15 * u); held += s
        q = i == 0 or m[5:7] in ('12', '03', '06', '09')
        d = dict(ts_id='TS-%02d' % (i + 1), month=m, profit=p, set_aside=s)
        if q:
            pa = r2(held * 0.6); held -= pa; d['paid_amount'] = pa; d['paid_on'] = iso(dd(m) + day(14))
        d['review_on'] = iso(add_months(dd(m), 1) + day(14))
        out.append(d)
    return out

# ---------- loans and leases (12)
def loans_d():
    out = []; lease_end = {'UN-07': 75, 'UN-01': 410, 'UN-02': 300, 'UN-03': 520, 'UN-04': 640, 'UN-05': 880, 'UN-06': 150}
    for i, u in enumerate([u for u in units if u['rent'] > 0]):
        d = lease_end[u['unit_id']]; left = max(1, round(d / 30.4))
        out.append(dict(loan_id='LN-%02d' % (i + 1), item='Lease of %s' % u['name'], kind=key('lkind', 'Unit lease'), lender='Landlord, %s' % u['city'], monthly_payment=u['rent'], balance=r2(u['rent'] * left),
                        end_date=ahead(d), review_on=ahead(max(5, d - 100))))
    more = [('Furniture for the Cascais units', 'Furniture loan', 'Furniture supplier', 420, 5040, 330), ('Furniture for Sintra cabin and cottage', 'Furniture loan', 'Furniture supplier', 310, 6200, 480),
            ('Laundry and linen equipment', 'Equipment loan', 'Equipment finance company', 265, 3180, 210), ('Deposit and set-up loan', 'Deposit loan', 'Local bank', 540, 12960, 600),
            ('Working capital loan', 'Bank loan', 'Local bank', 890, 17800, 820)]
    for j, (item, kd, lender, pay, bal, days) in enumerate(more):
        out.append(dict(loan_id='LN-%02d' % (len(out) + 1), item=item, kind=key('lkind', kd), lender=lender, monthly_payment=pay, balance=bal, end_date=ahead(days), review_on=ahead(max(5, days - 120))))
    return out

# ---------- break-even rows (12) from the last 12 months
def breakeven_d():
    out = []
    for i, u in enumerate(units):
        p = unit_profit(u['unit_id']); nights = max(p['nights'], 1)
        out.append(dict(be_id='BE-%02d' % (i + 1), unit=u['name'], fixed_cost=r2((p['fixed'] + p['utilities']) / 12.0), var_cost=r2((p['cleaning'] + p['supplies'] + p['maintenance']) / nights),
                        rate=r2(p['revenue'] / nights), fee_pct=round(p['fees'] / max(p['revenue'], 1), 4), review_on=ago(int(R.uniform(10, 170)))))
    return out

# ---------- growth scenarios (12) and unit pipeline (12)
def growth_d():
    v = [(1, 0, 0, 0), (2, 0, 0, 0), (0, 0.05, -0.02, 0), (0, 0.08, -0.04, 0), (0, 0, 0.05, 0.01), (0, 0, 0.10, 0.02), (0, 0.0, 0.03, -0.02), (-1, 0, 0, 0), (0, 0, 0, -0.01), (0, 0, 0, -0.03), (1, 0.05, -0.02, 0.01), (-2, 0.10, -0.05, -0.01)]
    return [dict(scn_id='GS-%02d' % (i + 1), scenario=key('scn', s), units_added=a, rate_change=b, occupancy_change=c, cost_change=d, review_on=ahead(20 + 9 * i)) for i, (s, (a, b, c, d)) in enumerate(zip(SCEN, v))]
def pipeline_d():
    rows = [('Two-bedroom flat near the river', 'Porto', 2, 138, 0.68, 7800, 1000, 150), ('Studio near the old town', 'Lisbon', 1, 92, 0.72, 5200, 720, 105), ('Three-bedroom house with a garden', 'Cascais', 3, 245, 0.60, 14500, 1900, 240),
            ('Small cabin in the woods', 'Sintra', 1, 155, 0.58, 6500, 800, 120), ('Loft above the market', 'Lisbon', 2, 128, 0.66, 8900, 1100, 140), ('Beach studio, weak winter demand', 'Cascais', 1, 74, 0.45, 5600, 1100, 130),
            ('Family apartment near the station', 'Porto', 3, 165, 0.64, 9800, 1250, 170), ('Penthouse with sea view', 'Cascais', 2, 285, 0.55, 18500, 2600, 260), ('Hillside cottage for four', 'Sintra', 2, 170, 0.57, 9200, 1050, 150),
            ('Central one-bedroom flat', 'Lisbon', 1, 110, 0.74, 6100, 850, 110), ('Large loft for groups', 'Porto', 3, 190, 0.52, 12500, 1800, 200), ('Garden flat near the beach', 'Cascais', 2, 142, 0.62, 8300, 1150, 135)]
    return [dict(idea_id='PI-%02d' % (i + 1), idea=n, city=key('city', c), bedrooms=b, expected_rate=r, expected_occ=o, setup_cost=s, rent=rt, running_cost=rc, decide_on=ahead(14 + 12 * i))
            for i, (n, c, b, r, o, s, rt, rc) in enumerate(rows)]

def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

if __name__ == '__main__':
    for n in ['pl', 'units', 'bookings', 'payouts', 'expenses', 'cash', 'forecast', 'cleaner_pay', 'supplies', 'maint', 'statements', 'cohost', 'tax', 'taxset', 'draws', 'loans', 'breakeven', 'growth', 'pipeline', 'team']:
        d = globals()[n + '_d'](); print(n, len(d))
    print(sum(r['revenue'] for r in PL if r['month'] == TODAY.isoformat()[:7] + '-01'), [(c['month'], c['closing'] if 'closing' in c else '') for c in CASHD][:1])
    for t in taxset_d(): print(t['month'], t['profit'], t['set_aside'], t.get('paid_amount'))
    for f in forecast_d(): print(f)
