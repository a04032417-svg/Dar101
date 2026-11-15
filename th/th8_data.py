"""Therapy part 8: demo rows from th_core (full generator output for aggregated tables, windows for row-level logs) plus generated planning rows."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th8_lists import *
import th_core as C
import datetime as _d

dd = to_date
ST = story()
TODAY_ = C.TODAY
MS0 = month_start(0).isoformat(); LM0 = month_start(1).isoformat()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows
def newest(rows, col='month'): return sorted(rows, key=lambda r: r[col], reverse=True)
def r0(x): return float(round(x))
def r2(x): return round(x + 1e-9, 2)

SM = C.service_month_rows(); PAYR = C.clinician_pay_rows(); EXP = C.expense_rows(); SUB = C.sublet_rows(); CL = C.claim_rows(); CASH = C.cash_rows(); TAX = C.tax_rows()
CMR = C.clinician_month_rows(); RM = C.room_month_rows(); SES = C.session_rows()
MONTHS24 = [iso(m) for m in C._months24()]

# ------------------------------------------------------------------ profit and loss by month
def _pnl_vals():
    out = {}
    for m in MONTHS24:
        sess = sum(x['revenue'] for x in SM if x['month'] == m and x['service'] != 'Group program')
        grp = sum(x['revenue'] for x in SM if x['month'] == m and x['service'] == 'Group program')
        sub = sum(x['amount'] for x in SUB if x['month'] == m)
        wo = sum(x['written_off'] for x in CL if x['date'][:7] == m[:7])
        cp = sum(x['amount'] + x['employer_cost'] for x in PAYR if x['month'] == m and x['pay_type'] != 'Hourly')
        sp = sum(x['amount'] + x['employer_cost'] for x in PAYR if x['month'] == m and x['pay_type'] == 'Hourly')
        rent = sum(x['amount'] for x in EXP if x['month'] == m and x['category'] == 'Rent')
        oth = sum(x['amount'] for x in EXP if x['month'] == m and x['category'] != 'Rent')
        n = sum(x['sessions'] for x in SM if x['month'] == m)
        out[m] = dict(sessions=n, session_revenue=r2(sess), group_revenue=r2(grp), sublet_income=r2(sub), write_offs=r2(wo), clinician_pay=r2(cp), staff_pay=r2(sp), rent=r2(rent), other_expenses=r2(oth))
    return out
PV = _pnl_vals()
def pnl_d():
    out = []
    for i, m in enumerate(MONTHS24, 1):
        out.append(dict(pl_id='PL-%03d' % i, month=m, **PV[m]))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0)

# ------------------------------------------------------------------ service profit by month
def svc_months_d():
    out = [dict(row_id=r['row_id'], month=r['month'], service=key('svcall', r['service']), booked=r['booked'], sessions=r['sessions'], revenue=r['revenue'], clinician_pay=r['clinician_pay'],
                room_cost=r['room_cost'], other_cost=r['other_cost']) for r in SM]
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['service'] == key('svcall', ST['losing_service']))

# ------------------------------------------------------------------ clinician profit by month
def clin_months_d():
    agg = {}
    for s in SES:
        if s['date'] > ago(0): continue
        a = agg.setdefault((s['clinician'], s['date'][:7] + '-01'), dict(rev=0.0, pay=0.0, room=0.0, oth=0.0))
        a['rev'] += s['charge']; a['pay'] += s['clinician_pay']; a['room'] += s['room_cost']; a['oth'] += s['other_cost']
    out = []
    for r in CMR:
        a = agg.get((r['clinician'], r['month']))
        if not a: continue
        out.append(dict(row_id=r['row_id'], month=r['month'], clinician=key('clin', r['clinician']), revenue=r2(a['rev']), clinician_pay=r2(a['pay']), room_cost=r2(a['room']), other_cost=r2(a['oth'])))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['clinician'] == key('clin', 'Kenji Watanabe'))

# ------------------------------------------------------------------ expenses
def expenses_d():
    out = []
    for e in EXP:
        meth = e['method']
        if e['category'] in ('Insurance', 'Phone and internet', 'Utilities'): meth = 'Direct debit'
        elif e['category'] == 'Office supplies' and e['amount'] <= 75: meth = 'Cash'
        out.append(dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('ecat', e['category']), description=e['description'], amount=e['amount'], paid_to=e['paid_to'],
                        method=key('paym', meth)))
    out = sorted(out, key=lambda r: (r['date'], r['expense_id']), reverse=True)
    return front(out, lambda r: r['method'] == key('paym', 'Card') and r['date'] >= ago(30))

# ------------------------------------------------------------------ budget by category
FACTOR = {'Rent': 1.0, 'Utilities': 1.05, 'Cleaning': 1.0, 'Practice software': 0.96, 'Phone and internet': 1.0, 'Insurance': 1.03, 'Marketing': 0.78, 'Training': 0.84, 'Supervision': 1.06,
          'Office supplies': 1.12, 'Therapy materials': 0.92, 'Accounting': 1.0, 'Bank and card fees': 0.98, 'Professional fees': 1.1}
def budget_d():
    jan1 = _d.date(TODAY_.year, 1, 1); frac = ((TODAY_ - jan1).days + 1) / 365.0; out = []
    for i, cat in enumerate(EXPENSE_CATEGORIES, 1):
        ytd = sum(e['amount'] for e in EXP if e['category'] == cat and e['date'] >= jan1.isoformat())
        out.append(dict(budget_id='BG-%02d' % i, category=key('ecat', cat), yearly_budget=max(200.0, float(round(ytd / frac * FACTOR[cat] / 100.0) * 100))))
    return front(out, lambda r: r['category'] == key('ecat', 'Marketing'))

# ------------------------------------------------------------------ room costs by month
def room_costs_d():
    out = []
    for i, m in enumerate(MONTHS24, 1):
        rent = sum(e['amount'] for e in EXP if e['month'] == m and e['category'] == 'Rent'); cl = sum(e['amount'] for e in EXP if e['month'] == m and e['category'] == 'Cleaning')
        ut = sum(e['amount'] for e in EXP if e['month'] == m and e['category'] == 'Utilities')
        oh = sum(x['open_hours'] for x in RM if x['month'] == m); uh = sum(x['session_hours'] + x['group_hours'] + x['sublet_hours'] for x in RM if x['month'] == m)
        out.append(dict(rc_id='RC-%02d' % i, month=m, rent=r2(rent), cleaning=r2(cl), utilities=r2(ut), open_hours=r2(oh), used_hours=r2(uh)))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0)

# ------------------------------------------------------------------ cash months and the cash back-cast for health months of cover
def _pos():
    pos = {}
    def add(d, k, v):
        if not d or dd(d) > TODAY_: return
        pos.setdefault(d[:7], {}).setdefault(k, 0.0); pos[d[:7]][k] += v
    for p in C.payment_rows(): add(p['date'], 'client', p['amount'])
    for x in CL: add(x['paid_on'], 'payer', x['paid_amount'])
    for x in SUB: add(x['paid_on'], 'sublet', x['amount'])
    for x in PAYR: add(x['paid_on'], 'out', x['amount'] + x['employer_cost'])
    for x in EXP: add(x['date'], 'out', x['amount'])
    for x in TAX: add(x['paid_on'], 'tax', x['set_aside'])
    return pos
def cash_d():
    out = []
    for i, r in enumerate(CASH, 1):
        out.append(dict(cash_id='CA-%02d' % i, **r))
    out.reverse()
    return front(out, lambda r: r['month'] == LM0)
def cover_by_month():
    """months of expenses in cash for the 24 months (the 14 cash months exactly, earlier months back-cast from the same payments)"""
    pos = _pos(); cov = {}
    for r in CASH:
        outflow = r['staff_pay'] + r['contractor_pay'] + r['rent'] + r['other_expenses']; cov[r['month']] = r['closing'] / outflow
    bal = CASH[0]['opening']
    for m in reversed([x for x in MONTHS24 if x < CASH[0]['month']]):
        p = pos.get(m[:7], {}); out = p.get('out', 0)
        cov[m] = bal / max(1.0, out)
        if m < '2025-02-01': cov[m] = None
        net = p.get('client', 0) + p.get('payer', 0) + p.get('sublet', 0) - out - p.get('tax', 0) - OWNER_DRAW
        bal -= net
    for m in [x for x in MONTHS24 if cov.get(x) is None]: cov[m] = cov['2025-02-01'] * (1.06 if m == '2025-01-01' else 1.12)
    return cov
COVER = cover_by_month()

# ------------------------------------------------------------------ 13-week cash forecast (own history x day-of-month pattern)
def forecast_d():
    last3 = CASH[-4:-1]
    cl_w = sum(r['client_payments'] for r in last3) / 3 / 4.33; pr_w = sum(r['payer_payments'] for r in last3) / 3 / 4.33
    pay_m = sum(r['staff_pay'] + r['contractor_pay'] for r in last3) / 3; oth_m = sum(r['other_expenses'] for r in last3) / 3
    tax_m = sum(x['set_aside'] for x in TAX[-12:-1]) / 11.0
    start = week_start(TODAY_) + _d.timedelta(days=7); out = []
    for i in range(13):
        mon = start + _d.timedelta(days=7 * i); days = [mon + _d.timedelta(days=k) for k in range(7)]
        dom = [x.day for x in days]
        f = 1.4 if any(8 <= v <= 16 for v in dom) else (0.85 if any(1 <= v <= 7 for v in dom) else 0.75)
        hol = 0.55 if (mon.month == 12 and mon.day >= 21) or (mon.month == 1 and mon.day <= 3) else (0.8 if mon.month == 1 and mon.day <= 10 else 1.0)
        jit = [1.02, 0.97, 1.04, 0.95, 1.01, 0.98, 1.03, 0.96, 1.0, 1.05, 0.94, 1.02, 0.99][i]
        client = cl_w * f * hol * jit; payer = pr_w * hol * (2 - jit)
        pay = (pay_m * 0.88 if 10 in dom else 0) + (pay_m * 0.12 if 20 in dom else 0)
        rent = (6800.0 if 1 in dom else 0) + oth_m / 4.0
        tax = 0
        for x in TAX:
            if mon.isoformat() <= x['due_date'] <= days[-1].isoformat(): tax = x['set_aside']
        if (not tax and 20 in dom) or (tax and any(x['status'] == 'Upcoming' and mon.isoformat() <= x['due_date'] <= days[-1].isoformat() for x in TAX)): tax = tax_m
        draw = (OWNER_DRAW / 2 if 15 in dom else 0) + (OWNER_DRAW / 2 if any(x.day == (_d.date(x.year + (x.month == 12), x.month % 12 + 1, 1) - _d.timedelta(days=1)).day for x in days) else 0)
        out.append(dict(week=key('wk', 'Week %d' % (i + 1)), week_start=iso(mon), client_payments=r0(client), payer_payments=r0(payer), pay=r0(pay), rent_costs=r0(rent), tax_set_aside=r0(tax),
                        owner_draw=r0(draw), fc_id='CF-%02d' % (i + 1)))
    return out

# ------------------------------------------------------------------ tax set-aside (inputs only: the amounts are looked up from Profit by Month)
def tax_d():
    out = [nb(dict(tax_id=r['tax_id'], month=r['month'], set_aside_pct=r['set_aside_pct'], due_date=r['due_date'], paid_on=r['paid_on'], status=key('taxst', r['status']))) for r in TAX]
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0)

# ------------------------------------------------------------------ health check by month
def health_d():
    bk = {}
    for r in CMR:
        a = bk.setdefault(r['month'], [0, 0]); a[0] += r['booked'] - r['cancelled']; a[1] += r['capacity']
    out = []
    for i, m in enumerate(MONTHS24, 1):
        bs = bk[m][0] / bk[m][1] if m in bk and bk[m][1] else 0.7
        out.append(dict(hc_id='HC-%02d' % i, month=m, months_cover=round(COVER[m], 2), booked_share=round(bs, 3)))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0)

# ------------------------------------------------------------------ money owed at month end
def owed_d():
    cag = C.client_ageing_rows(); pag = C.payer_ageing_rows(); out = []
    for i, r in enumerate(CASH, 1):
        m = r['month']
        cb = sum(x['balance'] for x in cag if x['month'] == m); oc = sum(x['amount'] for x in pag if x['month'] == m)
        asof = TODAY_ if m == MS0 else C._eom(dd(m))
        us = sum(x['amount'] for x in SUB if x['invoiced_on'] and x['invoiced_on'] <= iso(asof) and (not x['paid_on'] or x['paid_on'] > iso(asof)))
        out.append(dict(mo_id='MO-%02d' % i, month=m, client_balances=r2(cb), open_claims=r2(oc), unpaid_sublets=r2(us)))
    out.reverse()
    return front(out, lambda r: r['month'] == LM0)

# ------------------------------------------------------------------ bills due in the next 8 weeks
def bills_d():
    rows = []
    def add(d, item, cat, amt):
        if TODAY_ < d <= TODAY_ + _d.timedelta(days=56): rows.append((d, item, cat, amt))
    nclin = 6
    for k in (0, 1, 2):
        m = add_months(_d.date(TODAY_.year, TODAY_.month, 1), k)
        D_ = lambda n: m + _d.timedelta(days=n - 1)
        add(D_(1), 'Practice suite rent', 'Rent', 6800.0)
        add(D_(2), 'Scheduling, billing and records system', 'Practice software', 190.0 + 14 * nclin)
        add(D_(4), 'Practice and building cover, monthly', 'Insurance', 230.0)
        add(D_(7), 'Power, water and heating', 'Utilities', 455.0 if m.month in (12, 1, 2) else 390.0)
        add(D_(9), 'Phone lines and fibre', 'Phone and internet', 145.0)
        add(D_(14), 'Paper, printing and waiting room supplies', 'Office supplies', 90.0)
        add(D_(17), 'Toys, games, cards and worksheets', 'Therapy materials', 140.0 + (m.month % 2) * 40)
        add(D_(19), 'Bookkeeping and payroll', 'Accounting', 380.0)
        add(D_(27), 'Evening cleaning, 5 days a week', 'Cleaning', 640.0)
        add(D_(28), 'Monthly group supervision', 'Supervision', 180.0)
        add(C._eom(m), 'Card fees and account charges', 'Bank and card fees', 420.0 + 12 * k)
    add(TODAY_ + _d.timedelta(days=9), 'Online course for the associate', 'Training', 260.0)
    add(TODAY_ + _d.timedelta(days=22), 'Printed leaflets for the winter talks', 'Marketing', 185.0)
    add(TODAY_ + _d.timedelta(days=34), 'Annual membership fee, owner', 'Professional fees', 390.0)
    add(TODAY_ + _d.timedelta(days=41), 'Quarterly IT support visit', 'Practice software', 180.0)
    rows.sort(key=lambda x: (x[0], x[1]))
    return [dict(bill_id='BL-%02d' % i, due_date=iso(d), item=it, category=key('ecat', cat), amount=a) for i, (d, it, cat, a) in enumerate(rows, 1)]

# ------------------------------------------------------------------ service fixes (the base numbers come from the service months)
def _svc12(svc):
    ms = {iso(month_start(k)) for k in range(1, 13)}; t = dict(rev=0.0, pay=0.0, room=0.0, oth=0.0, n=0)
    for x in SM:
        if x['service'] == svc and x['month'] in ms:
            t['rev'] += x['revenue']; t['pay'] += x['clinician_pay']; t['room'] += x['room_cost']; t['oth'] += x['other_cost']; t['n'] += x['sessions']
    return t
MAT = {x['service']: x['materials'] for x in C.services}
def _fixed(svc):
    t = _svc12(svc); return float(round((t['room'] + t['oth'] - MAT[svc] * t['n']) / 12.0 / 10.0) * 10)
def fixes_d():
    spec = [('Behaviour therapy', 'Priya Raman', "Today's terms", "Keep today's fee, split and minutes", 0, 0.0, 0, 0),
            ('Behaviour therapy', 'Priya Raman', 'Raise the fee', 'Raise the list fee by 10', 10, 0.0, 0, 0),
            ('Behaviour therapy', 'Priya Raman', 'Raise the fee', 'Raise the list fee by 20', 20, 0.0, 0, 0),
            ('Behaviour therapy', 'Priya Raman', 'Change the split', 'Lower the contract split by 5 points', 0, -0.05, 0, 0),
            ('Behaviour therapy', 'Priya Raman', 'Change the split', 'Lower the contract split by 8 points', 0, -0.08, 0, 0),
            ('Behaviour therapy', 'Priya Raman', 'Shorter set-up', 'Cut 10 minutes of room set-up and tidy time', 0, 0.0, -10, 0),
            ('Behaviour therapy', 'Priya Raman', 'Cheaper materials', 'Reusable materials, 4 less per session', 0, 0.0, 0, -4),
            ('Behaviour therapy', 'Priya Raman', 'Combined fix', 'Fee up 12, split down 3 points, 5 minutes less, materials 3 less', 12, -0.03, -5, -3),
            ('Speech therapy', 'Priya Raman', "Today's terms", "Keep today's fee, split and minutes", 0, 0.0, 0, 0),
            ('Speech therapy', 'Priya Raman', 'Raise the fee', 'Raise the list fee by 10', 10, 0.0, 0, 0),
            ('Child session', 'Daniel Okoye', "Today's terms", "Keep today's fee, split and minutes", 0, 0.0, 0, 0),
            ('Family session', 'Sofia Marchetti', 'Shorter set-up', 'Cut 5 minutes of set-up between family sessions', 0, 0.0, -5, 0)]
    out = []
    for i, (svc, cl, kind, opt, df, ds, dm, dmat) in enumerate(spec, 1):
        out.append(dict(fix_id='FX-%02d' % i, service=key('svcall', svc), fixkind=key('fixkind', kind), option=opt, clinician=key('clin', cl), fee_change=float(df), split_change=ds, minutes_change=dm,
                        materials_change=float(dmat), materials=MAT[svc], fixed_month=_fixed(svc), decide_by=ahead(7 + 6 * i)))
    return out

# ------------------------------------------------------------------ hiring scenarios
def hiring_d():
    sp = [('Employed clinician, full caseload', 'Salary', 22, 118, 4, 4800, 0, 3200), ('Employed clinician, part-time caseload', 'Salary', 12, 118, 3, 2880, 0, 3200),
          ('Employed clinician, slow start', 'Salary', 18, 112, 6, 4500, 0, 3200), ('Contract clinician, full caseload', 'Percentage split', 20, 118, 4, 0, 70.8, 1800),
          ('Contract clinician, part-time', 'Percentage split', 10, 118, 3, 0, 70.8, 1800), ('Contract clinician for speech work', 'Percentage split', 14, 105, 5, 0, 68.3, 1800),
          ('Contract clinician, 60 percent split', 'Percentage split', 16, 125, 4, 0, 75.0, 1800), ('Associate under supervision', 'Per session', 15, 100, 3, 0, 45.0, 1400),
          ('Associate, evenings and Saturdays', 'Per session', 10, 100, 2, 0, 45.0, 1400), ('Associate, full week', 'Per session', 20, 100, 4, 0, 45.0, 1400),
          ('Employed child clinician', 'Salary', 16, 120, 5, 4500, 0, 4200), ('Contract clinician for couples', 'Percentage split', 12, 165, 4, 0, 99.0, 1800)]
    out = []
    for i, (sc, pt, sw, ch, rm, sal, spay, setup) in enumerate(sp, 1):
        out.append(dict(hire_id='HP-%02d' % i, scenario=sc, pay_type=key('hpay', pt), sessions_week=sw, avg_charge=float(ch), ramp_months=rm, salary=float(sal), session_pay=float(spay), setup_cost=float(setup),
                        start_date=ahead(30 + 14 * i)))
    return out

# ------------------------------------------------------------------ room options
def rooms_opt_d():
    sp = [('Sixth treatment room, full use', 'New treatment room', 1250, 55, 20, 0, 0, 4800), ('Sixth treatment room, quarter use', 'New treatment room', 1250, 55, 5, 0, 0, 4800),
          ('Small adult room on the same floor', 'New treatment room', 950, 45, 14, 0, 0, 3200), ('Large family room next door', 'New treatment room', 1800, 59, 16, 6, 28, 6500),
          ('Online sessions from a quiet corner', 'Online capacity', 0, 40, 10, 0, 0, 700), ('Online evenings for working clients', 'Online capacity', 0, 24, 8, 0, 0, 450),
          ('Online sessions with two more headsets', 'Online capacity', 60, 30, 12, 0, 0, 900), ('Sublet the Play Room in the mornings', 'Sublet the room', 0, 20, 0, 12, 24, 300),
          ('Sublet the Garden Room on Saturdays', 'Sublet the room', 0, 10, 0, 8, 22, 200), ('Sublet the Family Room on weekday evenings', 'Sublet the room', 0, 15, 0, 15, 28, 400),
          ('Open the practice until 21:00 on two evenings', 'Longer opening hours', 280, 8, 7, 0, 0, 350), ('Open on Sundays for three hours', 'Longer opening hours', 340, 3, 1, 0, 0, 250)]
    out = []
    for i, (opt, kd, rent, rh, es, sh, sr, setup) in enumerate(sp, 1):
        out.append(dict(opt_id='RO-%02d' % i, option=opt, kind=key('roomopt', kd), extra_rent=float(rent), room_hours=rh, expected_sessions=es, sublet_hours=sh, sublet_rate=float(sr), setup_cost=float(setup),
                        start_date=ahead(45 + 12 * i)))
    return out

# ------------------------------------------------------------------ set-up and equipment costs
def setup_d():
    out = []
    sp2 = [('Chairs and side tables for two consulting rooms', 1720, 560, 8), ('Desk and lockable filing cabinet', 560, 410, 8), ('Laptop for the new clinician', 1350, 300, 4), ('Headset and webcam for online sessions', 260, 250, 3),
           ('Child room shelving and play furniture', 1480, 520, 7), ('Printer and scanner for the front desk', 380, 160, 5), ('Sound machine for each consulting room door', 140, 90, 5),
           ('Quiet Room refit: flooring and lighting', 3900, 600, 10), ('Waiting area seating', 1150, 380, 8), ('Second laptop for billing', 980, 200, 4), ('Whiteboards and flip charts for groups', 310, 480, 6),
           ('Phone system handsets', 420, 330, 5), ('Family Room table and stackable chairs', 1250, 150, 8), ('Tablet for check-in and forms', 540, 70, 4), ('Safe for petty cash and records', 360, 540, 10)]
    for i, (it, cost, dago, yrs) in enumerate(sp2, 1):
        out.append(dict(item_id='ST-%02d' % i, item=it, date=ago(dago), cost=float(cost), years_of_use=yrs))
    out.sort(key=lambda r: r['date'], reverse=True)
    return out

# ------------------------------------------------------------------ next 12 months budget
def forecast12_d():
    hist = {}
    for m in MONTHS24[:-1]: hist[m] = PV[m]['sessions']
    base = sum(PV[iso(month_start(k))]['sessions'] for k in (1, 2, 4)) / 3.0
    seas = {1: 1.02, 2: 1.0, 3: 1.06, 4: 0.93, 5: 1.0, 6: 1.02, 7: 0.9, 8: 0.74, 9: 1.04, 10: 1.08, 11: 1.0, 12: 0.78}
    out = []
    for i in range(1, 13):
        m = month_start(-i); n = r0(base * seas[m.month] * (1 + 0.004 * i)); ch = 121.0 + (3.0 if m.month >= 1 and m.year > TODAY_.year else 0.0)
        pay = r0(n * ch * 0.465); rent = 6800.0 if i < 2 else 7000.0
        other = r0(3400 + 20 * n * 0.1 + (260 if m.month in (12, 1, 2) else 0))
        out.append(dict(bd_id='BD-%02d' % i, month=iso(m), sessions=n, avg_charge=ch, pay=float(pay), rent=rent, other_costs=float(other)))
    return out

# ------------------------------------------------------------------ growth milestones
def milestones_d():
    sp = [('Raise the Behaviour therapy fee to the break-even fee', -20, 'List fee reaches the break-even fee', 'Priya Raman', 'Done'),
          ('Move clinician pay share under 55 percent in every month', 45, 'Pay share of revenue at or under the target', 'Amira Lindqvist', 'In progress'),
          ('Build a cash reserve of three months of expenses', 240, 'Months of expenses in cash at 3', 'Amira Lindqvist', 'In progress'),
          ('Lift the booked share of the session cap to 85 percent', 60, 'Booked share of cap at or above the target', 'Grace Mensah', 'In progress'),
          ('Hire a third contract clinician', 120, 'New clinician sees 12 sessions a week', 'Amira Lindqvist', 'Not started'),
          ('Open evening online sessions', 25, 'Eight online evening sessions a week', 'Daniel Okoye', 'At risk'),
          ('Sublet the Play Room in the mornings', 75, 'Twelve sublet hours a week', 'Grace Mensah', 'Not started'),
          ('Agree next year\'s rent with the landlord', 90, 'Rent review meeting held and rent agreed', 'Ingrid Berg', 'Not started'),
          ('Bring overhead under 20 percent of revenue', 150, 'Overhead share at or under the target', 'Grace Mensah', 'In progress'),
          ('Run a second Stress skills group', 100, 'Group fill at or above 60 percent', 'Sofia Marchetti', 'Not started'),
          ('Review every fee against the local market band', -40, 'All ten fees checked against the band', 'Amira Lindqvist', 'Done'),
          ('Set up the monthly tax set-aside transfer', -90, 'Transfer made on the due date every month', 'Mateo Alvarez', 'Done'),
          ('Reach 480 attended sessions a month', 180, 'Attended sessions in a month at 480', 'Amira Lindqvist', 'In progress'),
          ('Replace the oldest laptops', 50, 'Two laptops bought and set up', 'Samir Haddad', 'Not started'),
          ('Move every expense into its budget category', 14, 'No expense left in a wrong category', 'Grace Mensah', 'In progress')]
    return [dict(ms_id='GM-%02d' % i, milestone=a, target_date=ahead(b), measure=c_, owner=d_, status=key('mstat', e)) for i, (a, b, c_, d_, e) in enumerate(sp, 1)]

# ------------------------------------------------------------------ reference tables
def services_d(): return [dict(service=key('svcall', x['service']), minutes=x['minutes'], fee=x['fee']) for x in C.services]
def team_d():
    out = []
    for t in C.team:
        d = dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                 monthly_salary=t['monthly_salary'], split_pct=t['split_pct'], session_rate=t['session_rate'], hourly_rate=t['hourly_rate'], session_cap=t['session_cap'], session_target=t['session_target'],
                 speciality=t['speciality'], country=t['country'], start=t['start'])
        out.append(d)
    return out

# ------------------------------------------------------------------ numbers for tool defaults (from the same data, last complete month and last 12 months)
def stats():
    S = {}; v = PV[LM0]; S['lm'] = v
    S['lm_revenue'] = v['session_revenue'] + v['group_revenue'] + v['sublet_income'] - v['write_offs']
    b = _svc12('Behaviour therapy'); n = max(1, b['n']); S['bt'] = dict(charge=b['rev'] / n, split=b['pay'] / b['rev'], room=b['room'] / n, other=b['oth'] / n, n=n)
    bk = [x for x in SM if x['service'] == 'Behaviour therapy' and x['month'] in {iso(month_start(k)) for k in range(1, 13)}]
    S['bt']['booked'] = sum(x['booked'] for x in bk)
    last3 = CASH[-4:-1]; S['cash_now'] = CASH[-1]['closing']
    return S
STATS = stats()

if __name__ == '__main__':
    for f in ('pnl_d', 'svc_months_d', 'clin_months_d', 'expenses_d', 'budget_d', 'room_costs_d', 'cash_d', 'forecast_d', 'tax_d', 'health_d', 'owed_d', 'bills_d', 'fixes_d', 'hiring_d', 'rooms_opt_d', 'setup_d',
              'forecast12_d', 'milestones_d', 'services_d', 'team_d'):
        r = globals()[f](); print(f, len(r), r[0])
    print(STATS)
